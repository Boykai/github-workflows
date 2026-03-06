# Feature Specification: Full Codebase Review & Refactoring

**Feature Branch**: `023-codebase-review-refactor`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Systematic review of the GitHub Projects Chat application (FastAPI backend + React frontend) to improve simplicity, modernize dependencies, eliminate DRY violations, and enforce best practices. Approach: audit → analyze → plan refactors → implement in priority order across 6 phases."

## Assumptions

- The application is a full-stack GitHub Projects management tool with a FastAPI backend (~15 runtime dependencies, ~4,870 LOC service monolith) and a React frontend (~54 components).
- The backend service layer (`service.py`) contains 78 methods (64 public) spanning projects, issues, PRs, Copilot, fields, board, commits, and infrastructure — all in a single file.
- The backend uses a transitional initialization pattern: `lifespan` + `app.state` coexists with module-level globals and lazy singletons across `dependencies.py`, `main.py`, and 17+ files that import services directly.
- Error handling utilities (`handle_service_error`, `safe_error_response`) exist in `logging_utils.py` but are underutilized — most endpoints reinvent error handling inline.
- Repository resolution logic is duplicated across `utils.py` (canonical 3-step fallback), `workflow.py` (cache-only variant), and `main.py` (inline duplication).
- Spec 020 (githubkit migration) targets reducing `service.py` to ~3,500 LOC by replacing hand-rolled httpx infrastructure with the githubkit SDK. This review is broader and complementary.
- Spec 022 (API rate limit protection) addresses WebSocket refresh loops and sub-issue caching. This review scopes those as already-planned work and does not duplicate them.
- The frontend test suite has 29+ test files and the backend has 18+ test classes. All existing tests must continue passing after each refactoring step.
- No user-visible behavior changes result from this work — all changes are internal quality improvements.
- React 19 and Tailwind v4 migrations are deferred to separate dedicated efforts due to their scope and breaking-change risk.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Backend DRY Consolidation (Priority: P1)

As a developer maintaining the backend, I want duplicated patterns (repository resolution, error handling, cache boilerplate, validation guards) consolidated into single reusable implementations so that bug fixes and behavior changes only need to happen in one place.

**Why this priority**: DRY violations are the highest-impact maintainability issue. The same logic in 3-8 places means bugs must be fixed N times, and divergence between copies creates subtle inconsistencies. This delivers the most maintainability value per line changed.

**Independent Test**: After consolidation, grep the codebase for each pattern to confirm exactly one authoritative implementation exists, and verify all existing tests pass without modification (except import path changes).

**Acceptance Scenarios**:

1. **Given** the repository resolution logic exists in `utils.py`, `workflow.py`, and `main.py`, **When** consolidation is complete, **Then** all call sites use the single `resolve_repository()` function from `utils.py` and no inline duplicates remain.
2. **Given** API endpoints catch exceptions and construct error responses inline, **When** the error handling helpers are adopted, **Then** at least 80% of API endpoint error paths use `handle_service_error()` or `safe_error_response()` instead of inline try/except/raise patterns.
3. **Given** multiple endpoints check `session.selected_project_id` with the same validation pattern, **When** a shared validation dependency is created, **Then** all 5+ endpoints use the shared dependency and no inline validation duplicates remain.
4. **Given** cache check/refresh boilerplate is duplicated across 4+ files, **When** a generic cached-fetch wrapper is created, **Then** all cache access patterns use the wrapper and no inline cache boilerplate remains.

---

### User Story 2 — Service Layer Decomposition (Priority: P2)

As a developer working on the GitHub API integration, I want the ~4,870 LOC service monolith split into logical, focused modules so that I can navigate, understand, and modify individual concerns without loading the entire file.

**Why this priority**: The service monolith is the single largest complexity hotspot. Splitting it into focused modules (projects, issues, pull requests, copilot, fields, board, client infrastructure) makes each piece independently comprehensible. This also unblocks the githubkit migration (spec 020) by providing smaller, more manageable files to migrate.

**Independent Test**: After decomposition, verify that each new module is under 800 LOC, all 78 methods are accessible through the existing service interface (backward-compatible facade), and the full backend test suite passes.

**Acceptance Scenarios**:

1. **Given** `service.py` contains 78 methods across 7+ concern areas, **When** decomposition is complete, **Then** each concern area lives in its own module file and no single module exceeds 800 LOC.
2. **Given** 17+ files import from the service layer directly, **When** the facade pattern is applied, **Then** all existing imports continue to work without modification through the backward-compatible entry point.
3. **Given** the service decomposition is complete, **When** the full backend test suite runs, **Then** all tests pass with at most import-path updates to test mocks.

---

### User Story 3 — Dependency Audit & Modernization (Priority: P3)

As a project maintainer, I want all backend and frontend dependencies audited against their latest stable versions, redundant dependencies removed, and version constraints updated so that the project benefits from security patches, performance improvements, and reduced dependency surface area.

