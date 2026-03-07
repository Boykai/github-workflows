-- Migration 013: Track agent lifecycle state for repo/list reconciliation.

ALTER TABLE agent_configs
ADD COLUMN lifecycle_status TEXT NOT NULL DEFAULT 'pending_pr';

UPDATE agent_configs
SET lifecycle_status = COALESCE(NULLIF(lifecycle_status, ''), 'pending_pr');