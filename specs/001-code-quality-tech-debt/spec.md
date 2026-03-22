# Feature Specification: Code Quality & Technical Debt — Cache Wrapper Extraction, Error Handling Consolidation & Dead Code Sweep

**Feature Branch**: `001-code-quality-tech-debt`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "Theme 1: Code Quality & Technical Debt — Cache Wrapper Extraction, Error Handling Consolidation & Dead Code Sweep"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Global Cache Pattern Consolidation (Priority: P1)

As a backend engineer working on a service that fetches data from external APIs, I want a single `cached_fetch()` async helper that encapsulates the repeated cache-get → freshness-check → fetch → cache-set-with-TTL → stale-fallback pattern so that I can add new cached endpoints in one call instead of duplicating 8–10 lines of boilerplate each time, and so that cache-related bugs are fixed in one place rather than across 10 scattered call sites.

**Why this priority**: This pattern is the most duplicated piece of logic in the service layer (~80 lines across 10 call sites in 5 files). Consolidating it delivers the largest single line-of-code reduction, eliminates the highest number of copy-paste drift risks, and establishes the foundational abstraction that all future cache-backed fetches will use.

**Independent Test**: Can be fully tested by invoking any single cached endpoint (e.g., fetching board data), verifying that a cache miss triggers the upstream fetch and stores the result with the correct TTL, and that a subsequent call within the TTL window returns the cached value without an upstream call. Stale-fallback behavior can be tested independently by simulating an upstream failure after a prior successful fetch.

**Acceptance Scenarios**:

1. **Given** the global cache has no entry for a requested key, **When** `cached_fetch()` is called, **Then** the provided fetch function is invoked, the result is stored in cache with the specified TTL, and the result is returned to the caller.
2. **Given** the global cache has a fresh (non-expired) entry for the requested key, **When** `cached_fetch()` is called, **Then** the cached value is returned without invoking the fetch function.
3. **Given** the global cache entry has expired and the fetch function raises an error, **When** `cached_fetch()` is called with stale-fallback enabled, **Then** the stale cached value is returned and the error is logged.
4. **Given** the global cache entry has expired and the fetch function raises an error, **When** `cached_fetch()` is called with stale-fallback disabled, **Then** the error propagates to the caller.
5. **Given** all 10 existing call sites have been refactored to use `cached_fetch()`, **When** the full test suite is executed, **Then** all existing tests pass with no behavioral changes observable at API boundaries (identical cache TTLs, stale-fallback semantics, and response shapes).

---

### User Story 2 - Cycle Cache Pattern Consolidation (Priority: P1)

As a backend engineer working with the `GitHubProjectsService`, I want a single `_cycle_cached()` instance method that encapsulates the repeated cycle-cache-get → hit-count-check → fetch → cycle-cache-set pattern so that the 7 call sites across 5 files are reduced to one-liner invocations and future cycle-cached lookups require no boilerplate.

**Why this priority**: This is a parallel, independent consolidation of the second most duplicated cache pattern. It is low-risk, scoped to one service class, and can be developed and merged alongside Story 1 without conflicts.

**Independent Test**: Can be fully tested by calling any cycle-cached method (e.g., fetching pull request cycle data), verifying cache-miss triggers the upstream fetch, cache-hit returns stored data, and hit-count thresholds behave identically to the current inline implementation.

**Acceptance Scenarios**:

1. **Given** the cycle cache has no entry for the requested key, **When** `_cycle_cached()` is called, **Then** the provided fetch function is invoked, the result is stored in the cycle cache, and the result is returned.
2. **Given** the cycle cache has an entry for the requested key within the hit-count threshold, **When** `_cycle_cached()` is called, **Then** the cached value is returned without invoking the fetch function.
3. **Given** all 7 existing call sites have been refactored to use `_cycle_cached()`, **When** the full test suite is executed, **Then** all existing tests pass with no behavioral changes.

---

### User Story 3 - Error Handling Consolidation (Priority: P2)

As a backend engineer maintaining API error boundaries, I want the 8 remaining catch-log-raise patterns migrated to the existing `handle_service_error()` helper (with an optional `error_cls` parameter for non-standard exception types) so that error logging format, context capture, and re-raise behavior are uniform across all service-layer error paths, and so that the `ai_agent.py` ValueError convention is preserved without a silent breaking change.

