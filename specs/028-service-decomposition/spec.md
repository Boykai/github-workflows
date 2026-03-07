# Feature Specification: Decompose service.py Monolith into 8 Focused Modules (Phase 2)

**Feature Branch**: `028-service-decomposition`
**Created**: 2026-03-07
**Status**: Draft
**Input**: User description: "Decompose service.py Monolith into 8 Focused Modules (Phase 2)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Extract HTTP/GraphQL Transport Layer (Priority: P1)

As a developer working on the GitHub integration, I want the low-level HTTP and GraphQL transport logic isolated in its own module so that I can modify retry policies, rate-limit handling, and request coalescing without scrolling through thousands of lines of unrelated business logic.

**Why this priority**: The transport layer is the foundation that all other modules depend on. Extracting it first establishes a clean base that subsequent extractions build upon. It also carries the lowest risk because transport methods have no domain-specific callers to break.

**Independent Test**: Can be fully tested by running the existing test suite after extracting transport methods (`_rest`, `_rest_response`, `_graphql`, `rest_request`, `_with_fallback`, rate-limit accessors, request coalescing, and lifecycle methods) into a standalone module. All existing tests must continue to pass with no modifications to test files.

**Acceptance Scenarios**:

1. **Given** the monolithic `service.py` containing 78 methods, **When** the HTTP infrastructure and GraphQL transport methods are extracted into `client.py`, **Then** the new module contains only transport-related methods and is under 800 lines of code.
2. **Given** `client.py` has been extracted, **When** the full automated test suite is run, **Then** all tests pass with zero regressions.
3. **Given** `client.py` exists as a separate module, **When** existing callers import from the package, **Then** they continue to work without any import changes due to facade re-exports.

---

### User Story 2 — Extract Domain Modules One at a Time (Priority: P1)

As a developer, I want each business domain (projects, issues, pull requests, copilot, fields, board, repository) encapsulated in its own module so that I can locate, understand, and modify domain-specific logic quickly without risk of unintended side effects in unrelated areas.

**Why this priority**: This is the core deliverable. Splitting the 78-method God object into focused, single-responsibility modules directly addresses the maintainability, readability, and testability problems caused by the monolith.

**Independent Test**: After each individual module extraction, the full automated test suite is run. Each extraction is verified independently before proceeding to the next one. The linter is run after every extraction to catch import or style issues.

**Acceptance Scenarios**:

1. **Given** the transport layer has been extracted, **When** the remaining domain methods are extracted into 7 modules (`projects.py`, `issues.py`, `pull_requests.py`, `copilot.py`, `fields.py`, `board.py`, `repository.py`), **Then** each module is under 800 lines of code and contains only methods matching its declared responsibility scope.
2. **Given** any single domain module has been extracted, **When** the automated test suite is run immediately after that extraction, **Then** all tests pass with zero regressions before the next extraction begins.
3. **Given** all 8 modules have been extracted, **When** the linter is run across all new and modified files, **Then** it reports zero errors.
4. **Given** all 8 modules exist, **When** any module is inspected for imports, **Then** no circular import chains exist between the new modules.

---

### User Story 3 — Preserve Backward Compatibility via Facade (Priority: P1)

As an existing consumer of the GitHub Projects service, I want the package's public interface to remain unchanged during the transition so that my code continues to work without any modifications while the internal restructuring takes place.

**Why this priority**: There are 17+ files that directly import the singleton or the service class. Breaking these imports would cause widespread failures across the entire application. Backward compatibility is a non-negotiable constraint for safe delivery.

**Independent Test**: Can be verified by confirming that every file currently importing from the package compiles and passes tests without any import-path changes. A grep across the codebase confirms no caller modifications were needed.

**Acceptance Scenarios**:

1. **Given** all 8 modules have been extracted, **When** the package `__init__.py` is inspected, **Then** it re-exports `GitHubProjectsService`, `github_projects_service`, and `GitHubClientFactory` exactly as before.
2. **Given** the facade re-exports are in place, **When** any of the 17+ consuming files are inspected, **Then** none of them have been modified to change import paths.
3. **Given** the full extraction is complete, **When** the entire application is started and exercised, **Then** all features work identically to before the refactoring.

