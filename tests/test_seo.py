"""SEO: robots, sitemap, per-page meta, and JSON-LD ↔ CSP-hash consistency."""

from __future__ import annotations

import base64
import hashlib
import re

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.routers.orders import _SITEMAP_PATHS

client = TestClient(app)
BASE = settings.base_url


def test_robots_txt():
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    body = r.text
    assert "Disallow: /verify/" in body
    assert f"Sitemap: {BASE}/sitemap.xml" in body


def test_sitemap_lists_all_public_pages_with_alternates():
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/xml")
    xml = r.text
    for path in _SITEMAP_PATHS:
        assert f"<loc>{BASE}{path}</loc>" in xml
    # hreflang alternates present (at least hu + x-default).
    assert 'hreflang="hu"' in xml
    assert 'hreflang="x-default"' in xml


def test_home_has_seo_meta_and_og():
    html = client.get("/").text
    assert "<title>Anita Tortái — Egyedi kézműves torták | Szentendre</title>" in html
    assert '<meta name="description"' in html
    assert f'<link rel="canonical" href="{BASE}/">' in html
    assert '<meta property="og:title"' in html
    assert f'<meta property="og:image" content="{BASE}/static/img/logo-256.png">' in html
    assert 'hreflang="hu"' in html


def test_jsonld_present_and_matches_csp_hash():
    r = client.get("/")
    html = r.text
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    assert m, "JSON-LD block missing"
    payload = m.group(1)
    assert '"@type":"Bakery"' in payload
    # The exact rendered bytes must hash to the value allow-listed in the CSP,
    # or the browser would block the block (whitespace drift = silent breakage).
    digest = base64.b64encode(hashlib.sha256(payload.encode("utf-8")).digest()).decode()
    assert f"'sha256-{digest}'" in r.headers["Content-Security-Policy"]
