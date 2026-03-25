# Research: Bug Basher

**Feature**: 001-bug-basher | **Date**: 2026-03-24 | **Status**: Complete

## Research Tasks

### R1: Bug Categorization and Priority Order

**Decision**: Audit in five priority-ordered categories as specified: (1) Security vulnerabilities, (2) Runtime errors, (3) Logic bugs, (4) Test gaps & quality, (5) Code quality issues.

**Rationale**: Priority order matches risk impact — security issues have the highest potential for damage (data breaches, unauthorized access), followed by runtime stability, correctness, test reliability, and finally maintainability. This ordering ensures the most critical issues are resolved first.

**Alternatives Considered**:
- Alphabetical file-by-file scan: Rejected because it doesn't prioritize high-risk findings.
- Category-by-category across the entire codebase: Selected — processes all files for one category before moving to the next, ensuring priority ordering is honored.

### R2: Existing Tooling and Validation Infrastructure

**Decision**: Leverage the existing validation toolchain without adding new tools.

**Rationale**: The codebase already has comprehensive tooling:
- **Backend linting**: Ruff (rules: E, W, F, I, B, C4, UP, FURB, PTH, PERF, RUF), line length 100
- **Backend type checking**: Pyright (standard mode, Python 3.13)
- **Backend security scanning**: Bandit (severity: medium, confidence: medium, skips B104, B608)
- **Backend testing**: pytest 9+ with pytest-asyncio (auto mode), pytest-cov (75% minimum)
- **Frontend linting**: ESLint with TypeScript, React Hooks, JSX A11y, Security plugins
- **Frontend testing**: Vitest 4+ with happy-dom, @testing-library/react
- **Frontend coverage**: 50% statements, 44% branches, 41% functions, 50% lines
- **Dependency auditing**: pip-audit (backend), npm audit (frontend)
- **Docker security**: Trivy scanning (HIGH/CRITICAL)

**Alternatives Considered**:
- Adding SonarQube: Rejected per FR-009 (no new dependencies).
- Adding semgrep: Rejected per FR-009.

### R3: Backend Security Patterns

**Decision**: Focus security review on authentication flows, session management, middleware stack, encryption-at-rest, input validation, and secret handling.

**Rationale**: The backend has a well-defined security surface:
- **Authentication**: GitHub OAuth with `GitHubAuthService`, session-based auth with configurable TTL (8 hours default)
- **Session management**: SQLite-backed sessions, encrypted tokens via Fernet (`ENCRYPTION_KEY`)
- **CSRF**: Double-submit cookie pattern with `X-CSRF-Token` header validation
- **Rate limiting**: Per-user via `slowapi`, key resolution: `github_user_id` > session cookie > IP
- **CSP**: Strict Content Security Policy with security headers (HSTS, X-Frame-Options, etc.)
- **Admin guard**: Path-based access control with `@admin` and `@adminlock` protection levels
- **Input validation**: Pydantic models with validators
- **Webhook verification**: GitHub webhook secret validation

**Key Areas to Audit**:
1. Auth bypass possibilities in dependency injection (`dependencies.py`)
2. Session fixation or token leakage
3. CSRF token validation edge cases
4. Admin elevation paths in debug mode
5. Secrets exposure in logging or error responses
6. SQL injection via raw queries (even with parameterized SQLite)
7. Path traversal in file operations

**Alternatives Considered**: N/A — security patterns are dictated by existing architecture.

### R4: Frontend Security Patterns

**Decision**: Focus frontend security review on XSS prevention, unsafe rendering, API token handling, and accessibility compliance.

**Rationale**: The frontend uses:
- React (auto-escapes JSX by default)
- React Markdown with GFM (potential XSS vector via `dangerouslySetInnerHTML` or unescaped HTML)
- API service layer for backend communication
- ESLint security plugin (already configured)

**Key Areas to Audit**:
1. `dangerouslySetInnerHTML` usage
2. URL construction and redirect handling
3. localStorage/sessionStorage of sensitive data
4. XSS via markdown rendering
5. CSRF token propagation in API calls

**Alternatives Considered**: N/A — patterns dictated by existing architecture.

### R5: Test Infrastructure and Regression Test Patterns

