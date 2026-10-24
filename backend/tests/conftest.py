"""Shared fixtures for the backend test-suite.

The tests exercise the real FastAPI application (routers, services, middleware,
error handlers, SSE broker) while swapping only the database-backed repository
for an in-memory fake, so no PostgreSQL instance is required.
"""

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

# Must be set before importing src.* because AppConfig is instantiated at import time.
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"
os.environ["CORS_ORIGINS"] = '["http://localhost:5173"]'
os.environ["LOG_LEVEL"] = "WARNING"
# Endpoint tests must not start a real DB-polling background task.
os.environ["ENABLE_PROGRESS_POLLING"] = "false"

import pytest  # noqa: E402
from dependency_injector import providers  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.db.models.project import Project, ProjectDetail  # noqa: E402
from src.main import app, container  # noqa: E402
from src.sse.broker import EventBroker  # noqa: E402

CORS_ORIGIN = "http://localhost:5173"


def make_project(
    execution_id: int,
    name: str,
    github_url: str = "https://github.com/me/repo",
    completion: int = 0,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Project:
    now = datetime.now(timezone.utc)
    return Project(
        id=uuid4(),
        execution_id=execution_id,
        name=name,
        github_url=github_url,
        completion_percentage=completion,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


class FakeProjectRepository:
    """In-memory stand-in for :class:`ProjectRepository`."""

    def __init__(self, projects: list[Project] | None = None):
        self.projects: dict[int, Project] = {p.execution_id: p for p in (projects or [])}
        self.details: dict[int, dict] = {}
        self.update_calls: list[tuple[int, int]] = []
        self.update_name_calls: list[tuple[int, str]] = []
        self.finalize_requests: list[int] = []
        self.finalize_resets: list[tuple[int, str]] = []
        self.list_error: Exception | None = None

    async def list_projects(self) -> list[Project]:
        if self.list_error is not None:
            raise self.list_error
        return list(self.projects.values())

    async def get_project_detail(self, execution_id: int) -> ProjectDetail | None:
        project = self.projects.get(execution_id)
        if project is None:
            return None
        return ProjectDetail(**project.model_dump(), **self.details.get(execution_id, {}))

    async def request_finalization(self, execution_id: int) -> Project | None:
        project = self.projects.get(execution_id)
        if project is None:
            return None
        eligible = (
            project.completion_percentage == 100
            and project.finalization_percentage == 0
            and project.final_repo_url is None
        )
        if not eligible:
            return None
        self.finalize_requests.append(execution_id)
        updated = project.model_copy(
            update={"finalization_percentage": 1, "finalize_error": None}
        )
        self.projects[execution_id] = updated
        return updated

    async def reset_finalization(self, execution_id: int, finalize_error: str) -> None:
        project = self.projects.get(execution_id)
        if project is None:
            return
        self.finalize_resets.append((execution_id, finalize_error))
        self.projects[execution_id] = project.model_copy(
            update={"finalization_percentage": 0, "finalize_error": finalize_error}
        )

    async def get_latest_updated_at(self) -> datetime | None:
        if not self.projects:
            return None
        return max(p.updated_at for p in self.projects.values())

    async def list_updated_since(self, since: datetime) -> list[Project]:
        return sorted(
            (p for p in self.projects.values() if p.updated_at > since),
            key=lambda p: p.updated_at,
        )

    async def update_name(self, execution_id: int, name: str) -> ProjectDetail | None:
        project = self.projects.get(execution_id)
        if project is None:
            return None
        self.update_name_calls.append((execution_id, name))
        updated = project.model_copy(update={"name": name})
        self.projects[execution_id] = updated
        return ProjectDetail(**updated.model_dump(), **self.details.get(execution_id, {}))

    async def update_completion(self, execution_id: int, completion_percentage: int) -> Project | None:
        project = self.projects.get(execution_id)
        if project is None:
            return None
        updated = project.model_copy(
            update={
                "completion_percentage": completion_percentage,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self.projects[execution_id] = updated
        self.update_calls.append((execution_id, completion_percentage))
        return updated


class FakeFinalizeWebhook:
    """Stand-in for :class:`FinalizeWebhookClient`."""

    def __init__(self, ok: bool = True, configured: bool = True):
        self.configured = configured
        self.ok = ok
        self.calls: list[int] = []

    async def trigger(self, execution_id: int) -> bool:
        self.calls.append(execution_id)
        return self.ok


@contextmanager
def app_client(repo=None, broker=None, webhook=None, raise_server_exceptions=True):
    """Yield a TestClient with the given repository/broker/webhook wired into the container."""
    if repo is not None:
        container.project_repository.override(providers.Object(repo))
    if broker is not None:
        container.event_broker.override(providers.Object(broker))
    if webhook is not None:
        container.finalize_webhook.override(providers.Object(webhook))
    try:
        with TestClient(app, raise_server_exceptions=raise_server_exceptions) as client:
            yield client
    finally:
        container.project_repository.reset_override()
        container.event_broker.reset_override()
        container.finalize_webhook.reset_override()


@pytest.fixture
def fake_repo() -> FakeProjectRepository:
    return FakeProjectRepository()


@pytest.fixture
def broker() -> EventBroker:
    return EventBroker()
