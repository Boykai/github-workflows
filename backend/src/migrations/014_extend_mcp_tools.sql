-- Migration 014: Extend MCP configurations for Tools page
-- Adds description, config content, sync status tracking, project scoping

ALTER TABLE mcp_configurations ADD COLUMN description TEXT NOT NULL DEFAULT '';
ALTER TABLE mcp_configurations ADD COLUMN config_content TEXT NOT NULL DEFAULT '{}';
ALTER TABLE mcp_configurations ADD COLUMN sync_status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE mcp_configurations ADD COLUMN sync_error TEXT NOT NULL DEFAULT '';
ALTER TABLE mcp_configurations ADD COLUMN synced_at TEXT;
ALTER TABLE mcp_configurations ADD COLUMN github_repo_target TEXT NOT NULL DEFAULT '';
ALTER TABLE mcp_configurations ADD COLUMN project_id TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_mcp_configs_project
    ON mcp_configurations(project_id);

CREATE INDEX IF NOT EXISTS idx_mcp_configs_sync_status
    ON mcp_configurations(sync_status);

-- Junction table for many-to-many agent <-> MCP tool relationship
CREATE TABLE IF NOT EXISTS agent_tool_associations (
    agent_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (agent_id, tool_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_tools_agent
    ON agent_tool_associations(agent_id);

CREATE INDEX IF NOT EXISTS idx_agent_tools_tool
    ON agent_tool_associations(tool_id);