**Decision**: Regression tests follow existing patterns — pytest fixtures for backend, Vitest with @testing-library for frontend.

**Rationale**: The codebase has established test infrastructure:
- **Backend fixtures**: `mock_session()`, `mock_db()`, `mock_settings()`, `mock_github_service()`, `mock_ai_agent_service()`, `client()` (httpx.AsyncClient)
- **Auto-use fixture**: `_clear_test_caches()` — clears global caches between tests
- **Factory helpers**: `make_mock_github_service()`, `make_mock_db_connection()`, etc.
- **Test environment**: `TESTING=1` disables CSRF and rate limiting; `DATABASE_PATH=:memory:` for isolation
- **Frontend setup**: `src/test/setup.ts` with globals enabled

**Regression Test Strategy**:
- Each bug fix gets ≥1 regression test that would have caught the bug
- Tests use existing fixtures and helpers — no new test infrastructure
- Tests are placed in the same test file as existing tests for the module, or a new file if none exists
- Test names follow pattern: `test_<module>_<bug_description>`

**Alternatives Considered**:
- Separate `tests/regression/` directory: Rejected — co-locating tests with existing module tests is the codebase convention.

### R6: Ambiguity Handling and TODO Pattern

**Decision**: Use `# TODO(bug-bash):` comment format for ambiguous issues, with structured description including issue, options, and rationale.

**Rationale**: The codebase already uses structured TODO comments (e.g., `NOTE(001-code-quality-tech-debt)`, `TODO(018-codebase-audit-refactor)`). The `TODO(bug-bash)` prefix maintains consistency while being searchable and distinct.

**Format**:
```python
# TODO(bug-bash): <Brief description>
# Options: (1) <option A>, (2) <option B>
# Rationale: <why this needs human decision>
```

**Alternatives Considered**:
- GitHub Issues for each ambiguity: Rejected — spec requires inline comments.
- FIXME prefix: Rejected — codebase convention uses TODO with identifier.

### R7: Validation and CI Compliance

**Decision**: After all fixes, validate with the full CI pipeline checklist.

**Rationale**: The CI pipeline defines the acceptance criteria for code quality.

**Backend Validation Commands**:
```bash
cd solune/backend
pip install -e ".[dev]"
ruff check src/ tests/
ruff format --check src/ tests/
pyright src/
pytest -q --tb=short
```

**Frontend Validation Commands**:
```bash
cd solune/frontend
npm ci
npm run lint
npm run type-check
npm run test
npm run build
```

**Alternatives Considered**: N/A — validation commands are defined by CI.

### R8: Scope Boundaries

**Decision**: Audit scope covers `solune/backend/src/`, `solune/backend/tests/`, `solune/frontend/src/`, and configuration files. Excluded: auto-generated files, vendored code, `.specify/` workflow files, `.github/` workflow files, `node_modules/`, `__pycache__/`, build artifacts.

**Rationale**: The spec states "audit every file in the repository" but also "auto-generated files and vendored third-party code are excluded." The `.specify/` and `.github/` directories are infrastructure, not application code. The `apps/` directory contains only a `.gitkeep` file.

**Alternatives Considered**:
- Include `.github/workflows/` in audit: Rejected — spec constraint says "do not change the project's architecture," and workflows are infrastructure.
- Include `solune/docs/`: Included for documentation accuracy but code fixes are limited to source files.

## Summary of Decisions

| # | Topic | Decision |
|---|-------|----------|
| R1 | Priority order | 5-tier priority: Security > Runtime > Logic > Tests > Code Quality |
| R2 | Tooling | Use existing tools only (ruff, pyright, bandit, eslint, vitest, pytest) |
| R3 | Backend security | Focus on auth, sessions, CSRF, admin elevation, secrets, SQL, paths |
| R4 | Frontend security | Focus on XSS, markdown rendering, token handling, redirects |
| R5 | Test patterns | Co-locate regression tests with existing module tests using existing fixtures |
| R6 | TODO format | `# TODO(bug-bash):` with issue, options, rationale |
| R7 | Validation | Full CI pipeline commands for backend and frontend |
| R8 | Scope | `solune/backend/src/`, `solune/backend/tests/`, `solune/frontend/src/`, configs |
