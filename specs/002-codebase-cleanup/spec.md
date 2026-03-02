# Feature Specification: Codebase Cleanup — Reduce Technical Debt and Improve Maintainability

**Feature Branch**: `002-codebase-cleanup`  
**Created**: 2026-03-02  
**Status**: Draft  
**Input**: User description: "Codebase Cleanup: Reduce Technical Debt and Improve Maintainability — Perform a thorough codebase cleanup across the entire repository (backend, frontend, scripts, specs) to improve maintainability and reduce technical debt. Make the actual code changes, commit them, and open or update a PR with a summary comment of all changes made."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove Dead Code and Unused Artifacts (Priority: P1)

As a developer, I want all dead code paths, unused imports, unused variables, unreachable functions, commented-out logic, and orphaned test artifacts removed from the codebase so that the code I read and maintain reflects only what the system actually uses.

**Why this priority**: Dead code is the single largest contributor to confusion during development. Removing it immediately improves readability for every contributor and eliminates false signals during code search and refactoring. This also addresses the visible MagicMock database file artifacts cluttering the backend workspace root.

**Independent Test**: Can be fully tested by running the full CI suite (linting, type-checking, unit tests, build) after removals and confirming all checks pass with zero regressions. A manual review confirms no removed symbol is imported or called anywhere in the codebase.

**Acceptance Scenarios**:

1. **Given** the codebase contains functions, methods, or components that are defined but never imported or called, **When** these unused definitions are removed, **Then** the CI suite passes and no runtime errors occur.
2. **Given** there are commented-out code blocks (not documentation comments) in source files, **When** these blocks are removed, **Then** the files contain only active logic and documentation comments.
3. **Given** there are unused imports, variables, or type definitions across backend and frontend, **When** they are removed, **Then** linting and type-checking tools report no new errors.
4. **Given** there are MagicMock-generated database files in the backend workspace root, **When** these artifacts are deleted, **Then** the workspace root contains only expected project files and directories.
5. **Given** there are unused route handlers with no corresponding frontend calls or test coverage, **When** they are removed, **Then** no frontend functionality breaks and no test targets the removed route.

---

### User Story 2 - Eliminate Stale and Meaningless Tests (Priority: P2)

As a developer, I want stale tests—tests that target deleted functionality, tests that mock internals so heavily they validate nothing real, and tests for code paths that no longer exist—removed so that the test suite is a reliable indicator of system health.

**Why this priority**: Stale tests create false confidence and slow down CI. Removing them makes the test suite trustworthy and faster, which directly supports confident refactoring and deployment.

**Independent Test**: Can be fully tested by running the complete test suite after removals and confirming all remaining tests pass. A review confirms that every removed test targeted non-existent code or was purely mocking internal wiring with no behavioral assertion.

**Acceptance Scenarios**:

1. **Given** there are test files or test cases testing deleted or refactored functionality, **When** these tests are removed, **Then** the remaining test suite passes and all tested functionality still has coverage.
2. **Given** there are tests that mock internals so heavily they do not test real behavior, **When** these tests are removed, **Then** no meaningful coverage is lost (the behavior is covered by other integration or unit tests, or the underlying code no longer exists).
3. **Given** there are leftover test artifacts (e.g., MagicMock-generated files in the workspace root), **When** they are cleaned up, **Then** the workspace root and test directories contain only intentional project files.

---

### User Story 3 - Consolidate Duplicated Logic (Priority: P3)

As a developer, I want near-duplicate functions, utility helpers, service methods, and copy-pasted test patterns consolidated into single implementations so that bug fixes and enhancements need to be made in only one place.

**Why this priority**: Duplication leads to divergence over time—one copy gets updated while another doesn't. Consolidation reduces the surface area for bugs and makes the codebase easier to reason about.

**Independent Test**: Can be fully tested by running the full CI suite after consolidation and confirming all tests pass. A diff review confirms that each consolidated function replaces all former duplicates and call sites are updated.

**Acceptance Scenarios**:

