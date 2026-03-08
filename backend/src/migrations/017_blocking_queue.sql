-- Migration 017: Blocking Queue — Serial Issue Activation & Branch Ancestry Control
--
-- New table for per-repository blocking queue that serializes issue activation
-- and controls branch ancestry when blocking issues exist.

CREATE TABLE IF NOT EXISTS blocking_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_key TEXT NOT NULL,
    issue_number INTEGER NOT NULL,
    project_id TEXT NOT NULL,
    is_blocking INTEGER NOT NULL DEFAULT 0,
    queue_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (queue_status IN ('pending', 'active', 'in_review', 'completed')),
    parent_branch TEXT,
    blocking_source_issue INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    activated_at TEXT,
    completed_at TEXT,
    UNIQUE(repo_key, issue_number)
);

CREATE INDEX IF NOT EXISTS idx_blocking_queue_repo_status
    ON blocking_queue(repo_key, queue_status);

CREATE INDEX IF NOT EXISTS idx_blocking_queue_repo_blocking
    ON blocking_queue(repo_key, is_blocking, queue_status);

-- Add blocking column to pipeline_configs
ALTER TABLE pipeline_configs ADD COLUMN blocking INTEGER NOT NULL DEFAULT 0;

-- Add blocking column to chores
ALTER TABLE chores ADD COLUMN blocking INTEGER NOT NULL DEFAULT 0;
