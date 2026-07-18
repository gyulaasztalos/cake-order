# cake-order

Public, customer-facing **cake order intake webapp** for a one-person pastry business
([anitatortai.hu](https://www.facebook.com/anitatortaihu/)). One function only:
a customer describes the cake they want; the order is e-mail-verified (tokenized
link), then delivered to the chef as a nicely formatted e-mail — and later as a
draft offer in the internal pricing app.

> Design & requirements live in a **private** planning doc (not in this public repo).

## Stack

FastAPI · SQLAlchemy 2.0 · Alembic · Jinja + HTMX · Pico.css · PostgreSQL. Packaged with
**uv**, built as a multi-arch (amd64 + arm64) Docker image, deployed via ArgoCD GitOps.

Hungarian UI by default, English and German selectable. No accounts, no login —
the only gate is e-mail verification of the submitted order.

## Local development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync                       # create .venv from uv.lock
uv run uvicorn app.main:app --reload
# http://localhost:8000  ·  /healthz  ·  /readyz
uv run pytest                 # tests
uv run ruff check .           # lint
uv run mypy                   # types
```

If you change dependencies in `pyproject.toml`, regenerate the lockfile and commit it:

```bash
uv lock
```

## Docker

```bash
docker build -t cake-order:dev .
docker run --rm -p 8000:8000 cake-order:dev
```

## Releases (CI/CD)

Every push/PR runs the test workflow (ruff, mypy, pytest, bandit, pip-audit).
Pushing a semver tag builds and pushes a multi-arch image to Docker Hub
(`asztalosgyula/cake-order`) and GHCR (`ghcr.io/gyulaasztalos/cake-order`):

```bash
git tag v0.1.0
git push origin v0.1.0
```

Renovate in the ArgoCD repo then bumps the deployed image tag → ArgoCD syncs to the cluster.

## Endpoints

| Path              | Purpose                                        |
|-------------------|------------------------------------------------|
| `/`               | Order form (public)                            |
| `/order`          | Form submission (POST)                         |
| `/verify/{token}` | E-mail verification link → order confirmation  |
| `/privacy`        | Privacy notice (GDPR)                          |
| `/healthz`        | Liveness probe (no deps)                       |
| `/readyz`         | Readiness incl. dependencies (DB)              |
| `/metrics`        | Prometheus metrics                             |
