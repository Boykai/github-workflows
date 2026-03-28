-- 034: Auto-merge toggle + Phase 8 pipeline state extensions
--
-- Part A: Add auto_merge column to project_settings for per-project auto merge toggle.
-- When auto_merge = 1, pipelines automatically squash-merge parent PRs on completion.
ALTER TABLE project_settings ADD COLUMN auto_merge INTEGER NOT NULL DEFAULT 0;

-- Part B: Extend pipeline_states for concurrent execution tracking.
-- Adds concurrent_group_id, is_isolated, and recovered_at columns.
ALTER TABLE pipeline_states ADD COLUMN concurrent_group_id TEXT;
ALTER TABLE pipeline_states ADD COLUMN is_isolated INTEGER NOT NULL DEFAULT 1;
ALTER TABLE pipeline_states ADD COLUMN recovered_at TEXT;
