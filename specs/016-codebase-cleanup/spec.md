# Feature Specification: Perform Repository-Wide Codebase Cleanup Across Backend & Frontend

**Feature Branch**: `016-codebase-cleanup`  
**Created**: 2026-03-02  
**Status**: Draft  
**Input**: User description: "Perform Repository-Wide Codebase Cleanup Across Backend & Frontend"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove Dead Code and Unused Artifacts (Priority: P1)

A developer working in the codebase encounters functions, components, imports, variables, type definitions, and models that are defined but never used anywhere. Commented-out logic blocks clutter files and obscure the actual behavior. The developer removes all dead code paths — unused functions, methods, React components, imports, variables, type definitions, Pydantic models, route handlers with no callers or test coverage, unused React hooks, and frontend utility functions. Commented-out logic blocks (excluding documentation comments) are also removed. After the cleanup, every remaining symbol in the codebase is actively referenced.

**Why this priority**: Dead code is the highest-impact cleanup target. It directly harms readability, increases cognitive load for every contributor, and can mask real bugs. Removing it delivers immediate clarity and makes subsequent cleanup categories easier to execute.

**Independent Test**: Can be fully tested by running all existing linters and test suites after removal. Every deleted symbol must have zero references in the codebase (verified via static analysis). All CI checks must pass with no regressions.

**Acceptance Scenarios**:

1. **Given** a function or method defined in the backend that is never imported or called, **When** the cleanup is performed, **Then** the function or method is removed and all CI checks pass.
2. **Given** a React component defined in the frontend that is never imported or rendered, **When** the cleanup is performed, **Then** the component file or export is removed and all CI checks pass.
3. **Given** a commented-out logic block that is not a documentation comment, **When** the cleanup is performed, **Then** the commented-out block is removed.
4. **Given** unused imports, variables, or type definitions in any file, **When** the cleanup is performed, **Then** they are removed and all CI checks pass.
5. **Given** an API route handler with no frontend callers and no test coverage, **When** the cleanup is performed, **Then** it is removed and no public API contracts (route paths, request/response shapes) used by the frontend are altered.
6. **Given** code that is loaded via string-based plugin loading or migration discovery, **When** the developer evaluates whether to remove it, **Then** the code is retained unless confirmed truly unused through runtime or reference analysis.

---

### User Story 2 - Remove Backwards-Compatibility Shims and Legacy Branches (Priority: P1)

A developer discovers compatibility layers, polyfills, and adapter code that exist solely to support deprecated API shapes or migration-period aliases that are no longer needed. Dead conditional branches such as `if old_format:` or `if legacy:` patterns are found in the codebase. The developer removes all backwards-compatibility shims and dead conditional branches. After cleanup, the codebase contains only current-version code paths.

**Why this priority**: Backwards-compatibility shims add complexity and confusion. They often guard code paths that are no longer exercised, creating false impressions about what the system actually does. Removing them is essential to accurately represent the system's behavior.

**Independent Test**: Can be fully tested by removing the shims and running all CI checks. If any test or runtime path depended on the removed shim, it would surface as a test failure or linter error.

**Acceptance Scenarios**:

1. **Given** a compatibility layer or polyfill supporting a deprecated API shape, **When** the cleanup is performed, **Then** the compatibility code is removed and all CI checks pass.
2. **Given** a dead conditional branch guarding a legacy code path (e.g., `if old_format:`, `if legacy:`), **When** the cleanup is performed, **Then** the branch and its contents are removed, retaining only the active code path.
3. **Given** migration-period aliases that map old names to current names, **When** the cleanup is performed, **Then** the aliases are removed and all references use the current names.

---

### User Story 3 - Consolidate Duplicated Logic (Priority: P2)

A developer notices near-duplicate functions, helpers, service methods, API client logic, Pydantic model definitions, and TypeScript types scattered across the codebase. Copy-pasted test patterns exist without shared helpers or factories. The developer merges duplicated implementations into single canonical versions and refactors tests to use shared helpers and factories. After cleanup, each piece of logic exists in exactly one place.

**Why this priority**: Duplication is the leading source of inconsistency bugs — when behavior is updated in one copy but not another. Consolidation reduces the maintenance surface and ensures consistent behavior. This is prioritized after dead code removal because removing dead code first reduces the volume of duplicates to analyze.

**Independent Test**: Can be fully tested by running all CI checks after consolidation. Each merge must preserve existing behavior — no test should change its expected outcome. New shared helpers/factories must be exercised by the refactored tests.

**Acceptance Scenarios**:

1. **Given** two or more near-duplicate functions or helpers performing the same operation, **When** the cleanup is performed, **Then** they are merged into a single implementation and all callers are updated to use it.
2. **Given** copy-pasted test patterns that differ only in setup data, **When** the cleanup is performed, **Then** the patterns are refactored to use shared test helpers or factories.
3. **Given** duplicated API client logic across frontend services, **When** the cleanup is performed, **Then** the logic is consolidated into a shared service or utility.
4. **Given** overlapping Pydantic model definitions or TypeScript type declarations, **When** the cleanup is performed, **Then** they are consolidated into single canonical definitions.

---

### User Story 4 - Delete Stale and Irrelevant Tests (Priority: P2)

A developer finds test files and test cases that cover deleted or refactored functionality, tests that over-mock internals to the point they no longer validate real behavior, and tests for code paths that no longer exist. Leftover test artifacts (such as mock database files in the workspace root) are also present. The developer removes all stale tests and artifacts. After cleanup, every remaining test validates current, real behavior.

**Why this priority**: Stale tests provide false confidence and waste CI time. Over-mocked tests can mask regressions by passing even when the underlying code is broken. Cleaning them up improves test suite reliability and reduces CI execution time.

**Independent Test**: Can be fully tested by removing the identified tests and artifacts, then running the full test suite. All remaining tests must pass. Removed tests must be confirmed to reference code paths or functionality that no longer exists.

**Acceptance Scenarios**:

1. **Given** a test file covering functionality that has been deleted, **When** the cleanup is performed, **Then** the test file is removed.
2. **Given** a test case that references a function or code path that no longer exists, **When** the cleanup is performed, **Then** the test case is removed.
3. **Given** a test that over-mocks internals and no longer validates real behavior, **When** the cleanup is performed, **Then** the test is removed or refactored to test real behavior.
4. **Given** leftover test artifacts in the workspace (e.g., mock database files in the backend root), **When** the cleanup is performed, **Then** the artifacts are removed.

---

### User Story 5 - General Hygiene and Dependency Cleanup (Priority: P3)

A developer reviews the repository for general hygiene issues: orphaned migration files or configuration referencing deleted features, stale `TODO` / `FIXME` / `HACK` comments tied to completed work, unused dependencies in package manifests, and unused Docker Compose services or environment variables. The developer addresses each hygiene issue. After cleanup, the repository configuration accurately reflects the current state of the project.

**Why this priority**: Hygiene issues accumulate gradually and individually have low impact, but collectively they degrade developer experience and onboarding speed. This is the lowest priority because each item is minor, but addressing them completes the cleanup and prevents future confusion.

**Independent Test**: Can be fully tested by running all CI checks and verifying that no removed configuration causes build, test, or runtime failures. Stale comments can be verified by confirming the referenced work is complete.

**Acceptance Scenarios**:

1. **Given** an orphaned migration file or configuration referencing a deleted feature, **When** the cleanup is performed, **Then** the orphaned file or configuration entry is removed.
2. **Given** a `TODO`, `FIXME`, or `HACK` comment referencing work that has been completed, **When** the cleanup is performed, **Then** the comment is removed.
3. **Given** an unused dependency listed in a package manifest, **When** the cleanup is performed, **Then** the dependency is removed from the manifest and the project builds successfully without it.
4. **Given** an unused Docker Compose service or environment variable, **When** the cleanup is performed, **Then** it is removed and the remaining services function correctly.

---

### Edge Cases

