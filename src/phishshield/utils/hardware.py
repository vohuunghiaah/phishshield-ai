"""Device-specific training preflight. Model libraries are imported on demand."""

import argparse
import csv
import ctypes
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


MODELS = {"random_forest": "Random Forest", "xgboost": "XGBoost", "mlp": "MLP"}


class HardwareError(RuntimeError):
    """The requested device could not be verified for this model."""


def check_cpu():
    """Collect host facts without querying accelerator drivers or libraries."""
    facts = dict(
        os=platform.platform(),
        python_version=platform.python_version(),
        interpreter=sys.executable,
        cpu_name=platform.processor() or platform.machine(),
        physical_cores=None,
        logical_cores=os.cpu_count(),
        ram_total_bytes=None,
        ram_available_bytes=None,
    )
    if sys.platform.startswith("linux"):
        blocks = Path("/proc/cpuinfo").read_text().strip().split("\n\n")
        processors = [
            dict(line.split(":", 1) for line in block.splitlines() if ":" in line)
            for block in blocks
        ]
        cores = set()
        for processor in processors:
            fields = {k.strip(): v.strip() for k, v in processor.items()}
            if fields.get("model name"):
                facts["cpu_name"] = fields["model name"]
            if "physical id" in fields and "core id" in fields:
                cores.add((fields["physical id"], fields["core id"]))
        facts["physical_cores"] = len(cores) or None
        mem = dict(
            line.split(":", 1)
            for line in Path("/proc/meminfo").read_text().splitlines()
        )
        facts["ram_total_bytes"] = int(mem["MemTotal"].split()[0]) * 1024
        facts["ram_available_bytes"] = int(mem["MemAvailable"].split()[0]) * 1024
    elif sys.platform == "win32":
        script = (
            "$cpu=Get-CimInstance Win32_Processor; $mem=Get-CimInstance Win32_OperatingSystem; "
            "@{cpu_name=($cpu.Name -join ', ');physical_cores=($cpu.NumberOfCores|Measure-Object -Sum).Sum;"
            "ram_total_bytes=([long]$mem.TotalVisibleMemorySize*1024);"
            "ram_available_bytes=([long]$mem.FreePhysicalMemory*1024)}|ConvertTo-Json -Compress"
        )
        facts.update(
            json.loads(
                subprocess.check_output(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-NonInteractive",
                        "-Command",
                        script,
                    ],
                    timeout=30,
                )
            )
        )
    else:
        raise HardwareError("Kiểm tra RAM hiện hỗ trợ Linux/Colab và Windows.")
    return facts


def booster_device(estimator, requested):
    config = json.loads(estimator.get_booster().save_config())
    actual = config["learner"]["generic_param"]["device"]
    if actual.split(":")[0] != requested:
        raise HardwareError(
            f"XGBoost yêu cầu {requested}, nhưng booster thực tế dùng {actual}."
        )
    return actual


def _gpu_inventory(ordinal):
    # Translate the CUDA-visible ordinal to its physical PCI address. nvidia-smi
    # indices need not match process indices under CUDA_VISIBLE_DEVICES.
    driver = (
        ctypes.WinDLL("nvcuda.dll")
        if sys.platform == "win32"
        else ctypes.CDLL("libcuda.so.1")
    )
    count, handle = ctypes.c_int(), ctypes.c_int()
    bus = ctypes.create_string_buffer(32)
    for method, args in [
        ("cuInit", (0,)),
        ("cuDeviceGetCount", (ctypes.byref(count),)),
        ("cuDeviceGet", (ctypes.byref(handle), ordinal)),
        ("cuDeviceGetPCIBusId", (bus, len(bus), handle)),
    ]:
        code = getattr(driver, method)(*args)
        if code:
            raise HardwareError(f"{method} trả mã lỗi CUDA {code}.")
    result = subprocess.check_output(
        [
            "nvidia-smi",
            "-i",
            bus.value.decode("ascii"),
            "--query-gpu=name,memory.total,memory.free,driver_version",
            "--format=csv,noheader,nounits",
        ],
        text=True,
        timeout=15,
    )
    name, total, free, version = next(
        csv.reader([result.strip()], skipinitialspace=True)
    )
    return dict(
        gpu_name=name,
        gpu_count=count.value,
        gpu_ordinal=ordinal,
        vram_total_bytes=int(total) * 1024**2,
        vram_available_bytes=int(free) * 1024**2,
        nvidia_driver=version,
    )


