-- Migration 019: Add persistent user_profiles table for profile page feature
CREATE TABLE IF NOT EXISTS user_profiles (
    github_user_id TEXT PRIMARY KEY,
    display_name TEXT,
    bio TEXT,
    avatar_path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_updated
    ON user_profiles(updated_at);