"""The optional Piskóta (sponge) choice: validation, e-mail, and intake payload."""

from __future__ import annotations

import datetime as dt

import pytest

from app.i18n import CATALOGS, SPONGES, t
from app.services.orders import earliest_due_date, validate


def _validate(sponge: str):
    return validate(
        name="Teszt Elek",
        email="teszt@example.com",
        phone="",
        due_date_raw=(earliest_due_date() + dt.timedelta(days=1)).isoformat(),
        cake_type="birthday",
        sponge=sponge,
        flavor="",
        portions_raw="12",
        description="Egy szép torta kérek.",
        consent=True,
    )


@pytest.mark.parametrize("slug", SPONGES)
def test_every_offered_sponge_is_accepted(slug):
    data = _validate(slug)
    assert data.sponge == slug
    assert "sponge" not in data.errors  # optional field, never an error


def test_blank_sponge_is_allowed():
    data = _validate("")
    assert data.sponge == ""
    assert not data.errors


def test_tampered_sponge_is_dropped_not_stored():
    # Anything outside the fixed list is discarded rather than persisted.
    assert _validate("<script>alert(1)</script>").sponge == ""
    assert _validate("nonexistent_flavour").sponge == ""


@pytest.mark.parametrize("locale", sorted(CATALOGS))
def test_every_sponge_is_translated_in_every_locale(locale):
    """Project rule: user-facing strings exist in ALL locales, so no key leaks raw."""
    for key in ("form.sponge", "form.sponge_hint", "form.sponge_ph", "email.field.sponge"):
        assert t(key, locale) != key, f"{key} missing for {locale}"
    for slug in SPONGES:
        key = f"form.sponge.{slug}"
        assert t(key, locale) != key, f"{key} missing for {locale}"


def test_intake_payload_sends_the_hungarian_label():
    """cake-pricing stores readable text (like flavor), not the slug."""
    from app.models import Order
    from app.services.backend import _payload

    order = Order(
        name="X",
        email="x@example.com",
        due_date=dt.date(2026, 12, 24),
        cake_type="birthday",
        sponge="fekete_kakaos",
        description="d",
        locale="hu",
        consent_at=dt.datetime.now(dt.UTC),
    )
    assert _payload(order)["sponge"] == "Fekete kakaós"


def test_intake_payload_omits_sponge_when_unset():
    from app.models import Order
    from app.services.backend import _payload

    order = Order(
        name="X",
        email="x@example.com",
        due_date=dt.date(2026, 12, 24),
        cake_type="birthday",
        description="d",
        locale="hu",
        consent_at=dt.datetime.now(dt.UTC),
    )
    assert _payload(order)["sponge"] is None
