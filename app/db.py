"""Database engine, session, and connection settings.

Connection is assembled from env vars set by the deployment: DB_HOST, DB_NAME,
DB_USER, DB_PASSWORD, optional DB_PORT. For local dev, set them in the shell or
a .env-style export.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _database_url() -> str:
    """Build a psycopg (v3) SQLAlchemy URL from the environment.

    A full DATABASE_URL, if provided, wins — handy for tests / ad-hoc runs.
    """
    if url := os.getenv("DATABASE_URL"):
        return url
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "cake-order")
    user = os.getenv("DB_USER", "cake-order")
    password = os.getenv("DB_PASSWORD", "")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


# pool_pre_ping guards against stale connections (CNPG failover, idle drops).
# Small pool — a single public form does not need more.
engine = create_engine(
    _database_url(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: yield a session, always closed afterwards."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
