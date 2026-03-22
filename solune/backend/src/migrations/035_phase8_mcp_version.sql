-- 035: Phase 8 — Add version column to mcp_configurations for optimistic concurrency control.

ALTER TABLE mcp_configurations ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