---

### User Story 4 — Replace Module-Level Singleton with Dependency Injection (Priority: P2)

As a developer, I want the module-level `github_projects_service` singleton removed and replaced with proper dependency injection so that the service can be tested in isolation, multiple instances can coexist, and the application follows modern software architecture practices.

**Why this priority**: While important for long-term code quality, this step depends on all 8 modules being extracted first. It also requires updating 17+ import sites across the codebase, making it the highest-risk change. It is sequenced after the safer structural extraction.

**Independent Test**: Can be verified by removing the singleton instantiation, updating all 17+ import sites to use dependency injection, and confirming the full test suite passes. A grep for the old singleton import pattern confirms it no longer appears anywhere in the codebase.

**Acceptance Scenarios**:

1. **Given** all 8 modules are extracted and the facade is in place, **When** the module-level `github_projects_service` singleton is removed from `service.py`, **Then** no file in the codebase directly imports the singleton object.
2. **Given** the singleton has been removed, **When** each of the 17+ consuming files is inspected, **Then** each obtains the service instance via the dependency injection mechanism rather than a direct module-level import.
3. **Given** dependency injection is in place, **When** the full automated test suite is run, **Then** all tests pass with zero regressions.

---

### User Story 5 — Improve Developer Onboarding and Navigation (Priority: P3)

As a new team member, I want the GitHub Projects service organized into clearly named, small modules so that I can understand the codebase structure within my first day and find the relevant code for any task in under a minute.

**Why this priority**: Developer experience is a downstream benefit of the structural improvements. It does not require any additional implementation work beyond what Stories 1-4 deliver, but it represents an important measurable outcome.

**Independent Test**: Can be verified by having a developer unfamiliar with the codebase locate a specific method (e.g., "find where pull requests are merged") and measuring the time to locate the correct file and method.

**Acceptance Scenarios**:

1. **Given** all 8 modules are extracted with clear responsibility scopes, **When** a developer needs to find issue-related logic, **Then** they can navigate directly to `issues.py` without searching through unrelated code.
2. **Given** each module is under 800 lines, **When** a developer opens any single module, **Then** they can read and understand the entire module's scope within a single session.

---

### Edge Cases

- What happens if a method logically belongs to two modules (e.g., linking a PR to an issue involves both PR and issue logic)? The method is placed in the module that owns the primary entity being acted upon, with the other module calling it via a well-defined interface.
- What happens if extracting a module introduces a circular import between two new modules? The shared dependency is factored out into the transport layer (`client.py`) or into a shared types/utilities location that both modules can import from.
- What happens if a test file mocks `service.py` methods by path (e.g., `patch("src.services.github_projects.service.GitHubProjectsService.some_method")`)? The facade re-exports ensure the old import paths continue to resolve. Test patches referencing the original module path still work.
- What happens if the singleton is removed but a background task still holds a stale reference? All background tasks and polling loops must obtain the service instance through the dependency injection mechanism at invocation time, not at module-import time.
- What happens if one module extraction breaks an unrelated test due to import ordering changes? Each extraction is followed immediately by a full test run, isolating the exact change that introduced the failure for quick diagnosis and rollback.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The monolithic `service.py` MUST be decomposed into exactly 8 focused modules: `client.py`, `projects.py`, `issues.py`, `pull_requests.py`, `copilot.py`, `fields.py`, `board.py`, and `repository.py`.
- **FR-002**: Each extracted module MUST contain fewer than 800 lines of code.
- **FR-003**: Each module MUST have a single, clearly scoped responsibility matching the target decomposition table:

  | Module             | Responsibility                                            |
  | ------------------ | --------------------------------------------------------- |
  | `client.py`        | HTTP infrastructure, request retry, GraphQL transport, rate limits, request coalescing |
  | `projects.py`      | List and retrieve projects                                |
  | `issues.py`        | Issue CRUD, completion detection, sub-issues              |
  | `pull_requests.py` | PR CRUD, merge, review, branch operations                 |
  | `copilot.py`       | Copilot assignment, bot ID detection, polling helpers      |
  | `fields.py`        | Project field queries and mutations                       |
  | `board.py`         | Board queries, data retrieval, reconciliation             |
  | `repository.py`    | Repository info, branch/commit workflow, file operations  |

