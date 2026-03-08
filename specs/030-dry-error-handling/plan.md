# Implementation Plan: DRY Logging & Error Handling Modernization

**Branch**: `030-dry-error-handling` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/030-dry-error-handling/spec.md`

## Summary

Standardize error handling across both backend and frontend layers. On the backend, activate the existing dead-code `handle_service_error()` helper (currently zero callers despite 12 places replicating its pattern), migrate 79 raw `HTTPException` usages across 8 files to the AppException hierarchy, add a general-purpose `ConflictError(409)` exception, fix silent catch blocks, and inject correlation IDs into background tasks. On the frontend, create a shared logger utility gated by `import.meta.env.DEV`, introduce a reusable `<ErrorAlert>` component replacing scattered inline error displays, install `sonner` for toast notifications wired to TanStack QueryClient's default `onError`, and register global unhandled error handlers. The approach reuses existing infrastructure — no new backend logging libraries, no changes to the global exception handler, and the `board.py` exemplar as the reference pattern.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript ~5.9 (frontend)
**Primary Dependencies**: FastAPI 0.135, Pydantic v2.12, aiosqlite 0.22 (backend); React 19.2, TanStack Query v5.90, Tailwind CSS v4, Vite 7.3 (frontend); sonner (new frontend dependency)
**Storage**: SQLite with WAL mode (aiosqlite) — no schema changes required
**Testing**: pytest + pytest-asyncio (backend), Vitest 4 + Testing Library (frontend)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: No performance-sensitive changes; error handling paths are not on the hot path
**Constraints**: No new backend logging library; existing structured logging is production-grade; `handle_service_error()` stays as-is (just needs callers); `board.py` is the reference pattern
**Scale/Scope**: ~8 modified backend files, ~3 new frontend files, ~12 modified frontend files; 79 HTTPException replacements, 12 handle_service_error activations, 1 new exception class, 1 new npm dependency (sonner)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 6 prioritized user stories (P1–P6), Given-When-Then acceptance scenarios, 18 functional requirements, 8 success criteria, edge cases, and assumptions |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated; existing test suites must pass with zero regressions (FR-016, FR-017) |
| **V. Simplicity/DRY** | ✅ PASS | This feature *is* DRY — eliminates boilerplate by activating existing helpers, centralizing error display, and standardizing patterns. No new abstractions; reuses existing `handle_service_error()`, `AppException` hierarchy, and `ErrorBoundary` patterns. Single new npm dependency (sonner) is lightweight and purpose-built. |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-018) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | No new tests mandated; existing test suites serve as regression gates |
| **V. Simplicity/DRY** | ✅ PASS | All changes are mechanical refactors (search-and-replace patterns) or small new utilities. No new abstraction layers. `ConflictError` follows the exact same pattern as existing `NotFoundError`, `AuthenticationError`, etc. Logger utility is ~20 lines. ErrorAlert is a simple presentational component. sonner is a single `<Toaster />` mount point. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/030-dry-error-handling/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R6)
├── data-model.md        # Phase 1: Entity definitions, exception hierarchy, component types
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── error-responses.md  # Phase 1: Error response shape contracts
│   └── components.md       # Phase 1: Frontend component interface contracts
├── checklists/
│   └── requirements.md     # Specification quality checklist (complete)
└── tasks.md                # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── exceptions.py                    # MODIFIED: Add ConflictError class
│   ├── logging_utils.py                 # UNCHANGED: handle_service_error() already exists (just gains callers)
│   ├── main.py                          # MODIFIED: Add correlation IDs to background tasks
│   ├── dependencies.py                  # MODIFIED: Migrate HTTPException → AppException
│   ├── middleware/
│   │   └── request_id.py                # UNCHANGED: request_id_var already exists (referenced by background tasks)
│   └── api/
│       ├── agents.py                    # MODIFIED: Migrate 16 HTTPException + 3 manual logger+raise patterns
│       ├── auth.py                      # MODIFIED: Migrate 5 HTTPException usages
│       ├── board.py                     # MODIFIED: Replace 2 manual logger+raise with handle_service_error
│       ├── chat.py                      # UNCHANGED: logger.error calls don't have immediate raise patterns
│       ├── chores.py                    # MODIFIED: Migrate 18 HTTPException + 3 manual logger+raise patterns
│       ├── cleanup.py                   # MODIFIED: Replace 3 manual logger+raise with handle_service_error
│       ├── pipelines.py                 # MODIFIED: Migrate 7 HTTPException usages
│       ├── settings.py                  # MODIFIED: Fix silent except block at L156
│       ├── signal.py                    # MODIFIED: Migrate 11 HTTPException usages
│       ├── tools.py                     # MODIFIED: Migrate 12 HTTPException usages
│       ├── webhooks.py                  # MODIFIED: Migrate 3 HTTPException usages
│       └── workflow.py                  # MODIFIED: Replace 1 manual logger+raise with handle_service_error
└── tests/
    └── unit/                            # UNCHANGED: Existing tests serve as regression gate

frontend/
├── src/
│   ├── utils/
│   │   └── logger.ts                    # NEW: Shared logger utility wrapping console methods
│   ├── components/
│   │   └── common/
│   │       ├── ErrorAlert.tsx           # NEW: Shared error display component
│   │       └── ErrorBoundary.tsx        # MODIFIED: Replace console.error with logger.error
│   ├── hooks/
│   │   ├── useBoardControls.ts          # MODIFIED: Add logger to silent catches
│   │   ├── useSidebarState.ts           # MODIFIED: Add logger to silent catches
│   │   ├── useAppTheme.ts              # MODIFIED: Add logger to silent catch
│   │   ├── useRealTimeSync.ts          # MODIFIED: Replace console.error with logger.error
│   │   └── usePipelineConfig.ts        # MODIFIED: Replace console.warn with logger.warn
│   ├── pages/
│   │   ├── ProjectsPage.tsx             # MODIFIED: Replace inline error displays with ErrorAlert
│   │   └── AgentsPipelinePage.tsx       # MODIFIED: Replace console.warn with logger.warn
│   ├── services/
│   │   └── api.ts                       # MODIFIED: Replace console.error with logger.error
│   ├── App.tsx                          # MODIFIED: Add Toaster, add mutation onError default
│   └── main.tsx                         # MODIFIED: Add global unhandled error handlers
└── tests/                               # UNCHANGED: Existing tests serve as regression gate
```

**Structure Decision**: Web application (frontend/ + backend/). All changes are modifications to existing files or small new utility files. No new directories created except `frontend/src/utils/` (if it doesn't exist). The feature is primarily a refactoring effort — replacing scattered anti-patterns with calls to existing/new centralized utilities. No database schema changes. No new backend endpoints.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Corrected HTTPException mapping (see research.md R1) | Existing `ValidationError` is 422, not 400; `GitHubAPIError` is 502, not 500. Mapping must match existing status codes to avoid behavioral changes. | Changing existing exception status codes (rejected: would break existing consumers and tests) |
| `ConflictError` coexists with `McpLimitExceededError` | Both are 409, but `McpLimitExceededError` is MCP-specific. `ConflictError` is the general-purpose 409 for non-MCP conflicts. | Reusing `McpLimitExceededError` for all 409s (rejected: semantically wrong — "MCP limit exceeded" is not a general conflict) |
| sonner for toasts (new dependency) | Lightweight (~3KB gzip), zero-config, works with React 19, supports custom styling via className. No existing toast library in the project. | react-hot-toast (rejected: less maintained), custom implementation (rejected: YAGNI — sonner covers all needs) |
