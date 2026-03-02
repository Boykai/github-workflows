# Feature Specification: Repository-Wide Codebase Cleanup Across Backend & Frontend

**Feature Branch**: `016-codebase-cleanup`  
**Created**: 2026-03-02  
**Status**: Draft  
**Input**: User description: "Perform Repository-Wide Codebase Cleanup Across Backend & Frontend"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove Dead Code and Unused Artifacts (Priority: P1)

A developer opens the codebase and finds that unused functions, components, imports, variables, type definitions, and models have been removed. Commented-out logic blocks (excluding documentation comments) are gone. The codebase contains only code that is actively used or referenced. The developer can navigate the codebase with confidence that every definition they encounter is meaningful and in use.

**Why this priority**: Dead code is the highest-impact cleanup target. It increases cognitive load, confuses search results, and gives a false sense of coverage. Removing it immediately improves readability, maintainability, and developer productivity across both backend and frontend.

**Independent Test**: Can be fully tested by running static analysis tools to confirm zero unused exports, imports, variables, and definitions exist, and by verifying that all CI checks pass after removal.

**Acceptance Scenarios**:

1. **Given** the backend contains functions or methods that are defined but never imported or called, **When** the cleanup is applied, **Then** those functions and methods are removed and all CI checks pass.
2. **Given** the frontend contains React components, hooks, or utility functions that are never imported or rendered, **When** the cleanup is applied, **Then** those components, hooks, and utilities are removed and all CI checks pass.
3. **Given** the codebase contains commented-out logic blocks (not documentation comments), **When** the cleanup is applied, **Then** those commented-out blocks are removed.
4. **Given** the backend contains unused imports, variables, or Pydantic models, **When** the cleanup is applied, **Then** they are removed and all CI checks pass.
5. **Given** the frontend contains unused imports, variables, or TypeScript type definitions, **When** the cleanup is applied, **Then** they are removed and all CI checks pass.
6. **Given** the backend contains API route handlers with no frontend callers and no test coverage, **When** the cleanup is applied, **Then** those route handlers are removed and no public API contracts (route paths, request/response shapes) used by the frontend are altered.

---

### User Story 2 - Remove Backwards-Compatibility Shims and Legacy Code (Priority: P1)

A developer reviewing the codebase finds that compatibility layers, polyfills, adapter code supporting deprecated API shapes, and migration-period aliases have been removed. Dead conditional branches following patterns such as `if old_format:` or `if legacy:` are gone. The codebase reflects only the current supported behavior without vestiges of previous migration periods.

**Why this priority**: Backwards-compatibility shims add branching complexity and obscure the actual execution path. Removing them reduces bugs caused by ambiguous control flow and simplifies future refactoring. This is a prerequisite for safe consolidation work.

**Independent Test**: Can be fully tested by searching for legacy patterns (`old_format`, `legacy`, `deprecated`, compatibility shim markers) and confirming none remain, then verifying all CI checks pass.

**Acceptance Scenarios**:

1. **Given** the codebase contains compatibility layers or adapter code for deprecated API shapes, **When** the cleanup is applied, **Then** those layers are removed and all CI checks pass.
2. **Given** the codebase contains dead conditional branches with legacy patterns (e.g., `if old_format:`, `if legacy:`), **When** the cleanup is applied, **Then** those branches are removed and the remaining code path reflects current behavior.
3. **Given** the codebase contains migration-period aliases or polyfills, **When** the cleanup is applied, **Then** those aliases and polyfills are removed.

---

### User Story 3 - Consolidate Duplicated Logic (Priority: P2)

A developer working on a feature finds that near-duplicate functions, helpers, and service methods have been merged into single implementations. Copy-pasted test patterns have been replaced with shared helpers and factories. Duplicated API client logic and overlapping model definitions have been consolidated. The developer can reuse a single well-defined function instead of choosing between multiple near-identical copies.

**Why this priority**: Duplicated logic is a maintenance burden that leads to inconsistent bug fixes and divergent behavior. Consolidation reduces the surface area for bugs and ensures a single source of truth for shared behavior. This is prioritized after dead code removal because consolidation is safer when the codebase has already been trimmed.

**Independent Test**: Can be fully tested by identifying all consolidated functions and verifying that their callers produce identical results before and after consolidation, with all CI checks passing.

**Acceptance Scenarios**:

