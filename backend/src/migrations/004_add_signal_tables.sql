-- Migration 004: Signal messaging integration tables

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

CREATE INDEX IF NOT EXISTS idx_signal_conn_user ON signal_connections(github_user_id);
CREATE INDEX IF NOT EXISTS idx_signal_conn_phone_hash ON signal_connections(signal_phone_hash);
CREATE INDEX IF NOT EXISTS idx_signal_conn_status ON signal_connections(status);

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

CREATE INDEX IF NOT EXISTS idx_signal_msg_conn ON signal_messages(connection_id);
CREATE INDEX IF NOT EXISTS idx_signal_msg_status ON signal_messages(delivery_status);
CREATE INDEX IF NOT EXISTS idx_signal_msg_retry ON signal_messages(next_retry_at)
    WHERE delivery_status = 'retrying';

CREATE TABLE IF NOT EXISTS signal_conflict_banners (
    id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL,
    message TEXT NOT NULL,
    dismissed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_signal_banner_user ON signal_conflict_banners(github_user_id)
    WHERE dismissed = 0;