**Why this priority**: This story depends on the stability established by Stories 1 and 2 (Phase A) because it touches overlapping files. It delivers the second-largest line reduction (~15–20 lines) and eliminates the riskiest class of boilerplate — inconsistent error handling — which can cause silent data loss or misleading log output.

**Independent Test**: Can be tested by triggering an error in each of the 8 call sites (3 in `board.py`, 4 in `ai_agent.py`, 1 in `agents/service.py`) and verifying that the exception type, message, and logged context are identical before and after migration.

**Acceptance Scenarios**:

1. **Given** `handle_service_error()` is extended with an `error_cls` parameter, **When** a service error occurs in `ai_agent.py`, **Then** a `ValueError` is raised (not an `AppException` subclass), preserving the existing API error-response shape.
2. **Given** the 3 call sites in `board.py` are migrated to `handle_service_error()`, **When** a service error occurs, **Then** a `GitHubAPIError` is raised with the same message and context as the original inline pattern.
3. **Given** the bare `raise` in `agents/service.py` is migrated, **When** a service error occurs, **Then** the original exception is re-raised with identical behavior to the current bare raise.
4. **Given** all 8 call sites are migrated, **When** the full test suite is executed, **Then** all API-layer test assertions for hardcoded exception type checks pass unchanged.
5. **Given** the `ai_agent.py` ValueError handling deviates from the `AppException` subclass convention, **When** a developer reads the code, **Then** an inline comment explicitly documents the deliberate deviation and the reason for it.

---

### User Story 4 - Dead Code Removal and Spec 039 (Priority: P2)

As a backend engineer, I want all identified dead code removed from the service layer — starting with the unreachable `branch_in_delete` inner block in `cleanup_service.py` — and documented in a formal Spec 039 under `specs/039-dead-code-cleanup/`, so that the codebase has zero dead code paths, the CHANGELOG reference to Spec 039 is fulfilled, and the inventory is auditable.

**Why this priority**: Dead code creates confusion during code review, inflates test coverage denominators, and masks real issues. The `cleanup_service.py` block is a confirmed unreachable path that could hide bugs. This story also closes an existing documentation gap (Spec 039 announced in CHANGELOG but directory missing).

**Independent Test**: Can be tested by running `ruff check --select F401,F811` and `vulture` against `src/` before and after the sweep, confirming the inventory matches the spec, and exercising the `branch_preserved` code path with a dedicated regression test.

**Acceptance Scenarios**:

1. **Given** the `cleanup_service.py` `branch_in_delete` inner block (lines 641–649) is identified as unreachable, **When** code inspection confirms that `preserved_branch_names` and `branches_to_delete` are mutually exclusive by construction, **Then** the block is removed.
2. **Given** the dead code block is removed, **When** a regression test exercises the `branch_preserved` code path, **Then** the test passes and confirms preserved branches are correctly handled.
3. **Given** `ruff check --select F401,F811` and `vulture` are run against `src/`, **When** the results are collected, **Then** all findings are documented in Spec 039 as a time-boxed, auditable inventory.
4. **Given** Spec 039 is authored under `specs/039-dead-code-cleanup/`, **When** the spec is reviewed, **Then** it lists every dead code item including the `cleanup_service.py` L641–649 block, and each item has a disposition (remove, defer, or retain with justification).

---

### User Story 5 - Intentional Deviation Documentation (Priority: P3)

As a backend engineer reading `workflow.py`, I want inline comments at the two `resolve_repository()` call sites that intentionally deviate from the canonical 5-step fallback (lines ~543 and ~615) so that I understand why these callers are different and do not "fix" them during future refactoring, explicitly acknowledging the ~90% consolidation state.

**Why this priority**: This is a documentation-only change with zero functional risk. It prevents future engineers from introducing bugs by mistakenly consolidating these intentional deviations.

**Independent Test**: Can be verified by code review — confirming that the comments are present, accurate, and explain the rationale for the deviation.

**Acceptance Scenarios**:

