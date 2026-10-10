import json
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
import yaml
from .content import ROOT, Strict
from .indexing import rebuild, read_cards
from .decision import Question, decide, export_report, content_revision, localized

@asynccontextmanager
async def lifespan(app):
    app.state.index_warning = None
    try:
        rebuild()
    except (ValueError, OSError, yaml.YAMLError):
        # Serve only a previously valid index; do not hide a first-start failure.
        from .indexing import DB
        if not DB.exists():
            raise
        read_cards()
        app.state.index_warning = "Content rebuild failed; serving previous index. Run validation and repair content."
    yield

app = FastAPI(title="AgentAtlas local", lifespan=lifespan, docs_url=None, redoc_url=None)
class BodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        if headers.get(b"content-encoding", b"identity").lower() != b"identity":
            return await Response("Unsupported content encoding", status_code=415)(scope, receive, send)
        buffer, size = bytearray(), 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"")
            size += len(body)
            if size > 32_000:
                return await Response("Request too large", status_code=413)(scope, receive, send)
            buffer.extend(body)
            if not message.get("more_body", False):
                break
        delivered = False
        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(buffer), "more_body": False}
            return await receive()
        await self.app(scope, bounded_receive, send)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

@app.middleware("http")
async def local_boundary(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in ["http://127.0.0.1:18765", "http://localhost:18765"]:
        return Response("Origin rejected", status_code=403)
    if request.headers.get("content-length", "0").isdigit() and int(request.headers.get("content-length", "0")) > 32_000:
        return Response("Request too large", status_code=413)
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

@app.get("/api/health")
def health():
    return {"status": "ok", "model_api": "disabled", "network": "no product outbound requests", "index_warning": app.state.index_warning}

@app.get("/api/cases")
def cases(locale: Literal["zh-CN", "en"] = "zh-CN", validation: Literal["all", "not_run", "local_passed", "independently_reproduced"] = "all"):
    cards = read_cards()
    revision = content_revision(cards)
    return [{**c, "content_revision": revision} for c in localized(cards, locale) if validation == "all" or c["validation"]["status"] == validation]

@app.get("/api/cases/{case_id}")
def detail(case_id: str, locale: Literal["zh-CN", "en"] = "zh-CN", revision: str | None = None):
    cards = read_cards()
    current = content_revision(cards)
    if revision is not None and revision != current:
        raise HTTPException(409, "Content revision expired; query again")
    for card in localized(cards, locale):
        if card["id"] == case_id:
            return {**card, "content_revision": current}
    raise HTTPException(404, "Case not found")

@app.post("/api/decision")
def decision(request: Question):
    return decide(request, read_cards())

class Export(Strict):
    request: Question
    selected: list[str]
    format: Literal["json", "markdown"]
    content_revision: str
    result_id: str

@app.post("/api/export")
def export(request: Export):
    if len(request.selected) > 3 or len(request.selected) != len(set(request.selected)):
        raise HTTPException(422, "Select up to three distinct candidates")
    result = decide(request.request, read_cards())
    if request.content_revision != result["content_revision"] or request.result_id != result["result_id"]:
        raise HTTPException(409, "Result expired or input changed; query again")
    if not set(request.selected).issubset(c["card"]["id"] for c in result["candidates"]):
        raise HTTPException(422, "Selection must be current candidates")
    if any(c["status"] == "incompatible" and c["card"]["id"] in request.selected for c in result["candidates"]):
        raise HTTPException(422, "Excluded candidates cannot enter comparison")
    report, md = export_report(result, request.selected)
    return Response(json.dumps(report, ensure_ascii=False, indent=2) if request.format == "json" else md, media_type="application/json" if request.format == "json" else "text/markdown", headers={"Content-Disposition": 'attachment; filename="agentatlas-decision.' + ("json" if request.format == "json" else "md") + '"'})

app.add_middleware(BodyLimit)

if (ROOT / "web" / "dist").exists():
    app.mount("/", StaticFiles(directory=ROOT / "web" / "dist", html=True), name="web")
