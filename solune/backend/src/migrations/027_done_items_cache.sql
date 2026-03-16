-- 027: Cache for Done-status project items to reduce cold-start API calls
-- Items in "Done" rarely change; persisting them avoids re-fetching from
-- the GitHub GraphQL API on every fresh login / server restart.

CREATE TABLE IF NOT EXISTS done_items_cache (
    project_id   TEXT    NOT NULL,
    item_type    TEXT    NOT NULL DEFAULT 'task',  -- 'task' or 'board'
    items_json   TEXT    NOT NULL,                 -- JSON array of serialised items
    item_count   INTEGER NOT NULL DEFAULT 0,
    data_hash    TEXT,                             -- hash for change detection
    updated_at   TEXT    NOT NULL,
    PRIMARY KEY (project_id, item_type)
);
