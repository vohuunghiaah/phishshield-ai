from io import BytesIO
import hashlib
import json
import joblib
import numpy as np

from phishshield.features.pipeline import VERSION, extract_features, schema


def read_json(path):
    return json.loads(path.read_text("utf8"))


def selected(root, name, *, official=False):
    path = root / "checkpoints/selected_model" / name / "selection.json"
    if not path.is_file():
        raise FileNotFoundError("Chưa có checkpoint đã chọn cho chế độ này.")
    meta = read_json(path)
    artifact = path.with_name("model.joblib")
    if meta["artifact"] != artifact.relative_to(root).as_posix():
        raise ValueError("Sai đường dẫn checkpoint đã chọn.")
    registry = root / "manifests/model_selection_v2.json"
    if registry.exists() or meta.get("phase") == "TUNED_V2":
        if read_json(registry)[name] != meta:
            raise ValueError("Checkpoint khác registry đã khóa.")
    if official:
        pin = {"primary": ("0a78a47a3a46579cabed3da4d68ed926573fd87df3df45afc9d59e24468ef948", "url_html", 0.20, 43),
               "url_fallback": ("0ce231574e7d61d7fdedb65b85f00c7cc1ecdd5e02859cb48bb4ea955f9a2897", "url_only", 0.15, 44)}[name]
        if (meta["checkpoint_sha256"], meta["modality"], meta["threshold"], meta["seed"]) != pin or meta["phase"] != "TUNED_V2":
            raise ValueError("Model release mismatch")
    payload = artifact.read_bytes()
    if hashlib.sha256(payload).hexdigest() != meta["checkpoint_sha256"]:
        raise ValueError("Checksum checkpoint không khớp.")
    bundle = joblib.load(BytesIO(payload))
    if (
        meta["feature_version"] != VERSION
        or bundle["version"] != VERSION
        or bundle["columns"] != schema(meta["modality"])
        or bundle["model"] != meta["model"]
        or bundle["modality"] != meta["modality"]
    ):
        raise ValueError("Sai phiên bản model/schema.")
    return meta, bundle


def predict(root, url, html=None, status="disabled", *, model_bundle=None):
    name = "primary" if html is not None else "url_fallback"
    meta, bundle = model_bundle if model_bundle is not None else selected(root, name)
    modality = meta["modality"]
    if html is None and modality != "url_only":
        raise ValueError("Cần mô hình URL-only riêng")
    features = extract_features(url, html if modality == "url_html" else None)
    cols = bundle["columns"]
    x = np.asarray([features[c] for c in cols])
    # Sequential replacement from the training median yields additive score differences.
    # Attribution is order-dependent; keep the locked schema order.
    steps = np.tile(bundle["baseline"], (len(cols) + 1, 1))
    for i in range(len(cols)):
        steps[i + 1 :, i] = x[i]
    probs = bundle["estimator"].predict_proba(steps)[:, 1]
    contrib = np.diff(probs)
    score = float(probs[-1])
    top = [
        dict(feature=cols[i], value=float(x[i]), contribution=float(contrib[i]))
        for i in np.argsort(-np.abs(contrib))[:5]
        if contrib[i] != 0
    ]
    positive = score >= meta["threshold"]
    note = "Phân loại theo ngưỡng validation. Kết quả là ước lượng của mô hình."
    return dict(
        prediction=int(positive),
        phishing_probability=score,
        risk_level="cao" if positive else "thấp",
        model_name=meta["model"],
        model_version=meta["checkpoint_sha256"][:12],
        model_phase=meta.get("phase"),
        feature_count=len(cols),
        feature_modality=modality,
        html_extraction_status=status,
        threshold=meta["threshold"],
        explanation={
            "text": note,
            "method": "Thay từng biến từ trung vị train theo thứ tự schema",
            "contributions": top,
        },
        warnings=["HTTPS riêng lẻ không chứng minh độ an toàn."],
    )
