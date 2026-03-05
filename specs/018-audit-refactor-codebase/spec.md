# Feature Specification: Audit & Refactor FastAPI + React GitHub Projects V2 Codebase

**Feature Branch**: `018-audit-refactor-codebase`  
**Created**: 2026-03-05  
**Status**: Draft  
**Input**: User description: "Audit & Refactor FastAPI + React GitHub Projects V2 Codebase"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Modernize Backend and Frontend Dependencies (Priority: P1)

As a developer maintaining the project, I want all backend and frontend dependencies updated to their latest stable versions so that the codebase benefits from security patches, performance improvements, and new features while removing unused packages.

**Why this priority**: Outdated dependencies introduce security vulnerabilities and compatibility issues. Removing the unused `agent-framework-core` package eliminates confusion and reduces install footprint. This is the foundation that all subsequent refactoring depends on.

**Independent Test**: Can be fully tested by running the full backend test suite and frontend test suite after dependency updates, confirming zero import errors and no behavioral regressions.

**Acceptance Scenarios**:

1. **Given** the backend dependency manifest includes `agent-framework-core`, **When** the dependency audit is complete, **Then** `agent-framework-core` is removed from the manifest and the application starts without errors
2. **Given** the AI completion SDK dependency is at an older version, **When** the dependency is bumped to latest stable, **Then** all existing provider integrations (client creation, session configuration, message handling, permission management, event types, and model listing) continue to function correctly
3. **Given** the AI inference dependencies are at older versions, **When** they are bumped to latest stable, **Then** the fallback AI provider continues to produce completions without errors
4. **Given** the frontend dependency manifest lists older versions of the UI framework, build tool, test runner, data-fetching library, and end-to-end test framework, **When** all are bumped to latest stable, **Then** the frontend builds, unit tests pass, and end-to-end tests pass with no regressions

---

### User Story 2 - Eliminate Duplicate Code Through DRY Consolidation (Priority: P1)

As a developer working on the codebase, I want duplicated patterns (client pooling, fallback chains, retry logic, and header construction) consolidated into shared helpers so that future changes only need to be made in one place, reducing bug surface area and improving maintainability.

**Why this priority**: Code duplication is the primary source of drift-related bugs. When the same logic exists in multiple places, fixing a bug in one location but not the other leads to inconsistent behavior. This directly impacts system reliability.

**Independent Test**: Can be fully tested by running the existing backend test suite. Each consolidation (client pool, fallback helper, retry unification, header builder) can be validated independently by confirming that the behavior before and after refactoring is identical.

**Acceptance Scenarios**:

1. **Given** two separate modules each contain their own logic for caching and creating AI clients using token-based keys, **When** the shared client pool is extracted, **Then** both modules use the single shared pool, duplicate caching logic is removed, and AI completions and model listing continue to work
2. **Given** the main service module contains multiple repeated try/except fallback patterns for different operations, **When** a generic fallback helper is introduced, **Then** all identified fallback chains use the helper, and primary-then-fallback behavior is preserved for each operation
3. **Given** there are two separate retry mechanisms (a dedicated retry function and inline retry-on-rate-limit logic), **When** retry logic is unified into a single consistent strategy, **Then** all retried operations use the same mechanism and rate-limit handling is consistent
4. **Given** there are multiple header-building functions and inline custom header constructions, **When** they are consolidated into a single header builder, **Then** all outgoing requests use the unified builder and feature-flag-based headers are supported through a single entry point

---

### User Story 3 - Fix Anti-Patterns in Backend Code (Priority: P2)

As a developer and system operator, I want identified anti-patterns resolved so that the system is more reliable, testable, and free of misleading code paths.

**Why this priority**: Anti-patterns create operational risk (unbounded memory growth, data loss on restart), misleading developer experiences (stub functions that silently do nothing), and test fragility (global singletons). While the system works today, these patterns accumulate technical debt that becomes harder to fix over time.

**Independent Test**: Each anti-pattern fix can be tested independently — the hardcoded model fix is testable by passing different model values; the in-memory state migration is testable by restarting the service and confirming data persistence; the file deletion fix is testable by invoking the commit workflow with deletions; bounded caches are testable by exceeding the capacity limit.

