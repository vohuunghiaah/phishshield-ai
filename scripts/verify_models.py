"""Verify release identity before deserialization and compare both predictions to saved fixtures."""
import hashlib
import json
from pathlib import Path
import sklearn
import numpy as np
from phishshield.inference.service import selected, predict

ROOT = Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    release = json.loads((root / "MODEL_MANIFEST.json").read_text("utf8"))
    if sklearn.__version__ != release["scikit_learn"]:
        raise ValueError("Incompatible scikit-learn")
    for name, record in release["files"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("Release digest mismatch: " + name)
    for role, spec in release["models"].items():
        meta, bundle = selected(root, role)
        est = bundle["estimator"]
        if (list(est.classes_) != [0, 1] or bundle["columns"] != spec["columns"]
                or meta["threshold"] != spec["threshold"] or est.random_state != spec["seed"]
                or any(est.get_params()[k] != v for k, v in spec["parameters"].items())
                or len(est.estimators_) != 300):
            raise ValueError("Model configuration mismatch: " + role)
        fixture = release["fixtures"][role]
        pred = predict(root, **fixture["input"], model_bundle=(meta, bundle))
        np.testing.assert_allclose(pred["phishing_probability"], fixture["score"], atol=1e-12, rtol=0)
        if pred["prediction"] != fixture["prediction"]:
            raise ValueError("Prediction mismatch")
        print(role, len(bundle["columns"]), meta["threshold"], spec["sha256"])


if __name__ == "__main__":
    verify()

