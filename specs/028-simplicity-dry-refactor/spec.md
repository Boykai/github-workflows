# Feature Specification: Simplicity & DRY Refactoring Across Backend and Frontend

**Feature Branch**: `028-simplicity-dry-refactor`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "Implement Simplicity & DRY Refactoring Across Backend and Frontend"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consistent Error Handling and Validation Across Backend Endpoints (Priority: P1)

As a developer maintaining the backend, when I add or modify an API endpoint, I should be able to rely on a single set of shared helpers for repository resolution, error handling, and session validation instead of copying boilerplate from other endpoints. This reduces bugs caused by inconsistent implementations and makes it faster to onboard new contributors.

**Why this priority**: The 8 duplicate repository resolution implementations and 5+ hand-rolled error handling blocks are the most immediate sources of bugs and maintenance friction. Consolidating them is the lowest-risk, highest-value change and unblocks the larger service decomposition.

**Independent Test**: Can be verified by confirming that all API endpoints delegate repository resolution, error handling, and project validation to the shared helpers, and that the existing backend test suite passes without modification.

**Acceptance Scenarios**:

1. **Given** a developer searches the codebase for `_get_repository_info`, **When** the Phase 1 consolidation is complete, **Then** there are zero results — all callers use the canonical `resolve_repository()` helper.
2. **Given** an API endpoint encounters a service-layer error, **When** the error is caught, **Then** the endpoint delegates to the shared error handling helper rather than inline catch-log-raise logic.
3. **Given** an API endpoint requires a selected project, **When** it checks for a valid project selection, **Then** it uses the shared `require_selected_project()` dependency rather than an inline guard clause.
4. **Given** an API endpoint fetches cacheable data, **When** it performs the fetch, **Then** it delegates to the shared cache wrapper rather than manually checking, getting, and setting cache entries.

---

### User Story 2 - Decomposed Backend Service with Backward Compatibility (Priority: P1)

As a developer working on the backend, when I need to modify or extend GitHub Projects functionality, I should be able to navigate to a focused, appropriately-sized module rather than scrolling through a single file with nearly 5,000 lines and 78 methods. All existing imports and usages must continue to work unchanged during migration.

**Why this priority**: The monolithic service file is the single largest source of complexity in the codebase. Decomposing it into focused modules is essential for long-term maintainability, but must preserve backward compatibility to avoid a risky big-bang migration.

**Independent Test**: Can be verified by confirming that the monolithic service file has been split into focused modules each under 800 lines, that a backward-compatible facade re-exports all public symbols, and that all existing tests and imports work without changes.

**Acceptance Scenarios**:

1. **Given** the service decomposition is complete, **When** a developer inspects the service directory, **Then** it contains 8 focused modules (client, projects, issues, pull requests, copilot, fields, board, repository) each under 800 lines.
2. **Given** the decomposition uses composition over inheritance, **When** any decomposed module needs to make API calls, **Then** it accesses the shared client reference rather than inheriting from a base class.
3. **Given** existing code imports from the service package, **When** the decomposition is deployed, **Then** all existing imports continue to resolve correctly via the backward-compatible facade in the package init.
4. **Given** the module-level singleton pattern is replaced, **When** any endpoint needs the service, **Then** it receives it via dependency injection through application state and the dependency provider.

---

### User Story 3 - Unified Service Initialization (Priority: P2)

As a developer deploying the application, when services are initialized at startup, there should be a single, predictable initialization path rather than competing patterns that cause confusion about which instance of a service is being used.

**Why this priority**: Three competing initialization patterns (lifespan, module-level globals, lazy singletons) create ambiguity about service lifecycle and can cause subtle bugs where different parts of the application use different service instances. This must follow the service decomposition to avoid conflicting changes.

**Independent Test**: Can be verified by confirming that all service instantiation flows through a single initialization path, that module-level instantiation and lazy singletons have been removed, and that the application starts successfully with the OAuth flow working.

**Acceptance Scenarios**:

1. **Given** the initialization consolidation is complete, **When** a developer searches the codebase for service instantiation patterns, **Then** all services are created during application startup and stored on application state.
2. **Given** the consolidated initialization is deployed, **When** the application starts, **Then** the application boots successfully and the OAuth authentication flow works end-to-end.
3. **Given** a developer needs a service reference in an API endpoint, **When** they declare it as a dependency, **Then** they use the dependency provider from the shared dependencies module which retrieves it from application state.

---

### User Story 4 - DRY Frontend Hooks and Shared UI Components (Priority: P2)

As a frontend developer, when I build a new CRUD resource page, settings panel, or data-driven UI, I should be able to compose it from shared hooks and components rather than duplicating 600+ lines of hook logic or reimplementing common UI patterns like modals, preview cards, and error alerts.

