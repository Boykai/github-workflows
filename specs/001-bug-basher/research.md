# Research: Bug Basher — Full Codebase Review & Fix

**Feature**: `001-bug-basher` | **Date**: 2026-03-15 | **Plan**: [plan.md](plan.md)

## Research Tasks

### RT-001: Bug Bash Best Practices for Python/FastAPI + React/TypeScript Monorepos

**Decision**: Adopt a priority-ordered, file-by-file sweep approach where each file is audited against all five categories before moving to the next. Fixes are applied in priority order (security first) across the entire codebase, with a single validation pass at the end.

**Rationale**: A category-first approach (audit all files for security, then all for runtime, etc.) risks context-switching overhead and missing cross-category bugs within the same file. A file-by-file sweep is more efficient and reduces the chance of overlooking related bugs. However, triage and fix ordering still respects priority: security fixes are committed before runtime fixes, etc.

**Alternatives considered**:
- Category-first sweep (audit all files for security, then start over for runtime): rejected due to high context-switching cost and repeated file reads.
- Random/opportunistic approach: rejected because it doesn't guarantee priority ordering required by SC-009.

---

### RT-002: Python Security Vulnerability Patterns in FastAPI Applications

**Decision**: Focus security audit on the following FastAPI-specific patterns:
1. **Input validation**: Ensure all API endpoints validate inputs via Pydantic models (not raw dicts/strings). Check path parameters, query parameters, and request bodies.
2. **SQL injection**: Verify all SQLite queries use parameterized statements (not string interpolation/f-strings). Check `aiosqlite` usage throughout `database.py`, `chat_store.py`, `settings_store.py`, `session_store.py`, `mcp_store.py`, `pipeline_state_store.py`.
3. **Secrets exposure**: Scan for hardcoded API keys, tokens, passwords, or encryption keys in source code and configuration files. Check `config.py`, `docker-compose.yml`, `.env` files, and any committed secrets.
4. **Auth bypasses**: Review `github_auth.py`, `admin_guard.py` middleware, and `guard_service.py` for missing or bypassable authentication checks.
5. **Path traversal**: Check `app_service.py` (already uses `_safe_app_path` — verify correctness), file upload handling, and any file system operations.
6. **CORS misconfiguration**: Review CORS settings in `main.py` for overly permissive origins.
7. **CSP headers**: Review `csp.py` middleware for completeness.
8. **Rate limiting**: Review `rate_limit.py` middleware coverage.
9. **Encryption**: Review `encryption.py` for proper key management and algorithm choices.

**Rationale**: These are the OWASP Top 10 patterns most relevant to the FastAPI + SQLite stack used in this project. The codebase handles GitHub OAuth, encryption keys, and file system operations — all high-risk areas.

**Alternatives considered**:
- Generic SAST tool scan only: rejected because automated tools miss logic-level auth bypasses and context-specific issues.
- Full OWASP checklist: rejected as many items (e.g., SSRF, XXE) are less relevant to this stack.

---

### RT-003: Python Runtime Error Patterns

**Decision**: Focus runtime error audit on:
1. **Unhandled exceptions**: Check `try/except` coverage in API routes, service methods, and async handlers. Look for bare `except:` clauses that swallow errors.
2. **Null/None references**: Check for missing `Optional` annotations and unguarded attribute access on potentially-None values.
3. **Resource leaks**: Verify all `aiosqlite` connections are properly closed (context managers). Check file handles in `attachment_formatter.py` and `app_service.py`.
4. **Import errors**: Verify all imports resolve correctly. Check for circular imports in the service layer.
5. **Type errors**: Cross-reference Pydantic model fields with SQLite schema columns. Check the known `accepted` vs `confirmed` status mapping in `chat_recommendations`.
6. **Async race conditions**: Review `websocket.py`, `signal_bridge.py`, and `copilot_polling/` for shared mutable state without proper synchronization.
7. **Timestamp parsing**: Verify `fromisoformat()` calls handle the trailing `Z` in SQLite RFC3339 timestamps (known issue: Python's `fromisoformat` can't parse `Z` directly before 3.11+).

**Rationale**: These are the most common runtime failure modes in async Python web applications. The codebase uses `aiosqlite` (async DB), WebSockets, and background polling — all areas prone to resource leaks and race conditions.

**Alternatives considered**:
- Static-analysis-only approach: rejected because many runtime errors (race conditions, resource leaks) require understanding execution flow, not just syntax.

---

### RT-004: React/TypeScript Frontend Bug Patterns

