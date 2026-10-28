-- 0007: drop the external integer execution id.
-- The projects.id UUID is now the only public project identifier used by the
-- API, the SSE payloads and the n8n webhooks.

ALTER TABLE projects
    DROP COLUMN execution_id;

DROP SEQUENCE IF EXISTS projects_execution_id_seq;
