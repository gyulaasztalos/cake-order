"""cake-pricing intake client — phase 2 stub (PLANNING §6).

The interface is final; the wire-up is feature-flagged off. When the intake API
exists on cake-pricing, forward_order() POSTs the confirmed order (creating a
customer + an external draft offer with request_date) using a bearer token.
Until then it is a recorded no-op so the rest of the app never special-cases.
"""

from __future__ import annotations

import datetime as dt

from app.config import settings
from app.models import Order


def forward_order(order: Order) -> bool:
    """Push a confirmed order to cake-pricing. Returns True if forwarded."""
    if not settings.backend_enabled:
        return False
    raise NotImplementedError("cake-pricing intake API is phase 2 (PLANNING §6)")


def mark_forwarded(order: Order) -> None:
    order.status = "forwarded"
    order.forwarded_at = dt.datetime.now(dt.UTC)
