# Research: Bug Basher — Full Codebase Review & Fix

**Feature**: `031-bug-basher` | **Date**: 2026-03-08

## Research Tasks & Findings

### R-001: Migration Numbering Conflicts (Still Unresolved)

**Decision**: Flag duplicate migration prefixes (013, 014, 015) as `TODO(bug-bash)` — this remains an architectural decision requiring a deployment reconciliation strategy.

**Rationale**: The migration runner (`database.py:_discover_migrations()`) uses regex `^(\d{3})_.*\.sql$` and sorts by numeric prefix. When two files share the same prefix, the `_run_migrations()` function updates `schema_version` after executing each file, causing the second file at the same version number to be skipped on subsequent runs. A new migration `017_blocking_queue.sql` has been added since the previous bug bash, confirming the numbering continues to diverge.

**Confirmed duplicate pairs** (unchanged from previous review):

| Prefix | File A (applied first alphabetically) | File B (silently skipped) |
|--------|---------------------------------------|---------------------------|
| 013 | `013_agent_config_lifecycle_status.sql` | `013_pipeline_configs.sql` |
| 014 | `014_agent_default_models.sql` | `014_extend_mcp_tools.sql` |
| 015 | `015_agent_icon_name.sql` | `015_pipeline_mcp_presets.sql` |

**Current full migration list** (20 files):
001 → 002 → 003 → 004 → 005 → 006 → 007 → 008 → 009 → 010 → 011 → 012 → 013(×2) → 014(×2) → 015(×2) → 016 → 017

**Alternatives considered**:
- *Renumber the "B" files to 018, 019, 020*: Would require a reconciliation plan for existing deployments. May still conflict with future migrations.
- *Add duplicate-detection logic to migration runner*: More defensive but doesn't fix the data issue for existing deployments.
- *Merge duplicate migration pairs*: Safest long-term but changes SQL files that may have already been partially applied.

**Status**: ⚠️ TODO(bug-bash) — requires deployment reconciliation strategy and human decision on existing database state.

---

### R-002: Signal Chat Error Message Leakage (Existing TODOs)

**Decision**: Verify existing `TODO(bug-bash):` comments are still present and accurate. No additional action needed.

**Rationale**: Three locations in `backend/src/services/signal_chat.py` send raw exception details to users via Signal. These were identified and documented with `TODO(bug-bash):` comments in the previous bug bash (030):

| Line | Context | Current Code |
|------|---------|-------------|
| 175–179 | `#agent` command error | `f"Error processing #agent command: {exc}"` |
| 538–541 | CONFIRM action error | `f"⚠️ Could not complete: {str(e)[:200]}"` |
| 818–824 | Main pipeline error | `f"⚠️ I couldn't process your message...\n\n_{str(e)[:200]}_"` |

The trade-off remains: sanitize to generic messages (like web chat) vs. keep detailed errors (Signal is a private 1:1 channel). This requires a human decision about the privacy model for Signal error messages.

**Status**: ✅ Resolved (previously flagged, verify TODOs still present)

---

### R-003: Temporary File Accumulation in Chat Upload

**Decision**: Fix the temp file leak in `backend/src/api/chat.py` by adding cleanup logic after the file content is read.

**Rationale**: The chat file upload endpoint (`/chat/upload`, lines 900–984) writes files to `/tmp/chat-uploads/` but never removes them. Over time this causes disk space exhaustion. The file contents are read immediately after writing, so the file can be deleted after use. No periodic cleanup task exists.

Key observations:
- Size limit enforced: 10 MB max (line 936)
- Filename sanitized against path traversal (lines 950–956)
- Files written with `file_path.write_bytes(content)` (line 974)
- No deletion or TTL mechanism

**Alternatives considered**:
- *Use `tempfile.NamedTemporaryFile` with auto-delete*: Cleaner but changes control flow more than needed.
- *Add periodic cleanup background task*: More robust long-term but more complex.
- *Delete file after read*: Simplest fix, minimal change, addresses the immediate leak.

**Status**: ✅ Resolved — fix with cleanup after file processing

---

### R-004: CORS Configuration Permissiveness (Existing TODO)

**Decision**: Flag as `TODO(bug-bash):` — restricting CORS methods/headers may break existing API consumers.

**Rationale**: `main.py` (lines 388–401) uses `allow_methods=["*"]` and `allow_headers=["*"]` in CORS middleware. While more restrictive settings are better security practice, changing this could break existing API consumers or preflight requests. The origins list is properly validated via `settings.cors_origins_list`. An existing `TODO(bug-bash)` comment documents this.

**Status**: ⚠️ TODO(bug-bash) — verify existing TODO still present

---

### R-005: Backend Exception Handling Patterns

**Decision**: No bulk action — 159 occurrences of `except Exception` across 47 files in `backend/src/`. This is a codebase-wide pattern, not a bug.

**Rationale**: The spec constraint FR-013 prohibits drive-by refactors. Broad exception handling is an established codebase pattern with proper logging (`logger.exception()` or `logger.error()`) at each site. The top offenders are:
- `github_projects/service.py`: 50 occurrences (wrapping GitHub API calls)
- `workflow_orchestrator/orchestrator.py`: 23 occurrences (wrapping workflow steps)
- `api/chat.py`: 12 occurrences (wrapping chat operations)

Individual cases where exceptions leak to users (like Signal chat) are handled separately under R-002. Narrowing exception types across the entire codebase would be a refactoring effort, not a bug fix.