**Why this priority**: Frontend duplication is the largest category of redundant code by line count (~1,500+ lines across hooks, components, and API definitions). Consolidation directly reduces the surface area for UI bugs and accelerates feature development. This work has no cross-dependencies with backend changes and can proceed in parallel.

**Independent Test**: Can be verified by confirming that CRUD hooks, settings hooks, shared UI components, centralized query keys, and the API endpoint factory are implemented, and that the frontend test suite passes fully.

**Acceptance Scenarios**:

1. **Given** a CRUD hook factory exists, **When** a developer needs CRUD operations for a new resource, **Then** they instantiate the factory with resource-specific configuration rather than writing a new hook from scratch.
2. **Given** settings hooks are unified, **When** a developer needs to access user, global, or project settings, **Then** they use the generic settings hook parameterized with the appropriate configuration.
3. **Given** shared UI components exist for modals, preview cards, and error alerts, **When** a developer needs these patterns, **Then** they import and configure the shared components rather than duplicating markup and styling.
4. **Given** a centralized query key registry exists, **When** a developer defines a new query, **Then** they add the key to the single registry rather than hardcoding strings inline.
5. **Given** an API endpoint factory exists, **When** a developer needs to define a new API group, **Then** they use the factory with a base path and method definitions rather than writing boilerplate fetch calls.

---

### User Story 5 - Simplified ChatInterface Component (Priority: P3)

As a frontend developer maintaining the chat feature, when I need to modify message display logic or input behavior, I should be able to work in a focused component rather than navigating a 400+ line megacomponent that mixes concerns.

**Why this priority**: The ChatInterface component is a usability concern for developers but lower priority than the broader hook and component consolidation. Splitting it improves maintainability without affecting end-user functionality.

**Independent Test**: Can be verified by confirming that the ChatInterface has been split into focused sub-components for message display and input, and that the chat feature continues to function correctly with all existing tests passing.

**Acceptance Scenarios**:

1. **Given** the ChatInterface has been split, **When** a developer inspects the chat components, **Then** there are separate message list and input components with clearly separated concerns.
2. **Given** the split is deployed, **When** a user interacts with the chat feature, **Then** all existing functionality (sending messages, viewing history, drag/resize) works identically to before.

---

### User Story 6 - Consolidated Test Helpers (Priority: P3)

As a developer writing backend tests, when I need mock data or test fixtures, I should find them in a single, well-organized location rather than scattered across helper files and inline in test modules.

**Why this priority**: Test helper consolidation is a quality-of-life improvement for developers that reduces confusion about which mock factory to use. It depends on the backend changes being complete first to avoid conflicting modifications.

**Independent Test**: Can be verified by confirming that all mock factories are consolidated into the shared test configuration, inline patches are replaced with fixtures, and the full test suite passes.

**Acceptance Scenarios**:

1. **Given** test helpers are consolidated, **When** a developer needs a mock object for testing, **Then** they import it from the shared test configuration rather than from scattered helper files.
2. **Given** inline patches are replaced with fixtures, **When** the full backend test suite runs, **Then** all 47+ unit tests and 3+ integration tests pass.
3. **Given** the frontend test suite is unmodified, **When** it runs, **Then** all 29+ unit tests and 9+ E2E tests pass.

---

### Edge Cases

- What happens if a module imported from the backward-compatible facade is also imported directly from a decomposed sub-module? The facade re-exports must point to the same objects to avoid identity or equality issues.
- How does the system behave if the cache wrapper encounters a cache backend failure? The fetch function must still execute and return data, falling back to an uncached path.
- What happens if the validation dependency for selected project is called in an endpoint that intentionally operates without a selected project? Endpoints that do not require a project selection must not use this dependency.
- How does the CRUD hook factory handle a resource that needs custom mutation logic beyond standard create/update/delete? The factory must support per-resource overrides for non-standard operations.
- What happens if the API endpoint factory is used for an endpoint group that requires non-standard authentication or headers? The factory must accept optional configuration for custom request options.
- What happens during the migration window when some endpoints use the new dependency injection pattern and others still reference the old singleton? The facade must ensure both patterns resolve to the same service instance until migration is complete.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a single canonical repository resolution helper that all API endpoints use, eliminating all duplicate implementations.
- **FR-002**: System MUST provide shared error handling helpers that API endpoints use to process service-layer errors, replacing inline catch-log-raise patterns.
- **FR-003**: System MUST provide a shared validation dependency for checking that a project is selected in the current session, replacing inline guard clauses.
- **FR-004**: System MUST provide a generic cache wrapper that encapsulates the check/get/set pattern, replacing verbose inline caching logic.
- **FR-005**: System MUST decompose the monolithic service file into focused modules, each containing fewer than 800 lines of code, organized by domain responsibility.
- **FR-006**: System MUST use composition over inheritance for the decomposed service modules, with each module accessing shared functionality through a client reference rather than class inheritance.
- **FR-007**: System MUST maintain a backward-compatible facade that re-exports all public symbols from decomposed modules, ensuring existing imports continue to work without modification.
- **FR-008**: System MUST replace the module-level singleton pattern with dependency injection via application state and a dependency provider function.
- **FR-009**: System MUST consolidate all service initialization into a single path through the application lifespan, application state, and dependency injection, removing module-level instantiation and lazy singleton patterns.
- **FR-010**: System MUST provide a frontend CRUD hook factory that generates standard create, read, update, and delete operations for any resource from a shared configuration.
- **FR-011**: System MUST provide a unified settings hook that serves user, global, and project settings through a single generic hook parameterized by API method and query key factory.
- **FR-012**: System MUST provide shared frontend UI components for modals, preview cards, and error alerts to replace duplicated UI patterns across the application.
- **FR-013**: System MUST provide a centralized query key registry for all frontend data-fetching queries, eliminating inline hardcoded query key strings.
- **FR-014**: System MUST split the ChatInterface megacomponent into focused sub-components (message list and input) with clearly separated concerns.
- **FR-015**: System MUST provide an API endpoint factory that generates standard API call functions for a resource group from a base path and method definitions.
- **FR-016**: System MUST consolidate all backend test mock factories into the shared test configuration, replacing scattered helper files and inline patches with reusable fixtures.
- **FR-017**: System MUST ensure that all existing backend tests (47+ unit, 3+ integration) and frontend tests (29+ unit, 9+ E2E) pass after all changes are applied.

