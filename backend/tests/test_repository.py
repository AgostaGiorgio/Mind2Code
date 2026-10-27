"""Repository unit tests using a fake PostgresClient/session.

Covers: FR-7 (T-6 list semantics), FR-15/FR-21 (T-6 update semantics) and the
project-construction error branches.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.db.models.project import ProjectStatus
from src.repositories.projects import ProjectRepository

PROJECT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_PROJECT_ID = UUID("22222222-2222-4222-8222-222222222222")
UNKNOWN_PROJECT_ID = UUID("99999999-9999-4999-8999-999999999999")


def _row(project_id=PROJECT_ID, name="Alpha", completion=40, status=None):
    now = datetime.now(timezone.utc)
    return {
        "id": project_id,
        "name": name,
        "github_url": f"https://github.com/me/{name.lower()}",
        "completion_percentage": completion,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None


class FakeSession:
    def __init__(self, rows=None, error=None):
        self._rows = rows or []
        self._error = error
        self.executed = []

    async def execute(self, statement, params=None):
        self.executed.append((statement, params))
        if self._error is not None:
            raise self._error
        return FakeResult(self._rows)

    def begin(self):
        return _FakeTransaction()


class _FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False


class FakePostgresClient:
    def __init__(self, session):
        self._session = session

    @asynccontextmanager
    async def async_session(self):
        yield self._session


def _repo(rows=None, error=None):
    session = FakeSession(rows=rows, error=error)
    return ProjectRepository(FakePostgresClient(session)), session


def test_list_projects_returns_models():
    repo, _ = _repo(
        rows=[
            _row(PROJECT_ID, "Alpha", 40),
            _row(OTHER_PROJECT_ID, "Beta", 10),
        ]
    )
    projects = asyncio.run(repo.list_projects())
    assert [p.name for p in projects] == ["Alpha", "Beta"]
    assert projects[0].completion_percentage == 40
    assert projects[0].id == PROJECT_ID


def test_list_projects_empty_returns_empty_list():
    repo, _ = _repo(rows=[])
    assert asyncio.run(repo.list_projects()) == []


def test_list_projects_swallows_sqlalchemy_error():
    repo, _ = _repo(error=SQLAlchemyError("db down"))
    assert asyncio.run(repo.list_projects()) == []


def test_list_projects_swallows_validation_error():
    # Row missing required fields -> Pydantic ValidationError -> [].
    repo, _ = _repo(rows=[{"id": uuid4(), "name": "Alpha"}])
    assert asyncio.run(repo.list_projects()) == []


def _documents():
    return {
        "user_input": "input",
        "requirements": "req",
        "code_summary": "code",
        "test_summary": "tests",
        "final_review": "review",
        "retrospective": "retro",
    }


def test_get_project_detail_returns_model_and_passes_param():
    repo, session = _repo(rows=[{**_row(PROJECT_ID, "Alpha", 40), **_documents()}])
    detail = asyncio.run(repo.get_project_detail(PROJECT_ID))
    assert detail is not None
    assert detail.id == PROJECT_ID
    assert detail.completion_percentage == 40
    assert detail.user_input == "input"
    assert detail.requirements == "req"
    assert detail.retrospective == "retro"
    assert detail.code_summary == "code"
    assert detail.test_summary == "tests"
    assert detail.final_review == "review"
    assert session.executed[0][1] == {"project_id": PROJECT_ID}


def test_get_project_detail_missing_returns_none():
    repo, _ = _repo(rows=[])
    assert asyncio.run(repo.get_project_detail(UNKNOWN_PROJECT_ID)) is None


def test_get_project_detail_parses_status():
    repo, _ = _repo(rows=[_row(PROJECT_ID, "Alpha", 40, status="CODE_RUNNING")])
    detail = asyncio.run(repo.get_project_detail(PROJECT_ID))
    assert detail is not None
    assert detail.status is ProjectStatus.CODE_RUNNING


def test_get_project_detail_error_returns_none():
    repo, _ = _repo(error=SQLAlchemyError("boom"))
    assert asyncio.run(repo.get_project_detail(PROJECT_ID)) is None


def test_request_finalization_returns_project_and_passes_param():
    repo, session = _repo(rows=[_row(PROJECT_ID, "Alpha", 100)])
    project = asyncio.run(repo.request_finalization(PROJECT_ID))
    assert project is not None
    assert project.id == PROJECT_ID
    assert session.executed[0][1] == {"project_id": PROJECT_ID}


def test_request_finalization_not_eligible_returns_none():
    repo, _ = _repo(rows=[])
    assert asyncio.run(repo.request_finalization(UNKNOWN_PROJECT_ID)) is None


def test_request_finalization_error_returns_none():
    repo, _ = _repo(error=SQLAlchemyError("boom"))
    assert asyncio.run(repo.request_finalization(PROJECT_ID)) is None


def test_reset_finalization_executes_update():
    repo, session = _repo(rows=[])
    asyncio.run(repo.reset_finalization(PROJECT_ID, "boom"))
    assert session.executed[0][1] == {
        "project_id": PROJECT_ID,
        "finalize_error": "boom",
    }


def test_create_project_returns_detail_and_passes_params():
    row = {**_row(PROJECT_ID, "Build me", 0), "auto": True, "user_input": "Build me"}
    repo, session = _repo(rows=[row])
    detail = asyncio.run(repo.create_project("Build me", "Build me", True))
    assert detail is not None
    assert detail.id == PROJECT_ID
    assert detail.auto is True
    assert detail.user_input == "Build me"
    assert session.executed[0][1] == {
        "name": "Build me",
        "github_url": "",
        "user_input": "Build me",
        "auto": True,
    }


def test_create_project_error_returns_none():
    repo, _ = _repo(error=SQLAlchemyError("boom"))
    assert asyncio.run(repo.create_project("Build me", "Build me", False)) is None


def test_update_name_returns_updated_detail_and_passes_params():
    repo, session = _repo(rows=[{**_row(PROJECT_ID, "Renamed", 40), **_documents()}])
    detail = asyncio.run(repo.update_name(PROJECT_ID, "Renamed"))
    assert detail is not None
    assert detail.name == "Renamed"
    assert detail.requirements == "req"
    assert session.executed[0][1] == {"project_id": PROJECT_ID, "name": "Renamed"}


def test_update_name_unknown_returns_none():
    repo, _ = _repo(rows=[])
    assert asyncio.run(repo.update_name(UNKNOWN_PROJECT_ID, "X")) is None


def test_update_name_error_returns_none():
    repo, _ = _repo(error=SQLAlchemyError("boom"))
    assert asyncio.run(repo.update_name(PROJECT_ID, "X")) is None


def test_list_updated_since_returns_models_and_passes_param():
    since = datetime.now(timezone.utc)
    repo, session = _repo(rows=[_row(PROJECT_ID, "Alpha", 75)])
    projects = asyncio.run(repo.list_updated_since(since))
    assert projects[0].completion_percentage == 75
    assert session.executed[0][1] == {"since": since}


def test_list_updated_since_error_returns_empty_list():
    repo, _ = _repo(error=SQLAlchemyError("boom"))
    assert asyncio.run(repo.list_updated_since(datetime.now(timezone.utc))) == []


def test_get_latest_updated_at_returns_value():
    now = datetime.now(timezone.utc)
    repo, _ = _repo(rows=[{"latest_updated_at": now}])
    assert asyncio.run(repo.get_latest_updated_at()) == now


def test_get_latest_updated_at_empty_returns_none():
    repo, _ = _repo(rows=[])
    assert asyncio.run(repo.get_latest_updated_at()) is None


def test_get_latest_updated_at_error_returns_none():
    repo, _ = _repo(error=SQLAlchemyError("boom"))
    assert asyncio.run(repo.get_latest_updated_at()) is None


def test_update_completion_returns_updated_project():
    repo, session = _repo(rows=[_row(PROJECT_ID, "Alpha", 75)])
    updated = asyncio.run(repo.update_completion(PROJECT_ID, 75))
    assert updated is not None
    assert updated.completion_percentage == 75
    assert session.executed[0][1] == {
        "project_id": PROJECT_ID,
        "completion_percentage": 75,
    }


def test_update_completion_unknown_returns_none():
    repo, _ = _repo(rows=[])
    assert asyncio.run(repo.update_completion(UNKNOWN_PROJECT_ID, 50)) is None


def test_update_completion_error_returns_none():
    repo, _ = _repo(error=SQLAlchemyError("boom"))
    assert asyncio.run(repo.update_completion(PROJECT_ID, 50)) is None