1. **Given** there exist near-duplicate utility functions or service methods that perform the same operation with minor variations, **When** they are merged into a single canonical implementation, **Then** all call sites use the consolidated version and all tests pass.
2. **Given** there are copy-pasted patterns in test files that could leverage shared helpers or factories (existing helpers in factories.py and mocks.py), **When** test code is refactored to use these shared utilities, **Then** the test files are shorter, tests still pass, and the shared helpers cover the common patterns.
3. **Given** there are duplicated model definitions or overlapping type definitions across backend or frontend, **When** they are consolidated, **Then** a single definition exists and all consumers reference it.

---

### User Story 4 - Remove Backwards-Compatibility Shims (Priority: P4)

As a developer, I want compatibility layers, polyfills, adapter code, and conditional branches that exist only to support older API shapes, deprecated config formats, or migration-period aliases removed so that the code reflects only the current system behavior.

**Why this priority**: Compatibility shims add complexity and make it unclear what the "real" code path is. They can mask bugs when the legacy path is triggered accidentally. Removing them simplifies control flow.

**Independent Test**: Can be fully tested by running the full CI suite after removal and confirming all checks pass. A search for patterns like `if old_format:`, `if legacy:`, `# deprecated`, or `# compat` confirms none remain.

**Acceptance Scenarios**:

1. **Given** there are conditional branches guarding legacy/old-format code paths, **When** the legacy branches are removed and only the current path is retained, **Then** the system behaves identically and all tests pass.
2. **Given** there are adapter functions or alias mappings for deprecated configurations, **When** they are removed, **Then** no configuration file or runtime path references the old names.

---

### User Story 5 - General Hygiene and Dependency Cleanup (Priority: P5)

As a developer, I want orphaned configs, stale TODO/FIXME/HACK comments referencing completed work, unused dependencies, and unused Docker Compose services cleaned up so that the project metadata accurately reflects what the system needs and what remains to be done.

**Why this priority**: While lower urgency than code-level cleanup, stale metadata and unused dependencies increase cognitive overhead, slow down installs, and can introduce security vulnerabilities through abandoned packages.

**Independent Test**: Can be fully tested by performing a clean install of all dependencies after cleanup and running the full CI suite. A grep for TODO/FIXME/HACK confirms only actionable items remain.

**Acceptance Scenarios**:

1. **Given** there are TODO, FIXME, or HACK comments referencing work that has been completed, **When** they are removed, **Then** only comments referencing genuinely outstanding work remain.
2. **Given** there are dependencies listed in project manifests that are not imported or used anywhere in the code, **When** they are removed from the manifests, **Then** clean installs succeed and all tests pass.
3. **Given** there are orphaned configuration files or migration files referencing deleted features, **When** they are removed, **Then** no runtime or build process references them.
4. **Given** there are unused Docker Compose services or environment variables, **When** they are removed, **Then** the Docker stack starts successfully with the remaining configuration.

---

### Edge Cases

