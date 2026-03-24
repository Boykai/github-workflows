# Research: Bug Basher — Full Codebase Review & Fix

**Feature**: 002-bug-basher
**Date**: 2026-03-24
**Status**: Complete — all unknowns resolved

## Research Tasks

### R1 — Bug Bash Review Strategy: File-by-File vs. Category-First

**Context**: The spec requires auditing the entire codebase across five categories in priority order. Need to determine the most effective review approach — scan each file once for all categories, or perform category-focused passes.

**Decision**: Category-first passes in priority order (security → runtime → logic → test quality → code quality).

**Rationale**:
- Category-first maintains cognitive focus — reviewing all files for security issues in one pass is more reliable than context-switching between categories per file.
- Priority ordering ensures the highest-risk issues (security) are caught and fixed first, even if later passes are interrupted.
- Each pass produces a self-contained set of fixes with their own regression tests, allowing incremental commits and test suite validation between passes.
- A fix in an earlier pass (e.g., security) may eliminate or change a finding from a later pass (e.g., logic bug), avoiding wasted effort.

**Alternatives Considered**:
1. **File-by-file review**: Rejected — requires mentally switching between security, runtime, logic, test, and code quality concerns for each file, increasing the risk of missed findings.
2. **Automated-only review (tools only)**: Rejected — tools like `bandit` and `ruff` catch known patterns but miss project-specific logic bugs, incorrect state transitions, and test quality issues that require domain understanding.
3. **Hybrid (tools first, then manual)**: Considered — tools should be run first within each category pass to establish a baseline, but manual review is still required. This is effectively what we do within each phase.

---

### R2 — Python Security Auditing: bandit Configuration and Coverage

**Context**: The project uses bandit for security scanning. Need to confirm it covers the critical security patterns for this codebase.

**Decision**: Use existing `bandit` configuration (severity: medium, confidence: medium) as a baseline, supplemented with manual review of auth flows, CSRF handling, and secret management.

**Rationale**:
- bandit detects common Python security patterns (SQL injection via string formatting, hardcoded passwords, weak crypto, shell injection, etc.) but cannot detect application-specific auth logic bugs.
- The FastAPI application uses aiosqlite with parameterized queries (via `?` placeholders), which bandit recognizes as safe. Manual review should verify no string interpolation is used in SQL queries.
- CSRF middleware, admin guard middleware, and session encryption are custom implementations that require manual review — bandit does not understand their semantics.
- The OAuth 2.0 flow in `auth.py` needs manual review for state parameter validation, redirect URI validation, and token storage security.

**Alternatives Considered**:
1. **semgrep**: Rejected — adds a new dependency; bandit plus manual review is sufficient for this codebase size.
2. **Safety (now pip-audit)**: Already configured — `pip-audit` covers dependency vulnerabilities separately from source code scanning.

---

### R3 — Frontend Security Auditing: XSS and Client-Side Risks

**Context**: The React frontend renders user-generated content (chat messages, markdown, agent output). Need to identify XSS vectors.

**Decision**: Manual review of all components that render dynamic content, supplemented by `npm audit` for dependency vulnerabilities.

**Rationale**:
- React's JSX escapes content by default, but explicit `dangerouslySetInnerHTML`, markdown rendering (`react-markdown`), and URL construction (`window.open`, `href` attributes) can introduce XSS if not sanitized.
- The chat interface renders markdown from AI agent output — `react-markdown` with `remark-gfm` should be checked for sanitization of raw HTML blocks.
- URL handling in links (e.g., GitHub repo URLs, webhook URLs) should be validated to prevent `javascript:` protocol injection.
- The frontend uses `eslint-plugin-security` which catches some patterns, but cannot detect all XSS vectors in complex rendering logic.

**Alternatives Considered**:
1. **DOMPurify integration**: Not needed if `react-markdown` is configured securely — it does not render raw HTML by default.
2. **CSP-only defense**: CSP headers (already configured in `csp.py`) provide defense-in-depth but should not be the sole XSS protection.

---

### R4 — Test Quality Audit: Mock Leak Detection Patterns

**Context**: The spec specifically calls out `MagicMock` objects leaking into production paths (e.g., database file paths). Need patterns to detect this.

**Decision**: Grep-based scan for `MagicMock` in test fixtures, followed by manual review of fixtures that construct file paths, database connections, or configuration objects.

**Rationale**:
- Mock leaks occur when a `MagicMock()` object (which stringifies to something like `<MagicMock id=...>`) is used where a real string path is expected, potentially creating files/directories with mock-derived names.
- Common patterns: `db_path = mock_config.database_path` where `mock_config` is a MagicMock without explicit return values for `database_path`.
- Detection: Search for `MagicMock()` (no `spec=`) in conftest.py and fixture definitions, then trace usage into production code paths that expect concrete values (file paths, URLs, config strings).
- The project uses `tmp_path` fixtures for file-based tests, which is the correct pattern — mocks should not be used for file paths.

