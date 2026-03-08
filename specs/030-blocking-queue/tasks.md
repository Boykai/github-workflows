# Tasks: Blocking Queue — Serial Issue Activation & Branch Ancestry Control

**Input**: Design documents from `/specs/030-blocking-queue/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — spec.md explicitly requests unit tests for the blocking queue state machine (8-issue scenario), `#block` parsing, and integration tests for chore trigger and pipeline creation with blocking=True.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/` (per plan.md project structure)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and new model definitions required by all subsequent phases

- [ ] T001 Create database migration in backend/src/migrations/017_blocking_queue.sql with blocking_queue table (id, repo_key, issue_number, project_id, is_blocking, queue_status with CHECK constraint, parent_branch, blocking_source_issue, created_at, activated_at, completed_at, UNIQUE(repo_key, issue_number)), indexes (idx_blocking_queue_repo_status, idx_blocking_queue_repo_blocking), and ALTER TABLE additions to add blocking INTEGER NOT NULL DEFAULT 0 to both pipeline_configs and chores tables
- [ ] T002 [P] Create BlockingQueueStatus StrEnum (pending, active, in_review, completed) and BlockingQueueEntry Pydantic model mirroring all DB columns in backend/src/models/blocking.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Model updates and core service layer that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Add blocking: bool = False to Chore, ChoreCreate, and ChoreUpdate models in backend/src/models/chores.py
- [ ] T004 [P] Add blocking: bool = False to PipelineConfig and PipelineConfigUpdate models in backend/src/models/pipeline.py
- [ ] T005 Create SQLite persistence layer in backend/src/services/blocking_queue_store.py using existing get_db() pattern with methods: insert, update_status, get_by_repo (with optional status filter, ordered by created_at ASC), get_by_issue, get_pending, get_open_blocking (active or in_review blocking entries ordered by created_at ASC)
- [ ] T006 Create core blocking queue service in backend/src/services/blocking_queue.py with functions: enqueue_issue(repo_key, issue_number, project_id, is_blocking), try_activate_next(repo_key) implementing batch activation rules (non-blocking concurrent when no blocking open; serial when blocking open; non-blocking batch up to next blocking entry; blocking alone), mark_active(repo_key, issue_number, parent_branch), mark_in_review(repo_key, issue_number), mark_completed(repo_key, issue_number), get_base_ref_for_issue(repo_key, issue_number), get_current_base_branch(repo_key), has_open_blocking_issues(repo_key); include per-repo asyncio.Lock (dict[str, asyncio.Lock]) and SQLite BEGIN IMMEDIATE transactions for concurrency control
- [ ] T007 [P] Add BlockingQueueEntry interface, BlockingQueueStatus type, BlockingQueueUpdatedEvent interface, and blocking boolean field to existing Chore, ChoreUpdate, PipelineConfig, and PipelineConfigUpdate types in frontend/src/types/index.ts

**Checkpoint**: Foundation ready — core blocking queue engine and all model definitions are in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Blocking Queue Core: Serial Issue Activation (Priority: P1) 🎯 MVP

**Goal**: Serialize issue activation when blocking issues exist — only one blocking issue runs agents at a time, pending issues activate in correct batch order when active issues transition.

**Independent Test**: Create multiple issues with blocking flags in sequence, verify only one activates at a time, verify pending issues activate in order when active issue transitions to "in review" or completes. Validate the full 8-issue mixed scenario.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Create unit test for blocking queue state machine with 8-issue scenario (creation order, activation order, batch rules, completion cascades) in backend/tests/unit/test_blocking_queue.py — test enqueue_issue, try_activate_next, mark_in_review, mark_completed; verify: non-blocking immediate activation when no blocking open, serial activation with blocking open, batch activation rules (non-blocking together up to next blocking entry, blocking alone), activation cascade on in_review and completed transitions

### Implementation for User Story 1

