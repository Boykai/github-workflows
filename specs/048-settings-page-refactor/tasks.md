# Tasks: Settings Page Refactor with Secrets

**Input**: Design documents from `/specs/048-settings-page-refactor/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are REQUIRED by the feature specification (FR-035, Verification steps 1–3, and SC-005). Backend and frontend tests are included in user story phases.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `solune/backend/src/`, `solune/backend/tests/`
- **Frontend**: `solune/frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new dependency and prepare project for secrets feature

- [ ] T001 Add `pynacl` dependency to `solune/backend/pyproject.toml` under `[project.dependencies]`
- [ ] T002 [P] Install backend dependencies via `cd solune/backend && uv sync --dev` and verify no conflicts
- [ ] T003 [P] Run backend baseline tests via `cd solune/backend && python -m pytest tests/ -v` and record current state
- [ ] T004 [P] Run frontend baseline tests via `cd solune/frontend && npm test` and record current state

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create backend secrets service and API that MUST be complete before the Secrets Manager UI (US3) and MCP integration (US6) can be built

**⚠️ CRITICAL**: US3 (Secrets Manager) and US6 (MCP Preset Integration) depend on this phase being complete

### 2A: Secrets Service

- [ ] T005 Create `solune/backend/src/services/secrets_service.py` with `SecretsService` class — constructor accepts `GitHubClientFactory` instance, following singleton pattern from `solune/backend/src/services/github_projects/__init__.py`
- [ ] T006 Implement `get_or_create_environment(access_token, owner, repo, environment_name)` method in `solune/backend/src/services/secrets_service.py` — calls `client.rest.repos.async_create_or_update_environment()` to ensure the `copilot` environment exists
- [ ] T007 Implement `list_secrets(access_token, owner, repo, environment_name)` method in `solune/backend/src/services/secrets_service.py` — calls `client.rest.actions.async_list_environment_secrets()`, returns list of secret names + metadata (never values)
- [ ] T008 Implement `_encrypt_secret_value(access_token, owner, repo, environment_name, plaintext)` private method in `solune/backend/src/services/secrets_service.py` — fetches repo public key via `client.rest.actions.async_get_environment_public_key()`, encrypts with `nacl.public.SealedBox`, returns base64-encoded ciphertext + key_id
- [ ] T009 Implement `set_secret(access_token, owner, repo, environment_name, secret_name, secret_value)` method in `solune/backend/src/services/secrets_service.py` — encrypts value via `_encrypt_secret_value()`, then calls `client.rest.actions.async_create_or_update_environment_secret()`
- [ ] T010 Implement `delete_secret(access_token, owner, repo, environment_name, secret_name)` method in `solune/backend/src/services/secrets_service.py` — calls `client.rest.actions.async_delete_environment_secret()`
- [ ] T011 Implement `check_secrets(access_token, owner, repo, environment_name, secret_names)` method in `solune/backend/src/services/secrets_service.py` — calls `list_secrets()` and returns `dict[str, bool]` map of which requested names exist

### 2B: Secrets API Router

- [ ] T012 Create `solune/backend/src/api/secrets.py` with `router = APIRouter(tags=["secrets"])` and import `require_session` dependency from `solune/backend/src/api/dependencies.py`
- [ ] T013 Add Pydantic request/response models in `solune/backend/src/api/secrets.py`: `SecretSetRequest(value: str)` with max 64KB validation, `SecretListResponse(total_count: int, secrets: list[SecretListItem])`, `SecretListItem(name: str, created_at: str, updated_at: str)`, `SecretCheckResponse(results: dict[str, bool])`
- [ ] T014 Implement `GET /secrets/{owner}/{repo}/{environment}` endpoint in `solune/backend/src/api/secrets.py` — calls `secrets_service.list_secrets()`, requires authenticated session
- [ ] T015 [P] Implement `PUT /secrets/{owner}/{repo}/{environment}/{secret_name}` endpoint in `solune/backend/src/api/secrets.py` — validates `secret_name` matches `^[A-Z][A-Z0-9_]*$` (max 255 chars), calls `secrets_service.get_or_create_environment()` then `secrets_service.set_secret()`, requires authenticated session
- [ ] T016 [P] Implement `DELETE /secrets/{owner}/{repo}/{environment}/{secret_name}` endpoint in `solune/backend/src/api/secrets.py` — validates `secret_name`, calls `secrets_service.delete_secret()`, requires authenticated session
- [ ] T017 Implement `GET /secrets/{owner}/{repo}/{environment}/check` endpoint in `solune/backend/src/api/secrets.py` — accepts `names` query parameter (comma-separated), calls `secrets_service.check_secrets()`, returns name-to-boolean map

