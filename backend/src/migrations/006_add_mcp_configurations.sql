-- Migration 006: Add MCP configurations table for GitHub agent settings

CREATE TABLE IF NOT EXISTS mcp_configurations (
    id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mcp_configs_user ON mcp_configurations(github_user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_configs_user_name ON mcp_configurations(github_user_id, name);
