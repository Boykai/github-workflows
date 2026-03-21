# Feature Specification: Lint & Type Suppression Audit

**Feature Branch**: `001-lint-suppression-audit`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "Lint & Type Suppression Audit: Reduce ~111 noqa / type:ignore / eslint-disable Statements Across Backend & Frontend"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Audit and Resolve Backend Type Suppressions (Priority: P1)

As a developer, I want all `# type: ignore` and `# pyright:` suppressions in the backend source code audited and resolved so that the type checker catches real type errors instead of silently ignoring them.

There are currently 39 `# type: ignore` and 10 `# pyright:` directives across the backend source. The largest categories are `return-value` (12 instances — mostly cache-related), `type-arg` (6 instances — generic `asyncio.Task` without type parameters), `reportMissingImports` (5 instances — conditional imports), and `arg-type` (7 instances). Each suppression must be examined: if the underlying type issue can be fixed with proper annotations, generics, or narrowing, the suppression is removed. If the suppression is technically necessary (e.g., dynamic attribute access in logging, conditional third-party imports that may not be installed), it is retained with a justification comment.

**Why this priority**: Type suppressions mask the most dangerous class of bugs — logic errors, incorrect return types, and unsafe casts. Resolving these first delivers the highest safety improvement per suppression removed.

**Independent Test**: Can be fully tested by running `pyright` and `ruff check` across the backend source and verifying zero new errors are introduced while the suppression count is reduced by the target amount. All existing unit tests must continue to pass.

**Acceptance Scenarios**:

1. **Given** the backend source code with 49 type suppressions (`type: ignore` + `pyright:`), **When** the audit is complete, **Then** at least 60% of suppressions are removed by fixing the underlying type issues, and all remaining suppressions include an inline justification comment.
2. **Given** a `# type: ignore[return-value]` on a cache return, **When** the developer adds proper generic annotations or type narrowing, **Then** the suppression is no longer needed and the type checker passes without it.
3. **Given** a `# pyright: reportAttributeAccessIssue=false` file-level directive, **When** the underlying attribute access patterns are properly typed, **Then** the file-level suppression is removed and Pyright reports no errors.
4. **Given** a `# type: ignore[reportMissingImports]` for a conditional import, **When** the import is wrapped in a proper `TYPE_CHECKING` guard or try/except with typed fallback, **Then** the suppression is retained only if no typed alternative exists, with a justification comment.

---

### User Story 2 - Audit and Resolve Frontend Accessibility and React Hook Suppressions (Priority: P2)

As a developer, I want all `eslint-disable` directives in the frontend source code audited and resolved so that accessibility standards (jsx-a11y) are enforced and React hook dependency arrays are correct.

There are currently 14 `eslint-disable` directives across the frontend source. The breakdown is: 7 `react-hooks/exhaustive-deps` suppressions (incomplete dependency arrays), 5 `jsx-a11y` suppressions (3 backdrop-dismiss patterns using raw `div` click handlers, 2 autofocus patterns), and 2 `@typescript-eslint/no-explicit-any` suppressions. Each must be examined: accessibility suppressions should be replaced with semantic elements (e.g., `<button>` or `<dialog>` for backdrop dismiss), hook dependency arrays should be corrected or stabilized with `useCallback`/`useMemo`, and `any` types should be replaced with proper types where feasible.

**Why this priority**: Accessibility suppressions directly impact users with disabilities and represent potential compliance risks. Hook dependency suppressions can cause stale closures and subtle rendering bugs. These are the second-highest-impact category after type safety.

**Independent Test**: Can be fully tested by running `eslint` across the frontend source and verifying zero new warnings are introduced while the suppression count is reduced by the target amount. All existing component tests must continue to pass.

**Acceptance Scenarios**:

1. **Given** 5 `jsx-a11y` suppressions in the frontend, **When** the audit is complete, **Then** at least 4 are removed by replacing raw `div` click handlers with semantic interactive elements (e.g., `<button>`) and autofocus patterns with proper focus management.
2. **Given** 7 `react-hooks/exhaustive-deps` suppressions, **When** the audit is complete, **Then** each is either resolved by correcting the dependency array (using `useCallback`, `useMemo`, or refs to stabilize dependencies) or retained with a justification comment explaining why the dependency is intentionally excluded.
3. **Given** 2 `@typescript-eslint/no-explicit-any` suppressions, **When** the audit is complete, **Then** proper types replace `any` where the type can be determined, and any retained suppressions include a justification.

---

### User Story 3 - Audit and Resolve Backend Linter Suppressions (Priority: P3)