def _model_probe(model, device):
    if model == "mlp":
        import torch

        info = {"library": "torch", "library_version": torch.__version__}
        if device == "cuda":
            if not torch.version.cuda or not torch.cuda.is_available():
                raise HardwareError(
                    f"PyTorch {torch.__version__} chưa có CUDA khả dụng."
                )
            info["cuda_version"] = torch.version.cuda
        x = torch.ones((2, 2), device=device)
        product = x @ x
        if product.device.type != device or product.sum().item() != 8:
            raise HardwareError("Phép nhân ma trận PyTorch sai thiết bị hoặc kết quả.")
        if device == "cuda":
            torch.cuda.synchronize(product.device)
            info.update(_gpu_inventory(product.device.index))
        return dict(info, actual_device=product.device.type)

    if model == "random_forest":
        import sklearn
        from sklearn.ensemble import RandomForestClassifier

        estimator = RandomForestClassifier(n_estimators=2, random_state=42, n_jobs=1)
        info = dict(library="scikit-learn", library_version=sklearn.__version__)
    else:
        import xgboost

        info = dict(library="xgboost", library_version=xgboost.__version__)
        if device == "cuda":
            build = xgboost.build_info()
            if build.get("USE_CUDA") is not True:
                raise HardwareError(
                    f"XGBoost {xgboost.__version__} được build không có CUDA."
                )
            info["cuda_version"] = ".".join(map(str, build["CUDA_VERSION"]))
        estimator = xgboost.XGBClassifier(
            n_estimators=2,
            max_depth=2,
            n_jobs=1,
            tree_method="hist",
            device=device,
            random_state=42,
        )
    import numpy as np

    x = np.arange(16, dtype=np.float32).reshape(-1, 1)
    estimator.fit(x, (x[:, 0] >= 8).astype(int))
    actual = booster_device(estimator, device) if model == "xgboost" else "cpu"
    if device == "cuda":
        info.update(_gpu_inventory(int(actual.partition(":")[2] or 0)))
    elif not np.isfinite(estimator.predict_proba(x)).all():
        raise HardwareError("CPU smoke test trả xác suất không hữu hạn.")
    return dict(info, actual_device=actual.split(":")[0])


def check_gpu(model_name):
    if model_name not in ("xgboost", "mlp"):
        raise HardwareError("Random Forest của scikit-learn chỉ hỗ trợ DEVICE = 'cpu'.")
    return dict(_model_probe(model_name, "cuda"), cuda_support=True)


def check_hardware(model_name, device):
    if model_name not in MODELS or device not in ("cpu", "cuda"):
        raise HardwareError(f"Model/device không hợp lệ: {model_name}/{device}")
    if model_name == "random_forest" and device == "cuda":
        raise HardwareError("Random Forest của scikit-learn chỉ hỗ trợ DEVICE = 'cpu'.")
    try:
        host = check_cpu()
        probe = (
            check_gpu(model_name)
            if device == "cuda"
            else _model_probe(model_name, "cpu")
        )
    except Exception as exc:
        hint = (
            "Kiểm tra Colab Runtime > Change runtime type > GPU, driver và bản CUDA của thư viện."
            if device == "cuda"
            else "Kiểm tra Python và dependency CPU của mô hình."
        )
        raise HardwareError(f"{MODELS[model_name]} / {device}: {exc}. {hint}") from exc
    return dict(
        model=model_name,
        requested_device=device,
        **host,
        **probe,
        smoke_test="PASS",
        hardware_check_status="READY",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=MODELS)
    parser.add_argument("device", choices=["cpu", "cuda"])
    args = parser.parse_args()
    print("=" * 60, "PHISHSHIELD AI - HARDWARE CHECK", "=" * 60, sep="\n")
    print(
        f"Model           : {MODELS[args.model]}\nRequested device: {args.device.upper()}"
    )
    try:
        metadata = check_hardware(args.model, args.device)
    except HardwareError as exc:
        parser.exit(1, f"Hardware status : FAILED\n{exc}\n")
    for key, value in metadata.items():
        if key not in ("requested_device", "model"):
            print(
                f"{key.replace('_', ' '):20}: {value if value is not None else 'N/A'}"
            )
    print("=" * 60)


if __name__ == "__main__":
    main()
