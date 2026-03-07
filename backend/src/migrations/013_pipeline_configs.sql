-- Pipeline configurations table for storing saved Agent Pipeline workflows.
-- Each pipeline has ordered stages with agent assignments and per-agent model selection.
-- Stages are stored as JSON (same pattern as workflow_config and agent tools).

CREATE TABLE IF NOT EXISTS pipeline_configs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    stages TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(name, project_id)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_configs_project_id
    ON pipeline_configs(project_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_configs_updated_at
    ON pipeline_configs(updated_at DESC);
