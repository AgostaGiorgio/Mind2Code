from sqlalchemy import text

_PROJECT_COLUMNS = """
id, name, github_url, completion_percentage,
finalization_percentage, final_repo_url, finalize_error, auto, status,
created_at, updated_at
"""

LIST_PROJECTS = text(f"""
SELECT {_PROJECT_COLUMNS}
FROM projects
ORDER BY created_at DESC
""")

GET_PROJECT_DETAIL = text("""
SELECT id, name, github_url, completion_percentage,
       finalization_percentage, final_repo_url, finalize_error, auto, status,
       created_at, updated_at,
       user_input,
       requirements,
       "code-summary" AS code_summary,
       "test-summary" AS test_summary,
       review AS final_review,
       retrospective
FROM projects
WHERE id = :project_id
""")

CREATE_PROJECT = text("""
INSERT INTO projects (name, github_url, user_input, auto)
VALUES (:name, :github_url, :user_input, :auto)
RETURNING id, name, github_url, completion_percentage,
          finalization_percentage, final_repo_url, finalize_error, auto, status,
          created_at, updated_at,
          user_input,
          requirements,
          "code-summary" AS code_summary,
          "test-summary" AS test_summary,
          review AS final_review,
          retrospective
""")

UPDATE_COMPLETION = text(f"""
UPDATE projects
SET completion_percentage = :completion_percentage,
    updated_at = now()
WHERE id = :project_id
RETURNING {_PROJECT_COLUMNS}
""")

UPDATE_NAME = text("""
UPDATE projects
SET name = :name,
    updated_at = now()
WHERE id = :project_id
RETURNING id, name, github_url, completion_percentage,
          finalization_percentage, final_repo_url, finalize_error, auto, status,
          created_at, updated_at,
          user_input,
          requirements,
          "code-summary" AS code_summary,
          "test-summary" AS test_summary,
          review AS final_review,
          retrospective
""")

# Atomically claims a finalization request only for an eligible project
# (fully complete, not already finalizing or finalized).
REQUEST_FINALIZATION = text(f"""
UPDATE projects
SET finalization_percentage = 1,
    finalize_error = NULL,
    updated_at = now()
WHERE id = :project_id
  AND completion_percentage = 100
  AND finalization_percentage = 0
  AND final_repo_url IS NULL
RETURNING {_PROJECT_COLUMNS}
""")

# Rolls a finalization request back to "not started" so the UI can retry.
RESET_FINALIZATION = text("""
UPDATE projects
SET finalization_percentage = 0,
    finalize_error = :finalize_error,
    updated_at = now()
WHERE id = :project_id
""")

GET_LATEST_UPDATED_AT = text("""
SELECT max(updated_at) AS latest_updated_at
FROM projects
""")

LIST_PROJECTS_UPDATED_SINCE = text(f"""
SELECT {_PROJECT_COLUMNS}
FROM projects
WHERE updated_at > :since
ORDER BY updated_at ASC
""")
