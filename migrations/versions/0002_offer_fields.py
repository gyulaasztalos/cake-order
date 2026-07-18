"""Concept-form fields: cake_type + portions.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No rows exist pre-launch, so a plain NOT NULL add with a throwaway
    # server_default is safe; the default is dropped right after.
    op.add_column(
        "orders",
        sa.Column("cake_type", sa.String(16), nullable=False, server_default="other"),
    )
    op.alter_column("orders", "cake_type", server_default=None)
    op.add_column("orders", sa.Column("portions", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "portions")
    op.drop_column("orders", "cake_type")
