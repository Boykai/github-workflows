-- Migration 018: Add project-level pipeline blocking override to project_settings
-- NULL = inherit from assigned pipeline's blocking flag (no explicit override)
-- 0   = force blocking OFF for this project regardless of pipeline default
-- 1   = force blocking ON for this project regardless of pipeline default
ALTER TABLE project_settings ADD COLUMN pipeline_blocking_override INTEGER;
