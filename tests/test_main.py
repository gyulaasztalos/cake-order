"""Middleware: open-redirect guard on lang switch + /metrics host gate."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings
from app.main import _safe_redirect_path, app

client = TestClient(app)


def test_safe_redirect_path_blocks_open_redirects():
    # The httpx TestClient normalizes URLs, so the raw-ASGI-path vector (a path
    # starting with // reaching the app un-normalized) is unit-tested directly.
    assert _safe_redirect_path("//evil.example/x") == "/"
    assert _safe_redirect_path("/\\evil.example") == "/"
    assert _safe_redirect_path("https://evil.example") == "/"
    assert _safe_redirect_path("/rolam") == "/rolam"
    assert _safe_redirect_path("/") == "/"


def test_lang_switch_keeps_normal_path():
    r = client.get("/rolam?lang=en", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/rolam"


def test_metrics_blocked_on_public_host(monkeypatch):
    monkeypatch.setattr(settings, "public_host", "order.anitatortai.hu")
    assert client.get("/metrics", headers={"host": "order.anitatortai.hu"}).status_code == 404
    # In-cluster scrapers (service name / IP host) still get metrics.
    ok = client.get("/metrics", headers={"host": "cake-order.cake-order.svc.cluster.local"})
    assert ok.status_code == 200
