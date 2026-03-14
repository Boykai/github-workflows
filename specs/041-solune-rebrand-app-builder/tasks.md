# Tasks: Solune Rebrand & App Builder Architecture

**Input**: Design documents from `/specs/041-solune-rebrand-app-builder/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly mandated for all stories. Test tasks are included only where the plan/spec explicitly calls for them (app service unit tests, guard tests, frontend build verification).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Post-restructure**: `solune/backend/`, `solune/frontend/` for platform code
- **Pre-restructure tasks (Phase 1-2)**: Reference current paths (`backend/`, `frontend/`) since restructure is part of the work
- **Apps directory**: `apps/` at repository root
- **Root files**: `README.md`, `docker-compose.yml` at repository root

---

## Phase 1: Setup (Monorepo Infrastructure)

**Purpose**: Archive current state and establish the monorepo directory structure that all other phases depend on.

- [ ] T001 Tag current repository state as `pre-solune-archive` for recovery per FR-001
- [ ] T002 Create `solune/` directory at repository root and move all source directories (`backend/`, `frontend/`, `docs/`, `scripts/`, `specs/`) into it using `git mv`
- [ ] T003 Move remaining top-level configuration files (`docker-compose.yml`, `CHANGELOG.md`, `mcp.json`, `.env.example`, `.pre-commit-config.yaml`, `.markdownlint.json`, `.markdown-link-check.json`, `.dockerignore`, `.cgcignore`, `tasks.md`) into `solune/` using `git mv`
- [ ] T004 Create `apps/` directory at repository root with `apps/.gitkeep` per FR-003
- [ ] T005 Ensure `.github/` directory remains at repository root (already correct location) per FR-004
- [ ] T006 Create root-level `README.md` with Solune platform overview placeholder per FR-005
- [ ] T007 Create root-level `docker-compose.yml` that orchestrates the entire monorepo with build contexts referencing `./solune/backend`, `./solune/frontend` per FR-005

---

## Phase 2: Foundational (Path Updates & Build Verification)

**Purpose**: Update all internal path references to reflect the new monorepo structure. MUST complete before any user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete — the project must build and pass tests from the new structure.

- [ ] T008 [P] Update `solune/docker-compose.yml` build contexts and volume paths to use relative paths within `solune/` per FR-006
- [ ] T009 [P] Update `.github/workflows/ci.yml` working directory references to `solune/backend` and `solune/frontend` per FR-006
- [ ] T010 [P] Update `.vscode/mcp.json` and `solune/mcp.json` tool paths to reflect new directory structure per FR-006
- [ ] T011 [P] Update `.devcontainer/` configuration paths to reference `solune/` subdirectory per FR-006
- [ ] T012 [P] Update all script files in `solune/scripts/` to reference new relative paths per FR-006
- [ ] T013 Verify the entire project builds from the new monorepo structure: `cd solune && docker compose build` per SC-001
- [ ] T014 Verify all existing backend tests pass: `cd solune/backend && python -m pytest tests/ -v` per SC-001
- [ ] T015 Verify all existing frontend tests pass: `cd solune/frontend && npx vitest run` and `npm run build` per SC-001

**Checkpoint**: Monorepo structure is valid — project builds and all tests pass from new paths.

---

## Phase 3: User Story 1 — Monorepo Restructure and Archive (Priority: P1) 🎯 MVP

**Goal**: Complete the monorepo restructure so the repository root contains exactly: `solune/`, `apps/`, `.github/`, root `README.md`, and root `docker-compose.yml`.

**Independent Test**: Verify the archive tag exists, `apps/` directory is present with `.gitkeep`, all source files reside under `solune/`, and all existing tests pass from the new directory structure (SC-001, SC-002).

### Implementation for User Story 1

- [ ] T016 [US1] Validate repository root contains exactly: `solune/`, `apps/`, `.github/`, `README.md`, `docker-compose.yml`, and standard dotfiles — remove any stray files
- [ ] T017 [US1] Verify root-level `docker-compose.yml` can orchestrate all services with `docker compose config` from repository root
- [ ] T018 [US1] Verify `pre-solune-archive` tag exists and can be checked out for recovery
- [ ] T019 [US1] Run full CI pipeline equivalent locally to confirm zero regressions: backend tests, frontend tests, build, and lint per SC-001 and SC-002

**Checkpoint**: User Story 1 complete — monorepo structure is valid and verified.

---

## Phase 4: User Story 2 — Full Product Rebrand to Solune (Priority: P1)

**Goal**: Replace all occurrences of old product names and identifiers with Solune equivalents across ~70+ files, rewrite README and developer documentation, update all frontend branding.

**Independent Test**: Case-insensitive search for old brand strings ("Agent Projects", "ghchat-", "GitHub Workflows Chat", "github-workflows" as product name) returns zero matches. Application launches with correct branding on all visible pages (SC-003, SC-004).

### Implementation for User Story 2

- [ ] T020 [P] [US2] Replace `agent-projects-backend` → `solune-backend` in `solune/backend/pyproject.toml` per FR-007
- [ ] T021 [P] [US2] Replace `agent-projects-frontend` → `solune-frontend` in `solune/frontend/package.json` per FR-007
- [ ] T022 [P] [US2] Replace `ghchat-backend` → `solune-backend`, `ghchat-frontend` → `solune-frontend`, `ghchat-signal-api` → `solune-signal-api` in `solune/docker-compose.yml` per FR-007
- [ ] T023 [P] [US2] Replace `ghchat-network` → `solune-network`, `ghchat-data` → `solune-data` in `solune/docker-compose.yml` and root `docker-compose.yml` per FR-007
- [ ] T024 [P] [US2] Replace `/var/lib/ghchat/data` → `/var/lib/solune/data` in `solune/docker-compose.yml`, backend config files, and `.env.example` per FR-007
- [ ] T025 [P] [US2] Replace `Agent Projects` → `Solune` across all `*.md`, `*.tsx`, `*.ts`, `*.py`, `*.yml` files per FR-007
- [ ] T026 [P] [US2] Replace `GitHub Workflows Chat` → `Solune` in `.github/agents/copilot-instructions.md` per FR-007
- [ ] T027 [P] [US2] Replace `github-workflows` (product name context) → `solune` in documentation, badges, and internal links per FR-007
- [ ] T028 [P] [US2] Update `AppPage.tsx` heading/hero text to display "Solune" in `solune/frontend/src/pages/AppPage.tsx` per FR-008
- [ ] T029 [P] [US2] Update `LoginPage.tsx` branding to display "Solune" in `solune/frontend/src/pages/LoginPage.tsx` per FR-008
- [ ] T030 [P] [US2] Update `Sidebar.tsx` brand mark to display "Solune" in `solune/frontend/src/components/Sidebar.tsx` per FR-008
- [ ] T031 [US2] Rewrite root `README.md` with Solune product pitch: "Agent-driven development platform" with updated feature descriptions and badges per FR-009
- [ ] T032 [US2] Rewrite `.github/agents/copilot-instructions.md` with new monorepo structure, Solune platform role, agent operation on `apps/` subdirectories, and `@admin`/`@adminlock` routing model per FR-010
- [ ] T033 [US2] Run comprehensive search for old brand strings and eliminate any remaining occurrences per FR-011 and SC-003: `grep -ri "Agent Projects\|ghchat-\|GitHub Workflows Chat" solune/ --include="*.py" --include="*.ts" --include="*.tsx" --include="*.yml" --include="*.yaml" --include="*.json" --include="*.md" --include="*.html" --include="*.sh" --include="*.toml" --include="*.cfg" --include="*.env*"`
- [ ] T034 [US2] Verify frontend builds successfully and branding displays correctly: `cd solune/frontend && npm run build && npm run type-check` per SC-004

**Checkpoint**: User Story 2 complete — zero old brand strings, all pages show "Solune" branding.

---

## Phase 5: User Story 3 — App Management and Lifecycle (Priority: P2)

**Goal**: Implement the complete backend for application CRUD operations, lifecycle management, directory scaffolding, and path validation.

**Independent Test**: Create an application via API, verify scaffolded directory exists under `apps/<app-name>/`, cycle through start/stop/delete, confirm each status transition and final cleanup (SC-005, SC-006, SC-011).

### Implementation for User Story 3

- [ ] T035 [P] [US3] Create database migration `solune/backend/src/migrations/024_apps.sql` with `apps` table schema, indexes, and `updated_at` trigger per data-model.md
- [ ] T036 [P] [US3] Create Pydantic models (`App`, `AppCreate`, `AppUpdate`, `AppStatusResponse`, `AppStatus`, `RepoType`) in `solune/backend/src/models/app.py` per data-model.md
- [ ] T037 [US3] Create app service in `solune/backend/src/services/app_service.py` with `create_app()` including name validation, reserved-name rejection, directory scaffolding under `apps/<app-name>/`, and database insertion per FR-013, FR-014, FR-015
- [ ] T038 [US3] Implement `list_apps()`, `get_app()`, and `update_app()` methods in `solune/backend/src/services/app_service.py` per FR-013
- [ ] T039 [US3] Implement `start_app()` and `stop_app()` with valid state transition enforcement in `solune/backend/src/services/app_service.py` per FR-017
- [ ] T040 [US3] Implement `delete_app()` with active-app rejection (must stop first), directory cleanup, and database removal in `solune/backend/src/services/app_service.py` per FR-017, FR-018
- [ ] T041 [US3] Implement app scaffold template generation (README.md, config.json, src/.gitkeep, CHANGELOG.md, docker-compose.yml) in `solune/backend/src/services/app_service.py` per FR-015 and data-model.md scaffold template
- [ ] T042 [US3] Create API routes in `solune/backend/src/api/apps.py`: GET /api/v1/apps (list with optional status filter), POST /api/v1/apps (create), GET /api/v1/apps/{app_name} (detail) per contracts/apps-api.md
- [ ] T043 [US3] Add API routes in `solune/backend/src/api/apps.py`: PUT /api/v1/apps/{app_name} (update), DELETE /api/v1/apps/{app_name} (delete) per contracts/apps-api.md
- [ ] T044 [US3] Add API routes in `solune/backend/src/api/apps.py`: POST /api/v1/apps/{app_name}/start, POST /api/v1/apps/{app_name}/stop, GET /api/v1/apps/{app_name}/status per contracts/apps-api.md
- [ ] T045 [US3] Register apps router in `solune/backend/src/main.py`: `app.include_router(apps_router, prefix="/api/v1/apps", tags=["apps"])`
- [ ] T046 [US3] Add path validation and sanitization utility (alphanumeric + hyphens only, no traversal, no reserved names) in `solune/backend/src/services/app_service.py` per FR-014 and SC-011
- [ ] T047 [US3] Verify app service with backend linting and type checking: `cd solune/backend && python -m ruff check src/api/apps.py src/models/app.py src/services/app_service.py && python -m pyright src/models/app.py src/services/app_service.py`

**Checkpoint**: User Story 3 complete — full app CRUD + lifecycle works via API, scaffolding creates valid directory structures, name validation rejects all invalid inputs.

---

## Phase 6: User Story 4 — Apps Page with Live Preview (Priority: P2)

**Goal**: Build the frontend Apps page with card-based app listing, detail view with embedded live preview iframe, and start/stop controls.

**Independent Test**: Navigate to `/apps`, verify cards render for multiple apps in various states, open detail view for a running app, confirm preview frame loads and start/stop controls update status (SC-007, SC-008).

### Implementation for User Story 4

- [ ] T048 [P] [US4] Create TypeScript types (`App`, `AppCreate`, `AppUpdate`, `AppStatusResponse`, `AppStatus`, `RepoType`) in `solune/frontend/src/types/apps.ts` per data-model.md
- [ ] T049 [P] [US4] Create API client with functions for all app endpoints (list, create, get, update, delete, start, stop, status) in `solune/frontend/src/services/appsApi.ts` per contracts/apps-api.md
- [ ] T050 [US4] Create TanStack Query hooks (`useApps`, `useApp`, `useCreateApp`, `useUpdateApp`, `useDeleteApp`, `useStartApp`, `useStopApp`) in `solune/frontend/src/hooks/useApps.ts`
- [ ] T051 [P] [US4] Create `AppCard` component with name, description, status badge (creating=blue, active=green, stopped=gray, error=red), and action buttons in `solune/frontend/src/components/apps/AppCard.tsx` per FR-019, FR-021
- [ ] T052 [P] [US4] Create `AppPreview` component with iframe wrapper for live app preview (src=`http://localhost:{port}`), `sandbox` attribute for XSS/clickjacking protection, loading state, and offline/error state fallback in `solune/frontend/src/components/apps/AppPreview.tsx` per FR-022
- [ ] T053 [US4] Create `AppDetailView` component with app info, embedded `AppPreview`, and start/stop/delete controls in `solune/frontend/src/components/apps/AppDetailView.tsx` per FR-020
- [ ] T054 [US4] Create `AppsPage` component with card grid layout, create-app dialog, and navigation to detail view in `solune/frontend/src/pages/AppsPage.tsx` per FR-019
- [ ] T055 [US4] Add routes `/apps` and `/apps/:appName` in `solune/frontend/src/App.tsx` (or main router file) following existing route patterns per research.md R10
- [ ] T056 [US4] Add "Apps" navigation link to `solune/frontend/src/components/Sidebar.tsx` per FR-019
- [ ] T057 [US4] Verify frontend builds and type-checks: `cd solune/frontend && npm run build && npm run type-check && npx vitest run`

