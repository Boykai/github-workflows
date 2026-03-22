# Tasks: Auto Merge — Automatically Squash-Merge Parent PRs When Pipelines Complete

**Input**: Design documents from `/specs/001-auto-merge-pipelines/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — the feature touches critical merge paths (plan.md §IV Test Optionality).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- **Migrations**: `solune/backend/src/migrations/`
- **Tests (backend)**: `solune/backend/tests/unit/`
- **Tests (frontend)**: `solune/frontend/src/__tests__/`
- **Agents**: `.github/agents/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and core model additions that all other phases depend on

- [x] T001 Create database migration adding auto_merge column to project_settings table in `solune/backend/src/migrations/034_auto_merge.sql`
- [x] T002 Add `auto_merge: bool = False` field to `ProjectBoardConfig` model in `solune/backend/src/models/settings.py`
- [x] T003 [P] Add `auto_merge: bool = False` field to `PipelineState` dataclass in `solune/backend/src/services/workflow_orchestrator/models.py`
- [x] T004 [P] Add `auto_merge: boolean` to `ProjectBoardConfig` and `PipelineConfig` TypeScript interfaces in `solune/frontend/src/types/index.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Settings persistence, API handler, pipeline state serialization, and GitHub API helpers that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Add `"auto_merge"` to `PROJECT_SETTINGS_COLUMNS` tuple and update `_merge_settings_rows()` to merge `auto_merge` column value into `ProjectBoardConfig` in `solune/backend/src/services/settings_store.py`
- [x] T006 Add `is_auto_merge_enabled()` function with 10-second TTL in-memory cache (mirror `is_queue_mode_enabled()`) in `solune/backend/src/services/settings_store.py`
- [x] T007 Handle `auto_merge` in `update_project_settings_endpoint()`: convert to int, upsert to user row, sync to `__workflow__` canonical row, invalidate cache (same pattern as `queue_mode`) in `solune/backend/src/api/settings.py`
- [x] T008 [P] Serialize `auto_merge` field in pipeline metadata JSON (read/write) in `solune/backend/src/services/pipeline_state_store.py`
- [x] T009 [P] Add `get_check_runs_for_ref(ref)` REST helper (`GET /repos/{owner}/{repo}/commits/{ref}/check-runs`) to `solune/backend/src/services/github_projects/pull_requests.py`
- [x] T010 [P] Add `get_pr_mergeable_state(pr_number)` GraphQL helper (query `pullRequest.mergeable` field) to `solune/backend/src/services/github_projects/pull_requests.py`
- [x] T011 [P] Create `AutoMergeResult` dataclass (`status`, `pr_number`, `merge_commit`, `error`, `context` fields) in `solune/backend/src/services/copilot_polling/auto_merge.py`

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Enable Auto Merge and Merge Automatically on Pipeline Success (Priority: P1) 🎯 MVP

**Goal**: When Auto Merge is enabled (project OR pipeline level) and a pipeline completes successfully, the parent PR is automatically squash-merged to the default branch without manual intervention.

**Independent Test**: Enable Auto Merge on a project, run a pipeline to successful completion, and verify the parent PR is squash-merged automatically. Also verify draft PRs are marked ready-for-review before merge, and merge failures produce error notifications.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T012 [P] [US1] Unit test for `_attempt_auto_merge()` success path (CI passes, PR mergeable, squash merge succeeds) in `solune/backend/tests/unit/test_auto_merge.py`
- [x] T013 [P] [US1] Unit test for `_attempt_auto_merge()` returning `devops_needed` on CI failure in `solune/backend/tests/unit/test_auto_merge.py`
- [x] T014 [P] [US1] Unit test for `_attempt_auto_merge()` returning `devops_needed` on CONFLICTING mergeability state in `solune/backend/tests/unit/test_auto_merge.py`
- [x] T015 [P] [US1] Unit test for `_attempt_auto_merge()` returning `merge_failed` when merge API call fails in `solune/backend/tests/unit/test_auto_merge.py`
- [x] T016 [P] [US1] Unit test for `_attempt_auto_merge()` marking draft PR ready-for-review before merge in `solune/backend/tests/unit/test_auto_merge.py`
- [x] T017 [P] [US1] Unit test for auto_merge flag resolution OR logic (project true OR pipeline true → active) in `solune/backend/tests/unit/test_settings_auto_merge.py`
- [x] T018 [P] [US1] Unit test for settings persistence round-trip (write auto_merge=true, read back) in `solune/backend/tests/unit/test_settings_auto_merge.py`

### Implementation for User Story 1

- [x] T019 [US1] Implement `_attempt_auto_merge()` function: discover main PR via existing multi-strategy logic, mark draft PRs ready-for-review, check CI status via `get_check_runs_for_ref()`, check mergeability via `get_pr_mergeable_state()`, call `merge_pull_request(merge_method='SQUASH')` if all pass, return structured `AutoMergeResult` in `solune/backend/src/services/copilot_polling/auto_merge.py`
- [x] T020 [US1] Add auto_merge flag resolution at pipeline start in `execute_full_workflow()`: check both project-level (`is_auto_merge_enabled()`) and pipeline-level auto_merge values (OR logic), set `pipeline_state.auto_merge = True` when either is true in `solune/backend/src/services/copilot_polling/pipeline.py`
- [x] T021 [US1] Apply "auto-merge" GitHub label to the issue when auto_merge is activated for a pipeline in `execute_full_workflow()` in `solune/backend/src/services/copilot_polling/pipeline.py`
- [x] T022 [US1] Add auto-merge trigger in `_transition_after_pipeline_complete()`: check `pipeline_state.auto_merge OR is_auto_merge_enabled(project_id)`, call `_attempt_auto_merge()`, handle result (merged → broadcast success; devops_needed → dispatch DevOps; merge_failed → mark ERROR, notify) in `solune/backend/src/services/copilot_polling/pipeline.py`
- [x] T023 [US1] Add WebSocket broadcast calls for `auto_merge_completed` and `auto_merge_failed` events using `connection_manager.broadcast_to_project()` in `solune/backend/src/services/copilot_polling/pipeline.py`

**Checkpoint**: At this point, User Story 1 should be fully functional — enabling Auto Merge and having a pipeline complete triggers automatic squash-merge of the parent PR

---

## Phase 4: User Story 2 — Skip Human Agent Step When Auto Merge Is Active (Priority: P1)

**Goal**: When Auto Merge is active and the human agent is the last step, automatically skip it with a ⏭ SKIPPED indicator and close the sub-issue with an audit comment, proceeding directly to auto-merge.

**Independent Test**: Configure a pipeline with a human agent as the last step, enable Auto Merge, run the pipeline, and verify the human step is marked SKIPPED (⏭) with the sub-issue closed with "Skipped — Auto Merge enabled" comment.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T024 [P] [US2] Unit test for human agent skip when auto_merge is true and human is last step in `solune/backend/tests/unit/test_auto_merge.py`
- [x] T025 [P] [US2] Unit test for human agent NOT skipped when auto_merge is false in `solune/backend/tests/unit/test_auto_merge.py`
- [x] T026 [P] [US2] Unit test for human agent NOT skipped when human is NOT the last step in `solune/backend/tests/unit/test_auto_merge.py`

### Implementation for User Story 2

- [x] T027 [US2] Add human agent skip logic in `_advance_pipeline()`: when next agent is `"human"` AND it's the last step AND `auto_merge` is active, mark step as `AgentStepState.SKIPPED` (⏭) in tracking table in `solune/backend/src/services/copilot_polling/pipeline.py`
- [x] T028 [US2] Close the human sub-issue with a "Skipped — Auto Merge enabled" comment when the human step is skipped in `solune/backend/src/services/copilot_polling/pipeline.py`
- [x] T029 [US2] Proceed directly to pipeline completion and auto-merge flow after human skip (no human agent assignment) in `solune/backend/src/services/copilot_polling/pipeline.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — pipelines with human last steps skip them and auto-merge

