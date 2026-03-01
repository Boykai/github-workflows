-- Migration 008: Add cleanup audit logs table for branch/PR cleanup operations

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

CREATE INDEX IF NOT EXISTS idx_cleanup_audit_user ON cleanup_audit_logs(github_user_id);
CREATE INDEX IF NOT EXISTS idx_cleanup_audit_repo ON cleanup_audit_logs(owner, repo);