**Checkpoint**: User Story 4 complete — Apps page renders cards, detail view shows preview, start/stop controls work.

---

## Phase 7: User Story 5 — Slash Command Context Switching (Priority: P3)

**Goal**: Enable `/<app-name>` chat commands to switch the active working context, display a context indicator, and route agent operations to the correct app directory.

**Independent Test**: Create two apps, type `/<app-name>` in chat, verify context indicator changes, confirm subsequent agent operations target the correct application directory (SC-009).

### Implementation for User Story 5

- [ ] T058 [P] [US5] Add `active_app_name` session attribute to the session model/storage in `solune/backend/src/` (extend existing session handling) per data-model.md App Context entity
- [ ] T059 [US5] Create context switch endpoint `POST /api/v1/chat/context` in `solune/backend/src/api/chat.py` (or new file) that validates app existence, updates session `active_app_name`, and returns confirmation per contracts/slash-commands.md
- [ ] T060 [US5] Implement `resolve_working_directory(session)` utility that returns `apps/<app-name>` when context is set, or `solune` for platform context, in `solune/backend/src/services/app_service.py` per contracts/slash-commands.md
- [ ] T061 [US5] Integrate working directory resolution into agent operation routing layer so file operations use the active app context path
- [ ] T062 [P] [US5] Extend frontend chat input component to detect `/` prefix and provide autocomplete suggestions from the apps list in `solune/frontend/src/` (extend existing command autocomplete) per contracts/slash-commands.md
- [ ] T063 [P] [US5] Add context indicator component to the chat header showing the currently active app name and status in `solune/frontend/src/` per FR-024
- [ ] T064 [US5] Create frontend API call for context switch endpoint and integrate with chat input submission flow in `solune/frontend/src/services/appsApi.ts` per contracts/slash-commands.md
- [ ] T065 [US5] Handle `/platform` command to clear context (set `active_app_name` to null) and update indicator per contracts/slash-commands.md
- [ ] T066 [US5] Ensure conversation history remains visible across context switches — context switch recorded as system message per FR-026