1. **Given** `workflow.py:543` (`get_config` with custom `session.github_username` fallback), **When** a developer reads the code, **Then** an inline comment explains why this caller deviates from the canonical `resolve_repository()` 5-step fallback.
2. **Given** `workflow.py:615` (`discover_agents` with intentional partial-resolution for query param override), **When** a developer reads the code, **Then** an inline comment explains why this caller intentionally uses partial resolution.

---

### User Story 6 - Singleton Removal Deferral (Priority: P3)

As a backend engineer, I want a clear, documented decision that module-level singleton removal (at `service.py:459` and `agents.py:363`) is explicitly deferred to a dedicated follow-up PR, so that this high-blast-radius change does not destabilize the current refactoring work and so that the follow-up PR scope is pre-defined.

**Why this priority**: This item has the highest blast radius (17+ consuming files including background tasks, signal bridge, and orchestrator). Deferring it prevents scope creep and ensures the current PR ships safely.

**Independent Test**: Can be verified by confirming that no changes are made to the singleton patterns in this PR, and that a follow-up tracking item exists with the required scope (audit 17+ consumers, introduce `get_github_service()` accessor, update test mocks).

**Acceptance Scenarios**:

1. **Given** the module-level singletons at `service.py:459` and `agents.py:363`, **When** this PR is reviewed, **Then** those singletons remain untouched and a documented deferral note exists.
2. **Given** the deferral is documented, **When** the follow-up PR is scoped, **Then** it includes: audit of all 17+ consuming files, introduction of a `get_github_service()` accessor pattern, and updates to all affected test mocks.

---

### Edge Cases

- What happens when the upstream fetch function returns `None` — should `cached_fetch()` cache `None` values or treat them as cache misses?
- How does `cached_fetch()` behave when the cache backend itself is unavailable (e.g., connection timeout)?
- What happens when `_cycle_cached()` receives a hit-count threshold of 0 — should it always fetch or always return cached?
- How does `handle_service_error()` behave when the original exception has no message or an empty message?
- What happens if `ruff` or `vulture` report false positives during the dead code inventory — how are those documented and excluded?
- What if the `branch_in_delete` block is actually reachable through a code path not covered by existing tests?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add a `cached_fetch()` async helper to `cache.py` that encapsulates the global cache pattern (cache.get → freshness check → fetch → cache.set with TTL and optional stale fallback), then refactor all 10 call sites across `board.py`, `projects.py` (4 sites), `utils.py`, `issues.py`, and `service.py`, targeting approximately 80 lines of total reduction.
- **FR-002**: System MUST add a `_cycle_cached()` instance method to `GitHubProjectsService` that encapsulates the cycle-cache pattern (get → hit-count check → fetch → set), then refactor all 7 call sites across `pull_requests.py` (3 sites), `projects.py`, `copilot.py` (2 sites), and `issues.py`.
- **FR-003**: System MUST migrate the 8 remaining catch-log-raise patterns to `handle_service_error()` across `api/board.py` (3 sites raising `GitHubAPIError`), `services/ai_agent.py` (4 sites raising `ValueError`), and `services/agents/service.py` (1 site with bare raise), targeting approximately 15–20 lines of reduction.
- **FR-004**: System SHOULD extend `handle_service_error()` with an `error_cls` parameter (or introduce a thin ValueError-compatible wrapper) so that `ai_agent.py` sites can adopt the helper without changing the exception type surfaced to existing callers.
- **FR-005**: System MUST remove the unreachable `branch_in_delete` inner block in `cleanup_service.py` (lines 641–649) after confirming by code inspection that `preserved_branch_names` and `branches_to_delete` are mutually exclusive by construction, and MUST add a regression test exercising the `branch_preserved` code path.
- **FR-006**: System MUST author Spec 039 under `specs/039-dead-code-cleanup/` documenting all identified dead code items before executing any sweep, and MUST run `ruff check --select F401,F811` and `vulture` against `src/` to generate a time-boxed, auditable inventory.
- **FR-007**: System SHOULD add inline comments to `workflow.py` (~line 543 and ~line 615) documenting why those two `resolve_repository()` callers intentionally deviate from the canonical 5-step fallback.
- **FR-008**: System MUST defer module-level singleton removal (at `service.py:459` and `agents.py:363`) to a dedicated follow-up PR. That follow-up PR MUST audit all 17+ consuming files, introduce a `get_github_service()` accessor pattern, and update all affected test mocks before merging.
- **FR-009**: System MUST preserve identical functional behavior observable by API consumers after each phase: cache TTLs, stale-fallback semantics, and exception types surfaced at API boundaries MUST remain unchanged.
- **FR-010**: System MUST document the `ai_agent.py` `ValueError` handling deviation from the `AppException` subclass convention with explicit inline code comments explaining the deliberate choice.
- **FR-011**: System MUST pass `python -m pytest tests/ -x` and `ruff check src/` with no new warnings after every completed item as a verification gate.