As a developer, I want all `# noqa` linter suppressions in the backend source code audited and resolved so that Ruff lint rules are genuinely enforced.

There are currently 21 `# noqa` directives in the backend source. The breakdown is: 12 `B008` (function call in default argument — all FastAPI `Depends()`), 6 `F401` (unused imports — re-exports in `__init__.py`), 1 `E402` (module-level import not at top), and 2 `PTH118`/`PTH119` (use of `os.path` instead of `pathlib`). Each category requires a different resolution strategy: `B008` suppressions for FastAPI `Depends()` are a well-known false positive and should be retained with a justification comment (or suppressed globally in linter config); `F401` re-exports should use explicit `__all__` declarations; `PTH` violations should be migrated to `pathlib` where safe.

**Why this priority**: These are lower-risk than type suppressions and accessibility issues. Most `B008` suppressions are legitimate (FastAPI pattern), and `F401` re-exports are structural. Resolution improves code hygiene but has lower safety impact.

**Independent Test**: Can be fully tested by running `ruff check` across the backend source and verifying zero new errors while the suppression count is reduced by the target amount. All existing unit tests must continue to pass.

**Acceptance Scenarios**:

1. **Given** 12 `B008` suppressions for FastAPI `Depends()`, **When** the audit is complete, **Then** a per-rule global exemption is configured in the linter settings (or a per-file exemption for API route files), eliminating the need for inline suppressions.
2. **Given** 6 `F401` suppressions for re-exported imports, **When** the audit is complete, **Then** each `__init__.py` uses an explicit `__all__` list to declare public re-exports, and the `F401` suppressions are removed.
3. **Given** 2 `PTH118`/`PTH119` suppressions, **When** the audit is complete, **Then** the file path operations are migrated to `pathlib` equivalents where it does not compromise security (CodeQL sanitizer patterns retained as-is with justification).

---

### User Story 4 - Audit and Resolve Test File Suppressions (Priority: P4)

As a developer, I want all type suppressions in test files audited and resolved so that test code maintains the same type safety standards as production code.

There are currently 27 `# type: ignore` directives in backend test files and 5 `@ts-expect-error` directives in frontend test files. Test suppressions are often used to access private attributes on mocks, override frozen/read-only fields, or shim browser globals. Each must be examined: private attribute access should use proper test helpers or fixtures, frozen field overrides should use mock construction parameters, and browser global shims should use typed test utilities.

**Why this priority**: Test suppressions are lower priority than production code suppressions because they don't affect runtime safety. However, untyped test code can mask interface changes and cause silent test rot.

**Independent Test**: Can be fully tested by running type checkers (`pyright`, `tsc`) and test suites (`pytest`, `vitest`) and verifying all tests pass with fewer suppressions.

**Acceptance Scenarios**:

1. **Given** 27 `# type: ignore` directives in backend tests, **When** the audit is complete, **Then** at least 50% are removed by using proper mock construction, typed fixtures, or cast helpers, and all remaining suppressions include justification comments.
2. **Given** 5 `@ts-expect-error` directives in frontend test files, **When** the audit is complete, **Then** WebSocket global overrides use a typed test utility and the `@ts-expect-error` directives are reduced or properly documented.

---

### Edge Cases

- What happens when removing a suppression reveals a genuine type error in the code? The underlying code must be fixed to resolve the type error, not just the suppression. If the fix is non-trivial, it should be flagged as a follow-up issue.
- What happens when a suppression is needed for a third-party library with incorrect type stubs? The suppression is retained with a comment citing the upstream issue and the specific version affected.
- What happens when removing a `react-hooks/exhaustive-deps` suppression causes an infinite re-render loop? The dependency must be stabilized using `useCallback`, `useMemo`, or `useRef`, not re-suppressed.
- What happens when a file-level `pyright` directive covers multiple attribute access patterns? Each pattern must be individually assessed; the file-level directive can only be removed if all patterns are resolved.
- What happens when migrating `os.path` to `pathlib` breaks a CodeQL sanitizer pattern? The `os.path` usage is retained with a justification comment referencing the CodeQL sanitizer requirement.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every suppression statement across the codebase MUST be catalogued with its file, line, rule, and category (type safety, linting, accessibility, test-specific).
- **FR-002**: Each suppression MUST be classified as either "removable" (underlying issue can be fixed) or "justified" (technically necessary and documented).
- **FR-003**: All "removable" suppressions MUST be resolved by fixing the underlying code issue, not by changing linter/type-checker configuration to ignore the rule globally (except for FR-009).
- **FR-004**: All "justified" suppressions that are retained MUST include an inline comment explaining why the suppression is necessary, citing the specific technical constraint.
- **FR-005**: All changes MUST pass the existing linter configurations (`ruff check`, `eslint`, `pyright`, `tsc --noEmit`) without introducing new errors or warnings.
- **FR-006**: All changes MUST pass the existing test suites (`pytest`, `vitest`) without introducing test failures.
- **FR-007**: Frontend accessibility suppressions (`jsx-a11y`) MUST be resolved by replacing non-semantic elements with proper semantic interactive elements (e.g., replace `<div onClick>` with `<button>` for backdrop dismiss patterns).
- **FR-008**: Backend `__init__.py` re-export files MUST use explicit `__all__` declarations instead of `# noqa: F401` on individual imports.
- **FR-009**: FastAPI `Depends()` false-positive linter warnings (`B008`) MUST be resolved via a targeted per-rule configuration in the linter settings rather than per-line suppressions.
- **FR-010**: The total suppression count across the codebase MUST be reduced by at least 50% from the current baseline of ~116 statements.
- **FR-011**: No behavioral changes MUST be introduced — all changes are strictly internal refactoring of type annotations, element semantics, and linter configuration.

