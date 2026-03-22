-- 037: Phase 8 — Create recovery_log table for label-driven state recovery auditing.

CREATE TABLE IF NOT EXISTS recovery_log (
    issue_number INTEGER NOT NULL,
    project_id TEXT NOT NULL,
    source_labels_json TEXT NOT NULL,
    reconstructed_stage TEXT,
    reconstructed_status TEXT,
    confidence TEXT NOT NULL
        CHECK (confidence IN ('high', 'medium', 'low', 'ambiguous')),
    ambiguity_flags_json TEXT NOT NULL DEFAULT '[]',
    requires_manual_review INTEGER NOT NULL DEFAULT 0,
    recovered_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    recovery_source TEXT NOT NULL DEFAULT 'labels'
        CHECK (recovery_source IN ('labels', 'database', 'mixed')),
    PRIMARY KEY (issue_number, project_id, recovered_at)
);
