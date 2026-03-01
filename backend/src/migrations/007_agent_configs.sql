-- Migration 007: Create agent_configs table for custom agent definitions.
-- Stores agents created via the #agent chat command.

CREATE TABLE IF NOT EXISTS agent_configs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    status_column TEXT NOT NULL,
    tools TEXT NOT NULL DEFAULT '[]',
    project_id TEXT NOT NULL,
    owner TEXT NOT NULL,
    repo TEXT NOT NULL,
    created_by TEXT NOT NULL,
    github_issue_number INTEGER,
    github_pr_number INTEGER,
    branch_name TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, project_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_configs_project ON agent_configs(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_configs_slug ON agent_configs(slug, project_id);
