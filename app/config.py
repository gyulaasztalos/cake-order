"""App configuration from environment (12-factor).

Every knob is env-driven so the same image runs in k3s and at a provider
(PLANNING.md — hosting portability). Secrets (SMTP password, DB creds) arrive
via env from the secret store; nothing sensitive lives here.
"""

from __future__ import annotations

import os


class Settings:
    app_env: str = os.getenv("APP_ENV", "prod")
    # Public base URL — verification links are built from this.
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
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
    min_lead_days: int = int(os.getenv("MIN_LEAD_DAYS", "3"))

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
    mail_from: str = os.getenv("MAIL_FROM", "rendeles@anitatortai.hu")
    order_inbox: str = os.getenv("ORDER_INBOX", "info@anitatortai.hu")

    # --- phase 2: cake-pricing intake API (§6) ---
    backend_enabled: bool = os.getenv("BACKEND_ENABLED", "false").lower() == "true"
    backend_url: str = os.getenv("BACKEND_URL", "")
    backend_token: str = os.getenv("BACKEND_TOKEN", "")


settings = Settings()