**Why this priority**: Dependency hygiene is lower-urgency than structural improvements but prevents technical debt from compounding. Removing unused dependencies reduces attack surface and install time. Updating version constraints ensures compatibility with security fixes.

**Independent Test**: Run dependency installation from a clean environment and verify no version conflicts, no unused dependency warnings, and all tests pass. Confirm removed dependencies have zero import references.

**Acceptance Scenarios**:

1. **Given** `tenacity>=8.2.0` is declared as a dependency, **When** the audit determines it is unused (custom retry logic is used instead), **Then** the dependency is removed and no import references to `tenacity` exist in the codebase.
2. **Given** the frontend lists both `jsdom` and `happy-dom` as test dependencies but vitest only uses `happy-dom`, **When** the audit is complete, **Then** the unused test environment package is removed.
3. **Given** backend dependencies have minimum versions from early 2024, **When** the version audit is complete, **Then** all dependency version floors are updated to their latest stable minor versions compatible with the application.
4. **Given** frontend `@dnd-kit` packages have a major version mismatch (`core@6.3.1` vs `sortable@10.0.0`), **When** the audit is complete, **Then** all `@dnd-kit` packages are aligned to compatible versions.

---

### User Story 4 — Initialization Pattern Consolidation (Priority: P3)

As a developer, I want the backend to use a single consistent initialization pattern for services so that service lifetime and dependency injection are predictable and there is one obvious way to access any service.

**Why this priority**: Three competing patterns (lifespan `app.state`, module-level globals, lazy singletons) create confusion about which approach is canonical. Consolidating to one pattern reduces cognitive overhead, but the functional impact is lower than DRY or decomposition work.

**Independent Test**: After consolidation, grep for module-level service singletons and verify they are replaced by the consolidated pattern. All tests and the application startup sequence must pass.

**Acceptance Scenarios**:

1. **Given** services are accessible via `app.state`, module-level globals, and lazy singletons, **When** consolidation is complete, **Then** all services are initialized via the lifespan handler and accessed exclusively through dependency injection.
2. **Given** 17+ files import services directly at module level, **When** the migration is complete, **Then** all service access goes through dependency-injection parameters and no module-level service imports remain outside of `dependencies.py`.

---

### User Story 5 — Frontend Quality Improvements (Priority: P4)

As a frontend developer, I want large components identified and refactored, duplicate hook/service patterns consolidated, type safety improved, and accessibility coverage verified so that the frontend is maintainable and meets quality standards.

**Why this priority**: Frontend quality work is important but lower-priority than backend structural issues because the backend service layer is the primary complexity bottleneck. Frontend improvements can proceed in parallel once the backend work is scoped.

**Independent Test**: After cleanup, verify no component exceeds 300 LOC, no `: any` type annotations remain in production code, all frontend unit tests pass, and the eslint accessibility plugin reports no new violations.

**Acceptance Scenarios**:

1. **Given** some components in `chat/` and `board/` exceed 300 LOC, **When** refactoring is complete, **Then** every component file is under 300 LOC with extracted sub-components or hooks.
2. **Given** hooks and API services may contain duplicate fetch/mutation patterns, **When** the DRY review is complete, **Then** shared patterns are extracted into reusable utilities with no duplicate implementations.
3. **Given** the codebase may contain `: any` type annotations, **When** the type-safety pass is complete, **Then** zero `: any` annotations exist in production source files (test files excepted).
4. **Given** the frontend uses accessibility testing libraries, **When** the accessibility audit is complete, **Then** all interactive components pass automated accessibility checks.

---

### User Story 6 — Best Practices & CI Enforcement (Priority: P4)

As a project maintainer, I want security best practices enforced, CI artifacts improved, and quality gates automated so that regressions are caught before they reach production.

**Why this priority**: Best practices enforcement is the final layer — it codifies the quality improvements from earlier phases into automated checks that prevent regression. It depends on the earlier phases being complete.

**Independent Test**: Verify that CI runs all linters, tests, and coverage checks; that dependency vulnerability scanning is active; and that the pre-commit hook runs in CI.

**Acceptance Scenarios**:

1. **Given** CI does not currently publish coverage artifacts, **When** CI is updated, **Then** test coverage reports are generated and accessible as build artifacts for both backend and frontend.
2. **Given** no automated dependency vulnerability scanning is configured, **When** scanning is added, **Then** builds fail on known critical or high-severity vulnerabilities in dependencies.
3. **Given** `python-jose` has known maintenance concerns, **When** the security audit is complete, **Then** the JWT library choice is either validated as safe for the current use case or replaced with an actively maintained alternative.

### Edge Cases

- What happens if a DRY consolidation changes error message formats that external consumers (e.g., the frontend) depend on? All error response shapes must be preserved exactly.
- What happens if service decomposition breaks circular imports? Each module's imports must be validated and any circular dependencies resolved via dependency inversion or lazy imports.
- What happens if a dependency version update introduces breaking changes in transitive dependencies? Each update must be tested individually with the full test suite before combining updates.
- What happens if removing a "redundant" dependency breaks an import that's used conditionally (e.g., `tenacity` used in a code path not covered by tests)? Verify zero import references via static analysis (grep + linter) before removal.
- What happens if the service facade introduces a performance overhead for high-frequency internal calls? The facade must be a thin pass-through with negligible overhead; measure response times before and after.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1: Dependency Audit & Modernization**

