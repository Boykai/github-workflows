# Tasks: Housekeeping Issue Templates with Configurable Triggers

**Input**: Design documents from `/specs/014-housekeeping-triggers/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/housekeeping-api.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted per spec guidance (Constitution Principle IV: Test Optionality with Clarity).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- GitHub Actions workflows in `.github/workflows/`
- Database migrations in `backend/src/migrations/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the project structure and scaffolding for the housekeeping feature

- [x] T001 Create housekeeping service package with __init__.py in backend/src/services/housekeeping/__init__.py
- [x] T002 [P] Create database migration with housekeeping_templates, housekeeping_tasks, and housekeeping_trigger_history tables in backend/src/migrations/006_housekeeping.sql

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, service base, seed data, and API scaffold that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create Pydantic models for IssueTemplate, HousekeepingTask, TriggerEvent, and all request/response schemas in backend/src/models/housekeeping.py
- [x] T004 [P] Define three built-in seed template data structures (Security and Privacy Review, Test Coverage Refresh, Bug Bash) in backend/src/services/housekeeping/seed.py
- [x] T005 Implement HousekeepingService base class with aiosqlite database connection, table initialization, and seed template insertion logic in backend/src/services/housekeeping/service.py
- [x] T006 Create housekeeping API router with FastAPI dependency injection scaffold and GET /templates endpoint (list seeded templates) in backend/src/api/housekeeping.py
- [x] T007 Register housekeeping router with /api/v1/housekeeping prefix in backend/src/main.py
- [x] T008 [P] Add housekeeping TypeScript type definitions (IssueTemplate, HousekeepingTask, TriggerEvent) and API client base URL in frontend/src/services/api.ts
- [x] T009 [P] Create useHousekeeping hook scaffold with TanStack Query client setup and base query keys in frontend/src/hooks/useHousekeeping.ts

**Checkpoint**: Foundation ready — database tables exist, models defined, seed templates inserted, API router mounted, frontend types and hook scaffold in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Create and Configure a Housekeeping Task (Priority: P1) 🎯 MVP

**Goal**: Allow maintainers to create named housekeeping tasks with template references and trigger configurations (time-based or count-based) that persist and display in the task list.

**Independent Test**: Create a housekeeping task with name, description, template reference, and trigger config (time-based weekly or count-based every 10 issues), then verify it persists and appears in the task list with all configured values.

### Implementation for User Story 1

- [x] T010 [US1] Implement task CRUD methods (create_task, get_task, list_tasks, update_task, delete_task) with SQLite queries in backend/src/services/housekeeping/service.py
- [x] T011 [US1] Implement task validation logic (template_id must reference existing template, trigger_type/trigger_value consistency, unique name per project_id, cooldown_minutes >= 1) in backend/src/services/housekeeping/service.py
- [x] T012 [US1] Add task CRUD API endpoints (GET /tasks, GET /tasks/{task_id}, POST /tasks, PUT /tasks/{task_id}, DELETE /tasks/{task_id}) with project_id query parameter in backend/src/api/housekeeping.py
- [x] T013 [P] [US1] Add task API client methods (listTasks, getTask, createTask, updateTask, deleteTask) with TypeScript types in frontend/src/services/api.ts
- [x] T014 [US1] Add task queries and mutations (useTaskList, useTask, useCreateTask, useUpdateTask, useDeleteTask) with cache invalidation in frontend/src/hooks/useHousekeeping.ts
- [x] T015 [P] [US1] Create HousekeepingTaskForm component with name, description, template selector dropdown, trigger type radio (time/count), trigger value input (cron or integer), and inline validation errors in frontend/src/components/housekeeping/HousekeepingTaskForm.tsx
- [x] T016 [US1] Create HousekeepingTaskList component displaying tasks with name, trigger type/value, last triggered timestamp, and enabled status in frontend/src/components/housekeeping/HousekeepingTaskList.tsx

**Checkpoint**: Maintainers can create, view, edit, and delete housekeeping tasks through the UI. Tasks persist in SQLite with validated configurations. MVP is functional.

---

## Phase 4: User Story 2 — Automatic Trigger Execution (Priority: P1)

