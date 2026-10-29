-- 0006: project creation support
-- `auto` tells the external pipeline whether every step should run
-- automatically, one after the other.
-- Locally created projects take their execution_id from a reserved sequence
-- (starting at 1,000,000) so they cannot clash with external execution ids.

ALTER TABLE projects
    ADD COLUMN auto BOOLEAN NOT NULL DEFAULT FALSE;

CREATE SEQUENCE IF NOT EXISTS projects_execution_id_seq;

SELECT setval(
    'projects_execution_id_seq',
    GREATEST(COALESCE((SELECT MAX(execution_id) FROM projects), 0) + 1, 1000000),
    false
);

ALTER TABLE projects
    ALTER COLUMN execution_id SET DEFAULT nextval('projects_execution_id_seq');

ALTER SEQUENCE projects_execution_id_seq OWNED BY projects.execution_id;