### 2C: Router Registration

- [ ] T018 Register secrets router in `solune/backend/src/api/__init__.py` — import `secrets.router` and include with prefix `/secrets` following existing pattern for settings, tools, etc.

### 2D: Secrets Types (Frontend)

- [ ] T019 [P] Add `SecretListItem` interface (`name: string`, `created_at: string`, `updated_at: string`) to `solune/frontend/src/types/index.ts`
- [ ] T020 [P] Add `SecretsListResponse` interface (`total_count: number`, `secrets: SecretListItem[]`) to `solune/frontend/src/types/index.ts`
- [ ] T021 [P] Add `SecretCheckResponse` interface (`results: Record<string, boolean>`) to `solune/frontend/src/types/index.ts`

### 2E: Secrets API Client (Frontend)

- [ ] T022 Add `secretsApi` object to `solune/frontend/src/services/api.ts` following the `settingsApi` pattern — methods: `listSecrets(owner, repo, env)`, `setSecret(owner, repo, env, name, value)`, `deleteSecret(owner, repo, env, name)`, `checkSecrets(owner, repo, env, names[])`

### 2F: Secrets Query Hooks (Frontend)

- [ ] T023 Create `solune/frontend/src/hooks/useSecrets.ts` with `secretsKeys` factory pattern: `all: ['secrets']`, `list: (owner, repo, env) => [...all, 'list', owner, repo, env]`, `check: (owner, repo, env, names) => [...all, 'check', owner, repo, env, ...names]`
- [ ] T024 Implement `useSecrets(owner, repo, env)` query hook in `solune/frontend/src/hooks/useSecrets.ts` — calls `secretsApi.listSecrets()`, enabled when all params are defined, returns `{ secrets, isLoading, error }`
- [ ] T025 [P] Implement `useSetSecret()` mutation hook in `solune/frontend/src/hooks/useSecrets.ts` — calls `secretsApi.setSecret()`, invalidates `secretsKeys.list` and `secretsKeys.check` on success
- [ ] T026 [P] Implement `useDeleteSecret()` mutation hook in `solune/frontend/src/hooks/useSecrets.ts` — calls `secretsApi.deleteSecret()`, invalidates `secretsKeys.list` and `secretsKeys.check` on success
- [ ] T027 [P] Implement `useCheckSecrets(owner, repo, env, names[])` query hook in `solune/frontend/src/hooks/useSecrets.ts` — calls `secretsApi.checkSecrets()`, enabled when all params are defined

**Checkpoint**: Foundation ready — backend secrets service, API, frontend types, API client, and hooks are complete. User story implementation can now begin.

---

## Phase 3: User Story 1 — Essential AI Settings at a Glance (Priority: P1) 🎯 MVP

**Goal**: Settings page opens to the Essential tab showing AI provider, model, and temperature — the most-used settings — without scrolling or expanding

**Independent Test**: Navigate to `/settings` → Essential tab is active by default → AI provider, chat model, agent model, temperature slider visible → change provider → models refresh → save → persists on reload

### Implementation for User Story 1