**Goal**: Housekeeping tasks fire automatically — time-based tasks via GitHub Actions cron calling the evaluate-triggers endpoint, count-based tasks via webhook on issue creation — creating parent GitHub Issues with sub issues.

**Independent Test**: Configure a time-based task with a short interval and verify the evaluate-triggers endpoint creates a GitHub Issue on schedule; configure a count-based task and create the threshold number of parent issues to verify automatic triggering.

### Implementation for User Story 2

- [x] T017 [P] [US2] Create time-based scheduler module with cron expression parsing (support named presets: daily, weekly, monthly) and is_task_due evaluation in backend/src/services/housekeeping/scheduler.py
- [x] T018 [P] [US2] Create count-based counter module with threshold evaluation (current_count - last_triggered_issue_count >= trigger_value) and atomic counter tracking in backend/src/services/housekeeping/counter.py
- [x] T019 [US2] Implement trigger execution logic (_execute_task: create parent issue from template via GitHub Issues API, then generate sub issues using WorkflowOrchestrator and DEFAULT_AGENT_MAPPINGS) in backend/src/services/housekeeping/service.py
- [x] T020 [US2] Implement idempotency cooldown guard with atomic compare-and-swap on last_triggered_at within SQLite transaction (skip if within cooldown_minutes window) in backend/src/services/housekeeping/service.py
- [x] T021 [US2] Add evaluate-triggers endpoint (POST /evaluate-triggers) that evaluates all enabled time-based tasks for a project and executes due ones, with service token authentication in backend/src/api/housekeeping.py
- [x] T022 [US2] Extend webhook handler to process issues.opened events — evaluate all enabled count-based housekeeping tasks for the project and trigger those meeting threshold in backend/src/api/webhooks.py
- [x] T023 [P] [US2] Create housekeeping-cron.yml GitHub Actions workflow with schedule cron '*/15 * * * *', minimal permissions, GH_TOKEN authentication, and POST to /api/v1/housekeeping/evaluate-triggers in .github/workflows/housekeeping-cron.yml
- [x] T024 [US2] Implement default sub-issue configuration fallback — when task.sub_issue_config is null, use DEFAULT_AGENT_MAPPINGS from backend/src/constants.py for sub-issue generation in backend/src/services/housekeeping/service.py

**Checkpoint**: Time-based tasks automatically fire via the cron workflow; count-based tasks fire when issue creation threshold is met via webhooks. Idempotency guards prevent duplicate triggers within the cooldown window.

---

## Phase 5: User Story 3 — Built-in Starter Templates (Priority: P2)

**Goal**: Fresh installations include three pre-configured templates (Security and Privacy Review, Test Coverage Refresh, Bug Bash) with detailed #codebase context, protected from modification/deletion, and duplicable for customization.

**Independent Test**: Verify a fresh database initialization includes all three built-in templates via GET /templates?category=built-in; verify built-in templates cannot be modified or deleted; verify a built-in template can be duplicated into a custom copy.

### Implementation for User Story 3

- [x] T025 [US3] Finalize all three built-in seed template bodies with detailed title patterns, #codebase context references, and review/test/bug-finding instructions in backend/src/services/housekeeping/seed.py
- [x] T026 [US3] Implement built-in template protection (reject update/delete requests for category='built-in' with 403 response) in backend/src/services/housekeeping/service.py
- [x] T027 [US3] Add duplicate_template method to create a custom category copy from any template (including built-in) in backend/src/services/housekeeping/service.py
- [x] T028 [US3] Add POST /templates/{template_id}/duplicate endpoint returning the new custom template in backend/src/api/housekeeping.py

**Checkpoint**: Three built-in templates are available on fresh install, protected from modification, and can be duplicated into editable custom copies.

---

## Phase 6: User Story 4 — Manual "Run Now" Trigger (Priority: P2)

**Goal**: Maintainers can manually trigger any housekeeping task on demand, bypassing scheduled or count-based conditions, with cooldown warning and force override.

**Independent Test**: Select an existing task, invoke "Run Now", and verify a GitHub Issue is created and the event appears in history with trigger_type "manual". Verify cooldown warning appears if triggered again within the cooldown window.

