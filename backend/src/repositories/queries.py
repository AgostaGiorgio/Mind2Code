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
