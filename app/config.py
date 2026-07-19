"""App configuration from environment (12-factor).

Every knob is env-driven so the same image runs in k3s and at a provider
(PLANNING.md — hosting portability). Secrets (SMTP password, DB creds) arrive
via env from the secret store; nothing sensitive lives here.
"""

from __future__ import annotations

import os
from urllib.parse import urlsplit


class Settings:
    app_env: str = os.getenv("APP_ENV", "prod")
    # Public base URL — verification links are built from this. Canonical apex;
    # a www→apex redirect at the edge keeps links consistent.
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
    # Public Host headers (the tunnel hostnames). /metrics is 404'd for these so
    # the public edge can't scrape Prometheus data; in-cluster scrapers use the
    # service name/IP and are unaffected. Comma-separated; apex + www.
    public_hosts: frozenset[str] = frozenset(
        h.strip().lower()
        for h in os.getenv("PUBLIC_HOSTS", "anitatortai.hu,www.anitatortai.hu").split(",")
        if h.strip()
    )
    # Default UI language; hu/en/de catalogs ship from day one, but only the
    # locales listed here are selectable (de is built yet disabled at launch).
    default_locale: str = os.getenv("APP_LOCALE", "hu")
    enabled_locales: tuple[str, ...] = tuple(
        code.strip() for code in os.getenv("ENABLED_LOCALES", "hu,en").split(",") if code.strip()
    )

    # --- form limits (§3.1) ---
    name_max: int = int(os.getenv("NAME_MAX", "120"))
    phone_max: int = int(os.getenv("PHONE_MAX", "32"))
    description_max: int = int(os.getenv("DESCRIPTION_MAX", "2000"))
    min_lead_days: int = int(os.getenv("MIN_LEAD_DAYS", "7"))

    # --- verification (§3.2) ---
    token_ttl_hours: int = int(os.getenv("TOKEN_TTL_HOURS", "24"))

    # --- retention (§3.5, GDPR minimization) ---
    pending_retention_hours: int = int(os.getenv("PENDING_RETENTION_HOURS", "48"))
    confirmed_retention_days: int = int(os.getenv("CONFIRMED_RETENTION_DAYS", "30"))

    # --- bot defense (§3.4) ---
    # Minimum seconds between form render and submit (bots post instantly).
    min_fill_seconds: int = int(os.getenv("MIN_FILL_SECONDS", "3"))
    # Sliding-window budgets: max POST /order per IP and per email address.
    rate_window_minutes: int = int(os.getenv("RATE_WINDOW_MINUTES", "60"))
    rate_max_per_ip: int = int(os.getenv("RATE_MAX_PER_IP", "5"))
    rate_max_per_email: int = int(os.getenv("RATE_MAX_PER_EMAIL", "3"))
    # Salt for hashing IPs/emails in RATE_EVENTS (never stored raw).
    rate_hash_salt: str = os.getenv("RATE_HASH_SALT", "dev-only-salt")
    # Cloudflare Turnstile — wired but disabled until spam demands it.
    turnstile_enabled: bool = os.getenv("TURNSTILE_ENABLED", "false").lower() == "true"
    turnstile_site_key: str = os.getenv("TURNSTILE_SITE_KEY", "")
    turnstile_secret_key: str = os.getenv("TURNSTILE_SECRET_KEY", "")

    # --- email (§3.3) ---
    smtp_host: str = os.getenv("SMTP_HOST", "localhost")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    # starttls (587) | tls (465) | plain (25, dev mail-catcher only)
    smtp_security: str = os.getenv("SMTP_SECURITY", "starttls")
    # iCloud Mail only sends as the account address or a configured alias.
    mail_from: str = os.getenv("MAIL_FROM", "info@anitatortai.hu")
    order_inbox: str = os.getenv("ORDER_INBOX", "info@anitatortai.hu")

    # --- phase 2: cake-pricing intake API (§6) ---
    backend_enabled: bool = os.getenv("BACKEND_ENABLED", "false").lower() == "true"
    backend_url: str = os.getenv("BACKEND_URL", "")
    backend_token: str = os.getenv("BACKEND_TOKEN", "")
    # Public base URL of the internal cake-pricing UI, used ONLY to build the
    # chef's "open the draft" link in the order e-mail (e.g.
    # https://torta.local.asztalos.net). Empty = no link.
    pricing_base_url: str = os.getenv("PRICING_BASE_URL", "").rstrip("/")

    # --- self-hosted, cookieless visitor analytics (Umami) ---
    # Enabled only when a script URL is configured. ANALYTICS_SRC is the full
    # URL of the Umami tracker (e.g. https://stats.anitatortai.hu/script.js);
    # ANALYTICS_WEBSITE_ID is the site UUID from the Umami dashboard. When set,
    # the tracker's origin is added to the CSP script-src/connect-src so the
    # otherwise self-only policy still loads it.
    analytics_src: str = os.getenv("ANALYTICS_SRC", "").strip()
    analytics_website_id: str = os.getenv("ANALYTICS_WEBSITE_ID", "").strip()

    @property
    def analytics_enabled(self) -> bool:
        return bool(self.analytics_src and self.analytics_website_id)

    @property
    def analytics_origin(self) -> str:
        """Scheme+host of the analytics script, for the CSP allow-list. Empty
        if analytics is off or the URL is not absolute (never widens the CSP
        to a bare path)."""
        if not self.analytics_enabled:
            return ""
        parts = urlsplit(self.analytics_src)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            return ""
        return f"{parts.scheme}://{parts.netloc}"


settings = Settings()
