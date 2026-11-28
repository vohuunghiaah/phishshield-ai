import base64
import socket
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
import httpx
import pytest

from phishshield.api.app import create_app
from phishshield.inference import collector
from phishshield.inference import fetch as retrieval


@pytest.mark.parametrize(
    "status,expected", [(403, 422), (429, 503), (500, 503), (302, 503)]
)
def test_rpc_errors_and_redirects_stay_in_backend(
    monkeypatch, tmp_path, status, expected
):
    monkeypatch.setenv("PHISHSHIELD_FETCHER_URL", "http://127.0.0.1:18731")
    client = TestClient(create_app(tmp_path))
    requests = []

    def responder(request):
        requests.append(request)
        return httpx.Response(status, headers={"Location": "https://example.org/"})

    real_client = httpx.Client
    monkeypatch.setattr(
        collector.httpx,
        "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(responder), **kw),
    )
    response = client.post(
        "/predict", json={"url": "https://example.org/", "mode": "full"}
    )
    assert response.status_code == expected
    assert len(requests) == 1 and requests[0].url.host == "127.0.0.1"


def test_site_failure_is_distinct_from_worker_failure(monkeypatch):
    monkeypatch.setenv("PHISHSHIELD_FETCHER_URL", "http://127.0.0.1:18731")
    real_client = httpx.Client
    monkeypatch.setattr(
        collector.httpx,
        "Client",
        lambda **kw: real_client(
            transport=httpx.MockTransport(lambda req: httpx.Response(424)), **kw
        ),
    )
    assert collector.collect("https://example.org/") is None


def test_revalidate_every_redirect(monkeypatch):
    public = "https://example.org/"
    second = "https://example.net/"
    checked = []

    def verify(url):
        checked.append(url.geturl())
        if len(checked) > 1:
            raise retrieval.FetchPolicyError("blocked by test policy")
        return "example.org", (
            socket.AF_INET,
            socket.SOCK_STREAM,
            6,
            "",
            ("93.184.216.34", 443),
        )

    monkeypatch.setattr(retrieval, "resolve_public", verify)
    sock = MagicMock()
    monkeypatch.setattr(retrieval.socket, "socket", lambda *args: sock)
    monkeypatch.setattr(retrieval.ssl, "create_default_context", lambda: MagicMock())
    result = MagicMock()
    result.__enter__.return_value.status = 302
    result.__enter__.return_value.getheader.return_value = second
    monkeypatch.setattr(retrieval.http.client, "HTTPResponse", lambda _: result)
    with pytest.raises(retrieval.FetchPolicyError):
        retrieval.fetch_inner(public, 1024)
    assert checked == [public, second]
    sock.__enter__.return_value.connect.assert_called_once_with(("93.184.216.34", 443))


@pytest.mark.parametrize(
    "encoding,content_type",
    [("gzip", "application/octet-stream"), ("identity", "text/plain")],
)
def test_reject_malformed_worker_response(monkeypatch, encoding, content_type):
    monkeypatch.setenv("PHISHSHIELD_FETCHER_URL", "http://127.0.0.1:18731")
    real_client = httpx.Client

    def respond(req):
        return httpx.Response(
            200,
            headers={
                "content-type": content_type,
                "content-encoding": encoding,
                "X-Document-URL": base64.urlsafe_b64encode(
                    b"https://example.org/"
                ).decode(),
            },
        )

    monkeypatch.setattr(
        collector.httpx,
        "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw),
    )
    with pytest.raises(collector.WorkerUnavailable):
        collector.collect("https://example.org/")


def test_bad_worker_configuration_is_service_unavailable(monkeypatch, tmp_path):
    monkeypatch.setenv("PHISHSHIELD_FETCHER_URL", "http://127.0.0.1:invalid")
    client = TestClient(create_app(tmp_path))
    assert client.get("/capabilities").json() == {"full_scan": False}
    assert (
        client.post(
            "/predict", json={"url": "https://example.org/", "mode": "full"}
        ).status_code
        == 503
    )


@pytest.mark.parametrize(
    "error,status", [(TimeoutError(), 424), (OSError(), 503), (EOFError(), 503)]
)
def test_worker_error_classification(monkeypatch, error, status):
    from phishshield.inference import worker

    monkeypatch.setattr(worker, "verify_confinement", lambda: None)

    def fail(url, limit):
        raise error

    monkeypatch.setattr(worker, "fetch", fail)
    client = TestClient(worker.create_worker(), base_url="http://127.0.0.1")
    response = client.post(
        "/fetch",
        json={"url": "https://example.org/"},
        headers={"X-PhishShield-Worker": worker.PROTOCOL},
    )
    assert response.status_code == status
