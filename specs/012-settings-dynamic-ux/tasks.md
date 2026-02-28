# Tasks: Settings Page — Dynamic Value Fetching, Caching, and UX Simplification

**Input**: Design documents from `/specs/012-settings-dynamic-ux/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/settings-api.yaml

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted per Constitution Principle IV (Test Optionality).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Backend and frontend scaffolding needed before any feature work begins

- [x] T001 Add `ModelOption` and `ModelsResponse` Pydantic models to backend/src/models/settings.py
- [x] T002 [P] Create provider interface `ModelFetchProvider` protocol and provider registry in backend/src/services/model_fetcher.py
- [x] T003 [P] Add `fetchModels(provider)` method to the `settingsApi` object in frontend/src/services/api.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend service infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement `GitHubCopilotModelFetcher` class (implements `ModelFetchProvider`) with GitHub API call in backend/src/services/model_fetcher.py
- [x] T005 [P] Implement `AzureOpenAIModelFetcher` class (implements `ModelFetchProvider`, returns static list from env config) in backend/src/services/model_fetcher.py
- [x] T006 Implement `ModelFetcherService` with in-memory TTL cache (keyed by `{provider}:{token_hash}`, default TTL 600s) in backend/src/services/model_fetcher.py
- [x] T007 Add `GET /settings/models/{provider}` endpoint with `force_refresh` query param to backend/src/api/settings.py (delegates to `ModelFetcherService`)
- [x] T008 [P] Add `useModelOptions(provider)` TanStack Query hook with `staleTime: 5 min` and `enabled` flag to frontend/src/hooks/useSettings.ts

**Checkpoint**: Foundation ready — backend can fetch and cache models, frontend can query backend. User story implementation can now begin.

---

## Phase 3: User Story 1 — Simplified Settings Layout (Priority: P1) 🎯 MVP

**Goal**: Reorganize the Settings page so primary settings (model provider, chat model, GitHub agent model, Signal connection) are prominent at the top, and secondary/advanced settings are collapsed.

**Independent Test**: Navigate to Settings page → primary settings visible without scrolling; advanced settings collapsed by default; expand advanced section → all secondary settings functional.

### Implementation for User Story 1

- [x] T009 [P] [US1] Create `PrimarySettings` component rendering model provider, chat model, GitHub agent model, and Signal connection fields in frontend/src/components/settings/PrimarySettings.tsx
- [x] T010 [P] [US1] Create `AdvancedSettings` component with collapsible wrapper (collapsed by default) containing display, workflow, notification, allowed models, and project settings in frontend/src/components/settings/AdvancedSettings.tsx
- [x] T011 [US1] Refactor `SettingsPage` to render `PrimarySettings` at top and `AdvancedSettings` below in frontend/src/pages/SettingsPage.tsx
- [x] T012 [US1] Update `GlobalSettings` to extract primary AI fields into `PrimarySettings` scope in frontend/src/components/settings/GlobalSettings.tsx

**Checkpoint**: Settings page shows primary settings prominently and advanced settings collapsed. Fully functional and testable independently.

---

## Phase 4: User Story 2 — Dynamic Dropdown Population (Priority: P1) 🎯 MVP

**Goal**: Replace static model selection with dynamic dropdowns that fetch available models from the selected provider in real time.

**Independent Test**: Select GitHub Copilot as provider → model dropdown shows spinner → populates with live models from GitHub; switch provider → dropdown clears and repopulates; select static provider → static options shown, no fetch.

### Implementation for User Story 2

- [x] T013 [US2] Create `DynamicDropdown` component with idle, loading (spinner + disabled), and success states in frontend/src/components/settings/DynamicDropdown.tsx
- [x] T014 [US2] Integrate `DynamicDropdown` with `useModelOptions` hook for chat model selection in frontend/src/components/settings/PrimarySettings.tsx
- [x] T015 [US2] Integrate `DynamicDropdown` with `useModelOptions` hook for GitHub agent model selection in frontend/src/components/settings/PrimarySettings.tsx
- [x] T016 [US2] Add provider-change detection logic to clear and refetch model options when provider selection changes in frontend/src/components/settings/PrimarySettings.tsx
- [x] T017 [US2] Add `supports_dynamic_models` flag to `AIProvider` enum and expose in provider metadata in backend/src/models/settings.py
- [x] T018 [US2] Handle empty model list response by displaying "No models available for this provider" message in frontend/src/components/settings/DynamicDropdown.tsx

**Checkpoint**: Dynamic dropdowns populated from live provider API. Provider switching triggers refetch. Static providers show configured options. Testable independently.

---

## Phase 5: User Story 3 — Caching and Freshness Indicators (Priority: P2)

**Goal**: Show cached model options instantly on page revisit with freshness metadata, and refresh stale data in the background without blocking the user.

**Independent Test**: Fetch models → navigate away → return to Settings → dropdown pre-populated from cache with "Last updated X minutes ago" label; no new network request visible until cache expires.

### Implementation for User Story 3

- [x] T019 [US3] Add stale-while-revalidate behavior to `ModelFetcherService` — serve stale cache immediately, trigger `asyncio.create_task` for background refresh in backend/src/services/model_fetcher.py
- [x] T020 [US3] Expose `fetched_at` and `cache_hit` fields in the `/settings/models/{provider}` response from backend/src/api/settings.py
- [x] T021 [US3] Add freshness indicator component (e.g., "Last updated 5 minutes ago") adjacent to `DynamicDropdown` in frontend/src/components/settings/DynamicDropdown.tsx
- [x] T022 [US3] Configure TanStack Query `gcTime` and `staleTime` in `useModelOptions` to serve cached data on page revisit in frontend/src/hooks/useSettings.ts

**Checkpoint**: Cached dropdown values load instantly; freshness metadata displayed; background refresh works without blocking UI. Testable independently.

---

## Phase 6: User Story 4 — Graceful Error Handling and Retry (Priority: P2)

**Goal**: When model fetch fails, show a clear error message with retry button and fall back to cached values if available.

**Independent Test**: Simulate network failure → dropdown shows error message + retry button + cached values (if any); click retry → loading spinner → success or error; no cached values → error + retry only.

### Implementation for User Story 4

- [x] T023 [US4] Add error and retry states to `DynamicDropdown` — display error message, retry button, and fallback to cached values in frontend/src/components/settings/DynamicDropdown.tsx
- [x] T024 [US4] Implement retry logic in `useModelOptions` hook using TanStack Query `refetch` on retry button click in frontend/src/hooks/useSettings.ts
- [x] T025 [US4] Return structured error response with `status: "error"` and `message` from backend when fetch fails in backend/src/services/model_fetcher.py
- [x] T026 [US4] Handle "no cached values + error" state in `DynamicDropdown` — show error and retry with no selectable options in frontend/src/components/settings/DynamicDropdown.tsx

**Checkpoint**: Fetch failures show user-friendly error with retry. Cached fallback works. No broken or empty dropdowns without recourse. Testable independently.

---

## Phase 7: User Story 5 — Prerequisite Validation (Priority: P2)

**Goal**: When required credentials are missing (e.g., GitHub token), show an inline prerequisite message instead of attempting a failed fetch.

**Independent Test**: Open Settings without GitHub credentials → dynamic dropdown shows "Connect your GitHub account to see available models" message; configure credentials → dropdown auto-fetches models.

### Implementation for User Story 5

- [x] T027 [US5] Add auth prerequisite check in `GET /settings/models/{provider}` — verify token existence via `github_auth.py` session lookup before fetching in backend/src/api/settings.py
- [x] T028 [US5] Return `{ status: "auth_required", message: "..." }` response when credentials are missing in backend/src/services/model_fetcher.py
- [x] T029 [US5] Add `auth_required` state rendering to `DynamicDropdown` — inline message with link/button to setup flow in frontend/src/components/settings/DynamicDropdown.tsx
- [x] T030 [US5] Add Signal connection prerequisite check — display inline guidance when Signal is not configured in frontend/src/components/settings/PrimarySettings.tsx

**Checkpoint**: Missing credentials show clear prerequisite message. No failed fetches attempted. Completing setup triggers automatic fetch. Testable independently.

---

## Phase 8: User Story 6 — Rate-Limit Awareness (Priority: P3)

**Goal**: Detect and surface rate-limit warnings from the provider, apply exponential backoff, and auto-retry after backoff period.

**Independent Test**: Simulate rate-limit response → warning displayed near dropdown → backoff applied → auto-retry after backoff expires.

### Implementation for User Story 6

- [x] T031 [US6] Parse `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and `Retry-After` headers in `GitHubCopilotModelFetcher` in backend/src/services/model_fetcher.py
- [x] T032 [US6] Implement exponential backoff logic in `ModelFetcherService` — start at Retry-After value (or 60s default), double on consecutive 429s, cap at 15 min in backend/src/services/model_fetcher.py
- [x] T033 [US6] Set `rate_limit_warning` flag when remaining quota < 10% and include in `ModelsResponse` in backend/src/services/model_fetcher.py
- [x] T034 [US6] Add `rate_limited` state rendering to `DynamicDropdown` — non-blocking warning banner with cached values in frontend/src/components/settings/DynamicDropdown.tsx

