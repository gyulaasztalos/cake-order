"""Backend (cake-pricing intake) client unit tests — no network."""

from __future__ import annotations

import datetime as dt

import httpx
import pytest

from app.config import settings
from app.services import backend
from app.services.backend import forward_order


def _order():
    from app.models import Order

    return Order(
        id=42,
        name="Kovács Éva",
        email="eva@example.com",
        phone="+36 30 123 4567",
        due_date=dt.date.today() + dt.timedelta(days=14),
        cake_type="birthday",
        flavor="oreo",
        portions=16,
        description="16 szeletes epres torta",
        locale="hu",
        verified_at=dt.datetime.now(dt.UTC),
    )


def test_disabled_backend_is_a_noop(monkeypatch):
    monkeypatch.setattr(settings, "backend_enabled", False)
    assert forward_order(_order()) is None


def test_enabled_without_config_skips(monkeypatch):
    monkeypatch.setattr(settings, "backend_enabled", True)
    monkeypatch.setattr(settings, "backend_url", "")
    assert forward_order(_order()) is None


def test_forward_posts_hungarian_labels(monkeypatch):
    monkeypatch.setattr(settings, "backend_enabled", True)
    monkeypatch.setattr(settings, "backend_url", "http://cake-pricing.test")
    monkeypatch.setattr(settings, "backend_token", "tok")
    captured = {}

    def fake_post(url, json=None, headers=None, **kwargs):
        captured.update(url=url, json=json, headers=headers)
        return httpx.Response(
            201, json={"offer_id": 1, "customer_id": 2}, request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(backend.httpx, "post", fake_post)
    assert forward_order(_order()) == 1  # returns the created draft offer id
    assert captured["url"] == "http://cake-pricing.test/api/intake/offers"
    assert captured["headers"]["Authorization"] == "Bearer tok"
    assert captured["json"]["theme"] == "Születésnapi torta"  # label, not slug
    assert captured["json"]["flavor"] == "Oreo"
    assert captured["json"]["portions"] == 16


def test_forward_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(settings, "backend_enabled", True)
    monkeypatch.setattr(settings, "backend_url", "http://cake-pricing.test")
    monkeypatch.setattr(settings, "backend_token", "tok")

    def fake_post(url, **kwargs):
        return httpx.Response(401, request=httpx.Request("POST", url))

    monkeypatch.setattr(backend.httpx, "post", fake_post)
    with pytest.raises(httpx.HTTPStatusError):
        forward_order(_order())


def test_pricing_offer_url(monkeypatch):
    from app.services.backend import pricing_offer_url

    monkeypatch.setattr(settings, "pricing_base_url", "https://torta.local.asztalos.net")
    assert pricing_offer_url(42) == "https://torta.local.asztalos.net/offers/42/edit"
    assert pricing_offer_url(None) is None
    monkeypatch.setattr(settings, "pricing_base_url", "")
    assert pricing_offer_url(42) is None
