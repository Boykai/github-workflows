# Feature Specification: Simplicity & DRY Refactoring Plan (5 Phases)

**Feature Branch**: `028-simplicity-dry-refactor`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "Implement Simplicity & DRY Refactoring Plan (5 Phases)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Backend Developer Eliminates Duplicated Utility Code (Priority: P1)

A backend developer working on Project Solune encounters repeated patterns scattered across multiple files — repository resolution logic duplicated 8 times, error-handling boilerplate repeated in 5+ endpoints, inline session-validation guards in 5 places, and verbose cache access patterns in 3 files. Instead of copying the pattern yet again, the developer calls a single shared helper for each concern. The codebase is smaller, every bug fix or behavior change happens in one place, and new endpoints follow the established conventions automatically.

**Why this priority**: This is the highest-value, lowest-risk starting point. Each consolidation is a small, self-contained change that immediately reduces duplication and simplifies every subsequent phase. Completing this first shrinks the monolith's effective size before decomposition begins.

**Independent Test**: Can be fully tested by running the existing backend test suite after each helper is wired in. Verified by confirming that `grep` for the old duplicated patterns returns zero hits and all tests remain green.

**Acceptance Scenarios**:

1. **Given** 8 separate repository resolution implementations exist across backend files, **When** all callers are updated to use the single canonical helper, **Then** searching the codebase for the old duplicate function names returns zero results and the test suite passes.
2. **Given** 5+ endpoints contain hand-rolled error-handling try/catch blocks, **When** those endpoints are updated to use the shared error-handling helpers, **Then** 80% or more of endpoints use the shared helpers and all tests pass.
3. **Given** 5 inline session-validation guard clauses exist across endpoint files, **When** a shared validation helper is created and wired in, **Then** no inline validation guard clauses remain outside the shared helper and all tests pass.
4. **Given** 3 files contain verbose cache check/get/set patterns, **When** a generic cache wrapper is created and adopted, **Then** verbose cache patterns are eliminated from those files and all tests pass.

---

### User Story 2 — Backend Developer Works in Focused, Right-Sized Modules (Priority: P2)

A backend developer needs to modify issue-related logic. Today, they must navigate a single 4,950-line file containing 78 methods spanning unrelated concerns. After decomposition, the developer opens a focused module of fewer than 800 lines that contains only issue-related logic. They understand the context quickly, make their change confidently, and verify it with a targeted test run — without risk of unintended side effects in unrelated areas.

**Why this priority**: The monolith is the single largest source of complexity. Decomposing it depends on Phase 1 helpers being in place first. Once complete, every future change becomes faster and safer.

**Independent Test**: Can be fully tested by running the backend test suite after each module extraction. Verified by confirming that no single backend file exceeds 800 lines, no circular imports exist, the linter passes, and all existing callers continue to work unchanged through the backward-compatible facade.

**Acceptance Scenarios**:

1. **Given** a monolithic service file of 4,950 lines and 78 methods, **When** it is decomposed into focused modules, **Then** each resulting module is fewer than 800 lines and contains only logically related methods.
2. **Given** 17+ files import from the monolithic service, **When** a backward-compatible facade is put in place, **Then** all existing import paths continue to work without modification and all tests pass.
3. **Given** the decomposed modules, **When** the module-level singleton is replaced with dependency injection, **Then** services are provided via the dependency injection system and no module-level service instantiation remains.

---

### User Story 3 — Developer Experiences a Single, Predictable Startup Path (Priority: P3)

A developer debugging a startup issue currently must trace through three competing initialization patterns — lifespan hooks, module-level globals, and lazy singletons — to understand how services are created. After consolidation, there is exactly one initialization path: all services are created during application startup and injected through the dependency system. The developer can trace any service's lifecycle from a single entry point.

**Why this priority**: Initialization consolidation depends on the decomposed modules from Phase 2. It eliminates a category of subtle bugs (import-order dependencies, stale singletons) but is lower urgency than the duplication and monolith problems.

**Independent Test**: Can be fully tested by starting the application and verifying that health checks pass, the authentication flow works end-to-end, and no module-level service instantiation remains in the codebase.

**Acceptance Scenarios**:

