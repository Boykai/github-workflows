# Tasks: Fix App Creation to Respect Repo Type for Issue/Pipeline Placement

**Input**: Design documents from `/specs/049-fix-repo-type-routing/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Required — spec mandates verification via SC-001 through SC-007.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- **Tests**: `solune/backend/tests/unit/`, `solune/frontend/src/components/apps/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the shared `parse_github_url()` utility that multiple user stories depend on

- [X] T001 Add `parse_github_url(url: str) -> tuple[str, str]` utility function in `solune/backend/src/utils.py` — validates `github.com` host, strips `.git` suffix and trailing slashes, returns `(owner, repo)`, raises `ValidationError` for malformed URLs (FR-005)
- [X] T002 [P] Add unit tests for `parse_github_url()` in `solune/backend/tests/unit/test_utils.py` — cover valid URLs, `.git` suffix, trailing slash, non-github.com hosts, missing repo segment, empty/malformed input

**Checkpoint**: `parse_github_url()` ready — foundational utility for US3 and US4

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No additional foundational work needed — existing DB schema, models, and service methods are sufficient. The `parse_github_url()` utility from Phase 1 is the only prerequisite.

**⚠️ CRITICAL**: Phase 1 must complete before user story phases.

---

## Phase 3: User Story 1 — Same-Repo App Pipeline Launch (Priority: P1) 🎯 MVP

**Goal**: Ensure same-repo apps continue to route pipeline launches via the user-supplied `project_id`. This is a no-regression guard — the routing logic change must not break the existing default flow. (FR-001, FR-009)

**Independent Test**: Create a `same-repo` app with a pipeline and project_id, verify parent issue and sub-issues use `payload.project_id`.

### Implementation for User Story 1

- [X] T003 [US1] Refactor pipeline launch routing in `solune/backend/src/api/apps.py` — replace `launch_project_id = payload.project_id or app.github_project_id` with repo-type-aware conditional: `same-repo` uses `payload.project_id`, `new-repo` and `external-repo` use `app.github_project_id`; skip with logged warning if `launch_project_id` is None (FR-001, FR-007)

### Tests for User Story 1

- [X] T004 [P] [US1] Add/update unit tests in `solune/backend/tests/unit/test_api_apps.py` — verify `same-repo` app with pipeline uses `payload.project_id` for launch; verify `same-repo` without pipeline creates app with no pipeline launch; verify no regression from prior behavior (SC-004)

**Checkpoint**: Same-repo pipeline routing verified — zero regression risk confirmed

---

## Phase 4: User Story 2 — New-Repo App Pipeline Launch (Priority: P1)

**Goal**: Fix `new-repo` apps so pipeline launch uses `app.github_project_id` (the project created with the new repo) instead of `payload.project_id`. Issues must land in the new repo, not Solune's default. (FR-001)

**Independent Test**: Create a `new-repo` app with a pipeline, verify parent issue and sub-issues appear in the new repository's project.

### Implementation for User Story 2

> T003 already contains the routing fix for new-repo (conditional in `apps.py`). This phase adds the tests to verify it.

### Tests for User Story 2

- [X] T005 [P] [US2] Add unit tests in `solune/backend/tests/unit/test_api_apps.py` — verify `new-repo` app with pipeline uses `app.github_project_id` (not `payload.project_id`) for launch; verify `new-repo` with null `github_project_id` skips pipeline with warning (SC-001, FR-007)

**Checkpoint**: New-repo pipeline routing verified — issues routed to new repo's project

---

## Phase 5: User Story 3 — External-Repo App Scaffold Placement (Priority: P1)

**Goal**: Fix external-repo scaffold to commit files into the external repository instead of Solune's default repo. Parse `external_repo_url` to extract `owner`/`repo` and pass them to `get_branch_head_oid()` and `commit_files()`. (FR-002, FR-005, FR-008)

**Independent Test**: Create an `external-repo` app with a valid external repo URL, verify scaffold files are committed to the external repository.

### Implementation for User Story 3