### Implementation for User Story 4

- [x] T029 [US4] Implement manual run service method with cooldown check (return remaining seconds if within window), force-override flag, and trigger event recording in backend/src/services/housekeeping/service.py
- [x] T030 [US4] Add manual run endpoint (POST /tasks/{task_id}/run) with optional force=true query parameter, returning trigger event or 409 cooldown conflict in backend/src/api/housekeeping.py
- [x] T031 [P] [US4] Create RunNowButton component with loading state, cooldown confirmation dialog (showing last triggered time and remaining cooldown), and force-execute option in frontend/src/components/housekeeping/RunNowButton.tsx
- [x] T032 [US4] Add runTask mutation with cooldown state handling and optimistic UI update in frontend/src/hooks/useHousekeeping.ts

**Checkpoint**: Maintainers can manually trigger tasks via "Run Now" button. Cooldown protection warns about recent triggers but allows force override.

---

## Phase 7: User Story 5 — Manage Reusable Issue Templates (Priority: P2)

**Goal**: Maintainers can independently create, edit, and delete reusable GitHub Issue templates in a template library, with deletion warnings when templates are referenced by active tasks.

**Independent Test**: Create a new custom template, verify it appears in the template library and is selectable in task configuration. Edit its content and verify changes persist. Attempt to delete a referenced template and verify the warning.

### Implementation for User Story 5

- [x] T033 [US5] Implement template CRUD methods (create_template, get_template, list_templates with category filter, update_template, delete_template) in backend/src/services/housekeeping/service.py
- [x] T034 [US5] Implement template deletion safety check — query referencing housekeeping_tasks and return 409 Conflict with referencing_tasks list if active tasks reference the template, with force=true override in backend/src/services/housekeeping/service.py
- [x] T035 [US5] Add template CRUD API endpoints (GET /templates, GET /templates/{id}, POST /templates, PUT /templates/{id}, DELETE /templates/{id}) with category filter and force delete query parameter in backend/src/api/housekeeping.py
- [x] T036 [P] [US5] Add template API client methods (listTemplates, getTemplate, createTemplate, updateTemplate, deleteTemplate, duplicateTemplate) in frontend/src/services/api.ts
- [x] T037 [US5] Add template queries and mutations (useTemplateList, useCreateTemplate, useUpdateTemplate, useDeleteTemplate, useDuplicateTemplate) in frontend/src/hooks/useHousekeeping.ts
- [x] T038 [US5] Create TemplateLibrary component with template list, create/edit form, delete with reference warning confirmation, built-in template indicators and duplicate action in frontend/src/components/housekeeping/TemplateLibrary.tsx

**Checkpoint**: Full template library management is available. Templates can be created, edited, duplicated, and safely deleted with reference warnings.

---

## Phase 8: User Story 6 — View Trigger and Run History (Priority: P3)

**Goal**: Maintainers can view a chronological history log per housekeeping task showing timestamp, trigger type, resulting GitHub Issue URL, and success/failure status.

**Independent Test**: Trigger a task (manually or via evaluation), then view its history log to verify the entry includes timestamp, trigger type (scheduled/count-based/manual), issue URL, and status. Verify empty state message for tasks with no history.

### Implementation for User Story 6

- [x] T039 [US6] Implement trigger history query methods (get_task_history with limit, offset, and status filter; count total entries) in backend/src/services/housekeeping/service.py
- [x] T040 [US6] Add GET /tasks/{task_id}/history endpoint with limit, offset, and status query parameters returning paginated history list in backend/src/api/housekeeping.py
- [x] T041 [P] [US6] Add history API client method (getTaskHistory with pagination params) in frontend/src/services/api.ts
- [x] T042 [US6] Add history query (useTaskHistory with pagination state) in frontend/src/hooks/useHousekeeping.ts
- [x] T043 [US6] Create TriggerHistoryLog component displaying chronological entries with timestamp, trigger type badge, GitHub Issue URL link, status indicator (success/failure), error details expansion, and empty state message in frontend/src/components/housekeeping/TriggerHistoryLog.tsx