- [ ] T028 [US1] Rename `solune/frontend/src/components/settings/PrimarySettings.tsx` to `solune/frontend/src/components/settings/EssentialSettings.tsx` — update component name and all imports
- [ ] T029 [US1] Remove `SignalConnection` import and rendering from `EssentialSettings.tsx` — Signal moves to Preferences tab (FR-009)
- [ ] T030 [US1] Update `solune/frontend/src/pages/SettingsPage.tsx` to import `EssentialSettings` instead of `PrimarySettings` and render it as the content of the "Essential" tab panel

**Checkpoint**: Essential tab renders AI config only — FR-008, FR-009 satisfied

---

## Phase 4: User Story 2 — Tabbed Navigation Across All Settings (Priority: P1)

**Goal**: Settings page uses a 4-tab layout (Essential, Secrets, Preferences, Admin) with URL hash routing and unsaved changes preservation across tab switches

**Independent Test**: Navigate to `/settings` → see 4 tabs → click each → correct content shown → URL hash updates → navigate to `/settings#preferences` → Preferences tab auto-selected → non-admin user doesn't see Admin tab

### Implementation for User Story 2

- [ ] T031 [US2] Rewrite `solune/frontend/src/pages/SettingsPage.tsx` to use Shadcn `Tabs` component with 4 tabs: "Essential" (default), "Secrets", "Preferences", "Admin" — tab values map to URL hash fragments `#essential`, `#secrets`, `#preferences`, `#admin` (FR-001, FR-002, FR-003)
- [ ] T032 [US2] Add URL hash read logic in `SettingsPage.tsx` — on mount, read `window.location.hash` and set active tab accordingly; if hash is `#admin` and user is not admin, fall back to `#essential` (FR-004, FR-014)
- [ ] T033 [US2] Add URL hash write logic in `SettingsPage.tsx` — on tab change, update `window.location.hash` without triggering page navigation (FR-003)
- [ ] T034 [US2] Conditionally render "Admin" tab trigger in `SettingsPage.tsx` — visible only when `github_user_id === admin_github_user_id` from auth context (FR-005)
- [ ] T035 [US2] Preserve unsaved changes across tab switches in `SettingsPage.tsx` — use controlled tab state so tab content is not unmounted on switch, or use local state persistence (FR-006)
- [ ] T036 [US2] Add `role="tabpanel"` and `aria-labelledby` attributes to each tab panel in `SettingsPage.tsx` — Shadcn Tabs should provide this by default, verify and add if missing (FR-031)
- [ ] T037 [US2] Add auto-focus behavior on tab switch in `SettingsPage.tsx` — focus moves to the active tab panel content when a tab is selected (FR-033)

**Checkpoint**: Tab navigation works with URL hash routing, admin visibility control, and unsaved changes preservation — FR-001 through FR-007, FR-014, FR-031, FR-033 satisfied

---

## Phase 5: User Story 3 — Manage GitHub Environment Secrets for MCP API Keys (Priority: P1)

**Goal**: Users can securely set, update, and delete MCP API keys stored as GitHub environment secrets via the Secrets tab UI

**Independent Test**: Navigate to Secrets tab → select repository → see known secrets with "Not Set" status → set a secret → status changes to "Set" → update the secret → delete the secret → status returns to "Not Set"

### Implementation for User Story 3

