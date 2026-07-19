# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Public, customer-facing **cake order-intake** web app (FastAPI + SQLAlchemy +
Jinja + Pico.css, Python 3.14, packaged with `uv`). Sibling of the internal
**cake-pricing** app; deployed to a k3s HomeLab via the **ArgoCD** repo and
exposed through a Cloudflare Tunnel. For the full picture read
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); user-facing overview is
[`README.md`](README.md). The original spec lives in a **private** `PLANNING.md`
(the `§` refs in comments) — not in this repo.

## Commands

```bash
uv sync                                   # install from uv.lock
uv run uvicorn app.main:app --reload      # dev server on :8000
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest                             # full suite
uv run pytest tests/test_seo.py -q        # a single test file
uv lock                                   # after editing pyproject deps (commit the lock)
```

**DB-backed tests skip without `DATABASE_URL`.** To run them:

```bash
podman run -d --name cakeorderpg -e POSTGRES_PASSWORD=devpass -e POSTGRES_USER=cake \
  -e POSTGRES_DB=cake-order -p 55433:5432 postgres:18
export DATABASE_URL="postgresql+psycopg://cake:devpass@localhost:55433/cake-order"
uv run alembic upgrade head
```

If `uv run` is flaky under pyenv, call venv binaries directly
(`.venv/bin/python -m pytest`, `.venv/bin/mypy`). Under heavy machine load, test
imports can be slow — be patient rather than assuming a hang.

## Architecture in one screen

- All public routes live in [`app/routers/orders.py`](app/routers/orders.py):
  content pages, gallery, `POST /ajanlatkeres` (submit), `GET /verify/{token}`,
  `robots.txt`/`sitemap.xml`.
- Business logic is in `app/services/` (`orders`, `security`, `ratelimit`,
  `mailer`, `backend`), config in [`app/config.py`](app/config.py), strings in
  [`app/i18n.py`](app/i18n.py), Jinja wiring + globals in
  [`app/templating.py`](app/templating.py), SEO/JSON-LD in
  [`app/seo.py`](app/seo.py).
- **Two DB tables** ([`app/models.py`](app/models.py)): `orders` (a short-lived
  buffer, `pending→confirmed→forwarded`) and `rate_events` (salted-hash abuse
  ledger). The retention job [`app/jobs/purge.py`](app/jobs/purge.py) deletes
  old rows.
- Flow: form → validate → rate-limit → pending row + verification e-mail →
  customer clicks link → forward to cake-pricing (best-effort) + chef e-mail
  (primary) + customer confirmation.

## Conventions & invariants (don't break these)

- **Strict CSP, no inline JS.** Put scripts in `app/static/js/*.js` and wire with
  `addEventListener`; never inline `<script>`/`on*`. `tests/test_security.py`
  fails otherwise. New inline JSON-LD or scripts must be hash/nonce-allow-listed
  in `_build_csp()` (see `app/seo.py` for the pattern).
- **Every user-facing string goes through `t()`** with all three locales
  (`hu`/`en`/`de`) added. Hungarian voice is informal (*tegeződés*); customers
  send an *ajánlatkérés*, never a *rendelés*.
- **Commit before any externally observable success** (303 redirect, intake ack).
  Rate events are committed before mailing; the chef e-mail is the primary
  delivery and gates the `confirmed` status.
- **Secrets/PII**: only the SHA-256 of the verification token is stored; raw
  IPs/e-mails are never persisted. Keep it that way.
- **`MIN_LEAD_DAYS` and all limits are env-driven** — read `settings.*`, don't
  hardcode. Templates already interpolate `{days}` from `settings.min_lead_days`.
- **CI parity** with cake-pricing (Postgres service + `alembic upgrade head`);
  keep `.github/workflows/ci.yml` equivalent.
- **Python 3.14**: `except A, B:` without parens is valid (PEP 758) — ruff
  formatting that removes the parens is correct.

## Gallery photos

`.gitignore`d and never committed. Locally drop JP/PNG/WebP into
`app/static/img/gallery/{cakes,desserts,hero}/`; in prod they're an NFS mount and
an init container generates the `thumbs/` variants. `_gallery()` returns `Photo`
objects (thumb + full + placeholder); placeholders are non-clickable.
