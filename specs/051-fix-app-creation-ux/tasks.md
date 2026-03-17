# Tasks: Debug & Fix Apps Page — New App Creation UX

**Input**: Design documents from `/specs/051-fix-app-creation-ux/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included — explicitly requested by the specification (FR-014 verification steps 7–8).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `apps/solune/backend/src/`, `apps/solune/frontend/src/`
- **Backend tests**: `apps/solune/backend/tests/unit/`
- **Frontend tests**: `apps/solune/frontend/src/pages/`, `apps/solune/frontend/src/components/apps/`
- **Migrations**: `apps/solune/backend/src/migrations/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and model changes required by multiple user stories

- [ ] T001 Create SQL migration adding parent issue columns to apps table in `apps/solune/backend/src/migrations/029_app_parent_issue.sql`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core model and type changes that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Add `parent_issue_number` and `parent_issue_url` fields to App Pydantic model in `apps/solune/backend/src/models/app.py`
- [ ] T003 [P] Add `parent_issue_number` and `parent_issue_url` fields to TypeScript App interface in `apps/solune/frontend/src/types/apps.ts`

**Checkpoint**: Foundation ready — all model/type changes in place, user story implementation can now begin

---

## Phase 3: User Story 1 — Reliable Template File Copying During App Creation (Priority: P1) 🎯 MVP

**Goal**: Harden `build_template_files()` to collect and return warnings for failed files instead of silently skipping them, increase branch-readiness poll timeout with exponential backoff, and surface template file warnings to the frontend.

**Independent Test**: Create a new app and verify all template directories are present. Simulate a file read failure and confirm a warning is returned to the user. Verify branch-readiness poll supports up to ~18.5 seconds with exponential backoff.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T004 [US1] Write test for `build_template_files()` returning `tuple[list[dict], list[str]]` with warning collection for unreadable files in `apps/solune/backend/tests/unit/test_app_service_new_repo.py`
- [ ] T005 [US1] Write test for exponential backoff in branch-readiness polling (8 retries, base_delay=0.5s, max_delay=3s) in `apps/solune/backend/tests/unit/test_app_service_new_repo.py`

### Implementation for User Story 1

- [ ] T006 [P] [US1] Harden `build_template_files()` — add explicit error collection for file read failures and return `tuple[list[dict], list[str]]` (files, warnings) in `apps/solune/backend/src/services/template_files.py`
- [ ] T007 [P] [US1] Increase branch-readiness poll to 8 retries with exponential backoff (base_delay=0.5s, max_delay=3s, ~18.5s max) in `apps/solune/backend/src/services/app_service.py`
- [ ] T008 [US1] Surface template file warnings in `create_app_with_new_repo()` — unpack tuple from `build_template_files()` and append warnings to the App response `warnings[]` in `apps/solune/backend/src/services/app_service.py`

**Checkpoint**: Template file copying is robust and transparent. Branch-readiness poll handles GitHub latency. All file failures surfaced as warnings.

---

## Phase 4: User Story 2 — Automatic Parent Issue Creation to Launch Agent Pipeline (Priority: P1)

**Goal**: Wire up the existing orchestrator/polling infrastructure so that selecting a pipeline during app creation automatically creates a Parent Issue, sub-issues, and starts polling — all best-effort.

**Independent Test**: Create a new app with a pipeline selected → verify Parent Issue appears in repo Issues tab with tracking table, sub-issues are linked, polling is started. Verify that failure to create the Parent Issue adds a warning but does not block app creation.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [US2] Write test for parent issue creation when `pipeline_id` is provided in `create_app_with_new_repo()` in `apps/solune/backend/tests/unit/test_app_service_new_repo.py`
- [ ] T010 [US2] Write test for parent issue creation failure adding warning (best-effort pattern) in `apps/solune/backend/tests/unit/test_app_service_new_repo.py`
- [ ] T011 [US2] Write test for `DELETE /apps/{name}` closing parent issue when `parent_issue_number` is set in `apps/solune/backend/tests/unit/test_app_service_new_repo.py`

