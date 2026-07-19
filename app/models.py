"""ORM models — the whole persistent state of cake-order (PLANNING.md §3.5).

Two tables only. ORDERS holds a submission through its short life
(pending → confirmed → forwarded, or expired); retention jobs purge rows on the
configured windows, so this is a buffer, not an archive. RATE_EVENTS is an
append-only abuse ledger keyed by salted hashes — never raw IPs or emails.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Order lifecycle: pending (awaiting email verification) → confirmed (verified,
# emails sent) → forwarded (pushed to cake-pricing, phase 2). expired is set by
# the retention job for dead pending rows before purge.
ORDER_STATUSES = ("pending", "confirmed", "forwarded", "expired")


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'forwarded', 'expired')", name="ck_order_status"
        ),
        CheckConstraint("char_length(description) <= 4000", name="ck_description_len"),
        UniqueConstraint("token_hash", name="uq_orders_token_hash"),
        Index("ix_orders_status_entry", "status", "entry_date"),
        # At most one pending order per e-mail (dedupe backstop, migration 0004).
        Index(
            "uq_orders_pending_email",
            "email",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    update_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)

    # Customer-supplied fields (validated + length-limited at the edge; the DB
    # sizes are the hard backstop).
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    due_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    # Concept-form fields: cake type from a fixed option set, optional flavor
    # (owner's list, i18n.FLAVORS) and optional slices.
    cake_type: Mapped[str] = mapped_column(String(16), nullable=False)
    flavor: Mapped[str | None] = mapped_column(String(32))
    portions: Mapped[int | None] = mapped_column()
    description: Mapped[str] = mapped_column(Text, nullable=False)
    locale: Mapped[str] = mapped_column(String(5), default="hu", nullable=False)
    consent_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Verification token: only the SHA-256 hex digest is stored (§3.2).
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    token_expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    forwarded_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class RateEvent(Base):
    """Append-only rate-limit ledger. `key` = salted SHA-256 of IP or email."""

    __tablename__ = "rate_events"
    __table_args__ = (Index("ix_rate_events_lookup", "kind", "key", "entry_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)  # order_ip | order_email
    key: Mapped[str] = mapped_column(String(64), nullable=False)