- [X] T006 [US3] Add `external_repo_url` Pydantic model validation to `AppCreate` in `solune/backend/src/models/app.py` — add `model_validator` that calls `parse_github_url()` when `repo_type == external-repo` to validate URL format before any operations (FR-005)
- [X] T007 [US3] Modify `create_app()` in `solune/backend/src/services/app_service.py` — in the non-`NEW_REPO` branch, when `repo_type == EXTERNAL_REPO`, parse `external_repo_url` via `parse_github_url()` and use extracted `owner`/`repo` for `get_branch_head_oid()` and `commit_files()` instead of `settings.default_repo_owner`/`settings.default_repo_name` (FR-002)

### Tests for User Story 3

- [X] T008 [P] [US3] Add unit tests in `solune/backend/tests/unit/test_app_service.py` — verify `external-repo` scaffold uses parsed owner/repo from URL; verify malformed URL raises `ValidationError`; verify permission error surfaces cleanly (SC-002, FR-008)
- [X] T009 [P] [US3] Add model validation tests in `solune/backend/tests/unit/test_models.py` or `test_app_service.py` — verify `AppCreate` with `repo_type=external-repo` and invalid URL fails validation; verify valid URL passes (FR-005)

**Checkpoint**: External-repo scaffold routing verified — files committed to correct repo

---

## Phase 6: User Story 4 — External-Repo Auto-Create Project and Pipeline Launch (Priority: P2)

**Goal**: Auto-create a GitHub Project V2 on the external repository when an external-repo app is created with a pipeline. Link the project to the repo, store `github_project_id` and `github_project_url` on the app record, and use it for pipeline launch. (FR-003, FR-004)

**Independent Test**: Create an `external-repo` app with a pipeline, verify a Project V2 is created on the external repo and parent issue + sub-issues appear there.

### Implementation for User Story 4

- [X] T010 [US4] Add external-repo project auto-creation to `create_app()` in `solune/backend/src/services/app_service.py` — after scaffold commit for `EXTERNAL_REPO`, call `create_project_v2(access_token, owner, title)`, then `get_repository_info(access_token, owner, repo)` to get `repository_id`, then `link_project_to_repository(access_token, project_id, repository_id)`; store `github_project_id` and `github_project_url` on the app DB record; wrap in try/except for partial success (FR-003, FR-004)
- [X] T011 [US4] Update the DB INSERT in `create_app()` in `solune/backend/src/services/app_service.py` — include `github_project_id`, `github_project_url`, and `github_repo_url` columns for external-repo apps (FR-004)

### Tests for User Story 4

- [X] T012 [P] [US4] Add unit tests in `solune/backend/tests/unit/test_app_service.py` — verify external-repo with pipeline triggers project auto-creation; verify `github_project_id` and `github_project_url` stored on app record; verify project creation failure is non-fatal (app still created with null project fields); verify pipeline launch skipped with warning when project_id is null (SC-003, SC-005, FR-007)
- [X] T013 [P] [US4] Add unit tests in `solune/backend/tests/unit/test_api_apps.py` — verify `external-repo` app with pipeline uses `app.github_project_id` for launch; verify pipeline skipped gracefully when `github_project_id` is null (SC-003, FR-007)

**Checkpoint**: External-repo fully functional — scaffold, project, and pipeline all routed correctly

---

## Phase 7: User Story 5 — Frontend Project ID Scoping (Priority: P2)

**Goal**: The `CreateAppDialog` must only include `project_id` in the API payload when `repoType === 'same-repo'`. For `new-repo` and `external-repo`, `project_id` must be omitted so the backend uses its own routing logic. (FR-006)

**Independent Test**: Inspect the API payload for each repo type; verify `project_id` is present only for `same-repo`.

### Implementation for User Story 5

- [X] T014 [US5] Update `CreateAppDialog.tsx` payload construction in `solune/frontend/src/components/apps/CreateAppDialog.tsx` — change the `project_id` inclusion condition from `if (projectId)` to `if (repoType === 'same-repo' && projectId)` (FR-006)

### Tests for User Story 5

- [X] T015 [P] [US5] Add/update tests in `solune/frontend/src/components/apps/CreateAppDialog.test.tsx` — verify `same-repo` payload includes `project_id`; verify `new-repo` payload omits `project_id`; verify `external-repo` payload omits `project_id` (SC-006)

**Checkpoint**: Frontend correctly scopes `project_id` — backend routing not overridden

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, linting, and cross-story regression checks

