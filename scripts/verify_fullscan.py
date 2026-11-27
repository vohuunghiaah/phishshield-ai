"""Local integration check using IANA's example domain; do not retain downloaded HTML."""

import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlsplit

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--worker", default="http://127.0.0.1:18731")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if any(urlsplit(u).hostname != "127.0.0.1" for u in (args.api, args.worker)):
        raise ValueError("Local verification only")
    http = requests.Session()
    http.trust_env = False

    def prediction(payload, status=200):
        response = http.post(args.api + "/predict", json=payload, timeout=25)
        assert response.status_code == status, response.status_code
        return response.json()

    ready = http.get(args.worker + "/health", timeout=3).json()
    assert ready == {"protocol": "phishshield-static-v1", "confinement": "active"}
    assert http.get(args.api + "/capabilities", timeout=3).json()["full_scan"]
    target = "https://example.org/"
    collected = http.post(
        args.worker + "/fetch",
        json={"url": target},
        headers={"X-PhishShield-Worker": ready["protocol"]},
        timeout=17,
    )
    collected.raise_for_status()
    final = base64.urlsafe_b64decode(collected.headers["X-Document-URL"]).decode()
    full = prediction({"url": target, "mode": "full"})
    snapshot = prediction(
        {"url": final, "html": collected.content.decode("utf8"), "mode": "snapshot"}
    )
    quick = prediction({"url": target, "mode": "quick"})
    blocked = prediction({"url": "http://localhost/", "mode": "full"}, 422)
    missed = prediction({"url": "https://fullscan-fixture.invalid/", "mode": "full"})
    for key in (
        "model_version",
        "feature_modality",
        "feature_count",
        "threshold",
        "prediction",
    ):
        assert full[key] == snapshot[key], key
    error = abs(full["phishing_probability"] - snapshot["phishing_probability"])
    assert error < 1e-12 and full["feature_count"] == 34 and full["threshold"] == 0.2
    assert (
        full["html_extraction_status"] == "fetched" and full["fallback_reason"] is None
    )
    assert quick["feature_count"] == 17 and quick["threshold"] == 0.15
    assert (
        missed["html_extraction_status"] == "fetch_failed"
        and missed["fallback_reason"]
        and missed["feature_count"] == 17
    )
    assert (
        http.post(args.worker + "/fetch", json={"url": target}, timeout=3).status_code
        == 415
    )
    receipt = {
        "fixture": target,
        "html_bytes": len(collected.content),
        "fixture_sha256": sha256(collected.content).hexdigest(),
        "full_scan": full,
        "quick_features": quick["feature_count"],
        "snapshot_score_difference": error,
        "private_target": {"status": 422, "detail": blocked["detail"]},
        "dns_failure": missed["html_extraction_status"],
        "worker": ready,
        "missing_rpc_header": 415,
    }
    if args.output:
        args.output.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2), "utf8"
        )
    print(
        "Verified live HTML, primary 34, threshold 0.20, parity, offline Quick Scan and failure handling."
    )


if __name__ == "__main__":
    main()
