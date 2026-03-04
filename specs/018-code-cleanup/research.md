# Research: Codebase Cleanup — Reduce Technical Debt

**Feature**: 018-code-cleanup | **Date**: 2026-03-04

## Research Summary

This document consolidates all research findings needed to resolve unknowns in the Technical Context and inform the implementation plan. The codebase was analyzed for each of the five cleanup categories.

---

## Category 1: Backwards-Compatibility Shims

### Decision: Minimal shims found — one legacy token fallback

**Rationale**: The codebase is relatively young and well-maintained. The only backwards-compatibility pattern identified is in the encryption service, which gracefully handles pre-encryption plaintext tokens.

**Findings**:

1. **Legacy plaintext token fallback** (`backend/src/services/encryption.py`)
   - `EncryptionService.decrypt()` detects tokens with `gho_` prefix and returns them as-is instead of attempting Fernet decryption
   - This handles tokens stored before encryption-at-rest was enabled
   - **Action**: RETAIN — this is an active migration-period safety net. Users may still have pre-encryption sessions. Document for future removal once all sessions have rotated.
   - Tested in `backend/tests/unit/test_token_encryption.py::test_legacy_plaintext_fallback_on_decrypt`

2. **No `if legacy:` / `if old_format:` patterns found** — searched all Python and TypeScript files

3. **Migration 010 (`010_chores.sql`)** drops old `housekeeping_*` tables
   - This is a completed migration (housekeeping → chores rename)
   - The migration file itself is not a shim — it's a one-time cleanup
   - **Action**: RETAIN — migration files are executed sequentially and must not be deleted

**Alternatives Considered**: Removing the legacy token fallback was evaluated but rejected because active user sessions may still contain pre-encryption tokens. Removal should happen after a forced session rotation.

---

## Category 2: Dead Code Paths

### Decision: Focus on unused dependencies and targeted code analysis

**Rationale**: The codebase already benefits from ruff linting (unused imports, variables) and pyright type checking. The primary dead code targets are unused package dependencies.

**Findings**:

### Backend — Unused Dependencies

| Dependency | Status | Evidence |
|------------|--------|----------|
| `python-jose[cryptography]` | ❌ UNUSED | Zero imports of `jose` anywhere in `src/` or `tests/`. Auth uses FastAPI sessions + custom encryption, not JWT. |
| `agent-framework-core` | ❌ UNUSED | Referenced only in code comments describing architecture. Zero `from agent_framework` imports. |

### Backend — Dynamically Loaded Code (DO NOT REMOVE)

| Module | Dynamic Loading Mechanism |
|--------|--------------------------|
| `github-copilot-sdk` | Lazy `from copilot import CopilotClient` inside `CopilotCompletionProvider._get_client()`. Import happens at runtime only when copilot provider is selected. |
| All migration files (`001–010`) | Loaded by `database.py` migration runner via file discovery. Cannot be removed. |
| `completion_providers.py` providers | Provider classes selected at runtime via `AI_PROVIDER` setting string. All provider classes are reachable. |

### Frontend — Unused Dependencies

| Dependency | Status | Evidence |
|------------|--------|----------|
| `socket.io-client` | ❌ UNUSED | Frontend uses native `WebSocket` API in `useRealTimeSync.ts`. No Socket.IO imports anywhere. |
| `jsdom` (devDep) | ❌ UNUSED | vitest.config.ts uses `happy-dom` as test environment. `jsdom` is never referenced. |

### Frontend — All Other Dependencies Verified Used

- `tailwindcss-animate`: Used as plugin in `tailwind.config.js` line 78
- `@dnd-kit/*`: Used in `AgentColumnCell.tsx` and board drag-and-drop
- `@radix-ui/react-slot`, `class-variance-authority`, `clsx`, `tailwind-merge`: Used in UI component library (`button.tsx`, `utils.ts`)

### Code-Level Dead Code

- **No unused functions/components detected** — all exports are imported by at least one consumer
- **No commented-out code blocks** — search for 3+ consecutive comment lines yielded only documentation comments
- **No unused route handlers** — all API endpoints have corresponding frontend consumers or test coverage

**Alternatives Considered**: Running a full dead-code analysis tool (e.g., vulture for Python, ts-prune for TypeScript) was considered but deemed unnecessary given the small codebase size and existing linter coverage.

---

## Category 3: Duplicated Logic

### Decision: Consolidate test fixtures; service duplication is acceptable

**Rationale**: The main duplication is in test setup code, not production logic. Service methods follow similar CRUD patterns but are domain-specific, making consolidation counterproductive.

**Findings**:

### Test Fixture Duplication (HIGH PRIORITY)

1. **`mock_provider()` fixture** — defined 7 times across different test classes in `test_ai_agent.py`
   - Creates the same mock completion provider with identical setup
   - **Action**: Extract to `tests/helpers/mocks.py` as `make_mock_provider()`

