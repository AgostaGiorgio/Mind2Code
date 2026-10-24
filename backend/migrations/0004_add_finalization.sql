-- 0004: finalization lifecycle
-- finalization_percentage: 0 = not started, 1..99 = in progress, 100 = done.

ALTER TABLE projects
    ADD COLUMN finalization_percentage SMALLINT NOT NULL DEFAULT 0
        CHECK (finalization_percentage BETWEEN 0 AND 100),
    ADD COLUMN final_repo_url TEXT,
    ADD COLUMN finalized_at   TIMESTAMPTZ,
    ADD COLUMN finalize_error TEXT;
