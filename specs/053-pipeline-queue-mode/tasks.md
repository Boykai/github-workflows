# Tasks: Pipeline Queue Mode Toggle

**Input**: Design documents from `/specs/053-pipeline-queue-mode/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are explicitly requested in the parent issue specification (Phase 4 covers unit, integration, and frontend tests).

**Organization**: Tasks are grouped into 4 phases following the parent issue structure: Backend Data Model → Backend Queue Logic → Frontend Toggle → Tests. User stories are mapped to tasks via requirement traceability.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/` (Python/FastAPI), `solune/frontend/` (React/TypeScript)
- Backend tests: `solune/backend/tests/`
- Frontend tests: colocated with source or via vitest

---

## Phase 1: Backend Data Model (Foundational)

**Purpose**: Add the `queue_mode` column to the database and expose it through the settings model, store, and API layers. This phase MUST complete before any queue logic can be implemented.

- [x] T001 [P] [US1] **New migration** `solune/backend/src/migrations/031_queue_mode.sql` — `ALTER TABLE project_settings ADD COLUMN queue_mode INTEGER NOT NULL DEFAULT 0`
- [x] T002 [P] [US1] **Update** `ProjectBoardConfig` in `solune/backend/src/models/settings.py` — add `queue_mode: bool = False`; add `queue_mode: bool | None = None` to `ProjectSettingsUpdate`
- [x] T003 [US1] **Update** `PROJECT_SETTINGS_COLUMNS` + `upsert_project_settings()` SQL in `solune/backend/src/services/settings_store.py` to include the new column
- [x] T004 [US1] **Update** the PUT handler in `solune/backend/src/api/settings.py` to persist `queue_mode`

**Checkpoint**: Queue mode setting can be read and written via API. Toggle persistence verified.

---

## Phase 2: Backend Queue Logic

**Purpose**: Implement the core queue enforcement — gate agent assignment when queue is active, and dequeue the next pipeline when the active one completes.

- [x] T005 [US2] **Add** `count_active_pipelines_for_project(project_id)` helper in `solune/backend/src/services/pipeline_state_store.py` — scans L1 cache, O(n) but fast for realistic cardinality
- [x] T006 [US1] **Add** `is_queue_mode_enabled(project_id)` helper in `solune/backend/src/services/settings_store.py` — reads from DB with short-TTL BoundedDict cache
- [x] T007 [US2] **Gate agent assignment** in `execute_pipeline_launch()` in `solune/backend/src/api/pipelines.py` — between `set_pipeline_state` (L350) and `assign_agent_for_status` (L363): if queue is ON AND another pipeline is active, skip agent assignment & polling start, mark state as `queued=True`, return "Pipeline queued" message
- [x] T008 [US3] **Dequeue on completion** in `_transition_after_pipeline_complete()` in `solune/backend/src/services/copilot_polling/pipeline.py` — after `remove_pipeline_state()` (L1928), check queue mode, find oldest queued pipeline by `started_at` (FIFO), call `assign_agent_for_status()` on it
- [x] T009 [P] [US2] **Add** `queued: bool = False` to `PipelineState` dataclass in `solune/backend/src/services/workflow_orchestrator/models.py`
- [x] T010 [US3] **Add** dequeue trigger in `check_in_review_issues()` and done-detection in the polling loop for the "In Review" / "Done" slot-release paths in `solune/backend/src/services/copilot_polling/pipeline.py`

**Checkpoint**: Queue gate blocks agent assignment when another pipeline is active. Dequeue automatically starts the next pipeline on completion.

---

## Phase 3: Frontend Toggle

**Purpose**: Add the Queue Mode toggle UI, "Queued" badge on issue cards, and queue position toast notification.

- [x] T011 [P] [US1] **Update types** in `solune/frontend/src/types/index.ts` — add `queue_mode` to `ProjectBoardConfig`, `ProjectSettingsUpdate`, `ProjectSpecificSettings`, and `PipelineStateInfo`
- [x] T012 [US1] **Add toggle** in `solune/frontend/src/pages/ProjectsPage.tsx` toolbar row (around L201) — `ToolbarButton`-style pill using existing pattern, `ListOrdered` icon from lucide-react, label "Queue Mode", backed by `useProjectSettings` hook; tooltip: "Only one pipeline runs at a time — next starts when active reaches In Review or Done"
- [x] T013 [US5] **Add "Queued" badge** on `solune/frontend/src/components/board/IssueCard.tsx` when pipeline state has `queued: true` — small clock/queue icon badge on the card
- [x] T014 [US2] **Show queue position** in launch toast — when response message indicates "queued", display "Pipeline queued — position #N"

**Checkpoint**: Toggle renders and persists setting. "Queued" badge appears on queued pipeline cards. Toast shows queue position.

---

## Phase 4: Tests

**Purpose**: Verify queue mode behavior with unit, integration, and frontend tests.

- [x] T015 [P] [US2, US3, US4] **New** `solune/backend/tests/unit/test_queue_mode.py` — gate logic (queue ON + active → no agent), dequeue FIFO ordering, queue OFF preserves immediate behavior, `count_active_pipelines_for_project()` at 0/1/N
- [x] T016 [P] [US2, US3] **New** `solune/backend/tests/integration/test_queue_mode.py` — launch 2 issues with queue ON → first starts, second is queued → complete first → second auto-starts
- [x] T017 [P] [US1, US5] **Frontend tests** — test toggle renders, toggles `queue_mode` in settings, "Queued" badge visibility, launch toast message

**Checkpoint**: All queue mode tests pass. Coverage does not regress.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Data Model)**: No dependencies — can start immediately. BLOCKS Phase 2 and Phase 3.
- **Phase 2 (Queue Logic)**: Depends on Phase 1 completion. BLOCKS Phase 4.
- **Phase 3 (Frontend)**: Depends on Phase 1 (T001-T004) for type alignment. Can partially parallel with Phase 2.
- **Phase 4 (Tests)**: Depends on Phase 2 and Phase 3 completion.

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- T009 can run in parallel with T005-T008 (different file)
- T011 can run in parallel with backend Phase 2 work (different layer)
- T015, T016, and T017 can all run in parallel (different test files)

### Within Each Phase

- Phase 1: T001/T002 parallel → T003 → T004
- Phase 2: T005/T009 parallel → T006 → T007 → T008/T010
- Phase 3: T011 → T012 → T013/T014
- Phase 4: T015/T016/T017 all parallel

---

## Verification

```bash
# Unit tests
cd solune/backend && pytest tests/unit/test_queue_mode.py -v

# Coverage regression check
cd solune/backend && pytest --cov=src --cov-report=term-missing

# Frontend tests
cd solune/frontend && npm test

# Manual verification
# 1. Toggle ON → launch 2 issues → second held in Backlog (no agent) → complete first → second auto-starts
# 2. Toggle OFF → both launch immediately (existing behavior preserved)
```
