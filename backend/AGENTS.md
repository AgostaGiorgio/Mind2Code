# AGENTS.md — mind2code-backend

## Structure

- `src/` — FastAPI backend (Python, Poetry), **no `__init__.py`** (namespace packages).
- Layers: `routers/` -> `services/` -> `repositories/` -> `clients/postgres_client.py`
  -> `repositories/queries.py` (raw SQL).
- `src/db/models/` — Pydantic models mirroring the SQL schema (no ORM).
- `migrations/` — raw SQL migrations applied with **yoyo**.
- Not a monorepo tooling setup: no tests, no CI/CD in-repo.

## Backend

- **Deps:** Poetry with `poetry.toml` setting `create = false` (installs into the
  active environment, no in-project virtualenv).
- **Start (dev):** `poetry run python src/main.py` (also `uvicorn src.main:app --reload --port 8000`).
- **Start (Docker):** `poetry run uvicorn src.main:app --port 8000 --host 0.0.0.0`.
- **Migrations:** `yoyo apply --database <db_url> ./migrations`.
- **Config:** `pydantic-settings` reads from `.env`; optional `config.yaml` overrides.
- **DB:** Async SQLAlchemy + asyncpg; raw SQL via `text()` in
  `src/repositories/queries.py`, referenced as `q.NAME`.
- **DI:** `dependency-injector` wires `<entity>_service` into routers
  (`src/di.py`); routers use `@inject` + `Depends(Provide[Container.x_service])`.
- **Version:** read from `pyproject.toml` `[tool.poetry].version` via `tomli`.
- No linter/formatter config exists.

## Conventions

- Repository methods open a session with `self.__postgres_client.async_session()`;
  multi-statement writes go inside `async with session.begin():`.
- Catch narrowly: `except (SQLAlchemyError, ValidationError) as e:` with
  `exc_info=True`; never `except Exception`.
- Reads return `[]` / `None`; writes return the entity / `True` / `False` / `None`;
  routers map to 404/400.
- API prefix: `/api/v1`.

## Example slice (remove when you add real models)

The `items` entity is a working end-to-end example. When adding the first real
resource, delete/replace `src/db/models/item.py`, `src/repositories/items.py`,
`src/services/items.py`, the items endpoints in `src/routers/router.py`, the
`item_*` providers in `src/di.py`, the `items` statements in
`src/repositories/queries.py`, and migration `0001`.

## Skills

For DB-layer work use the `async-db-repository` skill; for schema/model changes
use `yoyo-sql-migrations`; for Orbit registration use `orbit-registration`.
