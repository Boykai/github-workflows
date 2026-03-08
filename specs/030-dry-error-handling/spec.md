# Feature Specification: DRY Logging & Error Handling Modernization

**Feature Branch**: `030-dry-error-handling`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "DRY Logging & Error Handling Modernization: Activate Dead Helpers, Migrate HTTPException → AppException, Add Frontend Toast/Logger/ErrorAlert"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Backend Error Contract Unification (Priority: P1)

As a backend developer, I want every API endpoint to use the project's AppException hierarchy (instead of raw HTTPException) and the existing `handle_service_error()` helper (instead of manual logger-plus-raise boilerplate), so that all error responses follow a single, consistent contract and every failure is automatically logged with structured context.

**Why this priority**: This is the highest-impact change. 26+ endpoints currently bypass the AppException hierarchy and 18 places duplicate the exact pattern that `handle_service_error()` already encapsulates. Unifying the backend error contract is the foundation that every other story depends on — it ensures consistent error shapes for the frontend, enables correlation-ID tracing, and removes the largest source of boilerplate in the codebase.

**Independent Test**: Can be verified by running the existing backend test suite and confirming (a) zero remaining raw HTTPException imports in API route files, (b) `handle_service_error()` has non-zero callers, and (c) all error responses include the expected AppException shape with `detail`, `status_code`, and correlation ID.

**Acceptance Scenarios**:

1. **Given** an API route file that previously raised `HTTPException(status_code=400, detail=...)`, **When** the migration is complete, **Then** the route raises the appropriate `ValidationError` from the AppException hierarchy instead.
2. **Given** a catch block that previously used `logger.error(..., exc_info=True)` followed by `raise SomeException(...)`, **When** the refactor is complete, **Then** the block calls `handle_service_error(exc, operation, ErrorClass)` and no manual logger+raise pattern remains.
3. **Given** the `backend/src/exceptions.py` module, **When** a 409-conflict scenario is needed, **Then** a new `ConflictError(AppException)` with `status_code=409` is available and used in place of `HTTPException(status_code=409, ...)`.
4. **Given** any silent `except Exception: pass` block in API route files, **When** the audit is complete, **Then** every such block includes at minimum a `logger.debug()` call so failures are never silently swallowed.

---

### User Story 2 — Frontend Logger Utility & Silent-Catch Remediation (Priority: P2)

As a frontend developer, I want a shared logger utility that wraps console methods and respects the development/production environment flag, and I want all currently silent catch blocks to use it, so that errors are visible during development and can be wired to external tracking in the future without changing call sites.

**Why this priority**: The logger utility is a prerequisite for the toast system (Story 3) and the global error handlers (Story 4). It also fixes the immediate problem of 7+ silent catches that hide failures during development.

**Independent Test**: Can be verified by importing the logger in a test, calling `logger.error()` in dev mode and confirming console output, then calling in production mode and confirming suppression. Silent-catch remediation can be verified by searching for empty catch blocks and confirming none remain.

**Acceptance Scenarios**:

1. **Given** the frontend codebase has no shared logger utility, **When** the utility is created, **Then** `logger.error()`, `logger.warn()`, and `logger.info()` methods are available and delegate to the browser console when in development mode.
2. **Given** a hook with a silent `catch {}` block (e.g., `useBoardControls`, `useSidebarState`, `useAppTheme`, `useMetadata`, `useRealTimeSync`), **When** the remediation is complete, **Then** the catch block calls `logger.error()` or `logger.warn()` with a descriptive message.
3. **Given** 6 existing `console.error()` / `console.warn()` calls scattered across frontend source files, **When** the migration is complete, **Then** all are replaced with the corresponding `logger` method.

---

### User Story 3 — Shared ErrorAlert Component & Inline Error Replacement (Priority: P3)

As a user of the application, I want error messages displayed in the UI to have a consistent look and behavior (including optional retry and dismiss actions), so that I can understand and act on errors without confusion caused by inconsistent styling.

