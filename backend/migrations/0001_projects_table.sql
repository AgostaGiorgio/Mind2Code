-- 0001: projects table
-- Stores the project portfolio keyed by an external integer execution_id.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    github_url TEXT NOT NULL,
    completion_percentage SMALLINT NOT NULL DEFAULT 0 CHECK (completion_percentage BETWEEN 0 AND 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_projects_execution_id ON projects (execution_id);
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects (updated_at DESC);
