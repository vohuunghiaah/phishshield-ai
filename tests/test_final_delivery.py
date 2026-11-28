"""Offline contract and integrity regressions for the local application."""
import json
from pathlib import Path
import joblib
import numpy as np
import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from phishshield.api.app import create_app
from phishshield.features.pipeline import VERSION, schema
from phishshield.inference.service import predict
from phishshield.utils.storage import sha256

ROOT=Path(__file__).resolve().parents[1]


class ConstantScore:
    def predict_proba(self,x):
        return np.tile([0.8,0.2],(len(x),1))


@pytest.fixture
def workspace(tmp_path):
    (tmp_path/"configs").mkdir()
    (tmp_path/"configs/api.yaml").write_text("live_fetch: false\nmax_html_bytes: 8388608")
    d=tmp_path/"checkpoints/selected_model/primary"
    d.mkdir(parents=True)
    p=d/"model.joblib"; cols=schema("url_html")
    joblib.dump(dict(estimator=ConstantScore(),columns=cols,baseline=np.zeros(len(cols)),version=VERSION,model="random_forest",modality="url_html"),p)
    meta=dict(model="random_forest",modality="url_html",threshold=.2,checkpoint_sha256=sha256(p),feature_version=VERSION,phase="TUNED_V2",artifact=p.relative_to(tmp_path).as_posix())
    (d/"selection.json").write_text(json.dumps(meta))
    (tmp_path/"manifests").mkdir()
    (tmp_path/"manifests/model_selection_v2.json").write_text(json.dumps(dict(primary=meta)))
    return tmp_path


def test_threshold_equality(workspace):
    r=predict(workspace,"https://example.org","<title>Fixture</title>","snapshot")
    assert r["phishing_probability"]==r["threshold"] and r["prediction"]==1


@pytest.mark.parametrize("failure",["missing","checksum","schema","registry"])
def test_system_failure_never_falls_back(workspace,failure):
    directory=workspace/"checkpoints/selected_model/primary"
    artifact=directory/"model.joblib"
    selection=directory/"selection.json"
    reg=workspace/"manifests/model_selection_v2.json"
    if failure=="missing":
        artifact.unlink()
    elif failure=="checksum":
        artifact.write_bytes(b"fixture")
    else:
        m=json.loads(selection.read_text())
        m["feature_version"]="invalid"
        selection.write_text(json.dumps(m))
        if failure=="schema":
            reg.write_text(json.dumps({"primary":m}))
    r=TestClient(create_app(workspace)).post("/predict",json={"url":"https://example.org","html":"<p>demo</p>"})
    assert r.status_code==503 and str(workspace) not in r.text


def test_static_snapshot_and_chunk_limit(workspace):
    c=TestClient(create_app(workspace))
    r=c.post("/predict",json={"url":"https://example.org","html":"<script>throw Error('fixture')</script>"})
    assert r.status_code==200 and r.json()["feature_count"]==34
    data=(b"a"*1048576 for _ in range(9))
    assert c.post("/predict",content=data).status_code==413


def test_ui_handles_unavailable_api(monkeypatch):
    monkeypatch.setenv("PHISHSHIELD_API_URL","http://127.0.0.1:1")
    app = AppTest.from_file(str(ROOT / "src/phishshield/ui/app.py"), default_timeout=12).run()
    assert not app.exception
    assert any("API chưa kết nối" in notice.value for notice in app.error)
    assert app.button[0].disabled
    assert all("Full Scan" not in radio.options for radio in app.radio)
