"""Application entrypoint / factory.

Wires static assets, the security-header middleware, the page routes, and the
ops endpoints (/healthz, /readyz, /metrics). This app is PUBLIC: every response
carries a strict Content-Security-Policy (no inline JS, self-only origins) —
templates must never use inline <script> or on* attributes.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app import __version__
from app.config import settings
from app.db import engine
from app.i18n import resolve_locale
from app.routers import orders as orders_router

app = FastAPI(
    title="cake-order", version=__version__, docs_url=None, redoc_url=None, openapi_url=None
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Strict headers for a public app. HSTS is added by the TLS-terminating ingress.
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; base-uri 'self'; "
        "form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def _safe_redirect_path(raw_path: str) -> str:
    """A same-origin path for the post-lang redirect. Anything not a single
    leading-slash absolute path (e.g. `//evil.com`, a scheme, backslashes)
    collapses to `/` so the Location header can't become an open redirect."""
    if raw_path.startswith("/") and not raw_path.startswith("//") and "\\" not in raw_path:
        return raw_path
    return "/"


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    # /metrics is ops-only: reachable in-cluster (Prometheus, internal Traefik)
    # but 404 on any public host so the tunnel doesn't expose it.
    host = request.headers.get("host", "").split(":", 1)[0].lower()
    if request.url.path == "/metrics" and host in settings.public_hosts:
        response: Response = JSONResponse({"detail": "Not Found"}, status_code=404)
    # ?lang=xx on any GET page → persist the choice, redirect to a clean URL.
    elif request.method == "GET" and (lang := request.query_params.get("lang")) is not None:
        response = RedirectResponse(url=_safe_redirect_path(request.url.path), status_code=303)
        response.set_cookie(
            "lang",
            resolve_locale(lang),
            max_age=60 * 60 * 24 * 180,
            httponly=True,
            samesite="lax",
        )
    else:
        response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers[name] = value
    return response


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok", "version": __version__})


@app.get("/readyz")
def readyz() -> JSONResponse:
    # Ready = we can reach our database; k8s must not route traffic before that.
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        return JSONResponse({"status": "not ready", "version": __version__}, status_code=503)
    return JSONResponse({"status": "ready", "version": __version__})


app.include_router(orders_router.router)
