# Research: Bug Basher — Full Codebase Review & Fix

**Feature**: 042-bug-basher
**Date**: 2026-03-15
**Status**: Complete

## Research Tasks

### R1: Backend Testing Infrastructure — pytest Configuration & Patterns

**Decision**: Use the existing pytest setup at `solune/backend/tests/` with `conftest.py` for fixtures, organized into `unit/`, `integration/`, and `helpers/` directories. Run via `cd solune/backend && python -m pytest tests/ -v`.

**Rationale**: The backend already has a mature test infrastructure with clearly separated unit and integration tests, shared fixtures in `conftest.py`, and helper utilities. The `pyproject.toml` configures pytest with `asyncio_mode = "auto"` for async test support, and `testpaths = ["tests"]`. New regression tests should follow the existing organization: unit tests for isolated function behavior, integration tests for cross-service or database-dependent behavior. Test file naming follows the `test_*.py` convention.

**Alternatives considered**:

- **Creating a separate regression test directory**: Would fragment the test organization. Existing `unit/` and `integration/` directories already provide clear placement guidance.
- **Using a different test runner**: pytest is already configured and operational. Changing runners would violate the "no new dependencies" constraint.

---

### R2: Frontend Testing Infrastructure — Vitest Configuration & Patterns

**Decision**: Use the existing vitest setup at `solune/frontend/` with `vitest.config.ts`, test utilities in `src/test/`, and factory patterns in `src/test/factories/`. Run via `cd solune/frontend && npx vitest run`.

**Rationale**: The frontend uses vitest with React Testing Library, configured in `vitest.config.ts`. Test files are co-located with source files using `*.test.{ts,tsx}` naming. The `src/test/` directory contains shared utilities (`test-utils.tsx`, `a11y-helpers.ts`) and factory functions (`factories/index.ts`) for creating test data. The setup file (`src/test/setup.ts`) configures the test environment. Over 40 existing test files demonstrate established patterns for component testing, hook testing, and utility testing.

**Alternatives considered**:

- **Using Playwright for all tests**: Playwright is configured for E2E tests only (`solune/frontend/e2e/`). Unit and component tests should use vitest for speed and isolation.
- **Adding Jest**: Would conflict with the existing vitest setup and violate the "no new dependencies" constraint.

---

### R3: Python Linting — ruff Configuration & Enforcement

**Decision**: Use ruff for Python linting with the existing configuration in `solune/backend/pyproject.toml`. Run via `cd solune/backend && python -m ruff check src/`. Line length is set to 100 characters.

**Rationale**: The `pyproject.toml` configures ruff with `line-length = 100` and selected rules. All bug fixes must pass the existing ruff configuration without introducing new violations (FR-007). The linter catches common Python issues including unused imports, undefined names, and style violations. Running ruff after each fix ensures compliance before committing.

**Alternatives considered**:

- **Using flake8 or pylint**: ruff is already configured and operational. Adding alternative linters would be redundant and violate constraints.
- **Modifying ruff rules**: Existing rules define the project's code style standard. Changing them is out of scope.

---

### R4: TypeScript Linting — ESLint Configuration & Enforcement

**Decision**: Use eslint with the existing configuration in `solune/frontend/eslint.config.js`. Run via `cd solune/frontend && npm run lint`.

**Rationale**: The frontend uses eslint with TypeScript support, configured via the flat config format (`eslint.config.js`). All TypeScript fixes must pass the existing eslint configuration. The `package.json` includes a `lint` script for convenience. Prettier is also configured (`.prettierrc`) for formatting — fixes should not introduce formatting violations.

**Alternatives considered**:

- **Adding stricter rules**: Existing rules define the standard. Tightening them would flag pre-existing code and is out of scope for the bug bash.
- **Using TypeScript compiler as sole checker**: `tsc` catches type errors but not the style/quality rules eslint enforces. Both should pass.

---

### R5: Security Review Patterns — Common Vulnerabilities in FastAPI + React

**Decision**: Focus security review on these high-risk patterns specific to the Solune tech stack:

1. **Injection risks**: SQL injection via raw queries (check for f-strings or `.format()` in SQL), command injection via `subprocess` or `os.system`, template injection in prompt files
2. **Authentication/authorization bypasses**: Missing auth dependency injection in route handlers, incorrect guard configuration in `guard-config.yml`, middleware ordering issues in `main.py`
3. **Secrets exposure**: Hardcoded tokens/keys in source (especially `config.py`, `.env.example`, Docker files), secrets in logging output
4. **Insecure defaults**: Debug mode enabled in production configs, permissive CORS settings, disabled security headers in CSP middleware
5. **Input validation**: Missing Pydantic model validation on API inputs, unvalidated file paths (especially in `app_service.py` which uses `_safe_app_path`), unvalidated file uploads