- **FR-004**: The package `__init__.py` MUST re-export `GitHubProjectsService`, `github_projects_service`, and `GitHubClientFactory` to preserve backward compatibility with all existing callers.
- **FR-005**: Modules MUST be extracted one at a time, with the full automated test suite passing after each individual extraction before the next extraction begins.
- **FR-006**: The linter MUST pass cleanly across all new and modified files after each extraction.
- **FR-007**: No circular import chains MUST exist between any of the 8 new modules.
- **FR-008**: The module-level `github_projects_service` singleton MUST be removed after all 8 modules are extracted.
- **FR-009**: All 17+ files that currently import the singleton MUST be updated to obtain the service instance via dependency injection.
- **FR-010**: The existing `dependencies.py` dependency injection mechanism MUST be used (or extended) to provide the service instance to all consumers.
- **FR-011**: Extractions MUST proceed in a defined order starting with the transport layer (`client.py`) since it has no domain-specific callers and is depended upon by all other modules.
- **FR-012**: Shared utility methods (e.g., static helper methods, cache management) MUST be placed in a location accessible to all modules without creating circular dependencies.

### Key Entities

- **GitHubProjectsService**: The existing monolithic service class (78 methods, ~4,913 LOC) that currently handles all GitHub Projects V2 interactions. After decomposition, it serves as a coordinator or is replaced by the individual domain modules.
- **GitHubClientFactory**: Connection pool manager for authenticated GitHub client instances. Already exists in `__init__.py` and is shared across all modules.
- **Module Facade (`__init__.py`)**: The package entry point that re-exports public symbols, ensuring backward compatibility during and after the transition.
- **Dependency Injection Provider (`dependencies.py`)**: The mechanism that supplies service instances to request handlers and background tasks, replacing direct singleton imports.
- **Domain Modules**: The 8 new focused modules, each encapsulating a specific area of GitHub Projects functionality with clear boundaries.

## Assumptions

- Phase 1 of the Simplicity & DRY Refactoring plan has been completed or is not a blocking prerequisite for the module extraction work.
- The existing automated test suite (1,153+ backend tests) provides sufficient coverage to detect regressions introduced by the refactoring.
- The `GitHubClientFactory` in `__init__.py` remains in its current location and is shared by all new modules via import.
- Methods that span multiple domains (e.g., linking PRs to issues) are assigned to the module owning the primary entity, with cross-module calls using standard imports.
- The singleton removal and dependency injection migration can be performed as the final step after all structural extractions are verified.
- Test files may need to be updated to mock new module paths, but the facade re-exports should minimize this.
- Background services and polling loops will be updated to use dependency injection at invocation time rather than holding module-level references.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 8 modules exist and every module contains fewer than 800 lines of code, verified by line count inspection.
- **SC-002**: The full automated test suite (1,153+ tests) passes with zero regressions after the complete decomposition.
- **SC-003**: Zero circular import chains exist between the new modules, verified by successful application startup and an import dependency analysis.
- **SC-004**: Zero files outside the `github_projects` package require import-path changes during the module extraction phase (backward compatibility preserved via facade).
- **SC-005**: The module-level singleton pattern is eliminated — zero occurrences of direct `github_projects_service` singleton imports remain in the codebase after the dependency injection migration.
- **SC-006**: The linter reports zero errors across all new and modified files.
- **SC-007**: A developer can locate any GitHub Projects method by navigating to the appropriately named module file in under 30 seconds, compared to searching a 4,913-line monolith.
- **SC-008**: Each module extraction is individually verified by a passing test suite run, with 8 sequential green test runs documented during the extraction process.
