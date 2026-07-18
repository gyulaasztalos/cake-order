"""Optional flavor choice on offer requests.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("flavor", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "flavor")
