"""Trusted local RPC to the confined worker; never connects to a user-supplied target."""

import base64
import os
from urllib.parse import urlsplit

import httpx

from phishshield.features.url_features import parse_url

PROTOCOL = "phishshield-static-v1"
MAX_HTML = 2 * 1024 * 1024


class WorkerUnavailable(RuntimeError):
    pass


class DestinationBlocked(ValueError):
    pass


def endpoint():
    value = os.environ.get("PHISHSHIELD_FETCHER_URL", "")
    if not value:
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise WorkerUnavailable("Invalid collector configuration") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "fetcher"}
        or not port
        or parsed.netloc != f"{parsed.hostname}:{port}"
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise WorkerUnavailable("Invalid collector configuration")
    return value


def available():
    try:
        base = endpoint()
        if not base:
            return False
        with httpx.Client(trust_env=False, timeout=1) as client:
            response = client.get(base + "/health")
            return response.status_code == 200 and response.json() == {
                "protocol": PROTOCOL,
                "confinement": "active",
            }
    except (ValueError, httpx.HTTPError, WorkerUnavailable):
        return False


def collect(url):
    """Return the final document URL and UTF-8 HTML, or None for a remote site failure."""
    base = endpoint()
    if base is None:
        raise WorkerUnavailable("Collector not configured")
    try:
        with httpx.Client(
            trust_env=False, timeout=httpx.Timeout(17, connect=2)
        ) as client:
            with client.stream(
                "POST",
                base + "/fetch",
                json={"url": url},
                headers={
                    "X-PhishShield-Worker": PROTOCOL,
                    "Accept-Encoding": "identity",
                },
            ) as response:
                if response.status_code == 403:
                    raise DestinationBlocked("Destination policy")
                if response.status_code == 424:
                    return None
                if (
                    response.status_code != 200
                    or response.headers.get("content-type")
                    != "application/octet-stream"
                    or response.headers.get("content-encoding", "identity")
                    != "identity"
                ):
                    raise WorkerUnavailable("Unexpected collector response")
                target = base64.b64decode(
                    response.headers["X-Document-URL"], altchars=b"-_", validate=True
                ).decode()
                parse_url(target)
                data = bytearray()
                for chunk in response.iter_raw():
                    if len(data) + len(chunk) > MAX_HTML:
                        raise WorkerUnavailable("Collector exceeded limit")
                    data.extend(chunk)
                html = data.decode("utf8")
                if not html.strip():
                    raise WorkerUnavailable("Collector returned empty document")
                return target, html
    except DestinationBlocked:
        raise
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise WorkerUnavailable("Collector unavailable") from exc
