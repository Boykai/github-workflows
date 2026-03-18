-- 029: Pipeline state persistence, stage groups, and onboarding tour state
-- Adds tables for durable pipeline run tracking (FR-001, FR-002, FR-003),
-- execution groups (FR-016), onboarding tour progress (FR-038),
-- and extends projects/agents with new columns.

-- ── Pipeline Runs ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_config_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    trigger TEXT NOT NULL DEFAULT 'manual',
    error_message TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (pipeline_config_id) REFERENCES pipeline_configs(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_config ON pipeline_runs(pipeline_config_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_project ON pipeline_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status)
    WHERE status IN ('pending', 'running');

CREATE TRIGGER IF NOT EXISTS trg_pipeline_runs_updated_at
AFTER UPDATE ON pipeline_runs
FOR EACH ROW
BEGIN
    UPDATE pipeline_runs SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE id = OLD.id;
END;

-- ── Stage Groups ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS stage_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_config_id TEXT NOT NULL,
    name TEXT NOT NULL,
    execution_mode TEXT NOT NULL DEFAULT 'sequential'
        CHECK (execution_mode IN ('sequential', 'parallel')),
    order_index INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (pipeline_config_id) REFERENCES pipeline_configs(id)
        ON DELETE CASCADE,
    UNIQUE (pipeline_config_id, order_index)
);

CREATE INDEX IF NOT EXISTS idx_stage_groups_config ON stage_groups(pipeline_config_id);

CREATE TRIGGER IF NOT EXISTS trg_stage_groups_updated_at
AFTER UPDATE ON stage_groups
FOR EACH ROW
BEGIN
    UPDATE stage_groups SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE id = OLD.id;
END;

-- ── Pipeline Stage States ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS pipeline_stage_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER NOT NULL,
    stage_id TEXT NOT NULL,
    group_id INTEGER,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    started_at TEXT,
    completed_at TEXT,
    agent_id TEXT,
    output TEXT,
    label_name TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs(id)
        ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES stage_groups(id)
        ON DELETE SET NULL,
    UNIQUE (pipeline_run_id, stage_id)
);

CREATE INDEX IF NOT EXISTS idx_stage_states_run ON pipeline_stage_states(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_stage_states_status ON pipeline_stage_states(status)
    WHERE status IN ('pending', 'running');

CREATE TRIGGER IF NOT EXISTS trg_pipeline_stage_states_updated_at
AFTER UPDATE ON pipeline_stage_states
FOR EACH ROW
BEGIN
    UPDATE pipeline_stage_states SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE id = OLD.id;
END;

-- ── Onboarding Tour State ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS onboarding_tour_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    current_step INTEGER NOT NULL DEFAULT 0
        CHECK (current_step >= 0 AND current_step <= 10),
    completed INTEGER NOT NULL DEFAULT 0
        CHECK (completed IN (0, 1)),
    dismissed_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TRIGGER IF NOT EXISTS trg_onboarding_tour_state_updated_at
AFTER UPDATE ON onboarding_tour_state
FOR EACH ROW
BEGIN
    UPDATE onboarding_tour_state SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE id = OLD.id;
END;

-- ── Extend project_settings table ──────────────────────────────
-- Add access_control_enabled column (FR-006)

ALTER TABLE project_settings ADD COLUMN access_control_enabled INTEGER NOT NULL DEFAULT 1;

-- ── Extend agents ──────────────────────────────────────────────
-- Agent visual_identifier and display_order for parallel layout (FR-018)
-- are stored within the pipeline_configs JSON blob (agents array), not as
-- separate columns.  No ALTER TABLE is needed.
