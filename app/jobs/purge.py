"""Retention job (PLANNING §3.5): GDPR data minimization.

Run periodically (k8s CronJob / cron):  python -m app.jobs.purge

- pending orders older than PENDING_RETENTION_HOURS  → deleted (token long dead)
- confirmed/forwarded older than CONFIRMED_RETENTION_DAYS → deleted (the order
  lives on in the chef's mailbox / cake-pricing)
- rate events outside the rate window → deleted
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, cast

from sqlalchemy import CursorResult, delete

from app.config import settings
from app.db import SessionLocal
from app.models import Order
from app.services.ratelimit import purge_expired

logger = logging.getLogger(__name__)


def run() -> dict[str, int]:
    now = dt.datetime.now(dt.UTC)
    pending_cutoff = now - dt.timedelta(hours=settings.pending_retention_hours)
    confirmed_cutoff = now - dt.timedelta(days=settings.confirmed_retention_days)

    session = SessionLocal()
    try:
        pending = cast(
            "CursorResult[Any]",
            session.execute(
                delete(Order).where(Order.status == "pending", Order.entry_date < pending_cutoff)
            ),
        ).rowcount
        confirmed = cast(
            "CursorResult[Any]",
            session.execute(
                delete(Order).where(
                    Order.status.in_(("confirmed", "forwarded", "expired")),
                    Order.entry_date < confirmed_cutoff,
                )
            ),
        ).rowcount
        rate = purge_expired(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    counts = {"pending": pending or 0, "confirmed": confirmed or 0, "rate_events": rate}
    logger.info("purge done: %s", counts)
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run())  # noqa: T201 — CLI entrypoint output
