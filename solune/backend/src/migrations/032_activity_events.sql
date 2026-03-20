-- Activity events table for unified audit trail.
-- Stores all significant actions (pipeline runs, CRUD, triggers, etc.)
-- as denormalized summary rows for efficient feed queries.

CREATE TABLE IF NOT EXISTS activity_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'system',
    action TEXT NOT NULL,
    summary TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_activity_project_time
    ON activity_events (project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_activity_entity
    ON activity_events (entity_type, entity_id);
