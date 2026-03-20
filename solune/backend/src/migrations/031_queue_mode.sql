-- 031: Add queue_mode column to project_settings
-- Enables per-project sequential pipeline execution mode.

ALTER TABLE project_settings ADD COLUMN queue_mode INTEGER NOT NULL DEFAULT 0;