**Decision**: Focus frontend audit on:
1. **Type safety**: Check for `any` type usage that bypasses TypeScript's type system. Verify API response types match backend models.
2. **XSS risks**: Check `dangerouslySetInnerHTML` usage. Verify `react-markdown` is configured safely.
3. **Missing error handling**: Check API service calls for missing `catch` handlers. Verify React Query error states are handled in UI.
4. **Memory leaks**: Check `useEffect` cleanup functions. Verify WebSocket connections are properly closed on unmount.
5. **Stale closures**: Check `useCallback`/`useMemo` dependency arrays for missing dependencies.
6. **Accessibility**: Verify interactive elements have proper ARIA attributes (leveraging existing `jsx-a11y` ESLint plugin).

**Rationale**: These are the highest-impact frontend bug categories for a React 19 + TypeScript application with API integrations and WebSocket connections.

**Alternatives considered**:
- Full accessibility audit: rejected as out-of-scope for a bug bash (the project already has `jsx-a11y` and dedicated accessibility test scripts).

---

### RT-005: Test Quality Patterns and Anti-Patterns

**Decision**: Focus test quality audit on:
1. **Mock leaks**: Check for `MagicMock` objects that could leak into production code paths (e.g., mock returning a `MagicMock` used as a file path, URL, or database value).
2. **Vacuous assertions**: Check for `assert True`, `assert mock.called` without verifying call arguments, or assertions that always pass regardless of the code under test.
3. **Missing async test markers**: Verify all async test functions use proper `pytest-asyncio` markers.
4. **Fixture scope issues**: Check for test fixtures with inappropriate scope (e.g., `session`-scoped database fixtures that leak state between tests).
5. **Missing edge case coverage**: Identify code paths (error handlers, boundary conditions, empty inputs) that have no test coverage.

**Rationale**: The spec explicitly calls out mock leaks as a priority concern. The backend uses extensive mocking for GitHub API calls, AI providers, and database operations — all areas where mock leaks are common.

**Alternatives considered**:
- Code coverage metrics only: rejected because high coverage doesn't guarantee test quality (a test can cover a line without meaningfully asserting its behavior).

---

### RT-006: Existing Linting and CI Configuration

**Decision**: Rely on existing linting infrastructure for validation:
- **Backend**: `ruff check src tests` (linting), `ruff format --check src tests` (formatting), `pyright src` (type checking), `pytest --cov=src` (tests + coverage)
- **Frontend**: `npm run lint` (ESLint), `npm run type-check` (TypeScript), `npm test` (Vitest), `npm run build` (build verification)
- **CI**: GitHub Actions `ci.yml` runs all checks on PR

**Rationale**: The project already has comprehensive linting and CI. No new tools are needed (FR-011 prohibits new dependencies). All fixes must pass existing checks.

**Alternatives considered**:
- Adding `bandit` for Python security scanning: rejected per FR-011 (no new dependencies).
- Adding `semgrep` for pattern-based scanning: rejected per FR-011.

---

### RT-007: Commit Strategy and Summary Table Format

**Decision**: Use atomic commits per bug fix. Each commit message follows the format: `fix(<category>): <short description>`. The summary table uses the markdown format specified in the feature spec, with columns: #, File, Line(s), Category, Description, Status.

**Rationale**: Atomic commits make it easy to revert individual fixes if they cause issues. The category prefix in commit messages enables filtering. The summary table format is mandated by the spec.

**Alternatives considered**:
- Single large commit: rejected because it makes individual fix review and revert impossible.
- Category-grouped commits: rejected because a single file may have fixes in multiple categories, making grouping awkward.

---

### RT-008: Database Status Mapping (accepted vs confirmed)

**Decision**: The known discrepancy between SQLite `chat_recommendations.status` values (`pending/accepted/rejected`) and the `RecommendationStatus` enum (`pending/confirmed/rejected`) is a documented design choice, not a bug. The mapping occurs in `chat_store.py` and is intentional. This should be verified during the logic bug audit but is expected to be correct.

**Rationale**: Repository memories confirm this is a known mapping. Changing it would alter the public API surface (FR-010 violation).

**Alternatives considered**:
- Aligning DB values with enum values: rejected per FR-010 (would change the DB schema, which is part of the internal API surface).

---

### RT-009: Timestamp Parsing Safety

**Decision**: Verify all `datetime.fromisoformat()` calls handle the trailing `Z` used in SQLite timestamps. Python 3.11+ handles `Z` natively, and the project targets Python 3.13, so `fromisoformat('...Z')` should work. However, if any code manually strips/replaces `Z`, that code should be checked for correctness.

**Rationale**: Repository memories flag this as a known concern. While Python 3.13 handles `Z`, older workaround code may still exist and could introduce bugs if the workaround itself has issues.

**Alternatives considered**:
- Using `dateutil.parser.parse()`: rejected per FR-011 (no new dependencies).

## Resolution Summary

All research tasks are resolved. No NEEDS CLARIFICATION items remain. The technical context is complete and the audit can proceed through the five priority categories using the patterns and tools identified above.