- [ ] T038 [US3] Create `solune/frontend/src/components/settings/SecretsManager.tsx` scaffold — export `SecretsManager` component accepting no required props, with internal state for selected `owner`, `repo`, and `environment` (defaults to `"copilot"`)
- [ ] T039 [US3] Add repository selector dropdown to `SecretsManager.tsx` — populate from user's available projects/repos using existing `useProjects()` or `projectsApi.listProjects()` hook (FR-022)
- [ ] T040 [US3] Define `KNOWN_SECRETS` constant in `SecretsManager.tsx` — array of `{ key: string, label: string }` entries, e.g. `{ key: "COPILOT_MCP_CONTEXT7_API_KEY", label: "Context7 API Key" }` (FR-023)
- [ ] T041 [US3] Implement Known Secrets section in `SecretsManager.tsx` — for each `KNOWN_SECRETS` entry, display friendly label, status badge ("Set ✓" if secret exists in `useSecrets()` data, "Not Set" otherwise), and Set/Update/Remove action buttons (FR-023, FR-024)
- [ ] T042 [US3] Implement secret value input in `SecretsManager.tsx` — password-type input with show/hide toggle, `autocomplete="off"`, `aria-label` attribute, never pre-filled from server (FR-026, FR-032)
- [ ] T043 [US3] Implement Set/Update action in `SecretsManager.tsx` — on submit, call `useSetSecret()` mutation with selected repo, environment, secret name, and entered value; show success/error feedback (FR-024)
- [ ] T044 [US3] Implement Remove action in `SecretsManager.tsx` — on confirm, call `useDeleteSecret()` mutation; show confirmation dialog before deletion (FR-024)
- [ ] T045 [US3] Implement "Add Custom Secret" form in `SecretsManager.tsx` — text input for secret name (validate `^[A-Z][A-Z0-9_]*$`, max 255 chars), password input for value (max 64KB), warning if name doesn't start with `COPILOT_MCP_` (FR-025, FR-027)
- [ ] T046 [US3] Wire `SecretsManager` into `SettingsPage.tsx` as the content of the "Secrets" tab panel
- [ ] T047 [US3] Handle empty state in `SecretsManager.tsx` — if user has no repositories, display "No repositories available" message and disable secret management controls (edge case from spec.md)
- [ ] T048 [US3] Handle API errors in `SecretsManager.tsx` — rate limit errors show user-friendly message with retry option and rate-limit reset time; encryption public key errors prevent save with clear message (edge cases from spec.md)

**Checkpoint**: Full secrets CRUD via UI — FR-015 through FR-027 satisfied

---

## Phase 6: User Story 4 — Preferences Tab (Priority: P2)

**Goal**: Display, Workflow, Notification, and Signal settings consolidated in a single Preferences tab with per-section save buttons

**Independent Test**: Navigate to Preferences tab → see 4 card sections → change a display preference → save → only display section saves → switch tabs and back → unsaved changes in other sections preserved

### Implementation for User Story 4

- [ ] T049 [US4] Create `solune/frontend/src/components/settings/PreferencesTab.tsx` — import and render `DisplayPreferences`, `WorkflowDefaults`, `NotificationPreferences`, and `SignalConnection` components, each wrapped in `SettingsSection` card (FR-010)
- [ ] T050 [US4] Pass correct props to each sub-component in `PreferencesTab.tsx` — `settings`, `onSave` callbacks for display/workflow/notification sections using `useUserSettings()` mutation; Signal components use their own hooks (FR-011)
- [ ] T051 [US4] Ensure per-section save buttons are preserved in `PreferencesTab.tsx` — each `SettingsSection` has its own Save button that only saves that section's data (FR-007, FR-011)
- [ ] T052 [US4] Wire `PreferencesTab` into `SettingsPage.tsx` as the content of the "Preferences" tab panel

**Checkpoint**: Preferences tab consolidates all personal settings with independent saves — FR-010, FR-011 satisfied

---

## Phase 7: User Story 5 — Admin-Only Tab (Priority: P2)

**Goal**: Admin tab showing global AI defaults, allowed models, and project settings — hidden from non-admin users

**Independent Test**: Log in as admin → Admin tab visible → modify global defaults → save → persists. Log in as non-admin → Admin tab not visible → navigate to `/settings#admin` → falls back to Essential tab

### Implementation for User Story 5

