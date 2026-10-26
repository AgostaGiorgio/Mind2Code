"""Model / JSON-contract tests.

Covers: FR-7 (camelCase project payload), FR-9 (progress event payload),
FR-17 (range validation for the update request), T-5.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.db.models.project import (
    FinalizationEvent,
    ProgressEvent,
    ProgressUpdateRequest,
    Project,
    ProjectCreateRequest,
    ProjectDetail,
    ProjectNameUpdateRequest,
)

PROJECT_ID = UUID("11111111-1111-4111-8111-111111111111")


def _project_kwargs():
    now = datetime.now(timezone.utc)
    return dict(
        id=PROJECT_ID,
        name="Alpha",
        github_url="https://github.com/me/alpha",
        completion_percentage=40,
        created_at=now,
        updated_at=now,
    )


def test_project_serializes_to_camel_case():
    project = Project(**_project_kwargs())
    payload = project.model_dump(by_alias=True)
    assert payload["id"] == PROJECT_ID
    assert payload["githubUrl"] == "https://github.com/me/alpha"
    assert payload["completionPercentage"] == 40
    # snake_case keys must not leak into the API contract
    assert "execution_id" not in payload
    assert "github_url" not in payload
    assert payload["auto"] is False


def test_project_accepts_snake_case_input():
    project = Project(**_project_kwargs())
    assert project.id == PROJECT_ID
    assert project.completion_percentage == 40


@pytest.mark.parametrize("value", [0, 1, 50, 99, 100])
def test_progress_update_request_accepts_in_range(value):
    request = ProgressUpdateRequest(completionPercentage=value)
    assert request.completion_percentage == value


@pytest.mark.parametrize("value", [-1, 101, 120, 1000])
def test_progress_update_request_rejects_out_of_range(value):
    with pytest.raises(ValidationError):
        ProgressUpdateRequest(completionPercentage=value)


def test_project_completion_percentage_is_bounded():
    with pytest.raises(ValidationError):
        Project(**{**_project_kwargs(), "completion_percentage": 150})


def test_progress_event_payload_contract():
    event = ProgressEvent(project_id=PROJECT_ID, completion_percentage=75)
    payload = event.model_dump(by_alias=True)
    assert payload == {"projectId": PROJECT_ID, "completionPercentage": 75}
    assert event.model_dump_json(by_alias=True) == (
        f'{{"projectId":"{PROJECT_ID}","completionPercentage":75}}'
    )


def test_finalization_event_payload_contract():
    event = FinalizationEvent(
        project_id=PROJECT_ID,
        finalization_percentage=60,
        final_repo_url=None,
        finalize_error=None,
    )
    assert event.model_dump(by_alias=True) == {
        "projectId": PROJECT_ID,
        "finalizationPercentage": 60,
        "finalRepoUrl": None,
        "finalizeError": None,
    }


def test_project_name_update_request_strips_whitespace():
    assert ProjectNameUpdateRequest(name="  Alpha  ").name == "Alpha"


@pytest.mark.parametrize("value", ["", "   "])
def test_project_name_update_request_rejects_blank(value):
    with pytest.raises(ValidationError):
        ProjectNameUpdateRequest(name=value)


def test_project_create_request_strips_input_and_defaults_auto():
    request = ProjectCreateRequest(userInput="  Build me  ")
    assert request.user_input == "Build me"
    assert request.auto is False
    assert ProjectCreateRequest(userInput="X", auto=True).auto is True


@pytest.mark.parametrize("value", ["", "   "])
def test_project_create_request_rejects_blank_input(value):
    with pytest.raises(ValidationError):
        ProjectCreateRequest(userInput=value)


def test_project_detail_payload_contract():
    detail = ProjectDetail(
        **_project_kwargs(),
        user_input="input",
        requirements="req",
        code_summary="code",
        test_summary="tests",
        final_review="review",
        retrospective="retro",
    )
    payload = detail.model_dump(by_alias=True)
    assert payload["id"] == PROJECT_ID
    assert payload["completionPercentage"] == 40
    assert payload["userInput"] == "input"
    assert payload["requirements"] == "req"
    assert payload["retrospective"] == "retro"
    assert payload["codeSummary"] == "code"
    assert payload["testSummary"] == "tests"
    assert payload["finalReview"] == "review"


def test_project_detail_documents_are_optional():
    detail = ProjectDetail(**_project_kwargs())
    assert detail.user_input is None
    assert detail.requirements is None
    assert detail.retrospective is None
    assert detail.model_dump(by_alias=True)["finalReview"] is None
