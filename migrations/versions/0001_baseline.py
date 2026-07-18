"""Baseline: orders + rate_events.

Revision ID: 0001
Revises:
Create Date: 2026-07-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "entry_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "update_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("locale", sa.String(5), nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("forwarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'forwarded', 'expired')", name="ck_order_status"
        ),
        sa.CheckConstraint("char_length(description) <= 4000", name="ck_description_len"),
        sa.UniqueConstraint("token_hash", name="uq_orders_token_hash"),
    )
    op.create_index("ix_orders_status_entry", "orders", ["status", "entry_date"])

    op.create_table(
        "rate_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "entry_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("key", sa.String(64), nullable=False),
    )
    op.create_index("ix_rate_events_lookup", "rate_events", ["kind", "key", "entry_date"])


def downgrade() -> None:
    op.drop_table("rate_events")
    op.drop_table("orders")
