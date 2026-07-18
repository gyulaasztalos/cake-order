"""Security regression tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_security_headers_present():
    r = client.get("/")
    csp = r.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Referrer-Policy"] == "no-referrer"


def test_no_inline_script_in_pages():
    # Strict CSP would break inline JS silently — fail loudly here instead.
    html = client.get("/").text
    assert "<script>" not in html
    assert "onclick=" not in html


def test_locale_cookie_is_clamped():
    # A hostile lang cookie must not reach templates (header/XSS vector).
    hostile = TestClient(app, cookies={"lang": "<script>evil</script>"})
    r = hostile.get("/")
    assert r.status_code == 200
    assert "<script>evil" not in r.text
