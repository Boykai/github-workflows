# Research: Code Quality Check

**Feature**: 032-code-quality-check
**Date**: 2026-03-10
**Status**: Complete

## Phase 1: Silent Failures & Security

### R-001: Exception Handling Patterns in Backend

**Decision**: Audit and narrow all 98 bare `except Exception:` blocks; replace zero `except: pass` blocks (none found)

**Rationale**: The codebase has 98 bare `except Exception:` blocks across 32 files (most commonly in services/chores/service.py with 11, services/workflow_orchestrator/config.py with 11, and services/copilot_polling/pipeline.py with 7). While zero `except: pass` blocks exist (the original estimate of 32 may have counted logging-only handlers), the bare `Exception` catches without specific types still mask the root cause of failures and reduce debuggability. Narrowing to specific exception types enables targeted testing and reveals unexpected failure modes.

**Alternatives considered**:

- Leave as-is with logging: Rejected — broad catches hide unexpected exception types
- Add only `as e` bindings: Insufficient — knowing the exception instance is helpful but does not narrow the catch scope
- Remove all try/except blocks: Too aggressive — graceful degradation is required for service resiliency

### R-002: Signal Chat Exception Leakage

**Decision**: Wrap the 3 `TODO(bug-bash)` locations in `signal_chat.py` (lines 175, 540, 820) with `safe_error_response()` from `logging_utils.py`

**Rationale**: All three locations format exception messages directly into Signal API replies (e.g., `f"Error processing #agent command: {exc}"`). Even though Signal is a 1:1 private channel, leaking internal details (Python tracebacks, internal variable names, file paths) violates defense-in-depth. The existing `safe_error_response()` utility already logs full details server-side and returns a generic user-facing string.

**Alternatives considered**:

- Keep as-is (private channel argument): Rejected — security principle should not depend on channel privacy assumptions
- Custom per-location sanitization: Rejected — `safe_error_response()` already provides the exact pattern needed

### R-003: CORS Configuration

**Decision**: Restrict `allow_methods` from `["*"]` to `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`

**Rationale**: The `TODO(bug-bash)` in `main.py` (line 388) documents the wildcard as intentionally permissive. Origin validation is already in place. Restricting methods to the actual set used by the application reduces attack surface without breaking functionality. `allow_headers` can remain `["*"]` to avoid breaking custom headers from the frontend or integrations, unless a specific header allowlist is identified.

**Alternatives considered**:

- Restrict both methods and headers: Deferred for headers — enumerating all headers requires a frontend audit and risks breaking integrations
- Keep wildcards: Rejected — methods are a known finite set and easy to enumerate

## Phase 2: DRY Consolidation

### R-004: Repository Resolution Unification

**Decision**: Standardize all call sites to `utils.resolve_repository()`. Remove `workflow.py::_get_repository_info()` (lines 89-114)

**Rationale**: `_get_repository_info()` is a synchronous, cache-only function that returns partial results (owner only, empty repo name). `resolve_repository()` is async with a proper 3-step fallback (GraphQL → DB → .env) and raises `ValidationError` on failure. The 45 existing calls to `resolve_repository()` across api/ files confirm it is already the dominant pattern. Two inline parsing locations in `board.py` (lines 388, 445) use `repo_key.split("/", 1)` which is a different pattern (parsing already-resolved keys, not resolution).

**Alternatives considered**:

- Keep `_get_repository_info()` for sync contexts: Rejected — all API endpoints are async; no sync callers exist
- Create a third resolver: Rejected — violates DRY; one canonical function is sufficient

### R-005: Error Handling Helper Adoption

**Decision**: Adopt `handle_service_error()` and `safe_error_response()` from `logging_utils.py` across all API route files

**Rationale**: Both functions exist (lines 215-278 of `logging_utils.py`) but are currently unused. Each API route independently implements the same try/log/raise pattern. `handle_service_error()` logs the full exception with traceback and raises an `AppException` subclass with a safe message. `safe_error_response()` logs and returns a safe string for non-raising contexts.

**Alternatives considered**:

- Create new error handling middleware: Over-engineering — the existing helpers are sufficient
- Use FastAPI exception handlers only: Insufficient — does not cover service-layer errors that need domain-specific error classes

### R-006: Cache-or-Fetch Pattern

**Decision**: Extract a `cached_fetch()` async helper from the repeated pattern in `projects.py`, `board.py`, and `chat.py`

