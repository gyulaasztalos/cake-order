"""SEO helpers: the JSON-LD structured-data block for the business.

The exact serialized string is shared with the CSP builder (main.py) so the
inline `<script type="application/ld+json">` can be allow-listed by its sha256
hash instead of loosening the policy with 'unsafe-inline'. Keep the string
construction deterministic (sorted keys) so the hash is stable across restarts.
"""

from __future__ import annotations

import base64
import hashlib
import json

from markupsafe import Markup

from app.config import settings


def _build() -> str:
    """Deterministic JSON-LD for the bakery. Sorted keys + compact separators so
    the byte content — and therefore its CSP hash — never drifts."""
    data = {
        "@context": "https://schema.org",
        "@type": "Bakery",
        "name": "Anita Tortái",
        "alternateName": "Anita Tortái — torta manufaktúra",
        "description": (
            "Egyedi, kézzel készített torták Szentendrén és környékén — "
            "születésnapi, esküvői és alkalmi torták rendelésre."
        ),
        "url": settings.base_url or "https://order.anitatortai.hu",
        "email": settings.order_inbox,
        "image": f"{settings.base_url}/static/img/logo-256.png",
        "logo": f"{settings.base_url}/static/img/logo-256.png",
        "areaServed": "Szentendre",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Szentendre",
            "addressRegion": "Pest",
            "addressCountry": "HU",
        },
        "sameAs": ["https://www.facebook.com/anitatortaihu/"],
        "servesCuisine": ["Torta", "Sütemény", "Desszert"],
        "priceRange": "$$",
    }
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# The canonical serialized string (hashed for CSP, rendered into the template).
STRUCTURED_DATA_JSON: str = _build()


def structured_data_json() -> Markup:
    """The JSON-LD as Markup so Jinja autoescaping leaves it byte-for-byte."""
    # Safe: STRUCTURED_DATA_JSON is our own json.dumps() output (no user input);
    # rendered byte-for-byte so its CSP hash matches.
    return Markup(STRUCTURED_DATA_JSON)  # noqa: S704  # nosec B704


def structured_data_csp_hash() -> str:
    """`sha256-<base64>` of the JSON-LD, for the CSP script-src allow-list."""
    digest = hashlib.sha256(STRUCTURED_DATA_JSON.encode("utf-8")).digest()
    return f"sha256-{base64.b64encode(digest).decode('ascii')}"
