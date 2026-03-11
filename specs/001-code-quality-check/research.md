# Research: Code Quality Check

**Feature**: 001-code-quality-check | **Date**: 2026-03-11

## Research Tasks & Findings

### R-001: Exception Handling — Current State of Silent Swallowing

**Decision**: Audit confirmed ~38 bare `except Exception:` blocks across 15 backend files, with most already binding `as e`. The 4 blocks in `logging_utils.py` are intentional resilience guards. Priority targets are `workflow_orchestrator/config.py` (9 blocks), `chores/service.py` (6 blocks), and `agents/service.py` (4 blocks).

**Rationale**: The original issue estimated 32 `except → pass` blocks and 94 bare `except Exception:` — actual counts are lower (2 pass blocks, ~38 bare except). Prior work already converted many. Remaining blocks need narrowing to specific exception types rather than blanket `Exception`.

**Alternatives considered**: Leaving bare `except Exception as e:` in place was rejected because it still catches too broadly (e.g., `SystemExit`, `KeyboardInterrupt` through `BaseException` are safe, but `Exception` catches programming errors like `AttributeError`).

---

### R-002: Exception Detail Leaks — Signal Chat Integration

**Decision**: Two locations in `signal_chat.py` leak internal exception details to external systems: line ~103 (`error_detail=str(e)[:500]` sent to Signal delivery status) and line ~329 (`result["error"] = str(e)[:200]` in proposal response). These must be sanitized.

**Rationale**: `safe_error_response()` does NOT exist in `logging_utils.py` as the issue suggested. The existing `handle_service_error()` helper is designed for route-level errors, not external API responses. A new `sanitize_error_for_external()` helper or inline sanitization is needed.

**Alternatives considered**: Using `handle_service_error()` was rejected because it raises HTTP exceptions (designed for FastAPI routes), not for formatting messages to external messaging APIs.

---

### R-003: CORS Configuration

**Decision**: Already resolved. `allow_methods` in `main.py` is set to `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`.

**Rationale**: No action needed — verified in codebase audit.

---

### R-004: Shared Backend Helpers — Current Adoption State

**Decision**: Four of five shared helpers already exist and are adopted:

| Helper | Location | Status |
|--------|----------|--------|
| `resolve_repository()` | `utils.py` | ✅ Exists, used across call sites |
| `cached_fetch()` | `utils.py` | ✅ Exists, used |
| `require_selected_project()` | `dependencies.py` | ✅ Exists, used |
| `handle_service_error()` | `logging_utils.py` | ✅ Exists, used |
| `safe_error_response()` | `logging_utils.py` | ❌ Does NOT exist |

**Rationale**: Prior refactoring work already addressed the DRY consolidation for these patterns. The remaining gap is the missing `safe_error_response()` for external-facing error sanitization (see R-002).

**Alternatives considered**: Creating `safe_error_response()` as specified in the issue was considered but rejected because the name implies HTTP response formatting. A more descriptive name like `sanitize_error_for_external()` better communicates its purpose for non-HTTP contexts (Signal API).

---

### R-005: Backend God File Split — Already Complete

**Decision**: `github_projects/service.py` has already been split from ~5,150 LOC into 12 focused modules totaling ~200 KB. The orchestration facade (`service.py`) is now 343 LOC.

**Rationale**: No action needed. The split matches the issue's recommended structure (issues, pull_requests, copilot, board, plus additional modules for agents, branches, graphql, identities, projects, repository).

---

### R-006: Frontend API Client Split Strategy

**Decision**: `frontend/src/services/api.ts` (1,136 LOC) should be split into domain modules. The file already organizes exports by domain (13 export objects: authApi, projectsApi, tasksApi, chatApi, boardApi, settingsApi, workflowApi, metadataApi, signalApi, mcpApi, cleanupApi, choresApi, agentsApi, pipelinesApi, modelsApi, toolsApi, agentToolsApi).

**Rationale**: The natural domain boundaries already exist as named export objects. Each can become its own module file, with the shared `request<T>()` function, `ApiError` class, and auth listener extracted to a `client.ts` module.

**Alternatives considered**: Keeping the monolithic file was rejected because 1,136 LOC exceeds the 500 LOC guideline and makes code review and merge conflicts harder. A single-function-per-file approach was rejected as too granular.

---

### R-007: Frontend Large Hooks — useBoardControls Analysis

**Decision**: `useBoardControls.ts` (375 LOC) mixes 5 concerns: filter state, sort state, group state, data transformation, and localStorage persistence. It should be split into `useBoardFilters` (state + persistence), `useBoardSort` (state + persistence), `useBoardGroups` (grouping logic), with `useBoardControls` as a composition wrapper.

**Rationale**: `usePipelineConfig.ts` (187 LOC) and `useChat.ts` (178 LOC) are already under the 250 LOC threshold and do not need splitting. Only `useBoardControls.ts` exceeds guidelines.

**Alternatives considered**: Extracting only the data transformation functions (not hooks) to a utility file was considered but rejected because the state management and transformation are tightly coupled through React state updates.

---

### R-008: TypeScript Strict Checks — Already Enabled

**Decision**: `noUnusedLocals: true` and `noUnusedParameters: true` are already enabled in `tsconfig.json`.

**Rationale**: No action needed — verified in codebase audit.

---

### R-009: Frontend Unsafe Type Casts

**Decision**: 13 `as unknown as` casts found across 10 files. Only 4 are in production code (2 in `AgentColumnCell.tsx` for dnd-kit library typing, 2 in `McpSettings.tsx` for error field access). The remaining 8 are in test files for mock typing.

**Rationale**: Production casts should be replaced with proper type guards or discriminated unions. Test casts are acceptable (mock objects often need type coercion).

