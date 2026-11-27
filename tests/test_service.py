import socket
import joblib
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sklearn.ensemble import RandomForestClassifier
from phishshield.api.app import create_app
from phishshield.features.pipeline import VERSION, extract_features
from phishshield.inference.fetch import resolve_public
from phishshield.features.url_features import parse_url
from phishshield.utils.storage import sha256, save_json


@pytest.fixture
def client(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/api.yaml").write_text(
        "live_fetch: false\nmax_html_bytes: 8388608\n"
    )
    return TestClient(create_app(tmp_path))


def test_untrained(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/model-info").json() == {"primary": None, "url_fallback": None}
    assert (
        client.post("/predict", json={"url": "https://example.org"}).status_code == 503
    )


def test_bad_request(client):
    assert client.post("/predict", json={"url": "invalid"}).status_code == 422


@pytest.mark.parametrize("mode", ["url_only", "url_html"])
def test_offline_online(mode, tmp_path, client):
    data = [
        ("https://example.org/", "<title>Example</title>"),
        ("http://example.net/login", "<form><input type=password></form>"),
    ]
    x = [
        extract_features(url, html if mode == "url_html" else None)
        for url, html in data
    ]
    a = np.array([list(d.values()) for d in x])
    estimator = RandomForestClassifier(n_estimators=5, random_state=42).fit(a, [0, 1])
    folder = (
        tmp_path
        / "checkpoints/selected_model"
        / ("primary" if mode == "url_html" else "url_fallback")
    )
    folder.mkdir(parents=True)
    dest = folder / "model.joblib"
    joblib.dump(
        dict(
            estimator=estimator,
            columns=list(x[0]),
            baseline=a[0],
            version=VERSION,
            model="random_forest",
            modality=mode,
        ),
        dest,
    )
    save_json(
        folder / "selection.json",
        dict(
            artifact=dest.relative_to(tmp_path).as_posix(),
            model="random_forest",
            modality=mode,
            threshold=0.5,
            checkpoint_sha256=sha256(dest),
            feature_version=VERSION,
        ),
    )
    url, html = data[1]
    resp = client.post(
        "/predict-from-html" if mode == "url_html" else "/predict",
        json={"url": url, **({"html": html} if mode == "url_html" else {})},
    )
    assert resp.status_code == 200
    assert resp.json()["phishing_probability"] == pytest.approx(
        estimator.predict_proba(a[1:])[0, 1]
    )
    assert resp.json()["feature_modality"] == mode
    if mode == "url_html":
        assert client.post("/predict", json={"url": url}).status_code == 503


@pytest.mark.parametrize(
    "addr",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.169.254",
        "::1",
        "224.0.0.1",
        "::ffff:127.0.0.1",
    ],
)
def test_dns_mixed_answer_is_blocked(monkeypatch, addr):
    def answer(*args, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", (ip, 80))
            for ip in ["1.1.1.1", addr]
        ]

    monkeypatch.setattr(socket, "getaddrinfo", answer)
    with pytest.raises(ValueError):
        resolve_public(parse_url("http://example.org/"))
