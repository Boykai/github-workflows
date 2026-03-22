# Research: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher | **Date**: 2026-03-22

## Research Tasks

### R1: Backend Technology Stack & Best Practices

**Decision**: Use existing `ruff`, `bandit`, `pyright`, and `pytest` toolchain for bug detection and validation.

**Rationale**: The backend already has a mature quality toolchain configured in `pyproject.toml`:
- **ruff** (>=0.15.0) — Linting with rules: E/W/F/I/B/C4/UP/FURB/PTH/PERF/RUF (covers many bug categories automatically)
- **bandit** (>=1.8.0) — Security vulnerability scanning (directly relevant to P1 category)
- **pyright** (>=1.1.408) — Static type checking (catches null refs, type errors from P2 category)
- **pytest** with coverage (>=9.0.0) — Test execution and validation
- **hypothesis** (>=6.131.0) — Property-based testing for edge cases

**Alternatives considered**:
- Adding `mypy` alongside `pyright` — Rejected: `pyright` already configured, adding `mypy` introduces dependency and potential conflicting configs
- Using `semgrep` for security scanning — Rejected: `bandit` already covers Python security; adding tools violates FR-008 (no new dependencies)

---

### R2: Frontend Technology Stack & Best Practices

**Decision**: Use existing `eslint`, TypeScript compiler, and `vitest` toolchain for bug detection and validation.

**Rationale**: The frontend has comprehensive quality tooling in `package.json`:
- **eslint** (^10.0.3) with `react-hooks` and `jsx-a11y` plugins — Catches hook violations, accessibility issues
- **TypeScript** strict mode via `tsc --noEmit` — Catches type errors, null refs
- **vitest** (^4.0.18) with `@testing-library/react` — Test execution
- **@vitest/coverage-v8** — Coverage measurement for test gap identification

**Alternatives considered**:
- Adding `SonarQube` or `CodeClimate` — Rejected: FR-008 prohibits new dependencies
- Using Playwright for regression testing — Rejected: Unit-level vitest tests are more appropriate for bug fix validation; Playwright E2E tests exist but are for integration scenarios

---

### R3: Database Layer Review Strategy

**Decision**: Focus on `aiosqlite` connection handling patterns, PRAGMA usage, and migration integrity.

**Rationale**: The backend uses SQLite via aiosqlite with specific patterns:
- Async connection pooling with persistent connections
- PRAGMA optimizations for performance
- Integrity check before migrations (`PRAGMA integrity_check`)
- Corrupt database detection and rename-to-`.corrupt` recovery
- File permissions restricted to 0600/0700

Key risk areas:
- Connection leaks in error paths (P2: resource leaks)
- SQL injection via string formatting instead of parameterized queries (P1: injection risks)
- Missing transaction boundaries causing data inconsistencies (P3: data inconsistencies)

**Alternatives considered**:
- Migrating to PostgreSQL for better concurrency — Rejected: Architecture change violates constraints
- Adding connection pool monitoring — Rejected: Not a bug fix, would be a new feature

---

### R4: Security Review Strategy

**Decision**: Systematic review of auth, input validation, secrets handling, and middleware security.

**Rationale**: The security attack surface includes:
- **Auth flow**: GitHub OAuth via `github_auth.py`, session management via `session_store.py`
- **Middleware**: CSRF (`csrf.py`), CSP (`csp.py`), rate limiting (`rate_limit.py`), admin guard (`admin_guard.py`)
- **Input validation**: Pydantic models for API inputs, Zod schemas for frontend validation
- **Secrets**: Encryption service (`encryption.py`), config secrets in `config.py`
- **API surface**: 22 API route modules with various auth requirements

Review order (by risk):
1. `config.py` — Secrets and sensitive defaults
2. `middleware/` — Auth bypass vectors
3. `api/auth.py` — Authentication logic
4. `services/github_auth.py` — OAuth implementation
5. `services/encryption.py` — Crypto operations
6. `services/session_store.py` — Session management
7. All `api/*.py` — Input validation on endpoints

**Alternatives considered**:
- Automated DAST scanning — Rejected: Requires running server, out of scope for code review
- Dependency vulnerability audit only — Rejected: `pip-audit` exists but FR-008 says no new deps; `pip-audit` is already a dev dep and can be run

---

### R5: Test Quality Assessment Strategy

**Decision**: Identify mock leaks, dead assertions, and untested paths using coverage data and manual review.

**Rationale**: Known test anti-patterns to check for:
- **Mock leaks**: `MagicMock` objects leaking into production code paths (e.g., database file paths, API URLs). The repository memory explicitly warns about this pattern.
- **Dead assertions**: `assert True`, `assert mock.called` without verifying call args, assertions on mock return values that are always the same
- **Missing coverage**: Run `pytest --cov` and `vitest --coverage` to identify uncovered code paths
- **Wrong mock targets**: Function-level imports need patching at the source module, not the consuming module (confirmed by repository memory)

Key areas:
- `tests/unit/test_main.py` — Lifespan mock settings must include observability fields
- `conftest.py` — Autouse fixtures for cache clearing
- Tests using `MagicMock` for file paths or database connections

**Alternatives considered**:
- Mutation testing to find weak tests — Rejected: Already configured (`mutmut`, `Stryker`) but runs weekly; too slow for a bug bash pass
- Coverage threshold enforcement — Already exists: backend 75%, frontend 50%/44%/41%/50%

---

### R6: Code Quality Patterns

**Decision**: Review for dead code, silent failures, hardcoded values, and duplicated logic using `ruff` rules and manual inspection.

**Rationale**: Key patterns to look for:
- **Dead code**: Unused imports (`F401`), unreachable code after return/raise, unused variables (`F841`)
- **Silent failures**: Bare `except:` or `except Exception:` without logging, empty except blocks
- **Hardcoded values**: Magic numbers, hardcoded URLs, embedded credentials
- **Duplication**: Repeated error handling patterns, duplicated validation logic

`ruff` already covers many of these via configured rules (F/W/E/B/UP), so the manual review focuses on semantic issues that linters cannot detect.

**Alternatives considered**:
- Using `vulture` for dead code detection — Rejected: FR-008 (no new dependencies)
- Automated deduplication tools — Rejected: Structural changes violate constraints

---

### R7: Commit Strategy & Validation Workflow

**Decision**: One commit per logical fix, full test suite validation after each category phase.

**Rationale**: Per FR-004, each commit must explain the bug, why it matters, and the fix. Grouping by category phase provides:
- Clear audit trail per bug category
- Bisectable history for regression tracking
- Validation checkpoint after each phase

Workflow per fix:
1. Identify bug → classify (fix vs. flag)
2. Apply minimal fix
3. Add regression test
4. Run targeted tests (related test file)
5. After batch: run full `pytest` / `vitest`
6. Commit with structured message: `fix(<category>): <what> — <why> — <how>`

**Alternatives considered**:
- One mega-commit per phase — Rejected: Violates FR-004 (clear commit per fix) and makes bisection impossible
- One commit per file — Rejected: Some fixes span multiple files; logical grouping is more meaningful
