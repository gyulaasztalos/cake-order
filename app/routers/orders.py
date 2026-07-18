"""Public routes: landing + content pages, offer-request form, verification.

Honeypot hits are answered with the normal success page (never tip off the
bot); rate-limit refusals and mailer failures re-render the form with a
banner. All visitor-facing strings go through t() in the resolved locale.
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Header, Request, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.i18n import CAKE_TYPES, FLAVORS, enabled_locale_names, resolve_locale
from app.services import backend, mailer, orders, ratelimit
from app.services.security import check_form_token, issue_form_token
from app.templating import templates

logger = logging.getLogger(__name__)
router = APIRouter()

# The owner drops real JPG photos into these directories (no code change
# needed); until then the galleries fall back to the placeholder SVGs.
_GALLERY_DIR = Path(__file__).parent.parent / "static" / "img" / "gallery"
_PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
_PLACEHOLDERS = [f"/static/img/gallery/cake-{i}.svg" for i in (1, 2, 3)]


def _gallery(kind: str) -> list[str]:
    photos = sorted(
        p.name for p in (_GALLERY_DIR / kind).glob("*") if p.suffix.lower() in _PHOTO_SUFFIXES
    )
    return [f"/static/img/gallery/{kind}/{name}" for name in photos] or _PLACEHOLDERS


def _locale(request: Request) -> str:
    return resolve_locale(request.cookies.get("lang"))


def _ctx(request: Request, **extra: object) -> dict[str, object]:
    return {
        "locale": _locale(request),
        "locales": enabled_locale_names(),
        "settings": settings,
        **extra,
    }


def _form_ctx(request: Request, **extra: object) -> dict[str, object]:
    min_due = dt.date.today() + dt.timedelta(days=settings.min_lead_days)
    ctx = _ctx(
        request,
        min_due=min_due.isoformat(),
        cake_types=CAKE_TYPES,
        flavors=FLAVORS,
        form_token=issue_form_token(),
    )
    ctx.update({"data": None, "errors": {}, "banner": None})
    ctx.update(extra)
    return ctx


# --- content pages ------------------------------------------------------------


@router.get("/")
def index(request: Request) -> Response:
    return templates.TemplateResponse(
        request, "index.html", _ctx(request, photos=_gallery("cakes")[:3])
    )


@router.get("/tortak")
def cakes(request: Request) -> Response:
    return templates.TemplateResponse(
        request, "cakes.html", _ctx(request, photos=_gallery("cakes"))
    )


@router.get("/desszertek")
def desserts(request: Request) -> Response:
    return templates.TemplateResponse(
        request, "desserts.html", _ctx(request, photos=_gallery("desserts"))
    )


@router.get("/rolam")
def about(request: Request) -> Response:
    return templates.TemplateResponse(request, "about.html", _ctx(request))


@router.get("/kapcsolat")
def contact(request: Request) -> Response:
    return templates.TemplateResponse(request, "contact.html", _ctx(request))


@router.get("/privacy")
def privacy(request: Request) -> Response:
    return templates.TemplateResponse(request, "privacy.html", _ctx(request))


# --- offer request flow -------------------------------------------------------


@router.get("/ajanlatkeres")
def offer_form(request: Request) -> Response:
    return templates.TemplateResponse(request, "offer.html", _form_ctx(request))


@router.post("/ajanlatkeres")
def submit_offer(
    request: Request,
    session: Session = Depends(get_session),
    name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    due_date: str = Form(""),
    cake_type: str = Form(""),
    flavor: str = Form(""),
    portions: str = Form(""),
    description: str = Form(""),
    consent: bool = Form(False),
    form_token: str = Form(""),
    website: str = Form(""),  # honeypot — humans never see or fill this
    x_forwarded_for: str | None = Header(None),
) -> Response:
    locale = _locale(request)

    def form_page(data=None, errors=None, banner=None, status_code: int = 200) -> Response:
        ctx = _form_ctx(request, data=data, errors=errors or {}, banner=banner)
        return templates.TemplateResponse(request, "offer.html", ctx, status_code=status_code)

    def submitted_page(shown_email: str) -> Response:
        return templates.TemplateResponse(
            request,
            "submitted.html",
            _ctx(request, email=shown_email, hours=settings.token_ttl_hours),
        )

    def validated() -> orders.OrderInput:
        return orders.validate(
            name, email, phone, due_date, cake_type, flavor, portions, description, consent
        )

    # 1) Honeypot: answer success, do nothing. Bots learn nothing.
    if website:
        logger.info("honeypot hit dropped")
        return submitted_page(email)

    # 2) Signed render-timestamp: too fast (bot) or stale/forged.
    if not check_form_token(form_token):
        return form_page(data=validated(), banner="error.too_fast", status_code=400)

    # 3) Field validation.
    data = validated()
    if data.errors:
        return form_page(data=data, errors=data.errors, status_code=422)

    # 4) Rate limits (per IP, then per e-mail address).
    ip = ratelimit.client_ip(x_forwarded_for, request.client.host if request.client else None)
    if not ratelimit.allow(
        session, ratelimit.KIND_ORDER_IP, ip, settings.rate_max_per_ip
    ) or not ratelimit.allow(
        session, ratelimit.KIND_ORDER_EMAIL, data.email, settings.rate_max_per_email
    ):
        return form_page(data=data, banner="error.rate_limited", status_code=429)

    # 5) Persist pending offer request + send the verification e-mail.
    order, raw_token = orders.create_or_refresh_pending(session, data, locale)
    try:
        mailer.send_verification(order, orders.verification_url(raw_token))
    except mailer.MailerError:
        logger.exception("verification e-mail failed")
        session.rollback()
        return form_page(data=data, banner="error.send_failed", status_code=502)

    return submitted_page(order.email)


@router.get("/verify/{token}")
def verify(request: Request, token: str, session: Session = Depends(get_session)) -> Response:
    state, order = orders.find_by_token(session, token)
    ctx = _ctx(request)
    if order:
        ctx["locale"] = resolve_locale(order.locale)

    if state == "already":
        return templates.TemplateResponse(request, "verify_already.html", ctx)
    if state == "invalid" or order is None:
        return templates.TemplateResponse(request, "verify_invalid.html", ctx, status_code=404)

    # The chef e-mail IS the offer request (until phase 2) — confirm only if it sends.
    try:
        mailer.send_order_to_chef(order)
    except mailer.MailerError:
        logger.exception("chef offer e-mail failed")
        session.rollback()
        return templates.TemplateResponse(
            request, "verify_failed.html", ctx | {"token": token}, status_code=502
        )
    orders.mark_confirmed(order)

    # Best-effort extras: customer confirmation + phase-2 forward.
    try:
        mailer.send_customer_confirmation(order)
    except mailer.MailerError:
        logger.exception("customer confirmation e-mail failed")
    try:
        if backend.forward_order(order):
            backend.mark_forwarded(order)
    except Exception:
        logger.exception("backend forward failed (offer request stays confirmed)")

    return templates.TemplateResponse(request, "verified.html", ctx)