**Checkpoint**: Rate-limit warnings displayed proactively. Backoff prevents further 429s. Auto-retry works after cooldown. Testable independently.

---

## Phase 9: User Story 7 — Full Accessibility (Priority: P3)

**Goal**: Ensure all Settings page elements — dynamic dropdowns, loading/error states, collapsible sections — are fully accessible via keyboard and screen reader.

**Independent Test**: Navigate entire Settings page with keyboard only → all elements reachable in logical tab order; use screen reader → loading, error, success states announced; test on 320px viewport → all controls usable.

### Implementation for User Story 7

- [x] T035 [US7] Add ARIA attributes to `DynamicDropdown` — `aria-busy`, `aria-label`, `aria-live="polite"` region for status announcements in frontend/src/components/settings/DynamicDropdown.tsx
- [x] T036 [US7] Add `role="alert"` to error messages and ensure retry button is keyboard-focusable in frontend/src/components/settings/DynamicDropdown.tsx
- [x] T037 [US7] Add `aria-expanded` and `aria-controls` to the `AdvancedSettings` collapsible toggle in frontend/src/components/settings/AdvancedSettings.tsx
- [x] T038 [US7] Verify responsive layout of `PrimarySettings` and `AdvancedSettings` across 320px–2560px viewports in frontend/src/components/settings/PrimarySettings.tsx and frontend/src/components/settings/AdvancedSettings.tsx

