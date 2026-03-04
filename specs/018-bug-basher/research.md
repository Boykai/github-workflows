# Research: Bug Basher — Full Codebase Review & Fix

**Feature**: `018-bug-basher` | **Date**: 2026-03-04

## Research Tasks

### R1: Backend Error Handling Patterns and Known Issues

**Decision**: Audit all `except` blocks in `backend/src/` for two anti-patterns: (1) raw `str(e)` leaking into API responses (violates established convention — see `logging_utils.py`), and (2) bare `except:` or overly broad `except Exception` that silently swallows errors. Fix confirmed instances using the established `safe_error_response()` and `handle_service_error()` patterns from `logging_utils.py`.

**Rationale**: Repository memories document a known convention: "Error messages in API responses must NOT include raw exception text (`str(e)`)." Multiple files have been flagged in prior reviews (`board.py`, `chat.py`, `workflow.py`, `cleanup_service.py`, `agent_creator.py`, `signal_chat.py`). This is the highest-signal area for security and runtime error findings. The `handle_service_error()` function's return type annotation should be `NoReturn` (per repository memory) — verify and fix if needed.

**Alternatives considered**:
- **Custom error sanitization per file**: Rejected — `safe_error_response()` and `handle_service_error()` already exist as centralized helpers and should be reused (DRY).
- **Ignoring `str(e)` in internal-only endpoints**: Rejected — all endpoints are potentially user-facing and should follow the same convention.

### R2: Production Assert Usage

**Decision**: Audit `backend/src/` for `assert` statements in production code paths. Replace with proper `if`-checks and error handling (`raise`, `return`, `log`). Python's `-O` flag strips asserts, making them unreliable for production validation.

**Rationale**: Repository memory flags known instances in `pipeline.py:795-796` and `chat.py:469`. These are runtime errors waiting to happen in optimized deployments.

**Alternatives considered**:
- **Leave asserts and document the `-O` restriction**: Rejected — production code should not depend on optimization flags. Proper error handling is the correct fix.
- **Add a custom `production_assert()` function**: Over-engineering — simple `if`/`raise` is sufficient and follows existing patterns.

### R3: Frontend Mock Leak Detection

**Decision**: Audit all frontend test files for mock objects (`vi.spyOn`, `vi.fn()`, `MagicMock` equivalents) that could leak into production code paths. Verify that `mockRestore()` or `mockClear()` is called in `afterEach`/`afterAll` blocks. The established pattern (per repository memory) uses `vi.spyOn` with `mockRestore()` in `beforeEach`/`afterEach` pairs.

**Rationale**: Repository memory documents the pattern from `ErrorBoundary.test.tsx` and `ThemeProvider.test.tsx`. Tests that don't follow this pattern risk polluting other tests with stale mocks or leaking mock behavior into production code paths.

**Alternatives considered**:
- **Global `restoreAllMocks` in vitest config**: Could mask per-test cleanup issues. Individual `mockRestore()` is more explicit and easier to debug.
- **Ignoring mock leaks in isolated test files**: Rejected — even single-file leaks can cause intermittent test failures.

### R4: Backend Test Execution Strategy

**Decision**: Run backend tests file-by-file using `timeout 30 python -m pytest tests/unit/test_X.py -q` to avoid hanging. Use `ruff check src tests && ruff format --check src tests` for linting. This is the established and verified strategy per repository memory.

**Rationale**: Running all ~1284 tests at once may hang. File-by-file execution with a 30-second timeout ensures reliable feedback during iterative bug fixing.

**Alternatives considered**:
- **Run all tests at once with a global timeout**: Risk of hanging or masking individual test failures.
- **Run only affected tests**: Risk of missing regressions in unrelated files caused by shared state changes.

### R5: Frontend Test and Lint Strategy

**Decision**: Run frontend tests with `cd frontend && npx vitest run`. Type checking with `npx tsc --noEmit`. Linting with `npx eslint .`. Tests use happy-dom environment with vitest globals enabled.

**Rationale**: Verified strategy per repository memory. Frontend tests are more reliable than backend for batch execution (~334 tests, ~33 files).

**Alternatives considered**:
- **File-by-file execution**: Unnecessary — frontend tests don't hang like backend tests.
- **Skipping type checking**: Rejected — `tsc --noEmit` catches type errors that are logic bugs.

### R6: Input Validation and Security Audit Scope

**Decision**: Focus security audit on: (1) API endpoint input validation (Pydantic model constraints, path parameter validation), (2) authentication/authorization checks in route handlers, (3) secrets/tokens in configuration files and source code, (4) SQL injection risks in raw query construction, (5) XSS risks in frontend components that render user input.

**Rationale**: These are the five most common security vulnerability categories in web applications. The project uses Pydantic for validation (good baseline) and SQLite via aiosqlite (parameterized queries are standard). The highest-risk areas are: custom query construction bypassing Pydantic, missing auth checks on new endpoints, and `.env.example` or hardcoded secrets.

**Alternatives considered**:
- **Automated SAST tooling only**: Insufficient — many logic-level security issues require manual review.
- **Limiting to backend only**: Rejected — frontend XSS and client-side validation bypasses are in scope.

### R7: Commit and Review Strategy

**Decision**: Group bug fixes by category and file proximity. Each commit message follows the format: "fix(<category>): <what> — <why> — <how>". Ambiguous issues get `# TODO(bug-bash):` comments with structured descriptions. The final summary table is generated after all fixes are applied and all tests pass.

**Rationale**: Grouping by category allows reviewers to assess related fixes together. The structured commit message format ensures traceability from the summary table back to individual commits.

**Alternatives considered**:
- **One commit per bug**: Maximizes atomicity but creates excessive commit noise for minor fixes.
- **Single bulk commit**: Rejected — makes code review impossible and violates the clear-commit-message requirement (FR-005).

### R8: Handling `handle_service_error()` Return Type

**Decision**: Verify whether `handle_service_error()` in `logging_utils.py` has the correct `NoReturn` type annotation. If annotated as `-> None`, change to `-> NoReturn` since the function always raises. This is a type safety bug that could mask unreachable code warnings from type checkers.

**Rationale**: Repository memory explicitly flags this: "Its return type annotation should be `NoReturn`, not `None`." A `-> None` annotation misleads pyright/mypy into thinking code after `handle_service_error()` is reachable.

**Alternatives considered**:
- **Leave as `-> None`**: Silently suppresses useful type checker warnings. This is a confirmed type bug.
- **Add `@typing.no_return` decorator**: Not a standard approach; explicit `-> NoReturn` return annotation is idiomatic.

## Summary

All research tasks resolved. No NEEDS CLARIFICATION items remain. Key findings:

1. **Error handling** is the highest-signal area — `str(e)` leaks and overly broad exception handling are documented anti-patterns in this codebase
2. **Production asserts** are known issues at specific locations (`pipeline.py`, `chat.py`)
3. **Mock cleanup** patterns are established but may not be consistently followed across all test files
4. **Test execution** must be done file-by-file for backend (timeout 30s each), batch for frontend
5. **Security audit** focuses on input validation, auth checks, secrets exposure, SQL injection, and XSS
6. **Commit strategy** groups by category with structured commit messages
7. **Type annotations** — `handle_service_error()` return type is a known bug to fix
8. **No new dependencies** are needed — all fixes use existing patterns and utilities