### Key Entities

- **Suppression Statement**: An inline directive that disables a specific linter or type-checker rule. Attributes: file path, line number, directive type (`noqa`, `type: ignore`, `pyright:`, `eslint-disable`, `@ts-expect-error`), specific rule code, category (type safety / lint / accessibility / test), and disposition (removed / retained with justification).
- **Suppression Category**: A grouping of related suppressions by their root cause. Categories include: cache return types, generic type parameters, conditional imports, FastAPI dependency injection, re-exports, accessibility patterns, React hook dependencies, explicit any types, test mocks, and browser global shims.
- **Justification Comment**: An inline comment accompanying a retained suppression that explains why it cannot be removed, referencing the specific technical constraint (e.g., "third-party type stub limitation", "CodeQL sanitizer requirement", "FastAPI convention").

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Total suppression count is reduced by at least 50% from the baseline of ~116 statements (target: ≤58 remaining).
- **SC-002**: 100% of retained suppressions include an inline justification comment explaining why removal is not feasible.
- **SC-003**: Zero new linter errors, type-checker errors, or test failures are introduced by the changes.
- **SC-004**: All 5 `jsx-a11y` accessibility suppressions are resolved or reduced to at most 1, with semantic interactive elements replacing raw `div` click handlers.
- **SC-005**: All existing tests (3,365+ backend unit tests, 1,217+ frontend tests) continue to pass after changes.
- **SC-006**: Developers reviewing the codebase can understand every retained suppression within 30 seconds by reading its justification comment.

## Assumptions

- The existing linter and type-checker configurations (`ruff`, `eslint`, `pyright`, `tsc`) are correct and should not be relaxed — the goal is to make the code conform, not to weaken the rules.
- FastAPI's `Depends()` pattern is a well-known false positive for `B008` (function call in default argument) and can be handled via per-rule linter configuration.
- Third-party libraries with incorrect type stubs (e.g., `copilot` package for `reportMissingImports`) will retain suppressions with version-specific justification comments rather than creating local type stubs.
- Accessibility refactoring (replacing `<div onClick>` with semantic elements) will maintain the same visual appearance and interaction behavior.
- React hook dependency corrections will not change component rendering behavior; any dependency stabilization (via `useCallback`/`useMemo`) is a safe optimization.
- Test file suppressions for mock attribute access and frozen field overrides are lower priority and may require test helper utilities that are out of scope for this audit.

## Scope Boundaries

### In Scope

- All `# noqa`, `# type: ignore`, `# pyright:`, `eslint-disable`, `@ts-expect-error`, and `@ts-ignore` directives in the `solune/backend/src/`, `solune/frontend/src/`, `solune/backend/tests/`, and related source directories.
- Linter configuration changes (e.g., per-rule exemptions in `pyproject.toml` or `eslint.config`) that eliminate the need for inline suppressions.
- Accessibility refactoring to replace non-semantic elements with proper interactive elements.
- Adding `__all__` declarations to `__init__.py` files.
- Adding inline justification comments to all retained suppressions.

### Out of Scope

- Adding new linting rules or type-checking rules beyond what is currently configured.
- Refactoring code for reasons other than resolving suppressions (no opportunistic cleanup).
- Creating local type stubs for third-party packages.
- Changing test infrastructure or adding new test utilities (beyond what is needed to remove test suppressions).
- Performance optimization or feature changes.