- [ ] T053 [US5] Create `solune/frontend/src/components/settings/AdminTab.tsx` — import and render `GlobalSettings` and `ProjectSettings` components (FR-012)
- [ ] T054 [US5] Pass correct props to `GlobalSettings` in `AdminTab.tsx` — `settings` from `useGlobalSettings()`, `onSave` callback using global settings mutation, reuse `globalSettingsSchema.ts` Zod validation + `flatten()`/`toUpdate()` converters (FR-013)
- [ ] T055 [US5] Pass correct props to `ProjectSettings` in `AdminTab.tsx` — `projects` list, `selectedProjectId`, project settings hooks
- [ ] T056 [US5] Wire `AdminTab` into `SettingsPage.tsx` as the content of the "Admin" tab panel — already conditionally rendered from US2 (T034)

**Checkpoint**: Admin tab works with existing validation and is hidden from non-admin users — FR-012, FR-013, FR-005 satisfied

---

## Phase 8: User Story 6 — MCP Preset Secret Status Indicators (Priority: P3)

**Goal**: Tools page shows warning badges on MCP presets that require unconfigured secrets, with deep-link to Secrets tab

**Independent Test**: Add MCP preset (e.g. Context7) that requires a secret → "API key not configured" warning visible → click warning → navigates to `/settings#secrets` → set the secret → return to Tools → warning gone

### Implementation for User Story 6

- [ ] T057 [US6] Add `required_secrets: list[str]` field to `McpPresetResponse` model in `solune/backend/src/models/tools.py` with `default_factory=list` (FR-028)
- [ ] T058 [US6] Update Context7 preset definition in `solune/backend/src/services/tools/presets.py` to include `required_secrets=["COPILOT_MCP_CONTEXT7_API_KEY"]` (FR-028)
- [ ] T059 [US6] Update `McpPresetsGallery` component in `solune/frontend/src/components/tools/McpPresetsGallery.tsx` — for each preset with `required_secrets`, call `useCheckSecrets()` hook and display "⚠ API key not configured" badge if any required secret is not set (FR-030)
- [ ] T060 [US6] Add deep-link from warning badge in `McpPresetsGallery.tsx` — clicking the warning navigates to `/settings#secrets` (optional enhancement)

**Checkpoint**: MCP presets show secret configuration warnings — FR-028, FR-029, FR-030 satisfied

---

## Phase 9: User Story 7 — Cleanup of Redundant Components (Priority: P3)

**Goal**: Remove dead code from settings module — delete components consolidated into new tabs and update all references

**Independent Test**: Search codebase for imports of deleted components → zero references found → run full test suite → all pass → settings directory contains only active components

### Implementation for User Story 7

- [ ] T061 [US7] Delete `solune/frontend/src/components/settings/AdvancedSettings.tsx` — functionality replaced by tab layout (FR-034)
- [ ] T062 [P] [US7] Delete `solune/frontend/src/components/settings/AIPreferences.tsx` — functionality consolidated into `EssentialSettings.tsx` (FR-034)
- [ ] T063 [P] [US7] Delete `solune/frontend/src/components/settings/AISettingsSection.tsx` — functionality consolidated into `GlobalSettings.tsx` via `AdminTab` (FR-034)
- [ ] T064 [P] [US7] Delete `solune/frontend/src/components/settings/DisplaySettings.tsx` — functionality consolidated via `DisplayPreferences` in `PreferencesTab` (FR-034)
- [ ] T065 [P] [US7] Delete `solune/frontend/src/components/settings/WorkflowSettings.tsx` — functionality consolidated via `WorkflowDefaults` in `PreferencesTab` (FR-034)
- [ ] T066 [P] [US7] Delete `solune/frontend/src/components/settings/NotificationSettings.tsx` — functionality consolidated via `NotificationPreferences` in `PreferencesTab` (FR-034)
- [ ] T067 [US7] Remove all import references to deleted components — search all `.tsx`, `.ts` files for imports of `AdvancedSettings`, `AIPreferences`, `AISettingsSection`, `DisplaySettings`, `WorkflowSettings`, `NotificationSettings` and remove/update them
- [ ] T068 [US7] Update or remove tests referencing deleted components — update `solune/frontend/src/components/settings/` test files that import or test deleted components (FR-035)

