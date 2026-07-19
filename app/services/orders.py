"""Order intake business logic: validation, token lifecycle, verification.

The raw verification token exists only in the e-mail link; the DB stores its
SHA-256 digest (PLANNING §3.2). Validation returns i18n error KEYS — the router
renders them via t() in the visitor's language.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re
import secrets
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.i18n import CAKE_TYPES, FLAVORS
from app.models import Order

# Permissive on purpose: digits, spaces, +, -, /, parentheses. It is a contact
# convenience, not an identifier.
_PHONE_RE = re.compile(r"^[0-9+\-/() ]{6,32}$")
# Any C0/C1 control char (incl. CR/LF). The name reaches an e-mail Subject
# header, so a newline would break header construction — reject at the edge.
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")

# Lead-time is a human deadline, so anchor it to the chef's wall clock, not the
# container's UTC — otherwise a submit just after Budapest midnight is off by a day.
_LOCAL_TZ = ZoneInfo("Europe/Budapest")


def local_today() -> dt.date:
    return dt.datetime.now(_LOCAL_TZ).date()


def earliest_due_date() -> dt.date:
    """Soonest date the form accepts. Single source for the input `min=` and
    the server-side check, so the two can never drift."""
    return local_today() + dt.timedelta(days=settings.min_lead_days)


@dataclass
class OrderInput:
    name: str = ""
    email: str = ""
    phone: str = ""
    due_date: dt.date | None = None
    cake_type: str = ""
    flavor: str = ""
    portions: int | None = None
    description: str = ""
    consent: bool = False
    errors: dict[str, str] = field(default_factory=dict)  # field -> i18n key


def validate(
    name: str,
    email: str,
    phone: str,
    due_date_raw: str,
    cake_type: str,
    flavor: str,
    portions_raw: str,
    description: str,
    consent: bool,
) -> OrderInput:
    data = OrderInput(
        name=name.strip()[: settings.name_max],
        email=email.strip(),
        phone=phone.strip(),
        cake_type=cake_type.strip(),
        # Optional; anything outside the fixed list (tampering) is dropped.
        flavor=flavor.strip() if flavor.strip() in FLAVORS else "",
        description=description.strip(),
        consent=consent,
    )
    if not data.name or _CONTROL_RE.search(data.name):
        data.errors["name"] = "error.name_required"

    try:
        data.email = validate_email(data.email, check_deliverability=False).normalized
    except EmailNotValidError:
        data.errors["email"] = "error.email_invalid"

    if data.phone and not _PHONE_RE.fullmatch(data.phone):
        data.errors["phone"] = "error.phone_invalid"

    try:
        data.due_date = dt.date.fromisoformat(due_date_raw)
    except ValueError:
        data.errors["due_date"] = "error.due_date_invalid"
    else:
        if data.due_date < earliest_due_date():
            data.errors["due_date"] = "error.due_date_too_soon"

    if data.cake_type not in CAKE_TYPES:
        data.errors["cake_type"] = "error.cake_type_required"

    if portions_raw.strip():
        try:
            data.portions = int(portions_raw)
        except ValueError:
            data.errors["portions"] = "error.portions_invalid"
        else:
            if not 1 <= data.portions <= 500:
                data.errors["portions"] = "error.portions_invalid"

    if not data.description:
        data.errors["description"] = "error.description_required"
    elif len(data.description) > settings.description_max:
        data.errors["description"] = "error.description_too_long"

    if not consent:
        data.errors["consent"] = "error.consent_required"
    return data


def _new_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)  # 256 bits
    return raw, hashlib.sha256(raw.encode()).hexdigest()


def create_or_refresh_pending(session: Session, data: OrderInput, locale: str) -> tuple[Order, str]:
    """Insert a pending order, or refresh the existing pending one for this
    e-mail (new token, updated fields) instead of piling up duplicates."""
    now = dt.datetime.now(dt.UTC)
    raw, digest = _new_token()
    expires = now + dt.timedelta(hours=settings.token_ttl_hours)

    # .first() (not scalar_one_or_none): a rare concurrent double-submit can
    # briefly leave two pending rows for one e-mail (the partial unique index in
    # migration 0004 blocks the durable case) — refresh the oldest rather than
    # crashing every future submit with MultipleResultsFound.
    order = session.scalars(
        select(Order).where(Order.email == data.email, Order.status == "pending").order_by(Order.id)
    ).first()
    if order is None:
        order = Order(
            name=data.name,
            email=data.email,
            phone=data.phone or None,
            due_date=data.due_date,
            cake_type=data.cake_type,
            flavor=data.flavor or None,
            portions=data.portions,
            description=data.description,
            locale=locale,
            consent_at=now,
            token_hash=digest,
            token_expires_at=expires,
        )
        session.add(order)
    else:
        order.name = data.name
        order.phone = data.phone or None
        order.due_date = data.due_date  # type: ignore[assignment]
        order.cake_type = data.cake_type
        order.flavor = data.flavor or None
        order.portions = data.portions
        order.description = data.description
        order.locale = locale
        order.consent_at = now
        order.token_hash = digest
        order.token_expires_at = expires
    session.flush()
    return order, raw


def find_by_token(session: Session, raw_token: str) -> tuple[str, Order | None]:
    """Resolve a verification link: ('ok'|'already'|'invalid', order).

    Locks the matched row FOR UPDATE so concurrent hits on the same link (a
    real click racing an e-mail scanner's prefetch) serialize: the first
    confirms and sends, the rest block then read 'confirmed' → 'already'.
    Without the lock both would send the chef mail and create a duplicate
    cake-pricing draft (the intake POST is not idempotent).
    """
    if not raw_token or len(raw_token) > 64:
        return "invalid", None
    digest = hashlib.sha256(raw_token.encode()).hexdigest()
    order = session.scalars(
        select(Order).where(Order.token_hash == digest).with_for_update()
    ).first()
    if order is None:
        return "invalid", None
    if order.status in ("confirmed", "forwarded"):
        return "already", order
    now = dt.datetime.now(dt.UTC)
    if order.status != "pending" or order.token_expires_at < now:
        return "invalid", None
    return "ok", order


def mark_confirmed(order: Order) -> None:
    order.status = "confirmed"
    order.verified_at = dt.datetime.now(dt.UTC)


def verification_url(raw_token: str) -> str:
    return f"{settings.base_url}/verify/{raw_token}"
