"""Loopback inference API for the two locked classifiers."""
import asyncio
import os
import time
from typing import Literal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from phishshield.features.url_features import parse_url
from phishshield.inference.service import predict, selected
from phishshield.inference.service import read_json

HTML_LIMIT = 8 * 1024 * 1024


class RequestLimit:
    """Bound the JSON envelope before parsing, including chunked requests."""
    def __init__(self, app, limit=HTML_LIMIT + 65536):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        body = bytearray()
        try:
            async with asyncio.timeout(15):
                while True:
                    msg = await receive()
                    if msg["type"] == "http.disconnect":
                        return
                    chunk = msg.get("body", b"")
                    if len(body) + len(chunk) > self.limit:
                        return await JSONResponse({"detail":"Yêu cầu quá lớn"},413)(scope,receive,send)
                    body.extend(chunk)
                    if not msg.get("more_body"):
                        break
        except TimeoutError:
            return await JSONResponse({"detail":"Hết thời gian nhận dữ liệu"},408)(scope,receive,send)
        async def replay():
            nonlocal body
            if body is None:
                return await receive()
            packet = {"type":"http.request","body":bytes(body),"more_body":False}
            body = None
            return packet
        await self.app(scope, replay, send)


class Input(BaseModel):
    url: str = Field(min_length=1, max_length=8192)


class Prediction(Input):
    html: str | None = None
    mode: Literal["quick", "full", "snapshot"] | None = None


class Snapshot(Input):
    html: str


def create_app(root=None):
    app = FastAPI(title="PhishShield AI", version="2.0")
    app.add_middleware(RequestLimit)

    def workspace():
        return Path(root or os.environ.get("PHISHSHIELD_ROOT") or Path(__file__).resolve().parents[3])

    def load(role):
        try:
            return selected(workspace(), role, official=root is None)
        except (OSError, ValueError, KeyError, TypeError, ImportError):
            raise HTTPException(503, "Checkpoint hoặc schema chưa sẵn sàng.") from None

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse({"detail":"Dữ liệu JSON hoặc trường đầu vào không hợp lệ."},422)

    @app.get("/health")
    def health():
        return {"status":"ok"}

    @app.get("/ready")
    def ready():
        for role in ("primary","url_fallback"):
            load(role)
        return {"status":"ready"}

    @app.get("/model-info")
    @app.get("/model/info")
    def model_info():
        result = {}
        for role in ("primary","url_fallback"):
            if not (workspace()/"checkpoints/selected_model"/role/"selection.json").is_file():
                result[role] = None
                continue
            meta, bundle = load(role)
            result[role] = {k:meta.get(k) for k in ("model","modality","phase","threshold","seed","feature_version","checkpoint_sha256")}
            result[role]["feature_count"] = len(bundle["columns"])
        return result

    @app.get("/performance")
    def performance():
        try:
            record = read_json(workspace()/"results/metrics/locked_test.json")
            primary = read_json(workspace()/"manifests/model_selection_v2.json")["primary"]
            if record["selection"] != primary:
                raise ValueError
        except (OSError,ValueError,KeyError):
            raise HTTPException(503,"Chưa có kết quả Test cho mô hình chính.") from None
        return {"split":"locked_test","model":primary["model"],"modality":primary["modality"],"metrics":record["metrics"]}

    def infer(url, html, status, reason=None):
        started = time.perf_counter()
        model = load("primary" if html is not None else "url_fallback")
        try:
            result = predict(workspace(),url,html,status,model_bundle=model)
            result.update(fallback_reason=reason, processing_ms=round(1000*(time.perf_counter()-started), 3))
            return result
        except (UnicodeError,ValueError):
            raise HTTPException(422,"URL hoặc snapshot không phân tích được.") from None

    @app.post("/explain")
    @app.post("/predict")
    def analyze(inp: Prediction):
        try:
            parse_url(inp.url)
        except (ValueError,UnicodeError):
            raise HTTPException(422,"URL HTTP(S) không hợp lệ.") from None
        if inp.mode == "snapshot" and inp.html is None:
            raise HTTPException(422,"Snapshot Analysis cần HTML.")
        if inp.html is not None and inp.mode in {"quick","full"}:
            raise HTTPException(422,"Hãy chọn Snapshot Analysis khi cung cấp HTML.")
        if inp.html is not None:
            if not inp.html.strip():
                raise HTTPException(422,"Snapshot rỗng.")
            try:
                html_bytes = len(inp.html.encode("utf8"))
            except UnicodeError:
                raise HTTPException(422,"HTML cần dùng UTF-8.") from None
            if html_bytes > HTML_LIMIT:
                raise HTTPException(413,"Snapshot quá lớn.")
            return infer(inp.url,inp.html,"snapshot")
        if inp.mode == "full":
            return infer(inp.url,None,"disabled","Full Scan chưa có egress cô lập đã xác minh. Đã phân tích URL ngoại tuyến.")
        return infer(inp.url,None,"disabled")

    @app.post("/predict-from-html")
    def snapshot(inp: Snapshot):
        return analyze(Prediction(url=inp.url,html=inp.html))

    return app


app = create_app()

