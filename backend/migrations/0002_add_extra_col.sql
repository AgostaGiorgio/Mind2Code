ALTER TABLE projects
    ADD COLUMN requirements TEXT,
    ADD COLUMN "code-summary" TEXT,
    ADD COLUMN "test-summary" TEXT,
    ADD COLUMN review TEXT;