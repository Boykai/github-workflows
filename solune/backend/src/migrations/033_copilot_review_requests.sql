-- Durable storage for copilot-review request timestamps.
-- Survives server restarts so _check_copilot_review_done() can
-- recover the request timestamp without relying solely on in-memory
-- state or HTML comment parsing.

CREATE TABLE IF NOT EXISTS copilot_review_requests (
    issue_number INTEGER PRIMARY KEY,
    requested_at TEXT NOT NULL,
    project_id TEXT
);
