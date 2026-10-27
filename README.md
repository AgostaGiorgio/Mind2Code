# Mind2Code

A single-user, mobile-first web application that tracks a portfolio of projects and streams live completion-percentage updates via Server-Sent Events (SSE).

## Monorepo layout

```
.
├── backend/   # FastAPI + Uvicorn + SQLAlchemy async + PostgreSQL
├── frontend/  # Vue 3 + Vite + TypeScript + Tailwind CSS
└── README.md
```

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.0 (async), asyncpg, dependency-injector, yoyo-migrations, Pydantic |
| Frontend | Node.js 20+, Vue 3, Vite, TypeScript, Tailwind CSS, axios, vue-router |
| Database | PostgreSQL 15+ |

## API contract

All REST endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/projects` | List all projects (lean payload) |
| `POST` | `/api/v1/projects` | Create a project (`userInput`, `auto`): n8n title extraction → DB insert → n8n requirements trigger — 201 |
| `GET` | `/api/v1/projects/{projectId}` | Fetch a single project with its documents (`finalReview`, `userInput`, `requirements`, `codeSummary`, `testSummary`) |
| `PATCH` | `/api/v1/projects/{projectId}` | Rename a project (`{ "name": "..." }`) |
| `POST` | `/api/v1/projects/{projectId}/finalize` | Start finalization (release) — 204 |
| `GET` | `/api/v1/events` | SSE stream (`text/event-stream`) |
| `POST` | `/api/v1/projects/{projectId}/progress` | Update a project's completion percentage |

Project identifiers are the UUIDs in `projects.id` (migration `0007` removed the
old integer `execution_id`).

### Project list and detail page

The dashboard renders a **single card containing one row per project** (name,
GitHub icon, and a **Status** column with the completion ring next to the
finalization control — a rocket to release, an orange ring while in progress, or
a warning icon on error). Clicking anywhere on a row (except the GitHub icon and
the finalize control) navigates to `/projects/{projectId}`; the chevron is the
keyboard-accessible target.

The detail page fetches the project with `GET /api/v1/projects/{projectId}` and
shows its header plus a **pipeline bar** with one step per phase, in order:
**User Input → Requirements → Code → Tests → Review → Retrospective**. Each step
has a dot that turns green when its document has content and is disabled
otherwise; the selected phase is rendered from Markdown below the bar. On load
the last available phase is selected, and it keeps following new phases as they
arrive over SSE until the user picks an earlier one. The header shows a single
ring with the completion (violet, outer arc) and, once the release has started or
finished, the finalization (orange, inner arc) percentages — no numbers inside.
Projects created with `auto = true` also show an **Auto** badge next to the
title.
The project name can be edited inline from the detail page header. The document
`TEXT` columns
(`user_input`, `requirements`, `code-summary`, `test-summary`, `review`,
`retrospective`) live on the `projects` table (migrations `0002`, `0003` and
`0005`) and are populated by the external service, like the completion
percentage.

### Creating a project

The dashboard's **New** action opens a bottom sheet with two inputs:

- **User input** (required): the free-form brief used by the pipeline.
- **Auto** (default `false`): tells the external pipeline whether to run every
  step automatically, one after the other.

`POST /api/v1/projects` runs three steps:

1. **Title extraction** — POSTs `{"user_input": "..."}` to
   `N8N_PROJECT_TITLE_WEBHOOK_URL`; the workflow must answer with
   `{"project_title": "..."}` (trimmed and truncated to 200 chars).
2. **Insert** — writes the row with that title, the user input and the `auto`
   flag; the database generates the row UUID (`projects.id`), which becomes the
   only project identifier. `github_url` stays empty until the pipeline fills it.
3. **Requirements** — POSTs `{"project_id": "<projects.id UUID>"}` to
   `N8N_REQUIREMENTS_WEBHOOK_URL`; the `200` response body is ignored.

If the title webhook is not configured or fails, creation is aborted
(`503` / `502`) and no row is written. If the requirements webhook fails, the
project is still created (`201`) and the error is only logged, because retrying
would insert a duplicate row. The `auto` flag is stored in the
`auto BOOLEAN NOT NULL DEFAULT FALSE` column (migration `0006`).

The UI navigates immediately to `/projects/new`, which renders a detail-page
skeleton (header, phase bar and document placeholders) while the title webhook
runs. On success the route is replaced with `/projects/{projectId}`; on
failure the page shows the error with **Retry** and **Back to projects**.

### SSE event contract

- Endpoint: `GET /api/v1/events`
- Headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`
- Event types: `progress` and `finalization`

`progress` payload (JSON):

```json
{
  "projectId": "11111111-1111-4111-8111-111111111111",
  "completionPercentage": 75,
  "status": "CODE_RUNNING"
}
```

`finalization` payload (JSON):

```json
{
  "projectId": "11111111-1111-4111-8111-111111111111",
  "finalizationPercentage": 60,
  "finalRepoUrl": null,
  "finalizeError": null
}
```

A heartbeat comment (`: heartbeat`) is sent at least every 15 seconds to keep proxies from closing an idle connection.

### Progress ingestion

Completion updates can reach the backend in two ways:

