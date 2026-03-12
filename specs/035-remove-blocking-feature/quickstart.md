# Quickstart: Remove Blocking Feature Entirely from Application

**Branch**: `035-remove-blocking-feature` | **Date**: 2026-03-12 | **Plan**: [plan.md](./plan.md)

## Overview

This guide walks through the removal of the Blocking feature from the Solune application. The blocking feature was partially implemented — database migrations and integration call sites exist throughout the codebase, but core service and model files were never created. Removal involves excising all references across ~20 files and creating a rollback migration.

## Prerequisites

- Python ≥3.12 with backend dependencies installed: `cd backend && pip install -e ".[dev]"`
- Node.js with frontend dependencies installed: `cd frontend && npm install`
- Familiarity with the repository structure (backend/, frontend/)

## Removal Order

Execute removals in this order to maintain build integrity at each step:

### Phase 1: Backend Test Cleanup

Remove or update test files first since they import non-existent modules.

1. **Delete** `backend/tests/unit/test_chat_block.py` (entire file — tests `#block` detection)
2. **Edit** `backend/tests/unit/test_api_board.py`:
   - Remove `TestSkipBlockingIssue` class (lines ~273–397)
   - Remove `TestDeleteBlockingIssue` class (lines ~401–560)
3. **Edit** `backend/tests/unit/test_copilot_polling.py`: Remove blocking queue mock patches
4. **Edit** `backend/tests/unit/test_api_pipelines.py`: Remove blocking mock references

### Phase 2: Backend Service Integration Removal

Remove blocking references from service files in dependency order (leaves first).

1. **Edit** `backend/src/services/copilot_polling/polling_loop.py`:
   - Delete `_step_sweep_blocking_queue()` function
   - Remove Step 4c from `_POLL_STEPS` list
2. **Edit** `backend/src/services/copilot_polling/recovery.py`:
   - Remove `BlockingQueueStatus` import and blocking queue guard block
3. **Edit** `backend/src/services/copilot_polling/pipeline.py`:
   - Remove `mark_completed` / `mark_in_review` blocking queue calls
   - Remove `_activate_queued_issue()` function
4. **Edit** `backend/src/services/signal_chat.py`:
   - Remove `with_blocking_label` import
   - Replace `with_blocking_label([], ...)` calls with plain `[]`
5. **Edit** `backend/src/services/chores/service.py`:
   - Remove `"blocking"` from preset dictionaries
   - Remove `"blocking"` from `_CHORE_UPDATABLE_COLUMNS`
   - Remove blocking flag resolution logic block
   - Remove blocking_queue enqueue try/except block
6. **Edit** `backend/src/services/workflow_orchestrator/orchestrator.py`:
   - Remove `with_blocking_label` import from constants
   - Remove blocking_queue import and enqueue logic
   - Remove `is_blocking` parameter from `execute_full_workflow`
   - Replace `with_blocking_label(labels, ...)` with plain `labels`

### Phase 3: Backend API Cleanup

1. **Edit** `backend/src/api/chat.py`:
   - Remove `proposal_is_blocking` variable and all blocking queue enqueue code
   - Remove blocking-related comments
2. **Edit** `backend/src/api/workflow.py`:
   - Remove `is_blocking=recommendation.is_blocking` parameter

### Phase 4: Database Migration

1. **Create** `backend/src/migrations/019_remove_blocking.sql`:
   - DROP TABLE blocking_queue
   - DROP COLUMN blocking from pipeline_configs
   - DROP COLUMN blocking from chores
   - DROP COLUMN pipeline_blocking_override from project_settings

### Phase 5: Frontend Test Cleanup

1. **Edit** `frontend/src/components/board/ProjectIssueLaunchPanel.test.tsx`: Remove `blocking: false`
2. **Edit** `frontend/src/components/pipeline/SavedWorkflowsList.test.tsx`: Remove `blocking: false`
3. **Edit** `frontend/src/pages/ProjectsPage.test.tsx`: Remove `blocking_override` references

### Phase 6: Verification

1. Run backend tests: `cd backend && python -m pytest tests/unit/ -v`
2. Run frontend tests: `cd frontend && npx vitest run`
3. Run linters: `cd backend && python -m ruff check src/` and `cd frontend && npm run type-check && npm run lint`
4. Run comprehensive grep: `grep -ri "blocking" --include="*.py" --include="*.ts" --include="*.tsx" backend/src/ frontend/src/` — verify only non-feature "blocking" references remain (e.g., non-blocking I/O comments)

## Verification Checklist

- [ ] `python -m pytest tests/unit/ -v` — all tests pass
- [ ] `npx vitest run` — all tests pass
- [ ] `python -m ruff check src/` — no lint errors
- [ ] `npm run type-check` — no type errors
- [ ] `grep -ri "blocking_queue\|BlockingQueue\|is_blocked\|is_blocking\|with_blocking_label\|blocking_override" backend/src/ frontend/src/` — zero matches
- [ ] Application starts without import errors
- [ ] No empty UI gaps or orphaned sections