---

## Phase 5: User Story 3 — CI Failure Recovery via DevOps Agent (Priority: P2)

**Goal**: When CI fails on an auto-merge-enabled pipeline, automatically dispatch a DevOps agent to investigate and fix, with a cap of 2 retries per pipeline.

**Independent Test**: Enable Auto Merge on a pipeline, introduce a CI failure, and verify the DevOps agent is dispatched. Verify the retry cap of 2 and deduplication (no double dispatch when DevOps is already active).

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T030 [P] [US3] Unit test for `check_run` webhook routing to `dispatch_devops_agent()` on failure/timed_out in `solune/backend/tests/unit/test_webhook_ci.py`
- [x] T031 [P] [US3] Unit test for `check_suite` webhook routing to `dispatch_devops_agent()` on failure in `solune/backend/tests/unit/test_webhook_ci.py`
- [x] T032 [P] [US3] Unit test for DevOps deduplication (skip dispatch when `devops_active` is true) in `solune/backend/tests/unit/test_auto_merge.py`
- [x] T033 [P] [US3] Unit test for DevOps retry cap (no dispatch after 2 attempts, pipeline marked ERROR) in `solune/backend/tests/unit/test_auto_merge.py`
- [x] T034 [P] [US3] Unit test for DevOps completion detection via "devops: Done!" marker triggers `_attempt_auto_merge()` retry in `solune/backend/tests/unit/test_auto_merge.py`

