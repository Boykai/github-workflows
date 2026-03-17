# Tasks: New Repository & New Project Creation for Solune

**Input**: Design documents from `/specs/049-repo-project-creation/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — explicitly requested in plan.md Phase 5 and quickstart.md verification checklist.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/` (Python), `solune/frontend/src/` (TypeScript/React)
- **Tests**: `solune/backend/tests/unit/` (pytest), `solune/frontend/src/` (Vitest co-located)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new files and infrastructure that multiple user stories depend on

- [x] T001 Add GraphQL mutation strings (CREATE_PROJECT_V2_MUTATION, LINK_PROJECT_V2_TO_REPO_MUTATION, UPDATE_PROJECT_V2_SINGLE_SELECT_FIELD_MUTATION) and GET_PROJECT_STATUS_FIELD_QUERY to `solune/backend/src/services/github_projects/graphql.py`
- [x] T002 [P] Create template file service module with GENERIC_COPILOT_INSTRUCTIONS constant, `build_template_files()` function, path traversal/symlink validation, and startup caching in `solune/backend/src/services/template_files.py`
- [x] T003 [P] Create DB migration with ALTER TABLE for new columns and recreated CHECK constraint for new-repo type in `solune/backend/src/migrations/028_new_repo_support.sql`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend service methods and model extensions that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [P] Add `create_repository()` method to RepositoryMixin using GitHubKit REST (`async_create_for_authenticated_user` for personal, `async_create_in_org` for org, `auto_init=True`) returning `{id, node_id, name, full_name, html_url, default_branch}` in `solune/backend/src/services/github_projects/repository.py`
- [x] T005 Add `list_available_owners()` method to RepositoryMixin using REST `GET /user` + `GET /user/orgs` returning personal account + permitted orgs as `[{login, avatar_url, type}]` in `solune/backend/src/services/github_projects/repository.py`
- [x] T006 [P] Add `create_project_v2()` method to ProjectsMixin that fetches owner node_id, calls CREATE_PROJECT_V2_MUTATION, then best-effort configures Status field options (Backlog, In Progress, In Review, Done) via UPDATE_PROJECT_V2_SINGLE_SELECT_FIELD_MUTATION in `solune/backend/src/services/github_projects/projects.py`
- [x] T007 Add `link_project_to_repository()` method to ProjectsMixin using LINK_PROJECT_V2_TO_REPO_MUTATION in `solune/backend/src/services/github_projects/projects.py`
- [x] T008 [P] Extend `RepoType` enum with `NEW_REPO = "new-repo"` in `solune/backend/src/models/app.py`
- [x] T009 Extend `AppCreate` model with optional fields `repo_owner: str | None`, `repo_visibility: Literal["public", "private"]`, `create_project: bool` and make `branch` optional when `repo_type == "new-repo"` in `solune/backend/src/models/app.py`
- [x] T010 Extend `App` model with nullable fields `github_repo_url: str | None`, `github_project_url: str | None`, `github_project_id: str | None` in `solune/backend/src/models/app.py`
- [x] T011 [P] Extend TypeScript types: add `'new-repo'` to `RepoType` union, add `Owner` interface `{login, avatar_url, type}`, add `repo_owner`, `repo_visibility`, `create_project` to `AppCreate`, add `github_repo_url`, `github_project_url`, `github_project_id` to `App`, add `CreateProjectRequest` and `CreateProjectResponse` types in `solune/frontend/src/types/apps.ts`

**Checkpoint**: Foundation ready — all backend service methods, models, and types are in place for user story implementation

---

## Phase 3: User Story 1 — Create New App with New GitHub Repository (Priority: P1) 🎯 MVP

**Goal**: Users can create a new GitHub repo with template files + a linked Project V2 from the Apps page via "New Repository" mode in the app creation dialog

