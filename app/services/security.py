"""Signed-timestamp form token (bot defense, PLANNING §3.4).

The order form embeds an HMAC-signed render timestamp. On submit we require the
signature to be valid and the form age to be at least MIN_FILL_SECONDS (bots
post instantly) and at most one day (stale/replayed forms). Stateless — no
server-side session needed.
"""

from __future__ import annotations

import hashlib
import hmac
import time

from app.config import settings

_MAX_FORM_AGE_SECONDS = 86400


def _sig(ts: str) -> str:
    key = f"form-ts:{settings.rate_hash_salt}".encode()
    return hmac.new(key, ts.encode(), hashlib.sha256).hexdigest()


def issue_form_token() -> str:
    ts = str(int(time.time()))
    return f"{ts}.{_sig(ts)}"


def check_form_token(value: str | None) -> bool:
    if not value or "." not in value:
        return False
    ts, sig = value.split(".", 1)
    if not hmac.compare_digest(sig, _sig(ts)):
        return False
    try:
        age = time.time() - int(ts)
    except ValueError:
        return False
    return settings.min_fill_seconds <= age <= _MAX_FORM_AGE_SECONDS


def hash_value(value: str) -> str:
    """Salted SHA-256 for rate-limit keys — raw IPs/emails are never stored."""
    return hashlib.sha256(f"{settings.rate_hash_salt}:{value}".encode()).hexdigest()
