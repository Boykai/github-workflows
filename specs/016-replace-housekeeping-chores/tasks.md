# Tasks: Replace Housekeeping with Chores

**Input**: Design documents from `/specs/016-replace-housekeeping-chores/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/chores-api.yaml, quickstart.md

**Tests**: Included — tests are requested per feature specification (plan.md Constitution Check IV, quickstart.md Phase 8).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Remove Housekeeping + Scaffold)

**Purpose**: Remove the existing Housekeeping feature entirely and prepare a clean slate for Chores. Covers FR-001.

- [X] T001 Create migration file backend/src/migrations/010_chores.sql — drop housekeeping tables (housekeeping_trigger_history, housekeeping_tasks, housekeeping_templates), create chores table with all columns, constraints, and indexes per data-model.md
- [X] T002 [P] Delete backend housekeeping files: backend/src/models/housekeeping.py, backend/src/services/housekeeping/ (entire directory including service.py, scheduler.py, counter.py, seed.py, __init__.py), backend/src/api/housekeeping.py
- [X] T003 [P] Delete frontend housekeeping files: frontend/src/components/housekeeping/ (entire directory including HousekeepingTaskForm.tsx, HousekeepingTaskList.tsx, RunNowButton.tsx, TemplateLibrary.tsx, TriggerHistoryLog.tsx), frontend/src/hooks/useHousekeeping.ts
- [X] T004 [P] Remove housekeeping router registration from backend/src/api/__init__.py — delete housekeeping_router import and include_router call
- [X] T005 [P] Remove HousekeepingService.initialize() call from lifespan in backend/src/main.py
- [X] T006 [P] Delete housekeeping test files in backend/tests/ and frontend/src/ and remove any remaining housekeeping references across the codebase

---

## Phase 2: Foundational (Backend Core)

**Purpose**: Core backend infrastructure — Pydantic models, service CRUD, and API router registration. MUST complete before any user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 Create Pydantic models and enums in backend/src/models/chores.py — ScheduleType enum, ChoreStatus enum, Chore model, ChoreCreate model, ChoreUpdate model, ChoreTriggerResult model, EvaluateChoreTriggersResponse model, ChoreChatMessage model, ChoreChatResponse model per data-model.md
- [X] T008 [P] Create backend/src/services/chores/__init__.py package initializer
- [X] T009 Implement ChoresService with core CRUD in backend/src/services/chores/service.py — create_chore(), list_chores(project_id), get_chore(chore_id), update_chore(chore_id, data), delete_chore(chore_id) using raw SQL + aiosqlite following existing database.py patterns (row factory, parameterized queries)
- [X] T010 [P] Create chores API router skeleton in backend/src/api/chores.py — define all 7 endpoint signatures per contracts/chores-api.yaml with placeholder handlers that raise NotImplementedError
- [X] T011 Register chores router in backend/src/api/__init__.py — add import and include_router(chores_router, prefix="/chores", tags=["chores"])

**Checkpoint**: Foundation ready — chores table exists, models defined, service has CRUD, router registered with stubs.

---

## Phase 3: User Story 1 — View Chores Panel on Project Board (P1) 🎯 MVP

**Goal**: Display a "Chores" panel on the right side of the project board showing all chores for the current project, with empty state messaging and an "Add Chore" button.

**Independent Test**: Navigate to project board page → Chores panel renders to the right of board columns → shows chore list or empty state with "Add Chore" button.

### Implementation for User Story 1

- [X] T012 [US1] Implement GET /chores/{project_id} handler in backend/src/api/chores.py — call ChoresService.list_chores(), return list of Chore models as JSON array
- [X] T013 [P] [US1] Create useChores React Query hooks in frontend/src/hooks/useChores.ts — useChoresList(projectId) with GET /chores/{project_id} query, plus mutation hook stubs for create/update/delete
- [X] T014 [P] [US1] Create ChoreCard component in frontend/src/components/chores/ChoreCard.tsx — display name, schedule type & value, last triggered date, computed "until next trigger" (remaining time or count), link to GitHub Issue Template path, Active/Paused status badge (read-only for now)
- [X] T015 [US1] Create ChoresPanel container in frontend/src/components/chores/ChoresPanel.tsx — renders list of ChoreCard components using useChoresList hook, empty state with "Add Chore" button, loading and error states
- [X] T016 [US1] Integrate ChoresPanel into frontend/src/pages/ProjectBoardPage.tsx — add to right side of project board layout, pass projectId prop

### Tests for User Story 1

- [X] T017 [P] [US1] Write backend unit test for list chores endpoint in backend/tests/unit/test_chores_api.py — test empty list response, multiple chores returned, project isolation
- [X] T018 [P] [US1] Write frontend test for ChoresPanel in frontend/src/components/chores/__tests__/ChoresPanel.test.tsx — test empty state rendering, chore list rendering, loading state

**Checkpoint**: Chores panel visible on project board with empty state or chore list. No create/edit/trigger functionality yet.

---

## Phase 4: User Story 2 — Add a Chore with Rich Input (P1)

**Goal**: Users can create a chore by providing detailed markdown template content. System generates a GitHub Issue Template (.md with YAML front matter), commits it via branch+PR, creates a tracking issue, and activates the chore in the panel.

**Independent Test**: Click "Add Chore" → enter rich markdown content → submit → verify branch created, template file committed to .github/ISSUE_TEMPLATE/, PR opened, tracking issue created in "In review" status, chore appears in panel as active.

### Implementation for User Story 2

- [X] T019 [US2] Create template_builder.py in backend/src/services/chores/template_builder.py — build_template(name, content) generates .md file with YAML front matter (name, about, title, labels, assignees defaults); commit_template_to_repo(github_service, access_token, owner, repo, project_id, name, template_content) handles full branch+commit+PR+tracking-issue workflow using existing github_service methods; includes is_sparse_input(text) heuristic per research.md R6
- [X] T020 [US2] Implement POST /chores/{project_id} handler in backend/src/api/chores.py — call template_builder to generate template + commit to repo via branch+PR, create tracking issue in "In review" status, call ChoresService.create_chore() with template path and content, return created Chore
- [X] T021 [P] [US2] Create AddChoreModal component in frontend/src/components/chores/AddChoreModal.tsx — modal dialog with name input and text area for template content, submit handler, sparse vs rich input detection on client side for UX routing (sparse opens chat flow in US3, rich submits directly)
- [X] T022 [US2] Wire "Add Chore" button in ChoresPanel to open AddChoreModal in frontend/src/components/chores/ChoresPanel.tsx
- [X] T023 [US2] Implement createChore mutation in frontend/src/hooks/useChores.ts — POST /chores/{project_id} with ChoreCreate payload, invalidate chores list query on success

### Tests for User Story 2

- [X] T024 [P] [US2] Write backend unit test for template builder and create chore in backend/tests/unit/test_chores_service.py — test build_template() YAML front matter generation, default metadata population, is_sparse_input() heuristic, duplicate name rejection
- [X] T025 [P] [US2] Write frontend test for AddChoreModal in frontend/src/components/chores/__tests__/AddChoreModal.test.tsx — test modal opens/closes, form validation, rich content submission flow

**Checkpoint**: Users can create chores with rich input. Template committed via PR. Chore appears in panel immediately as active.

---

## Phase 5: User Story 4 — Configure Chore Schedule (P1)

**Goal**: Users can configure how often a chore triggers — either by time interval (days) or by number of new parent issues created — as a separate step after chore creation. "Until next trigger" displays remaining time or count.

**Independent Test**: Create a chore → from panel, configure time schedule (14 days) → verify "Until next trigger" shows remaining time. Switch to count schedule (5 issues) → verify shows remaining count.

### Implementation for User Story 4

- [X] T026 [US4] Implement PATCH /chores/{project_id}/{chore_id} handler in backend/src/api/chores.py — call ChoresService.update_chore() with schedule_type and schedule_value, validate consistency (both set or both null, schedule_value > 0 when set), return updated Chore
- [X] T027 [P] [US4] Create ChoreScheduleConfig inline editor in frontend/src/components/chores/ChoreScheduleConfig.tsx — dropdown for schedule type (time/count), numeric input for value (days or issue count), save button calling update mutation
- [X] T028 [US4] Implement updateChore mutation in frontend/src/hooks/useChores.ts — PATCH /chores/{project_id}/{chore_id} with ChoreUpdate payload, invalidate chores list on success
- [X] T029 [US4] Integrate ChoreScheduleConfig into ChoreCard in frontend/src/components/chores/ChoreCard.tsx — show inline schedule editor when schedule is unconfigured or user clicks to edit, update "Until next trigger" display with computed remaining time (days/hours) or remaining count

### Tests for User Story 4

- [X] T030 [P] [US4] Write backend unit test for schedule update in backend/tests/unit/test_chores_api.py — test valid schedule config (time, count), invalid combinations (type without value), schedule_value <= 0 rejection
- [X] T031 [P] [US4] Write frontend test for ChoreScheduleConfig in frontend/src/components/chores/__tests__/ChoreScheduleConfig.test.tsx — test schedule type selection, value input, save action, validation

**Checkpoint**: Chores can be fully configured with schedules. Panel shows accurate "until next trigger" info.

---

## Phase 6: User Story 5 — Chore Triggers and Executes Agent Pipeline (P1)

**Goal**: When a chore's schedule condition is met, automatically create a GitHub Issue from the template and execute the agent pipeline to create sub-issues assigned to configured agents. Enforce 1-open-instance constraint per chore. Auto-detect externally-closed issues.

**Independent Test**: Configure a chore with a short schedule → invoke POST /chores/evaluate-triggers → verify GitHub Issue created from template content, sub-issues created per agent pipeline config, chore cycle resets (last_triggered_at updated), 1-open-instance enforced on second call.

### Implementation for User Story 5

- [X] T032 [P] [US5] Create scheduler.py in backend/src/services/chores/scheduler.py — evaluate_time_trigger(chore) checks if N days have elapsed since last_triggered_at (or created_at if never triggered), returns bool
- [X] T033 [P] [US5] Create counter.py in backend/src/services/chores/counter.py — count_parent_issues_since(project_id, since_count, github_service, access_token) counts non-chore, non-sub-issue parent issues created since last trigger count; evaluate_count_trigger(chore, current_count) compares against schedule_value threshold, returns bool
- [X] T034 [US5] Implement trigger_chore() in backend/src/services/chores/service.py — check 1-open-instance constraint (current_issue_number not set or issue closed externally), create GitHub Issue via github_service.create_issue() using template_content as body, add to project via github_service.add_issue_to_project(), load workflow config via get_workflow_config(), invoke WorkflowOrchestrator.create_all_sub_issues(ctx) with WorkflowContext, update chore record (current_issue_number, current_issue_node_id, last_triggered_at, last_triggered_count)
- [X] T035 [US5] Implement evaluate_triggers() in backend/src/services/chores/service.py — query all active chores with configured schedules, for each: check time/count condition using scheduler.py and counter.py, trigger eligible chores using CAS UPDATE pattern (WHERE last_triggered_at = old_value) to prevent double-firing, collect results
- [X] T036 [US5] Implement POST /chores/evaluate-triggers handler in backend/src/api/chores.py — call ChoresService.evaluate_triggers() with optional project_id filter, return EvaluateChoreTriggersResponse with evaluated/triggered/skipped counts and per-chore results

### Tests for User Story 5

- [X] T037 [P] [US5] Write backend unit test for scheduler in backend/tests/unit/test_chores_scheduler.py — test time elapsed triggers, not-yet-due skips, never-triggered chore uses created_at, edge case at exact boundary
- [X] T038 [P] [US5] Write backend unit test for counter in backend/tests/unit/test_chores_counter.py — test count threshold met, not met, exclusion of chore-generated issues and sub-issues from count
- [X] T039 [US5] Write backend unit test for trigger execution in backend/tests/unit/test_chores_service.py — test trigger_chore() creates issue and calls orchestrator, 1-open-instance enforcement skips trigger, cycle reset updates fields, CAS prevents double-fire

**Checkpoint**: Chores automatically trigger when conditions are met. Agent pipeline creates sub-issues. Full automation loop working end-to-end.

---

## Phase 7: User Story 6 — Toggle Chore Active / Paused (P2)

**Goal**: Users can pause and resume chores by clicking the Active/Paused status toggle in the Chores panel. Paused chores do not trigger even when their schedule condition is met.

**Independent Test**: Click Active status on a chore → status changes to Paused → run evaluate-triggers → verify paused chore is skipped. Click Paused → status returns to Active.

### Implementation for User Story 6

- [X] T040 [US6] Add clickable status toggle to ChoreCard in frontend/src/components/chores/ChoreCard.tsx — clicking Active/Paused badge calls updateChore mutation with toggled status value, optimistic update for instant UI feedback
- [X] T041 [US6] Verify evaluate_triggers() in backend/src/services/chores/service.py filters only active chores with configured schedules — adjust query WHERE clause if not already handled in T035

### Tests for User Story 6

- [X] T042 [P] [US6] Write backend unit test for status toggle in backend/tests/unit/test_chores_api.py — test PATCH with status change active→paused, paused→active, verify paused chores excluded from trigger evaluation

**Checkpoint**: Chores can be paused and resumed. Paused chores are skipped during trigger evaluation.

---

## Phase 8: User Story 7 — Remove a Chore (P2)

**Goal**: Users can remove a chore from the Chores panel. Removal deletes the chore record, closes any currently open GitHub Issue, and preserves the template file in the repository.

**Independent Test**: Remove a chore that has an open triggered issue → verify chore disappears from panel, associated GitHub Issue is closed, template .md file remains in .github/ISSUE_TEMPLATE/.

### Implementation for User Story 7

- [X] T043 [US7] Implement DELETE /chores/{project_id}/{chore_id} handler in backend/src/api/chores.py — if chore has current_issue_number, close the GitHub Issue via github_service; call ChoresService.delete_chore(); return deletion result with closed_issue_number if applicable
- [X] T044 [US7] Add remove chore action to ChoreCard in frontend/src/components/chores/ChoreCard.tsx — delete button with confirmation prompt, calls deleteChore mutation, shows feedback
- [X] T045 [US7] Implement deleteChore mutation in frontend/src/hooks/useChores.ts — DELETE /chores/{project_id}/{chore_id}, invalidate chores list query on success

### Tests for User Story 7

- [X] T046 [P] [US7] Write backend unit test for delete chore in backend/tests/unit/test_chores_api.py — test successful deletion, issue closure when open, 404 for nonexistent chore, template file NOT deleted

**Checkpoint**: Chores can be removed from the panel. Open issues are closed on removal. Template files preserved in repo.

---

## Phase 9: User Story 3 — Add Chore with Sparse Input via Chat (P2)

**Goal**: Users entering sparse input (short phrases, no structured markdown) are guided through an interactive chat conversation with the AI agent to collaboratively build a robust GitHub Issue Template before creating the chore.

**Independent Test**: Click "Add Chore" → enter sparse text (e.g., "create refactor chore") → chat agent opens → answer follow-up questions → confirm finalized template → verify same PR+tracking-issue+chore creation flow as rich input.

### Implementation for User Story 3

- [X] T047 [US3] Implement chat conversation state management in backend/src/services/chores/service.py — in-memory conversation store (dict keyed by conversation_id), system prompt for GitHub Issue Template generation via multi-turn conversation, conversation cleanup on template finalization
- [X] T048 [US3] Implement POST /chores/{project_id}/chat handler in backend/src/api/chores.py — receive ChoreChatMessage, create/retrieve conversation, call AIAgentService.generate_completion() with template-building system prompt and conversation history, detect when template is finalized (template_ready flag), return ChoreChatResponse with message, conversation_id, and optional template content
- [X] T049 [P] [US3] Create ChoreChatFlow component in frontend/src/components/chores/ChoreChatFlow.tsx — embedded mini-chat UI within AddChoreModal, message list display, text input, sends messages to /chores/{project_id}/chat endpoint, shows finalized template preview with confirm button when template_ready=true
- [X] T050 [US3] Integrate sparse detection routing into AddChoreModal in frontend/src/components/chores/AddChoreModal.tsx — on submit, apply sparse heuristic (≤15 words or ≤40 words single-line without markdown structure), route sparse input to ChoreChatFlow, route rich input to direct createChore mutation
- [X] T051 [US3] Add useChoreChat hook in frontend/src/hooks/useChores.ts — POST /chores/{project_id}/chat mutation, manage conversation_id state across messages, handle template_ready response to transition back to create flow

### Tests for User Story 3

- [X] T052 [P] [US3] Write backend unit test for chat endpoint in backend/tests/unit/test_chores_api.py — test first message creates conversation, subsequent messages continue conversation, template finalization detection
- [X] T053 [P] [US3] Write frontend test for sparse detection and chat flow in frontend/src/components/chores/__tests__/AddChoreModal.test.tsx — test sparse input routes to chat, rich input submits directly, chat conversation renders messages

**Checkpoint**: Sparse input users get AI-assisted template creation via interactive chat. Full end-to-end chore creation works for both rich and sparse paths.

---

## Phase 10: User Story 8 — Manual Chore Trigger (P3)

**Goal**: Users can manually trigger a chore for testing purposes, executing the same flow as automatic triggers (issue creation + agent pipeline). Subject to the same 1-open-instance constraint.

**Independent Test**: Manually trigger a chore with no open instance → verify issue created and agent pipeline executes. Try triggering again while issue is open → verify 409 response and user notification.

### Implementation for User Story 8

- [X] T054 [US8] Implement POST /chores/{project_id}/{chore_id}/trigger handler in backend/src/api/chores.py — call ChoresService.trigger_chore(), return ChoreTriggerResult on success, return 409 with skip_reason if open instance exists, return 404 if chore not found
- [X] T055 [US8] Add manual trigger button to ChoreCard in frontend/src/components/chores/ChoreCard.tsx — trigger button disabled when current_issue_number is set, calls triggerChore mutation, shows success/error feedback
- [X] T056 [US8] Implement triggerChore mutation in frontend/src/hooks/useChores.ts — POST /chores/{project_id}/{chore_id}/trigger, handle 409 conflict response with user-facing message, invalidate chores list on success

### Tests for User Story 8

- [X] T057 [P] [US8] Write backend unit test for manual trigger in backend/tests/unit/test_chores_api.py — test successful trigger returns ChoreTriggerResult, 409 when instance open, 404 for nonexistent chore

**Checkpoint**: Manual trigger works for testing. Same 1-open-instance constraint enforced as automatic triggers.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, error resilience, and final validation across all user stories.

- [X] T058 Implement edge case handling for externally-closed issues in backend/src/services/chores/service.py — during evaluate_triggers(), check if current_issue_number is set but the GitHub Issue is closed (via github_service), clear current_issue_number and current_issue_node_id so chore can trigger on next cycle
- [X] T059 [P] Add user-facing warnings for edge cases in frontend/src/components/chores/ChoreCard.tsx — warning indicator when template file may be missing, trigger failure state display ("Trigger failed — retrying"), warning when agent pipeline config is not set for project
- [X] T060 [P] Update API documentation and inline code comments across backend/src/api/chores.py and backend/src/services/chores/ files
- [X] T061 Run quickstart.md verification steps — docker-compose up --build, navigate to project board, verify Chores panel renders, create a chore, configure schedule, verify trigger evaluation, confirm all CRUD operations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Stories (Phases 3–10)**: All depend on Phase 2 completion
  - P1 stories recommended in order: US1 → US2 → US4 → US5
  - P2 stories can start after Phase 2: US6, US7, US3
  - P3 stories: US8 depends on US5 (reuses trigger_chore method)
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (View Panel)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (Add Chore Rich)**: Can start after Phase 2 — no hard dependencies; US1 panel will display results but US2 work is independent
- **US4 (Configure Schedule)**: Can start after Phase 2 — benefits from US1 panel for display but schedule config can be built independently
- **US5 (Trigger + Pipeline)**: Can start after Phase 2 — fully testable with schedules from US4, but trigger logic is independent
- **US6 (Toggle)**: Can start after Phase 2 — thin story, mostly frontend toggle; backend filter in evaluate_triggers from US5
- **US7 (Remove)**: Can start after Phase 2 — independent of other stories
- **US3 (Sparse Chat)**: Can start after Phase 2 — benefits from US2 (reuses same post-template creation flow)
- **US8 (Manual Trigger)**: Depends on US5 — reuses trigger_chore() method implemented in T034

### Within Each User Story

- Backend service methods before API endpoint handlers
- API endpoints before frontend hooks
- Frontend hooks before components that consume them
- Child components (ChoreCard) before parent containers (ChoresPanel)
- Page integration after container components
- Tests after implementation of the unit under test

### Parallel Opportunities

- **Phase 1**: T002, T003, T004, T005, T006 all marked [P] — can run after T001
- **Phase 2**: T007 and T008 can run in parallel (different files)
- **US1**: T013 and T014 can run in parallel (hooks vs component — different files)
- **US1**: T017 and T018 can run in parallel (backend vs frontend tests)
- **US2**: T021 can run in parallel with T019/T020 (frontend vs backend — different layers)
- **US4**: T027 can run in parallel with T026 (frontend component vs backend handler)
- **US5**: T032 and T033 can run in parallel (scheduler.py vs counter.py — independent)
- **US5**: T037 and T038 can run in parallel (scheduler vs counter tests)
- After Phase 2, user stories US1–US7 can theoretically start in parallel (US8 depends on US5)

---

## Parallel Example: User Story 1

```bash
# Backend and frontend can start in parallel after Phase 2:
Task T012: "Implement GET handler in backend/src/api/chores.py"
Task T013: "Create useChores hooks in frontend/src/hooks/useChores.ts"
Task T014: "Create ChoreCard in frontend/src/components/chores/ChoreCard.tsx"

