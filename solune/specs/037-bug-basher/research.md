# Research: Bug Basher — Full Codebase Review & Fix

**Feature**: 037-bug-basher | **Date**: 2026-03-12

## R1: Codebase Scope and File Inventory

**Decision**: Review all source files in `backend/src/` (~40 Python files) and `frontend/src/` (~261 TypeScript/TSX files), plus their corresponding test files. Configuration files (`.env.example`, `docker-compose.yml`, workflow YAML files) are included in the security scan but excluded from logic/runtime review.

**Rationale**: The spec requires auditing "every file in the repository" (FR-001). However, third-party dependencies (`node_modules/`, `.venv/`), build artifacts (`dist/`, `__pycache__/`), and generated files (migrations that have already been applied) are excluded as they are not authored code. The `.specify/` directory contains templates and scripts that are reviewed for security only (secrets exposure) but not for logic bugs since they are development tooling, not production code.

**Alternatives considered**:
- Reviewing only files changed in recent PRs (rejected: spec explicitly requires full codebase review)
- Including `node_modules` and dependencies (rejected: out of scope, would require dependency audit tools like `npm audit` or `pip-audit`)
- Reviewing only backend or only frontend (rejected: spec requires comprehensive review of both)

## R2: Backend Testing Framework and Patterns

**Decision**: Use `pytest` with the existing test structure in `backend/tests/unit/`. New regression tests follow the existing naming convention `test_{module_name}.py` and use the established fixtures from `conftest.py`. Async tests use `pytest-asyncio` with `@pytest.mark.asyncio` decorator.

**Rationale**: The backend has ~1736 existing unit tests that all pass. The test infrastructure is mature with shared fixtures for database mocking, GitHub API mocking, and service instantiation. New regression tests should integrate seamlessly with this infrastructure rather than introducing new patterns.

**Alternatives considered**:
- Creating a separate `tests/regression/` directory (rejected: existing convention places all unit tests in `tests/unit/`, adding a new directory adds unnecessary complexity)
- Using `unittest` instead of `pytest` (rejected: entire codebase uses pytest)
- Adding integration tests (rejected: FR-003 requires regression tests, not integration tests; integration tests would add complexity and execution time)

## R3: Frontend Testing Framework and Patterns

**Decision**: Use `vitest` with `happy-dom` environment. New regression tests are colocated with source files following the existing pattern (`ComponentName.test.tsx` alongside `ComponentName.tsx`). React Testing Library is used for component testing. Mock patterns follow the existing `vi.mock()` convention.

**Rationale**: The frontend has ~644 existing Vitest tests. Tests are colocated with their source files. The mock pattern using `vi.mock()` and `vi.fn()` is well-established. Following these patterns ensures new tests are discoverable and maintainable.

**Alternatives considered**:
- Centralizing tests in a `__tests__/` directory (rejected: codebase uses colocated tests)
- Using Cypress or Playwright for E2E tests (rejected: out of scope for regression tests)
- Using Jest instead of Vitest (rejected: project uses Vitest exclusively)

## R4: Security Review Methodology

**Decision**: Use a multi-layered approach: (1) manual code review for domain-specific security issues (auth bypasses, business logic), (2) `ruff` for Python security-related lint rules, (3) pattern-based search for common vulnerability indicators (hardcoded secrets, `eval()`, `dangerouslySetInnerHTML`, unsanitized SQL). CodeQL scanning may be applied as a final validation step.

**Rationale**: Automated security scanning tools catch common patterns but miss business logic vulnerabilities. Manual review is necessary for auth bypasses, incorrect access controls, and domain-specific injection points. The combination provides broad coverage without adding new tool dependencies.

**Alternatives considered**:
- Using only automated tools like Bandit or Semgrep (rejected: would miss business logic vulnerabilities; also violates FR-010 no new dependencies)
- Hiring external penetration testers (rejected: out of scope for a code-level bug bash)
- Reviewing only OWASP Top 10 categories (rejected: spec requires broader review including resource leaks and crypto issues)

## R5: Bug Fix Commit Strategy

**Decision**: Each bug fix is a focused, minimal change to the affected file(s) plus its regression test. Multiple bugs in the same file can be addressed in a single commit if they are in the same priority category. Each commit message follows the format: "fix({category}): {what} in {file} — {why and how}".

**Rationale**: FR-008 requires clear commit messages explaining what, why, and how. FR-012 requires minimal focused fixes. Grouping by category within a file keeps commits manageable while maintaining traceability.

**Alternatives considered**:
- One commit per bug regardless of proximity (rejected: creates excessive commit noise for adjacent fixes)
- One large commit for all fixes (rejected: makes it impossible to revert individual fixes and violates FR-008)
- Squash all commits at the end (rejected: loses individual fix history and commit messages)

## R6: Ambiguity Handling Protocol

**Decision**: When a potential bug is ambiguous or involves trade-offs, add a `# TODO(bug-bash):` comment in the source code at the relevant location. The comment includes: (1) description of the issue, (2) available options for resolution, (3) why it needs human review. The issue is also recorded in the summary table with status "⚠️ Flagged (TODO)".

**Rationale**: FR-005 explicitly defines this protocol. The `TODO(bug-bash)` prefix makes these comments searchable and distinguishable from regular TODOs. Including them in both code and summary ensures nothing is lost.

**Alternatives considered**:
- Creating GitHub issues for each ambiguous item (rejected: adds noise to the issue tracker; code comments are more discoverable during code review)
- Making a best-guess fix anyway (rejected: violates FR-005 and risks introducing new bugs from incorrect assumptions)
- Ignoring ambiguous issues entirely (rejected: violates the completeness requirement in SC-001)

## R7: Linting and Formatting Validation

**Decision**: Run `python -m ruff check src/` for Python linting and `npm run lint` + `npm run type-check` for TypeScript validation. Any pre-existing violations are documented but not fixed unless they represent actual bugs. New violations introduced by fixes must be resolved before committing.

**Rationale**: FR-007 requires linting checks to pass "without new violations." This means the baseline of existing violations is acceptable, but fixes must not introduce additional ones. Ruff is already configured in `pyproject.toml` with target version `py313`. ESLint and TypeScript strict mode are configured in the frontend.

**Alternatives considered**:
- Fixing all pre-existing lint violations (rejected: violates FR-012 minimal fixes and FR-009 no architecture changes)
- Running `black` or `prettier` formatting (rejected: would create noisy diffs unrelated to bug fixes)
- Skipping lint validation (rejected: violates FR-007)

## R8: Mock Leak Detection Strategy

**Decision**: Search for patterns where `MagicMock` or `Mock` objects could leak into production code paths — specifically: (1) mock objects used as file paths, database paths, or URLs, (2) mock objects passed through service layers without being scoped to the test, (3) patches that don't use `autospec=True` and could silently accept wrong arguments. Focus on `backend/tests/unit/` where `unittest.mock` is used.

**Rationale**: The spec explicitly calls out "MagicMock objects leaking into production paths like database file paths" (User Story 4, Acceptance Scenario 2). This is a known anti-pattern where tests pass but with mock objects being used as real values (e.g., `MagicMock()` as a file path creates a file named `<MagicMock ...>`).

**Alternatives considered**:
- Only checking for `MagicMock` in file paths (rejected: mock leaks can happen in any production code path, not just file paths)
- Using `autospec=True` on all mocks globally (rejected: would be a large refactor violating FR-012)
- Ignoring mock leaks as a test-only concern (rejected: spec explicitly identifies this as P4 priority)