**Rationale**: The tech stack (FastAPI + SQLite + React) has well-known vulnerability patterns. FastAPI's dependency injection for auth and Pydantic for validation are the primary defense mechanisms — any route missing these is a potential vulnerability. The `_safe_app_path` pattern in `app_service.py` (which validates paths stay within `_APPS_DIR`) shows the project is security-aware, so the review should check for consistency of this pattern across all filesystem operations. SQLite with parameterized queries via SQLAlchemy is generally safe, but raw SQL in migrations or ad-hoc queries could be vulnerable.

**Alternatives considered**:

- **Running SAST tools (Bandit, Semgrep)**: These tools can supplement manual review but cannot replace human judgment for architecture-level security issues. The manual review is primary; automated tools are complementary.
- **Penetration testing**: Out of scope — the bug bash is a static code review, not a dynamic security assessment.

---

### R6: Runtime Error Patterns — Common Issues in Async Python + React

**Decision**: Focus runtime error review on:

1. **Unhandled exceptions**: Missing try/except in async route handlers, bare `except:` that swallow errors silently, missing error responses
2. **Resource leaks**: Database connections not closed in error paths, file handles without context managers, WebSocket connections without cleanup
3. **Null/None references**: Optional fields accessed without guards, dictionary `.get()` vs `[]` access, nullable database columns accessed directly
4. **Missing imports**: Conditional imports that fail, circular import patterns, dynamic imports that reference non-existent modules
5. **Type errors**: Pydantic model field type mismatches, incorrect enum value usage (e.g., the known `accepted` vs `confirmed` status mapping in `chat_recommendations`), datetime parsing issues with `Z` suffix

**Rationale**: The async Python + SQLite combination introduces specific resource management challenges. The known `chat_recommendations.status` mapping issue (DB stores `accepted`, code uses `confirmed`) is an example of the type of inconsistency to look for. The `fromisoformat` issue with `Z` suffix timestamps is another known pattern. React hooks with improper cleanup (`useEffect` missing cleanup functions) are a common source of memory leaks in the frontend.

**Alternatives considered**:

- **Running type checkers (pyright, mypy)**: These complement manual review for type errors. pyright is mentioned in the test commands, suggesting it may already be used.
- **Runtime profiling**: Out of scope — the bug bash is static analysis.

---

### R7: Logic Bug Patterns — Verification Strategy

**Decision**: Focus logic bug review on:

1. **State transitions**: Enum value mismatches between DB and code, incorrect status updates in services, race conditions in concurrent operations
2. **API contract violations**: Response models that don't match documented types, missing fields in responses, incorrect HTTP status codes
3. **Off-by-one errors**: Pagination logic, array slicing, range boundaries in loops
4. **Data flow**: Values that are transformed incorrectly between layers (API → service → database), incorrect join conditions, missing filters
5. **Control flow**: Unreachable code after early returns, incorrect boolean logic, missing break/continue in loops

**Rationale**: Logic bugs are the most diverse category and require understanding of intended behavior. The spec's key entities (Bug Report Entry, Regression Test) provide the framework for documenting each finding. The existing test suite is the primary reference for "intended behavior" — if a test asserts a specific outcome, that outcome is the expected behavior.

**Alternatives considered**:

- **Property-based testing (Hypothesis)**: Powerful for finding edge cases but would add a dependency. Out of scope.
- **Formal verification**: Overkill for a bug bash. Manual code review is sufficient.

---

### R8: Test Quality Assessment — Mock Leak and Coverage Patterns

**Decision**: Focus test quality review on:

1. **Mock leaks**: `MagicMock` objects appearing in non-test paths (e.g., as file paths, database URIs), patches not properly scoped with `with` statements or decorators
2. **Assertions that never fail**: Tests with `assert True`, `assert response is not None` on non-nullable returns, overly permissive assertions
3. **Tests that pass for wrong reason**: Tests that mock the exact thing they should be testing, tests where the assertion matches the mock return value rather than real behavior
4. **Missing coverage**: Critical paths with no test (especially error handling, edge cases, security-relevant code)
5. **Test isolation**: Tests that depend on execution order, tests that share mutable state, tests that modify global configuration

**Rationale**: The spec explicitly calls out mock leaks (e.g., `MagicMock` objects leaking into production paths like database file paths) as a specific concern. This suggests the project has experienced this issue. The `conftest.py` and test helpers should be reviewed for patterns that could cause leaks. Frontend tests should be checked for proper cleanup of rendered components and event listeners.

**Alternatives considered**:

- **Coverage reporting (coverage.py, istanbul)**: These tools identify untested lines but not test quality. A 100% coverage report doesn't mean tests are meaningful. Manual review is needed for quality assessment.
- **Mutation testing**: Excellent for finding tests that pass for wrong reasons, but adds dependencies and significant runtime. Out of scope for this bug bash.