**Checkpoint**: Trigger history is viewable per task with all required fields, pagination, and status filtering.

---

## Phase 9: User Story 7 — Enable and Disable Housekeeping Tasks (Priority: P3)

**Goal**: Maintainers can enable or disable individual tasks without deletion, preserving configuration and history, with automatic triggers paused for disabled tasks.

**Independent Test**: Disable an active task and verify its automatic triggers no longer fire. Re-enable and verify triggers resume from current state. Confirm disabled tasks appear visually distinct in the task list.

### Implementation for User Story 7

- [x] T044 [US7] Implement task toggle service method (set enabled=true/false, preserve all config and history, resume triggers from current state on re-enable) in backend/src/services/housekeeping/service.py
- [x] T045 [US7] Add PATCH /tasks/{task_id}/toggle endpoint accepting {enabled: boolean} and returning updated task in backend/src/api/housekeeping.py
- [x] T046 [US7] Add toggle mutation (useToggleTask) with optimistic UI update in frontend/src/hooks/useHousekeeping.ts
- [x] T047 [US7] Add enable/disable toggle switch and visual distinction for disabled tasks (greyed out or "Paused" label) in frontend/src/components/housekeeping/HousekeepingTaskList.tsx

**Checkpoint**: Tasks can be enabled and disabled. Disabled tasks stop automatic triggers but retain configuration and history. Visual distinction is clear in the UI.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, logging, documentation, and validation improvements across all stories

- [x] T048 [P] Add structured error handling and logging (using existing logging patterns) across all HousekeepingService methods in backend/src/services/housekeeping/service.py
- [x] T049 [P] Add input sanitization and rate limiting (max 1 call per minute per project) for evaluate-triggers endpoint in backend/src/api/housekeeping.py
- [x] T050 [P] Add loading states, error boundaries, and toast notifications to all housekeeping UI components in frontend/src/components/housekeeping/
- [x] T051 [P] Add catch-up trigger detection — on startup, evaluate missed time-based triggers since last_triggered_at and execute once per missed task in backend/src/services/housekeeping/service.py
- [x] T052 Run quickstart.md validation against all implemented endpoints and verify three built-in templates are accessible

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) and User Story 1 (task CRUD must exist for trigger execution)
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — seed templates defined in Foundational, this phase refines and protects them
- **User Story 4 (Phase 6)**: Depends on User Story 2 (trigger execution logic must exist)
- **User Story 5 (Phase 7)**: Depends on Foundational (Phase 2) — template CRUD is independent of task stories
- **User Story 6 (Phase 8)**: Depends on User Story 2 or User Story 4 (trigger events must exist to display)
- **User Story 7 (Phase 9)**: Depends on User Story 1 (task CRUD must exist for toggle)
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US2 (P1)**: Depends on US1 (needs task definitions to evaluate triggers against)
- **US3 (P2)**: Can start after Foundational — independent of US1/US2 (refines seed templates)
- **US4 (P2)**: Depends on US2 (reuses trigger execution logic from US2)
- **US5 (P2)**: Can start after Foundational — independent template management
- **US6 (P3)**: Can start after US2/US4 (needs trigger history entries to display)
- **US7 (P3)**: Can start after US1 (needs task records to toggle)

### Within Each User Story

- Backend service methods before API endpoints
- API endpoints before frontend API clients
- Frontend API clients before hooks
- Hooks before UI components
- Validation/protection logic before dependent endpoints

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (different files)
- **Phase 2**: T003 + T004 in parallel; T008 + T009 in parallel (frontend files independent of backend)
- **Phase 3**: T013 (api.ts) + T015 (TaskForm) in parallel; both are independent of each other
- **Phase 4**: T017 (scheduler.py) + T018 (counter.py) in parallel (different files, same interface)
- **Phase 4**: T023 (cron workflow) in parallel with backend service work
- **Phase 5 + US7**: US3 and US7 can run in parallel (different concerns, different files)
- **Phase 7**: T036 (api.ts) in parallel with backend work
- **Phase 8**: T041 (api.ts) in parallel with backend work
- **Phase 10**: T048 + T049 + T050 + T051 all in parallel (different files/concerns)
- **Cross-story**: US3 + US5 can run in parallel (US3 = seed protection, US5 = template CRUD)
- **Cross-story**: US6 + US7 can run in parallel (different concerns, minimal file overlap)

