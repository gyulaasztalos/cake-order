"""Shared pytest fixtures.

Flow tests need a real Postgres (DATABASE_URL) — they are skipped otherwise so
plain unit runs still work. Run everything:

    podman run -d --name cakeorderpg -e POSTGRES_PASSWORD=devpass -e POSTGRES_USER=cake \\
        -e POSTGRES_DB=cake-order -p 55433:5432 postgres:18
    export DATABASE_URL=postgresql+psycopg://cake:devpass@localhost:55433/cake-order
    uv run alembic upgrade head
    uv run python -m pytest
"""

from __future__ import annotations

import os

import pytest

HAS_DB = bool(os.getenv("DATABASE_URL"))


@pytest.fixture
def clean_db():
    """Function-scoped: empty orders/rate_events tables."""
    if not HAS_DB:
        pytest.skip("requires DATABASE_URL")
    from sqlalchemy import text

    from app.db import SessionLocal

    s = SessionLocal()
    try:
        s.execute(text("TRUNCATE orders, rate_events RESTART IDENTITY"))
        s.commit()
    finally:
        s.close()
    yield


@pytest.fixture
def outbox(monkeypatch):
    """Capture outgoing e-mails instead of talking SMTP."""
    from app.services import mailer

    sent: list = []
    monkeypatch.setattr(mailer, "_send", sent.append)
    return sent


@pytest.fixture
def fast_form(monkeypatch):
    """Disable the min-fill-time check so tests can submit instantly."""
    from app.config import settings

    monkeypatch.setattr(settings, "min_fill_seconds", 0)
