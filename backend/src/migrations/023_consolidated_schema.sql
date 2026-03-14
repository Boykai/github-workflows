-- Consolidated schema (replaces migrations 001–023)
-- Generated from the full migration history on 2026-03-14
--
-- This single file creates every table, index, and constraint
-- that the application requires.  New migrations after this
-- consolidation should be numbered 024+.

-- ── Tables ────────────────────────────────────────────────

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
    created_at TEXT NOT NULL DEFAULT (datetime('now')), lifecycle_status TEXT NOT NULL DEFAULT 'pending_pr', default_model_id TEXT NOT NULL DEFAULT '', default_model_name TEXT NOT NULL DEFAULT '', icon_name TEXT,
    UNIQUE(name, project_id)
);

CREATE TABLE IF NOT EXISTS agent_tool_associations (
    agent_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (agent_id, tool_id)
);

CREATE TABLE IF NOT EXISTS agent_trigger_inflight (
    trigger_key TEXT PRIMARY KEY,
    started_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    action_type TEXT,
    action_data TEXT,
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS chat_proposals (
    proposal_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    original_input TEXT NOT NULL,
    proposed_title TEXT NOT NULL,
    proposed_description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'edited', 'cancelled')),
    edited_title TEXT,
    edited_description TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    expires_at TEXT
, file_urls TEXT DEFAULT NULL, selected_pipeline_id TEXT DEFAULT NULL);

CREATE TABLE IF NOT EXISTS chat_recommendations (
    recommendation_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    data TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
, file_urls TEXT DEFAULT NULL);

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
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')), execution_count INTEGER NOT NULL DEFAULT 0, ai_enhance_enabled INTEGER NOT NULL DEFAULT 1, agent_pipeline_id TEXT NOT NULL DEFAULT '', is_preset INTEGER NOT NULL DEFAULT 0, preset_id TEXT NOT NULL DEFAULT '',
    UNIQUE(name, project_id),
    CHECK(
        (schedule_type IS NULL AND schedule_value IS NULL) OR
        (schedule_type IS NOT NULL AND schedule_value IS NOT NULL AND schedule_value > 0)
    )
);

