-- Migration 024: Application management
-- Supports multi-app lifecycle (create, start, stop, delete) for the Solune platform.

CREATE TABLE IF NOT EXISTS apps (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    directory_path TEXT NOT NULL,
    associated_pipeline_id TEXT,
    status TEXT NOT NULL DEFAULT 'creating'
        CHECK (status IN ('creating', 'active', 'stopped', 'error')),
    repo_type TEXT NOT NULL DEFAULT 'same-repo'
        CHECK (repo_type IN ('same-repo', 'external-repo')),
    external_repo_url TEXT,
    port INTEGER,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (associated_pipeline_id) REFERENCES workflow_configurations(id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_apps_status ON apps(status);
CREATE INDEX IF NOT EXISTS idx_apps_created_at ON apps(created_at);

-- Trigger to auto-update updated_at on row modification
CREATE TRIGGER IF NOT EXISTS trg_apps_updated_at
    AFTER UPDATE ON apps
    FOR EACH ROW
BEGIN
    UPDATE apps SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE name = OLD.name;
END;
