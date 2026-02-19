# Tasks: SQLite-Backed Settings Storage

**Input**: Design documents from `/specs/006-sqlite-settings-storage/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/settings-api.yaml, quickstart.md

**Tests**: Not requested in the feature specification. Test tasks are omitted per Constitution Principle IV (Test Optionality).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new dependency, configure database path, update Docker, add constants

- [x] T001 [P] Add aiosqlite dependency to backend/pyproject.toml
- [x] T002 [P] Add DATABASE_PATH setting to backend/src/config.py
- [x] T003 [P] Add notification event type constants to backend/src/constants.py
- [x] T004 [P] Add named volume ghchat-data mounted at /app/data in docker-compose.yml

---

## Phase 2: Foundational — Database Init & Schema (US2)

**Purpose**: Core database infrastructure that MUST be complete before ANY user story can be implemented

**Covers User Story 2** — Database Initialization and Schema Management (P1)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Create migrations package at backend/src/migrations/__init__.py
- [x] T006 [P] Create initial SQL migration at backend/src/migrations/001_initial_schema.sql per data-model.md schema (all 5 tables: schema_version, user_sessions, user_preferences, project_settings, global_settings)
- [x] T007 Implement database module at backend/src/services/database.py — single persistent aiosqlite connection, WAL mode + busy_timeout + foreign_keys pragmas, migration runner (reads .sql files from migrations/, compares to schema_version, applies sequentially in transaction), INFO/ERROR logging per FR-040/FR-041. See research.md decisions 1, 3, 5
- [x] T008 [P] Create Settings Pydantic models at backend/src/models/settings.py — UserPreferences, GlobalSettings, ProjectSettings, EffectiveUserSettings, update request models per contracts/settings-api.yaml schemas and data-model.md columns
- [x] T009 Integrate database initialization into FastAPI lifespan at backend/src/main.py — call database init before yield, close connection after yield, store connection on app.state

**Checkpoint**: Database auto-creates on first startup, schema_version tracks version, all tables exist. US2 acceptance scenarios pass.

---

## Phase 3: User Story 1 — Persistent User Sessions (Priority: P1) 🎯 MVP

**Goal**: Sessions survive backend restarts. Users stay logged in across container recreation.

**Independent Test**: Log in, restart backend container, reload browser — user is still authenticated with same session data.

### Implementation for User Story 1

- [x] T010 [US1] Implement session store at backend/src/services/session_store.py — async CRUD: save_session (INSERT OR REPLACE), get_session (SELECT by session_id, reject if expired per FR-012), delete_session (DELETE by session_id), get_sessions_by_user (SELECT by github_user_id), purge_expired_sessions (DELETE WHERE updated_at + expiry < now, return count). Use model_dump()/model_validate() per research.md decision 2. DEBUG logging per FR-043
- [x] T011 [P] [US1] Refactor backend/src/services/github_auth.py — remove in-memory _sessions dict, replace all session reads/writes with session_store calls (get_session, save_session, delete_session). Import session_store and pass db connection from app.state. Keep GitHubAuthService OAuth flow unchanged
- [x] T012 [P] [US1] Add periodic session cleanup task to backend/src/main.py — use asyncio.create_task() in lifespan startup to spawn cleanup coroutine (while True / await asyncio.sleep(interval)), cancel on shutdown. Log cleanup summary at INFO per FR-042. See research.md decision 4

**Checkpoint**: User logs in → restart backend → reload browser → still authenticated. Session expiry and logout both remove from DB. MVP complete.

---

## Phase 4: User Story 10 + User Story 9 — Settings API & Global Settings (Priority: P2)

**Goal**: Backend API returns merged effective settings. Global defaults are seeded from env vars and editable.

**Independent Test**: Set global defaults, set user overrides for a subset, call GET /api/v1/settings/user — response contains merged result with user overrides on top of global defaults.

### Implementation for User Stories 10 & 9

- [x] T013 [US10] Implement settings store at backend/src/services/settings_store.py — async CRUD for user_preferences (get/upsert by github_user_id), global_settings (get singleton/update), project_settings (get/upsert by user+project). Implement merge logic: global → user → project per data-model.md merge algorithm. All fields resolved (no NULLs in output). DEBUG logging per FR-043
- [x] T014 [US9] Add global settings seeding logic to backend/src/services/database.py — after migrations complete, check if global_settings has 0 rows, if so INSERT defaults from Settings (config.py env vars: AI_PROVIDER, COPILOT_MODEL, DEFAULT_REPOSITORY, DEFAULT_ASSIGNEE, COPILOT_POLLING_INTERVAL). Log seeding at INFO. Per FR-020/FR-021: only seed on first startup, never overwrite existing
- [x] T015 [US10] Create settings API endpoints at backend/src/api/settings.py — 6 endpoints per contracts/settings-api.yaml: GET/PUT /settings/user, GET/PUT /settings/global, GET/PUT /settings/project/{project_id}. All require authentication via get_current_session dependency. PUT endpoints accept partial updates. Return EffectiveUserSettings/GlobalSettings/EffectiveProjectSettings response models
- [x] T016 [US10] Register settings router in backend/src/api/__init__.py — add settings router with prefix /settings alongside existing routers
- [x] T017 [P] [US10] Add TypeScript settings types to frontend/src/types/index.ts — EffectiveUserSettings, UserPreferencesUpdate, GlobalSettings, GlobalSettingsUpdate, EffectiveProjectSettings, ProjectSettingsUpdate, AIPreferences, DisplayPreferences, WorkflowDefaults, NotificationPreferences per contracts/settings-api.yaml schemas
- [x] T018 [P] [US10] Add settingsApi methods to frontend/src/services/api.ts — getUserSettings(), updateUserSettings(), getGlobalSettings(), updateGlobalSettings(), getProjectSettings(projectId), updateProjectSettings(projectId) matching the 6 API endpoints

**Checkpoint**: curl GET /api/v1/settings/user returns merged settings. PUT updates persist. Global settings seeded from env vars on first startup.

---

## Phase 5: User Story 4 + User Story 3 — Settings Page & AI Preferences (Priority: P2)

**Goal**: Users can navigate to a Settings page and configure their AI preferences.

**Independent Test**: Log in, click Settings nav link, change AI provider and model, save, send a chat message — system uses selected model. Restart server — preferences retained.

### Implementation for User Stories 4 & 3

- [x] T019 [P] [US4] Create SettingsSection base component at frontend/src/components/settings/SettingsSection.tsx — reusable collapsible section wrapper with title, description, children slot, save button, loading/success/error states
- [x] T020 [P] [US3] Create AIPreferences component at frontend/src/components/settings/AIPreferences.tsx — form fields for provider (select: copilot/azure_openai), model (text input), temperature (range slider 0.0–2.0). Uses SettingsSection wrapper. Calls updateUserSettings({ ai: {...} }) on save
- [x] T021 [P] [US9] Create GlobalSettings component at frontend/src/components/settings/GlobalSettings.tsx — form for all global settings fields (AI, display, workflow, notifications, allowed_models). Uses getGlobalSettings()/updateGlobalSettings() API methods
- [x] T022 [US4] Implement useSettings hook at frontend/src/hooks/useSettings.ts — TanStack Query useQuery for getUserSettings (cache key: ['settings', 'user']), useMutation for updateUserSettings with optimistic updates and cache invalidation. Similar queries for global and project settings
- [x] T023 [US4] Create SettingsPage layout at frontend/src/pages/SettingsPage.tsx — renders sections: AIPreferences, DisplayPreferences (placeholder), WorkflowDefaults (placeholder), NotificationPreferences (placeholder), ProjectSettings (placeholder), GlobalSettings. Passes useSettings data. Section placeholders render "Coming soon" until their components are built
- [x] T024 [US4] Add 'settings' to activeView union type and header nav link in frontend/src/App.tsx — add Settings alongside Chat and Project Board tabs, render SettingsPage when activeView === 'settings'

**Checkpoint**: Settings page accessible via nav. AI preferences editable and saved. Global settings section visible and editable.

---

## Phase 6: User Story 5 — UI/Display Preferences (Priority: P2)

**Goal**: Theme and default view preferences are API-backed and persist across sessions/devices. Header theme toggle syncs bidirectionally.

**Independent Test**: Set theme to dark and default view to board in Settings, log out, log back in — app loads in dark mode on board view.

### Implementation for User Story 5

- [x] T025 [US5] Create DisplayPreferences component at frontend/src/components/settings/DisplayPreferences.tsx — form fields: theme (select: light/dark), default_view (select: chat/board/settings), sidebar_collapsed (toggle). Uses SettingsSection wrapper. Calls updateUserSettings({ display: {...} }) on save
- [x] T026 [US5] Modify frontend/src/hooks/useAppTheme.ts for bidirectional settings API sync — when authenticated: read theme from useSettings, write theme changes to both API and localStorage. When unauthenticated: fall back to localStorage only (FR-038). Header toggle triggers API save (FR-035)
- [x] T027 [US5] Apply default_view preference on login in frontend/src/App.tsx — after authentication, read user's default_view from settings and set as initial activeView. Fall back to 'chat' if no preference set (FR-014)

**Checkpoint**: Theme toggle in header saves to API. Settings page DisplayPreferences section works. Default view applied on login.

---

## Phase 7: User Story 6 + User Story 7 — Workflow & Notification Preferences (Priority: P3)

**Goal**: Users configure default repository, assignee, polling interval, and per-event notification toggles.

**Independent Test (US6)**: Set default repository in Settings, create a task via chat without specifying repo — task created in default repo.

**Independent Test (US7)**: Disable task_status_change notifications, trigger a status change — no notification. Enable agent_completion — notification arrives.

### Implementation for User Stories 6 & 7

- [x] T028 [P] [US6] Create WorkflowDefaults component at frontend/src/components/settings/WorkflowDefaults.tsx — form fields: default_repository (text input), default_assignee (text input), copilot_polling_interval (number input, min 0). Uses SettingsSection wrapper. Calls updateUserSettings({ workflow: {...} }) on save
- [x] T029 [P] [US7] Create NotificationPreferences component at frontend/src/components/settings/NotificationPreferences.tsx — four toggle switches for task_status_change, agent_completion, new_recommendation, chat_mention. Uses SettingsSection wrapper. Calls updateUserSettings({ notifications: {...} }) on save
- [x] T030 [P] [US4] Add unsaved changes warning to frontend/src/pages/SettingsPage.tsx — track dirty state across all sections, prompt user on navigation away (beforeunload event + in-app navigation guard) per FR-037

**Checkpoint**: All preference sections functional. Unsaved changes warning active.

---

## Phase 8: User Story 8 — Project-Level Settings (Priority: P3)

**Goal**: Per-project board config and agent pipeline mappings, scoped to user + project.

**Independent Test**: Select Project A, configure board display prefs, switch to Project B with different settings — each project retains its own config.

### Implementation for User Story 8

- [x] T031 [US8] Create ProjectSettings component at frontend/src/components/settings/ProjectSettings.tsx — project selector dropdown (from user's projects), board_display_config editor (column order, collapsed columns, show_estimates), agent_pipeline_mappings editor (status → agent list). Uses getProjectSettings()/updateProjectSettings() API methods
- [x] T032 [US8] Replace ProjectSettings placeholder in frontend/src/pages/SettingsPage.tsx — import and render ProjectSettings component, pass current selected project ID from session context

**Checkpoint**: Project-specific settings editable per project. Different projects show their own configs.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Observability, code quality, end-to-end validation

- [x] T033 [P] Add DEBUG-level logging for individual DB read/write operations across backend/src/services/session_store.py and backend/src/services/settings_store.py per FR-043
- [x] T034 [P] Run linting (ruff for backend, eslint for frontend) and verify no type errors (pyright/mypy, tsc --noEmit)
- [x] T035 Run quickstart.md end-to-end validation — execute all quickstart steps (docker compose up, verify logs, login, session persistence, settings page, API curl tests, container recreation)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 Sessions (Phase 3)**: Depends on Phase 2 (database module, tables exist)
- **US10+US9 Settings API (Phase 4)**: Depends on Phase 2 (database module, models). Independent of Phase 3
- **US4+US3 Settings Page (Phase 5)**: Depends on Phase 4 (API endpoints, frontend types/api client)
- **US5 Display Prefs (Phase 6)**: Depends on Phase 5 (Settings page, useSettings hook)
- **US6+US7 Workflow & Notifications (Phase 7)**: Depends on Phase 5 (Settings page, useSettings hook). Independent of Phase 6
- **US8 Project Settings (Phase 8)**: Depends on Phase 5 (Settings page). Independent of Phase 6/7
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Phase 2 only — fully independent of all other stories
- **US2 (P1)**: No story dependencies — IS the foundational phase
- **US10+US9 (P2)**: Phase 2 only — fully independent of US1
- **US4+US3 (P2)**: Depends on US10+US9 (needs backend API)
- **US5 (P2)**: Depends on US4 (needs Settings page and useSettings hook)
- **US6 (P3)**: Depends on US4 (needs Settings page)
- **US7 (P3)**: Depends on US4 (needs Settings page)
- **US8 (P3)**: Depends on US4 (needs Settings page) + US10 (needs project API)
- **US9 frontend**: Included in Phase 5 (GlobalSettings.tsx)

### Within Each User Story

- Models before services
- Services before API endpoints
- API endpoints before frontend consumers
- Base components before composite pages
- Core implementation before integration

### Parallel Opportunities

**Phase 1**: All 4 tasks (T001–T004) are [P] — different files, fully parallel

**Phase 2**: T005+T006+T008 are [P] (migrations package, SQL file, Pydantic models). T007 depends on T006. T009 depends on T007

**Phase 3**: T011+T012 are [P] after T010 (both consume session_store, modify different files)

**Phase 4**: T017+T018 (frontend) are [P] alongside T013–T016 (backend) — independent codebases

**Phase 5**: T019+T020+T021+T022 are all [P] (separate component/hook files). T023 depends on them. T024 depends on T023

**Phase 7**: T028+T029+T030 are all [P] (separate files)

**Cross-phase**: Phase 3 (US1) and Phase 4 (US10+US9) can run in parallel after Phase 2 — they share no files

---

## Parallel Example: After Phase 2 Completes

```
Track A (Sessions — US1):          Track B (Settings API — US10+US9):
  T010: session_store.py             T013: settings_store.py
  T011: github_auth.py  ─┐           T014: database.py seeding
  T012: main.py cleanup  ─┘(P)       T015: api/settings.py
                                      T016: api/__init__.py
                                      T017: types/index.ts   ─┐
                                      T018: api.ts            ─┘(P with backend)