**Why this priority**: This directly improves user experience by replacing ad-hoc inline error displays with a uniform component. It depends on the error contract (Story 1) to ensure consistent error messages, but can be developed in parallel on the frontend.

**Independent Test**: Can be verified by rendering the `ErrorAlert` component in isolation with various prop combinations (`message` only, `message` + `onRetry`, `message` + `onDismiss`, all props) and confirming correct styling and callback behavior.

**Acceptance Scenarios**:

1. **Given** the frontend has no shared error display component, **When** `ErrorAlert` is created, **Then** it accepts `message`, `onRetry?`, `onDismiss?`, and `className?` props and renders with standardized styling consistent with the design system.
2. **Given** a page (e.g., ChatInterface, ProjectsPage, IssueRecommendationPreview) that displays an inline error with custom markup, **When** the migration is complete, **Then** the inline error is replaced by `<ErrorAlert>` with equivalent behavior.
3. **Given** the `onRetry` prop is provided, **When** the user clicks the retry action, **Then** the provided callback is invoked.
4. **Given** the `onDismiss` prop is provided, **When** the user clicks the dismiss action, **Then** the error alert is removed from the UI.

---

### User Story 4 — Toast Notification System for Mutation Errors (Priority: P4)

As a user performing actions that trigger server mutations, I want to see a brief, non-blocking toast notification when a mutation fails, so that I am informed of the failure without losing my place in the UI.

**Why this priority**: Toasts are the standard pattern for transient error feedback in modern web applications. This story depends on the logger utility (Story 2) and benefits from the consistent error messages produced by the backend migration (Story 1).

**Independent Test**: Can be verified by triggering a failing mutation in a test environment and confirming a toast notification appears with the error message, auto-dismisses after a timeout, and does not block other UI interactions.

**Acceptance Scenarios**:

1. **Given** the application has no toast notification system, **When** the toast provider is installed, **Then** a `<Toaster />` component is mounted at the application root with styling consistent with the design system.
2. **Given** a mutation fails and no per-mutation `onError` handler is defined, **When** the default `onError` callback fires, **Then** a toast notification is displayed with the error message and the error is logged via `logger.error()`.
3. **Given** a mutation has its own `onError` handler, **When** that mutation fails, **Then** the per-mutation handler executes and the default toast behavior is bypassed for that mutation.

---

### User Story 5 — Background Task Correlation IDs (Priority: P5)

As an operations engineer reviewing logs, I want background task log entries to include a traceable correlation ID with a `bg-` prefix, so that I can distinguish background-task logs from HTTP-request logs and trace a complete background operation across all its log lines.

**Why this priority**: This is a low-risk, high-value observability improvement that depends on the backend error contract being in place (Story 1) but does not affect the frontend at all.

**Independent Test**: Can be verified by starting the application, allowing background tasks to run, and confirming log output includes correlation IDs matching the pattern `bg-<task-name>-<uuid>` (e.g., `bg-polling-<uuid>`, `bg-cleanup-<uuid>`).

**Acceptance Scenarios**:

1. **Given** the `_polling_watchdog_loop` background task in `main.py`, **When** it executes, **Then** all log lines emitted during that iteration include a `request_id` matching the pattern `bg-polling-<uuid>`.
2. **Given** the `_session_cleanup_loop` background task, **When** it executes, **Then** all log lines include a `request_id` matching `bg-cleanup-<uuid>`.
3. **Given** the `_auto_start_copilot_polling` background task, **When** it executes, **Then** all log lines include a `request_id` matching `bg-copilot-<uuid>`.

---

### User Story 6 — Global Unhandled Error Capture (Priority: P6)

As a developer, I want unhandled promise rejections and uncaught errors in the browser to be captured and routed through the shared logger, so that no frontend error goes completely unnoticed.

**Why this priority**: This is a safety-net story that catches anything the other stories miss. It depends on the logger utility (Story 2) being available.

