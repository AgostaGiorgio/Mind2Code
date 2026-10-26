ALTER TABLE projects
    ALTER COLUMN execution_id DROP DEFAULT;

ALTER SEQUENCE IF EXISTS projects_execution_id_seq OWNED BY NONE;
DROP SEQUENCE IF EXISTS projects_execution_id_seq;

ALTER TABLE projects
    DROP COLUMN auto;