### Implementation for User Story 3

- [x] T035 [P] [US3] Create DevOps repository agent with YAML frontmatter (`name: DevOps`, `description`, `icon: wrench`) and system prompt specialized for CI log reading, test failure identification, merge conflict resolution, and check re-triggering at `.github/agents/devops.agent.md`
- [x] T036 [P] [US3] Add `CheckRunEvent`, `CheckSuiteEvent`, `CheckRunData`, `CheckSuiteData`, `CheckRunPR`, and `BranchRef` Pydantic models in `solune/backend/src/api/webhook_models.py`
- [x] T037 [US3] Implement `dispatch_devops_agent()` function: check dedup (`devops_active`), check retry cap (`devops_attempts < 2`), dispatch via standard Copilot dispatch, set `devops_active=True`, increment `devops_attempts`, broadcast `devops_triggered` event in `solune/backend/src/services/copilot_polling/auto_merge.py`
- [x] T038 [US3] Route `check_run` (action=completed, conclusion=failure/timed_out) and `check_suite` (action=completed, conclusion=failure) events to `dispatch_devops_agent()` in `solune/backend/src/api/webhooks.py`
- [x] T039 [US3] Implement DevOps completion detection: on "devops: Done!" marker, set `devops_active=False`, retry `_attempt_auto_merge()`; after 2nd failed attempt mark pipeline ERROR and notify user in `solune/backend/src/services/copilot_polling/pipeline.py`

**Checkpoint**: At this point, CI failures on auto-merge pipelines trigger DevOps agent recovery with proper retry cap and deduplication

---

## Phase 6: User Story 4 — Project-Level Auto Merge Toggle in UI (Priority: P2)

**Goal**: Display an Auto Merge toggle on the Projects page adjacent to the Queue Mode toggle, using the same chip/badge styling, with a confirmation dialog for retroactive activation.

**Independent Test**: Navigate to the Projects page, click the Auto Merge toggle, verify it persists and reflects in the project configuration. Enable on a project with active pipelines and verify the confirmation dialog appears.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T040 [P] [US4] Frontend test: Auto Merge toggle renders adjacent to Queue Mode toggle in `solune/frontend/src/__tests__/`
- [x] T041 [P] [US4] Frontend test: Toggle click persists auto_merge setting in `solune/frontend/src/__tests__/`
- [x] T042 [P] [US4] Frontend test: Confirmation dialog shown when enabling with active pipelines in `solune/frontend/src/__tests__/`

### Implementation for User Story 4

- [x] T043 [P] [US4] Export `GitMerge` icon from lucide-react in `solune/frontend/src/lib/icons.ts`
- [x] T044 [US4] Add Auto Merge toggle button to ProjectsPage adjacent to Queue Mode toggle: read from `projectSettings.project.board_display_config.auto_merge`, call `updateSettings({ auto_merge: !isAutoMerge })` on click, use GitMerge icon, green/primary active state, muted inactive state in `solune/frontend/src/pages/ProjectsPage.tsx`
- [x] T045 [US4] Add confirmation dialog for retroactive toggle: when enabling auto_merge on a project with active pipelines, show dialog listing N active pipelines that will be affected, require confirmation before saving in `solune/frontend/src/pages/ProjectsPage.tsx`

**Checkpoint**: At this point, the project-level Auto Merge toggle is functional with confirmation dialog for retroactive activation

---