**Checkpoint**: User Story 5 complete — `/<app-name>` switches context, indicator updates, agent operations target correct directory.

---

## Phase 8: User Story 6 — Admin Guard for Self-Editing Protection (Priority: P3)

**Goal**: Implement `@admin` and `@adminlock` guard mechanisms that protect platform core files from agent modifications during app-building operations.

**Independent Test**: Configure protected paths, attempt agent operations targeting `solune/` (should be blocked), attempt operations targeting `apps/` (should proceed), verify correct enforcement per SC-010.

### Implementation for User Story 6

- [ ] T067 [P] [US6] Create guard configuration file `solune/guard-config.yml` with default rules: `solune/**` → admin, `.github/**` → adminlock, `apps/**` → none per contracts/admin-guard.md
- [ ] T068 [P] [US6] Create `GuardResult` Pydantic model (allowed, admin_blocked, locked lists) in `solune/backend/src/models/` per contracts/admin-guard.md
- [ ] T069 [US6] Create guard service in `solune/backend/src/services/guard_service.py` with `check_guard(file_paths)` that evaluates paths against config rules using most-specific-match-wins logic per FR-027, FR-028, FR-029, FR-030
- [ ] T070 [US6] Implement guard configuration loader that reads `guard-config.yml` and supports hot-reload without restart in `solune/backend/src/services/guard_service.py`
- [ ] T071 [US6] Create guard middleware in `solune/backend/src/middleware/admin_guard.py` that intercepts agent file operations and returns 403 with explanation for blocked/locked paths per contracts/admin-guard.md
- [ ] T072 [US6] Integrate guard middleware into agent operation routing layer — evaluate each target file path before allowing file system access
- [ ] T073 [US6] Implement per-file evaluation for mixed-path operations: block only protected paths, allow app paths through per FR-030
- [ ] T074 [US6] Add elevation override mechanism for `@admin` paths: accept an elevation flag that bypasses admin (but not adminlock) blocks per contracts/admin-guard.md

