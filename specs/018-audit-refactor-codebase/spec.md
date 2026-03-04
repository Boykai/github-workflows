# Feature Specification: Audit & Refactor FastAPI+React GitHub Projects Copilot Codebase

**Feature Branch**: `018-audit-refactor-codebase`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "Audit & Refactor FastAPI+React GitHub Projects Copilot Codebase"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Modernize All Dependencies (Priority: P1)

As a **developer maintaining the codebase**, I want all backend and frontend dependencies updated to their latest stable versions and unused packages removed, so that the project benefits from security patches, bug fixes, and new features without carrying dead weight.

**Why this priority**: Outdated or unused dependencies pose security risks and increase maintenance burden. This is foundational — later refactoring work builds on a stable, up-to-date dependency tree.

**Independent Test**: Can be fully tested by running `pip install`, `npm install`, then the existing backend and frontend test suites. If all tests pass after the version bumps, the upgrade is verified.

**Acceptance Scenarios**:

1. **Given** the backend dependency manifest, **When** the unused `agent-framework-core` package is removed, **Then** the backend installs and runs without errors, and no import references to `agent-framework-core` exist in the codebase.
2. **Given** the backend dependency manifest, **When** all remaining backend packages are bumped to latest stable, **Then** the application starts successfully and the existing test suite passes with no regressions.
3. **Given** the frontend dependency manifest, **When** all frontend packages are bumped to latest stable, **Then** the application builds successfully and the existing test suite passes with no regressions.
4. **Given** the Copilot SDK is updated, **When** the application uses `CopilotClient`, `CopilotClientOptions`, `SessionConfig`, `MessageOptions`, `PermissionHandler`, `SessionEventType`, and `CopilotClient.list_models()`, **Then** all symbols still resolve and behave as expected.

---

### User Story 2 — Eliminate Duplicate Code (DRY Consolidation) (Priority: P1)

As a **developer working on the codebase**, I want duplicated patterns consolidated into shared abstractions, so that bug fixes and enhancements only need to happen in one place and the codebase is easier to understand and maintain.

**Why this priority**: Code duplication is the top source of subtle inconsistencies and maintenance overhead. Consolidating these patterns directly reduces defect risk and developer onboarding time.

**Independent Test**: Can be fully tested by running the existing backend test suite after each consolidation. If all tests pass without modification to test expectations, the refactoring preserves correctness.

**Acceptance Scenarios**:

1. **Given** both `CopilotCompletionProvider` and `GitHubCopilotModelFetcher` each maintain their own client-caching logic, **When** a shared client pool is introduced in-place, **Then** both consumers use the same pool, duplicate `_clients` dict / `_token_key()` / `_get_or_create_client()` code is removed, and all tests pass.
2. **Given** multiple REST/GraphQL fallback try/except chains exist in `service.py`, **When** a generic `_with_fallback()` helper is extracted and applied, **Then** every previously duplicated fallback chain delegates to the helper, and all tests pass.
3. **Given** `_request_with_retry()` and `_graphql()` both implement overlapping retry-on-secondary-rate-limit logic, **When** the retry strategies are unified, **Then** there is a single consistent retry mechanism and all tests pass.
4. **Given** `_build_headers()`, `_build_graphql_headers()`, and scattered per-mutation header construction exist, **When** they are consolidated into a single builder with optional feature flags, **Then** all HTTP calls use the unified builder and all tests pass.

---

### User Story 3 — Fix Anti-Patterns (Priority: P2)

As a **developer and operator of the system**, I want known anti-patterns corrected or explicitly documented, so that the system is more robust, predictable, and easier to operate at scale.

**Why this priority**: Anti-patterns introduce subtle bugs and operational risks. Fixing them improves reliability and reduces surprises in production. This is prioritized after DRY consolidation because it addresses correctness and operability rather than structure.

**Independent Test**: Each anti-pattern fix can be tested independently — the parameterized model via a unit test, in-memory state documentation via code review, file deletion via an integration test, etc.

**Acceptance Scenarios**:

1. **Given** the GraphQL mutation for Copilot agent assignment hardcodes a model name, **When** the model is parameterized from configuration, **Then** the mutation uses the configured model value, and tests verify the parameterization.
2. **Given** in-memory dictionaries (`_messages`, `_proposals`, `_recommendations`) in the chat module have no persistence or documentation, **When** the limitation is explicitly documented or state is persisted, **Then** the chosen approach is clear to future developers.
3. **Given** the `delete_files` parameter exists in the commit workflow but is not implemented, **When** either file deletion support is added or the parameter is removed, **Then** the interface is honest — no dead parameters remain.
4. **Given** OAuth state storage is a bounded in-memory dict limited to a single instance, **When** the limitation is documented or state is migrated to persistent storage, **Then** the operational constraint is clear.
5. **Given** singleton services are registered via both `app.state` and module-global variables, **When** a single registration pattern is chosen, **Then** there is only one way to access each singleton.
6. **Given** various in-memory caches exist across the codebase, **When** all caches are audited, **Then** every cache uses the bounded-collection utilities to prevent unbounded memory growth.

---

### User Story 4 — Maintain Full Backward Compatibility (Priority: P1)

As an **end user of the application**, I want all existing features to continue working identically after the refactor, so that I experience zero disruption.

**Why this priority**: A refactor that breaks existing behavior has negative net value. Backward compatibility is a hard constraint, not a nice-to-have.

**Independent Test**: Can be fully tested by running the complete existing backend and frontend test suites and verifying all API endpoint contracts are unchanged.

**Acceptance Scenarios**:

1. **Given** the full backend test suite, **When** run after all refactoring is complete, **Then** all tests pass with no regressions.
2. **Given** the full frontend test suite, **When** run after all dependency bumps and any related changes, **Then** all tests pass with no regressions.
3. **Given** the existing API endpoint contracts, **When** any API is called with the same request as before the refactor, **Then** the response shape and status codes are identical.

---

### Edge Cases

- What happens when a newly bumped dependency introduces a breaking change in its API? The update must be validated against all usage sites — if a symbol is renamed or removed, the consuming code must be adapted.
- What happens if the shared client pool is accessed concurrently? The pool must be safe for concurrent async access, matching the safety guarantees of the original per-consumer caches.
- What happens when the unified retry helper encounters an error type not previously handled by one of the original retry strategies? The unified strategy must be the superset of all previously handled error types.
- What happens when the `_with_fallback()` helper's primary function fails with an unexpected exception type? The helper must clearly define which exceptions trigger fallback vs. which propagate immediately.
- What happens when in-memory caches hit their bounded size limits? Existing eviction behavior (from `BoundedDict`/`BoundedSet`) must be preserved — no data corruption or silent failures.
- What happens if the Copilot SDK removes or renames one of the required symbols in a future version? The dependency version should be pinned to a compatible range, and symbol usage should be verified at startup or test time.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Modernize Packages**

- **FR-001**: The unused `agent-framework-core` package MUST be removed from the backend dependency manifest, and no import references to it may remain in the codebase.
- **FR-002**: All backend dependencies MUST be updated to their latest stable versions, with verification that all used symbols and APIs still function correctly.
- **FR-003**: The Copilot SDK MUST be updated to the latest stable version, with explicit verification that the following symbols exist and work: `CopilotClient`, `CopilotClientOptions`, `SessionConfig`, `MessageOptions`, `PermissionHandler`, `SessionEventType`, `CopilotClient.list_models()`.
- **FR-004**: All frontend dependencies MUST be updated to their latest stable versions, with the application building and all tests passing.

**Phase 2 — DRY Consolidation**

- **FR-005**: A shared client pool MUST be extracted and used by both `CopilotCompletionProvider` and `GitHubCopilotModelFetcher`, eliminating the duplicate `_clients` dict, `_token_key()`, and `_get_or_create_client()` logic.
- **FR-006**: A generic fallback helper MUST be extracted in the main service module to replace all repeated try/except fallback chains (Copilot assignment GraphQL/REST, review request REST/GraphQL, add-issue-to-project multi-strategy).
- **FR-007**: Retry logic across the request retry mechanism and GraphQL request handler MUST be unified into a single consistent strategy for handling secondary rate limits.
- **FR-008**: Header construction MUST be consolidated from multiple builders and scattered inline construction into a single builder that accepts optional feature flags.

**Phase 3 — Fix Anti-Patterns**