## Phase 7: User Story 5 — Pipeline-Level Auto Merge Toggle (Priority: P3)

**Goal**: Add an Auto Merge toggle in the pipeline configuration panel, persisted via existing pipeline CRUD endpoints, providing fine-grained per-pipeline control.

**Independent Test**: Navigate to the pipeline configuration panel, toggle Auto Merge on for a specific pipeline, verify the setting persists independently from the project-level setting.

### Implementation for User Story 5

- [x] T046 [US5] Add Auto Merge switch/toggle to the pipeline configuration panel (AgentsPipelinePage / PipelineToolbar), persisted via existing pipeline CRUD endpoints in `solune/frontend/src/components/pipelines/`

**Checkpoint**: At this point, pipeline-level Auto Merge configuration is available alongside project-level control

---

## Phase 8: User Story 6 — Real-Time Notifications for Auto Merge Events (Priority: P3)

**Goal**: Display real-time toast notifications when auto-merge events occur (success, failure, DevOps triggered) via WebSocket events.

**Independent Test**: Trigger an auto-merge event and verify the appropriate toast notification appears in the UI in real time.

### Tests for User Story 6

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T047 [P] [US6] Frontend test: Toast notification shown for `auto_merge_completed` WebSocket event in `solune/frontend/src/__tests__/`

### Implementation for User Story 6

- [x] T048 [US6] Handle `auto_merge_completed`, `auto_merge_failed`, and `devops_triggered` WebSocket event types in the message handler: show success toast ("PR #X squash-merged"), error toast with details, and info toast ("DevOps agent resolving CI failure on #X") via sonner in `solune/frontend/src/hooks/useRealTimeSync.ts`
- [x] T049 [US6] Invalidate relevant TanStack Query caches on `auto_merge_completed` and `auto_merge_failed` events to refresh board data in `solune/frontend/src/hooks/useRealTimeSync.ts`

**Checkpoint**: All user stories are now independently functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Integration validation, documentation, and cross-cutting improvements

- [x] T050 [P] Add pipeline tracking table display for ⏭ SKIPPED indicator on auto_merge human skip (ensure existing SKIPPED state renders correctly) in `solune/frontend/src/components/pipelines/`
- [x] T051 [P] Verify DevOps agent is discoverable via `list_available_agents()` directory scan — no backend code changes needed, validate slug is `devops`
- [x] T052 Code cleanup: ensure all new code follows existing patterns (error handling via `getErrorHint`, logging, type safety)
- [x] T053 Run quickstart.md verification checklist to validate all implementation items
- [x] T054 [P] End-to-end validation: auto_merge column exists after migration, toggle persists, pipeline skips human, squash-merge executes, DevOps dispatches, WebSocket notifications arrive

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — core MVP, BLOCKS User Story 2
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) — extends pipeline completion flow
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — can run in PARALLEL with US1/US2
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — can run in PARALLEL with US1/US2/US3
- **User Story 5 (Phase 7)**: Depends on Foundational (Phase 2) — can run in PARALLEL with other stories
- **User Story 6 (Phase 8)**: Depends on User Story 1 (Phase 3) — needs backend broadcast events to exist
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational → No dependencies on other stories
- **User Story 2 (P1)**: After Foundational → Integrates with US1 pipeline completion flow (same file: pipeline.py)
- **User Story 3 (P2)**: After Foundational → Independent (different files: webhooks.py, auto_merge.py, devops.agent.md)
- **User Story 4 (P2)**: After Foundational → Independent (frontend only: ProjectsPage.tsx, icons.ts)
- **User Story 5 (P3)**: After Foundational → Independent (frontend only: pipelines/ components)
- **User Story 6 (P3)**: After US1 → Needs broadcast events from US1 implementation

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints/UI
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (different backend files), T004 can run in parallel (frontend file)
- **Phase 2**: T008, T009, T010, T011 can all run in parallel (different files)
- **Phase 3**: All test tasks (T012–T018) can run in parallel
- **Phase 5**: T035 (agent file) and T036 (webhook models) can run in parallel
- **Phase 6**: T043 (icons) can run in parallel with test tasks
- **Cross-phase**: US3 (Phase 5) and US4 (Phase 6) can run in parallel with US1/US2

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for _attempt_auto_merge() success path in solune/backend/tests/unit/test_auto_merge.py"
Task: "Unit test for _attempt_auto_merge() CI failure path in solune/backend/tests/unit/test_auto_merge.py"
Task: "Unit test for _attempt_auto_merge() conflict path in solune/backend/tests/unit/test_auto_merge.py"
Task: "Unit test for _attempt_auto_merge() merge_failed path in solune/backend/tests/unit/test_auto_merge.py"
Task: "Unit test for _attempt_auto_merge() draft PR handling in solune/backend/tests/unit/test_auto_merge.py"
Task: "Unit test for flag resolution OR logic in solune/backend/tests/unit/test_settings_auto_merge.py"
Task: "Unit test for settings persistence in solune/backend/tests/unit/test_settings_auto_merge.py"
```

## Parallel Example: User Story 3

```bash
# Launch independent tasks together:
Task: "Create DevOps repository agent at .github/agents/devops.agent.md"
Task: "Add CheckRunEvent/CheckSuiteEvent Pydantic models in solune/backend/src/api/webhook_models.py"
```

## Parallel Example: Cross-Phase

```bash
# After Foundational completes, these can all start in parallel:
Team A: User Story 1 (Phase 3) — Backend merge logic
Team B: User Story 3 (Phase 5) — DevOps agent + webhooks
Team C: User Story 4 (Phase 6) — Frontend toggle
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T011)
3. Complete Phase 3: User Story 1 (T012–T023)
4. **STOP and VALIDATE**: Test auto-merge end-to-end — pipeline completes → PR squash-merged
5. Deploy/demo if ready — core value delivered

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (**MVP! Core auto-merge works**)
3. Add User Story 2 → Test independently → Deploy/Demo (Human step skipped)
4. Add User Story 3 → Test independently → Deploy/Demo (CI failure recovery)
5. Add User Story 4 → Test independently → Deploy/Demo (Project toggle UI)
6. Add User Story 5 → Test independently → Deploy/Demo (Pipeline toggle UI)
7. Add User Story 6 → Test independently → Deploy/Demo (Real-time notifications)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 + User Story 2 (backend merge flow — same file pipeline.py)
   - Developer B: User Story 3 (DevOps agent + webhooks — separate files)
   - Developer C: User Story 4 + User Story 5 (frontend toggles)
