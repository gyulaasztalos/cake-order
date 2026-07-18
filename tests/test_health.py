"""Smoke tests for the skeleton app."""

import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_readyz():
    r = client.get("/readyz")
    if os.getenv("DATABASE_URL"):
        assert r.status_code == 200
        assert r.json()["status"] == "ready"
    else:
        # No DB in a pure unit run → readiness must honestly say so.
        assert r.status_code == 503


def test_index_is_utf8_hungarian():
    r = client.get("/")
    assert r.status_code == 200
    # Hungarian accented text must survive round-trip (UTF-8 is critical).
    assert "Anita tortái" in r.text


def test_api_docs_disabled():
    # Public app: no OpenAPI/docs surface.
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404
