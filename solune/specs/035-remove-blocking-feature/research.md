# Research: Remove Blocking Feature Entirely from Application

**Branch**: `035-remove-blocking-feature` | **Date**: 2026-03-12 | **Plan**: [plan.md](./plan.md)

## R-001: Blocking Feature Implementation Status

**Decision**: The blocking feature is **partially implemented** — database migrations and integration call sites exist, but core modules were never created.

**Rationale**: A comprehensive codebase audit reveals that the feature was designed and scaffolded into existing services via try/except guarded imports, but the actual implementation files were never committed. This makes removal simpler: most call sites already handle the absence gracefully via exception handling. The primary work is removing the dead integration code and the database migrations that would create blocking schema.

**Alternatives considered**:
- *Full rollback via git revert*: Rejected because blocking code was added incrementally across many commits and interleaved with other changes.
- *Feature flag disable*: Rejected because the spec explicitly requires complete removal, not disabling. Feature flags themselves must be removed per FR-011.

### Detailed Audit Findings

#### Missing Implementation Files (never created)
| Module | Expected Path | Status |
|--------|--------------|--------|
| `BlockingQueueEntry` model | `backend/src/models/blocking.py` | ❌ Does not exist |
| `BlockingQueueStatus` enum | `backend/src/models/blocking.py` | ❌ Does not exist |
| `blocking_queue` service | `backend/src/services/blocking_queue.py` | ❌ Does not exist |
| `blocking_queue_store` | `backend/src/services/blocking_queue_store.py` | ❌ Does not exist |
| `with_blocking_label()` | `backend/src/constants.py` | ❌ Not defined in file |
| `is_blocking` field | `backend/src/models/recommendation.py` | ❌ Not on model |

#### Existing Integration Points (to be removed)

| File | Lines | Nature |
|------|-------|--------|
| `backend/src/api/chat.py` | 762–763, 885–887, 913–928 | `proposal.is_blocking` access + blocking_queue enqueue |
| `backend/src/api/workflow.py` | 269 | `is_blocking=recommendation.is_blocking` parameter |
| `backend/src/services/workflow_orchestrator/orchestrator.py` | 12, 619, 2288, 2305, 2365 | `with_blocking_label` import, blocking queue enqueue, `is_blocking` param |
| `backend/src/services/signal_chat.py` | 20, 389, 453 | `with_blocking_label` import + calls |
| `backend/src/services/chores/service.py` | 21–55, 77, 539–585 | Preset blocking flags, blocking column, blocking resolution logic |
| `backend/src/services/copilot_polling/polling_loop.py` | 242–261, 291 | `_step_sweep_blocking_queue` function + Step 4c registration |
| `backend/src/services/copilot_polling/pipeline.py` | 1530–1596, 2357–2407 | `mark_completed`/`mark_in_review` calls + `_activate_queued_issue` |
| `backend/src/services/copilot_polling/recovery.py` | 110, 124–139, 338 | `BlockingQueueStatus` import + queue guard |

#### Database Migrations (to be removed/rolled back)

| Migration | File | Changes |
|-----------|------|---------|
| 017 | `017_blocking_queue.sql` | Creates `blocking_queue` table, adds `blocking` column to `pipeline_configs` and `chores` |
| 018 | `018_pipeline_blocking_override.sql` | Adds `pipeline_blocking_override` column to `project_settings` |

#### Test Files Affected

| File | Nature |
|------|--------|
| `backend/tests/unit/test_chat_block.py` | Entire file tests `#block` detection — remove entirely |
| `backend/tests/unit/test_api_board.py` | `TestSkipBlockingIssue` + `TestDeleteBlockingIssue` classes — remove |
| `backend/tests/unit/test_copilot_polling.py` | Blocking queue mock references — clean up |
| `backend/tests/unit/test_api_pipelines.py` | Blocking mock references — clean up |
| `frontend/src/components/board/ProjectIssueLaunchPanel.test.tsx` | `blocking: false` in mock data — remove field |
| `frontend/src/components/pipeline/SavedWorkflowsList.test.tsx` | `blocking: false` in mock data — remove field |
| `frontend/src/pages/ProjectsPage.test.tsx` | `blocking_override` mock references — remove |