**Checkpoint**: Dead code removed, no broken imports — FR-034, FR-035 satisfied

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Tests, accessibility, and final validation across all user stories

### Backend Tests

- [ ] T069 [P] Create `solune/backend/tests/unit/test_secrets_service.py` — mock githubkit client, test `list_secrets()`, `set_secret()` (verify NaCl encryption), `delete_secret()`, `get_or_create_environment()`, `check_secrets()` method
- [ ] T070 [P] Create `solune/backend/tests/integration/test_secrets_api.py` — test endpoint routing (`GET`, `PUT`, `DELETE`), authentication requirement (401 without session), secret name validation (reject invalid names), value size validation (reject >64KB)

### Frontend Tests

- [ ] T071 [P] Create unit tests for `SecretsManager` in `solune/frontend/src/components/settings/SecretsManager.test.tsx` — test list display, set secret flow, delete secret flow, error states, empty repo state, custom secret form validation
- [ ] T072 [P] Create unit tests for `EssentialSettings` in `solune/frontend/src/components/settings/EssentialSettings.test.tsx` — test provider switch triggers model refresh, temperature slider persistence, no Signal connection rendered
- [ ] T073 [P] Verify existing settings tests still pass — run `cd solune/frontend && npx vitest run src/components/settings/` and fix any failures caused by renamed/deleted components

### Accessibility

- [ ] T074 [P] Verify tab panels in `SettingsPage.tsx` have `role="tabpanel"` and `aria-labelledby` linked to tab triggers — Shadcn Tabs should provide this, verify with DOM inspection (FR-031)
- [ ] T075 [P] Verify all secret inputs in `SecretsManager.tsx` have `aria-label` attributes and `autocomplete="off"` (FR-032)
- [ ] T076 Verify `celestial-focus` class is preserved on all interactive elements across new and refactored components

### Final Validation

- [ ] T077 Run full backend test suite: `cd solune/backend && python -m pytest tests/ -v`
- [ ] T078 [P] Run full frontend test suite: `cd solune/frontend && npm test`
- [ ] T079 [P] Run frontend lint: `cd solune/frontend && npm run lint`
- [ ] T080 Manual verification: Settings page renders 4 tabs; Essential shows AI config only; Admin tab hidden for non-admin; navigate to `/settings#secrets` → Secrets tab auto-selected; existing settings save/load works with no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T002 for pynacl) — BLOCKS US3 and US6
- **US1 (Phase 3)**: Depends on Setup only — can start in parallel with Phase 2
- **US2 (Phase 4)**: Depends on Setup only — can start in parallel with Phase 2; blocks US3 (tab panel needed), US4, US5
- **US3 (Phase 5)**: Depends on Phase 2 (backend secrets API + hooks) AND US2 (tab structure)
- **US4 (Phase 6)**: Depends on US2 (tab structure)
- **US5 (Phase 7)**: Depends on US2 (tab structure)
- **US6 (Phase 8)**: Depends on Phase 2 (secrets check endpoint + hooks) AND US3 (secrets infrastructure)
- **US7 (Phase 9)**: Depends on US1, US2, US4, US5 being complete (components must be consolidated before originals are deleted)
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1 (Setup) ─────────────────────────────────────────────────┐
Phase 2 (Foundational) ────────────────────────────────┐         │
                                                       │         │
US1 (Essential Tab - P1) ──────────────────────────────┼────┐    │
US2 (Tab Navigation - P1) ─────────────┬───────────────┼────┤    │
                                       │               │    │    │
US3 (Secrets Manager - P1) ◄───────────┤◄──────────────┘    │    │
US4 (Preferences Tab - P2) ◄───────────┤                    │    │
US5 (Admin Tab - P2) ◄─────────────────┘                    │    │
                                                            │    │
