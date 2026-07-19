"""cake-pricing intake client (PLANNING §6, phase 2 — now live).

Feature-flagged via BACKEND_ENABLED. Forwarding is best-effort: the chef's
e-mail is the primary delivery; a backend failure logs and leaves the order
'confirmed' so nothing is lost. The intake API creates a customer + an
EXTERNAL DRAFT offer (no entry_date — the chef prices it on first save).
"""

from __future__ import annotations

import datetime as dt
import logging

import httpx

from app.config import settings
from app.i18n import t
from app.models import Order

logger = logging.getLogger(__name__)

_TIMEOUT = 10.0


def _payload(order: Order) -> dict[str, object]:
    return {
        "name": order.name,
        "email": order.email,
        "phone": order.phone,
        "due_date": order.due_date.isoformat(),
        # The chef reads Hungarian labels, not slugs.
        "theme": t(f"form.cake_type.{order.cake_type}", "hu"),
        "flavor": t(f"form.flavor.{order.flavor}", "hu") if order.flavor else None,
        "portions": order.portions,
        "description": order.description,
        "locale": order.locale,
        "request_date": (order.verified_at or dt.datetime.now(dt.UTC)).isoformat(),
    }


def forward_order(order: Order) -> int | None:
    """Push a confirmed order to cake-pricing. Returns the created draft
    offer's id (to link to it), or None if forwarding is disabled/unconfigured.
    Raises on an HTTP/transport error — the caller treats that as best-effort."""
    if not settings.backend_enabled:
        return None
    if not (settings.backend_url and settings.backend_token):
        logger.warning("backend enabled but URL/token missing — skipping forward")
        return None
    response = httpx.post(
        f"{settings.backend_url.rstrip('/')}/api/intake/offers",
        json=_payload(order),
        headers={"Authorization": f"Bearer {settings.backend_token}"},
        timeout=_TIMEOUT,
        trust_env=False,
    )
    response.raise_for_status()
    data = response.json()
    logger.info("order %s forwarded: %s", order.id, data)
    offer_id = data.get("offer_id")
    return int(offer_id) if offer_id is not None else None


def pricing_offer_url(offer_id: int | None) -> str | None:
    """The chef's link to price the created draft, or None if unavailable."""
    if offer_id is None or not settings.pricing_base_url:
        return None
    return f"{settings.pricing_base_url}/offers/{offer_id}/edit"


def mark_forwarded(order: Order) -> None:
    order.status = "forwarded"
    order.forwarded_at = dt.datetime.now(dt.UTC)