### Implementation for User Story 2

- [ ] T012 [US2] Wire up pipeline loading — load `WorkflowConfiguration` from `pipeline_id` when provided in `create_app_with_new_repo()` in `apps/solune/backend/src/services/app_service.py`
- [ ] T013 [US2] Create parent issue after repo + files commit — call `github_projects_service.create_issue()` with body from `append_tracking_to_body()`, title "Build {display_name}", store `parent_issue_number` and `parent_issue_url` on App record (best-effort) in `apps/solune/backend/src/services/app_service.py`
- [ ] T014 [US2] Create sub-issues and start pipeline polling — call `orchestrator.create_all_sub_issues()`, init `PipelineState`, call `ensure_polling_started()` (best-effort) in `apps/solune/backend/src/services/app_service.py`
- [ ] T015 [US2] Handle `same-repo` and `external-repo` types — parse correct owner/repo from `github_repo_url` or `external_repo_url` for parent issue creation in `apps/solune/backend/src/services/app_service.py`
- [ ] T016 [US2] Close parent issue on app deletion — in DELETE handler, if `parent_issue_number` and `github_repo_url` are set, call GitHub API to close the issue (best-effort, log warning on failure) in `apps/solune/backend/src/services/app_service.py`

**Checkpoint**: Pipeline-driven app creation is fully functional. Parent Issue + sub-issues + polling all wired up. Deletion closes the parent issue.

---

## Phase 5: User Story 3 — Pipeline Selection in Create App Dialog (Priority: P2)

**Goal**: Add a pipeline selector dropdown to the Create App dialog so users can choose which automated workflow to run, sending `pipeline_id` in the creation payload.

**Independent Test**: Open the Create App dialog → pipeline selector dropdown is visible → defaults to "None" → select a pipeline and submit → `pipeline_id` is included in the request payload.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T017 [US3] Write test for pipeline selector dropdown visible in create dialog and defaults to "None" in `apps/solune/frontend/src/pages/AppsPage.test.tsx`
- [ ] T018 [US3] Write test for `pipeline_id` included in creation payload when a pipeline is selected in `apps/solune/frontend/src/pages/AppsPage.test.tsx`

### Implementation for User Story 3

- [ ] T019 [US3] Add pipeline selector dropdown to Create App dialog — fetch pipelines via `['pipelines', projectId]` query, render `<select>` with "None" default, position after "Create Project" checkbox in `apps/solune/frontend/src/pages/AppsPage.tsx`
- [ ] T020 [US3] Wire `pipelineId` state into creation payload — add `useState`, include `pipeline_id` in `AppCreate` payload, reset on dialog close in `apps/solune/frontend/src/pages/AppsPage.tsx`

**Checkpoint**: Users can select a pipeline during app creation. The `pipeline_id` is sent to the backend.

---

## Phase 6: User Story 4 — Complete Warning Display After App Creation (Priority: P2)

**Goal**: Show ALL warnings from app creation (not just the first one) using warning-style toasts, and display a structured success summary toast.

**Independent Test**: Create an app that generates multiple warnings → verify all warnings are displayed with warning toast style (not error style). Verify success summary toast shows ✓ for successes and ⚠ for warnings.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T021 [US4] Write test for all warnings displayed (iterate `warnings[]` instead of only `warnings[0]`) in `apps/solune/frontend/src/pages/AppsPage.test.tsx`
- [ ] T022 [US4] Write test for warning toast style (not error style) and structured success summary toast in `apps/solune/frontend/src/pages/AppsPage.test.tsx`

### Implementation for User Story 4

- [ ] T023 [US4] Show ALL warnings — replace `showError(createdApp.warnings[0])` with iteration over all warnings using `showWarning()` or warning-style equivalent in `apps/solune/frontend/src/pages/AppsPage.tsx`
- [ ] T024 [US4] Add structured success summary toast — display "✓ Repository created / ✓ Template files committed / ✓ Pipeline started / ⚠ {warning}" after successful creation in `apps/solune/frontend/src/pages/AppsPage.tsx`

