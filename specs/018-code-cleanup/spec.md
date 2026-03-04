# Feature Specification: Codebase Cleanup — Reduce Technical Debt and Improve Maintainability

**Feature Branch**: `018-code-cleanup`  
**Created**: 2026-03-04  
**Status**: Draft  
**Input**: User description: "Perform a thorough codebase cleanup across the entire repository (backend, frontend, scripts, specs) to improve maintainability and reduce technical debt. Make the actual code changes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove Dead Code and Unused Artifacts (Priority: P1)

As a developer working in the codebase, I want all unreachable code, unused imports, unused variables, unused type definitions, and commented-out logic blocks removed, so that the codebase only contains code that is actively used and I can navigate and understand it more quickly.

**Why this priority**: Dead code is the single largest source of confusion for contributors. Removing it immediately improves readability, reduces cognitive load, and prevents developers from accidentally depending on non-functional code paths. This category is also the safest to tackle first because unused code by definition has no consumers.

**Independent Test**: Can be fully tested by running all existing CI checks (linting, type checking, and test suites for both backend and frontend) after the removals and verifying that every check passes with no regressions. Additionally, a search for known dead-code indicators (unused imports, unreferenced functions, commented-out logic blocks) should return zero results.

**Acceptance Scenarios**:

1. **Given** the codebase contains functions or components that are defined but never imported or called, **When** those definitions are removed, **Then** all CI checks pass and no remaining code references the removed definitions.
2. **Given** the codebase contains commented-out logic blocks (not documentation comments), **When** those blocks are removed, **Then** all CI checks pass and no functional behavior changes.
3. **Given** the codebase contains unused imports, variables, or type definitions, **When** those declarations are removed, **Then** all linters and type checkers pass without new warnings or errors.
4. **Given** the backend contains unused route handlers with no corresponding frontend calls or test coverage, **When** those handlers are removed, **Then** no existing API consumer is affected and all integration tests pass.
5. **Given** the frontend contains unused components, hooks, or utility functions, **When** those modules are removed, **Then** the frontend builds successfully and all existing tests pass.

---

### User Story 2 - Remove Backwards-Compatibility Shims (Priority: P1)

As a developer, I want all compatibility layers, polyfills, and adapter code that exist solely to support deprecated API shapes, old config formats, or migration-period aliases removed, so that the codebase reflects only current contracts and I do not waste time maintaining code paths that no longer serve any consumer.

**Why this priority**: Compatibility shims mask the true behavior of the system and create ambiguity about which code path is canonical. Removing them is a close second to dead code removal because shims are by definition transitional — once the migration is complete, they serve no purpose and introduce maintenance risk.

**Independent Test**: Can be fully tested by running all existing CI checks after shim removal and verifying that every check passes. A targeted search for common shim patterns (`if old_format:`, `if legacy:`, fallback aliases, deprecated parameter handling) should return zero results.

**Acceptance Scenarios**:

1. **Given** the codebase contains conditional branches that handle legacy or deprecated formats (e.g., `if old_format:`, `if legacy:`), **When** the legacy branch is removed and only the current path is retained, **Then** all CI checks pass and no existing consumer relies on the removed path.
2. **Given** the codebase contains adapter functions or wrapper modules that translate between old and new API shapes, **When** those adapters are removed and callers are updated to use the current API directly, **Then** all CI checks pass and public API contracts remain unchanged.
3. **Given** the codebase contains migration-period aliases (functions, config keys, or route aliases), **When** those aliases are removed, **Then** all CI checks pass and no external consumer references the removed alias.

---

### User Story 3 - Consolidate Duplicated Logic (Priority: P2)

As a developer, I want near-duplicate functions, utility helpers, service methods, and copy-pasted patterns consolidated into single implementations with clear ownership, so that bug fixes and improvements only need to be made in one place and the codebase is easier to maintain.

**Why this priority**: Duplicated logic increases the risk that fixes are applied inconsistently and makes the codebase harder to reason about. This is prioritized after dead code and shim removal because consolidation involves refactoring live code paths and requires more careful verification.

**Independent Test**: Can be fully tested by running all existing CI checks after consolidation, verifying that test coverage remains equivalent or improves, and confirming through code review that previously duplicated functions now have a single canonical implementation.

**Acceptance Scenarios**:

1. **Given** the codebase contains near-duplicate utility functions or service methods that perform the same operation with minor variations, **When** they are consolidated into a single implementation, **Then** all call sites use the consolidated version and all CI checks pass.
2. **Given** test files contain copy-pasted setup patterns that could use shared helpers or factories, **When** those patterns are extracted into shared test utilities (using existing helpers in `factories.py` and `mocks.py` where applicable), **Then** each duplicated pattern is replaced with a call to the shared helper and all tests pass.
3. **Given** duplicated model definitions or overlapping type definitions exist, **When** they are consolidated into canonical definitions, **Then** all consumers reference the consolidated type and all type checkers pass.

---

### User Story 4 - Delete Stale and Irrelevant Tests (Priority: P2)

As a developer, I want test files and test cases that test deleted or refactored functionality, mock internals so heavily they provide no real coverage, or exercise code paths that no longer exist removed, so that the test suite is trustworthy and I can rely on test results to validate actual behavior.

**Why this priority**: Stale tests erode confidence in the test suite and slow down CI pipelines without providing value. This shares priority with consolidation because both involve careful analysis of live code, but stale test removal is slightly safer since removing a test cannot break production behavior.

**Independent Test**: Can be fully tested by running the full test suite after removals and verifying that all remaining tests pass, no meaningful coverage is lost (coverage for active code paths is preserved), and any leftover test artifacts (e.g., orphaned mock database files) are cleaned up.

**Acceptance Scenarios**:

1. **Given** the test suite contains tests for code paths that have been deleted or fundamentally refactored, **When** those stale tests are removed, **Then** the test suite passes and coverage for all actively used code paths is preserved.
2. **Given** the test suite contains tests that mock internal implementation details so heavily they provide no real behavioral coverage, **When** those tests are removed, **Then** the test suite passes and no genuinely meaningful assertion is lost.
3. **Given** the workspace contains leftover test artifacts (e.g., orphaned database files, temporary mock files), **When** those artifacts are removed, **Then** the workspace is clean and no test depends on the removed artifact.

---

### User Story 5 - Perform General Hygiene Cleanup (Priority: P3)

As a developer, I want orphaned configuration files, stale TODO/FIXME/HACK comments referencing completed work, unused dependencies, and unused environment variables removed, so that the project configuration is lean and every item in the codebase serves a current purpose.

**Why this priority**: General hygiene items individually have low risk but collectively contribute to clutter and confusion. They are prioritized last because they have the least impact on day-to-day development compared to dead code, shims, duplication, and stale tests.

**Independent Test**: Can be fully tested by running all CI checks after cleanup, verifying that dependency install/build/test cycles complete successfully, and confirming through manual review that no orphaned configs, stale comments, or unused dependencies remain.

**Acceptance Scenarios**:

1. **Given** the codebase contains TODO, FIXME, or HACK comments that reference work that has already been completed, **When** those comments are removed, **Then** all CI checks pass and all remaining TODO/FIXME/HACK comments reference genuinely open work items.
2. **Given** the project's dependency files list packages that are not imported or used anywhere in the codebase, **When** those unused dependencies are removed, **Then** the project builds, installs, and tests successfully with the reduced dependency set.
3. **Given** the project contains orphaned migration files or configuration entries that reference deleted features, **When** those orphans are removed, **Then** all CI checks pass and no remaining configuration references a non-existent feature.

---

### Edge Cases

- What happens when a function appears unused but is loaded dynamically (e.g., via string-based plugin loading or migration discovery)?
  - Code must not be removed unless confirmed truly unused. Dynamic imports, plugin registries, and migration discovery mechanisms must be checked before removing any code that could be dynamically referenced.
- What happens when removing a backwards-compatibility shim changes the behavior of an existing consumer that still uses the deprecated path?
  - Each shim removal must verify that no consumer (including tests) references the deprecated path before removal. If any consumer still relies on the shim, the shim is retained and documented for future removal.
- What happens when consolidating duplicated functions introduces a subtle behavior difference that breaks one of the original call sites?
  - Consolidation must include verification that all call sites produce identical behavior before and after the change. The existing test suite serves as the safety net; all tests must pass after consolidation.
- What happens when a test is removed that appeared stale but actually provided coverage for an edge case in still-active code?
  - Test removal must be confirmed by verifying that the code path under test still exists and is covered by other tests, or that the code path itself has been removed. Coverage of active code paths must not decrease.