**Independent Test**: Open Apps page → click "New App" → select "New Repository" mode → fill in form → submit → verify new GitHub repo with template files and linked project board is created

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T012 [P] [US1] Unit tests for `create_repository()` (personal + org, auto_init, response shape) and `list_available_owners()` (user + orgs, empty orgs) in `solune/backend/tests/unit/test_github_repository.py`
- [x] T013 [P] [US1] Unit tests for `create_project_v2()` (happy path, status config failure is non-blocking) and `link_project_to_repository()` (happy path, idempotent) in `solune/backend/tests/unit/test_github_projects_create.py`
- [x] T014 [P] [US1] Unit tests for `build_template_files()` (file reading, copilot-instructions replacement with generic version, path traversal rejection, symlink rejection, caching) in `solune/backend/tests/unit/test_template_files.py`
- [x] T015 [P] [US1] Unit tests for `create_app_with_new_repo()` (happy path with project, happy path without project, repo failure → full failure, project failure after repo → partial success with null project fields) in `solune/backend/tests/unit/test_app_service_new_repo.py`

### Implementation for User Story 1

- [x] T016 [US1] Implement `create_app_with_new_repo()` orchestration in `solune/backend/src/services/app_service.py`: validate → create repo → poll for default branch → commit template files → optionally create project → link project → insert DB record with error tolerance (repo fail → fail, project fail → succeed with null project fields)
- [x] T017 [US1] Update `POST /apps` handler to route by `repo_type`: if `RepoType.NEW_REPO` → call `create_app_with_new_repo()`, else existing flow in `solune/backend/src/api/apps.py`
- [x] T018 [US1] Add `GET /apps/owners` endpoint that calls `list_available_owners()` and returns `[{login, avatar_url, type}]` in `solune/backend/src/api/apps.py`
- [x] T019 [P] [US1] Add `appsApi.owners()` method returning `Promise<Owner[]>` via `GET /apps/owners` in `solune/frontend/src/services/api.ts`
- [x] T020 [P] [US1] Add `useOwners()` hook with TanStack Query (30s stale time) in `solune/frontend/src/hooks/useApps.ts`
- [x] T021 [US1] Update "New App" create dialog with segmented control for repo type ("Same Repo" | "New Repository" | "External Repo") and conditional fields: New Repository mode shows owner dropdown, visibility toggle (default private), create-project checkbox (default on); Same Repo mode shows existing branch + project fields; External Repo mode shows URL field in `solune/frontend/src/pages/AppsPage.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently — users can create a new app with a new GitHub repository, template files, and a linked project board

---

## Phase 4: User Story 2 — Create Standalone GitHub Project V2 from Project Selector (Priority: P2)

**Goal**: Users can create a new GitHub Project V2 from the project selector dropdown anywhere in the app, with automatic selection after creation

**Independent Test**: Open project selector dropdown from any page → click "+ New Project" → fill in title and owner → submit → verify new project is created and auto-selected

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T022 [P] [US2] Unit tests for `create_standalone_project()` (happy path without repo link, happy path with repo link, project creation failure, linking failure is non-blocking) in `solune/backend/tests/unit/test_app_service_new_repo.py`

### Implementation for User Story 2

- [x] T023 [US2] Implement `create_standalone_project()` in `solune/backend/src/services/app_service.py`: takes `access_token, owner, title, repo_owner?, repo_name?` → calls `create_project_v2()` → optionally `link_project_to_repository()` → returns `{project_id, project_number, project_url}`
- [x] T024 [US2] Add `POST /projects/create` endpoint with request body `{title, owner, repo_owner?, repo_name?}` and response `{project_id, project_number, project_url}` (201 Created) in `solune/backend/src/api/projects.py`
- [x] T025 [P] [US2] Add `projectsApi.create()` method returning `Promise<CreateProjectResponse>` via `POST /projects/create` in `solune/frontend/src/services/api.ts`
- [x] T026 [P] [US2] Add `useCreateProject()` mutation hook that invalidates project list cache on success in `solune/frontend/src/hooks/useProjects.ts`
- [x] T027 [US2] Add "+ New Project" option at bottom of project list in ProjectSelector dropdown, opening a dialog with fields for project title (required), owner dropdown (from `useOwners()`), optional repo link; on success auto-select the new project in `solune/frontend/src/layout/ProjectSelector.tsx`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently — users can create standalone projects from the project selector

---

## Phase 5: User Story 3 — Same Repo Mode with Inline New Project (Priority: P3)

**Goal**: Users creating a new app in "Same Repo" mode can create a new project inline within the project selector field without leaving the dialog

**Independent Test**: Open "New App" → select "Same Repo" mode → click "+ New Project" in project selector → create project → verify project is created, linked to the repo, and selected for the app

### Implementation for User Story 3

- [x] T028 [US3] Add "+ New Project" inline option within the project selector field in Same Repo app creation flow, reusing the creation dialog from US2 (ProjectSelector) with the repo automatically pre-filled, in `solune/frontend/src/pages/AppsPage.tsx`

**Checkpoint**: Same Repo mode now supports inline project creation alongside existing project selection

---

## Phase 6: User Story 4 — Standalone "New Repository" Button on Apps Page (Priority: P3)

**Goal**: A dedicated "New Repository" button on the Apps page provides a shortcut to create a new repository without first selecting "New App"

**Independent Test**: Navigate to Apps page → click "New Repository" button → verify dialog opens pre-set to "New Repository" mode with identical behavior to Story 1

### Implementation for User Story 4

- [x] T029 [US4] Add standalone "New Repository" button on Apps page (next to existing "New App" button) that opens the create dialog pre-set to "New Repository" mode in `solune/frontend/src/pages/AppsPage.tsx`

**Checkpoint**: Apps page now has a dedicated shortcut for the most common creation action

---

## Phase 7: User Story 5 — View Repository and Project Details on App Cards (Priority: P3)

**Goal**: App cards and detail views display repo type badges and clickable links to GitHub repository and project URLs

**Independent Test**: Create apps with different repo types → verify AppCard shows correct badge ("Same Repo" / "New Repository" / "External Repo") and clickable links to GitHub repo/project URLs; verify AppDetailView shows links

### Implementation for User Story 5

- [x] T030 [P] [US5] Add repo type badge (styled by type: same-repo, new-repo, external-repo) and clickable links to `github_repo_url` and `github_project_url` (when available) to `solune/frontend/src/components/apps/AppCard.tsx`
- [x] T031 [P] [US5] Add clickable links to `github_repo_url` and `github_project_url` (when available) with labels to `solune/frontend/src/components/apps/AppDetailView.tsx`

**Checkpoint**: All app cards and detail views now surface GitHub resource links for easy navigation

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Docker configuration, integration testing, and final verification

- [x] T032 [P] Update Dockerfile to bundle template files via `COPY .github/ /app/templates/.github/`, `COPY .specify/ /app/templates/.specify/`, `COPY .gitignore /app/templates/.gitignore` and set `TEMPLATE_SOURCE_DIR=/app/templates` in `solune/backend/Dockerfile`
- [x] T033 [P] Integration test for end-to-end new-repo app creation flow (API call → DB state verification) in `solune/backend/tests/unit/test_app_service_new_repo.py`
- [x] T034 Run quickstart.md verification checklist: `pyright src` (0 errors), `ruff check src/` (clean), `pytest tests/ -x -q` (all pass), `npx tsc --noEmit` (no TS errors), `npx vitest run` (FE tests pass)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion — delivers MVP
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion — can run parallel with US1
- **User Story 3 (Phase 5)**: Depends on US1 (dialog) + US2 (project creation dialog) — sequential after both
- **User Story 4 (Phase 6)**: Depends on US1 (dialog with repo type selector) — sequential after US1
- **User Story 5 (Phase 7)**: Depends on Foundational (TypeScript types only) — can run parallel with US1/US2
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories; can run parallel with US1
- **User Story 3 (P3)**: Depends on US1 (dialog structure) + US2 (project creation dialog component)
- **User Story 4 (P3)**: Depends on US1 (dialog with repo type selector)
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) — No dependencies on other stories; can run parallel with US1/US2

### Within Each User Story

- Tests (included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Backend before frontend (API must exist before UI calls it)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Setup**: T002, T003 can run in parallel with T001 (different files)
- **Foundational**: T004 (repository.py) ‖ T006 (projects.py) ‖ T008 (app.py) ‖ T011 (apps.ts) — all different files
- **US1**: T012, T013, T014, T015 — all test files can run in parallel; T019 (api.ts) ‖ T020 (useApps.ts)
- **US2**: T025 (api.ts) ‖ T026 (useProjects.ts) — different files
- **US5**: T030 (AppCard.tsx) ‖ T031 (AppDetailView.tsx) — different files
- **Cross-story**: US1 ‖ US2 ‖ US5 can all start in parallel after Foundational phase
- **Polish**: T032 (Dockerfile) ‖ T033 (integration test) — different files

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together (write-first, must fail):
Task T012: "Unit tests for create_repository and list_available_owners in tests/unit/test_github_repository.py"
Task T013: "Unit tests for create_project_v2 and link_project_to_repository in tests/unit/test_github_projects_create.py"
Task T014: "Unit tests for template file reader in tests/unit/test_template_files.py"
Task T015: "Unit tests for create_app_with_new_repo in tests/unit/test_app_service_new_repo.py"

# Launch parallel frontend tasks:
Task T019: "Add appsApi.owners() in api.ts"
Task T020: "Add useOwners() hook in useApps.ts"
```

