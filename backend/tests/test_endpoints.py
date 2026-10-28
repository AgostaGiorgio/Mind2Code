"""Application endpoint tests (routers + services + middleware).

Covers
------
US-1 / FR-3, FR-7  : GET /api/v1/projects returns every project (camelCase).
FR-13, NFR-6       : health endpoint + correlation id header.
US-4 / FR-15,16,17,18,19 : POST /api/v1/projects/{id}/progress.
NFR-3 (T-11)       : CORS restriction + consistent JSON error body.
"""

import pytest

from tests.conftest import (
    CORS_ORIGIN,
    PROJECT_A_ID,
    PROJECT_B_ID,
    UNKNOWN_PROJECT_ID,
    FakeN8NClient,
    app_client,
    make_project,
)
from src.db.models.project import ProjectStatus


def test_us1_get_projects_lists_all(fake_repo, broker):
    fake_repo.projects = {
        PROJECT_A_ID: make_project(
            PROJECT_A_ID, "Alpha", "https://github.com/me/alpha", 40
        ),
        PROJECT_B_ID: make_project(
            PROJECT_B_ID, "Beta", "https://github.com/me/beta", 10
        ),
    }
    with app_client(fake_repo, broker) as client:
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        by_name = {item["name"]: item for item in data}
        assert by_name["Alpha"]["id"] == str(PROJECT_A_ID)
        assert by_name["Alpha"]["githubUrl"] == "https://github.com/me/alpha"
        assert by_name["Alpha"]["completionPercentage"] == 40
        assert by_name["Beta"]["completionPercentage"] == 10
        # FR-7 contract keys
        assert {"id", "name", "githubUrl", "completionPercentage"} <= set(
            by_name["Alpha"].keys()
        )
        assert "executionId" not in by_name["Alpha"]


def test_us1_empty_project_list_returns_empty_array(fake_repo, broker):
    with app_client(fake_repo, broker) as client:
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        assert response.json() == []


# --------------------------------------------------------------------------- #
# US-4 — Publish progress updates
# --------------------------------------------------------------------------- #