- [ ] T009 [US1] Modify execute_full_workflow() in backend/src/services/workflow_orchestrator/orchestrator.py to call blocking_queue.enqueue_issue() after issue creation; if issue is not immediately activated, return WorkflowResult with pending status and skip agent assignment; if activated, proceed with current flow
- [ ] T010 [US1] Modify status transition handler in backend/src/services/copilot_polling/pipeline.py to call blocking_queue.mark_in_review() when issue moves to "In review" and trigger assign_agent_for_status() for each newly activated issue returned by try_activate_next()
- [ ] T011 [US1] Modify completion handler in backend/src/services/copilot_polling/completion.py to call blocking_queue.mark_completed() when issue completes and trigger agent assignment for each newly activated issue returned by try_activate_next()
- [ ] T012 [US1] Integrate WebSocket broadcast of blocking_queue_updated event (repo_key, activated_issues, completed_issues, current_base_branch) via connection_manager.broadcast_to_project() after activation cascades in backend/src/services/blocking_queue.py

**Checkpoint**: Serial issue activation is fully functional. Issues queue correctly, activate in the right order, and cascade activations on transitions. The 8-issue scenario passes.

---

## Phase 4: User Story 2 — Branch Ancestry Control from Blocking Issues (Priority: P1)

**Goal**: Issues that activate while blocking issues are open automatically branch from the oldest open blocking issue's branch instead of `main`, reverting to `main` when no blocking issues remain.

**Independent Test**: Create a blocking issue and verify its branch is from `main`. Create a second issue while the first is active and verify it branches from the first's branch. Complete all blocking issues and verify new issues branch from `main` again.

### Implementation for User Story 2

- [ ] T013 [US2] Modify base_ref resolution in backend/src/services/workflow_orchestrator/orchestrator.py to call blocking_queue.get_base_ref_for_issue(repo_key, issue_number) for first agent assignment instead of hardcoded 'main'; retain current behavior for subsequent agents on already-branched issues
- [ ] T014 [US2] Record blocking_source_issue on activated entries when they branch from a blocking issue's branch via update in backend/src/services/blocking_queue.py (set blocking_source_issue in mark_active when parent_branch comes from a blocking issue)