**Rationale**: Both `projects.py` (lines 85-143) and `board.py` (lines 200-289) implement identical patterns: check cache → if miss, fetch from GitHub → cache result → on error, serve stale. `chat.py` (lines 220-235) is read-only (cache lookup for context) and may not benefit from the helper. The helper should support: cache key, async fetch function, refresh flag, and stale fallback.

**Alternatives considered**:

- Decorator-based caching (e.g., `@cached`): Rejected — the pattern involves stale-fallback logic that doesn't fit a simple decorator
- Use a third-party caching library: Rejected — the existing `InMemoryCache` is sufficient; adding dependencies for this is unnecessary

### R-007: Validation Guard Extraction

**Decision**: Create `require_selected_project(session) -> str` in `dependencies.py`

**Rationale**: The pattern `if not session.selected_project_id: raise ValidationError(...)` appears in at least 5 endpoints with inconsistent error messages. A single guard function ensures consistent messages and can be extended with additional checks (e.g., project access verification).

**Alternatives considered**:

- FastAPI `Depends()` with a dedicated dependency: Viable alternative but more complex for a simple validation check
- Pydantic model validation: Rejected — the check is at the session level, not request body level

### R-008: Frontend Dialog/Modal Consolidation

**Decision**: Use `ConfirmationDialog` (202 lines, fully accessible) as the base composition pattern for all modals

**Rationale**: `ConfirmationDialog` already implements focus trapping, Escape key handling, ARIA attributes (`aria-modal`, `aria-labelledby`, `aria-describedby`), async loading states, error display, backdrop click handling, and tab navigation. Other modal implementations should compose this base to ensure consistent accessibility.

**Alternatives considered**:

- Radix UI Dialog primitive: Would require adding a new dependency; `ConfirmationDialog` already provides the needed patterns
- Headless UI: Same concern — additional dependency when existing solution is sufficient

### R-009: cn() Standardization

**Decision**: Replace all template literal className constructions with `cn()` from `lib/utils`

**Rationale**: 25 files use template literal classNames while 18 files use `cn()`. The `cn()` utility combines `clsx` and `tailwind-merge` to properly handle Tailwind class conflicts. Template literals cannot merge conflicting Tailwind classes (e.g., `p-2` and `p-4` both remain).

**Alternatives considered**:

- Keep both patterns: Rejected — inconsistency and Tailwind merge issues
- Use clsx directly: Rejected — `cn()` wraps clsx with tailwind-merge, which is needed for Tailwind

## Phase 3: Module Decomposition

### R-010: GitHub Projects Service Split

**Decision**: Split `github_projects/service.py` (5,220 lines) into 5 focused modules

**Rationale**: The file contains all GitHub API operations spanning issues, PRs, Copilot, board data, and shared infrastructure. At 5,220 lines, it far exceeds the 500 LOC guideline. The proposed split into `issues.py`, `pull_requests.py`, `copilot.py`, `board.py`, and `service.py` (facade) follows the existing method groupings visible in the file.

**Alternatives considered**:

- Fewer modules (3): Rejected — PRs and issues have distinct lifecycles; Copilot operations are a separate domain
- More modules (8+): Over-splitting — the proposed 5 covers the natural domain boundaries

### R-011: Frontend API Service Split

**Decision**: Split `services/api.ts` (1,128 lines) into domain modules with a re-export index

**Rationale**: The file contains 50+ functions covering all API domains. The proposed split (`client.ts`, `projects.ts`, `chat.ts`, `agents.ts`, `tools.ts`, `board.ts`, `index.ts`) follows the natural API domain boundaries and maintains backward compatibility via re-exports.

**Alternatives considered**:

- Keep as single file with better organization: Rejected — 1,128 lines exceeds the 400 LOC guideline
- Generate from OpenAPI spec: Future optimization, not a refactoring strategy

### R-012: Large Hooks Decomposition

**Decision**: Decompose hooks exceeding 400 LOC into focused sub-hooks

**Rationale**: `usePipelineConfig.ts` (616 LOC), `useChat.ts` (385 LOC), and `useBoardControls.ts` (375 LOC) mix state management, mutations, and validation logic. Extracting sub-hooks (e.g., `usePipelineState` + `usePipelineMutations` + `usePipelineValidation`) follows React best practices for hook composition.

**Alternatives considered**:

- Context-based extraction: Over-engineering for this scope
- Leave useChat and useBoardControls (under 400): Viable — they are close to the threshold; focus on usePipelineConfig first