def test_us4_valid_update_persists_and_broadcasts_to_all_clients(fake_repo, broker):
    fake_repo.projects = {
        PROJECT_A_ID: make_project(PROJECT_A_ID, "Alpha", completion=40)
    }
    q1 = broker.subscribe()
    q2 = broker.subscribe()

    with app_client(fake_repo, broker) as client:
        response = client.post(
            f"/api/v1/projects/{PROJECT_A_ID}/progress",
            json={"completionPercentage": 75},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(PROJECT_A_ID)
        assert body["completionPercentage"] == 75

        # stored completion becomes 75
        assert fake_repo.projects[PROJECT_A_ID].completion_percentage == 75

        # both SSE clients received a matching progress event
        expected = (
            "progress",
            f'{{"projectId":"{PROJECT_A_ID}","completionPercentage":75,"status":null}}',
        )
        assert q1.get_nowait() == expected
        assert q2.get_nowait() == expected


def test_us3_new_client_sees_current_value_after_update(fake_repo, broker):
    fake_repo.projects = {
        PROJECT_A_ID: make_project(PROJECT_A_ID, "Alpha", completion=40)
    }
    with app_client(fake_repo, broker) as client:
        client.post(
            f"/api/v1/projects/{PROJECT_A_ID}/progress",
            json={"completionPercentage": 75},
        )
        data = client.get("/api/v1/projects").json()
        assert data[0]["completionPercentage"] == 75


@pytest.mark.parametrize("value", [120, -1, 101])
def test_us4_out_of_range_rejected_with_422(fake_repo, broker, value):
    fake_repo.projects = {
        PROJECT_A_ID: make_project(PROJECT_A_ID, "Alpha", completion=40)
    }
    q = broker.subscribe()

    with app_client(fake_repo, broker) as client:
        response = client.post(
            f"/api/v1/projects/{PROJECT_A_ID}/progress",
            json={"completionPercentage": value},
        )
        assert response.status_code == 422
        # nothing persisted or broadcast
        assert fake_repo.projects[PROJECT_A_ID].completion_percentage == 40
        assert fake_repo.update_calls == []
        assert q.empty()


@pytest.mark.parametrize("value", [0, 100])
def test_us4_boundary_values_accepted(fake_repo, broker, value):
    fake_repo.projects = {
        PROJECT_A_ID: make_project(PROJECT_A_ID, "Alpha", completion=40)
    }
    with app_client(fake_repo, broker) as client:
        response = client.post(
            f"/api/v1/projects/{PROJECT_A_ID}/progress",
            json={"completionPercentage": value},
        )
        assert response.status_code == 200
        assert response.json()["completionPercentage"] == value


def test_us4_unknown_project_id_returns_404(fake_repo, broker):
    q = broker.subscribe()
    with app_client(fake_repo, broker) as client:
        response = client.post(
            f"/api/v1/projects/{UNKNOWN_PROJECT_ID}/progress",
            json={"completionPercentage": 50},
        )
        assert response.status_code == 404
        assert q.empty()


def test_us4_malformed_project_id_returns_422(fake_repo, broker):
    with app_client(fake_repo, broker) as client:
        response = client.post(
            "/api/v1/projects/not-a-uuid/progress", json={"completionPercentage": 50}
        )
        assert response.status_code == 422


def test_us4_missing_body_returns_422(fake_repo, broker):
    with app_client(fake_repo, broker) as client:
        response = client.post(
            f"/api/v1/projects/{PROJECT_A_ID}/progress", json={}
        )
        assert response.status_code == 422


# --------------------------------------------------------------------------- #
# Create project
# --------------------------------------------------------------------------- #


def test_create_project_persists_user_input_and_auto(fake_repo, broker):
    n8n = FakeN8NClient(title="Build a todo app")
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(
            "/api/v1/projects",
            json={"userInput": "# Build a todo app\nWith authentication", "auto": True},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Build a todo app"
        assert body["auto"] is True
        assert body["userInput"] == "# Build a todo app\nWith authentication"
        assert body["githubUrl"] == ""
        assert body["completionPercentage"] == 0
        assert body["finalizationPercentage"] == 0
        assert body["requirements"] is None
        assert "executionId" not in body
    assert fake_repo.create_calls == [
        {
            "name": "Build a todo app",
            "user_input": "# Build a todo app\nWith authentication",
            "auto": True,
        }
    ]
    assert n8n.title_calls == ["# Build a todo app\nWith authentication"]
    assert n8n.requirements_calls == [body["id"]]
    assert body["id"] in {str(project_id) for project_id in fake_repo.projects}


def test_create_project_defaults_auto_to_false(fake_repo, broker):
    n8n = FakeN8NClient(title="Generated title")
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post("/api/v1/projects", json={"userInput": "A simple idea"})
        assert response.status_code == 201
        body = response.json()
        assert body["auto"] is False
        assert body["name"] == "Generated title"
        assert body["userInput"] == "A simple idea"
    assert fake_repo.create_calls[0]["auto"] is False
    assert n8n.requirements_calls == [body["id"]]


def test_create_project_title_webhook_failure_returns_502(fake_repo, broker):
    n8n = FakeN8NClient(title=None)
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post("/api/v1/projects", json={"userInput": "Some idea"})
        assert response.status_code == 502
    assert fake_repo.create_calls == []
    assert n8n.requirements_calls == []


def test_create_project_not_configured_returns_503(fake_repo, broker):
    n8n = FakeN8NClient(title_configured=False, requirements_configured=False)
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post("/api/v1/projects", json={"userInput": "Some idea"})
        assert response.status_code == 503
    assert fake_repo.create_calls == []


def test_create_project_requirements_failure_still_creates(fake_repo, broker):
    n8n = FakeN8NClient(title="Still created", requirements_ok=False)
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post("/api/v1/projects", json={"userInput": "Some idea"})
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Still created"
    assert n8n.requirements_calls == [body["id"]]
    assert body["id"] in {str(project_id) for project_id in fake_repo.projects}


@pytest.mark.parametrize("user_input", ["", "   ", "\n\n"])
def test_create_project_blank_input_returns_422(fake_repo, broker, user_input):
    with app_client(fake_repo, broker) as client:
        response = client.post("/api/v1/projects", json={"userInput": user_input})
        assert response.status_code == 422
    assert fake_repo.create_calls == []


def test_create_project_missing_user_input_returns_422(fake_repo, broker):
    with app_client(fake_repo, broker) as client:
        response = client.post("/api/v1/projects", json={"auto": True})
        assert response.status_code == 422
    assert fake_repo.create_calls == []


# --------------------------------------------------------------------------- #
# Single project detail (data + Markdown documents)
# --------------------------------------------------------------------------- #


def test_get_project_detail_returns_project_with_documents(fake_repo, broker):
    fake_repo.projects[PROJECT_A_ID] = make_project(
        PROJECT_A_ID, "Alpha", completion=40
    )
    fake_repo.details[PROJECT_A_ID] = {
        "user_input": "input",
        "requirements": "req",
        "code_summary": "code",
        "test_summary": "tests",
        "final_review": "review",
        "retrospective": "retro",
    }
    with app_client(fake_repo, broker) as client:
        response = client.get(f"/api/v1/projects/{PROJECT_A_ID}")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(PROJECT_A_ID)
        assert "executionId" not in body
        assert body["completionPercentage"] == 40
        assert body["githubUrl"] == "https://github.com/me/repo"
        assert body["userInput"] == "input"
        assert body["requirements"] == "req"
        assert body["retrospective"] == "retro"
        assert body["codeSummary"] == "code"
        assert body["testSummary"] == "tests"
        assert body["finalReview"] == "review"


def test_get_project_detail_unknown_returns_404(fake_repo, broker):
    with app_client(fake_repo, broker) as client:
        response = client.get(f"/api/v1/projects/{UNKNOWN_PROJECT_ID}")
        assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Rename project
# --------------------------------------------------------------------------- #


def test_rename_project_updates_name_and_keeps_documents(fake_repo, broker):
    fake_repo.projects[PROJECT_A_ID] = make_project(
        PROJECT_A_ID, "Alpha", completion=40
    )
    fake_repo.details[PROJECT_A_ID] = {
        "user_input": "input",
        "requirements": "req",
        "code_summary": "code",
        "test_summary": "tests",
        "final_review": "review",
        "retrospective": "retro",
    }
    with app_client(fake_repo, broker) as client:
        response = client.patch(
            f"/api/v1/projects/{PROJECT_A_ID}", json={"name": "  Beta  "}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Beta"
        assert body["id"] == str(PROJECT_A_ID)
        assert body["userInput"] == "input"
        assert body["finalReview"] == "review"
        assert body["retrospective"] == "retro"
    assert fake_repo.update_name_calls == [(PROJECT_A_ID, "Beta")]


def test_rename_project_unknown_returns_404(fake_repo, broker):
    with app_client(fake_repo, broker) as client:
        response = client.patch(
            f"/api/v1/projects/{UNKNOWN_PROJECT_ID}", json={"name": "X"}
        )
        assert response.status_code == 404


@pytest.mark.parametrize("name", ["", "   "])
def test_rename_project_blank_returns_422(fake_repo, broker, name):
    fake_repo.projects[PROJECT_A_ID] = make_project(PROJECT_A_ID, "Alpha")
    with app_client(fake_repo, broker) as client:
        response = client.patch(
            f"/api/v1/projects/{PROJECT_A_ID}", json={"name": name}
        )
        assert response.status_code == 422
    assert fake_repo.update_name_calls == []


# --------------------------------------------------------------------------- #
# Finalize (release) a project
# --------------------------------------------------------------------------- #


def test_finalize_eligible_project_triggers_webhook(fake_repo, broker):
    fake_repo.projects[PROJECT_A_ID] = make_project(
        PROJECT_A_ID, "Alpha", completion=100
    )
    n8n = FakeN8NClient()
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(f"/api/v1/projects/{PROJECT_A_ID}/finalize")
        assert response.status_code == 204
    assert fake_repo.finalize_requests == [PROJECT_A_ID]
    assert n8n.finalize_calls == [str(PROJECT_A_ID)]
    assert fake_repo.projects[PROJECT_A_ID].finalization_percentage == 1


def test_finalize_incomplete_project_returns_409(fake_repo, broker):
    fake_repo.projects[PROJECT_A_ID] = make_project(
        PROJECT_A_ID, "Alpha", completion=99
    )
    n8n = FakeN8NClient()
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(f"/api/v1/projects/{PROJECT_A_ID}/finalize")
        assert response.status_code == 409
    assert n8n.finalize_calls == []
    assert fake_repo.finalize_requests == []


def test_finalize_already_started_returns_409(fake_repo, broker):
    project = make_project(PROJECT_A_ID, "Alpha", completion=100).model_copy(
        update={"finalization_percentage": 1}
    )
    fake_repo.projects[PROJECT_A_ID] = project
    n8n = FakeN8NClient()
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(f"/api/v1/projects/{PROJECT_A_ID}/finalize")
        assert response.status_code == 409
    assert n8n.finalize_calls == []


def test_finalize_unknown_project_returns_404(fake_repo, broker):
    n8n = FakeN8NClient()
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(f"/api/v1/projects/{UNKNOWN_PROJECT_ID}/finalize")
        assert response.status_code == 404


def test_finalize_webhook_failure_resets_and_returns_503(fake_repo, broker):
    fake_repo.projects[PROJECT_A_ID] = make_project(
        PROJECT_A_ID, "Alpha", completion=100
    )
    n8n = FakeN8NClient(finalize_ok=False)
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(f"/api/v1/projects/{PROJECT_A_ID}/finalize")
        assert response.status_code == 503
    assert fake_repo.projects[PROJECT_A_ID].finalization_percentage == 0
    assert fake_repo.projects[PROJECT_A_ID].finalize_error is not None


def test_finalize_not_configured_returns_503(fake_repo, broker):
    fake_repo.projects[PROJECT_A_ID] = make_project(
        PROJECT_A_ID, "Alpha", completion=100
    )
    n8n = FakeN8NClient(finalize_configured=False)
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(f"/api/v1/projects/{PROJECT_A_ID}/finalize")
        assert response.status_code == 503
    assert fake_repo.finalize_requests == [PROJECT_A_ID]
    assert fake_repo.projects[PROJECT_A_ID].finalization_percentage == 0


# --------------------------------------------------------------------------- #
# Retry a failed phase
# --------------------------------------------------------------------------- #


def _error_project():
    return make_project(PROJECT_A_ID, "Alpha").model_copy(
        update={"status": ProjectStatus.ERROR}
    )


def test_retry_phase_from_error_triggers_webhook(fake_repo, broker):
    fake_repo.projects[PROJECT_A_ID] = _error_project()
    n8n = FakeN8NClient()
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(f"/api/v1/projects/{PROJECT_A_ID}/CODE")
        assert response.status_code == 200
        body = response.json()
        # The backend leaves the status untouched: n8n updates it.
        assert body["status"] == "ERROR"
    assert n8n.phase_calls == [("CODE", str(PROJECT_A_ID))]


def test_retry_phase_requires_error_status(fake_repo, broker):
    fake_repo.projects[PROJECT_A_ID] = make_project(PROJECT_A_ID, "Alpha", completion=40)
    n8n = FakeN8NClient()
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(f"/api/v1/projects/{PROJECT_A_ID}/CODE")
        assert response.status_code == 409
    assert n8n.phase_calls == []


def test_retry_phase_unknown_project_returns_404(fake_repo, broker):
    n8n = FakeN8NClient()
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(f"/api/v1/projects/{UNKNOWN_PROJECT_ID}/CODE")
        assert response.status_code == 404
    assert n8n.phase_calls == []


def test_retry_phase_invalid_phase_returns_422(fake_repo, broker):
    fake_repo.projects[PROJECT_A_ID] = _error_project()
    with app_client(fake_repo, broker) as client:
        response = client.post(f"/api/v1/projects/{PROJECT_A_ID}/BOGUS")
        assert response.status_code == 422


def test_retry_phase_not_configured_keeps_error(fake_repo, broker):
    fake_repo.projects[PROJECT_A_ID] = _error_project()
    n8n = FakeN8NClient(phases_configured=False)
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(f"/api/v1/projects/{PROJECT_A_ID}/REQUIREMENTS")
        assert response.status_code == 503
    assert n8n.phase_calls == []
    assert fake_repo.projects[PROJECT_A_ID].status is ProjectStatus.ERROR


def test_retry_phase_webhook_failure_keeps_error(fake_repo, broker):
    fake_repo.projects[PROJECT_A_ID] = _error_project()
    n8n = FakeN8NClient(phase_ok=False)
    with app_client(fake_repo, broker, n8n) as client:
        response = client.post(f"/api/v1/projects/{PROJECT_A_ID}/REVIEW")
        assert response.status_code == 502
    assert n8n.phase_calls == [("REVIEW", str(PROJECT_A_ID))]
    assert fake_repo.projects[PROJECT_A_ID].status is ProjectStatus.ERROR


# --------------------------------------------------------------------------- #
# Health, CORS and error handling (T-2, T-11)
# --------------------------------------------------------------------------- #


def test_health_endpoint(fake_repo, broker):
    with app_client(fake_repo, broker) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_cors_allows_configured_origin_only(fake_repo, broker):
    with app_client(fake_repo, broker) as client:
        allowed = client.get("/api/v1/projects", headers={"Origin": CORS_ORIGIN})
        assert allowed.headers.get("access-control-allow-origin") == CORS_ORIGIN

        denied = client.get("/api/v1/projects", headers={"Origin": "http://evil.example"})
        assert denied.headers.get("access-control-allow-origin") is None