**Checkpoint**: Full keyboard navigation, screen reader announcements for all states, responsive layout verified. Testable independently.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T039 [P] Update quickstart.md with verified setup and validation steps in specs/012-settings-dynamic-ux/quickstart.md
- [x] T040 In-flight fetch cancellation when provider changes rapidly (abort controller) in frontend/src/hooks/useSettings.ts
- [x] T041 [P] Cache invalidation on authentication status change — clear stale entries when user logs out or token expires in backend/src/services/model_fetcher.py
- [x] T042 Code cleanup — remove any unused imports or dead code introduced during feature implementation across all modified files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — layout reorganization
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) + User Story 1 (Phase 3) — dynamic dropdowns need the new layout
- **User Story 3 (Phase 5)**: Depends on User Story 2 (Phase 4) — caching enhances the dynamic dropdowns
- **User Story 4 (Phase 6)**: Depends on User Story 2 (Phase 4) — error handling for the dynamic fetch
- **User Story 5 (Phase 7)**: Depends on Foundational (Phase 2) — prerequisite check is backend + dropdown state
- **User Story 6 (Phase 8)**: Depends on User Story 2 (Phase 4) — rate-limit handling for the fetch pipeline
- **User Story 7 (Phase 9)**: Depends on User Stories 1–6 — accessibility audit of all implemented components
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — No dependencies on other stories
- **US2 (P1)**: Depends on US1 (needs layout to place dropdowns) — but independently testable
- **US3 (P2)**: Depends on US2 (caching enhances dynamic dropdowns) — independently testable
- **US4 (P2)**: Depends on US2 (error handling for dynamic fetch) — independently testable
- **US5 (P2)**: Can start after Foundational — independently testable (does not depend on US1/US2)
- **US6 (P3)**: Depends on US2 (rate-limit handling for fetch pipeline) — independently testable
- **US7 (P3)**: Should be implemented last, after all UI components exist — independently testable