3. After US1 completes: Developer D picks up User Story 6 (notifications)
4. Stories complete and integrate independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 54 |
| **Phase 1 (Setup)** | 4 tasks |
| **Phase 2 (Foundational)** | 7 tasks |
| **US1 — Auto Merge on Success (P1)** | 12 tasks (7 tests + 5 impl) |
| **US2 — Human Agent Skip (P1)** | 6 tasks (3 tests + 3 impl) |
| **US3 — DevOps CI Recovery (P2)** | 10 tasks (5 tests + 5 impl) |
| **US4 — Project Toggle UI (P2)** | 6 tasks (3 tests + 3 impl) |
| **US5 — Pipeline Toggle UI (P3)** | 1 task |
| **US6 — Real-Time Notifications (P3)** | 3 tasks (1 test + 2 impl) |
| **Phase 9 (Polish)** | 5 tasks |
| **Parallel Opportunities** | 31 tasks marked [P] |
| **Suggested MVP Scope** | User Story 1 (Phase 1 + 2 + 3 = 23 tasks) |

### Independent Test Criteria

| Story | Independent Test |
|-------|-----------------|
| **US1** | Enable Auto Merge → pipeline completes → parent PR squash-merged automatically |
| **US2** | Pipeline with human last step → auto_merge active → human step marked ⏭ SKIPPED |
| **US3** | Auto-merge pipeline → CI failure → DevOps agent dispatched (max 2 retries) |
| **US4** | Projects page → click Auto Merge toggle → setting persists, confirmation dialog on retroactive |
| **US5** | Pipeline config panel → toggle Auto Merge → setting persists independently |
| **US6** | Auto-merge event occurs → toast notification appears in real time |

### Format Validation

✅ ALL 54 tasks follow the checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Auto merge flag uses OR logic: project OR pipeline = active
- Retroactive toggle handled via lazy check at merge decision point (no eager state updates)
- DevOps agent discovered via existing `.github/agents/` directory scan — no backend code changes
- All icons imported through `@/lib/icons` barrel file (ESLint enforced)