**Independent Test**: Can be verified by deliberately triggering an unhandled promise rejection in a test and confirming `logger.error()` is called with the rejection reason.

**Acceptance Scenarios**:

1. **Given** the application entry point (`main.tsx`), **When** the app initializes, **Then** global handlers for `unhandledrejection` and `window.onerror` are registered.
2. **Given** an unhandled promise rejection occurs, **When** the `unhandledrejection` handler fires, **Then** the rejection reason is passed to `logger.error()`.
3. **Given** an uncaught error occurs, **When** the `window.onerror` handler fires, **Then** the error details are passed to `logger.error()`.

---

### Edge Cases

- What happens when `handle_service_error()` receives an exception that is itself an AppException subclass? It should re-raise without double-wrapping.
- What happens when a background task's correlation ID generation fails (e.g., UUID library unavailable)? The task should continue with a fallback ID such as `bg-<task-name>-unknown`.
- What happens when the toast notification system fails to render (e.g., Toaster not mounted)? Errors should still be logged via `logger.error()` regardless of toast display status.
- What happens when `logger.error()` is called before the logger module is initialized? The logger should be stateless and immediately functional upon import (no initialization step required).
- What happens when an API endpoint raises an exception type not in the mapping (e.g., status 422)? The global exception handler should catch unhandled AppException subclasses and return a structured error response; any truly unexpected exception should return a generic 500 with correlation ID.
- What happens when multiple mutations fail simultaneously? Each failure should produce its own toast notification, and the toast system should queue or stack them without losing any.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Backend**

- **FR-001**: System MUST replace all manual `logger.error(..., exc_info=True)` + `raise SomeException(...)` patterns (18 instances across `cleanup.py`, `workflow.py`, `board.py`, `agents.py`, `chores.py`, `chat.py`) with calls to the existing `handle_service_error(exc, operation, ErrorClass)` in `logging_utils.py`.
- **FR-002**: System MUST migrate all raw `HTTPException` usages (26+ instances across `agents.py`, `chores.py`, `auth.py`, `signal.py`, `tools.py`, `pipelines.py`, `webhooks.py`, `dependencies.py`) to the appropriate AppException subclass using the mapping: 400→`ValidationError`, 401→`AuthenticationError`, 403→`AuthorizationError`, 404→`NotFoundError`, 409→`ConflictError`, 500→`GitHubAPIError`.
- **FR-003**: System MUST add a `ConflictError` class inheriting from `AppException` with `status_code=409` to the exceptions module. No other changes to the AppException hierarchy are required.
- **FR-004**: System MUST audit all `except` blocks across backend API route files and ensure none silently swallow exceptions. The known silent block in `settings.py` MUST receive at minimum a `logger.debug()` call.
- **FR-005**: System MUST inject a synthetic correlation ID context variable into the three background task loops (`_polling_watchdog_loop`, `_session_cleanup_loop`, `_auto_start_copilot_polling`) using a `bg-<task-name>-<uuid>` pattern so that all log lines emitted during background task execution are traceable.
- **FR-006**: After migration, zero API route files MUST contain `from fastapi import HTTPException` or `from starlette.exceptions import HTTPException` imports (the global exception handler in `main.py` and any middleware may still reference HTTPException for catch-all purposes).

**Phase 2 — Frontend**

