-- Add queue_mode column to project_settings for per-project pipeline queue toggle.
-- When queue_mode = 1, only one pipeline runs at a time per project.
ALTER TABLE project_settings ADD COLUMN queue_mode INTEGER NOT NULL DEFAULT 0;