1. **Given** the backend contains near-duplicate functions or service methods, **When** the cleanup is applied, **Then** they are merged into single implementations and all callers are updated.
2. **Given** the backend test suite contains copy-pasted test patterns, **When** the cleanup is applied, **Then** shared helpers or factories are used to eliminate the duplication.
3. **Given** the frontend contains duplicated API client logic in services, **When** the cleanup is applied, **Then** the logic is consolidated into shared service functions.
4. **Given** the codebase contains overlapping Pydantic model definitions or TypeScript types, **When** the cleanup is applied, **Then** they are consolidated into single canonical definitions.

---

### User Story 4 - Delete Stale and Irrelevant Tests (Priority: P2)

A developer reviewing the test suite finds that test files and cases covering deleted or refactored functionality have been removed. Tests that over-mock internals and no longer validate real behavior are gone. Tests for code paths that no longer exist have been cleaned up. Leftover test artifacts (e.g., stray database files in the workspace root) are removed. The remaining test suite accurately reflects the current codebase and provides meaningful coverage.

**Why this priority**: Stale tests create a false sense of security and waste CI execution time. They can also block refactoring by failing on code that no longer exists. Cleaning them up ensures the test suite is a reliable quality gate.

**Independent Test**: Can be fully tested by running the full test suite and confirming all remaining tests pass, and by verifying that no test references deleted functions, components, or code paths.

**Acceptance Scenarios**:

1. **Given** the test suite contains tests covering deleted functionality, **When** the cleanup is applied, **Then** those tests are removed and the remaining test suite passes.
2. **Given** the test suite contains tests that over-mock internals and no longer validate real behavior, **When** the cleanup is applied, **Then** those tests are removed or rewritten to test actual behavior.
3. **Given** the workspace root contains leftover test artifacts (e.g., MagicMock database files), **When** the cleanup is applied, **Then** those artifacts are removed.
4. **Given** tests exist for code paths that were removed in earlier cleanup steps, **When** the cleanup is applied, **Then** those tests are removed.

---

### User Story 5 - General Hygiene and Dependency Cleanup (Priority: P3)

A developer reviewing the project configuration finds that orphaned migration files or configs referencing deleted features have been removed. Stale `TODO`, `FIXME`, and `HACK` comments tied to completed work are cleaned up. Unused dependencies have been removed from dependency manifests. Unused Docker Compose services or environment variables are gone. The project configuration accurately reflects the current state of the application.

**Why this priority**: Configuration and dependency hygiene is lower urgency than code cleanup but important for long-term maintainability. Unused dependencies increase install times and security surface area. Stale comments mislead developers. This is addressed last because it has the lowest risk of breaking functionality.

**Independent Test**: Can be fully tested by auditing dependency manifests for unused packages, searching for stale TODO/FIXME/HACK comments, and verifying all CI checks and builds pass after removal.

**Acceptance Scenarios**:

1. **Given** the project contains orphaned migration files or configs referencing deleted features, **When** the cleanup is applied, **Then** those files and configs are removed.
2. **Given** the codebase contains stale `TODO`, `FIXME`, or `HACK` comments tied to completed work, **When** the cleanup is applied, **Then** those comments are removed.
3. **Given** dependency manifests contain unused packages, **When** the cleanup is applied, **Then** those packages are removed and the application builds and runs correctly.
4. **Given** Docker Compose configuration contains unused services or environment variables, **When** the cleanup is applied, **Then** those entries are removed and the development environment functions correctly.

---

### Edge Cases