**Checkpoint**: User Story 6 complete — guards block `solune/` and `.github/` modifications, allow `apps/` freely.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation.

- [ ] T075 [P] Update `solune/docs/` with new architecture documentation reflecting monorepo structure and app management features
- [ ] T076 [P] Update `CHANGELOG.md` in `solune/` with rebrand and app builder architecture changes
- [ ] T077 Run full end-to-end verification per quickstart.md: `docker compose up` from repo root starts all services
- [ ] T078 Verify zero old-brand strings remain across entire repository per SC-003
- [ ] T079 Verify Apps page accessible at `/apps` and full CRUD lifecycle works per SC-006, SC-007
- [ ] T080 Verify `/<app-name>` command switches context correctly per SC-009
- [ ] T081 Verify guard blocks `solune/` modifications and allows `apps/` modifications per SC-010
- [ ] T082 Run full backend test suite: `cd solune/backend && python -m pytest tests/ -v`
- [ ] T083 Run full frontend test suite: `cd solune/frontend && npx vitest run && npm run build && npm run type-check`
- [ ] T084 Run backend linting: `cd solune/backend && python -m ruff check src/`
- [ ] T085 Run frontend linting: `cd solune/frontend && npm run lint`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (path updates must be valid before any feature work)
- **User Story 1 (Phase 3)**: Depends on Foundational — validates the monorepo structure
- **User Story 2 (Phase 4)**: Depends on Foundational — can run in parallel with US1 (rebrand targets new paths)
- **User Story 3 (Phase 5)**: Depends on US1 completion (needs `apps/` directory and valid monorepo) — can run in parallel with US2
- **User Story 4 (Phase 6)**: Depends on US3 (needs app management API)
- **User Story 5 (Phase 7)**: Depends on US3 (needs app data for context switching)
- **User Story 6 (Phase 8)**: Depends on US1 (needs monorepo structure for path-based guards)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Independent of US1 but ideally lands alongside it
- **User Story 3 (P2)**: Depends on US1 for `apps/` directory — Independent of US2
- **User Story 4 (P2)**: Depends on US3 for app management API — Can use mock data during US3 development
- **User Story 5 (P3)**: Depends on US3 for app data — Independent of US4 and US6
- **User Story 6 (P3)**: Depends on US1 for monorepo path structure — Independent of US3, US4, US5

