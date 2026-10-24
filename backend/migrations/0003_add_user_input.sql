-- 0003: add the free-form user input document column

ALTER TABLE projects
    ADD COLUMN user_input TEXT;
