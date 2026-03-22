-- 034: Phase 8 — Extend pipeline_states for concurrent execution tracking
-- Adds concurrent_group_id, is_isolated, and recovered_at columns.

ALTER TABLE pipeline_states ADD COLUMN concurrent_group_id TEXT;
ALTER TABLE pipeline_states ADD COLUMN is_isolated INTEGER NOT NULL DEFAULT 1;
ALTER TABLE pipeline_states ADD COLUMN recovered_at TEXT;