### Within Each User Story

- Models/migrations before services
- Services before API routes
- API routes before frontend integration
- Types before API clients before hooks before components before pages
- Core implementation before integration and verification

### Parallel Opportunities

- **Phase 2**: All path update tasks (T008–T012) can run in parallel — they target different files
- **Phase 4 (US2)**: All string replacement tasks (T020–T030) can run in parallel — independent files
- **Phase 5 (US3)**: T035 (migration) and T036 (models) can run in parallel, then T037–T041 (service) sequentially
- **Phase 6 (US4)**: T048 (types) and T049 (API client) can run in parallel, then T051 and T052 (components) in parallel
- **Phase 7 (US5)**: T058 (session model) and T062, T063 (frontend components) can run in parallel
- **Phase 8 (US6)**: T067 (config) and T068 (model) can run in parallel
- **Cross-story**: US1 and US2 can be worked on in parallel. US5 and US6 can be worked on in parallel (both depend on US3/US1 respectively)

---

## Parallel Example: User Story 3 (App Management)

```bash
# Launch migration and model creation in parallel:
Task T035: "Create migration 024_apps.sql in solune/backend/src/migrations/"
Task T036: "Create Pydantic models in solune/backend/src/models/app.py"

# Then service implementation (sequential — depends on models):
Task T037: "Create app service create_app() in solune/backend/src/services/app_service.py"
Task T038: "Implement list/get/update in solune/backend/src/services/app_service.py"
Task T039: "Implement start/stop in solune/backend/src/services/app_service.py"

# Then API routes (sequential — depends on service):
Task T042: "Create CRUD routes in solune/backend/src/api/apps.py"
Task T043: "Add update/delete routes in solune/backend/src/api/apps.py"
Task T044: "Add lifecycle routes in solune/backend/src/api/apps.py"
```

