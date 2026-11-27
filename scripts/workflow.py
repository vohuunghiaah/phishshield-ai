"""Commands invoked by the numbered Colab notebooks."""

import argparse
import importlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import yaml
from phishshield.data.prepare import FEATURES, prepare
from phishshield.utils.storage import RUNTIME_ROOT, save_json, validate_drive_access
from phishshield.utils.workspace import initialize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", type=int, choices=range(13))
    parser.add_argument("--seed", type=int, choices=[42, 43, 44])
    parser.add_argument("--mode", choices=list(FEATURES))
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--phase", choices=["TUNED_V2"], default="TUNED_V2")
    parser.add_argument(
        "--action", choices=["report", "select", "test"], default="report"
    )
    parser.add_argument("--tune", action="store_true")
    args = parser.parse_args()
    # Notebook bootstrap has verified identity before setting the environment.
    root = Path(os.environ["PHISHSHIELD_DRIVE_ROOT"]).resolve(strict=True)
    runtime = Path(os.environ.get("PHISHSHIELD_RUNTIME_ROOT", RUNTIME_ROOT))
    runtime.mkdir(parents=True, exist_ok=True)
    if args.step == 0:
        validate_drive_access(root)
        initialize(root)
        configs = {
            p.stem: yaml.safe_load(p.read_text("utf8"))
            for p in (root / "configs").glob("*.yaml")
        }
        for module in (
            "phishshield.features.pipeline",
            "phishshield.api.app",
            "phishshield.training.runs",
        ):
            importlib.import_module(module)
        gpu = (
            subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
            ).stdout.strip()
            if shutil.which("nvidia-smi")
            else None
        )
        base = Path(__file__).resolve().parents[1]
        subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(base / "tests")],
            cwd=base,
            check=True,
        )
        result = dict(
            root=str(root),
            runtime=str(runtime),
            python=sys.version,
            cpu=platform.processor() or platform.machine(),
            gpu=gpu,
            free_drive=shutil.disk_usage(root).free,
            free_runtime=shutil.disk_usage(runtime).free,
            configs=list(configs),
            tests="passed",
        )
        save_json(root / "reports/setup/runtime_environment.json", result)
    elif args.step == 1:
        from phishshield.data.download import download

        result = download(root)
    elif args.step == 2:
        result = prepare(root, runtime)["audit"]
    elif args.step == 3:
        from phishshield.data.eda import eda

        result = str(eda(root, runtime))
    elif args.step in (4, 5):
        mode = ("url_only", "url_html")[args.step - 4]
        cache = prepare(root, runtime)
        result = dict(
            path=str(root / FEATURES[mode]),
            sha256=cache["artifacts"][FEATURES[mode]],
            columns=cache["schemas"][mode],
        )
    elif args.step == 6:
        from phishshield.data.splits import lock_split

        result = lock_split(root, runtime)
    elif args.step in (7, 8, 9):
        from phishshield.training.runs import train

        model = ("random_forest", "xgboost", "mlp")[args.step - 7]
        if args.tune:
            from phishshield.data.tuning_workspace import tuning_workspace
            from phishshield.tuning.search import search

            with tuning_workspace(root, runtime) as workspace:
                result = [
                    search(workspace, runtime, model, mode, args.device)["selected_trial"]
                    for mode in ([args.mode] if args.mode else FEATURES)
                ]
        else:
            result = [
                train(root, runtime, model, mode, seed, args.device, args.phase)[
                    "status"
                ]
                for mode in ([args.mode] if args.mode else FEATURES)
                for seed in ([args.seed] if args.seed else [42, 43, 44])
            ]
    elif args.step == 10:
        from phishshield.evaluation.compare import compare, evaluate_test
        from phishshield.tuning.reporting import reports

        result = {"report": reports, "select": compare, "test": evaluate_test}[
            args.action
        ](root, *([] if args.action == "report" else [runtime]))
    elif args.step == 11:
        from phishshield.explainability.report import explain

        result = explain(root, runtime)
    else:
        from fastapi.testclient import TestClient
        from streamlit.testing.v1 import AppTest
        from phishshield.api.app import create_app

        client = TestClient(create_app(root))
        result = {
            "health": client.get("/health").json(),
            "models": client.get("/model-info").json(),
        }
        for endpoint, payload in [
            ("predict", {"url": "https://example.org/"}),
            (
                "predict-from-html",
                {
                    "url": "https://example.org/",
                    "html": "<html><title>Demo</title></html>",
                },
            ),
        ]:
            response = client.post("/" + endpoint, json=payload)
            expected = (
                200
                if result["models"][
                    "url_fallback" if endpoint == "predict" else "primary"
                ]
                else 503
            )
            if response.status_code not in (200, 503):
                response.raise_for_status()
            if response.status_code != expected:
                raise RuntimeError(f"{endpoint}: {response.status_code}")
            result[endpoint] = response.json()
        app = AppTest.from_file(
            str(Path(__file__).resolve().parents[1] / "src/phishshield/ui/app.py")
        ).run(timeout=60)
        if len(app.exception) or not len(app.button):
            raise RuntimeError("Streamlit smoke failed")
        result["ui"] = "rendered"
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
