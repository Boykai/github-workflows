-- Migration: 012_chat_persistence.sql
-- Description: Create tables for persistent chat message, proposal, and recommendation storage.
-- Previously these were stored in module-level in-memory dicts and lost on restart.

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    action_type TEXT,
    action_data TEXT,
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);

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
);

CREATE INDEX IF NOT EXISTS idx_chat_proposals_session ON chat_proposals(session_id);

CREATE TABLE IF NOT EXISTS chat_recommendations (
    recommendation_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    data TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_chat_recommendations_session ON chat_recommendations(session_id);
