"""HTTP boundary for the isolated Full Scan container. No checkpoint or host mounts."""

import asyncio
import base64
import json
import os
from pathlib import Path
import socket

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

from phishshield.inference.fetch import FetchPolicyError, fetch

LIMIT = 2 * 1024 * 1024
PROTOCOL = "phishshield-static-v1"


def verify_confinement():
    fields = dict(
        line.split(":", 1)
        for line in Path("/proc/self/status").read_text().splitlines()
        if ":" in line
    )
    if (
        os.geteuid() == 0
        or int(fields["CapBnd"], 16)
        or int(fields["CapEff"], 16)
        or int(fields["NoNewPrivs"]) != 1
    ):
        raise RuntimeError("Worker privileges not confined")
    # A real listening fixture distinguishes a denied connection from a closed port.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 80))
        listener.listen(1)
        try:
            connection = socket.create_connection(listener.getsockname(), timeout=0.5)
        except OSError:
            return
        connection.close()
        raise RuntimeError("Worker can reach the private canary")


def create_worker():
    verify_confinement()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "fetcher"]
    )
    slots = asyncio.Semaphore(2)

    @app.get("/health")
    async def health():
        return {"protocol": PROTOCOL, "confinement": "active"}

    @app.post("/fetch")
    async def collect(request: Request):
        if (
            request.headers.get("x-phishshield-worker") != PROTOCOL
            or request.headers.get("content-type") != "application/json"
        ):
            return Response(status_code=415)
        body = bytearray()
        try:
            async with asyncio.timeout(4):
                async for chunk in request.stream():
                    if len(body) + len(chunk) > 32768:
                        return Response(status_code=413)
                    body.extend(chunk)
            url = json.loads(body)["url"]
            if not isinstance(url, str) or not 0 < len(url) <= 8192:
                return Response(status_code=422)
        except TimeoutError:
            return Response(status_code=408)
        except (TypeError, KeyError, UnicodeError, ValueError):
            return Response(status_code=422)
        if slots.locked():
            return Response(status_code=429)
        async with slots:
            try:
                location, html = await asyncio.to_thread(fetch, url, LIMIT)
            except FetchPolicyError:
                return JSONResponse({"reason": "policy"}, status_code=403)
            except (ValueError, TimeoutError):
                return JSONResponse({"reason": "unavailable"}, status_code=424)
            except (RuntimeError, OSError, EOFError):
                return Response(status_code=503)
        data = html.encode("utf8")
        if not html.strip() or len(data) > LIMIT:
            return Response(status_code=424)
        location_header = base64.urlsafe_b64encode(location.encode("utf8")).decode(
            "ascii"
        )
        return Response(
            data,
            media_type="application/octet-stream",
            headers={
                "X-Document-URL": location_header,
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    return app


if __name__ == "__main__":
    uvicorn.run(
        create_worker(),
        host="0.0.0.0",
        port=8731,
        access_log=False,
        limit_concurrency=12,
        timeout_keep_alive=2,
    )