- **FR-009**: The hardcoded model identifier in the Copilot agent assignment GraphQL mutation MUST be parameterized, reading the value from the agent assignment configuration.
- **FR-010**: The in-memory chat state dictionaries (`_messages`, `_proposals`, `_recommendations`) MUST either be persisted to the database or have their intentional in-memory MVP behavior explicitly documented with a TODO for future migration.
- **FR-011**: The `delete_files` parameter in the commit workflow MUST either be fully implemented using the GraphQL commit-on-branch file deletions capability, or be removed entirely from the interface.
- **FR-012**: The OAuth state storage limitation (single-instance, bounded to 1,000 entries) MUST be documented in code comments, or the storage MUST be migrated to the persistent database.
- **FR-013**: Singleton service registration MUST use a single pattern — either application state (preferred for testability) or module-global variables — with the dual-registration pattern removed.
- **FR-014**: All in-memory caches across the codebase MUST be audited to confirm they use the bounded-collection utilities, preventing unbounded memory growth.

**Cross-Cutting Constraints**

- **FR-015**: All refactoring MUST be performed in-place — no new files or modules may be created.
- **FR-016**: The dual AI provider pattern (Copilot SDK primary, Azure OpenAI fallback) MUST be maintained throughout all changes.
- **FR-017**: All existing API endpoint contracts MUST be preserved — no changes to request/response shapes or status codes.
- **FR-018**: The existing code style MUST be followed: `ruff` formatting, 100-character line length, double quotes.

### Key Entities

- **CopilotClientPool**: A shared abstraction for caching and reusing Copilot SDK client instances, keyed by authentication token. Used by both the completion provider and model fetcher.
- **Fallback Helper**: A generic utility function that accepts a primary operation, a fallback operation, and a context message — executing the primary first and falling back on specified failure types.
- **Unified Retry Strategy**: A single retry mechanism that handles secondary rate limits, transient errors, and configurable backoff, replacing the current overlapping retry implementations.
- **Unified Header Builder**: A single function that constructs HTTP headers for both REST and GraphQL requests, accepting optional feature flags for specialized headers.
- **BoundedDict / BoundedSet**: Existing utility classes that enforce a maximum size on in-memory caches with LRU or FIFO eviction. All caches must use these.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the existing backend test suite passes after all changes, with zero regressions.
- **SC-002**: 100% of the existing frontend test suite passes after all changes, with zero regressions.
- **SC-003**: The number of distinct retry-logic implementations is reduced from two (or more) to exactly one.
- **SC-004**: The number of distinct header-builder functions is reduced from three (or more) to exactly one.
- **SC-005**: The number of locations containing client-caching logic (`_clients` dict, `_token_key()`, `_get_or_create_client()`) is reduced from two to one (the shared pool).
- **SC-006**: All in-memory caches identified in the audit use bounded collections — zero unbounded `dict` or `set` instances remain for cache purposes.
- **SC-007**: Zero hardcoded model identifiers remain in GraphQL mutations — all model references come from configuration.
- **SC-008**: The `agent-framework-core` package is absent from the dependency manifest and the installed environment.
- **SC-009**: All backend and frontend dependencies are at their latest stable versions as of the date of the refactor.
- **SC-010**: The total lines of duplicated code eliminated by DRY consolidation is documented in a completion summary.

## Assumptions

- The Copilot SDK's latest stable version retains all currently used symbols (`CopilotClient`, `CopilotClientOptions`, `SessionConfig`, `MessageOptions`, `PermissionHandler`, `SessionEventType`, `CopilotClient.list_models()`). If any are removed or renamed, adaptation is required and should be documented.
- Frontend dependency bumps are straightforward and do not require React version migration steps (e.g., React 18 → 19 is out of scope unless the latest stable is still React 18).
- The existing test suites have sufficient coverage to detect regressions. No new test infrastructure is required, though individual tests may need updates if refactored internals change (while preserving external behavior).
- "In-place refactoring" means modifying existing files only — no new Python modules, no new TypeScript files, no new directories. Helper functions and classes are added within the files where they are used.
- The `BoundedDict` and `BoundedSet` utilities in `utils.py` are mature and ready for broader adoption across all caches.
- The decision on FR-010 (chat state persistence vs. documentation) and FR-011 (implement vs. remove `delete_files`) and FR-012 (document vs. migrate OAuth state) will be made by the implementer based on effort and risk, with the chosen approach clearly documented in the completion summary.
