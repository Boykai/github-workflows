# Research: Bug Basher — Full Codebase Review & Fix

**Feature**: `030-bug-basher` | **Date**: 2026-03-08

## Research Tasks & Findings

### R-001: Migration Numbering Conflicts

**Decision**: Flag duplicate migration prefixes (013, 014, 015) as `TODO(bug-bash)` until a deployment reconciliation strategy is defined.

**Rationale**: The migration runner (`database.py:_discover_migrations()`) uses regex `^(\d{3})_.*\.sql$` to parse migration files and sorts by the numeric prefix. When two files share the same prefix (e.g., `015_agent_icon_name.sql` and `015_pipeline_mcp_presets.sql`), both are discovered and appended to the list, but since the `_run_migrations()` function updates `schema_version` to the version number after executing each file, the second file with the same version number will be skipped on subsequent runs (version is already >= that number). This means only the first alphabetically-sorted file at each duplicate version is reliably applied.

**Confirmed duplicate pairs**:

| Prefix | File A (applied) | File B (silently skipped) |
|--------|-------------------|---------------------------|
| 013 | `013_agent_config_lifecycle_status.sql` | `013_pipeline_configs.sql` |
| 014 | `014_agent_default_models.sql` | `014_extend_mcp_tools.sql` |
| 015 | `015_agent_icon_name.sql` | `015_pipeline_mcp_presets.sql` |

**Alternatives considered**:
- *Renumber the "B" files to 016, 017, 018*: Would conflict with existing `016_chores_enhancements.sql`. Requires cascading renumber.
- *Add duplicate-detection logic to migration runner*: More defensive, but doesn't fix the data issue for existing deployments.
- *Renumber immediately*: Unsafe for existing deployments without a reconciliation plan.

**Recommended approach**: This is a **TODO(bug-bash)** candidate because renumbering migrations changes the applied-version tracking for all existing database deployments. Existing databases that have already applied some migrations under the old numbering would see version mismatches. A safe fix requires a migration reconciliation strategy that accounts for existing deployments. This is an architectural decision, not a simple bug fix.

---

### R-002: Signal Chat Error Message Leakage

**Decision**: Already flagged as `TODO(bug-bash):` — no additional action needed.

**Rationale**: Three locations in `backend/src/services/signal_chat.py` send raw exception details to users via Signal. This was already identified and documented with `TODO(bug-bash):` comments describing the trade-off: sanitize to generic messages (like web chat) vs. keep detailed errors (Signal is a private 1:1 channel). This requires a human decision about the privacy model for Signal error messages.

**Alternatives considered**: N/A — already properly flagged.

---

### R-003: Temporary File Accumulation in Chat Upload

**Decision**: Fix the temp file leak in `backend/src/api/chat.py` by adding cleanup logic.

**Rationale**: The chat file upload endpoint writes files to `{tempdir}/chat-uploads/` but never removes them. Over time, this causes disk space exhaustion. The fix should add cleanup after the file is processed (the file contents are read immediately after writing, so the file can be deleted after use).

**Alternatives considered**:
- *Use `tempfile.NamedTemporaryFile` with auto-delete*: Cleaner, but changes the control flow.
- *Add a periodic cleanup task*: More robust long-term, but more complex. Can be combined with the immediate fix.
- *Just delete after read*: Simplest fix, minimal change.

---

### R-004: CORS Configuration Permissiveness

**Decision**: Flag as `TODO(bug-bash):` — restricting CORS methods/headers may break existing integrations.

**Rationale**: `main.py` uses `allow_methods=["*"]` and `allow_headers=["*"]` in CORS middleware. While more restrictive settings would be better security practice, changing this could break existing API consumers. The current configuration is functional and the origins list is properly validated. This is a hardening recommendation, not a bug.

**Alternatives considered**:
- *Restrict to specific methods*: Could break preflight requests for custom headers used by the frontend.
- *Keep as-is*: Acceptable since origins are validated.

---

### R-005: Backend Exception Handling Patterns

**Decision**: No action — broad `except Exception` is acceptable given the logging patterns.

**Rationale**: ~89 occurrences of `except Exception` across backend code. All include proper logging (`logger.exception()` or `logger.error()`). While more specific exception types would be ideal, changing all of these is a refactoring effort, not a bug fix. The spec constraint (FR-013) prohibits drive-by refactors.

**Alternatives considered**:
- *Narrow exception types*: Would be a refactor, not a bug fix. Out of scope.
- *Flag each one*: Too many to flag individually; this is a codebase pattern, not a bug.

---

### R-006: Best Practices for Python Bug Bash Reviews

**Decision**: Follow a systematic file-by-file approach, prioritized by bug category.

**Rationale**: The spec defines five priority categories. The review should proceed in priority order within each file, and files should be organized by risk level (API endpoints and services first, then models, then utilities). Key areas to focus:
1. **API endpoints** (`backend/src/api/`): Input validation, auth checks, error responses
2. **Services** (`backend/src/services/`): Resource management, state handling, error propagation
3. **Models** (`backend/src/models/`): Type safety, validation rules, serialization
4. **Migrations** (`backend/src/migrations/`): SQL correctness, idempotency, naming
5. **Tests** (`backend/tests/`): Mock leaks, assertion quality, coverage gaps

---

### R-007: Best Practices for React/TypeScript Bug Bash Reviews

**Decision**: Follow the same priority-based approach for frontend code.

**Rationale**: Frontend bug categories map to:
1. **Security**: XSS risks in rendered content, unsafe HTML, token handling
2. **Runtime**: Uncaught promise rejections, null access on optional data, missing error boundaries
3. **Logic**: Incorrect state management, wrong API endpoint calls, stale closures
4. **Test quality**: Mock configuration, assertion completeness, edge case coverage
5. **Code quality**: Dead imports, unreachable code, duplicated logic

---

### R-008: Test Infrastructure Capabilities

**Decision**: Use existing test infrastructure (pytest + vitest) with existing helpers.

**Rationale**: 
- **Backend**: pytest with `pytest-asyncio` (auto mode), test helpers in `tests/helpers/` (factories, mocks, assertions), conftest.py with shared fixtures. Run with `python -m pytest tests/unit/ -v`.
- **Frontend**: Vitest with React Testing Library and Happy-DOM. Test utilities in `src/test/` (test-utils.tsx, factories). Run with `npx vitest run`.
- Both have sufficient infrastructure to add regression tests without introducing new tools.

**Alternatives considered**: N/A — using existing tools is required by the spec (no new dependencies).

## Summary of Resolutions

| ID | Issue | Resolution | Status |
|----|-------|------------|--------|
| R-001 | Migration numbering conflicts | Flag as TODO — requires deployment strategy | ⚠️ Flagged |
| R-002 | Signal error leakage | Already flagged — no action needed | ✅ Resolved |
| R-003 | Temp file accumulation | Fix with cleanup after file processing | ✅ Resolved |
| R-004 | CORS permissiveness | Flag as TODO — may break integrations | ⚠️ Flagged |
| R-005 | Broad exception handling | No action — codebase pattern, not a bug | ✅ Resolved |
| R-006 | Python review approach | Systematic priority-based file audit | ✅ Resolved |
| R-007 | TypeScript review approach | Same priority-based approach for frontend | ✅ Resolved |
| R-008 | Test infrastructure | Use existing pytest + vitest | ✅ Resolved |
