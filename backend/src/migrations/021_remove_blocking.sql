-- Migration 021: Remove blocking feature schema artifacts
-- Rolls back migrations 017 (blocking_queue table + blocking columns) and
-- 018 (pipeline_blocking_override column).

-- Drop the blocking_queue table and its indexes
DROP TABLE IF EXISTS blocking_queue;

-- Remove blocking column from pipeline_configs
ALTER TABLE pipeline_configs DROP COLUMN blocking;

-- Remove blocking column from chores
ALTER TABLE chores DROP COLUMN blocking;

-- Remove pipeline_blocking_override from project_settings
ALTER TABLE project_settings DROP COLUMN pipeline_blocking_override;
