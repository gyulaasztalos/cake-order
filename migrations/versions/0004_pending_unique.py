"""At most one pending order per e-mail (partial unique index).

Backs the create-or-refresh dedupe so a concurrent double-submit can't leave
two pending rows for one address (which later crashed every submit with
MultipleResultsFound before the query was made tolerant).

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-19
"""

from __future__ import annotations

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_orders_pending_email",
        "orders",
        ["email"],
        unique=True,
        postgresql_where="status = 'pending'",
    )


def downgrade() -> None:
    op.drop_index("uq_orders_pending_email", table_name="orders")
