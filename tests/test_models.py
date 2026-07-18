"""DB-free metadata guards for the ORM models."""

from __future__ import annotations

from app.models import Base, Order, RateEvent


def test_table_set_is_exactly_two():
    assert set(Base.metadata.tables) == {"orders", "rate_events"}


def test_orders_shape():
    cols = Order.__table__.columns
    assert cols["token_hash"].type.length == 64  # SHA-256 hex digest, never the raw token
    assert cols["email"].type.length == 254
    assert cols["phone"].nullable
    assert not cols["consent_at"].nullable  # GDPR consent is mandatory
    constraint_names = {c.name for c in Order.__table__.constraints}
    assert {"ck_order_status", "ck_description_len", "uq_orders_token_hash"} <= constraint_names


def test_rate_events_is_append_only_shape():
    # No update_date — rows are written once, purged by retention, never edited.
    assert "update_date" not in RateEvent.__table__.columns