**Alternatives Considered**:
1. **pytest-mock strict mode**: Rejected — would require significant refactoring and adds a new dev dependency.
2. **Custom conftest assertion**: Rejected — overly complex for a one-time audit; grep-based detection is sufficient.

---

### R5 — Runtime Error Patterns: aiosqlite and Resource Management

**Context**: The backend uses aiosqlite for database access. Need to identify common resource leak patterns in async SQLite usage.

**Decision**: Review all database session usage for proper `async with` context manager patterns, check for connection pool exhaustion scenarios, and verify WAL mode checkpoint handling.

**Rationale**:
- aiosqlite connections must be properly closed to avoid file handle leaks. The project uses a centralized `database.py` service — verify all callers use context managers or the service's lifecycle methods.
- WAL mode requires periodic checkpoints; verify the application handles checkpoint errors gracefully.
- Concurrent access patterns (multiple WebSocket handlers writing simultaneously) need review for potential database locking issues.
- File handle leaks can also occur in template file reading (`template_files.py`), log file handling, and temporary file operations.

**Alternatives Considered**:
1. **Connection pooling library**: N/A — aiosqlite is inherently single-connection; the project manages this via its database service.
2. **SQLAlchemy async**: Rejected as out of scope — the project uses raw aiosqlite by design.

---

### R6 — Regression Test Strategy: One Test Per Bug

**Context**: The spec requires at least one regression test per bug fix. Need a strategy for organizing these tests.

**Decision**: Add regression tests alongside existing test files for the modified module. Use descriptive test names with `test_regression_` prefix where the fix is not obvious from context.

**Rationale**:
- Placing regression tests in the existing test file for the modified module keeps tests discoverable and co-located with related tests.
- The project already has a `test_regression_bugfixes.py` file for general regression tests — additional regressions can be added there or in module-specific test files depending on context.
- Test names should describe the bug scenario, not the fix implementation (e.g., `test_webhook_rejects_empty_signature` not `test_fix_issue_42`).
- For security fixes, regression tests should verify both the fix (valid input works) and the exploit prevention (malicious input is rejected).

**Alternatives Considered**:
1. **Separate `tests/regression/` directory**: Rejected — fragments tests away from their related modules, making maintenance harder.
2. **All regressions in `test_regression_bugfixes.py`**: Rejected for module-specific bugs — the existing file covers cross-cutting regressions, not module-specific behavior.

---

### R7 — Commit Strategy: Per-Bug vs. Per-Phase Commits

**Context**: FR-004 requires clear commit messages explaining each bug. Need to determine commit granularity.

**Decision**: Per-phase commits with detailed commit messages listing all bugs found and fixed in that phase.

**Rationale**:
- Per-bug commits would create excessive commit history for a review task (potentially dozens of commits).
- Per-phase commits (security, runtime, logic, test quality, code quality) provide logical grouping while still allowing clear commit messages.
- Each commit message lists the bugs fixed in that phase with file locations, matching the summary report format.
- The summary report (Phase 5) provides the complete per-bug detail across all phases.

**Alternatives Considered**:
1. **Per-bug commits**: Rejected — too many small commits for a review task; makes history noisy.
2. **Single commit**: Rejected — loses traceability of which phase fixed which bugs.

---

### R8 — Linting and Formatting Tool Verification

**Context**: FR-007 requires existing linting/formatting checks to pass. Need to confirm the available tools and their configurations.

**Decision**: Run `ruff check` + `ruff format --check` + `pyright` + `bandit` (backend) and `npm run lint` + `npm run type-check` (frontend) after each phase.

**Rationale**:
- Backend linting: `ruff` handles both linting (E, W, F, I, B, C4, UP, FURB, PTH, PERF, RUF rules) and formatting (line length 100, Python 3.13 target). `pyright` provides type checking in standard mode.
- Backend security: `bandit` (severity: medium, confidence: medium) and `pip-audit` for dependency vulnerabilities.
- Frontend linting: ESLint with TypeScript, React Hooks, jsx-a11y, and security plugins. TypeScript compiler for type checking.
- All tools are already configured in `pyproject.toml` (backend) and `eslint.config.js` / `tsconfig.json` (frontend).
- Running after each phase catches issues early before they compound.

**Alternatives Considered**:
1. **Run tools only at the end**: Rejected — compounds errors and makes debugging harder.
2. **Add new tools (e.g., mypy)**: Rejected per FR-009 — no new dependencies.