CREATE TABLE IF NOT EXISTS cleanup_audit_logs (
    id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL,
    owner TEXT NOT NULL,
    repo TEXT NOT NULL,
    project_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'in_progress',
    branches_deleted INTEGER NOT NULL DEFAULT 0,
    branches_preserved INTEGER NOT NULL DEFAULT 0,
    prs_closed INTEGER NOT NULL DEFAULT 0,
    prs_preserved INTEGER NOT NULL DEFAULT 0,
    errors_count INTEGER NOT NULL DEFAULT 0,
    details TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS github_metadata_cache (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_key    TEXT NOT NULL,
    field_type  TEXT NOT NULL,
    value       TEXT NOT NULL,
    fetched_at  TEXT NOT NULL,
    UNIQUE(repo_key, field_type, value)
);

CREATE TABLE IF NOT EXISTS global_settings (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK(id = 1),
    ai_provider TEXT NOT NULL DEFAULT 'copilot',
    ai_model TEXT NOT NULL DEFAULT 'gpt-4o',
    ai_temperature REAL NOT NULL DEFAULT 0.7,
    theme TEXT NOT NULL DEFAULT 'light',
    default_view TEXT NOT NULL DEFAULT 'chat',
    sidebar_collapsed INTEGER NOT NULL DEFAULT 0,
    default_repository TEXT,
    default_assignee TEXT NOT NULL DEFAULT '',
    copilot_polling_interval INTEGER NOT NULL DEFAULT 60,
    notify_task_status_change INTEGER NOT NULL DEFAULT 1,
    notify_agent_completion INTEGER NOT NULL DEFAULT 1,
    notify_new_recommendation INTEGER NOT NULL DEFAULT 1,
    notify_chat_mention INTEGER NOT NULL DEFAULT 1,
    allowed_models TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL
, admin_github_user_id TEXT DEFAULT NULL, ai_agent_model TEXT);

CREATE TABLE IF NOT EXISTS issue_main_branches (
    issue_number INTEGER PRIMARY KEY,
    branch TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    head_sha TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS issue_sub_issue_map (
    issue_number INTEGER NOT NULL,
    agent_name TEXT NOT NULL,
    sub_issue_number INTEGER NOT NULL,
    sub_issue_node_id TEXT NOT NULL,
    sub_issue_url TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    PRIMARY KEY (issue_number, agent_name)
);

CREATE TABLE IF NOT EXISTS mcp_configurations (
    id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
, description TEXT NOT NULL DEFAULT '', config_content TEXT NOT NULL DEFAULT '{}', sync_status TEXT NOT NULL DEFAULT 'pending', sync_error TEXT NOT NULL DEFAULT '', synced_at TEXT, github_repo_target TEXT NOT NULL DEFAULT '', project_id TEXT NOT NULL DEFAULT '');

CREATE TABLE IF NOT EXISTS pipeline_configs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    stages TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL, is_preset INTEGER NOT NULL DEFAULT 0, preset_id TEXT NOT NULL DEFAULT '',
    UNIQUE(name, project_id)
);

CREATE TABLE IF NOT EXISTS pipeline_states (
    issue_number INTEGER PRIMARY KEY,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL,
    agent_name TEXT,
    agent_instance_id TEXT,
    pr_number INTEGER,
    pr_url TEXT,
    sub_issues TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS project_settings (
    github_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    board_display_config TEXT,
    agent_pipeline_mappings TEXT,
    updated_at TEXT NOT NULL, workflow_config TEXT, assigned_pipeline_id TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (github_user_id, project_id)
);

CREATE TABLE IF NOT EXISTS signal_conflict_banners (
    id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL,
    message TEXT NOT NULL,
    dismissed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signal_connections (
    id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL UNIQUE,
    signal_phone_encrypted TEXT NOT NULL,
    signal_phone_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    notification_mode TEXT NOT NULL DEFAULT 'all',
    last_active_project_id TEXT,
    linked_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signal_messages (
    id TEXT PRIMARY KEY,
    connection_id TEXT NOT NULL,
    direction TEXT NOT NULL,
    chat_message_id TEXT,
    content_preview TEXT,
    delivery_status TEXT NOT NULL DEFAULT 'pending',
    retry_count INTEGER NOT NULL DEFAULT 0,
    next_retry_at TEXT,
    error_detail TEXT,
    created_at TEXT NOT NULL,
    delivered_at TEXT
);

CREATE TABLE IF NOT EXISTS user_preferences (
    github_user_id TEXT PRIMARY KEY,
    ai_provider TEXT,
    ai_model TEXT,
    ai_temperature REAL,
    theme TEXT,
    default_view TEXT,
    sidebar_collapsed INTEGER,
    default_repository TEXT,
    default_assignee TEXT,
    copilot_polling_interval INTEGER,
    notify_task_status_change INTEGER,
    notify_agent_completion INTEGER,
    notify_new_recommendation INTEGER,
    notify_chat_mention INTEGER,
    updated_at TEXT NOT NULL
, ai_agent_model TEXT);

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL,
    github_username TEXT NOT NULL,
    github_avatar_url TEXT,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TEXT,
    selected_project_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- ── Indexes ───────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_agent_configs_project ON agent_configs(project_id);

CREATE INDEX IF NOT EXISTS idx_agent_configs_slug ON agent_configs(slug, project_id);

CREATE INDEX IF NOT EXISTS idx_agent_tools_agent
    ON agent_tool_associations(agent_id);

CREATE INDEX IF NOT EXISTS idx_agent_tools_tool
    ON agent_tool_associations(tool_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);

CREATE INDEX IF NOT EXISTS idx_chat_proposals_session ON chat_proposals(session_id);

CREATE INDEX IF NOT EXISTS idx_chat_recommendations_session ON chat_recommendations(session_id);

CREATE INDEX IF NOT EXISTS idx_chores_execution_count ON chores(execution_count DESC);

CREATE INDEX IF NOT EXISTS idx_chores_last_triggered_at ON chores(last_triggered_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_chores_preset
    ON chores(preset_id, project_id)
    WHERE preset_id != '';

CREATE INDEX IF NOT EXISTS idx_chores_project_id ON chores(project_id);

CREATE INDEX IF NOT EXISTS idx_chores_status ON chores(status);

CREATE INDEX IF NOT EXISTS idx_cleanup_audit_repo ON cleanup_audit_logs(owner, repo);

CREATE INDEX IF NOT EXISTS idx_cleanup_audit_user ON cleanup_audit_logs(github_user_id);

CREATE INDEX IF NOT EXISTS idx_mcp_configs_project
    ON mcp_configurations(project_id);

CREATE INDEX IF NOT EXISTS idx_mcp_configs_sync_status
    ON mcp_configurations(sync_status);

CREATE INDEX IF NOT EXISTS idx_mcp_configs_user ON mcp_configurations(github_user_id);

CREATE INDEX IF NOT EXISTS idx_mcp_configs_user_name ON mcp_configurations(github_user_id, name);

CREATE INDEX IF NOT EXISTS idx_metadata_cache_repo_type
    ON github_metadata_cache(repo_key, field_type);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pipeline_configs_preset
    ON pipeline_configs(preset_id, project_id)
    WHERE preset_id != '';

CREATE INDEX IF NOT EXISTS idx_pipeline_configs_project_id
    ON pipeline_configs(project_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_configs_updated_at
    ON pipeline_configs(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_project_settings_user ON project_settings(github_user_id);

CREATE INDEX IF NOT EXISTS idx_sessions_github_user_id ON user_sessions(github_user_id);

CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON user_sessions(updated_at);

CREATE INDEX IF NOT EXISTS idx_signal_banner_user ON signal_conflict_banners(github_user_id)
    WHERE dismissed = 0;

CREATE UNIQUE INDEX IF NOT EXISTS idx_signal_conn_phone_hash
    ON signal_connections(signal_phone_hash)
    WHERE signal_phone_hash != '';

CREATE INDEX IF NOT EXISTS idx_signal_conn_status ON signal_connections(status);

CREATE INDEX IF NOT EXISTS idx_signal_conn_user ON signal_connections(github_user_id);

CREATE INDEX IF NOT EXISTS idx_signal_msg_conn ON signal_messages(connection_id);

CREATE INDEX IF NOT EXISTS idx_signal_msg_retry ON signal_messages(next_retry_at)
    WHERE delivery_status = 'retrying';

CREATE INDEX IF NOT EXISTS idx_signal_msg_status ON signal_messages(delivery_status);