```

## Parallel Example: Phase 5 Component Sprint

```
All [P] — launch together:
  T019: SettingsSection.tsx
  T020: AIPreferences.tsx
  T021: GlobalSettings.tsx
  T022: useSettings.ts

Then sequential:
  T023: SettingsPage.tsx (imports T019–T022)
  T024: App.tsx (renders T023)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (4 tasks)
2. Complete Phase 2: Foundational / US2 (5 tasks)
3. Complete Phase 3: US1 — Persistent Sessions (3 tasks)
4. **STOP and VALIDATE**: Restart backend, confirm sessions survive. MVP achieved — core pain point solved

### Incremental Delivery

1. Setup + Foundational → Database operational (Phases 1–2)
2. Add US1 → Sessions persist → **MVP** (Phase 3)
3. Add US10+US9 → Settings API available, global defaults seeded (Phase 4)
4. Add US4+US3 → Settings page live, AI prefs editable (Phase 5)
5. Add US5 → Theme/view prefs API-backed (Phase 6)
6. Add US6+US7 → Workflow & notification prefs (Phase 7)
7. Add US8 → Project-level settings (Phase 8)
8. Polish → Logging, lint, quickstart validation (Phase 9)

Each phase adds value without breaking previous work. Stories are independently testable at each checkpoint.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks within the same phase
- [Story] label maps task to specific user story for traceability
- Backend uses raw aiosqlite (no ORM) — see research.md decision 6
- Pydantic model_dump()/model_validate() for all DB ↔ model conversion — see research.md decision 2
- Settings merge is server-side only — frontend receives fully-resolved objects
- InMemoryCache (cache.py) is NOT modified — it continues serving API response caching
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
