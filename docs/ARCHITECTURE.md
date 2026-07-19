# cake-order — Architecture

Extended, self-contained documentation for humans and AI assistants who need to
add a feature or troubleshoot a bug. Pairs with the top-level
[`README.md`](../README.md) (what/how-to-run) and [`CLAUDE.md`](../CLAUDE.md)
(quick orientation). The private `PLANNING.md` (`§` references in code comments
point to it) is the original spec and is intentionally not in this public repo —
everything you need to work in the code is captured here.

---

## 1. The big picture

cake-order is a **public, stateless-ish web app** whose only real job is to turn
a customer's cake description into (a) a verified e-mail to the chef and (b) a
draft offer in the internal pricing app. The database is a **short-lived buffer**,
not an archive: rows exist only long enough to run the double-opt-in and are then
purged.

```
                         Cloudflare edge (TLS, WAF, Turnstile-ready)
                                     │  (Cloudflare Tunnel, outbound-only)
                                     ▼
   Visitor ──HTTP──▶  cake-order (FastAPI, k3s)  ──SMTP──▶  chef + customer mailboxes
                                     │
                                     ├──HTTP (bearer)──▶  cake-pricing intake API  (draft offer)
                                     ├────────────────▶  PostgreSQL (CNPG)         (pending buffer)
                                     └────────────────▶  Umami (optional)          (cookieless stats)
```

Two sibling apps share one design language and one ecosystem:

- **cake-order** (this repo) — public intake, no auth.
- **[cake-pricing](https://github.com/gyulaasztalos/cake-pricing)** — internal
  pricing/offer tool behind Authentik. cake-order calls its `/api/intake/offers`.
- **ArgoCD** repo — GitOps manifests (Deployment, Service, IngressRoute,
  NetworkPolicy, purge CronJob, Cloudflare tunnel config).
- **terraform-project** repo — Cloudflare DNS/tunnel/redirects.

## 2. Code layout

```
app/
  main.py            FastAPI factory: static mount, security-header middleware,
                     /healthz /readyz /metrics, router include, CSP builder.
  config.py          Settings — every knob from an env var (12-factor).
  db.py              Engine + SessionLocal + get_session() dependency.
  models.py          ORM: Order (the buffer) + RateEvent (abuse ledger).
  i18n.py            Dependency-free hu/en/de string catalogs + t(key, locale).
  templating.py      Jinja env, shared globals (contact_email, analytics, SEO…),
                     filters (date). Also the e-mail Jinja env.
  seo.py             JSON-LD business block + its CSP sha256 hash (shared).
  routers/orders.py  ALL public routes: pages, gallery, form POST, verify,
                     robots/sitemap.
  services/
    orders.py        Validation, token lifecycle, verification state machine.
    security.py      HMAC-signed form token; salted hash for rate keys.
    ratelimit.py     Sliding-window budgets over the RATE_EVENTS ledger.
    mailer.py        SMTP send of verify / chef / customer e-mails.
    backend.py       cake-pricing intake client (best-effort forward).
  jobs/purge.py      Retention job (run as a CronJob): GDPR minimization.
  templates/         Jinja pages + email/ subfolder (html + txt parts).
  static/            Pico.css + app.css, fonts, icons, gallery dirs, JS
                     (form.js, lightbox.js).
migrations/          Alembic (0001–0004).
tests/               pytest; DB-backed tests skip without DATABASE_URL.
```

## 3. Data model (2 tables)

Only two tables — see [`app/models.py`](../app/models.py).

### `orders` — the submission buffer
Lifecycle status: **pending → confirmed → forwarded** (or **expired**, set by the
retention job for dead pending rows before purge).

Key columns: customer fields (`name`, `email`, `phone?`, `due_date`,
`cake_type`, `flavor?`, `portions?`, `description`, `locale`, `consent_at`); and
the verification triple `token_hash` (SHA-256 hex — **the raw token is never
stored**), `token_expires_at`, `verified_at`, `forwarded_at`.

Invariants enforced in the DB (not just the app):
- `CHECK` on `status` and `char_length(description) <= 4000`.
- `UNIQUE(token_hash)`.
- **Partial unique index** `uq_orders_pending_email` — at most one *pending* row
  per e-mail (dedupe backstop; migration 0004).

### `rate_events` — append-only abuse ledger
`kind` (`order_ip` | `order_email`) + `key` = **salted SHA-256** of the IP or
e-mail. Raw IPs/e-mails are never persisted. Rows outside the rate window are
purged.

## 4. The two core flows

### 4.1 Submit (`POST /ajanlatkeres`) — [`routers/orders.py`](../app/routers/orders.py)

Ordered, fail-safe steps:

1. **Honeypot** — a hidden `website` field. If filled, return the normal success
   page and do nothing (never tip off the bot).
2. **Signed form token** — an HMAC of the render timestamp
   ([`services/security.py`](../app/services/security.py)). Rejected if the
   signature is bad, the form is younger than `MIN_FILL_SECONDS` (bots post
   instantly) or older than a day (stale/replayed). The re-render carries the
   user's real input back (never re-tick an unchecked consent box).
3. **Field validation** ([`services/orders.py`](../app/services/orders.py)) —
   returns i18n **error keys**, rendered by `t()` in the visitor's language.
   Notable: names are rejected if they contain control chars (they reach an
   e-mail `Subject`); lead time is checked against `earliest_due_date()` anchored
   to Budapest wall-clock.
4. **Rate limits** (per IP, then per e-mail). The recorded events are
   **committed immediately** — a later mailer rollback must not erase them, or
   the counters could never trip during an SMTP outage.
5. **Persist pending + send verification e-mail**. `create_or_refresh_pending`
   refreshes the existing pending row for an e-mail (new token) instead of
   piling up duplicates. If the mail send fails, the transaction is rolled back
   and the form re-renders with a banner.

### 4.2 Verify (`GET /verify/{token}`)

`find_by_token` hashes the raw token, looks it up, and **locks the row
`FOR UPDATE`** so concurrent hits (a real click racing an e-mail scanner's
link-prefetch) serialize. Returns `('ok' | 'already' | 'invalid', order)`.

On `ok`, in this deliberate order:

1. **Forward to cake-pricing first** (best-effort) so the chef e-mail can include
   a link to the created draft. A failure is logged and swallowed — the order
   stays recoverable.
2. **Chef e-mail is the primary delivery** — the order is marked `confirmed`
   only if the chef mail sends; otherwise roll back and show a retry page.
3. If forwarding returned an offer id, mark the order `forwarded`.
4. **Customer confirmation** e-mail — best-effort.

> Design tradeoff: a rare retry after a chef-mail failure could create a second
> cake-pricing draft (the intake POST is not idempotent). Accepted — the chef
> deletes the duplicate; the row lock prevents the common double-submit case.

## 5. Security model

This app is **public and unauthenticated**, so defense is layered:

- **Strict CSP** (built in [`app/main.py`](../app/main.py) `_build_csp()`):
  `default-src 'self'`, no inline JS ever. Two deliberate widenings:
  - the JSON-LD block is allow-listed by its **sha256 hash** (see
    [`app/seo.py`](../app/seo.py)); a test asserts the rendered bytes hash to the
    value in the header, so whitespace drift can't silently break it.
  - when analytics is configured, **only** the Umami origin is added to
    `script-src`/`connect-src`.
  Plus `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`.
  HSTS is added at the TLS-terminating edge, not here.
- **`/metrics` is 404'd on public hosts** (`PUBLIC_HOSTS`) so the tunnel can't
  expose Prometheus data; in-cluster scrapers reach it by service name.
- **Bot defense**: honeypot + signed form token + sliding-window rate limits;
  Turnstile is wired but disabled until spam demands it.
- **Data minimization**: token hash only; salted-hash rate keys; retention purge.
- **No open redirect**: the `?lang=` handler collapses anything that isn't a
  single-leading-slash path to `/`.
- **Header-injection guard**: control chars rejected in the name field.

When adding a feature, keep the CSP strict: put JS in an **external file** under
`/static/js/` (like `lightbox.js`) and wire it with `addEventListener`, never
inline `<script>` or `on*` attributes. A test (`tests/test_security.py`) fails if
inline script sneaks in.

## 6. i18n

Three catalogs (`hu`, `en`, `de`) in [`app/i18n.py`](../app/i18n.py); `t(key,
locale)` falls back to the key itself (visible in dev) then to Hungarian. Only
`ENABLED_LOCALES` are user-selectable. UI voice is **tegeződés** (informal) and
the chef speaks first person. Customers submit an *ajánlatkérés* (offer request),
never a *rendelés*. When you add a user-facing string, add all three locales.

## 7. Gallery, hero, SEO (recent additions)

- **Gallery** — `_gallery(kind)` returns `Photo(thumb, full, placeholder)`
  objects, cached ~60 s (a hung NFS mount must not block request handlers).
  The grid renders thumbnails; real photos are `<button>`s that open the
  lightbox; placeholder SVGs render as plain, non-clickable `<img>`. Thumbnails
  live in a `thumbs/` subdir produced by the deployment's init container.
- **Hero** — `_hero_image()` returns the newest `hero/` photo (or `None` → SVG),
  shown half-faded behind the headline via a CSS-positioned `<img>` (no inline
  style, to satisfy the CSP).
- **Lightbox** — [`static/js/lightbox.js`](../app/static/js/lightbox.js):
  prev/next, keyboard (←/→/Esc), focus restore, backdrop-click close.
- **SEO** — per-page `title`/`meta_desc` blocks (Hungarian keyword-targeted),
  `canonical` + `hreflang`, Open Graph, JSON-LD `Bakery`, and the
  `robots.txt`/`sitemap.xml` routes.

## 8. Analytics (Umami, optional)

Cookie-less, self-hosted. Activated **only** when both `ANALYTICS_SRC` and
`ANALYTICS_WEBSITE_ID` are set — then the tracker `<script>` (external file) is
rendered and the CSP is widened to its origin. Everything stays in the operator's
own Postgres; the privacy page copy switches to describe it. See the ArgoCD
`apps/umami/` deployment.

## 9. Deployment topology

- **Image**: multi-arch, `python:3.14-slim`, runs `uvicorn app.main:app` on
  `:8000`. Built on tag push; Renovate bumps the tag in the ArgoCD repo.
- **k3s / ArgoCD** (`apps/cake-order/install/`): Deployment (+ init container that
  copies gallery photos off NFS and generates thumbnails), Service, Traefik
  IngressRoute, a **NetworkPolicy** treating the pod as a DMZ, and a **purge
  CronJob** running `python -m app.jobs.purge`.
- **Public exposure**: a **Cloudflare Tunnel** (`cloudflared`, outbound-only — no
  open ports, no A record). TLS terminates at the Cloudflare edge; the origin leg
  is plain HTTP inside the cluster. Canonical host is the apex `anitatortai.hu`
  with a `www → apex` redirect at the edge.
- **Postgres**: a shared CloudNativePG cluster; credentials arrive via env from
  External Secrets Operator (1Password). `readyz` gates traffic on DB
  reachability.
- **Retention CronJob** enforces `PENDING_RETENTION_HOURS` /
  `CONFIRMED_RETENTION_DAYS` (keys pending purge on `update_date` so a fresh
  re-submit isn't deleted while its link is still valid).

## 10. Gotchas & conventions

- **Python 3.14 target.** `except A, B:` without parentheses is valid (PEP 758);
  `ruff format` strips the redundant parens — this is correct, not a bug.
- **Commit-before-redirect / commit-before-ack.** DB durability must precede any
  externally observable success (a 303 redirect, or the intake 201). See the
  rate-event commit and the verify flow.
- **`get_session()`** commits in its post-yield teardown; where a later step must
  see the write (or an external party is told it succeeded), commit explicitly.
- **CI parity.** `.github/workflows/ci.yml` must stay equivalent to cake-pricing's
  (Postgres service + `alembic upgrade head` so DB tests actually run).
- **Testing.** DB-backed tests skip without `DATABASE_URL`. Under machine load,
  prefer `.venv/bin/python -m pytest`. Run one test:
  `uv run pytest tests/test_order_flow.py -q`.