### Key Entities

- **Global Cache (`cache.py`)**: The application-level cache store used for caching external API responses with TTL-based expiration and optional stale-fallback on upstream failure.
- **Cycle Cache (`GitHubProjectsService._cycle_cache`)**: An instance-level, hit-count-based cache used within the GitHub Projects service for short-lived, request-scoped data reuse.
- **`handle_service_error()`**: The existing centralized error-handling helper that captures context, logs errors, and re-raises with a consistent format.
- **Spec 039 (`specs/039-dead-code-cleanup/`)**: A formal specification document inventorying all dead code identified via static analysis tools, with disposition for each item.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Total lines of duplicated cache and error-handling boilerplate are reduced by at least 100 lines (~80 from cache consolidation + ~15–20 from error handling + ~9 from dead code removal) across the service layer.
- **SC-002**: All existing tests pass with zero behavioral changes at API boundaries — identical cache TTLs, stale-fallback semantics, exception types, and response shapes are verified before and after each refactoring phase.
- **SC-003**: The number of distinct implementations of the global cache pattern drops from 10 to 1 (the `cached_fetch()` helper), and the number of distinct implementations of the cycle cache pattern drops from 7 to 1 (the `_cycle_cached()` method).
- **SC-004**: `ruff check src/` produces no new warnings and `ruff check --select F401,F811` returns zero findings after the dead code sweep is complete.
- **SC-005**: Spec 039 exists under `specs/039-dead-code-cleanup/` with a complete, auditable inventory of all dead code items identified by static analysis, each with a documented disposition.
- **SC-006**: Zero unreachable code paths remain in `cleanup_service.py` and a regression test confirms the `branch_preserved` code path is exercised.
- **SC-007**: New cached endpoints can be added with a single `cached_fetch()` or `_cycle_cached()` call rather than 8–10 lines of inline boilerplate, reducing time-to-implement for future cache-backed features.

## Assumptions

- The existing `handle_service_error()` helper is well-established and its interface is stable enough to extend with an `error_cls` parameter without breaking existing callers.
- The `board.py` cache pattern with dual-key lookups, stale fallback, and rate-limit classification may not fit cleanly into the generic `cached_fetch()` wrapper; those instances SHOULD remain inline if the abstraction would be forced or ill-fitting (target 80% coverage with the wrapper).
- Static analysis tools (`ruff`, `vulture`) are available in the development environment and their output is authoritative for identifying unused imports and dead code.
- The `branch_in_delete` inner block in `cleanup_service.py` is genuinely unreachable based on the mutual exclusivity of `preserved_branch_names` and `branches_to_delete` — this assumption must be verified by code inspection before removal.
- The follow-up PR for singleton removal (FR-008) will be tracked as a separate work item and is not blocked by this specification.
- Industry-standard error handling practices apply: errors are logged with sufficient context for debugging, and re-raised exceptions preserve the original stack trace.

## Execution Phases

- **Phase A** (parallel, low risk): FR-001 (cached_fetch), FR-002 (_cycle_cached), FR-005/FR-006 (dead code inventory + cleanup_service block removal)
- **Phase B** (sequential, largest change): FR-003/FR-004 (error handling consolidation — requires Phase A stability)
- **Phase C** (sequential): FR-006 completion (Spec 039 authoring via static analysis, then dead code sweep — time-boxed)
- **Phase D** (deferred, separate PR): FR-008 (singleton removal — highest blast radius, explicitly blocked)
- **Verification gate after every item**: `python -m pytest tests/ -x` green + `ruff check src/` no new warnings
