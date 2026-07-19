"""Jinja environment + shared template globals/filters."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import __version__
from app.config import settings
from app.i18n import t

TEMPLATES_DIR = Path(__file__).parent / "templates"

_LOCAL_TZ: ZoneInfo | None
try:
    _LOCAL_TZ = ZoneInfo("Europe/Budapest")
except ZoneInfoNotFoundError:  # pragma: no cover - fallback if tzdata missing
    _LOCAL_TZ = None


def format_date(value: dt.datetime | dt.date | None) -> str:
    """Hungarian standard date: YYYY-MM-DD."""
    if value is None:
        return "—"
    if isinstance(value, dt.datetime) and _LOCAL_TZ is not None and value.tzinfo is not None:
        value = value.astimezone(_LOCAL_TZ)
    return value.strftime("%Y-%m-%d")


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# E-mail rendering: autoescape must apply to .html bodies but NOT to .txt
# alternatives (plain text with HTML entities would be garbage).
email_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)
email_env.globals["t"] = t
email_env.filters["date"] = format_date
templates.env.globals["t"] = t
templates.env.globals["default_locale"] = settings.default_locale
templates.env.globals["app_env"] = settings.app_env
templates.env.globals["version"] = __version__
templates.env.globals["year"] = dt.date.today().year
# The public contact address, env-driven (same ORDER_INBOX the mailer sends to).
templates.env.globals["contact_email"] = settings.order_inbox
templates.env.filters["date"] = format_date
