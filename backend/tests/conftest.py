"""Shared fixtures for the backend test-suite.

The tests exercise the real FastAPI application (routers, services, middleware,
error handlers, SSE broker) while swapping only the database-backed repository
for an in-memory fake, so no PostgreSQL instance is required.
"""

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import UUID, uuid4

# Must be set before importing src.* because AppConfig is instantiated at import time.
os.environ["POSTGRESQL_USER"] = "test"
os.environ["POSTGRESQL_PASSWORD"] = "test"
os.environ["POSTGRESQL_HOST"] = "localhost"
os.environ["POSTGRESQL_PORT"] = "5432"
os.environ["POSTGRESQL_DATABASE"] = "test_db"
os.environ["CORS_ORIGINS"] = '["http://localhost:5173"]'
os.environ["LOG_LEVEL"] = "WARNING"
# Endpoint tests must not start a real DB-polling background task.
os.environ["ENABLE_PROGRESS_POLLING"] = "false"
# Tests must not register against the real Orbit registry.
os.environ["ORBIT_API_URL"] = ""

import pytest  # noqa: E402
from dependency_injector import providers  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.db.models.project import Project, ProjectDetail  # noqa: E402
from src.main import app, container  # noqa: E402
from src.sse.broker import EventBroker  # noqa: E402

CORS_ORIGIN = "http://localhost:5173"

PROJECT_A_ID = UUID("11111111-1111-4111-8111-111111111111")
PROJECT_B_ID = UUID("22222222-2222-4222-8222-222222222222")
UNKNOWN_PROJECT_ID = UUID("99999999-9999-4999-8999-999999999999")


def make_project(
    project_id: UUID,
    name: str,
    github_url: str = "https://github.com/me/repo",
    completion: int = 0,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Project:
    now = datetime.now(timezone.utc)
    return Project(
        id=project_id,
        name=name,
        github_url=github_url,
        completion_percentage=completion,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


class FakeProjectRepository:
    """In-memory stand-in for :class:`ProjectRepository`."""

    def __init__(self, projects: list[Project] | None = None):
        self.projects: dict[UUID, Project] = {p.id: p for p in (projects or [])}
        self.details: dict[UUID, dict] = {}
        self.update_calls: list[tuple[UUID, int]] = []
        self.update_name_calls: list[tuple[UUID, str]] = []
        self.create_calls: list[dict] = []
        self.list_error: Exception | None = None

    async def list_projects(self) -> list[Project]:
        if self.list_error is not None:
            raise self.list_error
        return list(self.projects.values())

    async def get_project_detail(self, project_id: UUID) -> ProjectDetail | None:
        project = self.projects.get(project_id)
        if project is None:
            return None
        return ProjectDetail(**project.model_dump(), **self.details.get(project_id, {}))

    async def create_project(
        self, name: str, user_input: str, auto: bool
    ) -> ProjectDetail | None:
        project_id = uuid4()
        now = datetime.now(timezone.utc)
        project = Project(
            id=project_id,
            name=name,
            github_url="",
            completion_percentage=0,
            auto=auto,
            created_at=now,
            updated_at=now,
        )
        self.projects[project_id] = project
        self.details[project_id] = {"user_input": user_input}
        self.create_calls.append(
            {"name": name, "user_input": user_input, "auto": auto}
        )
        return ProjectDetail(**project.model_dump(), **self.details[project_id])

    async def get_latest_updated_at(self) -> datetime | None:
        if not self.projects:
            return None
        return max(p.updated_at for p in self.projects.values())

    async def list_updated_since(self, since: datetime) -> list[Project]:
        return sorted(
            (p for p in self.projects.values() if p.updated_at > since),
            key=lambda p: p.updated_at,
        )

    async def update_name(self, project_id: UUID, name: str) -> ProjectDetail | None:
        project = self.projects.get(project_id)
        if project is None:
            return None
        self.update_name_calls.append((project_id, name))
        updated = project.model_copy(update={"name": name})
        self.projects[project_id] = updated
        return ProjectDetail(**updated.model_dump(), **self.details.get(project_id, {}))

    async def update_completion(
        self, project_id: UUID, completion_percentage: int
    ) -> Project | None:
        project = self.projects.get(project_id)
        if project is None:
            return None
        updated = project.model_copy(
            update={
                "completion_percentage": completion_percentage,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self.projects[project_id] = updated
        self.update_calls.append((project_id, completion_percentage))
        return updated


class FakeN8NClient:
    """In-memory stand-in for :class:`N8NClient`."""

    def __init__(
        self,
        title: str | None = "Generated title",
        title_configured: bool = True,
        requirements_ok: bool = True,
        requirements_configured: bool = True,
        phase_ok: bool = True,
        phases_configured: bool = True,
    ):
        self.title = title
        self.project_title_configured = title_configured
        self.requirements_ok = requirements_ok
        self.requirements_configured = requirements_configured
        self.phase_ok = phase_ok
        self.phases_configured = phases_configured
        self.title_calls: list[str] = []
        self.requirements_calls: list[str] = []
        self.phase_calls: list[tuple[str, str]] = []

    async def extract_project_title(self, user_input: str) -> str | None:
        self.title_calls.append(user_input)
        return self.title

    async def trigger_requirements(self, project_id: str) -> bool:
        self.requirements_calls.append(project_id)
        return self.requirements_ok

    def phase_configured(self, phase: str) -> bool:
        return self.phases_configured

    async def trigger_phase(self, phase: str, project_id: str) -> bool:
        self.phase_calls.append((phase, project_id))
        return self.phase_ok


@contextmanager
def app_client(repo=None, broker=None, n8n_client=None, raise_server_exceptions=True):
    """Yield a TestClient with the given repository/broker/n8n client wired into the container."""
    if repo is not None:
        container.project_repository.override(providers.Object(repo))
    if broker is not None:
        container.event_broker.override(providers.Object(broker))
    if n8n_client is not None:
        container.n8n_client.override(providers.Object(n8n_client))
    try:
        with TestClient(app, raise_server_exceptions=raise_server_exceptions) as client:
            yield client
    finally:
        container.project_repository.reset_override()
        container.event_broker.reset_override()
        container.n8n_client.reset_override()


@pytest.fixture
def fake_repo() -> FakeProjectRepository:
    return FakeProjectRepository()


@pytest.fixture
def broker() -> EventBroker:
    return EventBroker()