# Then sequentially (component dependencies):
Task T015: "Create ChoresPanel container" (depends on T014 ChoreCard)
Task T016: "Integrate into ProjectBoardPage" (depends on T015 ChoresPanel)

# Tests in parallel after implementation:
Task T017: "Backend test for list chores"
Task T018: "Frontend test for ChoresPanel"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (remove Housekeeping)
2. Complete Phase 2: Foundational (models, service CRUD, router)
3. Complete Phase 3: User Story 1 (view Chores panel)
4. **STOP and VALIDATE**: Chores panel visible on project board with empty state
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Clean slate with chores infrastructure
2. Add US1 (View Panel) → Panel visible on board → **MVP!**
3. Add US2 (Add Chore Rich) → Users can create chores with detailed input
4. Add US4 (Configure Schedule) → Chores have configurable recurring schedules
5. Add US5 (Trigger + Pipeline) → Full automation loop — chores trigger and create issues/sub-issues
6. Add US6 (Toggle) → Users can pause/resume chores
7. Add US7 (Remove) → Users can manage their chore list
8. Add US3 (Sparse Chat) → AI-assisted chore creation for sparse input
9. Add US8 (Manual Trigger) → Testing/debugging capability
10. Polish → Edge cases, error handling, documentation

### Suggested MVP Scope

- Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (US1)
- Delivers: Chores panel visible, list API functional, empty state UX
- Validates: Migration works, models correct, router registered, panel renders correctly

---

## FR Coverage

| FR | Covered By | Phase |
|----|-----------|-------|
| FR-001 | T001–T006 | Phase 1 |
| FR-002 | T015, T016 | Phase 3 (US1) |
| FR-003 | T014 | Phase 3 (US1) |
| FR-004 | T021, T022 | Phase 4 (US2) |
| FR-005 | T049, T050 | Phase 9 (US3) |
| FR-006 | T019, T020 | Phase 4 (US2) |
| FR-007 | T019 | Phase 4 (US2) |
| FR-008 | T019, T020 | Phase 4 (US2) |
| FR-009 | T026, T027 | Phase 5 (US4) |
| FR-010 | T033 | Phase 6 (US5) |
| FR-011 | T027, T029 | Phase 5 (US4) |
| FR-012 | T034 | Phase 6 (US5) |
| FR-013 | T034 | Phase 6 (US5) |
| FR-014 | T034 | Phase 6 (US5) |
| FR-015 | T040, T041 | Phase 7 (US6) |
| FR-016 | T043, T044, T045 | Phase 8 (US7) |
| FR-017 | T054, T055 | Phase 10 (US8) |
| FR-018 | T035, T036 | Phase 6 (US5) |

---

## Notes

- [P] tasks = different files, no dependencies on in-progress work
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All file paths are relative to repository root
- Edge cases from spec.md handled in Phase 11 (T058, T059)