2. **`mock_ai_service()` fixture** — defined 4 times in `test_workflow_orchestrator.py`
   - Creates identical `AsyncMock` of `AIAgentService`
   - **Action**: Extract to `tests/helpers/mocks.py` as `make_mock_ai_service()`

3. **`mock_github_service()` fixture** — defined 6 times across multiple test files
   - Creates identical `AsyncMock` of `GitHubProjectsService`
   - **Action**: Consolidate into existing `tests/helpers/mocks.py`

### Service Logic (LOW PRIORITY — RETAIN)

- Backend services (`chores/service.py`, `agents/service.py`, `github_projects/service.py`) share CRUD-like patterns
- These are domain-specific with different validation, error handling, and business rules
- **Action**: RETAIN as-is — forced abstraction would violate Constitution Principle V (Simplicity: "Duplication is preferable to wrong abstraction")

### Frontend (NO DUPLICATION)

- No duplicate utility functions, hooks, or components detected
- Each hook has a unique purpose; no overlapping functionality

**Alternatives Considered**: Creating a base CRUD service class was evaluated but rejected — the methods share structural similarity but not behavioral similarity, making a base class a leaky abstraction.

---

## Category 4: Stale / Irrelevant Tests

### Decision: No stale tests found — test suite is current

**Rationale**: All test files were cross-referenced against production source modules. Every tested module still exists and the tests exercise current behavior.

**Findings**:

- **No tests for deleted functionality** — all tested modules exist in `src/`
- **No orphaned test artifacts** — no `.db`, `.sqlite`, or `MagicMock` files in workspace root or `backend/` root
- **Heavily-mocked tests**: Several test files use extensive mocking (`test_api_chat.py`, `test_workflow_orchestrator.py`, `test_copilot_polling.py`) but they test real behavior through mock boundaries — mock setups verify correct argument passing, state transitions, and error handling. These are legitimate unit tests, not over-mocked tests.
- **Signal feature has zero test coverage** — This is a gap (the feature is implemented in 4+ source files, 2 migrations, and Docker Compose) but is NOT a stale test issue. Creating tests is out of scope for this cleanup feature.

**Alternatives Considered**: Removing the legacy token decryption test (`test_legacy_plaintext_fallback_on_decrypt`) was considered since it tests a compatibility shim, but the shim is being retained (see Category 1), so the test is valid.

---

## Category 5: General Hygiene

### Decision: Remove unused dependencies and evaluate TODO comments

**Rationale**: The codebase is clean overall. The main hygiene items are unused package dependencies and a few TODO comments.

**Findings**:

### TODO/FIXME/HACK Comments

| Location | Comment | Status |
|----------|---------|--------|
| `backend/src/api/projects.py:54` | `TODO: Also fetch org projects the user has access to` | ✅ RETAIN — genuinely open feature work |
| `backend/src/services/signal_chat.py:175,538,818` | `TODO(bug-bash): Security — this leaks internal exception details...` | ✅ RETAIN — genuinely open security decision requiring human input |

**Action**: All TODO comments reference open work items. None are stale. No action needed.

### Unused Dependencies (actionable)

**Backend** (`pyproject.toml`):
- Remove `python-jose[cryptography]>=3.3.0` — zero imports
- Remove `agent-framework-core>=1.0.0a1` — zero imports (only in code comments)

**Frontend** (`package.json`):
- Remove `socket.io-client` from dependencies — never imported (uses native WebSocket)
- Remove `jsdom` from devDependencies — vitest uses `happy-dom`

### Orphaned Configs

- **No orphaned migration files** — all 10 migrations (001–010) are active
- **No orphaned Docker Compose services** — all 3 services (backend, frontend, signal-api) are in use
- **No orphaned environment variables** — all `.env.example` vars are referenced in `config.py`

**Alternatives Considered**: Removing the `signal-api` Docker Compose service was considered (since Signal has no tests), but the service is functional production code with active source files, not an orphan.

---

## Technology Best Practices Applied

### Python Dependency Removal

- Use `pip uninstall` and remove from `pyproject.toml` `dependencies` list
- Run `ruff check src tests && ruff format --check src tests` after changes
- Run `python -m pytest tests/unit/ -q` (file by file for stability) to verify no regressions

### JavaScript Dependency Removal

- Use `npm uninstall <package>` to update both `package.json` and `package-lock.json`
- Run `npx eslint . && npx tsc --noEmit && npx vitest run` to verify no regressions
- Run `npx vite build` to confirm production build succeeds

### Test Fixture Consolidation

- Follow existing pattern in `tests/helpers/mocks.py` (factory functions returning configured mocks)
- Use `make_mock_<service>()` naming convention matching existing helpers
- Update all consuming test files to import from `tests/helpers/mocks.py`
- Verify with `pytest` that all tests pass after consolidation