**Checkpoint**: Branch ancestry is controlled by the blocking queue. Issues branch from the correct source (oldest open blocking issue's branch or `main`). Combined with US1, the core blocking queue feature (activation + branching) is complete.

---

## Phase 5: User Story 3 — Chore Blocking Toggle (Priority: P2)

**Goal**: Chores gain a "Blocking" toggle; when triggered, the resulting issue is enqueued as blocking. Chores inherit the blocking flag from their assigned Pipeline if their own flag is not set.

**Independent Test**: Enable blocking on a Chore → trigger it → verify the resulting issue is enqueued with is_blocking=true. Test pipeline inheritance: Chore blocking=false + Pipeline blocking=true → issue is blocking.

### Implementation for User Story 3

- [ ] T015 [P] [US3] Add 'blocking' to _CHORE_UPDATABLE_COLUMNS frozenset and update row-to-model conversion to include blocking field in backend/src/services/chores/service.py
- [ ] T016 [US3] Implement blocking flag resolution in trigger_chore(): read chore.blocking OR pipeline.blocking (OR logic per R5) and pass is_blocking to execute_full_workflow() in backend/src/services/chores/service.py and backend/src/api/chores.py
- [ ] T017 [P] [US3] Add blocking field to useChores hook types and include blocking in useUpdateChore mutation payload in frontend/src/hooks/useChores.ts
- [ ] T018 [US3] Add "Blocking" toggle switch following ai_enhance_enabled pattern (Switch component with label and onCheckedChange calling updateChore) in frontend/src/components/chores/ChoreCard.tsx

**Checkpoint**: Chores can be configured as blocking from the UI. Triggered blocking chores create issues that enter the blocking queue correctly. Pipeline inheritance works.

---

## Phase 6: User Story 4 — Pipeline-Level Blocking Toggle (Priority: P2)

**Goal**: Pipelines gain a "Blocking" toggle; when enabled, ALL issues created by that Pipeline are automatically marked as blocking.

**Independent Test**: Enable blocking on a Pipeline → create issues through it → verify all resulting issues are enqueued as blocking.

### Implementation for User Story 4

- [ ] T019 [P] [US4] Add 'blocking' to pipeline column allowlist and update row-to-model conversion to include blocking field in backend/src/services/pipelines/service.py
- [ ] T020 [US4] Add blocking field to pipeline create/update/read endpoints in backend/src/api/pipelines.py
- [ ] T021 [P] [US4] Add blocking field to usePipelineConfig hook types and include blocking in update mutation payload in frontend/src/hooks/usePipelineConfig.ts
- [ ] T022 [US4] Add "Blocking" toggle switch with tooltip ("When enabled, every issue this pipeline creates will be blocking and serialize activation") to pipeline config form in frontend/src/components/pipeline/SavedWorkflowsList.tsx

**Checkpoint**: Pipelines can be configured as blocking from the UI. All issues from blocking pipelines are enqueued as blocking. Toggle persists immediately.

---

## Phase 7: User Story 5 — Chat `#block` Command (Priority: P2)

**Goal**: Users can include `#block` anywhere in a chat message to mark the resulting issue as blocking. `#block` is stripped before intent processing and does not affect the message's meaning.

**Independent Test**: Send "Fix the login page #block" → verify `#block` is stripped → verify issue created with is_blocking=true. Send message without `#block` → verify issue is non-blocking.

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T023 [P] [US5] Create unit test for #block detection and stripping in backend/tests/unit/test_chat_block.py — test cases: #block at end of message, #block at beginning, #block in middle, multiple #block occurrences, case-insensitive (#Block, #BLOCK), no #block present, #block as part of other word (e.g., #blockchain should NOT match)

### Implementation for User Story 5

- [ ] T024 [US5] Add #block detection using case-insensitive regex r'\s*#block\b' at Priority 0.5 (between #agent and feature request) in backend/src/api/chat.py; strip all occurrences from message content before downstream processing; set is_blocking=True flag
- [ ] T025 [US5] Propagate is_blocking flag through confirm_proposal() to execute_full_workflow() in backend/src/api/chat.py ensuring the flag reaches enqueue_issue()
- [ ] T026 [P] [US5] Add #block to command autocomplete suggestions list with description "Mark the resulting issue as blocking" and Lock icon in frontend/src/components/chat/ChatInterface.tsx
- [ ] T027 [US5] Add reactive visual 🔒 badge indicator on message composer when #block is detected in typed text (using regex /\b#block\b/i) in frontend/src/components/chat/ChatInterface.tsx

**Checkpoint**: Chat `#block` command works end-to-end. Users see autocomplete suggestions and visual feedback, and resulting issues are correctly enqueued as blocking.

---

## Phase 8: User Story 6 — Blocking Queue UI Indicators and Notifications (Priority: P3)

**Goal**: Visual indicators on the board for blocking issues (🔒 badge) and pending issues ("Pending (blocked)" label), plus real-time toast notifications when pending issues activate.

**Independent Test**: Create blocking and pending issues → verify 🔒 badge on blocking cards, "Pending (blocked)" on pending cards. Activate a pending issue → verify toast notification appears.

### Implementation for User Story 6

- [ ] T028 [P] [US6] Add 🔒 "Blocking" badge (amber-colored, Lock icon from lucide-react) to issue cards that have is_blocking=true in frontend/src/components/board/
- [ ] T029 [P] [US6] Add "Pending (blocked)" status label (gray-colored, Clock icon) to issue cards with queue_status='pending' in frontend/src/components/board/
- [ ] T030 [US6] Add blocking chain tooltip or collapsible sidebar showing ordered queue, current base branch, and next-in-line issue in frontend/src/components/board/
- [ ] T031 [US6] Add WebSocket event handler for blocking_queue_updated events and display toast notification "Issue #X is now active — agents starting" for each newly activated issue in frontend

**Checkpoint**: Board displays correct visual indicators for all blocking queue states. Toast notifications fire when pending issues activate. Users can understand the queue at a glance.

---

## Phase 9: User Story 7 — Container Restart Recovery (Priority: P3)

**Goal**: Blocking queue state survives container restarts and the system automatically recovers any missed activations on startup.

**Independent Test**: Create pending issues → restart container/polling loop → verify system calls try_activate_next() for all repos with non-completed entries and pending issues activate.

### Implementation for User Story 7

- [ ] T032 [US7] Add startup recovery in polling loop initialization in backend/src/services/copilot_polling/pipeline.py to query all repos with non-completed blocking queue entries and call try_activate_next(repo_key) for each to recover missed activations during downtime

**Checkpoint**: Blocking queue is resilient to infrastructure events. No issues are permanently stuck in "pending" after restarts.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Integration tests, edge case handling, and cross-story validation

- [ ] T033 [P] Create integration test for chore trigger with blocking=True verifying issue is enqueued and respects activation order in backend/tests/
- [ ] T034 [P] Create integration test for pipeline with blocking=True verifying all created issues are enqueued as blocking in backend/tests/
- [ ] T035 Review and harden edge case handling in backend/src/services/blocking_queue.py: manually closed issues detected during polling, deleted blocking branch fallback to 'main' with warning log, duplicate enqueue_issue calls (UNIQUE constraint handling), empty queue edge case
- [ ] T036 Run quickstart.md validation scenarios (toggle persistence, serial activation, branch ancestry, 8-issue scenario, restart recovery)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) — core activation engine
- **US2 (Phase 4)**: Depends on US1 (Phase 3) — branch ancestry requires activation to be working
- **US3 (Phase 5)**: Depends on Foundational (Phase 2) — can proceed in parallel with US1/US2 for backend CRUD; integration requires US1
- **US4 (Phase 6)**: Depends on Foundational (Phase 2) — can proceed in parallel with US1/US2 for backend CRUD; integration requires US1
- **US5 (Phase 7)**: Depends on Foundational (Phase 2) — can proceed in parallel with US1/US2 for chat parsing; integration requires US1
- **US6 (Phase 8)**: Depends on US1 (Phase 3) for queue data to display
- **US7 (Phase 9)**: Depends on US1 (Phase 3) for activation cascade to recover
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 — no dependencies on other stories. This IS the blocking queue engine.
- **US2 (P1)**: Depends on US1 — branch ancestry is meaningless without serial activation working.
- **US3 (P2)**: Backend CRUD can start after Phase 2. Integration with orchestrator requires US1.
- **US4 (P2)**: Backend CRUD can start after Phase 2. Integration with orchestrator requires US1.
- **US5 (P2)**: Chat parsing can start after Phase 2. Integration with orchestrator requires US1.
- **US6 (P3)**: Requires queue data from US1 to display indicators.
- **US7 (P3)**: Requires US1's try_activate_next() to be implemented.