**Acceptance Scenarios**:

1. **Given** a GraphQL mutation for assigning an AI coding agent has a hardcoded model identifier, **When** the model is parameterized, **Then** the model value is passed from the agent assignment configuration at the call site and different models can be specified
2. **Given** chat messages, proposals, and recommendations are stored in module-level dictionaries that are lost on restart, **When** this anti-pattern is addressed, **Then** either the data is persisted to the database using the existing migration system OR the in-memory approach is explicitly documented as an intentional MVP decision with a clear TODO for future migration
3. **Given** a commit workflow function accepts a file-deletion parameter but silently ignores it, **When** this anti-pattern is addressed, **Then** either file deletions are fully implemented using the appropriate mutation input OR the misleading parameter is removed from the function signature
4. **Given** an in-memory OAuth state store has no documented size bounds or restart behavior, **When** this anti-pattern is addressed, **Then** the store includes a code comment documenting its bounded capacity (maximum 1000 states) and the fact that states are lost on restart, with an optional migration path noted
5. **Given** service singletons are registered using both application state and module-global fallback variables, **When** this is standardized, **Then** all service singletons are registered exclusively through application state, module-global fallback variables are removed, and test isolation is improved
6. **Given** multiple in-memory caches throughout the codebase use plain dictionaries or sets without size bounds, **When** the audit is complete, **Then** all identified caches use the existing bounded collection utilities, preventing unbounded memory growth

---

### Edge Cases

- What happens when an upgraded dependency introduces a breaking API change? The system must still compile and pass all tests; any incompatible API change requires an adapter or pinned version.
- What happens when the shared client pool receives concurrent requests for the same token? The pool must handle concurrent access safely without creating duplicate clients or corrupting the cache.
- What happens when the unified fallback helper's primary function fails AND the fallback function also fails? The error from the fallback must be propagated with sufficient context to diagnose both failures.
- What happens when the unified retry strategy encounters a non-retryable error (e.g., 401 Unauthorized)? The retry mechanism must distinguish retryable errors (rate limits, transient network failures) from permanent errors and fail fast on permanent errors.
- What happens when an in-memory bounded cache reaches its capacity limit? The oldest entries must be evicted according to the existing bounded collection eviction policy, with no data corruption or service interruption.
- What happens when the database migration for chat persistence encounters a schema conflict? The migration must be idempotent and handle the case where the table already exists.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1 — Dependency Modernization

- **FR-001**: The backend dependency manifest MUST NOT include the `agent-framework-core` package, as it is unused
- **FR-002**: The AI completion SDK dependency MUST be updated to the latest stable version, and all existing API surfaces (client creation, session configuration, message options, permission handling, event types, and model listing) MUST remain functional
- **FR-003**: The AI inference dependencies (for the OpenAI-compatible and Azure-based fallback provider) MUST be updated to latest stable versions with no breakage to the fallback completion provider
- **FR-004**: The frontend dependency manifest MUST have its core UI framework, build tool, test runner, data-fetching library, and end-to-end test framework updated to latest stable versions

#### Phase 2 — DRY Consolidation

- **FR-005**: A shared client pool MUST be extracted that handles token-key-based caching and client creation, and MUST be used by both the primary AI completion provider and the model fetcher module — eliminating duplicate caching logic
- **FR-006**: A generic fallback helper MUST be introduced in the main service module that accepts a primary function, a fallback function, and a context message — and MUST replace all identified repeated try/except fallback chains (agent assignment via two strategies, review requests via two strategies, and project item addition via three strategies)
- **FR-007**: Retry logic MUST be unified into a single consistent strategy that consolidates the dedicated retry function and the inline retry-on-secondary-rate-limit logic, providing consistent behavior for all retried operations
- **FR-008**: Header construction MUST be consolidated into a single builder function that accepts optional feature flags, replacing the multiple separate header-building functions and inline custom header constructions

#### Phase 3 — Anti-Pattern Remediation