---

## Parallel Example: User Story 1

```bash
# After Foundational phase completes:

# Step 1 — Backend service (sequential, same file):
Task T010: "Implement task CRUD methods in backend/src/services/housekeeping/service.py"
Task T011: "Implement task validation logic in backend/src/services/housekeeping/service.py"

# Step 2 — Backend API + Frontend API (parallel, different files):
Task T012: "Add task CRUD API endpoints in backend/src/api/housekeeping.py"
Task T013: "Add task API client methods in frontend/src/services/api.ts"  [P]

# Step 3 — Frontend hook:
Task T014: "Add task queries and mutations in frontend/src/hooks/useHousekeeping.ts"

# Step 4 — Frontend components (parallel, different files):
Task T015: "Create HousekeepingTaskForm in frontend/src/components/housekeeping/HousekeepingTaskForm.tsx"  [P]
Task T016: "Create HousekeepingTaskList in frontend/src/components/housekeeping/HousekeepingTaskList.tsx"
```

## Parallel Example: User Story 2

```bash
# After US1 completes:

# Step 1 — Scheduler + Counter (parallel, different files):
Task T017: "Create scheduler module in backend/src/services/housekeeping/scheduler.py"  [P]
Task T018: "Create counter module in backend/src/services/housekeeping/counter.py"  [P]

# Step 2 — Trigger execution (sequential, depends on T017+T018):
Task T019: "Implement trigger execution logic in backend/src/services/housekeeping/service.py"
Task T020: "Implement idempotency cooldown guard in backend/src/services/housekeeping/service.py"

# Step 3 — Endpoints + Workflow (parallel, different files):
Task T021: "Add evaluate-triggers endpoint in backend/src/api/housekeeping.py"
Task T022: "Extend webhook handler in backend/src/api/webhooks.py"
Task T023: "Create housekeeping-cron.yml in .github/workflows/housekeeping-cron.yml"  [P]

# Step 4 — Default config fallback:
Task T024: "Implement default sub-issue config fallback in backend/src/services/housekeeping/service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Create and Configure Tasks)
4. **STOP and VALIDATE**: Create a task via API, verify it persists, verify task list displays it
5. Deploy/demo if ready — maintainers can define housekeeping tasks

### Incremental Delivery

1. Setup + Foundational → Foundation ready (database, models, seed templates)
2. Add US1 (Task CRUD) → Test independently → Deploy/Demo (**MVP!**)
3. Add US2 (Automatic Triggers) → Test independently → Deploy/Demo (tasks now fire automatically)
4. Add US3 (Built-in Templates) → Test independently → Deploy/Demo (protected starter templates)
5. Add US4 (Manual Run Now) → Test independently → Deploy/Demo (on-demand execution)
6. Add US5 (Template Management) → Test independently → Deploy/Demo (full template CRUD)
7. Add US6 (Trigger History) → Test independently → Deploy/Demo (auditability)
8. Add US7 (Enable/Disable) → Test independently → Deploy/Demo (operational flexibility)
9. Polish → Final validation, error handling, documentation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Task CRUD) → US2 (Triggers) → US4 (Run Now)
   - Developer B: US5 (Template Management) → US3 (Built-in Templates)
   - Developer C: US7 (Enable/Disable) → US6 (Trigger History)
3. Each story completes and integrates independently
4. Team completes Polish phase together

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [Story] label maps each task to its specific user story for traceability
- Each user story should be independently completable and testable
- Tests are NOT included per spec guidance — add test tasks only if explicitly requested
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- The three built-in templates (Security Review, Test Coverage, Bug Bash) are seeded in Foundational and refined in US3
- Idempotency guards (US2 T020) are critical — ensure atomic writes in SQLite to prevent double-triggers
- Frontend components use Shadcn/ui primitives following existing component patterns
- The evaluate-triggers endpoint uses service token auth, not user session auth
