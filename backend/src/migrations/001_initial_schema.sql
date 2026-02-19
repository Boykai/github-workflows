-- Migration 001: Initial schema for settings storage

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

CREATE INDEX IF NOT EXISTS idx_sessions_github_user_id ON user_sessions(github_user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON user_sessions(updated_at);

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
);

CREATE TABLE IF NOT EXISTS project_settings (
    github_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    board_display_config TEXT,
    agent_pipeline_mappings TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (github_user_id, project_id)
);

CREATE INDEX IF NOT EXISTS idx_project_settings_user ON project_settings(github_user_id);

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
);
