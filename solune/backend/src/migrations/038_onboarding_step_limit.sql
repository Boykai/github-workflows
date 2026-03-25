-- Migration 038: Expand onboarding_tour_state current_step CHECK constraint
-- from <= 10 to <= 13 to support 14 tour steps (0-indexed 0–13).
--
-- SQLite does not support ALTER TABLE ... ALTER CONSTRAINT, so we use
-- the standard table-rebuild pattern.

-- Step 1: Create temp table with new constraint
CREATE TABLE onboarding_tour_state_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    current_step INTEGER NOT NULL DEFAULT 0
        CHECK (current_step >= 0 AND current_step <= 13),
    completed INTEGER NOT NULL DEFAULT 0
        CHECK (completed IN (0, 1)),
    dismissed_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- Step 2: Copy existing data
INSERT INTO onboarding_tour_state_new
    (id, user_id, current_step, completed, dismissed_at, completed_at, created_at, updated_at)
SELECT
    id, user_id, current_step, completed, dismissed_at, completed_at, created_at, updated_at
FROM onboarding_tour_state;

-- Step 3: Drop original table
DROP TABLE onboarding_tour_state;

-- Step 4: Rename new table to original name
ALTER TABLE onboarding_tour_state_new RENAME TO onboarding_tour_state;

-- Step 5: Recreate trigger
CREATE TRIGGER IF NOT EXISTS trg_onboarding_tour_state_updated_at
AFTER UPDATE ON onboarding_tour_state
FOR EACH ROW
BEGIN
    UPDATE onboarding_tour_state SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE id = OLD.id;
END;
