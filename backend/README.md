# mind2code-backend

FastAPI REST API for **Mind2Code**. Serves the project portfolio and streams live completion updates via Server-Sent Events.

## Tech stack

| Technology | Notes |
| --- | --- |
| Python | `^3.12` |
| FastAPI | `^0.110.0` |
| SQLAlchemy 2.0 (async) + asyncpg | PostgreSQL access with raw SQL |
| Pydantic / pydantic-settings | Models and configuration |
| dependency-injector | DI container |
| Poetry | Dependency management (`create = false`) |
| yoyo-migrations | SQL migrations (dev) |
| Uvicorn | ASGI server |
| python-json-logger | Structured request/broadcast logs |

## Project structure

```
.
├── src/
│   ├── main.py                  # FastAPI app, DI wiring, router include
│   ├── di.py                    # dependency-injector container
│   ├── config/
│   │   ├── app_config.py        # pydantic-settings
│   │   └── logger.py            # JSON logging setup
│   ├── clients/postgres_client.py
│   ├── db/models/               # Pydantic models (mirror the schema)
│   ├── repositories/            # queries.py (raw SQL) + data access
│   ├── services/                # business logic
│   ├── routers/                 # API endpoints + health
│   └── sse/broker.py            # in-process SSE fan-out
├── migrations/                  # yoyo SQL migrations
├── pyproject.toml / poetry.toml
├── .env.example
└── Dockerfile
```

## Configuration

Copy `.env.example` to `.env` and fill in the values:

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | PostgreSQL async connection URI (`postgresql+asyncpg://...`) |
| `CORS_ORIGINS` | JSON array of allowed origins, e.g. `["http://localhost:5173"]` |
| `LOG_LEVEL` | *(optional)* Python logging level (default `INFO`) |

## Local development

```sh
poetry install
cp .env.example .env
yoyo apply --database postgresql://appuser:post-password@localhost:5432/mind2code ./migrations
poetry run python src/main.py
```

OpenAPI docs are available at `http://localhost:8000/docs`.

## API

All endpoints are prefixed with `/api/v1`, except the health check.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/projects` | List all projects |
| `GET` | `/api/v1/events` | SSE stream (`text/event-stream`) |
| `POST` | `/api/v1/projects/{executionId}/progress` | Update completion percentage |

### SSE event contract

- Event type: `progress`
- Payload: `{"executionId": <int>, "completionPercentage": <int>}`
- Heartbeat comment (`: heartbeat`) is sent at least every 15 seconds.

## Migrations

```sh
yoyo apply  --database <db_url> ./migrations   # apply
yoyo list   --database <db_url> ./migrations   # show status
yoyo rollback --database <db_url> ./migrations # roll back the last one
```

## Docker

```sh
docker build -t mind2code-backend .
docker run -p 8000:8000 -e DATABASE_URL=<async_db_url> -e CORS_ORIGINS='["http://localhost:5173"]' mind2code-backend
```