- What happens when code appears unused but is loaded dynamically via string-based plugin loading or migration discovery? Such code MUST NOT be removed without first confirming it is truly unused. Dynamic loading patterns must be audited before any removal.
- What happens when a function is unused in production code but is used in test code? If the function is only used in tests and those tests are themselves stale, both should be removed together. If the tests are valid, the function should be preserved.
- What happens when a dependency appears unused in code but is required as a transitive peer dependency or build tool? Dependency removal must be validated by running full builds and test suites, not just by searching for import statements.
- What happens when a `TODO` or `FIXME` comment references work that is only partially completed? Such comments should be preserved — only comments tied to fully completed work should be removed.
- What happens when consolidating duplicated logic causes a behavioral difference in edge cases? All consolidations must be verified by existing tests. If tests reveal behavioral differences, the consolidation must account for all existing callers' expectations.
- What happens when removing a backwards-compatibility shim changes a public API contract? Public API contracts (route paths, request/response shapes) MUST NOT be altered. Any shim removal that would change a public contract is out of scope.
- What happens when a migration file appears orphaned but is required for database schema history? Migration files that are part of the schema migration chain must not be removed, even if the features they supported have been deleted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All defined-but-never-called functions, methods, and React components MUST be removed from both backend and frontend codebases.
- **FR-002**: All commented-out logic blocks (excluding documentation comments) MUST be removed.
- **FR-003**: All unused imports, variables, type definitions, and Pydantic models MUST be removed.
- **FR-004**: All unused React hooks and frontend utility functions MUST be removed.
- **FR-005**: Backwards-compatibility layers, polyfills, and adapter code supporting deprecated API shapes MUST be removed.
- **FR-006**: Dead conditional branches following legacy patterns (e.g., `if old_format:`, `if legacy:`) MUST be removed.
- **FR-007**: Near-duplicate functions, helpers, and service methods MUST be consolidated into single implementations.
- **FR-008**: Copy-pasted test patterns MUST be refactored to use shared helpers or test factories.
- **FR-009**: Duplicated API client logic in frontend services MUST be consolidated.
- **FR-010**: Overlapping Pydantic model definitions and TypeScript types MUST be consolidated into canonical definitions.
- **FR-011**: Test files and cases covering deleted or refactored functionality MUST be removed.
- **FR-012**: Tests that over-mock internals and no longer validate real behavior MUST be removed or rewritten.
- **FR-013**: Leftover test artifacts (e.g., stray database files in workspace root) MUST be removed.
- **FR-014**: Orphaned migration files or configs referencing deleted features MUST be removed, unless they are part of the active migration chain.
- **FR-015**: Stale `TODO`, `FIXME`, and `HACK` comments tied to completed work MUST be removed.
- **FR-016**: Unused dependencies MUST be removed from dependency manifests.
- **FR-017**: Unused Docker Compose services or environment variables MUST be removed.
- **FR-018**: No public API contracts (route paths, request/response shapes) may be altered by any cleanup change.
- **FR-019**: Code loaded via string-based plugin loading or migration discovery MUST NOT be removed without first confirming it is truly unused.
- **FR-020**: All changes MUST be committed using conventional commit format: `refactor:` for consolidation changes and `chore:` for dead code and test removal.
- **FR-021**: A pull request MUST be opened with a full categorized summary covering every change and explaining why each piece of code was identified as dead, stale, or duplicated.
- **FR-022**: All existing CI checks MUST pass after cleanup: linting, type checking, tests, and build verification for both backend and frontend.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All CI checks pass after cleanup with zero new failures introduced — linting, type checking, tests, and builds for both backend and frontend.
- **SC-002**: Zero public API contracts are altered — all existing route paths and request/response shapes remain identical before and after cleanup.
- **SC-003**: All five cleanup categories (backwards-compatibility shims, dead code, duplicated logic, stale tests, general hygiene) have at least one committed change addressing them.
- **SC-004**: The pull request description contains a categorized summary covering every change, organized by the five cleanup categories.
- **SC-005**: Total lines of dead or duplicated code removed is documented in the pull request summary.
- **SC-006**: No dynamically loaded code (plugin loading, migration discovery) is incorrectly removed — verified by auditing all removals against dynamic loading patterns.
- **SC-007**: The remaining test suite maintains or improves its pass rate — no previously passing test is broken by the cleanup.
- **SC-008**: Developers can navigate the cleaned codebase with reduced cognitive load, as measured by the elimination of unused definitions, stale comments, and duplicated logic.

## Assumptions

- The codebase uses conventional commits, and all cleanup changes will follow the established `refactor:` and `chore:` prefixes.
- The backend stack is Python 3.12 / FastAPI / Pydantic v2 / aiosqlite, and the frontend stack is TypeScript 5.4 / React 18 / Vite 5.4 / TanStack Query v5 / Tailwind CSS 3.4 / Shadcn UI. Cleanup is scoped to these technologies.
- CI checks include `ruff`, `pyright`, and `pytest` for the backend, and `eslint`, `tsc`, `vitest`, and `vite build` for the frontend. All must remain green.
- Dynamic code loading patterns exist in the codebase (plugin systems, migration discovery) and must be audited before removing any code that might be loaded dynamically.
- "Public API contracts" refers to route paths and request/response shapes exposed by the backend and consumed by the frontend or external clients. Internal helper functions, service methods, and utility types are not considered public API contracts.
- Migration files that are part of the active database schema migration chain must not be removed, even if the features they originally supported have been deleted.
- The cleanup is strictly internal — no user-facing behavior changes are expected or permitted.
- Stale `TODO`, `FIXME`, and `HACK` comments are defined as those referencing work that has been fully completed. Comments referencing ongoing or future work must be preserved.