- What happens if a function appears unused via static analysis but is invoked dynamically (e.g., string-based plugin loading, migration discovery, or reflection)? Dynamic invocations must be confirmed as truly absent before removing the function.
- What happens if a test file covers functionality that is only exercised in production through a rarely-used code path? The code path must be traced end-to-end to confirm it is genuinely dead before removing its test.
- What happens if removing an "unused" dependency breaks a transitive dependency relied upon implicitly? Dependency removal must be validated by a full clean install and test run.
- What happens if consolidating two near-duplicate functions reveals subtle behavioral differences relied upon by different callers? All call sites must be audited for reliance on the differing behavior before merging.
- What happens if a compatibility shim is still referenced in external documentation, deployment scripts, or CI configuration outside the repository? Only in-repo references are in scope; external references should be flagged but not block cleanup.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All functions, methods, classes, and components that are defined but never imported or called anywhere in the codebase MUST be removed.
- **FR-002**: All commented-out code blocks (excluding documentation comments and intentional examples) MUST be removed from source files.
- **FR-003**: All unused imports, unused variables, and unused type definitions MUST be removed from all source files.
- **FR-004**: All MagicMock-generated database file artifacts present in the backend workspace root MUST be deleted.
- **FR-005**: All unused route handlers (API endpoints with no corresponding frontend calls and no test coverage) MUST be removed.
- **FR-006**: All unused React components, hooks, and utility functions in the frontend MUST be removed.
- **FR-007**: All test files or test cases that test deleted or refactored functionality MUST be removed.
- **FR-008**: All tests that mock internals so heavily they do not test any real behavior MUST be removed, provided the tested behavior is either covered elsewhere or no longer exists.
- **FR-009**: Near-duplicate functions, utility helpers, and service methods MUST be consolidated into single canonical implementations with all call sites updated.
- **FR-010**: Copy-pasted patterns in test files MUST be refactored to use shared helpers or factories where such helpers already exist (factories.py, mocks.py).
- **FR-011**: Duplicated model definitions and overlapping type definitions MUST be consolidated into single definitions.
- **FR-012**: Compatibility layers, polyfills, conditional legacy branches (e.g., `if old_format:`, `if legacy:`), and migration-period aliases MUST be removed.
- **FR-013**: TODO, FIXME, and HACK comments referencing completed work MUST be removed.
- **FR-014**: Unused dependencies in project manifests MUST be removed.
- **FR-015**: Orphaned configuration or migration files referencing deleted features MUST be removed.
- **FR-016**: Unused Docker Compose services or environment variables MUST be removed if applicable.
- **FR-017**: No public API contracts (route paths, request/response shapes) MUST be changed — only internal implementation may be modified.
- **FR-018**: Code that is imported or called dynamically (e.g., via string-based plugin loading or migration discovery) MUST NOT be removed without confirming it is truly unused.
- **FR-019**: All meaningful test coverage MUST be preserved — only genuinely stale or dead-code tests may be removed.
- **FR-020**: All changes MUST be pushed to a feature branch and a PR opened (or updated) with a categorized summary of every change made, organized by the five cleanup categories.
- **FR-021**: For each removal, the PR description MUST include a brief explanation of why the code was identified as dead, stale, or duplicated.

### Constraints

- All existing CI checks MUST pass after changes: linting, type-checking, unit tests, and builds for both backend and frontend.
- No public API contracts may be modified — only internal implementation changes are permitted.
- Existing code style conventions MUST be followed (double quotes and 100-char lines for backend; strict mode with path alias for frontend).
- Conventional commit messages MUST be used: `refactor:` for code consolidation, `chore:` for dead code and test removal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The total number of lines of dead code (unused functions, unreachable branches, commented-out logic) is reduced to zero, as confirmed by linting and manual review.
- **SC-002**: All MagicMock-generated artifact files are removed from the backend workspace root, reducing the count from the current number to zero.
- **SC-003**: The test suite execution time does not increase after cleanup (stale test removal may reduce it).
- **SC-004**: All CI checks (linting, type-checking, unit tests, builds) pass with zero failures on the cleanup branch.
- **SC-005**: No public API endpoint paths or request/response shapes are altered, as confirmed by comparing route definitions before and after.
- **SC-006**: Every near-duplicate function pair identified is replaced by a single implementation, reducing total function count in affected modules.
- **SC-007**: All dependencies listed in project manifests are actively used in the codebase, with zero orphaned entries remaining.
- **SC-008**: All remaining TODO/FIXME/HACK comments reference genuinely outstanding work items — none reference completed work.
- **SC-009**: A categorized PR summary is published documenting every change with rationale, organized across all five cleanup categories.
- **SC-010**: A clean install of project dependencies followed by a full test run succeeds without errors or warnings related to the changes.

## Assumptions

- The existing CI pipeline (ruff, pyright, pytest, eslint, tsc, vitest, vite build) is functional and will accurately catch regressions caused by cleanup.
- The MagicMock-generated files in the backend workspace root are test artifacts that are safe to delete (they are not runtime data).
- The existing shared test helpers (`factories.py`, `mocks.py`) are stable and suitable as targets for test refactoring.
- "Unused" is defined as: not imported, not called, not referenced by string-based dynamic loading, and not documented as an intentional public extension point.
- Dependencies marked as dev-only in manifests are still checked against dev tool imports (e.g., test frameworks, linters).
- External documentation and deployment scripts outside this repository are out of scope for this cleanup effort.
- Standard web application performance expectations apply (no specialized performance targets beyond CI passing).
