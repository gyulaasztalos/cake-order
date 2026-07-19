"""Cookieless-analytics config: CSP widening + gated script tag."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.main import _build_csp


def _settings(**over: str) -> Settings:
    s = Settings()
    for k, v in over.items():
        setattr(s, k, v)
    return s


def test_analytics_disabled_by_default():
    s = _settings()
    assert s.analytics_enabled is False
    assert s.analytics_origin == ""


def test_analytics_needs_both_src_and_id():
    assert _settings(analytics_src="https://stats.example/script.js").analytics_enabled is False
    assert _settings(analytics_website_id="abc").analytics_enabled is False
    s = _settings(analytics_src="https://stats.example/script.js", analytics_website_id="abc")
    assert s.analytics_enabled is True
    assert s.analytics_origin == "https://stats.example"


@pytest.mark.parametrize("src", ["/relative/script.js", "javascript:alert(1)", "not a url"])
def test_analytics_origin_rejects_non_absolute(src: str):
    # A path- or scheme-less src must never widen the CSP to a bare/unsafe value.
    s = _settings(analytics_src=src, analytics_website_id="abc")
    assert s.analytics_origin == ""


def test_build_csp_stays_self_when_disabled(monkeypatch):
    import app.main as main

    monkeypatch.setattr(main.settings, "analytics_src", "")
    monkeypatch.setattr(main.settings, "analytics_website_id", "")
    csp = _build_csp()
    # script-src carries self + the inline JSON-LD hash, but no external origin.
    assert "script-src 'self' 'sha256-" in csp
    assert "connect-src 'self';" in csp
    assert "https://" not in csp


def test_build_csp_widens_to_analytics_origin(monkeypatch):
    import app.main as main

    monkeypatch.setattr(main.settings, "analytics_src", "https://stats.anitatortai.hu/script.js")
    monkeypatch.setattr(main.settings, "analytics_website_id", "uuid-1")
    csp = _build_csp()
    # The analytics origin joins self + the JSON-LD hash in script-src.
    assert "script-src 'self' 'sha256-" in csp
    assert "https://stats.anitatortai.hu; connect-src" in csp
    assert "connect-src 'self' https://stats.anitatortai.hu;" in csp
    # Only the analytics origin is added — the rest stays self-only.
    assert "default-src 'self';" in csp
