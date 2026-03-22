-- 036: Phase 8 — Create collision_events table for MCP collision resolution auditing.

CREATE TABLE IF NOT EXISTS collision_events (
    collision_id TEXT PRIMARY KEY,
    target_entity_type TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    operation_a_json TEXT NOT NULL,
    operation_b_json TEXT NOT NULL,
    resolution_strategy TEXT NOT NULL
        CHECK (resolution_strategy IN ('last_write_wins', 'user_priority', 'manual_review')),
    resolution_outcome TEXT NOT NULL,
    winning_operation TEXT NOT NULL
        CHECK (winning_operation IN ('a', 'b', 'neither')),
    detected_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    resolved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_collision_events_entity
    ON collision_events(target_entity_type, target_entity_id);
