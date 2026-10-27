-- 0008: pipeline status written by the external n8n workflow.
-- NULL means the pipeline has not reported a status yet.

ALTER TABLE projects
    ADD COLUMN status TEXT CHECK (
        status IN (
            'ERROR',
            'REQUIREMENTS_RUNNING',
            'REQUIREMENTS_DONE',
            'CODE_RUNNING',
            'CODE_DONE',
            'TEST_RUNNING',
            'TEST_DONE',
            'REVIEW_RUNNING',
            'REVIEW_DONE',
            'RETROSPECTIVE_RUNNING',
            'RETROSPECTIVE_DONE'
        )
    );