## Parallel Example: Cross-Story Parallelism

```bash
# After Foundational phase completes, three stories can start simultaneously:
Developer A: User Story 1 (T012–T021) — Backend service + frontend dialog
Developer B: User Story 2 (T022–T027) — Standalone project creation
Developer C: User Story 5 (T030–T031) — App card badges and links
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T011) — CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T012–T021)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Create a new app with "New Repository" mode
   - Verify GitHub repo has template files with generic copilot-instructions.md
   - Verify linked Project V2 has Solune default columns
   - Verify app record in DB has github_repo_url and github_project_url
5. Deploy/demo if ready — MVP delivers the primary value proposition

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (**MVP!**)
3. Add User Story 2 → Test independently → Deploy/Demo (standalone project creation)
4. Add User Story 5 → Test independently → Deploy/Demo (visual badges + links)
5. Add User Story 3 → Test independently → Deploy/Demo (inline project creation in Same Repo)
6. Add User Story 4 → Test independently → Deploy/Demo (New Repository shortcut button)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1 — new repo creation, MVP)
   - Developer B: User Story 2 (P2 — standalone project creation)
   - Developer C: User Story 5 (P3 — app card badges)
3. After US1 + US2 complete:
   - Developer A: User Story 3 (P3 — inline project in Same Repo)
   - Developer B: User Story 4 (P3 — New Repository button shortcut)
4. Stories complete and integrate independently

---

## Summary

| Metric | Value |
|---|---|
| **Total tasks** | 34 |
| **Setup tasks** | 3 (T001–T003) |
| **Foundational tasks** | 8 (T004–T011) |
| **US1 tasks** | 10 (T012–T021) |
| **US2 tasks** | 6 (T022–T027) |
| **US3 tasks** | 1 (T028) |
| **US4 tasks** | 1 (T029) |
| **US5 tasks** | 2 (T030–T031) |
| **Polish tasks** | 3 (T032–T034) |
| **Parallel opportunities** | 6 groups identified |
| **Suggested MVP scope** | Setup + Foundational + US1 (21 tasks) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests included per plan.md Phase 5 requirements — write and verify they fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- `copilot-instructions.md` must be the hardcoded generic version, not read from disk
- Project V2 status column configuration is best-effort — failure is non-blocking
- Error tolerance: repo failure → full fail; project failure after repo → partial success with null project fields
