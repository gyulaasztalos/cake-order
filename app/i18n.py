"""Minimal i18n layer — externalized UI strings from day one.

Same pattern as the sibling app: per-locale dicts + a `t(key, locale)` lookup.
Dependency-free; can be swapped for gettext/Babel without touching call sites.
Hungarian is the default; English and German are selectable on the page.
"""

from __future__ import annotations

from app.config import settings

# Keys are dotted, stable identifiers (never shown raw).
HU: dict[str, str] = {
    "app.title": "Anita tortái — Tortarendelés",
    "app.tagline": "Egyedi torták, szeretettel készítve",
}

EN: dict[str, str] = {
    "app.title": "Anita's Cakes — Cake Order",
    "app.tagline": "Custom cakes, made with love",
}

DE: dict[str, str] = {
    "app.title": "Anitas Torten — Tortenbestellung",
    "app.tagline": "Individuelle Torten, mit Liebe gemacht",
}

CATALOGS: dict[str, dict[str, str]] = {"hu": HU, "en": EN, "de": DE}
SUPPORTED_LOCALES = tuple(CATALOGS)


def resolve_locale(value: str | None) -> str:
    """Clamp any user-supplied locale to the supported set (never trust input)."""
    return value if value in CATALOGS else settings.default_locale


def t(key: str, locale: str | None = None, **kwargs: object) -> str:
    """Translate a key. Falls back to Hungarian, then the key itself (visible in dev)."""
    cat = CATALOGS.get(locale or settings.default_locale, HU)
    text = cat.get(key) or HU.get(key, key)
    return text.format(**kwargs) if kwargs else text