US6 (MCP Integration - P3) ◄─── US3                         │    │
US7 (Cleanup - P3) ◄─── US1, US2, US4, US5 ────────────────┘    │
                                                                  │
Phase 10 (Polish) ◄─── All stories ──────────────────────────────┘
```

### Within Each User Story

- Models/types before services/hooks
- Services/hooks before components
- Components before page integration
- Core implementation before edge case handling

### Parallel Opportunities

**Phase 2 parallelism**:
- T005–T011 (backend service) and T019–T021 (frontend types) can run in parallel
- T022 (API client) and T023–T027 (hooks) are sequential but parallel with backend T012–T018

**Cross-story parallelism** (after Phase 2 + US2 complete):
- US3, US4, US5 can all start simultaneously since they target different tab panels
- US1 can run in parallel with everything after Setup

**Phase 9 parallelism**:
- T062–T066 (file deletions) are all independent and can run in parallel

**Phase 10 parallelism**:
- T069–T073 (tests) can all run in parallel
- T074–T076 (accessibility) can run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Backend service (sequential within, parallel with frontend):
Task T005: Create SecretsService scaffold
Task T006: Implement get_or_create_environment
Task T007: Implement list_secrets
...

# Frontend types (parallel with backend):
Task T019: Add SecretListItem type
Task T020: Add SecretsListResponse type
Task T021: Add SecretCheckResponse type

# After backend + types complete:
Task T022: Add secretsApi to api.ts
Task T023-T027: Create useSecrets hooks
```

## Parallel Example: User Stories 3, 4, 5 (after US2 complete)

```bash
# Developer A: User Story 3 (Secrets Manager)
Task T038-T048: SecretsManager component

# Developer B: User Story 4 (Preferences Tab)
Task T049-T052: PreferencesTab component

# Developer C: User Story 5 (Admin Tab)
Task T053-T056: AdminTab component
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 3: US1 — Essential Tab (T028–T030) — can start immediately
3. Complete Phase 4: US2 — Tab Navigation (T031–T037) — can start immediately
4. **STOP and VALIDATE**: Settings page has tab layout, Essential tab works
5. Deploy/demo if ready — users already benefit from improved navigation

### Core Feature (Add US3)

1. Complete Phase 2: Foundational (T005–T027) — backend + frontend secrets infra
2. Complete Phase 5: US3 — Secrets Manager (T038–T048)
3. **STOP and VALIDATE**: Full secrets CRUD via UI works end-to-end
4. Deploy/demo — primary new functionality is live

### Full Delivery (Add US4–US7 + Polish)

1. Complete Phase 6: US4 — Preferences Tab (T049–T052)
2. Complete Phase 7: US5 — Admin Tab (T053–T056)
3. Complete Phase 8: US6 — MCP Integration (T057–T060)
4. Complete Phase 9: US7 — Cleanup (T061–T068)
5. Complete Phase 10: Polish (T069–T080)
6. **FINAL VALIDATION**: All tests pass, no regressions

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup (Phase 1) together
2. Phase 2 (Foundational) splits: backend dev on T005–T018, frontend dev on T019–T027
3. US1 (Phase 3) can start immediately by a third dev
4. US2 (Phase 4) can start immediately by a fourth dev
5. Once Phase 2 + US2 complete:
   - Developer A: US3 (Secrets Manager)
   - Developer B: US4 (Preferences)
   - Developer C: US5 (Admin)
6. US6, US7, Polish follow in priority order

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The `copilot` environment name follows GitHub's convention for `$COPILOT_MCP_*` secret exposure to MCP servers
- `pynacl` is required by GitHub API — cannot use `cryptography` library for sealed-box encryption
- Per-section save buttons are preserved throughout (existing UX contract)
- Admin visibility check uses `github_user_id === admin_github_user_id` from auth context
