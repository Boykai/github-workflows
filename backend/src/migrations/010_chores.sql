-- Migration: 010_chores.sql
-- Replace Housekeeping with Chores feature

-- Drop housekeeping tables (reverse dependency order)
DROP TABLE IF EXISTS housekeeping_trigger_history;
DROP TABLE IF EXISTS housekeeping_tasks;
DROP TABLE IF EXISTS housekeeping_templates;

-- Create chores table
CREATE TABLE IF NOT EXISTS chores (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    template_path TEXT NOT NULL,
    template_content TEXT NOT NULL,
    schedule_type TEXT CHECK(schedule_type IN ('time', 'count') OR schedule_type IS NULL),
    schedule_value INTEGER,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'paused')),
    last_triggered_at TEXT,
    last_triggered_count INTEGER NOT NULL DEFAULT 0,
    current_issue_number INTEGER,
    current_issue_node_id TEXT,
    pr_number INTEGER,
    pr_url TEXT,
    tracking_issue_number INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(name, project_id),
    CHECK(
        (schedule_type IS NULL AND schedule_value IS NULL) OR
        (schedule_type IS NOT NULL AND schedule_value IS NOT NULL AND schedule_value > 0)
    )
);

CREATE INDEX IF NOT EXISTS idx_chores_project_id ON chores(project_id);
CREATE INDEX IF NOT EXISTS idx_chores_status ON chores(status);
