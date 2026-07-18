"""Public routes: order form, submission, e-mail verification, privacy page.

Honeypot hits are answered with the normal success page (never tip off the
bot); rate-limit refusals and mailer failures re-render the form with a
banner. All visitor-facing strings go through t() in the resolved locale.
"""

from __future__ import annotations

import datetime as dt
import logging

from fastapi import APIRouter, Depends, Form, Header, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.i18n import enabled_locale_names, resolve_locale
from app.services import backend, mailer, orders, ratelimit
from app.services.security import check_form_token, issue_form_token
from app.templating import templates

logger = logging.getLogger(__name__)
router = APIRouter()

LANG_COOKIE_MAX_AGE = 60 * 60 * 24 * 180  # half a year


def _locale(request: Request) -> str:
    return resolve_locale(request.cookies.get("lang"))


def _form_context(request: Request, locale: str, **extra: object) -> dict[str, object]:
    min_due = dt.date.today() + dt.timedelta(days=settings.min_lead_days)
    return {
        "min_due": min_due.isoformat(),
        "locale": locale,
        "locales": enabled_locale_names(),
        "settings": settings,
        "form_token": issue_form_token(),
        "data": None,
        "errors": {},
        "banner": None,
        **extra,
    }


@router.get("/")
def index(request: Request, lang: str | None = None) -> Response:
    # ?lang=xx → persist choice in a cookie and redirect to a clean URL.
    if lang is not None:
        response: Response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            "lang",
            resolve_locale(lang),
            max_age=LANG_COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
        )
        return response
    locale = _locale(request)
    return templates.TemplateResponse(request, "index.html", _form_context(request, locale))


@router.get("/privacy")
def privacy(request: Request) -> Response:
    locale = _locale(request)
    return templates.TemplateResponse(
        request, "privacy.html", {"locale": locale, "locales": enabled_locale_names()}
    )


@router.post("/order")
def submit_order(
    request: Request,
    session: Session = Depends(get_session),
    name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    due_date: str = Form(""),
    description: str = Form(""),
    consent: bool = Form(False),
    form_token: str = Form(""),
    website: str = Form(""),  # honeypot — humans never see or fill this
    x_forwarded_for: str | None = Header(None),
) -> Response:
    locale = _locale(request)

    def form_page(data=None, errors=None, banner=None, status_code: int = 200) -> Response:
        ctx = _form_context(request, locale, data=data, errors=errors or {}, banner=banner)
        return templates.TemplateResponse(request, "index.html", ctx, status_code=status_code)

    def submitted_page(shown_email: str) -> Response:
        return templates.TemplateResponse(
            request,
            "submitted.html",
            {
                "locale": locale,
                "locales": enabled_locale_names(),
                "email": shown_email,
                "hours": settings.token_ttl_hours,
            },
        )

    # 1) Honeypot: answer success, do nothing. Bots learn nothing.
    if website:
        logger.info("honeypot hit dropped")
        return submitted_page(email)

    # 2) Signed render-timestamp: too fast (bot) or stale/forged.
    if not check_form_token(form_token):
        data = orders.validate(name, email, phone, due_date, description, consent)
        return form_page(data=data, banner="error.too_fast", status_code=400)

    # 3) Field validation.
    data = orders.validate(name, email, phone, due_date, description, consent)
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

    # 5) Persist pending order + send the verification e-mail.
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
    locale = resolve_locale(order.locale) if order else _locale(request)
    ctx: dict[str, object] = {"locale": locale, "locales": enabled_locale_names()}

    if state == "invalid":
        return templates.TemplateResponse(request, "verify_invalid.html", ctx, status_code=404)
    if state == "already":
        return templates.TemplateResponse(request, "verify_already.html", ctx)

    if order is None:  # unreachable: state == "ok" implies an order
        return templates.TemplateResponse(request, "verify_invalid.html", ctx, status_code=404)
    # The chef e-mail IS the order (until phase 2) — only confirm if it sends.
    try:
        mailer.send_order_to_chef(order)
    except mailer.MailerError:
        logger.exception("chef order e-mail failed")
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
        logger.exception("backend forward failed (order stays confirmed)")

    return templates.TemplateResponse(request, "verified.html", ctx)