### Within Each User Story

- Models/types before services
- Backend before frontend (API contract must exist before UI consumes it)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (different repos/files)
- **Phase 2**: T005 can run in parallel with T004 (separate provider classes)
- **Phase 2**: T008 runs in parallel with T004–T007 (frontend hook independent of backend implementation)
- **Phase 3**: T009 and T010 can run in parallel (separate component files)
- **Phase 4**: T014 and T015 are sequential within PrimarySettings but can overlap with T017 (backend)
- **Phase 10**: T039 and T041 can run in parallel (docs vs. code)

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch backend provider implementations in parallel:
Task T004: "Implement GitHubCopilotModelFetcher in backend/src/services/model_fetcher.py"
Task T005: "Implement AzureOpenAIModelFetcher in backend/src/services/model_fetcher.py"

# Launch frontend hook in parallel with backend work:
Task T008: "Add useModelOptions hook in frontend/src/hooks/useSettings.ts"
```

## Parallel Example: Phase 3 (User Story 1)

```bash
# Launch new layout components in parallel:
Task T009: "Create PrimarySettings in frontend/src/components/settings/PrimarySettings.tsx"
Task T010: "Create AdvancedSettings in frontend/src/components/settings/AdvancedSettings.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T008)
3. Complete Phase 3: User Story 1 — Simplified Layout (T009–T012)
4. Complete Phase 4: User Story 2 — Dynamic Dropdowns (T013–T018)
5. **STOP and VALIDATE**: Test simplified layout + dynamic dropdowns independently
6. Deploy/demo if ready — this is the MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (Layout) → Test independently → Deploy/Demo
3. Add US2 (Dynamic Dropdowns) → Test independently → Deploy/Demo (MVP!)
4. Add US3 (Caching) → Test independently → Deploy/Demo
5. Add US4 (Error Handling) + US5 (Prereqs) → Test independently → Deploy/Demo
6. Add US6 (Rate Limits) + US7 (Accessibility) → Test independently → Deploy/Demo
7. Polish phase → Final validation → Release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Layout) → US2 (Dynamic Dropdowns)
   - Developer B: US5 (Prerequisite Validation) — independent of layout
3. After US2 is complete:
   - Developer A: US3 (Caching) → US6 (Rate Limits)
   - Developer B: US4 (Error Handling)
4. US7 (Accessibility) last — audits all completed components
5. Polish phase → everyone reviews

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 42 |
| **Phase 1 (Setup)** | 3 tasks |
| **Phase 2 (Foundational)** | 5 tasks |
| **US1 — Simplified Layout (P1)** | 4 tasks |
| **US2 — Dynamic Dropdowns (P1)** | 6 tasks |
| **US3 — Caching (P2)** | 4 tasks |
| **US4 — Error Handling (P2)** | 4 tasks |
| **US5 — Prerequisite Validation (P2)** | 4 tasks |
| **US6 — Rate-Limit Awareness (P3)** | 4 tasks |
| **US7 — Full Accessibility (P3)** | 4 tasks |
| **Polish** | 4 tasks |
| **Parallel opportunities** | 6 identified |
| **Suggested MVP scope** | US1 + US2 (Phases 1–4, 18 tasks) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Backend model_fetcher.py is a single new file with multiple classes — tasks T002/T004/T005/T006 build it incrementally
- Frontend DynamicDropdown.tsx is built incrementally across US2/US3/US4/US5/US6/US7 — each story adds states
