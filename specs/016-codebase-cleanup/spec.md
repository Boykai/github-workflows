# Feature Specification: Repository-Wide Codebase Cleanup (Backend + Frontend)

**Feature Branch**: `016-codebase-cleanup`  
**Created**: 2026-03-02  
**Status**: Draft  
**Input**: User description: "Refactor: Repository-Wide Codebase Cleanup (Backend + Frontend)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove Dead Code and Unused Artifacts (Priority: P1)

As a developer working on the codebase, I want all dead code paths, unused imports, unreferenced functions, and orphaned components removed so that the codebase is easier to navigate, understand, and maintain.

**Why this priority**: Dead code is the single largest source of confusion for developers. Removing it reduces cognitive load, shrinks build artifacts, and eliminates misleading search results when navigating the project. This is the highest-impact cleanup activity.

**Independent Test**: Can be fully tested by running all existing CI checks (linting, type checking, unit tests, and build) after removal and confirming they all pass with zero regressions.

**Acceptance Scenarios**:

1. **Given** the backend contains functions, Pydantic models, or imports that are defined but never referenced elsewhere, **When** a developer removes them, **Then** all backend CI checks (`ruff`, `pyright`, `pytest`) continue to pass.
2. **Given** the frontend contains React components, hooks, utility functions, or type definitions that are defined but never imported, **When** a developer removes them, **Then** all frontend CI checks (`eslint`, `tsc`, `vitest`, `vite build`) continue to pass.
3. **Given** commented-out logic blocks exist in the codebase (excluding documentation comments), **When** they are removed, **Then** no functional behavior changes and all CI checks pass.
4. **Given** unused API route handlers exist with no frontend callers and no test coverage, **When** they are removed, **Then** no public API contract is altered and all CI checks pass.

---

### User Story 2 - Remove Backwards-Compatibility Shims and Legacy Branches (Priority: P1)

As a developer, I want compatibility layers, polyfills, adapter code, and dead conditional branches supporting deprecated patterns removed so the codebase reflects only the current architecture.

**Why this priority**: Shims and legacy conditional branches add complexity, obscure the true logic, and can mask bugs. Removing them simplifies the code and reduces maintenance burden. This is equally critical as dead code removal.

**Independent Test**: Can be tested by running the full CI suite after removal and verifying all checks pass. Additionally, verify that no public API route paths or request/response shapes have changed.

**Acceptance Scenarios**:

1. **Given** the codebase contains compatibility layers or adapter code for deprecated API shapes, **When** they are removed, **Then** all CI checks pass and no public API contracts are altered.
2. **Given** dead conditional branches exist (e.g., `if old_format:` or `if legacy:` patterns), **When** they are deleted, **Then** the remaining code paths function correctly and all CI checks pass.

---

### User Story 3 - Consolidate Duplicated Logic (Priority: P2)

As a developer, I want near-duplicate functions, helpers, service methods, and type definitions consolidated into single implementations so that future changes only need to be made in one place.

**Why this priority**: Duplicated logic increases the risk of inconsistent behavior when one copy is updated but others are not. Consolidation reduces maintenance effort and bug surface area. This is prioritized after dead code removal since it involves restructuring rather than simple deletion.

**Independent Test**: Can be tested by running all CI checks after consolidation. Verify that every caller of the previously duplicated functions now uses the consolidated version and all tests pass.

**Acceptance Scenarios**:

1. **Given** near-duplicate functions or helpers exist in the backend, **When** they are merged into a single implementation, **Then** all callers use the consolidated version and all backend CI checks pass.
2. **Given** copy-pasted test patterns exist across test files, **When** they are refactored into shared helpers or factories, **Then** all tests continue to pass with the same coverage.
3. **Given** overlapping Pydantic model definitions or TypeScript type definitions exist, **When** they are consolidated, **Then** all dependent code uses the unified definitions and all CI checks pass.

---

### User Story 4 - Delete Stale and Irrelevant Tests (Priority: P2)

As a developer, I want test files and test cases that cover deleted functionality, over-mock internals, or test nonexistent code paths removed so the test suite accurately reflects current system behavior.

**Why this priority**: Stale tests give false confidence, slow down the test suite, and confuse developers about what the system actually does. Cleaning them up improves test suite reliability and execution speed.

**Independent Test**: Can be tested by running the full test suite after removal and confirming all remaining tests pass. Verify that no test covering active functionality is removed.

**Acceptance Scenarios**:

1. **Given** test files exist that cover deleted or refactored functionality, **When** they are removed, **Then** the remaining test suite passes and no active functionality loses coverage.
2. **Given** tests exist that over-mock internals and no longer validate real behavior, **When** they are removed, **Then** the test suite remains green and accurately reflects system behavior.
3. **Given** leftover test artifacts exist (e.g., stale mock database files in workspace root), **When** they are cleaned up, **Then** the workspace is free of orphaned artifacts.

---

### User Story 5 - General Hygiene and Dependency Cleanup (Priority: P3)

As a developer, I want orphaned configs, stale TODO/FIXME/HACK comments tied to completed work, unused dependencies, and unused infrastructure definitions cleaned up so that the project configuration accurately reflects what is actually in use.

