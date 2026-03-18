# Tasks: Debug & Fix Apps Page — New App Creation UX

**Input**: Design documents from `/specs/051-app-creation-ux/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — spec explicitly requests backend tests (`test_app_service_new_repo.py`) and frontend tests (`AppsPage.test.tsx`). Tests are implementation-last (not TDD).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `solune/backend/src/`, `solune/backend/tests/`
- **Frontend**: `solune/frontend/src/`
- Note: Issue references `apps/solune/` but actual repo paths are `solune/backend/` and `solune/frontend/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema changes and model updates shared across multiple user stories

- [ ] T001 Create migration `solune/backend/src/migrations/030_app_parent_issue.sql` — `ALTER TABLE apps ADD COLUMN parent_issue_number INTEGER DEFAULT NULL; ALTER TABLE apps ADD COLUMN parent_issue_url TEXT DEFAULT NULL;` (both nullable, no NOT NULL constraint; existing rows default to NULL)
- [ ] T002 [P] Add `parent_issue_number: int | None = None` and `parent_issue_url: str | None = None` fields to the `App` Pydantic model in `solune/backend/src/models/app.py` (after `github_project_id`, before `port`)
- [ ] T003 [P] Add `parent_issue_number: number | null` and `parent_issue_url: string | null` fields to the `App` TypeScript interface in `solune/frontend/src/types/apps.ts` (after `github_project_id`, before `port`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend changes that MUST be complete before user story phases can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Harden `build_template_files()` in `solune/backend/src/services/template_files.py` — change return type from `list[dict[str, str]]` to `tuple[list[dict[str, str]], list[str]]`; collect failed file paths in a warnings list instead of silently skipping via `continue`; return `(files, warnings)` tuple
- [ ] T005 Update the caller of `build_template_files()` in `create_app_with_new_repo()` at `solune/backend/src/services/app_service.py` — unpack `(template_files, template_warnings)` from the new return type; append each template warning to `warnings` list
- [ ] T006 Increase branch-readiness poll timeout in `create_app_with_new_repo()` at `solune/backend/src/services/app_service.py` — replace `range(5)` with `range(10)` and `asyncio.sleep(1)` with exponential backoff using 0-indexed attempt: `sleep = min(1.0 * (1.5 ** attempt), 4.0)` where attempt=0..9, yielding waits of ~1.0s, 1.5s, 2.25s, 3.4s, 4.0s, 4.0s... for ~15s max total wait
- [ ] T007 [P] Wire up pipeline loading in `create_app_with_new_repo()` at `solune/backend/src/services/app_service.py` — when `payload.pipeline_id` is provided, load the pipeline config from the database to get agent mappings and status order; store config for use by parent issue creation

**Checkpoint**: Foundation ready — template warnings propagate, branch poll is resilient, pipeline config is loadable

---

## Phase 3: User Story 1 — Reliable Template File Delivery (Priority: P1) 🎯 MVP

**Goal**: All scaffold template files are committed to new repositories, and any failures are surfaced as warnings to the user

**Independent Test**: Create a new-repo app → verify `.github/agents/`, `.github/prompts/`, `.github/workflows/`, `.specify/`, `.gitignore` are present; simulate a template file read failure → verify a descriptive warning appears in the creation response

### Implementation for User Story 1

- [ ] T008 [US1] Surface template file warnings to frontend — in `create_app_with_new_repo()` at `solune/backend/src/services/app_service.py`, ensure `template_warnings` from `build_template_files()` are added to the `warnings[]` array on the `App` response so users see which files failed (format: `"Failed to read template file: {path}"`)
- [ ] T009 [US1] Verify `.specify/memory/` directory handling in `build_template_files()` at `solune/backend/src/services/template_files.py` — confirm whether it is intentionally excluded or should be included per R7 research decision; add explicit exclusion filter or include it as needed

**Checkpoint**: User Story 1 fully functional — template files reliably delivered, failures surfaced as warnings

---

## Phase 4: User Story 2 — Automatic Parent Issue and Pipeline Launch (Priority: P1) 🎯 MVP

**Goal**: When a pipeline is selected during app creation, a Parent Issue is created in the target repository and the agent pipeline starts automatically

**Independent Test**: Create a new-repo app with a pipeline selected → verify parent issue exists in repo Issues tab with tracking table, sub-issues are created, polling service is active within 60 seconds

### Implementation for User Story 2

- [ ] T010 [US2] Add private function `_create_app_parent_issue()` in `solune/backend/src/services/app_service.py` — create a Parent Issue after template file commit using `github_projects_service.create_issue()` (from `solune/backend/src/services/github_projects/issues.py`) with body containing app description and tracking table via `append_tracking_to_body()` (from `solune/backend/src/services/agent_tracking.py`); title format: `"Build {app.display_name}"`; reference pattern: `_create_parent_issue_sub_issues()` in `solune/backend/src/api/tasks.py`
- [ ] T011 [US2] Store parent issue data on App record in `_create_app_parent_issue()` at `solune/backend/src/services/app_service.py` — set `parent_issue_number` and `parent_issue_url` from the `create_issue()` response; persist to database via UPDATE
- [ ] T012 [US2] Create sub-issues and start pipeline polling in `_create_app_parent_issue()` at `solune/backend/src/services/app_service.py` — call `orchestrator.create_all_sub_issues()` with a `WorkflowContext`, set up `PipelineState`, call `ensure_polling_started()`; reference pattern: `execute_full_workflow()` in `solune/backend/src/services/workflow_orchestrator/orchestrator.py`
- [ ] T013 [US2] Make parent issue creation best-effort in `create_app_with_new_repo()` at `solune/backend/src/services/app_service.py` — wrap `_create_app_parent_issue()` call in try/except; on failure, add warning `"Could not create parent issue: {reason}"` to `warnings[]`; app creation still succeeds
- [ ] T014 [P] [US2] Handle `same-repo` and `external-repo` app types in `_create_app_parent_issue()` at `solune/backend/src/services/app_service.py` — determine target owner/repo based on `repo_type`: `new-repo` uses `github_repo_url`, `external-repo` uses `external_repo_url`, `same-repo` uses the current Solune repo; parse owner/repo from the URL using `urllib.parse` or string splitting on `github.com/{owner}/{repo}`
- [ ] T015 [US2] Add parent issue close logic to `delete_app()` in `solune/backend/src/services/app_service.py` — accept optional `access_token: str` and `github_service` kwargs; when app has `parent_issue_number`, call GitHub REST API to PATCH issue state to `"closed"`; best-effort (failure logged, not raised); parse owner/repo from `github_repo_url` or `external_repo_url`
- [ ] T016 [US2] Update DELETE endpoint in `solune/backend/src/api/apps.py` — pass `access_token` and `github_service` from request context to `delete_app()` so it can close the parent issue

**Checkpoint**: User Story 2 fully functional — parent issue + sub-issues created automatically when pipeline selected, closed on app deletion

---

## Phase 5: User Story 3 — Pipeline Selection in Create Dialog (Priority: P2)

**Goal**: Users can choose a pipeline from available presets in the creation dialog

**Independent Test**: Open Create App dialog → verify pipeline dropdown appears with available options and "None" default → select a pipeline → submit → confirm `pipeline_id` is sent in API payload

### Implementation for User Story 3

- [ ] T017 [US3] Add pipeline selector dropdown to the Create App dialog in `solune/frontend/src/pages/AppsPage.tsx` — query available pipeline configs from the backend API, populate a `<Select>` component with options, default to "None" (no pipeline); include the selected `pipeline_id` in the `AppCreate` payload on submit
- [ ] T018 [US3] Handle empty pipeline presets state in `solune/frontend/src/pages/AppsPage.tsx` — when no pipeline configs are available, disable or hide the pipeline selector with a helpful message (e.g., "No pipelines available")

**Checkpoint**: User Story 3 fully functional — pipeline selection available in create dialog

---

## Phase 6: User Story 4 — Complete Warning Display (Priority: P2)

**Goal**: All warnings from app creation are displayed to the user, not just the first one

**Independent Test**: Trigger a creation with multiple warnings (e.g., Azure secret failure + template file failure) → verify all warnings appear as distinct toast notifications using warning style

### Implementation for User Story 4

- [ ] T019 [US4] Show ALL warnings in `solune/frontend/src/pages/AppsPage.tsx` — replace `showError(createdApp.warnings[0])` with iteration over all `createdApp.warnings`, displaying each as an individual toast using warning style (`showWarning` or equivalent) instead of error style

**Checkpoint**: User Story 4 fully functional — all warnings visible to user

---

## Phase 7: User Story 5 — Parent Issue Link in App Detail View (Priority: P2)

**Goal**: App detail view displays a clickable parent issue link and pipeline association name

**Independent Test**: Navigate to app detail page for an app with a parent issue → verify link is clickable; navigate to app without parent issue → verify no errors

### Implementation for User Story 5

- [ ] T020 [US5] Add parent issue link to `solune/frontend/src/components/apps/AppDetailView.tsx` — display `parent_issue_url` as a clickable external link alongside existing GitHub Repository and GitHub Project links; only render when `parent_issue_url` is not null
- [ ] T021 [US5] Display pipeline association name in `solune/frontend/src/components/apps/AppDetailView.tsx` — show `associated_pipeline_id` as a label when present (e.g., "Pipeline: {name}")
- [ ] T022 [US5] Ensure backward compatibility in `solune/frontend/src/components/apps/AppDetailView.tsx` — apps without `parent_issue_url` (created before this feature) render correctly with no parent issue section and no errors

**Checkpoint**: User Story 5 fully functional — parent issue link and pipeline name visible in detail view

---

## Phase 8: User Story 6 — Pipeline Status Badge on App Card (Priority: P3)

**Goal**: App cards show a small badge indicating pipeline/parent issue status

**Independent Test**: View apps list with mixed apps (some with pipelines, some without) → verify badges appear only on correct cards

### Implementation for User Story 6

- [ ] T023 [US6] Add pipeline status badge to `solune/frontend/src/components/apps/AppCard.tsx` — render a small badge (e.g., "Pipeline" with an icon) when the app has a non-null `parent_issue_url` or `associated_pipeline_id`; no badge when both are null
- [ ] T024 [US6] Ensure backward compatibility in `solune/frontend/src/components/apps/AppCard.tsx` — apps without parent issues display correctly with no extra badge

**Checkpoint**: User Story 6 fully functional — pipeline badges visible on app cards

---

## Phase 9: User Story 7 — Structured Creation Success Feedback (Priority: P3)

**Goal**: After creating an app, a structured summary toast shows the status of each creation step

**Independent Test**: Create a new-repo app with pipeline → verify summary toast shows ✓ Repository created / ✓ Template files committed / ✓ Pipeline started / ⚠ {any warnings}

### Implementation for User Story 7

- [ ] T025 [US7] Improve creation success feedback in `solune/frontend/src/pages/AppsPage.tsx` — replace the generic `showSuccess` toast with a structured summary toast after creation; include status indicators: ✓ Repository created, ✓ Template files committed, ✓ Pipeline started (if `parent_issue_url` is set), ⚠ {warning} for each warning
- [ ] T026 [US7] Handle partial success scenarios in the summary toast in `solune/frontend/src/pages/AppsPage.tsx` — when no pipeline was selected, omit the "Pipeline started" line; when warnings exist, show ⚠ indicators next to affected steps

**Checkpoint**: User Story 7 fully functional — structured creation feedback shown to user

---

## Phase 10: Testing & Verification

**Purpose**: Update tests to cover all new functionality

### Backend Tests

- [ ] T027 [P] Update backend tests in `solune/backend/tests/unit/test_app_service_new_repo.py` — add test for `build_template_files()` returning `(files, warnings)` tuple and template warnings propagating to `App.warnings`
- [ ] T028 [P] Add backend test for parent issue creation in `solune/backend/tests/unit/test_app_service_new_repo.py` — test that `_create_app_parent_issue()` calls `create_issue()` with correct title format `"Build {display_name}"` and body containing tracking table
- [ ] T029 [P] Add backend test for parent issue best-effort failure in `solune/backend/tests/unit/test_app_service_new_repo.py` — test that when parent issue creation fails, the app is still created with a warning containing `"Could not create parent issue"`
- [ ] T030 [P] Add backend test for pipeline state initialization in `solune/backend/tests/unit/test_app_service_new_repo.py` — test that sub-issues are created and polling is started when pipeline config has agent mappings
- [ ] T031 [P] Add backend test for no-pipeline scenario in `solune/backend/tests/unit/test_app_service_new_repo.py` — test that when `pipeline_id` is null, no parent issue is created and no polling is started
- [ ] T032 [P] Add backend test for `delete_app()` parent issue close in `solune/backend/tests/unit/test_app_service_new_repo.py` — test that when app has `parent_issue_number`, the GitHub API is called to close the issue; test that close failure is logged but does not block deletion
- [ ] T033 [P] Add backend test for exponential backoff in `solune/backend/tests/unit/test_app_service_new_repo.py` — test that the branch poll uses increasing sleep intervals up to ~15s max

### Frontend Tests

- [ ] T034 [P] Update frontend tests in `solune/frontend/src/pages/AppsPage.test.tsx` — add test for pipeline selector dropdown: verify it renders, has "None" default, and sends `pipeline_id` in payload when a pipeline is selected
- [ ] T035 [P] Update frontend tests in `solune/frontend/src/pages/AppsPage.test.tsx` — add test for all-warnings display: mock creation response with multiple warnings, verify each warning is shown as a distinct notification (not just the first)
- [ ] T036 [P] Update frontend tests in `solune/frontend/src/pages/AppsPage.test.tsx` — add test for structured success feedback: verify summary toast contains step indicators (Repository created, Template files committed, Pipeline started)
- [ ] T037 [P] Add backward compatibility test — verify apps without `parent_issue_url` and `parent_issue_number` render correctly in both `AppCard.tsx` and `AppDetailView.tsx` with no errors or missing sections

**Checkpoint**: All tests passing — `cd solune/backend && python -m pytest tests/unit/test_app_service*.py tests/unit/test_api_apps.py -v` and `cd solune/frontend && npx vitest run src/pages/AppsPage.test.tsx src/components/apps/AppCard.test.tsx src/components/apps/AppDetailView.test.tsx`

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements that affect multiple user stories

- [ ] T038 [P] Run quickstart.md verification checklist — create new-repo app, verify all scaffold files present, parent issue with tracking table exists, polling active, pipeline dropdown visible, all warnings shown
- [ ] T039 [P] Verify backward compatibility — existing apps without parent issues display correctly in both list and detail views with no visual errors
- [ ] T040 Verify app deletion closes parent issue — delete app with parent issue → confirm issue is closed (not deleted) in GitHub repository

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (migration + models must exist) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 (template warning infrastructure)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (pipeline loading, model fields)
- **User Story 3 (Phase 5)**: Depends on Phase 2 (pipeline loading backend ready)
- **User Story 4 (Phase 6)**: Depends on Phase 2 (warnings propagation)
- **User Story 5 (Phase 7)**: Depends on Phase 1 (TypeScript types updated)
- **User Story 6 (Phase 8)**: Depends on Phase 1 (TypeScript types updated)
- **User Story 7 (Phase 9)**: Depends on Phase 6 (warning display logic)
- **Testing (Phase 10)**: Depends on Phases 3–9 (all implementation complete)
- **Polish (Phase 11)**: Depends on Phase 10 (tests passing)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Independent of US1/US2
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Independent of other stories
- **User Story 5 (P2)**: Can start after Setup (Phase 1) — Only needs TypeScript type updates
- **User Story 6 (P3)**: Can start after Setup (Phase 1) — Only needs TypeScript type updates
- **User Story 7 (P3)**: Depends on US4 (warning display changes) for consistency

### Within Each User Story

- Models and types before services
- Services before API endpoints
- Backend before frontend (for API-dependent UI)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T002 + T003: Model/type updates (different files — backend vs. frontend)
- T004 + T006 + T007: Foundational backend changes (different code paths in different functions)
- T014: Same-repo/external-repo handling (parallel with T012 sub-issue creation)
- T023 + T020: Card badge and detail view link (different frontend components)
- T027–T037: All test tasks can run in parallel (different test files/cases)

---

## Parallel Example: User Story 2

```bash
# After Foundational phase is complete, launch these in parallel:
Task T010: "Add _create_app_parent_issue() in solune/backend/src/services/app_service.py"
Task T014: "Handle same-repo and external-repo types in _create_app_parent_issue()"

# After T010 + T014, launch sequentially:
Task T011: "Store parent issue data on App record"
Task T012: "Create sub-issues and start pipeline polling"
Task T013: "Make parent issue creation best-effort"
```

## Parallel Example: Frontend Stories (US5 + US6)

```bash
# After Setup phase (T003 TypeScript types), launch in parallel:
Task T020: "Add parent issue link to AppDetailView.tsx"
Task T023: "Add pipeline status badge to AppCard.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001–T003) — migration + models
2. Complete Phase 2: Foundational (T004–T007) — template warnings, poll backoff, pipeline loading
3. Complete Phase 3: User Story 1 (T008–T009) — template delivery
4. Complete Phase 4: User Story 2 (T010–T016) — parent issue + pipeline
5. **STOP and VALIDATE**: Test US1 + US2 independently
6. Deploy/demo if ready — core automation works

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Template reliability verified → Deploy (Safety net!)
3. Add User Story 2 → Parent issue + pipeline automation → Deploy (Core feature!)
4. Add User Stories 3 + 4 → Pipeline selector + full warnings → Deploy (UX polish)
5. Add User Stories 5 + 6 → Detail view + card badges → Deploy (Visibility)
6. Add User Story 7 → Structured feedback → Deploy (Delight)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Stories 1 + 2 (backend-heavy, P1)
   - Developer B: User Stories 3 + 4 (frontend, P2)
   - Developer C: User Stories 5 + 6 (frontend, P2/P3)
3. Stories complete and integrate independently
4. Developer D: Tests (Phase 10) after implementation phases

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 40 |
| **Setup tasks** | 3 (T001–T003) |
| **Foundational tasks** | 4 (T004–T007) |
| **US1 tasks** | 2 (T008–T009) |
| **US2 tasks** | 7 (T010–T016) |
| **US3 tasks** | 2 (T017–T018) |
| **US4 tasks** | 1 (T019) |
| **US5 tasks** | 3 (T020–T022) |
| **US6 tasks** | 2 (T023–T024) |
| **US7 tasks** | 2 (T025–T026) |
| **Test tasks** | 11 (T027–T037) |
| **Polish tasks** | 3 (T038–T040) |
| **Parallel opportunities** | 22 tasks marked [P] |
| **MVP scope** | Phases 1–4 (US1 + US2) = 16 tasks |

---

## Notes

- [P] tasks = different files, no dependencies — can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- File paths use actual repo paths (`solune/backend/`, `solune/frontend/`) not issue paths (`apps/solune/`)
- `build_template_files()` returns `tuple[list[dict], list[str]]` — all callers must unpack both values
- Parent issue creation is best-effort — app still created if issue creation fails
- Pipeline selection is optional — no pipeline selected = no parent issue created
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