- [X] T016 Run full backend test suite (`python -m pytest solune/backend/tests/ -x -q`) and fix any failures
- [X] T017 [P] Run full frontend test suite (`cd solune/frontend && npx vitest run`) and fix any failures
- [X] T018 [P] Run linters (`ruff check`, `ruff format --check`, `pyright`, `eslint`, `tsc --noEmit`) and fix any violations
- [X] T019 Validate quickstart.md scenarios — verify each repo type creates issues/scaffolds in the correct repository

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: N/A — no additional foundational work
- **Phase 3 (US1)**: Depends on Phase 1 (T001 must exist before T003 routing logic)
- **Phase 4 (US2)**: Depends on Phase 3 (T003 contains the routing fix for all types)
- **Phase 5 (US3)**: Depends on Phase 1 (T001 `parse_github_url` needed); can run in parallel with Phase 3-4 for model/service changes
- **Phase 6 (US4)**: Depends on Phase 5 (T007 external-repo scaffold path must exist before adding project auto-creation)
- **Phase 7 (US5)**: Independent of all backend phases — can run in parallel with Phases 3-6
- **Phase 8 (Polish)**: Depends on all prior phases

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories — routing refactor only
- **US2 (P1)**: Covered by same T003 routing refactor as US1 — tests are independent
- **US3 (P1)**: Depends on T001 (`parse_github_url`) — independent of US1/US2
- **US4 (P2)**: Depends on US3 scaffold fix (T007) — adds project auto-creation on top
- **US5 (P2)**: Fully independent — frontend-only change

### Within Each User Story

- Implementation tasks before test tasks (pragmatic order — tests verify the implementation)
- Models/validation before service logic
- Service logic before endpoint/API layer
- Core implementation before integration points

### Parallel Opportunities

- T001 and T002 can run in parallel (utility function + its tests in separate files)
- T004 and T005 are independent test tasks (same file but independent test classes)
- T008 and T009 can run in parallel (different test focuses, both test US3)
- T012 and T013 can run in parallel (service tests vs API tests for US4)
- **US5 (Phase 7) can run entirely in parallel with all backend phases (3-6)**
- T016, T017, T018 can run in parallel (backend tests, frontend tests, linters)

---

## Parallel Example: Core Implementation Sprint

```bash
# After Phase 1 completes, launch these in parallel:

# Track 1 — Backend routing (US1 + US2):
Task T003: Refactor pipeline launch routing in apps.py
Task T004: Same-repo pipeline launch tests
Task T005: New-repo pipeline launch tests

# Track 2 — Backend scaffold (US3):
Task T006: AppCreate model validation  
Task T007: External-repo scaffold routing in app_service.py
Task T008: External-repo scaffold tests
Task T009: Model validation tests

# Track 3 — Frontend (US5, fully independent):
Task T014: CreateAppDialog project_id scoping
Task T015: CreateAppDialog tests
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: `parse_github_url()` utility (T001-T002)
2. Complete Phase 3: Same-repo no-regression guard (T003-T004)
3. Complete Phase 4: New-repo routing fix (T005)
4. Complete Phase 5: External-repo scaffold fix (T006-T009)
5. **STOP and VALIDATE**: All P1 stories independently tested
6. Deploy/demo if ready — core routing bugs are fixed

### Incremental Delivery

1. Phase 1 → Utility ready
2. Phase 3 (US1) → Same-repo regression guard verified → Safe to proceed
3. Phase 4 (US2) → New-repo issues go to correct repo → Critical bug fixed
4. Phase 5 (US3) → External-repo scaffold goes to correct repo → Critical bug fixed
5. Phase 6 (US4) → External-repo has full pipeline support → Feature complete
6. Phase 7 (US5) → Frontend prevents payload override → Defense in depth
7. Phase 8 → Full suite passes, linters green → Ready to merge

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- T003 is the central routing refactor that serves US1, US2, and US4 — it's in Phase 3 because US1 is the highest priority and validates same-repo first
- T010 and T011 can be combined into a single commit since they modify the same function
- All GitHub service calls are mocked with `AsyncMock` — no live API calls in tests
- Commit after each task or logical group
