"""Hardware preflight and training guards. CUDA success cases here use doubles."""

import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from phishshield.training import runs
from phishshield.utils import hardware as hw


def forbidden(*args, **kwargs):
    pytest.fail("Unexpected device probe or training side effect")


@pytest.fixture
def host(monkeypatch):
    monkeypatch.setattr(
        hw, "check_cpu", lambda: {"cpu_name": "fixture", "ram_total_bytes": 1024}
    )
    monkeypatch.setattr(hw, "_gpu_inventory", forbidden)


@pytest.mark.parametrize(
    "model,library",
    [("random_forest", "sklearn"), ("xgboost", "xgboost"), ("mlp", "torch")],
)
def test_cpu_probes_only_selected_device(host, monkeypatch, model, library):
    lib = pytest.importorskip(library)
    monkeypatch.setattr(hw, "check_gpu", forbidden)
    monkeypatch.setattr(hw.subprocess, "check_output", forbidden)
    if model == "mlp":
        monkeypatch.setattr(lib.cuda, "is_available", forbidden)
        monkeypatch.setattr(lib.cuda, "synchronize", forbidden)
    else:
        monkeypatch.setitem(sys.modules, "torch", None)
    if model != "xgboost":
        monkeypatch.setitem(sys.modules, "xgboost", None)
    info = hw.check_hardware(model, "cpu")
    assert info["requested_device"] == info["actual_device"] == "cpu"
    assert info["library_version"] == lib.__version__
    assert info["hardware_check_status"] == "READY" and "gpu_name" not in info


def test_forest_rejects_cuda_before_any_probe(monkeypatch):
    monkeypatch.setattr(hw, "check_cpu", forbidden)
    monkeypatch.setattr(hw, "check_gpu", forbidden)
    with pytest.raises(hw.HardwareError, match="cpu"):
        hw.check_hardware("random_forest", "cuda")


@pytest.mark.parametrize(
    "build,observed", [(True, "cuda:1"), (False, None), (True, "cpu")]
)
def test_xgboost_cuda_only_uses_xgboost(host, monkeypatch, build, observed):
    monkeypatch.setitem(sys.modules, "torch", None)
    xgb = MagicMock()
    xgb.__version__ = "fixture"
    xgb.build_info.return_value = {"USE_CUDA": build, "CUDA_VERSION": [12, 5]}
    xgb.XGBClassifier.return_value.get_booster.return_value.save_config.return_value = (
        json.dumps({"learner": {"generic_param": {"device": observed}}})
    )
    monkeypatch.setitem(sys.modules, "xgboost", xgb)
    if observed == "cuda:1":
        monkeypatch.setattr(
            hw, "_gpu_inventory", lambda ordinal: {"gpu_ordinal": ordinal}
        )
        info = hw.check_hardware("xgboost", "cuda")
        assert info["actual_device"] == "cuda" and info["gpu_ordinal"] == 1
        assert info["cuda_version"] == "12.5"
    else:
        with pytest.raises(hw.HardwareError, match="Runtime"):
            hw.check_hardware("xgboost", "cuda")
    if build:
        assert xgb.XGBClassifier.call_args.kwargs["tree_method"] == "hist"
        assert xgb.XGBClassifier.call_args.kwargs["device"] == "cuda"
        xgb.XGBClassifier.return_value.fit.assert_called_once()
    else:
        xgb.XGBClassifier.assert_not_called()


@pytest.mark.parametrize(
    "available,actual", [(True, "cuda"), (False, None), (True, "cpu")]
)
def test_mlp_cuda_only_uses_torch(host, monkeypatch, available, actual):
    monkeypatch.setitem(sys.modules, "xgboost", None)
    torch = MagicMock()
    torch.__version__ = "fixture"
    torch.version.cuda = "12.8"
    torch.cuda.is_available.return_value = available
    product = torch.ones.return_value.__matmul__.return_value
    product.device = SimpleNamespace(type=actual, index=0)
    product.sum.return_value.item.return_value = 8
    monkeypatch.setitem(sys.modules, "torch", torch)
    if actual == "cuda":
        monkeypatch.setattr(
            hw, "_gpu_inventory", lambda ordinal: {"gpu_ordinal": ordinal}
        )
        assert hw.check_hardware("mlp", "cuda")["actual_device"] == "cuda"
        torch.ones.assert_called_once_with((2, 2), device="cuda")
        torch.cuda.synchronize.assert_called_once_with(product.device)
    else:
        with pytest.raises(hw.HardwareError, match="Runtime"):
            hw.check_hardware("mlp", "cuda")
        torch.cuda.synchronize.assert_not_called()


def test_failed_hardware_stops_before_run(tmp_path, monkeypatch):
    monkeypatch.setattr(runs, "read_locked_split", forbidden)
    with pytest.raises(hw.HardwareError):
        runs.train(tmp_path, tmp_path, "random_forest", "url_only", 42, "cuda")
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("model", list(runs.MEMBERS))
def test_train_manifest_and_device_reuse(tmp_path, host, monkeypatch, model):
    if model in ("xgboost", "mlp"):
        pytest.importorskip("torch" if model == "mlp" else model)
    root = tmp_path / "workspace"
    runtime = tmp_path / "runtime"
    hp = {
        "random_forest": {"n_estimators": 2},
        "xgboost": {"n_estimators": 2, "tree_method": "hist", "n_jobs": 1},
        "mlp": {
            "epochs": 1,
            "batch_size": 4,
            "patience": 1,
            "hidden": 4,
            "learning_rate": 0.01,
        },
    }

    def config(root, name):
        return hp if name == "models" else {"train_seeds": [42], "thresholds": [0.5]}

    monkeypatch.setattr(runs, "config", config)
    monkeypatch.setattr(
        runs, "read_locked_split", lambda root: {"sha256": "test-split"}
    )
    cols = runs.schema("url_only")
    rng = np.random.default_rng(42)
    frame = pd.DataFrame(rng.random((16, len(cols))), columns=cols)
    frame["label"] = [0, 1] * 8
    monkeypatch.setattr(
        runs,
        "partitions",
        lambda *args: {"train": frame.iloc[:8], "validation": frame.iloc[8:]},
    )
    meta = runs.train(root, runtime, model, "url_only", 42)
    saved = runs.verified_run(root, runs.run_dir(root, model, "url_only", 42))
    assert meta == saved and meta["device"] == "cpu"
    h = saved["hardware"]
    assert (
        h["requested_device"] == h["actual_device"] == "cpu"
        and h["hardware_check_status"] == "READY"
    )
    if model == "mlp":
        assert h["parameter_device"] == "cpu"
    if model == "xgboost":
        assert h["booster_device"] == "cpu"
    assert (
        runs.train(root, runtime, model, "url_only", 42)["attempt"] == meta["attempt"]
    )
    if model != "random_forest":
        monkeypatch.setattr(
            runs, "check_hardware", lambda *args: {"actual_device": "cuda"}
        )
        with pytest.raises(RuntimeError, match="thiết bị"):
            runs.train(root, runtime, model, "url_only", 42, "cuda")
        assert saved == runs.verified_run(
            root, runs.run_dir(root, model, "url_only", 42)
        )