### Key Entities

- **Shared Helper**: A reusable function or dependency (repository resolution, error handling, validation, caching) that replaces duplicated inline logic across multiple API endpoints.
- **Service Module**: A focused sub-module of the decomposed service, responsible for a single domain area (projects, issues, pull requests, etc.) and composed via a shared client reference.
- **Backward-Compatible Facade**: The package-level re-export layer that maps all previously-public symbols to their new locations in the decomposed modules, ensuring zero-disruption migration.
- **CRUD Hook Factory**: A frontend hook generator that produces standard create, read, update, and delete operations for any resource type from a shared configuration object.
- **API Endpoint Factory**: A frontend function generator that produces typed API call functions for a resource group from a base path and set of method definitions.
- **Query Key Registry**: A centralized map of all query keys used by the frontend data-fetching layer, ensuring consistent cache invalidation and preventing key collisions.

## Assumptions

- The existing canonical repository resolution function is correct and feature-complete — only its adoption by all callers is required.
- The existing error handling helpers are correct and feature-complete — they only need to be wired into the API endpoints that currently use inline error handling.
- Composition over inheritance is the confirmed architectural decision for the service decomposition, as stated in the issue context.
- The backward-compatible facade approach (re-exports in the package init) provides a safe migration path that avoids a big-bang refactor of all 17+ files that import from the service module.
- Frontend and backend changes have no cross-dependencies and can proceed in parallel, as stated in the issue context.
- The CRUD hook factory pattern is applicable to at least the agents and chores hooks, which share the most structural similarity.
- The 8-module decomposition target (client, projects, issues, pull requests, copilot, fields, board, repository) is the confirmed split, as defined in the issue context.
- Phase sequencing (Phase 1 before Phase 2, Phase 5 after Phases 1–3) is required to reduce risk and avoid conflicting changes.
- Dependency version upgrades, UI redesign, and CI/coverage improvements are explicitly out of scope per the issue context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Total lines of duplicated code across backend and frontend are reduced by at least 1,500 lines compared to the pre-refactoring baseline.
- **SC-002**: The monolithic service file (currently ~4,950 lines) is decomposed into 8 modules, each containing fewer than 800 lines.
- **SC-003**: Zero results are returned when searching the codebase for the legacy repository resolution function, confirming all duplicate implementations have been removed.
- **SC-004**: 80% or more of API endpoints use the shared error handling helpers rather than inline error processing.
- **SC-005**: Session project validation logic exists in exactly one location (the shared validation dependency), with zero inline guard clauses remaining in API endpoint handlers.
- **SC-006**: All service initialization follows a single pattern (lifespan → application state → dependency injection), with zero module-level singletons or lazy instantiation patterns remaining.
- **SC-007**: Application starts successfully and the OAuth authentication flow works end-to-end after all initialization changes are applied.
- **SC-008**: Frontend CRUD hook factory, shared UI components, query key registry, and API endpoint factory are implemented, reducing frontend duplication by at least 1,000 lines.
- **SC-009**: All existing backend tests (47+ unit, 3+ integration) pass after all refactoring changes are applied.
- **SC-010**: All existing frontend tests (29+ unit, 9+ E2E) pass after all refactoring changes are applied.
- **SC-011**: The ChatInterface component is split into focused sub-components, with no single component exceeding 200 lines.
- **SC-012**: All backend test mock factories are located in a single shared configuration file, with zero scattered helper files or inline mock patches remaining.
