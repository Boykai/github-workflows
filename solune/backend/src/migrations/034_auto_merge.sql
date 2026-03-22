-- Add auto_merge column to project_settings for per-project auto merge toggle.
-- When auto_merge = 1, pipelines automatically squash-merge parent PRs on completion.
ALTER TABLE project_settings ADD COLUMN auto_merge INTEGER NOT NULL DEFAULT 0;