**Alternatives considered**: Ignoring all casts was rejected because production code casts mask type safety. Fixing test casts was rejected as low-value busywork.

---

### R-010: Module-Level Singletons

**Decision**: Two singletons confirmed with existing TODO markers:

1. `_orchestrator_instance` in `workflow_orchestrator/orchestrator.py` with `get_workflow_orchestrator()`
2. `_ai_agent_service_instance` in `ai_agent.py` with `get_ai_agent_service()` and `reset_ai_agent_service()`

Both are tagged `TODO(018-codebase-audit-refactor)`.

**Rationale**: These should migrate to FastAPI `app.state` or `Depends()` injection. The `reset_*` function pattern indicates they are already designed with testability in mind, making migration straightforward.

**Alternatives considered**: Keeping singletons with better documentation was rejected because module-level state prevents proper lifecycle management and complicates testing.

---

### R-011: `__import__()` Anti-Pattern

**Decision**: Not found in `template_builder.py`. The anti-pattern has already been removed.

**Rationale**: No action needed — verified in codebase audit.

---

### R-012: Duplicate Migration Prefixes

**Decision**: Confirmed duplicate prefixes: 013 (2 files), 014 (2 files), 015 (2 files) = 6 migration files sharing 3 prefix numbers. Total: 20 migration files covering prefixes 001–020.

**Rationale**: SQLite migration runner applies files in lexicographic order, so `013_agent_config_lifecycle_status.sql` runs before `013_pipeline_configs.sql` (alphabetical). This works but is fragile — any new migration with prefix 013 could interleave unpredictably. A uniqueness validation test should be added.

**Alternatives considered**: Renumbering existing migrations was rejected because it would require all existing databases to be re-migrated or a migration rename mapping, which is more disruptive than adding a uniqueness check.

---

### R-013: Chat Persistence State

**Decision**: Migration `012_chat_persistence.sql` already creates `chat_messages`, `chat_proposals`, and `chat_recommendations` tables. However, `api/chat.py` line 84 has `TODO(018-codebase-audit-refactor): Migrate these in-memory stores to SQLite`, indicating the code still uses in-memory stores for some chat data. Additionally, `signal_chat.py` uses `_signal_pending: dict[str, dict] = {}` as an unbounded in-memory store.

**Rationale**: The database schema exists but the application code may not fully use it yet. The in-memory `_signal_pending` dict lacks cleanup and size limits.

---

### R-014: Frontend Dependencies and Test Structure

**Decision**: Both already resolved:

- `jsdom` is NOT installed (only `happy-dom` present)
- Only `frontend/src/test/` exists (no duplicate `tests/` directory)

**Rationale**: No action needed — verified in codebase audit.

---

### R-015: Frontend cn() Usage

**Decision**: No template literal className anti-patterns found. The `cn()` helper from `lib/utils.ts` is the standard pattern.

**Rationale**: No action needed — verified in codebase audit. Template literal usage found was for `aria-label` attributes (acceptable).

---

### R-016: AbortController for Fetch Cancellation

**Decision**: Infrastructure partially exists — the `request<T>()` function accepts `RequestInit` which can carry `AbortSignal`. One endpoint (`fetchModels`) explicitly documents signal support. However, systematic abort-on-navigation is not implemented.

**Rationale**: TanStack Query supports automatic AbortSignal propagation via `queryFn({ signal })`. The gap is that most API functions don't pass `init` through to `request()`.

---

### R-017: Bundle Analysis

**Decision**: `rollup-plugin-visualizer` should be added to `vite.config.ts` as an opt-in plugin for CI bundle size tracking.

**Rationale**: No existing bundle analysis tooling is configured. This is a non-breaking addition.

---

### R-018: TODO/FIXME Resolution

**Decision**: 4 TODO comments found in backend:

1. `api/chat.py:84` — In-memory store migration (covered by R-013)
2. `api/projects.py:109` — Org project fetching (feature request, not quality issue)
3. `github_projects/agents.py:363` — Singleton removal (covered by R-010)
4. `github_projects/service.py:338` — Singleton removal (covered by R-010)

**Rationale**: Items 1, 3, 4 are addressed by other work items. Item 2 is a feature enhancement and should be converted to a GitHub issue.

---

## Summary of Resolved vs. Remaining Items

### Already Resolved (No Action Needed)

| Item | Reference |
|------|-----------|
| CORS configuration | R-003 |
| Backend god file split | R-005 |
| Shared backend helpers (4 of 5) | R-004 |
| TypeScript strict checks | R-008 |
| `__import__()` anti-pattern | R-011 |
| jsdom removal | R-014 |
| Test directory consolidation | R-014 |
| cn() standardization | R-015 |

### Remaining Work Items

| Item | Priority | Effort | Reference |
|------|----------|--------|-----------|
| Exception handling audit (38 blocks) | P0 | 2–3 days | R-001 |
| Signal chat exception leaks (2 locations) | P0 | 0.5 day | R-002 |
| Frontend API client split (1,136 LOC) | P2 | 2–3 days | R-006 |
| useBoardControls split (375 LOC) | P2 | 1 day | R-007 |
| Unsafe type casts (4 production) | P2 | 0.5 day | R-009 |
| Module-level singletons (2 services) | P3 | 2 days | R-010 |
| Duplicate migration prefix validation | P3 | 0.5 day | R-012 |
| Chat persistence completion | P3 | 1–2 days | R-013 |
| AbortController propagation | P3 | 1 day | R-016 |
| Bundle analysis setup | P3 | 0.5 day | R-017 |
| TODO resolution (4 items) | P3 | 0.5 day | R-018 |