## Phase 4: Type Safety

### R-013: Backend Return Type Hints

**Decision**: Add explicit return type annotations to all public functions in `services/` and `api/`; use `TypedDict` for structured dict returns

**Rationale**: Python 3.12+ supports modern type syntax. 24 functions are missing return types. Generic `dict` and `list` returns lose type information at boundaries. `TypedDict` provides compile-time checking with zero runtime overhead.

**Alternatives considered**:

- Pydantic response models only: Insufficient — service-layer functions also need type annotations
- dataclasses: Viable but `TypedDict` is more appropriate for dict-like returns since the codebase already returns dicts

### R-014: Frontend Strict TypeScript Checks

**Decision**: Enable `noUnusedLocals: true` and `noUnusedParameters: true` in `tsconfig.json`

**Rationale**: Currently both are `false` (lines 15-16 of `tsconfig.json`). The existing ESLint config already enforces `@typescript-eslint/no-unused-vars` with `_` prefix exception, so most code should already be compliant. Enabling TypeScript-level checks provides a second safety net.

**Alternatives considered**:

- ESLint-only enforcement: Already in place but TypeScript compiler checks catch more cases
- Enable all strict flags at once: Too aggressive — incremental strictness is safer

### R-015: Unsafe Type Casts

**Decision**: Replace all `as unknown as Record<string, unknown>` casts with proper types

**Rationale**: Search found zero occurrences of this exact pattern in the current codebase. The issue may have been resolved in a prior refactor or the pattern may exist in a different form. A targeted search for `as unknown` should be performed during implementation to catch remaining unsafe casts.

**Alternatives considered**:

- Runtime validation (zod): Adds a dependency; appropriate for API boundaries but heavy for internal type assertions
- Type guards: Best practice for narrowing union types; should be used where discriminated unions are defined

## Phase 5: Technical Debt

### R-016: Singleton to DI Migration

**Decision**: Migrate module-level singletons to FastAPI `app.state` / `Depends()` pattern

**Rationale**: Found 4+ singleton patterns: `ai_agent.py` (`_ai_agent_service_instance`), `workflow_orchestrator/orchestrator.py` (`_orchestrator_instance`), `database.py` (`_connection`), `cache.py` (`cache = InMemoryCache()`). `dependencies.py` already implements a hybrid pattern (app.state with module-level fallback) that can serve as the migration template. The `github_projects/service.py` has an explicit TODO for this (line 5215).

**Alternatives considered**:

- Third-party DI framework (dependency-injector): Over-engineering — FastAPI's built-in DI is sufficient
- Keep hybrids: Current state is transitional; completing the migration eliminates the fallback complexity

### R-017: Anti-Pattern — Dynamic Import via Built-in

**Decision**: Replace `__import__("time").time()` with `import time; time.time()` in `template_builder.py` (line 245)

**Rationale**: The `__import__()` call bypasses standard import mechanisms, confuses IDE tooling, and makes dependency tracking harder. This is a simple one-line fix.

**Alternatives considered**: None — standard imports are the only acceptable alternative

### R-018: Migration Prefix Duplicates

**Decision**: Add duplicate-detection with a startup warning; defer renumbering to a separate migration strategy

**Rationale**: The `TODO(bug-bash)` in `database.py` (lines 213-221) documents that prefixes 013, 014, and 015 each have two files. The `_run_migrations()` function tracks progress by version number, so the second file sharing a prefix is silently skipped. Renumbering requires a reconciliation strategy for existing production databases. A duplicate-detection warning at startup is the safest first step.

**Alternatives considered**:

- Immediate renumbering: Risk — existing databases have schema_version set based on old numbering
- Ignore: Rejected — silent skipping of migrations is a data integrity risk

### R-019: Chat Persistence

**Decision**: Migrate in-memory chat stores (`_messages`, `_proposals`, `_recommendations` in `chat.py` lines 79-91) to SQLite using existing migration 012

**Rationale**: Migration `012_chat_persistence.sql` already created the necessary tables. The in-memory dicts are an MVP implementation marked with `TODO(018-codebase-audit-refactor)`. Bounded retention (1,000 messages per session default) prevents unbounded storage growth.

**Alternatives considered**:

- Redis: Over-engineering for a single-server deployment using SQLite
- File-based persistence: Rejected — SQLite is already the data store and migration exists

### R-020: Unused Dependencies and Test Consolidation

