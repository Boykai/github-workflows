-- Migration: 007_housekeeping.sql
-- Housekeeping Issue Templates with Configurable Triggers

CREATE TABLE IF NOT EXISTS housekeeping_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    title_pattern TEXT NOT NULL,
    body_content TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'custom' CHECK(category IN ('built-in', 'custom')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS housekeeping_tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    template_id TEXT NOT NULL REFERENCES housekeeping_templates(id),
    sub_issue_config TEXT,
    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('time', 'count')),
    trigger_value TEXT NOT NULL,
    last_triggered_at TEXT,
    last_triggered_issue_count INTEGER NOT NULL DEFAULT 0,
    enabled INTEGER NOT NULL DEFAULT 1,
    cooldown_minutes INTEGER NOT NULL DEFAULT 5,
    project_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, project_id)
);

CREATE TABLE IF NOT EXISTS housekeeping_trigger_history (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES housekeeping_tasks(id),
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('scheduled', 'count-based', 'manual')),
    issue_url TEXT,
    issue_number INTEGER,
    status TEXT NOT NULL CHECK(status IN ('success', 'failure')),
    error_details TEXT,
    sub_issues_created INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_trigger_history_task_id ON housekeeping_trigger_history(task_id);
CREATE INDEX IF NOT EXISTS idx_trigger_history_timestamp ON housekeeping_trigger_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_housekeeping_tasks_project ON housekeeping_tasks(project_id);
