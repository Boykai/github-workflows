-- Migration 025: Fix apps table foreign key reference
-- The apps table incorrectly references the non-existent workflow_configurations
-- table. The correct table is pipeline_configs.

-- Disable FK checks during table recreation
PRAGMA foreign_keys = OFF;

-- Recreate apps table with the correct foreign key
CREATE TABLE apps_new (
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
    FOREIGN KEY (associated_pipeline_id) REFERENCES pipeline_configs(id)
        ON DELETE SET NULL
);

-- Copy existing data (if any)
INSERT INTO apps_new SELECT * FROM apps;

-- Swap tables
DROP TABLE apps;
ALTER TABLE apps_new RENAME TO apps;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_apps_status ON apps(status);
CREATE INDEX IF NOT EXISTS idx_apps_created_at ON apps(created_at);

-- Recreate trigger
CREATE TRIGGER IF NOT EXISTS trg_apps_updated_at
    AFTER UPDATE ON apps
    FOR EACH ROW
BEGIN
    UPDATE apps SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE name = OLD.name;
END;

-- Re-enable FK checks
PRAGMA foreign_keys = ON;
