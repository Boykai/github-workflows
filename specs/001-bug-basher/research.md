# Research: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher | **Date**: 2026-03-26 | **Phase**: 0 (Outline & Research)

## Research Tasks

### R-001: Backend Technology Stack & Best Practices

**Context**: The backend is Python 3.12+ / FastAPI with aiosqlite (SQLite), Pydantic models, and async patterns throughout.

**Decision**: Use the existing CI validation pipeline as the quality gate — `ruff check`, `ruff format --check`, `bandit`, `pyright`, and `pytest --cov` with 75% coverage enforcement.

**Rationale**: The project already has a mature, well-configured linting and testing pipeline. Leveraging existing tools ensures consistency and avoids adding new dependencies (FR-005). The `ruff` configuration covers pycodestyle, Pyflakes, isort, flake8-bugbear, comprehensions, pyupgrade, refurb, pathlib, perflint, and Ruff-specific rules — comprehensive coverage for code quality scanning.

**Alternatives Considered**:
- Adding `pylint` or `mypy`: Rejected — the project uses `ruff` + `pyright` which provides equivalent coverage without new dependencies.
- Adding `safety` for vulnerability scanning: Rejected — `pip-audit` is already configured and `bandit` covers code-level security.

---

### R-002: Frontend Technology Stack & Best Practices

**Context**: The frontend is TypeScript 5.x / React 19 with Vite, Vitest, ESLint, Prettier, and Tailwind CSS.

**Decision**: Use the existing frontend validation pipeline — `npm audit --audit-level=high`, `npm run lint`, `npm run type-check`, `npm run test`, and `npm run build`.

**Rationale**: The frontend has ESLint configured via `eslint.config.js`, TypeScript strict checking via `tsconfig.json`, and Vitest for unit testing. These tools catch type errors, unused variables, import issues, and runtime failures.

**Alternatives Considered**:
- Adding `eslint-plugin-security`: Rejected — no new dependencies allowed.
- Running Stryker mutation testing: Available (`test:mutate`) but not part of the core CI pipeline and would be too slow for a bug bash review.

---

### R-003: Security Review Patterns for Python/FastAPI

**Context**: Security vulnerabilities are the highest priority (P1). The backend handles auth, encryption, webhooks, and external API integrations.

**Decision**: Focus security review on:
1. **Authentication/Authorization**: `github_auth.py`, `admin_guard.py`, `session_store.py` — verify token validation, session management, and admin access controls.
2. **Input Validation**: All API route handlers — verify Pydantic model validation on request bodies, path parameters, and query parameters.
3. **Secrets Management**: `config.py`, `encryption.py`, `.env.example` — verify no hardcoded secrets, proper encryption key handling, and secure defaults.
4. **Injection Prevention**: `database.py`, `chat_store.py`, any raw SQL — verify parameterized queries.
5. **CSRF/CSP/Rate Limiting**: Middleware files — verify correct configuration and no bypasses.

**Rationale**: These are the highest-risk areas in the codebase based on the architecture. FastAPI's Pydantic integration provides automatic input validation for typed endpoints, but untyped or `Any`-typed parameters could be vulnerable.

**Alternatives Considered**:
- Full OWASP Top 10 audit: The scope naturally covers the applicable categories (injection, broken auth, security misconfiguration, etc.) through the focused file review.

---

### R-004: Runtime Error Patterns in Async Python

**Context**: The backend is fully async (FastAPI + aiosqlite). Common async runtime error patterns include unhandled exceptions in coroutines, resource leaks, and race conditions.

**Decision**: Focus runtime review on:
1. **Exception handling**: Verify `try/except` blocks in all service methods, especially around external API calls (`httpx`, `githubkit`) and database operations.
2. **Resource management**: Verify `async with` for database connections, HTTP clients, and file handles. Check for proper cleanup in error paths.
3. **Null/None references**: Check for unguarded `.get()` calls, optional field access without checks, and dictionary key access without validation.
4. **Import correctness**: Verify all imports resolve and no circular dependencies exist (pyright should catch these).

**Rationale**: The `handle_service_error()` pattern (in `logging_utils.py`) is the established convention for safe error handling — verify it's used consistently across all service files.

**Alternatives Considered**:
- Running `asyncio` debug mode: Useful for development but not applicable to static code review.

---

### R-005: Test Quality Assessment Strategy

**Context**: The test suite has 3575+ backend unit tests and 155+ frontend test files. Test quality issues include mock leaks, assertions that never fail, and untested paths.