1. **External writer (primary).** A separate service updates the `projects` rows
   directly in PostgreSQL. A background poller in the backend (`ProgressPoller`)
   reads the rows whose `updated_at` moved past a watermark every
   `POLL_INTERVAL_SECONDS` seconds and broadcasts the matching `progress` events
   to all connected SSE clients. The backend is therefore no longer required to
   be the writer in order to stream updates.
2. **HTTP API.** `POST /api/v1/projects/{projectId}/progress` still persists the
   update and broadcasts immediately.

Because the polling path and the API path can observe the same row change, the
SSE broker collapses consecutive identical values for a given `projectId` and
event type, so clients receive exactly one event per actual change. The
`progress` dedupe also takes `status` into account, so a status-only change is
still broadcast.

### Pipeline status

`projects.status` (nullable, migration `0008`) is written by the external n8n
workflow and reports where the pipeline is:

`ERROR`, `REQUIREMENTS_RUNNING`, `REQUIREMENTS_DONE`, `CODE_RUNNING`,
`CODE_DONE`, `TEST_RUNNING`, `TEST_DONE`, `REVIEW_RUNNING`, `REVIEW_DONE`,
`RETROSPECTIVE_RUNNING`, `RETROSPECTIVE_DONE`.

The column has a `CHECK` constraint on these values. The detail-page phase bar
marks completed phases green, makes the `_RUNNING` phase dot pulse, and shows the
failed phase in red for `ERROR` (the first phase without a document, or the last
phase if all documents exist). The backend returns the status in the project
payloads and includes it in every `progress` SSE event.

### Finalization

A project that reaches `completion_percentage = 100` can be **finalized**: the
demo is released as a real, public GitHub repository. The `finalization_percentage`
column tracks the release progress (`0` = not started, `1..99` = in progress,
`100` = done) and `final_repo_url` holds the released repository URL.

Flow:

1. The UI shows a **Finalize** action only when the project is 100% complete
   (a rocket in the dashboard).
2. `POST /api/v1/projects/{projectId}/finalize` validates eligibility (409 if not
   complete, already finalizing or already finalized), atomically sets
   `finalization_percentage = 1` and calls the n8n webhook with
   `{"project_id": "<projects.id UUID>"}` → `204`.
3. n8n performs the work (create repo, single-commit push) and writes the
   progress back to PostgreSQL, bumping `updated_at` at each step.
4. The poller observes the changes and streams `finalization` events over the
   same SSE channel.

If the webhook cannot be reached, the backend rolls the request back to `0`
(with `finalize_error`) so the user can retry.

## Environment variables

### Backend (`backend/.env.example`)

| Variable | Description |
| --- | --- |
| `POSTGRESQL_USER` | PostgreSQL user |
| `POSTGRESQL_PASSWORD` | PostgreSQL password |
| `POSTGRESQL_HOST` | PostgreSQL host |
| `POSTGRESQL_PORT` | PostgreSQL port |
| `POSTGRESQL_DATABASE` | PostgreSQL database name |
| `CORS_ORIGINS` | Comma-separated list of allowed origins (e.g. `http://localhost:5173`) |
| `ENABLE_PROGRESS_POLLING` | Poll PostgreSQL for externally written progress updates (default `true`) |
| `POLL_INTERVAL_SECONDS` | Seconds between progress polls (default `2`) |
| `N8N_FINALIZE_WEBHOOK_URL` | n8n webhook invoked to start a project finalization (unset ⇒ finalize returns 503) |
| `N8N_PROJECT_TITLE_WEBHOOK_URL` | n8n webhook extracting the project title from `user_input` (unset ⇒ project creation returns 503) |
| `N8N_REQUIREMENTS_WEBHOOK_URL` | n8n webhook that starts requirements generation for a newly created project |
| `N8N_TIMEOUT_SECONDS` | Timeout shared by every n8n webhook call (default `120`) |
| `ORBIT_API_URL` | Full Orbit registration endpoint (`https://api.orbit.agogi.dev/api/v1/register`); unset ⇒ Orbit disabled |
| `APP_URL` | Public URL of this service, shown in Orbit (must be an absolute http(s) URL) |

### Frontend (`frontend/.env.example`)

| Variable | Description |
| --- | --- |
| `VITE_API_BASE_URL` | Backend base URL used at build time (e.g. `http://localhost:8000`) |

## Local development

1. Start PostgreSQL and create a database named `mind2code`.
2. Copy and fill environment files:

```sh
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

3. Apply backend migrations:

```sh
cd backend
poetry install
yoyo apply --database postgresql://USER:PASSWORD@localhost:5432/mind2code ./migrations
```

4. Start the backend:

```sh
poetry run python src/main.py
```

5. Start the frontend:

```sh
cd ../frontend
npm install
npm run dev
```

The dashboard is available at `http://localhost:5173` and the API docs at `http://localhost:8000/docs`.

## Docker

Both services can be built with their respective Dockerfiles:

```sh
cd backend && docker build -t mind2code-backend .
cd ../frontend && docker build --build-arg VITE_API_BASE_URL=http://localhost:8000 -t mind2code-frontend .
```