**Why this priority**: While lower impact than code-level cleanup, stale configuration and dependencies add confusion, increase install times, and can introduce security exposure from unused packages. This is the final polishing step.

**Independent Test**: Can be tested by verifying all CI checks pass, confirming no build or runtime errors occur, and checking that removed dependencies are truly unused by the codebase.

**Acceptance Scenarios**:

1. **Given** stale TODO, FIXME, or HACK comments reference completed work, **When** they are removed, **Then** remaining comments are relevant and actionable.
2. **Given** unused dependencies exist in project manifests, **When** they are removed, **Then** the project builds and all tests pass without them.
3. **Given** orphaned migration files or configs reference deleted features, **When** they are removed, **Then** the system starts and operates correctly.
4. **Given** unused Docker Compose services or environment variables exist, **When** they are removed, **Then** the containerized environment functions correctly.

---

### Edge Cases

- What happens when code appears unused but is loaded dynamically via string-based plugin loading or migration discovery? Such code MUST NOT be removed without first confirming it is truly unused.
- What happens when a function is only referenced in a single test? If the function is dead code, both the function and its test should be removed together.
- What happens when removing a backwards-compatibility shim changes the behavior of an internal (non-public) interface? Callers of the internal interface must be updated to use the current pattern.
- What happens when consolidated logic has slight behavioral differences between the duplicates? The consolidated version must preserve the correct behavior for all callers; differences must be reconciled before merging.
- What happens when a dependency is listed as unused but is required at runtime (e.g., as a transitive dependency or plugin)? Such dependencies MUST NOT be removed without runtime verification.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All backwards-compatibility shims, polyfills, and adapter code supporting deprecated API shapes or migration-period aliases MUST be removed
- **FR-002**: All dead conditional branches (e.g., `if old_format:`, `if legacy:` patterns) MUST be deleted
- **FR-003**: All functions, methods, and components that are defined but never imported or called MUST be removed
- **FR-004**: All commented-out logic blocks (excluding documentation comments) MUST be removed
- **FR-005**: All unused imports, variables, type definitions, and model definitions MUST be removed
- **FR-006**: All unused API route handlers with no frontend callers or test coverage MUST be removed
- **FR-007**: All unused hooks and frontend utility functions MUST be removed
- **FR-008**: Near-duplicate functions, helpers, and service methods MUST be consolidated into single implementations
- **FR-009**: Copy-pasted test patterns MUST be refactored using shared helpers or factories
- **FR-010**: Duplicated API client logic MUST be consolidated
- **FR-011**: Overlapping model definitions and type definitions MUST be consolidated
- **FR-012**: Test files and cases covering deleted or refactored functionality MUST be removed
- **FR-013**: Tests that over-mock internals and no longer validate real behavior MUST be removed
- **FR-014**: Leftover test artifacts (e.g., stale mock database files) MUST be cleaned up
- **FR-015**: Orphaned migration files or configs referencing deleted features MUST be removed
- **FR-016**: Stale TODO, FIXME, and HACK comments tied to completed work MUST be removed
- **FR-017**: Unused dependencies MUST be removed from project manifests
- **FR-018**: Unused infrastructure service definitions or environment variables MUST be removed
- **FR-019**: No public API contracts (route paths, request/response shapes) may be altered
- **FR-020**: Code loaded via string-based plugin loading or migration discovery MUST NOT be removed without first confirming it is truly unused
- **FR-021**: All changes MUST be committed using conventional commit format (`refactor:` for consolidation, `chore:` for dead code and test removal)
- **FR-022**: A PR MUST be opened with a categorized summary covering every change and explaining why each piece of code was identified as dead, stale, or duplicated

## Assumptions

- The current CI pipeline (linting, type checking, testing, building) is the authoritative source of truth for correctness. If all CI checks pass after a change, the change is considered safe.
- "Public API contracts" refers specifically to HTTP route paths and their request/response shapes — internal function signatures, class interfaces, and module structures may be refactored.
- Documentation comments (docstrings, JSDoc, inline explanations) are not considered "commented-out logic" and should be preserved.
- Dynamic code loading patterns (string-based plugin discovery, migration file discovery) exist in the codebase and require special caution before removal.
- The project uses conventional commits, and the appropriate prefix (`refactor:` or `chore:`) is determined by whether the change restructures code or removes dead code.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five cleanup categories (shims removal, dead code elimination, logic consolidation, stale test deletion, general hygiene) have at least one committed change addressing them
- **SC-002**: All CI checks pass after cleanup: backend linting, backend type checking, backend tests, frontend linting, frontend type checking, frontend tests, and frontend build
- **SC-003**: Zero public API contract changes — all existing route paths and request/response shapes remain identical before and after cleanup
- **SC-004**: The PR description contains a categorized summary covering every change, organized by the five cleanup categories
- **SC-005**: Net reduction in lines of code across the repository (excluding any new shared helpers or factories introduced for consolidation)
- **SC-006**: No dynamically-loaded code (plugin loaders, migration discovery) is removed without explicit confirmation that it is unused
- **SC-007**: All remaining tests in the suite pass, confirming no active functionality lost coverage
