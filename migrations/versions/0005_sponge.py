"""Optional sponge (piskóta) choice on offer requests.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("sponge", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "sponge")