**Status**: ✅ Resolved — no action (codebase pattern, not a bug)

---

### R-006: Systematic Review Strategy for Python Backend

**Decision**: Follow a priority-based, file-by-file approach organized by risk level.

**Rationale**: The spec defines five priority categories. The review proceeds in priority order within each file, and files are organized by risk:

1. **API endpoints** (`backend/src/api/`, 18 files): Input validation, auth checks, error responses, request handling
2. **Services** (`backend/src/services/`, 49 files): Resource management, state handling, error propagation, business logic
3. **Models** (`backend/src/models/`, 19 files): Type safety, validation rules, serialization correctness
4. **Migrations** (`backend/src/migrations/`, 20 files): SQL correctness, idempotency, naming conflicts
5. **Tests** (`backend/tests/unit/`, 53 files): Mock leaks, assertion quality, coverage gaps

**Status**: ✅ Resolved

---

### R-007: Systematic Review Strategy for React/TypeScript Frontend

**Decision**: Follow the same priority-based approach for frontend code (183 component/hook/page files).

**Rationale**: Frontend bug categories map to:
1. **Security**: XSS risks in rendered content, unsafe HTML via `dangerouslySetInnerHTML`, token handling in localStorage/cookies
2. **Runtime**: Uncaught promise rejections, null access on optional data, missing error boundaries, unhandled loading states
3. **Logic**: Incorrect state management, wrong API endpoint calls, stale closures in hooks, incorrect React Query cache invalidation
4. **Test quality**: Mock configuration, assertion completeness, edge case coverage, React Testing Library best practices
5. **Code quality**: Dead imports, unreachable code, duplicated logic, unused components

**Status**: ✅ Resolved

---

### R-008: Test Infrastructure Assessment

**Decision**: Use existing test infrastructure (pytest + vitest) with existing helpers. No new tools needed.

**Rationale**:
- **Backend**: pytest with `pytest-asyncio` (auto mode), 53 unit test files. Helpers in `tests/helpers/` (factories, mocks, assertions). Shared fixtures in `conftest.py` provide: `mock_session()`, `mock_db()` (in-memory SQLite with migrations), `mock_settings()`, `mock_github_service()`, and full `client()` with httpx.AsyncClient. Run with `python -m pytest tests/unit/ -v --tb=short`.
- **Frontend**: Vitest with React Testing Library and Happy-DOM. Test utilities in `src/test/` (test-utils.tsx with auto-wrapped TooltipProvider, factories). Run with `npx vitest run`.
- Both have sufficient infrastructure to add regression tests without introducing new tools.

**Status**: ✅ Resolved — use existing tools (spec requires no new dependencies)

---

### R-009: Database Connection and Security Patterns

**Decision**: Database connection management is sound — no bugs identified in the connection pattern itself.

**Rationale**: `database.py` uses a module-level singleton `_connection` with proper security:
- WAL mode enabled (`PRAGMA journal_mode=WAL`)
- Busy timeout set to 5000ms (`PRAGMA busy_timeout=5000`)
- Foreign keys enforced (`PRAGMA foreign_keys=ON`)
- Directory permissions: 0700, file permissions: 0600
- Single persistent connection appropriate for SQLite (not suited for connection pooling)

The migration numbering issue (R-001) is separate from the connection pattern.

**Status**: ✅ Resolved — connection pattern is secure and appropriate

---

### R-010: Secrets and Configuration Validation

**Decision**: Secrets handling is properly implemented with production/debug mode separation. No bugs identified.

**Rationale**: `config.py` uses Pydantic BaseSettings with environment variable loading. Key secrets (`SESSION_SECRET_KEY`, `ENCRYPTION_KEY`, `GITHUB_WEBHOOK_SECRET`, `GITHUB_CLIENT_SECRET`) are validated:
- Production mode (`DEBUG=false`): Missing secrets raise validation errors
- Debug mode (`DEBUG=true`): Missing secrets produce warnings
- Session secret enforces minimum 64 characters in production
- Cookie secure flag auto-detected from `FRONTEND_URL` (HTTPS → secure cookies)
- Token encryption at rest via Fernet (cryptography library)
- Log sanitization prevents secrets from appearing in logs

**Status**: ✅ Resolved — secrets handling is appropriate

## Summary of Resolutions

| ID | Issue | Resolution | Status |
|----|-------|------------|--------|
| R-001 | Migration numbering conflicts (013, 014, 015 duplicates) | Flag as TODO — requires deployment reconciliation strategy | ⚠️ Flagged |
| R-002 | Signal error message leakage (3 locations) | Already flagged — verify existing TODOs | ✅ Resolved |
| R-003 | Temp file accumulation in chat upload | Fix with cleanup after file processing | ✅ Resolved |
| R-004 | CORS permissiveness (wildcard methods/headers) | Already flagged — verify existing TODO | ⚠️ Flagged |
| R-005 | Broad exception handling (159 occurrences) | No action — codebase pattern, not a bug | ✅ Resolved |
| R-006 | Python backend review strategy | Priority-based file-by-file audit | ✅ Resolved |
| R-007 | Frontend review strategy | Same priority-based approach | ✅ Resolved |
| R-008 | Test infrastructure capabilities | Use existing pytest + vitest | ✅ Resolved |
| R-009 | Database connection security | Sound pattern — no bugs | ✅ Resolved |
| R-010 | Secrets and configuration | Properly implemented — no bugs | ✅ Resolved |