---

## R-002: Database Migration Strategy

**Decision**: Create a new forward migration (`019_remove_blocking.sql`) that drops all blocking-related schema artifacts. Do NOT delete migration files 017 and 018 — they must remain for migration history integrity.

**Rationale**: The application uses sequential numbered migrations. Deleting historical migrations would break the migration runner for any existing database that has already applied them. The correct approach is a new migration that reverses the schema changes.

**Alternatives considered**:
- *Delete migration files 017 and 018*: Rejected because existing databases may have already run these migrations. Deleting them would cause the migration runner to lose track of applied state.
- *Manual SQL cleanup*: Rejected because it's not reproducible and violates the migration-based schema management pattern.

### Migration 019 Content

```sql
-- Migration 019: Remove blocking feature schema artifacts
-- Rolls back migrations 017 and 018

-- Drop the blocking_queue table and its indexes
DROP TABLE IF EXISTS blocking_queue;

-- Remove blocking column from pipeline_configs
-- SQLite does not support DROP COLUMN before 3.35.0; use safe approach
ALTER TABLE pipeline_configs DROP COLUMN blocking;

-- Remove blocking column from chores
ALTER TABLE chores DROP COLUMN blocking;

-- Remove pipeline_blocking_override from project_settings
ALTER TABLE project_settings DROP COLUMN pipeline_blocking_override;
```

---

## R-003: "Non-blocking" vs "Blocking Feature" Disambiguation

**Decision**: Only remove references to the **Blocking feature** (blocking queue, `#block` detection, `is_blocking` flags, blocking labels). Preserve all references to "non-blocking" in the generic programming sense (e.g., non-blocking I/O, non-blocking label cleanup operations).

**Rationale**: The spec explicitly states (Assumptions section): "The term 'blocking' in the context of this removal refers specifically to the Blocking feature and its domain concepts — not to generic programming constructs (e.g., blocking I/O, thread blocking) which are unrelated and should remain untouched."

**Lines to preserve (NOT remove)**:
- `pipeline.py:454` — "clean up pipeline labels (non-blocking)" — refers to non-blocking I/O pattern
- `pipeline.py:486` — "Non-blocking: failed to clean up pipeline labels" — refers to fire-and-forget pattern
- `pipeline.py:1237` — "blocking pipeline advance until" — refers to a child PR blocking pipeline advancement (workflow concept, not the Blocking feature)
- `recovery.py:189` — "Apply stalled label before re-assignment (non-blocking)" — refers to non-blocking I/O
- `recovery.py:200` — "Non-blocking: failed to apply stalled label" — refers to fire-and-forget pattern

---

## R-004: Frontend Blocking UI Components

**Decision**: No frontend UI components for the blocking feature exist. Only test mock data fields need cleanup.

**Rationale**: The audit found zero blocking-related UI components, views, panels, or navigation items in the frontend source code (`frontend/src/`). The blocking feature UI was never built. The only frontend references are in test files where mock data includes `blocking: false` or `blocking_override` fields. These must be cleaned to prevent confusion and ensure mock data matches actual API contracts.

**Alternatives considered**:
- *Leave test mock fields in place*: Rejected because they reference fields that don't exist on the actual API response types, creating confusion for future developers.

---

## R-005: Chores Service Preset Blocking Flags

**Decision**: Remove the `"blocking"` key from all chore preset definitions and from `_CHORE_UPDATABLE_COLUMNS`, plus remove the blocking resolution logic block in the chore service.

**Rationale**: The chore presets (`security-review`, `performance-review`, `bug-basher`) include a `"blocking"` flag that controls whether chore-created issues enter the blocking queue. Since the blocking queue is being removed entirely, these flags serve no purpose. The `blocking` column will also be dropped from the `chores` database table via migration 019.

**Specific removals in chores/service.py**:
1. Remove `"blocking": False` / `"blocking": True` from preset dictionaries (lines 21–55)
2. Remove `"blocking"` from `_CHORE_UPDATABLE_COLUMNS` set (line 77)
3. Remove the blocking flag resolution block (lines ~539–585) that resolves `is_blocking` from chore → assignment → pipeline
4. Remove the blocking_queue enqueue try/except block that follows