### Within Each User Story

- Tests (included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (different files)
- **Phase 2**: T003, T004, T007 can run in parallel (different files); T005 must complete before T006 (store before service)
- **Phase 3**: T008 (test) can be written in parallel with other story prep
- **Phase 5**: T015 and T017 can run in parallel (backend service + frontend hook); T016 depends on T015
- **Phase 6**: T019 and T021 can run in parallel (backend service + frontend hook)
- **Phase 7**: T023 and T026 can run in parallel (backend test + frontend autocomplete)
- **Phase 8**: T028 and T029 can run in parallel (different visual indicators)
- **Phase 10**: T033 and T034 can run in parallel (different integration tests)
- **Cross-phase**: US3 backend CRUD (T015-T016), US4 backend CRUD (T019-T020), and US5 chat parsing (T024-T025) can all proceed in parallel once Phase 2 is complete

---

## Parallel Example: User Story 1

```text
# Write test first (can start immediately after Phase 2):
Task T008: "Unit test for blocking queue state machine in backend/tests/unit/test_blocking_queue.py"

# Then implement in order:
Task T009: "Modify execute_full_workflow() in orchestrator.py"
Task T010: "Modify pipeline.py status transition handler"
Task T011: "Modify completion.py completion handler"
Task T012: "Integrate WebSocket broadcast in blocking_queue.py"
```

## Parallel Example: US3 + US4 + US5 (after Phase 2)

```text
# These three user stories can be worked on in parallel by different developers:

# Developer A — US3 Chore Toggle:
Task T015: "Add blocking to _CHORE_UPDATABLE_COLUMNS in chores/service.py"
Task T017: "Add blocking to useChores hook in useChores.ts"

# Developer B — US4 Pipeline Toggle:
Task T019: "Add blocking to pipeline column allowlist in pipelines/service.py"
Task T021: "Add blocking to usePipelineConfig hook in usePipelineConfig.ts"

# Developer C — US5 Chat #block:
Task T023: "Unit test for #block parsing in test_chat_block.py"
Task T026: "Add #block autocomplete in ChatInterface.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T007)
3. Complete Phase 3: User Story 1 — Serial Activation (T008–T012)
4. Complete Phase 4: User Story 2 — Branch Ancestry (T013–T014)
5. **STOP and VALIDATE**: Run 8-issue scenario test, verify activation order AND branch ancestry
6. Deploy/demo if ready — core blocking queue is fully functional

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 + US2 → Test independently → Deploy/Demo (**MVP!** — blocking queue works end-to-end)
3. Add US3 (Chore toggle) → Test independently → Deploy/Demo
4. Add US4 (Pipeline toggle) → Test independently → Deploy/Demo
5. Add US5 (Chat #block) → Test independently → Deploy/Demo
6. Add US6 (UI indicators) → Test independently → Deploy/Demo
7. Add US7 (Restart recovery) → Test independently → Deploy/Demo
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Serial Activation) — CRITICAL PATH
   - Developer B: US3 backend CRUD (T015–T016) + US4 backend CRUD (T019–T020)
   - Developer C: US5 chat parsing (T023–T025) + Frontend types (T007)
3. Once US1 is complete:
   - Developer A: US2 (Branch Ancestry)
   - Developer B: US3 frontend (T017–T018) + US4 frontend (T021–T022)
   - Developer C: US5 frontend (T026–T027) + US6 (UI indicators)
4. Final: US7 (Restart recovery) + Polish phase

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 36 |
| **Setup tasks** | 2 (T001–T002) |
| **Foundational tasks** | 5 (T003–T007) |
| **US1 tasks** | 5 (T008–T012) |
| **US2 tasks** | 2 (T013–T014) |
| **US3 tasks** | 4 (T015–T018) |
| **US4 tasks** | 4 (T019–T022) |
| **US5 tasks** | 5 (T023–T027) |
| **US6 tasks** | 4 (T028–T031) |
| **US7 tasks** | 1 (T032) |
| **Polish tasks** | 4 (T033–T036) |
| **Parallel opportunities** | 10 groups across phases |
| **MVP scope** | US1 + US2 (14 tasks: T001–T014) |
| **New backend files** | 4 (migration, model, service, store) |
| **Modified backend files** | ~10 |
| **Modified frontend files** | ~8 |

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach for US1 and US5)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The `_CHORE_UPDATABLE_COLUMNS` frozenset in chores/service.py MUST be updated or blocking field updates will be rejected with ValueError
- The `_PIPELINE_COLUMNS` allowlist in pipelines/service.py MUST be updated similarly
- Per-repo asyncio.Lock in blocking_queue.py is critical — all state-changing operations must acquire it
- SQLite `BEGIN IMMEDIATE` transactions complement the application-layer lock for atomicity