- **FR-007**: System MUST provide a logger utility module exposing `logger.error()`, `logger.warn()`, and `logger.info()` methods that wrap browser console methods and only emit output when running in development mode.
- **FR-008**: System MUST replace all existing `console.error()` and `console.warn()` calls in frontend source files (6 instances) with the corresponding `logger` method.
- **FR-009**: System MUST add `logger.error()` or `logger.warn()` calls to all currently silent catch blocks in frontend hooks (`useBoardControls`, `useSidebarState`, `useAppTheme`, `useMetadata`, `useRealTimeSync`).
- **FR-010**: System MUST provide a shared `ErrorAlert` component accepting `message` (required), `onRetry?`, `onDismiss?`, and `className?` props, styled consistently with the existing design system.
- **FR-011**: System MUST replace inline error displays in `ChatInterface`, `IssueRecommendationPreview`, `VoiceInputButton`, `ProjectsPage`, `AgentPresetSelector`, and `McpSettings` with the shared `ErrorAlert` component.
- **FR-012**: System MUST install a toast notification library and mount its provider at the application root, with default styles matching the design system.
- **FR-013**: System MUST configure a default `onError` callback on the query client that logs the error via `logger.error()` and displays a toast notification with the error message for unhandled mutation errors.
- **FR-014**: Per-mutation `onError` overrides MUST continue to be respected; the default callback only fires when no override is provided.
- **FR-015**: System MUST register global handlers for `unhandledrejection` and `window.onerror` in the application entry point, routing errors through `logger.error()`.

**Phase 3 — Verification**

- **FR-016**: The existing backend test suite MUST pass with zero regressions after the HTTPException→AppException migration.
- **FR-017**: The existing frontend test suite MUST pass with zero regressions after all frontend changes.
- **FR-018**: A post-migration audit MUST confirm zero remaining `HTTPException` imports in API route files and non-zero callers of `handle_service_error()`.

### Key Entities

- **AppException**: Base exception class for all application errors; carries `status_code`, `detail`, and correlation ID. Existing subclasses: `ValidationError` (400), `AuthenticationError` (401), `AuthorizationError` (403), `NotFoundError` (404), `GitHubAPIError` (500).
- **ConflictError**: New subclass of `AppException` with `status_code=409`, representing resource-conflict scenarios (e.g., duplicate creation, concurrent modification).
- **ErrorAlert**: Shared frontend component for displaying errors in the UI with optional retry and dismiss callbacks.
- **Logger Utility**: Frontend module wrapping browser console methods, gated by an environment flag, serving as the single logging entry point for the entire frontend.
- **Toaster**: Application-root toast notification provider for transient, non-blocking user feedback on mutation errors.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero raw `HTTPException` imports remain in any backend API route file after migration (down from 26+).
- **SC-002**: `handle_service_error()` has 18+ call sites after activation (up from zero callers).
- **SC-003**: Zero silent `catch` / `except` blocks remain in both backend API route files and frontend hook files after remediation.
- **SC-004**: 100% of backend error responses include a structured payload with `detail`, `status_code`, and correlation ID — verified by the existing test suite passing without regression.
- **SC-005**: All inline error displays in the 6 identified frontend components are replaced by the shared `ErrorAlert` component, reducing error-display code duplication by at least 80%.
- **SC-006**: Any unhandled mutation error produces a visible toast notification within 1 second of the failure, without requiring per-mutation boilerplate.
- **SC-007**: All background task log entries include a correlation ID matching the `bg-<task-name>-<uuid>` pattern, enabling end-to-end tracing of background operations.
- **SC-008**: The existing backend and frontend test suites pass with zero regressions after all changes.

## Assumptions

- The existing `handle_service_error()` function in `logging_utils.py` is correct and complete — it only needs callers, not modifications.
- The existing global exception handler in `main.py` already handles `AppException` subclasses and returns structured responses; adding `ConflictError` requires no handler changes.
- The `board.py` file serves as the reference implementation for correct AppException usage on the backend.
- No new backend logging library is needed — the existing structured logging infrastructure is production-grade.
- The `sonner` library is the chosen toast solution — lightweight, modern, and compatible with the existing frontend stack.
- The `request_id_var` context variable from `middleware/request_id.py` is the correct mechanism for injecting correlation IDs into background tasks.
- The logger utility in production mode should suppress `logger.info()` and `logger.warn()` output but always emit `logger.error()` regardless of mode, as errors should never be silently suppressed even in production.
- Per-mutation `onError` overrides in TanStack Query take precedence over the global default — this is standard TanStack Query behavior and does not require custom logic.