**Decision**: Remove `jsdom` from devDependencies; merge `src/tests/` into `src/test/`

**Rationale**: `happy-dom` (v20.8.0) is the active test environment. `jsdom` (v28.1.0) is installed but unused. `src/test/` contains setup files (setup.ts, test-utils.tsx, a11y-helpers.ts, factories/) while `src/tests/` contains one test file (`utils/formatAgentName.test.ts`). Consolidation into `src/test/` is straightforward.

**Alternatives considered**:

- Keep both test frameworks: Rejected — unnecessary dependency weight
- Merge into `src/tests/`: Rejected — `src/test/` has more files and the setup infrastructure

## Phase 6: Performance & Observability

### R-021: Frontend Memoization

**Decision**: Add `useMemo` for expensive computations and `React.memo` for pure child components

**Rationale**: Pages like `AgentsPage` rebuild derived data structures every render. `useMemo` prevents re-computation when dependencies haven't changed. `React.memo` prevents re-rendering of child components when props haven't changed.

**Alternatives considered**:

- Reselect/createSelector: Adds a dependency; `useMemo` is built-in and sufficient
- Virtualization for large lists: Complementary but separate concern

### R-022: AbortController Integration

**Decision**: Pass `AbortSignal` from TanStack Query to the `request<T>()` function in `api.ts`

**Rationale**: TanStack React Query (already in use, vendored in vite config) provides signal support. The `request<T>()` function needs to accept and forward the signal to `fetch()` calls. This prevents memory leaks from stale state updates on unmounted components.

**Alternatives considered**:

- Manual cleanup in useEffect: Error-prone and doesn't integrate with React Query's built-in cancellation
- Axios with CancelToken: Would require adding Axios as a dependency; native AbortController is sufficient

### R-023: Bounded In-Memory Structures

**Decision**: Add explicit max-size limits to all in-memory caches and stores

**Rationale**: `cache.py` uses a simple unbounded dict with TTL-only expiration. `workflow.py` already uses `BoundedDict(maxlen=1000)` for request deduplication. The `BoundedDict` pattern should be extended to the main `InMemoryCache` and chat stores.

**Alternatives considered**:

- `functools.lru_cache`: Not suitable for async operations with complex keys
- Third-party cache (cachetools): Adds a dependency; `BoundedDict` is already in the codebase

## Phase 7: Testing & Linting

### R-024: Backend Exception Test Coverage

**Decision**: Add specific test cases for each narrowed exception type after Phase 1 changes

**Rationale**: After narrowing `except Exception` to specific types, each type needs a dedicated test case. The existing test infrastructure (pytest + pytest-asyncio, comprehensive fixtures in conftest.py) supports this.

**Alternatives considered**:

- Property-based testing (Hypothesis): Complementary but not the primary approach for exception testing
- Integration tests only: Insufficient — unit tests for specific exception paths are needed

### R-025: Frontend Page and Component Tests

**Decision**: Add render tests for all page components and `jest-axe` accessibility assertions

**Rationale**: Page components (`AgentsPage`, `ProjectsPage`, `AppPage`) are largely untested. Only ~10 of 46 hooks are tested. The test infrastructure (Vitest + React Testing Library + happy-dom) is already in place. `a11y-helpers.ts` exists in `src/test/`.

**Alternatives considered**:

- E2E tests only (Playwright): Already exists for integration; unit/render tests needed for faster feedback
- Snapshot tests: Fragile for components with dynamic content

### R-026: ESLint Enhancement

**Decision**: Add `eslint-plugin-import` for import ordering and `eslint-plugin-react` for React-specific rules

**Rationale**: Current ESLint config (flat config, 26 lines) only has `react-hooks` and `jsx-a11y` plugins. Missing import ordering and React-specific rules that catch common mistakes.

**Alternatives considered**:

- Biome: Would require migration from ESLint; not appropriate for this scope
- Manual enforcement: Error-prone; automated linting is preferred

### R-027: Bundle Analysis

**Decision**: Add `rollup-plugin-visualizer` to Vite config for CI bundle size tracking

**Rationale**: Vite config (54 lines) already has manual chunk splitting for vendors. Adding bundle analysis enables data-driven optimization decisions. The plugin integrates directly with Vite's Rollup-based build.

**Alternatives considered**:

- webpack-bundle-analyzer: Vite uses Rollup, not webpack
- source-map-explorer: Works but less integrated with Vite's build pipeline
