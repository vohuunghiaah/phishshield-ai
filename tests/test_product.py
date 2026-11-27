import asyncio
import importlib.util
from pathlib import Path
import socket

from fastapi.testclient import TestClient
import pytest

from phishshield.api.app import RequestLimit, create_app
from phishshield.inference.fetch import resolve_public
from phishshield.features.url_features import parse_url


@pytest.mark.parametrize("url", ["http://localhost", "http://169.254.169.254/", "http://[::1]/", "http://127.0.0.1/", "https://example.org:8443/"])
def test_fetch_boundary_is_closed(url):
    with pytest.raises(ValueError):
        resolve_public(parse_url(url))


@pytest.mark.parametrize("mode", ["quick", "full"])
def test_url_modes_never_make_target_connection(tmp_path, monkeypatch, mode):
    def unexpected(*args, **kwargs):
        pytest.fail("outbound DNS")
    monkeypatch.setattr(socket, "getaddrinfo", unexpected)
    monkeypatch.setenv("PHISHSHIELD_ISOLATED_EGRESS", "1")
    c = TestClient(create_app(tmp_path))
    assert c.post("/predict", json={"url":"https://example.org/","mode":mode}).status_code == 503


def test_invalid_mode_combinations(tmp_path):
    client = TestClient(create_app(tmp_path))
    for payload in ({"mode":"snapshot"},{"mode":"quick","html":"<p/>"},{"mode":"full","html":"<p/>"}):
        assert client.post("/predict",json={"url":"https://example.org/",**payload}).status_code == 422


def test_request_read_timeout():
    async def run():
        messages = []
        async def timeout():
            raise TimeoutError
        async def send(msg):
            messages.append(msg)
        await RequestLimit(None)({"type":"http","method":"POST"},timeout,send)
        assert messages[0]["status"] == 408
    asyncio.run(run())


def test_installer_validates_before_writing(tmp_path):
    path = Path(__file__).resolve().parents[1]/"scripts/install_models.py"
    spec = importlib.util.spec_from_file_location("installer", path)
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    source = tmp_path/"source"
    folder = source/"manifests"
    folder.mkdir(parents=True)
    (folder/"model_selection_v2.json").write_text("{}")
    destination = tmp_path/"dest"
    destination.mkdir()
    with pytest.raises(ValueError, match="digest"):
        installer.install(source, destination)
    assert list(destination.iterdir()) == []

