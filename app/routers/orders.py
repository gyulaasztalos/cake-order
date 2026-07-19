"""Public routes: landing + content pages, offer-request form, verification.

Honeypot hits are answered with the normal success page (never tip off the
bot); rate-limit refusals and mailer failures re-render the form with a
banner. All visitor-facing strings go through t() in the resolved locale.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
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
# needed); until then the galleries fall back to the placeholder SVGs. The
# initContainer also writes a downscaled copy of each photo into a `thumbs/`
# subdir — the grid shows the thumbnail, the lightbox loads the full image.
_GALLERY_DIR = Path(__file__).parent.parent / "static" / "img" / "gallery"
_PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
_PLACEHOLDERS = [f"/static/img/gallery/cake-{i}.svg" for i in (1, 2, 3)]
_GALLERY_TTL = 60.0  # seconds


@dataclass(frozen=True)
class Photo:
    """A gallery entry: `thumb` for the grid, `full` for the lightbox. For the
    empty-gallery placeholder SVGs both are the same URL and `placeholder` is
    True, so the template can render them non-clickable (no lightbox)."""

    thumb: str
    full: str
    placeholder: bool = False


_PLACEHOLDER_PHOTOS = [Photo(thumb=u, full=u, placeholder=True) for u in _PLACEHOLDERS]
_gallery_cache: dict[str, tuple[float, list[Photo]]] = {}
_hero_cache: tuple[float, str | None] | None = None


def _list_photos(kind: str) -> list[str]:
    """Photo file names in a gallery dir, newest first (higher-numbered names
    are later uploads). The `thumbs` subdir is skipped by the suffix filter."""
    return sorted(
        (p.name for p in (_GALLERY_DIR / kind).glob("*") if p.suffix.lower() in _PHOTO_SUFFIXES),
        reverse=True,
    )


def _gallery(kind: str) -> list[Photo]:
    """Photos for a gallery, cached ~60 s.

    In production the directory is an NFS mount; listing it on every request
    would let a hung NAS block the sync page handlers and exhaust the
    threadpool (taking down the order form too). The cache touches the mount
    at most once per TTL, and on any listing error serves the last good result
    (or placeholders) so pages keep rendering through a NAS outage.
    """
    now = time.monotonic()
    cached = _gallery_cache.get(kind)
    if cached and now - cached[0] < _GALLERY_TTL:
        return cached[1]
    try:
        names = _list_photos(kind)
        # Thumbnails the initContainer produced; if one is missing, fall back to
        # the full image so the grid still shows something.
        thumbs = {p.name for p in (_GALLERY_DIR / kind / "thumbs").glob("*")}
        base = f"/static/img/gallery/{kind}"
        result = [
            Photo(
                thumb=f"{base}/thumbs/{name}" if name in thumbs else f"{base}/{name}",
                full=f"{base}/{name}",
            )
            for name in names
        ] or _PLACEHOLDER_PHOTOS
    except OSError:
        logger.exception("gallery listing failed for %s", kind)
        return cached[1] if cached else _PLACEHOLDER_PHOTOS
    _gallery_cache[kind] = (now, result)
    return result


def _hero_image() -> str | None:
    """Newest photo from the dedicated `hero/` dir for the faded homepage
    backdrop, or None (the template then shows the SVG). Cached like _gallery."""
    global _hero_cache
    now = time.monotonic()
    if _hero_cache and now - _hero_cache[0] < _GALLERY_TTL:
        return _hero_cache[1]
    try:
        names = _list_photos("hero")
        result = f"/static/img/gallery/hero/{names[0]}" if names else None
    except OSError:
        logger.exception("hero listing failed")
        return _hero_cache[1] if _hero_cache else None
    _hero_cache = (now, result)
    return result


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
    ctx = _ctx(
        request,
        min_due=orders.earliest_due_date().isoformat(),
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
        request,
        "index.html",
        _ctx(request, photos=_gallery("cakes")[:3], hero_image=_hero_image()),
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


# --- SEO: robots + sitemap ----------------------------------------------------

# Public, indexable pages (the token-bearing /verify URLs are deliberately out).
_SITEMAP_PATHS = [
    "/",
    "/tortak",
    "/desszertek",
    "/rolam",
    "/kapcsolat",
    "/ajanlatkeres",
    "/privacy",
]


@router.get("/robots.txt", include_in_schema=False)
def robots() -> Response:
    lines = ["User-agent: *", "Allow: /", "Disallow: /verify/"]
    if settings.base_url:
        lines.append(f"Sitemap: {settings.base_url}/sitemap.xml")
    return Response("\n".join(lines) + "\n", media_type="text/plain")


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap() -> Response:
    # One <url> per public page, each with hreflang alternates for the ?lang=
    # variants so search engines serve the right language.
    locales = list(enabled_locale_names())
    entries: list[str] = []
    for path in _SITEMAP_PATHS:
        loc = f"{settings.base_url}{path}"
        alts = "".join(
            f'<xhtml:link rel="alternate" hreflang="{code}" '
            f'href="{settings.base_url}{path}?lang={code}"/>'
            for code in locales
        )
        alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{loc}"/>'
        entries.append(f"<url><loc>{loc}</loc>{alts}</url>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(entries) + "</urlset>"
    )
    return Response(xml, media_type="application/xml")


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

    # 2) Signed render-timestamp: too fast (bot) or stale/forged. Pass the
    # validated data (errors included) so the re-render reflects what the user
    # actually entered — never silently re-tick an unchecked consent box.
    if not check_form_token(form_token):
        bad = validated()
        return form_page(data=bad, errors=bad.errors, banner="error.too_fast", status_code=400)

    # 3) Field validation.
    data = validated()
    if data.errors:
        return form_page(data=data, errors=data.errors, status_code=422)

    # 4) Rate limits (per IP, then per e-mail address). Commit the recorded
    # events immediately: a later mailer rollback must NOT erase them, or the
    # counters could never trip during an SMTP outage — exactly when they matter.
    ip = ratelimit.client_ip(x_forwarded_for, request.client.host if request.client else None)
    within_budget = ratelimit.allow(
        session, ratelimit.KIND_ORDER_IP, ip, settings.rate_max_per_ip
    ) and ratelimit.allow(
        session, ratelimit.KIND_ORDER_EMAIL, data.email, settings.rate_max_per_email
    )
    session.commit()
    if not within_budget:
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

    # Forward to cake-pricing FIRST (best-effort) so the chef e-mail can link to
    # the created draft. The row lock in find_by_token serializes concurrent hits
    # (an e-mail scanner prefetch can't double-forward). A rare retry after a
    # chef-mail failure could create a second draft — acceptable; the chef
    # deletes the duplicate.
    offer_id: int | None = None
    try:
        offer_id = backend.forward_order(order)
    except Exception:
        logger.exception("backend forward failed (continuing without a draft link)")
    offer_url = backend.pricing_offer_url(offer_id)

    # The chef e-mail is the primary delivery — confirm only if it sends.
    try:
        mailer.send_order_to_chef(order, offer_url)
    except mailer.MailerError:
        logger.exception("chef offer e-mail failed")
        session.rollback()
        return templates.TemplateResponse(
            request, "verify_failed.html", ctx | {"token": token}, status_code=502
        )
    orders.mark_confirmed(order)
    if offer_id is not None:
        backend.mark_forwarded(order)

    # Best-effort: customer confirmation.
    try:
        mailer.send_customer_confirmation(order)
    except mailer.MailerError:
        logger.exception("customer confirmation e-mail failed")

    return templates.TemplateResponse(request, "verified.html", ctx)