- What happens when removing an unused dependency causes a transitive dependency to also be removed, breaking another package that implicitly relied on it?
  - After removing any dependency, the full install and build cycle must succeed. If a transitive dependency issue arises, the dependency is re-added and the situation is documented.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All backwards-compatibility shims, including conditional branches for legacy/deprecated formats, adapter functions for old API shapes, and migration-period aliases, MUST be identified and removed. Only the current, canonical code path MUST remain.
- **FR-002**: All dead code MUST be removed, including: functions, methods, and components that are defined but never imported or called; commented-out logic blocks (excluding documentation comments); unused imports, variables, and type definitions; unused route handlers with no corresponding consumer or test coverage; and unused frontend components, hooks, and utility functions.
- **FR-003**: Near-duplicate functions, utility helpers, and service methods that perform the same operation with minor variations MUST be consolidated into a single canonical implementation. All call sites MUST be updated to use the consolidated version.
- **FR-004**: Copy-pasted patterns in test files MUST be extracted into shared test helpers or factories, leveraging existing shared utilities where applicable.
- **FR-005**: Duplicated model definitions and overlapping type definitions MUST be consolidated into single canonical definitions.
- **FR-006**: Test files and test cases that test deleted or fundamentally refactored functionality MUST be removed.
- **FR-007**: Tests that mock internal implementation details so heavily they provide no real behavioral coverage MUST be removed.
- **FR-008**: Leftover test artifacts (e.g., orphaned mock database files in the workspace root) MUST be removed.
- **FR-009**: Orphaned migration files and configuration entries that reference deleted features MUST be removed.
- **FR-010**: Stale TODO, FIXME, and HACK comments that reference completed work MUST be removed. Comments referencing genuinely open work items MUST be preserved.
- **FR-011**: Unused dependencies MUST be removed from the project's dependency manifests.
- **FR-012**: All existing CI checks MUST continue to pass after every change: linting, type checking, and test suites for both backend and frontend.
- **FR-013**: No public API contracts (route paths, request shapes, response shapes) MUST be changed — only internal implementation may be modified.
- **FR-014**: Code that is imported or called dynamically (e.g., via string-based plugin loading, migration discovery, or runtime registration) MUST NOT be removed without confirming it is truly unused.
- **FR-015**: All meaningful test coverage MUST be preserved — only tests that are genuinely stale or test deleted code may be removed.
- **FR-016**: Existing code style conventions MUST be followed for all changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing CI checks (linting, type checking, test suites) pass with zero new failures after the cleanup is complete.
- **SC-002**: The total number of lines of dead code (unreachable functions, unused imports, commented-out logic) is reduced to zero as confirmed by linter output and manual review.
- **SC-003**: Zero backwards-compatibility shims remain in the codebase, as confirmed by searching for common shim patterns (legacy conditionals, deprecated adapters, migration aliases).
- **SC-004**: Every instance of duplicated logic identified during the cleanup is consolidated into a single implementation, reducing the total count of near-duplicate function groups to zero.
- **SC-005**: All stale test cases (tests for deleted code, over-mocked tests with no behavioral coverage) are removed, and the remaining test suite maintains equivalent or improved coverage of actively used code paths.
- **SC-006**: Zero stale TODO/FIXME/HACK comments referencing completed work remain in the codebase.
- **SC-007**: Zero unused dependencies remain in the project's dependency manifests, as confirmed by a successful build and test cycle with the reduced dependency set.
- **SC-008**: The PR description contains a categorized summary of every change, organized by the five cleanup categories, with a brief explanation for each removal.

## Assumptions

- The existing CI pipeline (linting, type checking, and test suites for both backend and frontend) provides sufficient coverage to detect regressions introduced by cleanup changes.
- The repository has no external consumers that depend on internal implementation details (only public API contracts are considered stable).
- Backwards-compatibility shims that still have active consumers are not present; if discovered during cleanup, they will be retained and documented rather than removed.
- Dynamic code loading (plugin registries, migration discovery) follows discoverable patterns that can be traced to confirm whether a given function is truly unused.
- The existing shared test utilities (`factories.py`, `mocks.py`) are sufficient as consolidation targets for duplicated test patterns, and new shared helpers may be created if needed.
- Dependency removal will not affect production deployments since only development and unused runtime dependencies are targeted.
- The cleanup scope is limited to the current repository — no changes to external services, APIs, or third-party integrations.
