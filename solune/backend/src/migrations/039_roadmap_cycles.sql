-- Migration 039: Create roadmap_cycles audit table for the Self-Evolving Roadmap Engine.
-- Stores cycle records for history queries and title-based deduplication.

CREATE TABLE IF NOT EXISTS roadmap_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    batch_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_roadmap_cycles_project_id
    ON roadmap_cycles(project_id);

CREATE INDEX IF NOT EXISTS idx_roadmap_cycles_project_created
    ON roadmap_cycles(project_id, created_at DESC);