- **FR-009**: The hardcoded model identifier in the agent assignment mutation MUST be replaced with a parameterized value sourced from the agent assignment configuration
- **FR-010**: Module-level in-memory dictionaries for chat messages, proposals, and recommendations MUST either be migrated to persistent storage using the existing database service and migration system, OR be explicitly documented as an intentional MVP decision with a TODO comment
- **FR-011**: The file-deletion parameter in the commit workflow MUST either be fully implemented to support file deletions in commit mutations, OR be removed from the function signature to prevent a misleading stub
- **FR-012**: The in-memory OAuth state store MUST include a code comment documenting its bounded capacity (maximum 1000 entries), its loss-on-restart behavior, and an optional future migration path
- **FR-013**: Service singleton registration MUST use application-level state exclusively; all module-global fallback variables for service singletons MUST be removed
- **FR-014**: All identified in-memory caches (pipeline states, issue branch mappings, sub-issue mappings, processed PR trackers, pending agent assignments, and similar) MUST use the existing bounded collection utilities to prevent unbounded memory growth

#### Cross-Cutting Constraints

- **FR-015**: All refactoring MUST be performed in-place — no new files or modules may be created, and existing module structure MUST be preserved
- **FR-016**: The dual AI provider pattern (primary SDK provider with fallback to an OpenAI-compatible provider) MUST be preserved throughout all changes
- **FR-017**: All existing API endpoints consumed by the frontend MUST maintain full backward compatibility — no changes to request/response contracts
- **FR-018**: All existing backend tests MUST pass after changes, and any tests affected by refactored code MUST be updated to match the new implementation
- **FR-019**: All existing frontend tests MUST pass after dependency updates

### Key Entities

- **Client Pool**: A shared resource that caches AI client instances keyed by a hash of the authentication token, preventing redundant client creation across modules
- **Fallback Helper**: A reusable function encapsulating the pattern of attempting a primary operation and gracefully falling back to an alternative on failure, with contextual logging
- **Retry Strategy**: A unified mechanism for retrying operations that fail due to transient errors (rate limits, network timeouts), with configurable attempt counts and backoff behavior
- **Header Builder**: A single function responsible for constructing all outgoing request headers, supporting base headers, GraphQL-specific headers, and optional feature-flag headers
- **Bounded Cache**: A size-limited collection (dictionary or set) that automatically evicts entries when capacity is reached, preventing unbounded memory growth
- **Chat State**: Messages, proposals, and recommendations associated with user chat sessions, currently stored in-memory and candidates for persistence

## Assumptions

- The existing bounded collection utilities (`BoundedDict`/`BoundedSet`) in the utils module are production-ready and suitable for all identified cache use cases
- The existing database service and migration system can accommodate new tables for chat state persistence if that path is chosen
- Bumping frontend dependencies to latest stable will not require major refactoring of component code (only minor API adjustments if any)
- The AI completion SDK's latest stable version maintains backward-compatible API surfaces for the six identified APIs (client, session config, message options, permission handler, event types, model listing)
- A maximum capacity of 1000 entries for the OAuth state store is sufficient for the expected concurrent user load
- The in-place refactoring constraint means all changes happen within existing files — shared helpers are added to existing modules rather than new files

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of backend tests pass after all changes with zero regressions
- **SC-002**: 100% of frontend tests pass after dependency updates with zero regressions
- **SC-003**: The application starts and serves all existing API endpoints without errors after the refactor
- **SC-004**: Duplicate client-caching logic is reduced from two independent implementations to one shared implementation
- **SC-005**: Repeated fallback try/except patterns in the service module are reduced from at least three separate implementations to a single reusable helper
- **SC-006**: Retry logic is reduced from two separate mechanisms to one unified strategy
- **SC-007**: Header-building code is reduced from multiple functions/inline constructions to one configurable builder
- **SC-008**: All identified in-memory caches use bounded collections, ensuring no cache can grow beyond its defined capacity limit
- **SC-009**: The hardcoded model value is eliminated — the agent assignment mutation accepts a configurable model parameter
- **SC-010**: The unused `agent-framework-core` dependency is removed, reducing the backend's install footprint