## Parallel Example: User Story 4 (Apps Page)

```bash
# Launch types and API client in parallel:
Task T048: "Create TypeScript types in solune/frontend/src/types/apps.ts"
Task T049: "Create API client in solune/frontend/src/services/appsApi.ts"

# Launch card and preview components in parallel (after hooks):
Task T051: "Create AppCard in solune/frontend/src/components/apps/AppCard.tsx"
Task T052: "Create AppPreview in solune/frontend/src/components/apps/AppPreview.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (archive + directory structure)
2. Complete Phase 2: Foundational (path updates + build verification)
3. Complete Phase 3: User Story 1 (monorepo validation)
4. Complete Phase 4: User Story 2 (rebrand)
5. **STOP and VALIDATE**: Monorepo works, all branding is Solune, tests pass
6. Deploy/demo if ready — this is a clean, rebranded foundation

### Incremental Delivery

1. Complete Setup + Foundational → Monorepo ready
2. Add User Story 1 + User Story 2 → Rebranded monorepo (MVP!)
3. Add User Story 3 → App management API functional → Test independently
4. Add User Story 4 → Apps page with preview → Test independently
5. Add User Story 5 → Context switching → Test independently
6. Add User Story 6 → Guard protection → Test independently
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (monorepo validation) + User Story 3 (app backend)
   - Developer B: User Story 2 (rebrand) + User Story 4 (apps page, after US3 API is ready)
   - Developer C: User Story 6 (admin guard, after US1)
3. After US3 completes:
   - Developer C picks up: User Story 5 (context switching)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Tests are included only where plan.md/spec.md explicitly calls for them (backend lint/type-check, build verification)
- Total tasks: 85 (T001–T085)