**Decision**: Focus test quality review on:
1. **Mock isolation**: Search for `MagicMock`, `patch`, and `Mock` usage — verify mocks don't leak into production code paths (especially file paths, database connections, URLs).
2. **Assertion effectiveness**: Look for tests with no assertions, tests that catch exceptions too broadly, and tests where the assertion condition is always true.
3. **Coverage gaps**: Cross-reference service files with test files to identify untested services or untested branches within tested services.
4. **Test-for-wrong-reason**: Look for tests that pass because of mock behavior rather than actual code behavior.

**Rationale**: The project already has `pytest-cov` with 75% coverage enforcement and property-based testing with Hypothesis. The focus should be on quality of existing tests rather than just coverage numbers.

**Alternatives Considered**:
- Running mutation testing (`mutmut`): Available but too time-intensive for a bug bash. Best used as a follow-up activity.

---

### R-006: Code Quality Patterns & Dead Code Detection

**Context**: Code quality is the lowest priority (P5) but still in scope. The codebase is large (~143 backend + ~419 frontend source files).

**Decision**: Focus code quality review on:
1. **Dead code**: Functions/methods/classes with no callers, unreachable branches after early returns, and unused imports (ruff `F` rules should catch most).
2. **Duplicated logic**: Similar patterns across service files that could be consolidated.
3. **Hardcoded values**: Magic numbers, hardcoded URLs, timeouts, or limits that should be in `config.py` or `constants.py`.
4. **Silent failures**: Empty `except` blocks, swallowed errors, missing log statements in error paths.

**Rationale**: Ruff already catches many code quality issues (unused imports, unreachable code). The manual review focuses on semantic issues that static analysis cannot detect.

**Alternatives Considered**:
- Using `vulture` for dead code: Rejected — no new dependencies. Ruff's `F` rules + manual review provides sufficient coverage.

---

### R-007: CI Pipeline Integration & Validation Strategy

**Context**: The CI pipeline (`.github/workflows/ci.yml`) runs backend and frontend checks in parallel. All fixes must pass CI.

**Decision**: Validation order for the bug bash:
1. **Backend**: `ruff check src tests` → `ruff format --check src tests` → `bandit -r src/ -ll -ii --skip B104,B608` → `pyright src` → `pytest --cov=src --cov-report=term-missing --ignore=tests/property --ignore=tests/fuzz --ignore=tests/chaos --ignore=tests/concurrency`
2. **Frontend**: `npm audit --audit-level=high` → `npm run lint` → `npm run type-check` → `npm run test` → `npm run build`
3. Run full validation after each category phase (P1 security, P2 runtime, etc.) to catch regressions early.

**Rationale**: This mirrors the exact CI pipeline, ensuring that local validation matches what CI will enforce. Running after each phase prevents cascading failures.

**Alternatives Considered**:
- Running only at the end: Rejected — too risky for a large-scale review. Early validation catches issues before they compound.

---

### R-008: Commit Strategy & Summary Output Format

**Context**: FR-007 requires clear commit messages. FR-010 requires a summary table. The constraint says each fix should be minimal and focused.

**Decision**:
- **Commit granularity**: One commit per bug category per phase (e.g., "fix: P1 security — sanitize user input in webhook handler"). Group closely related fixes within the same file into a single commit.
- **Commit message format**: `fix(<category>): <what> — <why> — <how>` or `test(<category>): add regression test for <bug>`
- **Summary table format**: As specified in the issue — sequential number, file, lines, category, description, status (✅ Fixed / ⚠️ Flagged).

**Rationale**: Grouping by category keeps the git history readable while still providing traceability. The summary table is the final deliverable that ties everything together.

**Alternatives Considered**:
- One commit per bug: Would create too many small commits for a comprehensive review. Grouping by category provides a better balance.

## Summary of Resolved Items

All Technical Context fields are resolved — no NEEDS CLARIFICATION items remain.

| Item | Resolution |
|------|-----------|
| Backend stack | Python 3.12+, FastAPI, aiosqlite, Pydantic, async patterns |
| Frontend stack | TypeScript 5.x, React 19, Vite, Vitest, Tailwind CSS |
| Security review approach | Focused on auth, input validation, secrets, injection, middleware |
| Runtime error patterns | Async resource management, exception handling, null checks |
| Test quality strategy | Mock isolation, assertion effectiveness, coverage gaps |
| Code quality approach | Dead code, duplication, hardcoded values, silent failures |
| CI validation pipeline | Mirror exact CI steps; validate after each category phase |
| Commit strategy | Group by category; clear commit messages with what/why/how |