**Checkpoint**: Users see full transparency into app creation results. All warnings visible, styled correctly.

---

## Phase 7: User Story 5 — Parent Issue Link and Pipeline Info in App Detail View (Priority: P3)

**Goal**: Display the Parent Issue as a clickable link in the app detail view, show pipeline name, and add a pipeline status badge to app cards in the list. Maintain backward compatibility for apps without parent issues.

**Independent Test**: View an app with a Parent Issue → link is clickable, opens in new tab. View an app with a pipeline → pipeline name shown. View the apps list → pipeline badge on cards with active pipelines. View an app without parent issue → no errors, section absent.

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T025 [P] [US5] Write test for parent issue link rendered as clickable `<a>` tag when `parent_issue_url` is non-null in `apps/solune/frontend/src/components/apps/AppDetailView.test.tsx`
- [ ] T026 [P] [US5] Write test for pipeline badge shown on AppCard when `parent_issue_number` is non-null in `apps/solune/frontend/src/components/apps/AppCard.test.tsx`
- [ ] T027 [US5] Write test for backward compatibility — app without `parent_issue_url` renders cleanly without errors in `apps/solune/frontend/src/components/apps/AppDetailView.test.tsx`

### Implementation for User Story 5

- [ ] T028 [US5] Add parent issue link — conditionally render `<a href={parent_issue_url}>` with "Parent Issue #{parent_issue_number}" label, opens in new tab, in GitHub links section in `apps/solune/frontend/src/components/apps/AppDetailView.tsx`
- [ ] T029 [US5] Add pipeline name display — conditionally render pipeline name (or fallback to `associated_pipeline_id`) when pipeline is set in `apps/solune/frontend/src/components/apps/AppDetailView.tsx`
- [ ] T030 [P] [US5] Add pipeline status badge — conditionally render small indigo pill badge "Pipeline" when `parent_issue_number` is non-null, positioned after status badge in `apps/solune/frontend/src/components/apps/AppCard.tsx`

**Checkpoint**: All user stories are independently functional. Detail view shows parent issue + pipeline info. Cards show pipeline badge. Legacy apps display correctly.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verification, backward compatibility, and full test suite execution

- [ ] T031 Run quickstart.md validation steps — verify migration applied, all endpoints return expected data
- [ ] T032 Backward compatibility verification — confirm apps created before this feature display correctly in list and detail views
- [ ] T033 Run full backend test suite: `cd apps/solune/backend && python -m pytest tests/unit/test_app_service*.py tests/unit/test_api_apps.py -v`
- [ ] T034 Run full frontend test suite: `cd apps/solune/frontend && npx vitest run src/pages/AppsPage.test.tsx src/components/apps/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — can start after Phase 2
- **User Story 2 (Phase 4)**: Depends on Foundational — can start after Phase 2 (parallel with US1)
- **User Story 3 (Phase 5)**: Depends on Foundational + US2 backend wiring (T012) for pipeline loading
- **User Story 4 (Phase 6)**: Depends on Foundational — can start after Phase 2 (parallel with US1/US2)
- **User Story 5 (Phase 7)**: Depends on Foundational + model fields (T002, T003)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent — can start after Foundational
- **User Story 2 (P1)**: Independent — can start after Foundational (parallel with US1)
- **User Story 3 (P2)**: Depends on US2 backend pipeline wiring (T012) for pipeline data; frontend-only otherwise
- **User Story 4 (P2)**: Independent — can start after Foundational (frontend-only change)
- **User Story 5 (P3)**: Independent — can start after Foundational (frontend-only, uses new type fields from T003)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/types before services
- Services before endpoints/UI
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 2**: T002 (backend model) and T003 (frontend type) can run in parallel — different repos
- **Phase 3**: T006 (template_files.py) and T007 (app_service.py) can run in parallel — different files
- **Phase 5 + Phase 6**: US3 and US4 can run in parallel — both frontend, but different concerns
- **Phase 7**: T025 (AppDetailView test) and T026 (AppCard test) can run in parallel — different test files
- **Phase 7**: T028/T029 (AppDetailView) and T030 (AppCard) can run in parallel — different component files
- **Cross-phase**: US1 (backend) and US4/US5 (frontend) can be worked on in parallel by different developers

---

## Parallel Example: User Story 1

```bash
# Launch implementation tasks for different files together:
Task T006: "Harden build_template_files() in apps/solune/backend/src/services/template_files.py"
Task T007: "Increase branch-readiness poll timeout in apps/solune/backend/src/services/app_service.py"

