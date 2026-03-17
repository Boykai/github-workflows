-- 028: Add new-repo support to apps table
-- Adds columns for GitHub repo/project URLs and project ID.
-- Recreates the repo_type CHECK constraint to include 'new-repo'.

-- Step 1: Add new columns (nullable TEXT)
ALTER TABLE apps ADD COLUMN github_repo_url TEXT DEFAULT NULL;
ALTER TABLE apps ADD COLUMN github_project_url TEXT DEFAULT NULL;
ALTER TABLE apps ADD COLUMN github_project_id TEXT DEFAULT NULL;

-- Step 2: Recreate the apps table with the updated CHECK constraint.
-- SQLite does not support ALTER TABLE … DROP CONSTRAINT, so we must
-- recreate the table to update the CHECK.

CREATE TABLE apps_new (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT DEFAULT '',
    directory_path TEXT NOT NULL,
    associated_pipeline_id TEXT,
    status TEXT NOT NULL CHECK (status IN ('creating', 'active', 'stopped', 'error')),
    repo_type TEXT NOT NULL CHECK (repo_type IN ('same-repo', 'external-repo', 'new-repo')),
    external_repo_url TEXT,
    github_repo_url TEXT,
    github_project_url TEXT,
    github_project_id TEXT,
    port INTEGER,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (associated_pipeline_id) REFERENCES workflow_configurations(id)
);

INSERT INTO apps_new (
    name, display_name, description, directory_path,
    associated_pipeline_id, status, repo_type, external_repo_url,
    github_repo_url, github_project_url, github_project_id,
    port, error_message, created_at, updated_at
)
SELECT
    name, display_name, description, directory_path,
    associated_pipeline_id, status, repo_type, external_repo_url,
    github_repo_url, github_project_url, github_project_id,
    port, error_message, created_at, updated_at
FROM apps;

DROP TABLE apps;

ALTER TABLE apps_new RENAME TO apps;

-- Re-create indexes
CREATE INDEX IF NOT EXISTS idx_apps_status ON apps(status);
CREATE INDEX IF NOT EXISTS idx_apps_created_at ON apps(created_at);

-- Re-create the updated_at trigger
CREATE TRIGGER IF NOT EXISTS trg_apps_updated_at
AFTER UPDATE ON apps
FOR EACH ROW
BEGIN
    UPDATE apps SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE name = NEW.name;
END;
