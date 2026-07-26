"""Slice count (Torta szeletek száma) is mandatory only for per-slice cake types."""

from __future__ import annotations

import datetime as dt

import pytest

from app.i18n import PORTIONS_REQUIRED_TYPES
from app.services.orders import earliest_due_date, validate

OPTIONAL_TYPES = ("dessert", "other")


def _validate(cake_type: str, portions_raw: str):
    return validate(
        name="Teszt Elek",
        email="teszt@example.com",
        phone="",
        due_date_raw=(earliest_due_date() + dt.timedelta(days=1)).isoformat(),
        cake_type=cake_type,
        flavor="",
        portions_raw=portions_raw,
        description="Egy szép torta kérek.",
        consent=True,
    )


@pytest.mark.parametrize("cake_type", PORTIONS_REQUIRED_TYPES)
def test_blank_portions_rejected_for_per_slice_types(cake_type):
    data = _validate(cake_type, "")
    assert data.errors.get("portions") == "error.portions_required"


@pytest.mark.parametrize("cake_type", OPTIONAL_TYPES)
def test_blank_portions_allowed_for_dessert_and_other(cake_type):
    data = _validate(cake_type, "")
    assert "portions" not in data.errors
    assert data.portions is None


@pytest.mark.parametrize("cake_type", PORTIONS_REQUIRED_TYPES)
def test_supplied_portions_accepted(cake_type):
    data = _validate(cake_type, "12")
    assert "portions" not in data.errors
    assert data.portions == 12


def test_invalid_portions_still_reported_as_invalid_not_missing():
    data = _validate("birthday", "abc")
    assert data.errors.get("portions") == "error.portions_invalid"
    data = _validate("birthday", "0")
    assert data.errors.get("portions") == "error.portions_invalid"


def test_unknown_cake_type_does_not_demand_portions():
    # The cake_type error is the real problem; don't pile on a portions error.
    data = _validate("nonsense", "")
    assert data.errors.get("cake_type") == "error.cake_type_required"
    assert "portions" not in data.errors