- What happens when code appears unused but is loaded dynamically via string-based plugin loading or migration discovery? The code must be confirmed truly unused through runtime or reference analysis before removal. When in doubt, retain the code and document the decision.
- What happens when a backwards-compatibility shim is still exercised by an external consumer not visible in the repository? Scope is limited to internal implementation only. If no in-repo references exist and no external consumer documentation is found, the shim is a removal candidate.
- What happens when consolidating duplicated logic introduces a subtle behavioral difference? All existing tests must continue to pass after consolidation. If a behavioral difference is detected (test failure), the consolidation must be revised to preserve existing behavior.
- What happens when removing a test reveals that no other test covers the same functionality? The developer must verify whether the functionality still exists. If it does, a replacement test should be considered out-of-scope for this cleanup but documented for follow-up.
- What happens when a `TODO` / `FIXME` comment references work that is partially complete? The comment should be retained and updated to reflect the current state, rather than removed.
- What happens when removing an unused dependency causes a transitive dependency to also be removed, breaking another package? Dependency removal must be validated by running the full build and test suite. If a transitive dependency issue is detected, the removal is reverted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All backwards-compatibility shims, polyfills, and adapter code supporting deprecated API shapes or migration-period aliases MUST be removed.
- **FR-002**: All dead conditional branches guarding legacy code paths (e.g., `if old_format:`, `if legacy:` patterns) MUST be removed.
- **FR-003**: All functions, methods, and React components that are defined but never imported or called MUST be removed.
- **FR-004**: All commented-out logic blocks (excluding documentation comments) MUST be removed.
- **FR-005**: All unused imports, variables, type definitions, and Pydantic models MUST be removed.
- **FR-006**: All unused API route handlers with no frontend callers and no test coverage MUST be removed, provided they are not part of a public API contract.
- **FR-007**: All unused React hooks and frontend utility functions MUST be removed.
- **FR-008**: Near-duplicate functions, helpers, and service methods MUST be consolidated into single implementations.
- **FR-009**: Copy-pasted test patterns MUST be refactored to use shared helpers or factories.
- **FR-010**: Duplicated API client logic in frontend services MUST be consolidated.
- **FR-011**: Overlapping Pydantic model definitions and TypeScript type declarations MUST be consolidated into canonical definitions.
- **FR-012**: Test files and cases covering deleted or refactored functionality MUST be removed.
- **FR-013**: Tests that over-mock internals and no longer validate real behavior MUST be removed or refactored.
- **FR-014**: Leftover test artifacts (e.g., mock database files in the workspace root) MUST be removed.
- **FR-015**: Orphaned migration files or configurations referencing deleted features MUST be removed.
- **FR-016**: Stale `TODO` / `FIXME` / `HACK` comments tied to completed work MUST be removed.
- **FR-017**: Unused dependencies MUST be removed from package manifests.
- **FR-018**: Unused Docker Compose services or environment variables MUST be removed.
- **FR-019**: No public API contracts (route paths, request/response shapes) may be altered by any cleanup change.
- **FR-020**: Code loaded via string-based plugin loading or migration discovery MUST NOT be removed without first confirming it is truly unused.
- **FR-021**: All cleanup changes MUST pass the existing CI checks: backend linting, backend type checking, backend tests, frontend linting, frontend type checking, frontend tests, and frontend build.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five cleanup categories (backwards-compatibility shims, dead code, duplicated logic, stale tests, general hygiene) have at least one committed change addressing them.
- **SC-002**: All CI checks pass after the complete cleanup: backend linting, backend type checking, backend tests, frontend linting, frontend type checking, frontend tests, and frontend build — with zero new failures introduced.
- **SC-003**: Zero public API contracts (route paths, request/response shapes) are altered, verified by diffing route definitions and response models before and after cleanup.
- **SC-004**: The total number of unused imports, variables, and type definitions detected by linters is reduced to zero (or matches the pre-existing baseline for intentional suppressions).
- **SC-005**: Every removal is traceable — the PR description contains a categorized summary explaining why each piece of code was identified as dead, stale, or duplicated.
- **SC-006**: The test suite execution time does not increase as a result of the cleanup (and is expected to decrease due to stale test removal).
- **SC-007**: The codebase line count decreases or remains stable — no net increase in lines of code results from the cleanup, confirming that consolidation and removal outweigh any added shared helpers.
- **SC-008**: No dynamically loaded code (plugin loading, migration discovery) is removed without documented confirmation that it is truly unused.

## Assumptions

- The cleanup scope is limited to the existing repository codebase. No external consumers of the API beyond the in-repo frontend are considered.
- "Public API contracts" refers to route paths and request/response shapes consumed by the frontend. Internal service interfaces, helper function signatures, and test utilities may be changed freely.
- The current CI pipeline (backend: linting, type checking, tests; frontend: linting, type checking, tests, build) is the authoritative validation gate for all changes.
- Backwards-compatibility shims are identified by patterns such as conditional branches guarding old formats, adapter functions mapping deprecated shapes, and aliased exports for migration periods.
- "Unused" is determined by static analysis (no in-repo references) combined with caution for dynamic loading patterns. Runtime-only references that are not discoverable via static analysis require manual confirmation.
- Consolidation of duplicated logic preserves existing behavior exactly — no behavioral changes are introduced during refactoring.
- Stale `TODO` / `FIXME` / `HACK` comments are identified by cross-referencing with completed work items, merged PRs, or resolved issues.
- Unused dependencies are identified by cross-referencing package manifest entries with actual import statements across the codebase.
- Conventional commit prefixes (`refactor:` for consolidation, `chore:` for dead code and test removal) are used for all cleanup commits.