# Then sequentially (same file dependency):
Task T008: "Surface template file warnings in apps/solune/backend/src/services/app_service.py"
```

## Parallel Example: User Story 5

```bash
# Launch tests for different component files together:
Task T025: "Test parent issue link in AppDetailView.test.tsx"
Task T026: "Test pipeline badge in AppCard.test.tsx"

# Launch implementation for different component files together:
Task T028+T029: "Parent issue link + pipeline name in AppDetailView.tsx"
Task T030: "Pipeline badge in AppCard.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (migration)
2. Complete Phase 2: Foundational (model + type changes)
3. Complete Phase 3: User Story 1 (template file hardening)
4. **STOP and VALIDATE**: Test template file copying independently
5. Deploy/demo if ready — template reliability is the most critical fix

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (P1) → Test independently → Deploy (template file reliability ✓)
3. Add User Story 2 (P1) → Test independently → Deploy (parent issue + pipeline automation ✓)
4. Add User Story 3 (P2) → Test independently → Deploy (pipeline selector UX ✓)
5. Add User Story 4 (P2) → Test independently → Deploy (full warning display ✓)
6. Add User Story 5 (P3) → Test independently → Deploy (detail view + badge ✓)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (backend — template files) + User Story 2 (backend — parent issue)
   - Developer B: User Story 3 (frontend — pipeline selector) + User Story 4 (frontend — warnings)
   - Developer C: User Story 5 (frontend — detail view + cards)
3. Stories complete and integrate independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 34 |
| **Setup tasks** | 1 (T001) |
| **Foundational tasks** | 2 (T002–T003) |
| **US1 tasks (P1)** | 5 (T004–T008) |
| **US2 tasks (P1)** | 8 (T009–T016) |
| **US3 tasks (P2)** | 4 (T017–T020) |
| **US4 tasks (P2)** | 4 (T021–T024) |
| **US5 tasks (P3)** | 6 (T025–T030) |
| **Polish tasks** | 4 (T031–T034) |
| **Parallel opportunities** | 6 identified (see Dependencies section) |
| **Suggested MVP scope** | US1 only (Phases 1–3, 8 tasks) |

### Independent Test Criteria Per Story

| Story | Independent Test |
|-------|-----------------|
| US1 | Create app → verify template dirs present + simulate read failure → warning returned + backoff handles 18.5s |
| US2 | Create app with pipeline → Parent Issue in repo Issues tab with tracking table + sub-issues + polling started |
| US3 | Open Create App dialog → pipeline dropdown visible → defaults to "None" → pipeline_id in payload |
| US4 | Create app with multiple warnings → all displayed with warning style + structured success summary |
| US5 | View app with parent issue → clickable link + pipeline name shown + badge on card + legacy apps clean |

### Format Validation

✅ All 34 tasks follow the checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
✅ Setup/Foundational/Polish tasks have NO story label
✅ User story phase tasks have story labels ([US1]–[US5])
✅ [P] markers only on tasks with different files and no dependencies
✅ All tasks include exact file paths

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests MUST fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Reference patterns: `_create_parent_issue_sub_issues()` in `tasks.py`, `execute_full_workflow()` in `orchestrator.py`, `append_tracking_to_body()` in `agent_tracking.py`, `ensure_polling_started()` in `polling_loop.py`
