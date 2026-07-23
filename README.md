# cake-order

Public, customer-facing **cake order-intake webapp** for the one-person pastry
business *Anita Tortái* — a *cukrász manufaktúra* in Szentendre, Hungary
([anitatortai.hu](https://www.facebook.com/anitatortaihu/)).

One job, done well: a customer describes the cake they want; the request is
**e-mail-verified** (tokenized link), then delivered to the chef as a formatted
e-mail **and** pushed into the internal pricing app ([cake-pricing](https://github.com/gyulaasztalos/cake-pricing))
as a draft offer. No accounts, no login — the only gate is verifying the e-mail
address on the submitted request.

> **Design & requirements** live in a **private** `PLANNING.md` (not in this
> public repo). This README plus [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
> are the public, self-contained documentation. AI assistants: start with
> [`CLAUDE.md`](CLAUDE.md).

## What it does

- **Multi-page marketing site** — landing/hero, cake & dessert galleries, about,
  contact, privacy — Hungarian by default, English selectable (German catalog
  ships but is disabled at launch).
- **Offer-request form** (`/ajanlatkeres`) with server-side validation and
  layered bot defense (honeypot + signed form-timestamp + per-IP/e-mail rate
  limits; Cloudflare Turnstile wired but off).
- **Double opt-in**: a submission is *pending* until the customer clicks the
  verification link; only then are e-mails sent and the draft forwarded.
- **Gallery with lightbox** — thumbnails in a grid, click for a full-size
  overlay viewer with prev/next; a half-faded hero photo behind the headline.
- **GDPR-minded**: only a SHA-256 digest of the token is stored; raw IPs/e-mails
  are never persisted (salted-hash rate ledger); a retention CronJob purges old
  rows; a cookie-less analytics option (Umami).
- **SEO**: per-page titles/descriptions, canonical + `hreflang`, Open Graph,
  JSON-LD `Bakery` (allow-listed by hash under a strict CSP), `sitemap.xml`,
  `robots.txt`.

## Stack

FastAPI · SQLAlchemy 2.0 · Alembic · Jinja + a little HTMX · Pico.css ·
PostgreSQL · Python 3.14. Packaged with **uv**, built as a multi-arch
(amd64 + arm64) Docker image, deployed to a k3s HomeLab via **ArgoCD** GitOps,
and exposed publicly through a **Cloudflare Tunnel** (no open ports).

## Local development

Requires [uv](https://docs.astral.sh/uv/) and a PostgreSQL for the DB-backed
tests (the app also boots without one — pages render; DB routes need it).

```bash
uv sync                                   # create .venv from uv.lock
uv run uvicorn app.main:app --reload      # http://localhost:8000

# quality gates (what CI runs)
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest
```

### Database for tests

DB-backed tests are skipped unless `DATABASE_URL` is set. Spin up Postgres and
apply migrations:

```bash
podman run -d --name cakeorderpg -e POSTGRES_PASSWORD=devpass -e POSTGRES_USER=cake \
  -e POSTGRES_DB=cake-order -p 55433:5432 postgres:18
export DATABASE_URL="postgresql+psycopg://cake:devpass@localhost:55433/cake-order"
uv run alembic upgrade head
uv run pytest                             # run a single test: uv run pytest tests/test_seo.py -q
```

> If `uv run` is flaky under a pyenv shell, call the venv binaries directly:
> `.venv/bin/python -m pytest`, `.venv/bin/mypy`, etc.

If you change dependencies in `pyproject.toml`, regenerate and commit the lock:
`uv lock`.

## Gallery photos

Photos are **never committed** (this repo is public) — `.gitignore` keeps
`app/static/img/gallery/{cakes,desserts}/` empty except a `.gitkeep`. The pages
auto-list whatever JPG/PNG/WebP files are present, newest first.

- **Locally**: drop photos into those folders; the grid falls back to the
  full-size images (no thumbnails are generated in dev).
- **In production**: the folders come from a **read-only NFS mount** off the NAS.
  An init container copies them to pod-local disk **and** generates a `thumbs/`
  variant of each (grid = thumbnail, lightbox = full size). Managing photos =
  copying files onto the share, then restarting the pod.
- **Hero backdrop**: the newest photo in a `hero/` folder is shown half-faded
  behind the landing headline; if empty, a placeholder SVG is used.

## Docker

```bash
docker build -t cake-order:dev .
docker run --rm -p 8000:8000 cake-order:dev   # CMD runs uvicorn on :8000
```

## Releases (CI/CD)

Every push/PR runs the workflow: `ruff check` + `ruff format --check`, `mypy`,
`alembic upgrade head` against a Postgres service, `pytest`, plus `bandit` and
`pip-audit`. Pushing a semver tag builds and pushes a multi-arch image to Docker
Hub (`asztalosgyula/cake-order`) and GHCR (`ghcr.io/gyulaasztalos/cake-order`):

```bash
git tag v1.0.0 && git push origin v1.0.0
```

Renovate in the ArgoCD repo then bumps the deployed image tag → ArgoCD syncs it
to the cluster.

## Endpoints

| Path              | Method | Purpose                                              |
|-------------------|--------|------------------------------------------------------|
| `/`               | GET    | Landing page (hero, why-me, gallery preview, steps)  |
| `/tortak`         | GET    | Cakes gallery (lightbox)                             |
| `/desszertek`     | GET    | Desserts gallery (lightbox)                          |
| `/rolam`          | GET    | About                                               |
| `/kapcsolat`      | GET    | Contact                                             |
| `/ajanlatkeres`   | GET    | Offer-request form                                  |
| `/ajanlatkeres`   | POST   | Form submission → pending order + verification mail |
| `/verify/{token}` | GET    | E-mail verification → forward + chef/customer mail  |
| `/privacy`        | GET    | Privacy notice (GDPR)                               |
| `/robots.txt`     | GET    | Crawl rules + sitemap pointer                       |
| `/sitemap.xml`    | GET    | Sitemap with `hreflang` alternates                  |
| `/healthz`        | GET    | Liveness (no deps)                                  |
| `/readyz`         | GET    | Readiness (checks DB)                               |
| `/metrics`        | GET    | Prometheus metrics (404'd on public hosts)          |

`?lang=hu|en|de` on any GET page persists the language in a cookie and redirects
to the clean URL.

## Configuration

All behavior is env-driven (12-factor); see [`app/config.py`](app/config.py) for
the full list and defaults. Highlights: `BASE_URL`, `PUBLIC_HOSTS`,
`ENABLED_LOCALES`, `MIN_LEAD_DAYS` (default **7**), `TOKEN_TTL_HOURS`,
`PENDING_RETENTION_HOURS` / `CONFIRMED_RETENTION_DAYS`, the `SMTP_*` group,
`BACKEND_*` (cake-pricing intake), `PRICING_BASE_URL`, and `ANALYTICS_*` (Umami).

## Where to read next

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — request flows, data model,
  security model, deployment topology, and gotchas.
- [`CLAUDE.md`](CLAUDE.md) — orientation for AI assistants (commands, layout,
  invariants).

## License

© 2026 Gyula Asztalos. Licensed under the **GNU Affero General Public License v3.0**
(AGPL-3.0) — see [`LICENSE`](LICENSE). Because this is a network application, the AGPL's
§13 applies: if you run a modified version as a service, you must offer its users the
corresponding source. The source is at <https://github.com/gyulaasztalos/cake-order>.
