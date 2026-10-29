-- Recreate the integer execution id (values are regenerated, not restored).
ALTER TABLE projects
    ADD COLUMN execution_id INTEGER;

CREATE SEQUENCE IF NOT EXISTS projects_execution_id_seq;

UPDATE projects
SET execution_id = nextval('projects_execution_id_seq');

ALTER TABLE projects
    ALTER COLUMN execution_id SET NOT NULL,
    ALTER COLUMN execution_id SET DEFAULT nextval('projects_execution_id_seq');

ALTER TABLE projects
    ADD CONSTRAINT projects_execution_id_key UNIQUE (execution_id);

CREATE INDEX IF NOT EXISTS idx_projects_execution_id ON projects (execution_id);

ALTER SEQUENCE projects_execution_id_seq OWNED BY projects.execution_id;