1. **Given** 3 competing initialization patterns exist, **When** they are consolidated into a single pattern, **Then** all services are instantiated in the startup lifecycle hook and injected via the dependency system.
2. **Given** the consolidated initialization, **When** the application starts, **Then** health checks pass and the authentication flow completes successfully.
3. **Given** the consolidated initialization, **When** a developer searches for module-level service instantiation outside the lifecycle hook, **Then** zero instances are found.

---

### User Story 4 — Frontend Developer Builds New CRUD Features Without Copying Boilerplate (Priority: P2)

A frontend developer needs to add a new resource management screen. Today, they copy 300+ lines from an existing hook, rename variables, and adjust endpoints — a process prone to missed renames and inconsistent behavior. After refactoring, the developer calls a generic CRUD hook factory with the resource name and configuration, getting list/create/update/delete functionality with consistent caching, error handling, and optimistic updates in under 20 lines.

**Why this priority**: Frontend duplication is independent of backend work and can be tackled in parallel. The CRUD hook factory alone saves ~600 lines and directly reduces the effort for every future feature.

**Independent Test**: Can be fully tested by running the frontend test suite after refactoring each hook. Verified by confirming that the refactored hooks pass all existing tests and the generic factory is reused across at least 2 resource types.

**Acceptance Scenarios**:

1. **Given** duplicated CRUD hooks exist across multiple files, **When** a generic CRUD hook factory is created and hooks are refactored to use it, **Then** each refactored hook delegates to the factory and all frontend tests pass.
2. **Given** 3 near-identical settings hooks exist, **When** they are refactored to use the generic pattern, **Then** the duplicated logic is eliminated and all tests pass.
3. **Given** duplicated UI patterns exist across preview cards, modals, and error displays, **When** shared components are created, **Then** each consuming component uses the shared component and all tests pass.
4. **Given** query keys are scattered across multiple hook files, **When** a centralized query key registry is created, **Then** all hooks reference keys from the registry and no inline key definitions remain.
5. **Given** a 412-line chat interface component, **When** it is split into focused sub-components, **Then** each sub-component is independently testable and the combined behavior is unchanged.

---

### User Story 5 — Developer Maintains a Clean, Consistent Test Suite (Priority: P3)

A developer writing new tests discovers that mock factories are duplicated between a helpers file and individual test files, leading to inconsistent setups and brittle patches. After cleanup, all mock factories live in a single shared location, and test files use these shared fixtures instead of inline patches. New tests follow one clear pattern.

**Why this priority**: Test cleanup depends on the backend refactoring in Phases 1–3 being complete. It reduces maintenance burden and prevents test drift, but is lower urgency than production code quality.

**Independent Test**: Can be fully tested by running the full backend test suite after consolidating mocks and fixtures. Verified by confirming that the separate mock helpers file is removed and all tests use shared fixtures.

**Acceptance Scenarios**:

1. **Given** mock factories are duplicated between a helpers file and individual test files, **When** all mocks are consolidated into shared fixtures, **Then** the separate helpers file is removed and all tests pass.
2. **Given** inline patches exist in end-to-end test files, **When** they are replaced with shared fixtures, **Then** the inline patches are eliminated and all tests pass.

---

### Edge Cases

- What happens if a shared helper's signature changes during Phase 1 — do all callers get updated atomically, or can the migration be incremental?
- How does the backward-compatible facade handle methods that are renamed or split during decomposition?
- What happens if circular imports are introduced during module extraction — how are they detected and resolved?
- What happens if the application is started before all initialization patterns are consolidated — does the old pattern still work as a fallback?
- How are in-flight pull requests handled when the monolith file they target no longer exists after decomposition?
- What happens if a frontend shared component's interface doesn't fully cover a consuming component's needs — can it be extended without breaking other consumers?

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1 — Backend DRY Consolidation

- **FR-001**: System MUST provide a single canonical repository resolution helper that all endpoints use, eliminating all duplicate implementations.
- **FR-002**: System MUST provide shared error-handling helpers that endpoints use instead of hand-rolled try/catch boilerplate; at least 80% of endpoints MUST use these helpers after migration.
- **FR-003**: System MUST provide a shared session-validation helper that replaces all inline `selected_project_id` guard clauses across endpoint files.
- **FR-004**: System MUST provide a generic cache wrapper that encapsulates the check/get/set pattern, replacing verbose cache code in all consuming files.
- **FR-005**: Each Phase 1 consolidation MUST be independently mergeable — the test suite MUST pass after each individual change.

