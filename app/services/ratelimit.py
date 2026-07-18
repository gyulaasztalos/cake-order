"""DB-backed sliding-window rate limiting (PLANNING §3.4).

Budgets are counted over RATE_WINDOW_MINUTES from the append-only RATE_EVENTS
table, so limits survive restarts and need no extra infrastructure. Keys are
salted hashes (services.security.hash_value) — never raw IPs or addresses.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import RateEvent
from app.services.security import hash_value

KIND_ORDER_IP = "order_ip"
KIND_ORDER_EMAIL = "order_email"


def allow(session: Session, kind: str, raw_key: str, budget: int) -> bool:
    """True (and records the event) if `raw_key` is within its budget."""
    key = hash_value(raw_key)
    window_start = dt.datetime.now(dt.UTC) - dt.timedelta(minutes=settings.rate_window_minutes)
    count = session.execute(
        select(func.count())
        .select_from(RateEvent)
        .where(RateEvent.kind == kind, RateEvent.key == key, RateEvent.entry_date >= window_start)
    ).scalar_one()
    if count >= budget:
        return False
    session.add(RateEvent(kind=kind, key=key))
    return True


def purge_expired(session: Session) -> int:
    """Delete events older than the window; called by the retention job."""
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(minutes=settings.rate_window_minutes)
    result = cast(
        "CursorResult[Any]", session.execute(delete(RateEvent).where(RateEvent.entry_date < cutoff))
    )
    return result.rowcount or 0


def client_ip(forwarded_for: str | None, direct: str | None) -> str:
    """Client address for rate limiting.

    Behind our ingress the LAST X-Forwarded-For entry is the one the trusted
    proxy appended; earlier entries are client-forgeable and ignored.
    """
    if forwarded_for:
        return forwarded_for.rsplit(",", 1)[-1].strip()
    return direct or "unknown"
