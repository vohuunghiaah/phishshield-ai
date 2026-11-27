"""Measure CPU inference on two synthetic parity fixtures, without network retrieval."""
import argparse
import json
import platform
import statistics
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import requests

from phishshield.features.pipeline import extract_features
from phishshield.inference.service import selected

ROOT = Path(__file__).resolve().parents[1]


def measure(operation, n):
    for _ in range(3):
        operation()
    samples = []
    for _ in range(n):
        start = time.perf_counter()
        operation()
        samples.append((time.perf_counter() - start) * 1000)
    return {"p50_ms": statistics.median(samples), "p95_ms": float(np.percentile(samples, 95))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=25)
    args = parser.parse_args()
    release = json.loads((ROOT / "MODEL_MANIFEST.json").read_text("utf8"))
    data = {"warmup": 3, "n": args.requests, "os": platform.platform(), "processor": platform.processor(),
            "python": platform.python_version(), "sklearn": version("scikit-learn"), "roles": {}}
    for role, fixture in release["fixtures"].items():
        payload = fixture["input"]
        meta, bundle = selected(ROOT, role, official=True)
        features = extract_features(payload["url"], payload.get("html"))
        x = np.array([[features[k] for k in bundle["columns"]]])
        est = bundle["estimator"]
        def explain():
            steps = np.tile(bundle["baseline"], (x.size+1,1))
            for i in range(x.size):
                steps[i+1:,i] = x[0,i]
            np.diff(est.predict_proba(steps)[:,1])
        def api():
            response = requests.post(args.base+"/predict",json=payload,timeout=20)
            response.raise_for_status()
        ops = {"load": lambda: selected(ROOT,role,official=True), "features": lambda: extract_features(payload["url"],payload.get("html")),
               "one_prediction": lambda: est.predict_proba(x), "sequential_explanation": explain, "http_total": api}
        data["roles"][role] = {"bytes": (ROOT/meta["artifact"]).stat().st_size,
                               **{k:measure(op,args.requests) for k,op in ops.items()}}
    dest = ROOT / "reports/product/benchmark.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data,indent=2),"utf8")


if __name__ == "__main__":
    main()

