-- Migration 011: Create github_metadata_cache table for repository metadata caching.
-- Stores labels, branches, milestones, and collaborators fetched from GitHub API.

CREATE TABLE IF NOT EXISTS github_metadata_cache (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_key    TEXT NOT NULL,
    field_type  TEXT NOT NULL,
    value       TEXT NOT NULL,
    fetched_at  TEXT NOT NULL,
    UNIQUE(repo_key, field_type, value)
);

CREATE INDEX IF NOT EXISTS idx_metadata_cache_repo_type
    ON github_metadata_cache(repo_key, field_type);