- **FR-001**: System MUST have all backend dependency version floors updated to the latest compatible stable versions as of March 2026.
- **FR-002**: System MUST NOT include any dependency that has zero import references in the codebase (backend and frontend).
- **FR-003**: The `@dnd-kit` frontend packages MUST all be at compatible major versions with no cross-package version mismatch.
- **FR-004**: System MUST NOT include redundant test-environment packages (only the actively configured test environment package is retained).

**Phase 2: Backend DRY Consolidation**

- **FR-005**: All repository resolution call sites MUST use the single canonical `resolve_repository()` function. No inline or variant implementations may exist.
- **FR-006**: All API endpoint error handling MUST use the shared error handling utilities from `logging_utils.py`. Inline try/except/raise patterns for service errors are not permitted.
- **FR-007**: All endpoints that require a selected project MUST use a shared validation dependency. Inline `if not session.selected_project_id` checks are not permitted.
- **FR-008**: All cache access patterns MUST use a shared cache-fetch wrapper. Inline cache check/refresh boilerplate is not permitted.
- **FR-009**: All test mock setup MUST be centralized in `conftest.py` fixtures. Duplicate mock setup across test files is not permitted.

**Phase 3: Service Layer Decomposition**

- **FR-010**: The `service.py` monolith MUST be decomposed into focused modules, each under 800 LOC, organized by concern area (projects, issues, pull requests, copilot, fields, board, client infrastructure).
- **FR-011**: A backward-compatible facade MUST preserve the existing public interface so that all existing imports and call sites continue to work.
- **FR-012**: Every public method currently on `GitHubProjectsService` MUST remain accessible through the decomposed module structure.

**Phase 4: Initialization Consolidation**

- **FR-013**: All service initialization MUST go through a single pattern (lifespan + dependency injection). Module-level service globals outside `dependencies.py` are not permitted.

**Phase 5: Frontend Quality**

- **FR-014**: No single component file in the frontend MUST exceed 300 LOC.
- **FR-015**: No `: any` type annotations MUST exist in frontend production source files.
- **FR-016**: All interactive frontend components MUST pass automated accessibility checks.

**Phase 6: CI & Best Practices**

- **FR-017**: CI MUST generate and publish test coverage artifacts for both backend and frontend.
- **FR-018**: CI MUST include automated dependency vulnerability scanning that fails on critical/high vulnerabilities.
- **FR-019**: The JWT library used by the backend MUST be validated as actively maintained and free of known vulnerabilities, or replaced.

## Dependencies & Sequencing

- **Phase 1** (Dependency Audit) and **Phase 2** (Backend DRY) can run in parallel.
- **Phase 3** (Service Decomposition) depends on Phase 2 completion — consolidated patterns must be in place before splitting files.
- **Phase 4** (Initialization Consolidation) depends on Phase 3 — service modules must be stable before changing how they are initialized.
- **Phase 5** (Frontend Quality) can run in parallel with Phases 2-4.
- **Phase 6** (CI & Best Practices) depends on Phases 1-5 — enforcement gates require the codebase to already meet the standards.

## Cross-References

- **Spec 020 (githubkit migration)**: Targets replacing hand-rolled httpx infrastructure in `service.py` with the githubkit SDK. This review's Phase 3 (service decomposition) should happen **before** the githubkit migration — smaller files are easier to migrate. The two specs are complementary, not overlapping.
- **Spec 022 (API rate limit protection)**: Addresses WebSocket refresh loops and sub-issue caching. This review does not duplicate that scope. Phase 2 cache consolidation may provide shared infrastructure that spec 022 benefits from.

## Scope Exclusions

- React 19 migration (significant breaking changes; deferred to dedicated effort).
- Tailwind v4 migration (major config overhaul; deferred to dedicated effort).
- Signal integration deep-dive and MCP configurations.
- New feature development — this spec is strictly about improving existing code quality.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The largest single source file in the backend is under 800 LOC (down from ~4,870 LOC).
- **SC-002**: The total number of distinct repository-resolution implementations is exactly 1 (down from 3).
- **SC-003**: 80% or more of API endpoint error paths use the shared error handling utilities (up from ~0%).
- **SC-004**: Zero redundant dependencies remain — every declared dependency has at least one import reference in production code.
- **SC-005**: All existing backend tests (47+ unit, 3+ integration) and frontend tests (29+ unit, 9+ E2E) pass after every phase.
- **SC-006**: Developers can locate any GitHub API method's implementation in under 30 seconds by navigating to the appropriately named module (vs. scrolling through a 4,870-line file).
- **SC-007**: CI pipelines publish coverage artifacts and fail on critical dependency vulnerabilities.
- **SC-008**: No component in the frontend exceeds 300 LOC.
