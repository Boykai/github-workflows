# Tasks: DRY Logging & Error Handling Modernization

**Input**: Design documents from `/specs/030-dry-error-handling/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (error-responses.md, components.md), quickstart.md

**Tests**: Not explicitly requested in the feature specification. Existing backend (pytest) and frontend (vitest) test suites must continue to pass with zero regressions (FR-016, FR-017). No new test tasks are included.

**Organization**: Tasks grouped by user story (P1–P6) for independent implementation and testing. Backend stories (US1, US5) and frontend stories (US2, US3, US4, US6) can proceed in parallel across layers. Each user story can be delivered as an independently verifiable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5, US6)
- Exact file paths included in descriptions

## Path Conventions

- **Web app**: `backend/src/` (Python/FastAPI), `frontend/src/` (React/TypeScript)
- Backend exceptions: `backend/src/exceptions.py`
- Backend logging: `backend/src/logging_utils.py` (handle_service_error — existing, zero callers)
- Backend API routes: `backend/src/api/*.py`
- Backend entry point: `backend/src/main.py`
- Frontend utilities: `frontend/src/utils/`
- Frontend components: `frontend/src/components/common/`
- Frontend hooks: `frontend/src/hooks/`
- Frontend entry: `frontend/src/main.tsx`, `frontend/src/App.tsx`

---

## Phase 1: Setup

**Purpose**: Establish baseline — confirm existing test suites pass before making any changes.

- [ ] T001 Verify existing backend test suite passes by running `pytest backend/tests/ -v` to establish a clean baseline
- [ ] T002 [P] Verify existing frontend compiles and tests pass by running `npx tsc --noEmit` and `npx vitest run` in frontend/

**Checkpoint**: Baseline confirmed. All existing tests pass. Ready for implementation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the ConflictError exception class that the HTTPException migration depends on. This MUST be complete before US1 migration tasks can begin.

**⚠️ CRITICAL**: The `ConflictError` class is required by US1's HTTPException→AppException migration for any `status_code=409` replacements.

- [ ] T003 Add `ConflictError(AppException)` class with `status_code=409` to backend/src/exceptions.py — place after `NotFoundError` and before `ValidationError`, following the exact pattern from research.md R2: `def __init__(self, message: str = "Resource conflict"): super().__init__(message, status_code=status.HTTP_409_CONFLICT)`

**Checkpoint**: `ConflictError` is importable and returns status code 409. The complete AppException hierarchy now includes `ConflictError`. Ready for US1.

---

## Phase 3: User Story 1 — Backend Error Contract Unification (Priority: P1) 🎯 MVP

**Goal**: Migrate all 79 raw HTTPException usages across 8 files to AppException subclasses, activate the dead `handle_service_error()` helper across 12 manual logger+raise patterns in 5 files, and fix silent catch blocks — so that every API error follows the unified AppException contract.

**Independent Test**: Run the existing backend test suite and confirm: (a) zero remaining `HTTPException` imports in API route files, (b) `handle_service_error()` has 12+ call sites (up from zero), (c) no silent `except` blocks remain in API routes, (d) all tests pass.

### HTTPException → AppException Migration (FR-002, FR-006)

> **Mapping** (from research.md R1): 400→`ValidationError`, 401→`AuthenticationError`, 403→`AuthorizationError`, 404→`NotFoundError`, 409→`ConflictError`, 422→`ValidationError`, 500→`AppException(message, status_code=500)` for non-GitHub errors or `GitHubAPIError` for GitHub-related errors, 502→`GitHubAPIError`. Each replacement requires reading semantic context to select the correct subclass. Reference: `board.py` as the exemplar.

- [ ] T004 [P] [US1] Migrate 5 HTTPException usages to AppException subclasses in backend/src/dependencies.py — replace `from fastapi import HTTPException` with appropriate AppException imports, map each raise by semantic context (401→AuthenticationError, 500→AppException base)
- [ ] T005 [P] [US1] Migrate 5 HTTPException usages to AppException subclasses in backend/src/api/auth.py — map 400→ValidationError, 401→AuthenticationError, 500→AppException base
- [ ] T006 [P] [US1] Migrate 16 HTTPException usages to AppException subclasses and replace 3 manual logger.error+raise patterns with handle_service_error() calls in backend/src/api/agents.py — map 400→ValidationError, 404→NotFoundError, 500→GitHubAPIError; import handle_service_error from src.logging_utils
- [ ] T007 [P] [US1] Migrate 18 HTTPException usages to AppException subclasses and replace 3 manual logger.error+raise patterns with handle_service_error() calls in backend/src/api/chores.py — map 400→ValidationError, 404→NotFoundError, 500→GitHubAPIError; import handle_service_error from src.logging_utils
- [ ] T008 [P] [US1] Migrate 11 HTTPException usages to AppException subclasses in backend/src/api/signal.py — map 400→ValidationError, 404→NotFoundError, 500→GitHubAPIError
- [ ] T009 [P] [US1] Migrate 12 HTTPException usages to AppException subclasses in backend/src/api/tools.py — map 400→ValidationError, 404→NotFoundError, 500→GitHubAPIError
- [ ] T010 [P] [US1] Migrate 7 HTTPException usages to AppException subclasses in backend/src/api/pipelines.py — map 400→ValidationError, 404→NotFoundError, 500→GitHubAPIError
- [ ] T011 [P] [US1] Migrate 3 HTTPException usages to AppException subclasses in backend/src/api/webhooks.py — map 400→ValidationError, 401→AuthenticationError, 500→AppException base

### Activate handle_service_error() (FR-001)

> **Pattern** (from contracts/error-responses.md): Replace `logger.error("Failed to X: %s", e, exc_info=True)` + `raise SomeException(message="Failed to X") from e` with `handle_service_error(e, "X", SomeException)`. The function logs at ERROR with exc_info=True and raises the specified AppException subclass.

- [ ] T012 [P] [US1] Replace 3 manual logger.error+raise patterns with handle_service_error() calls in backend/src/api/cleanup.py — import handle_service_error from src.logging_utils
- [ ] T013 [P] [US1] Replace 2 manual logger.error+raise patterns with handle_service_error() calls in backend/src/api/board.py — import handle_service_error from src.logging_utils
- [ ] T014 [P] [US1] Replace 1 manual logger.error+raise pattern with handle_service_error() call in backend/src/api/workflow.py — verify WorkflowError compatibility per research.md R3 (if WorkflowError is not an AppException subclass, keep the existing pattern)

### Fix Silent Catch Blocks (FR-004)

- [ ] T015 [P] [US1] Fix silent `except Exception: pass` block in backend/src/api/settings.py (~L156) by adding `logger.debug("Cache invalidation skipped: %s", e)` with the exception variable
- [ ] T016 [US1] Audit all `except` blocks across backend/src/api/ files — verify no remaining silent catch blocks that swallow exceptions without any logging; document any additional fixes applied

### Verification

- [ ] T017 [US1] Verify zero remaining `from fastapi import HTTPException` or `from starlette.exceptions import HTTPException` imports in backend/src/api/ and backend/src/dependencies.py (FR-006) — the global exception handler in main.py and middleware may still reference HTTPException
- [ ] T018 [US1] Verify handle_service_error has 12+ call sites by running `grep -r "handle_service_error" backend/src/api/` (FR-001, FR-018)
- [ ] T019 [US1] Run existing backend test suite (`pytest backend/tests/ -v`) to confirm zero regressions from the HTTPException→AppException migration (FR-016)

**Checkpoint**: All backend API routes use AppException subclasses exclusively. `handle_service_error()` is activated with 12+ callers. No silent catch blocks remain. Backend tests pass. This is the MVP — the unified backend error contract is in place.

---

## Phase 4: User Story 2 — Frontend Logger Utility & Silent-Catch Remediation (Priority: P2)

**Goal**: Create a shared logger utility wrapping console methods with environment-aware gating, replace all existing console.error/console.warn calls, and add logging to all silent catch blocks in frontend hooks.

**Independent Test**: Import the logger in a test, call `logger.error()` in dev mode and confirm console output. Search for empty catch blocks and confirm none remain. Search for `console.error`/`console.warn` and confirm none remain outside logger.ts.

### Implementation for User Story 2

- [ ] T020 [US2] Create shared logger utility in frontend/src/utils/logger.ts — export `logger` object with `error()` (always emits), `warn()` (dev only via `import.meta.env.DEV`), and `info()` (dev only) methods wrapping corresponding console methods, per data-model.md and contracts/components.md specifications
- [ ] T021 [P] [US2] Replace `console.error('ErrorBoundary caught:', ...)` with `logger.error('ErrorBoundary caught:', ...)` in frontend/src/components/common/ErrorBoundary.tsx — add `import { logger } from '@/utils/logger'`
- [ ] T022 [P] [US2] Replace `console.error('Auth-expired listener threw:', ...)` with `logger.error('Auth-expired listener threw:', ...)` in frontend/src/services/api.ts — add `import { logger } from '@/utils/logger'`
- [ ] T023 [P] [US2] Replace `console.error('Failed to parse WebSocket message:', ...)` with `logger.error(...)` and add `logger.info('WebSocket not available, falling back to polling')` to the silent WebSocket constructor catch (~L173) in frontend/src/hooks/useRealTimeSync.ts
- [ ] T024 [P] [US2] Replace `console.warn('Pipeline assignment failed:', ...)` with `logger.warn('Pipeline assignment failed:', ...)` in frontend/src/hooks/usePipelineConfig.ts
- [ ] T025 [P] [US2] Replace `console.warn('Failed to seed preset pipelines:', ...)` with `logger.warn('Failed to seed preset pipelines:', ...)` in frontend/src/pages/AgentsPipelinePage.tsx
- [ ] T026 [P] [US2] Add `logger.warn('Failed to parse board controls from localStorage')` and `logger.warn('Failed to save board controls to localStorage')` to the 2 silent catch blocks in frontend/src/hooks/useBoardControls.ts (~L110, ~L117)
- [ ] T027 [P] [US2] Add `logger.warn('Failed to read sidebar state from localStorage')` and `logger.warn('Failed to save sidebar state to localStorage')` to the 2 silent catch blocks in frontend/src/hooks/useSidebarState.ts (~L10, ~L23)
- [ ] T028 [P] [US2] Add `logger.warn('Failed to persist theme to server')` to the silent catch block in frontend/src/hooks/useAppTheme.ts (~L39)

**Checkpoint**: Logger utility is available. All `console.error()`/`console.warn()` calls replaced. All silent catch blocks in hooks have logging. Frontend compiles and tests pass.

---

## Phase 5: User Story 3 — Shared ErrorAlert Component & Inline Error Replacement (Priority: P3)

**Goal**: Create a reusable `<ErrorAlert>` component with standardized destructive styling and replace scattered inline error displays across 3+ components, so that all user-facing error messages have a consistent look with optional retry and dismiss actions.

**Independent Test**: Render `<ErrorAlert>` in isolation with various prop combinations (message only, message + onRetry, message + onDismiss, all props) and confirm correct styling and callback behavior. Navigate to each page, trigger an error, confirm ErrorAlert renders correctly.

### Implementation for User Story 3

- [ ] T029 [US3] Create shared `<ErrorAlert>` component in frontend/src/components/common/ErrorAlert.tsx — accept `message` (required), `onRetry?`, `onDismiss?`, `className?` props; use `role="alert"`, destructive styling (`border border-destructive/30 bg-destructive/10 text-destructive rounded-[1.1rem] p-4`), and `cn()` utility for className merging, per contracts/components.md specification
- [ ] T030 [P] [US3] Replace 3 inline error display banners (refresh error, projects error, board error with retry) with `<ErrorAlert>` in frontend/src/pages/ProjectsPage.tsx — preserve `onRetry` callbacks for the board error banner; do NOT replace rate-limit banners (they use accent colors, not destructive)
- [ ] T031 [P] [US3] Replace inline error display with `<ErrorAlert>` in frontend/src/components/chat/IssueRecommendationPreview.tsx (~L111)
- [ ] T032 [P] [US3] Replace file error displays with `<ErrorAlert>` in frontend/src/components/chat/ChatInterface.tsx — map over `fileErrors` array with `<ErrorAlert key={err} message={err} />`

**Checkpoint**: ErrorAlert component exists with consistent styling. All identified inline error displays replaced. Frontend compiles and tests pass.

---

## Phase 6: User Story 4 — Toast Notification System for Mutation Errors (Priority: P4)

**Goal**: Install sonner, mount `<Toaster />` at the application root, and wire TanStack QueryClient's default `mutations.onError` to auto-toast unhandled mutation errors — so that users see non-blocking feedback when mutations fail without per-mutation boilerplate.

**Independent Test**: Trigger a failing mutation (without per-mutation `onError`) and confirm a toast notification appears with the error message within 1 second, auto-dismisses after ~5 seconds, and does not block other UI interactions. Confirm per-mutation `onError` overrides still work.

### Implementation for User Story 4

- [ ] T033 [US4] Install `sonner` package in frontend/ by running `npm install sonner`
- [ ] T034 [US4] Add `<Toaster position="top-right" richColors toastOptions={{ className: 'text-sm' }} />` to frontend/src/App.tsx — place after `<RouterProvider />` inside the `<QueryClientProvider>` wrapper; import `Toaster` from `sonner`
- [ ] T035 [US4] Add default `mutations.onError` callback to QueryClient `defaultOptions` in frontend/src/App.tsx — log via `logger.error('Mutation failed:', error)` and show toast via `toast.error(error instanceof Error ? error.message : 'An error occurred')` per contracts/components.md; import `toast` from `sonner` and `logger` from `@/utils/logger`

**Checkpoint**: Sonner installed. Toaster mounted. Default mutation errors auto-toast. Per-mutation `onError` overrides still respected (standard TanStack Query v5 behavior). Frontend compiles and tests pass.

---

## Phase 7: User Story 5 — Background Task Correlation IDs (Priority: P5)

**Goal**: Inject synthetic `request_id_var` context variables into the three background task loops in `main.py` using a `bg-<task-name>-<hex8>` pattern, so that all background task log lines include traceable correlation IDs distinguishable from HTTP request IDs.

**Independent Test**: Start the application, allow background tasks to run, and confirm log output includes correlation IDs matching `bg-polling-<hex8>`, `bg-cleanup-<hex8>`, and `bg-copilot-<hex8>` patterns.

### Implementation for User Story 5

- [ ] T036 [US5] Inject correlation ID `bg-polling-{uuid4().hex[:8]}` into `_polling_watchdog_loop()` in backend/src/main.py — import `uuid4` from `uuid` and `request_id_var` from `src.middleware.request_id`; set the token at the start of each iteration with `token = request_id_var.set(...)` and reset in a `finally` block with `request_id_var.reset(token)`, per contracts/error-responses.md
- [ ] T037 [P] [US5] Inject correlation ID `bg-cleanup-{uuid4().hex[:8]}` into `_session_cleanup_loop()` in backend/src/main.py — same pattern as T036
- [ ] T038 [P] [US5] Inject correlation ID `bg-copilot-{uuid4().hex[:8]}` into `_auto_start_copilot_polling()` in backend/src/main.py — same pattern as T036

**Checkpoint**: Background task logs include `bg-polling-*`, `bg-cleanup-*`, `bg-copilot-*` correlation IDs. Backend tests still pass.

---

## Phase 8: User Story 6 — Global Unhandled Error Capture (Priority: P6)

**Goal**: Register global handlers for `unhandledrejection` and `window.onerror` in the application entry point, routing all uncaught errors through `logger.error()` so that no frontend error goes completely unnoticed.

**Independent Test**: Deliberately trigger an unhandled promise rejection in a test environment and confirm `logger.error()` is called with the rejection reason. Trigger an uncaught error and confirm `window.onerror` routes it through the logger.

### Implementation for User Story 6

- [ ] T039 [US6] Register global `window.addEventListener('unhandledrejection', ...)` and `window.onerror` handlers in frontend/src/main.tsx — place before the `createRoot` call; import `logger` from `./utils/logger`; log rejection reason and error details via `logger.error()` per contracts/components.md specification

**Checkpoint**: Global error handlers registered. Unhandled rejections and uncaught errors are logged. Frontend compiles and tests pass.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, regression testing, and quickstart verification across all user stories.

- [ ] T040 Run full backend test suite (`pytest backend/tests/ -v`) to verify zero regressions across all backend changes (FR-016)
- [ ] T041 [P] Run full frontend test suite (`npx vitest run`) to verify zero regressions across all frontend changes (FR-017)
- [ ] T042 [P] Verify TypeScript compilation (`npx tsc --noEmit` in frontend/) — zero type errors
- [ ] T043 Run quickstart.md verification checklist — confirm all 13 verification items pass: ConflictError imports (409), zero HTTPException in routes, 12+ handle_service_error callers, no silent catches, background task correlation IDs, logger utility works, console.* replaced, ErrorAlert renders, toast fires on mutation error, global handlers capture unhandled errors, backend tests pass, frontend tests pass, TypeScript compiles

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — baseline test runs
- **Foundational (Phase 2)**: Depends on Setup — ConflictError must exist before US1 migration
- **US1 (Phase 3)**: Depends on Foundational — HTTPException migration needs ConflictError for 409 replacements
- **US2 (Phase 4)**: Depends on Setup only — frontend logger is independent of backend changes; can run in parallel with US1
- **US3 (Phase 5)**: Depends on Setup only — ErrorAlert component is independent; can run in parallel with US1 and US2
- **US4 (Phase 6)**: Depends on US2 — toast onError callback uses `logger.error()`
- **US5 (Phase 7)**: Depends on Foundational only — correlation IDs use existing request_id_var infrastructure; can run in parallel with US1
- **US6 (Phase 8)**: Depends on US2 — global handlers use `logger.error()`
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (Phase 2) — backend-only, no frontend dependencies
- **US2 (P2)**: Independent of backend stories — can start after Setup (Phase 1)
- **US3 (P3)**: Independent of other stories — can start after Setup (Phase 1); benefits from US2 but does not require it
- **US4 (P4)**: Depends on US2 — needs `logger` utility for the `mutations.onError` callback
- **US5 (P5)**: Depends on Foundational (Phase 2) — backend-only, no frontend dependencies; can run in parallel with US1
- **US6 (P6)**: Depends on US2 — needs `logger` utility for global error handlers

### Within Each User Story

- All HTTPException migration tasks within US1 are independent per-file and marked [P]
- All handle_service_error activation tasks within US1 are independent per-file and marked [P]
- Logger utility (T020) must be created before any replacement/addition tasks (T021–T028)
- ErrorAlert component (T029) must be created before any replacement tasks (T030–T032)
- sonner must be installed (T033) before Toaster mount and QueryClient config (T034–T035)
- All three background task correlation ID tasks (T036–T038) are in the same file but independent loop functions

### Parallel Opportunities

- **Cross-layer parallelism**: US1 (backend) can run in parallel with US2 (frontend) and US3 (frontend) — completely different files and tech stacks
- **Within US1**: All 8 HTTPException migration tasks (T004–T011) can run in parallel — different files
- **Within US1**: All 3 handle_service_error tasks (T012–T014) can run in parallel — different files
- **Within US2**: All 8 replacement/addition tasks (T021–T028) can run in parallel after T020 — different files
- **Within US3**: All 3 replacement tasks (T030–T032) can run in parallel after T029 — different files
- **Within US5**: T037 and T038 can run in parallel with T036 — independent loop functions in the same file
- **Polish**: T040, T041, and T042 can run in parallel

---

## Parallel Example: User Story 1 (HTTPException Migration)

```bash
# Launch all 8 HTTPException migration tasks in parallel (different files):
Task: "Migrate HTTPException → AppException in backend/src/dependencies.py"
Task: "Migrate HTTPException → AppException in backend/src/api/auth.py"
Task: "Migrate HTTPException → AppException in backend/src/api/agents.py"
Task: "Migrate HTTPException → AppException in backend/src/api/chores.py"
Task: "Migrate HTTPException → AppException in backend/src/api/signal.py"
Task: "Migrate HTTPException → AppException in backend/src/api/tools.py"
Task: "Migrate HTTPException → AppException in backend/src/api/pipelines.py"
Task: "Migrate HTTPException → AppException in backend/src/api/webhooks.py"

# Launch all handle_service_error activation tasks in parallel (different files):
Task: "Replace manual logger+raise with handle_service_error() in backend/src/api/cleanup.py"
Task: "Replace manual logger+raise with handle_service_error() in backend/src/api/board.py"
Task: "Replace manual logger+raise with handle_service_error() in backend/src/api/workflow.py"
```

## Parallel Example: User Story 2 (Logger Replacements)

```bash
# After T020 (logger.ts created), launch all replacement tasks in parallel:
Task: "Replace console.error in ErrorBoundary.tsx"
Task: "Replace console.error in api.ts"
Task: "Replace console.error and add logger.info in useRealTimeSync.ts"
Task: "Replace console.warn in usePipelineConfig.ts"
Task: "Replace console.warn in AgentsPipelinePage.tsx"
Task: "Add logger.warn to useBoardControls.ts"
Task: "Add logger.warn to useSidebarState.ts"
Task: "Add logger.warn to useAppTheme.ts"
```

## Parallel Example: Cross-Layer

```bash
# After Foundational (Phase 2), these can all start simultaneously:
Backend Developer: US1 (HTTPException migration + handle_service_error activation)
Frontend Developer A: US2 (Logger utility + replacements)
Frontend Developer B: US3 (ErrorAlert component + replacements)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Run baseline tests
2. Complete Phase 2: Add ConflictError to exceptions.py
3. Complete Phase 3: Migrate all HTTPException, activate handle_service_error, fix silent catches
4. **STOP and VALIDATE**: Zero HTTPException imports, 12+ handle_service_error callers, backend tests pass
5. Deploy/demo if ready — backend error contract is unified

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation ready (ConflictError exists)
2. Add US1 (Phase 3) → Backend error contract unified → **MVP!** All API errors follow AppException shape
3. Add US2 (Phase 4) → Frontend logger utility + silent catches fixed → Development visibility improved
4. Add US3 (Phase 5) → ErrorAlert component + inline errors replaced → Consistent error UI
5. Add US4 (Phase 6) → Toast system wired → Mutation errors auto-surfaced to users
6. Add US5 (Phase 7) → Background task correlation IDs → Full observability
7. Add US6 (Phase 8) → Global error capture → Safety net for uncaught errors
8. Phase 9 → Polish, full regression testing, quickstart validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Backend Developer: US1 (Phase 3) → US5 (Phase 7) — all backend changes
   - Frontend Developer A: US2 (Phase 4) → US4 (Phase 6) → US6 (Phase 8) — logger-dependent chain
   - Frontend Developer B: US3 (Phase 5) — ErrorAlert is fully independent
3. Stories complete and integrate independently
4. Phase 9: Full team validates

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 43 |
| **US1 Tasks** | 16 (T004–T019) |
| **US2 Tasks** | 9 (T020–T028) |
| **US3 Tasks** | 4 (T029–T032) |
| **US4 Tasks** | 3 (T033–T035) |
| **US5 Tasks** | 3 (T036–T038) |
| **US6 Tasks** | 1 (T039) |
| **Foundational Tasks** | 1 (T003) |
| **Setup Tasks** | 2 (T001–T002) |
| **Polish Tasks** | 4 (T040–T043) |
| **Parallel Opportunities** | 12+ (8 HTTPException files ‖, 3 handle_service_error files ‖, 8 logger replacements ‖, 3 ErrorAlert replacements ‖, 3 correlation ID tasks ‖, cross-layer US1‖US2‖US3, polish T040‖T041‖T042) |
| **Backend Files Modified** | 14 (exceptions.py, dependencies.py, main.py, settings.py, agents.py, auth.py, board.py, chat.py — unchanged, chores.py, cleanup.py, pipelines.py, signal.py, tools.py, webhooks.py, workflow.py) |
| **Frontend Files Created** | 2 (logger.ts, ErrorAlert.tsx) |
| **Frontend Files Modified** | 12 (App.tsx, main.tsx, ErrorBoundary.tsx, api.ts, useRealTimeSync.ts, usePipelineConfig.ts, AgentsPipelinePage.tsx, useBoardControls.ts, useSidebarState.ts, useAppTheme.ts, ProjectsPage.tsx, IssueRecommendationPreview.tsx, ChatInterface.tsx) |
| **New Dependencies** | 1 (sonner) |
| **MVP Scope** | US1 only (Phases 1–3, tasks T001–T019) |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 is the highest-impact change (79 HTTPException replacements, 12 handle_service_error activations) and constitutes the MVP
- No new backend tests — existing test suite serves as regression gate (FR-016, FR-017)
- The HTTPException→AppException status code mapping is corrected per research.md R1: `ValidationError` is 422 (not 400), `GitHubAPIError` is 502 (not 500). Each replacement requires reading semantic context.
- `chat.py` logger.error calls do NOT have immediate raise patterns — they are excluded from handle_service_error activation per research.md R3
- `workflow.py` handle_service_error activation depends on whether `WorkflowError` is an AppException subclass — verify during implementation per research.md R3
- `McpLimitExceededError` callers remain unchanged — `ConflictError` is for non-MCP 409 conflicts per research.md R2
- Rate-limit banners in ProjectsPage use accent colors (not destructive) and are NOT replaced by ErrorAlert
- Per-mutation `onError` overrides take precedence over the global default — standard TanStack Query v5 behavior
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