#### Phase 2 — Service Decomposition

- **FR-006**: The monolithic service file MUST be decomposed into focused modules, each containing fewer than 800 lines.
- **FR-007**: A backward-compatible facade MUST re-export all public methods so that existing callers require no import changes during migration.
- **FR-008**: Each module extraction MUST be independently mergeable — the test suite and linter MUST pass after each extraction.
- **FR-009**: After all extractions, the module-level singleton MUST be replaced with dependency injection; no module-level service instantiation MUST remain.
- **FR-010**: No circular imports MUST exist between the decomposed modules.

#### Phase 3 — Initialization Consolidation

- **FR-011**: All service instantiation MUST happen in a single lifecycle hook and be provided to endpoints through the dependency injection system.
- **FR-012**: No module-level globals or lazy singletons MUST remain for service instantiation after consolidation.
- **FR-013**: The application MUST start successfully with health checks passing and authentication flow completing end-to-end after consolidation.

#### Phase 4 — Frontend DRY Consolidation

- **FR-014**: A generic CRUD hook factory MUST be created that provides list/create/update/delete operations with consistent caching and error handling; at least 2 existing resource hooks MUST be refactored to use it.
- **FR-015**: Near-identical settings hooks MUST be refactored to share a common implementation, eliminating duplicated logic.
- **FR-016**: Shared UI components MUST be created for preview cards, modals (with escape-key/backdrop/overflow logic), and error displays; consuming components MUST use these shared components.
- **FR-017**: A centralized query key registry MUST be created; all hooks MUST reference keys from this registry rather than defining them inline.
- **FR-018**: The oversized chat interface component MUST be split into focused, independently testable sub-components.
- **FR-019**: Each frontend refactoring step MUST be independently mergeable — the frontend test suite MUST pass after each step.

#### Phase 5 — Test Cleanup

- **FR-020**: All mock factories MUST be consolidated into shared fixtures; the separate mock helpers file MUST be removed.
- **FR-021**: Inline patches in end-to-end test files MUST be replaced with shared fixtures.
- **FR-022**: The full backend test suite MUST pass after test cleanup is complete.

### Assumptions

- The existing test suite (47+ backend unit tests, 3+ integration tests, 29+ frontend unit tests, 9+ E2E tests) provides sufficient coverage to validate that refactoring preserves behavior.
- The backward-compatible facade is a transitional measure; callers will eventually be updated to import directly from the focused modules.
- The dependency injection system already exists in the codebase and does not need to be built from scratch.
- Frontend and backend refactoring have no cross-dependencies and can proceed in parallel.
- Performance characteristics are preserved through refactoring — no new bottlenecks are introduced.
- Standard industry practices for error handling (user-friendly messages with appropriate fallbacks) and caching (transparent wrapper with refresh capability) are acceptable defaults.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Total lines of duplicated code eliminated is 1,500 or more across backend and frontend.
- **SC-002**: The largest backend file is fewer than 800 lines (down from 4,950).
- **SC-003**: 80% or more of backend endpoints use shared error-handling helpers instead of hand-rolled boilerplate.
- **SC-004**: Zero duplicate repository resolution implementations remain — searching the codebase returns zero results for the old function names.
- **SC-005**: Zero inline session-validation guard clauses remain outside the shared validation helper.
- **SC-006**: The full backend test suite (47+ unit, 3+ integration tests) passes after all backend phases are complete.
- **SC-007**: The full frontend test suite (29+ unit, 9+ E2E tests) passes after all frontend refactoring is complete.
- **SC-008**: The application starts successfully, health checks pass, and the authentication flow completes after initialization consolidation.
- **SC-009**: No circular imports exist between decomposed backend modules — the linter confirms this.
- **SC-010**: The generic CRUD hook factory is reused by at least 2 frontend resource hooks, each requiring fewer than 20 lines of hook-specific configuration.
- **SC-011**: Developer onboarding time for understanding a single backend concern is reduced — the focused module a developer needs to read is fewer than 800 lines instead of 4,950.
