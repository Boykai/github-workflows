---
name: Code Quality Check
about: Recurring chore — Code Quality Check
title: '[CHORE] Code Quality Check'
labels: chore
assignees: ''
---

# Code Check

Perform the following:
---

## Phase 1: Critical — Fix Silent Failures & Security

### 1.1 Eliminate Silent Exception Swallowing (Backend)
- **Problem**: 32 `except → pass` blocks silently swallow errors; 94 bare `except Exception:` without `as e` lose context
- **Action**: Audit every `except` block in `backend/src/`. Replace `pass` with `logger.debug(...)` or propagate. Narrow `except Exception` to specific types (`httpx.HTTPStatusError`, `KeyError`, `ValueError`, etc.)
- **Files**: All service files, particularly `services/github_projects/service.py`, `services/copilot_polling/pipeline.py`, `services/workflow_orchestrator/orchestrator.py`
- **Impact**: Prevents hidden runtime bugs, improves debuggability

### 1.2 Fix Exception Detail Leaks (Backend)
- **Problem**: 3 locations in `signal_chat.py` leak internal exception details to external Signal API (tagged `TODO(bug-bash)`)
- **Action**: Wrap with `safe_error_response()` from existing `logging_utils.py`. Return generic user-facing messages, log internals
- **Files**: `src/services/signal_chat.py`
- **Impact**: Security — prevents information disclosure

### 1.3 Tighten CORS Configuration (Backend)
- **Problem**: `allow_methods=["*"]` in `main.py` (tagged `TODO(bug-bash)`)
- **Action**: Restrict to actual methods used: `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`
- **Files**: `src/main.py`

---

## Phase 2: DRY — Consolidate Duplicated Patterns

### 2.1 Unify Repository Resolution (Backend)
- **Problem**: 8 separate code paths resolve `(owner, repo)` with inconsistent fallback logic. `workflow.py:_get_repository_info()` duplicates `utils.resolve_repository()` but skips the 3-step fallback. `main.py` inlines the entire 102-line fallback
- **Action**: Standardize all call sites to use `utils.resolve_repository()`. Delete `_get_repository_info()` and inline copies
- **Files**: `api/workflow.py`, `api/projects.py`, `api/tasks.py`, `api/chat.py`, `api/chores.py`, `main.py`
- **Lines saved**: ~100+

### 2.2 Use Existing Error Handling Helpers (Backend)
- **Problem**: `handle_service_error()` and `safe_error_response()` exist in `logging_utils.py` but are never called. Each endpoint reinvents the `try → log → raise` pattern independently
- **Action**: Adopt these helpers across `api/board.py`, `api/workflow.py`, `api/projects.py`, `api/auth.py`. Replace ad-hoc catch-log-raise blocks
- **Files**: All route files in `src/api/`
- **Lines saved**: ~50

### 2.3 Extract Cache-or-Fetch Pattern (Backend)
- **Problem**: 5+ endpoints repeat the identical cache-check/fetch/cache-set pattern (~80 lines of boilerplate total)
- **Action**: Create a generic `cached_fetch(cache_key, fetch_fn, refresh, *args)` async helper in `src/utils.py` or a new `src/cache_utils.py`
- **Files**: `api/projects.py`, `api/board.py`, `api/chat.py`
- **Lines saved**: ~60

### 2.4 Extract Validation Guards (Backend)
- **Problem**: `if not session.selected_project_id: raise ValidationError(...)` repeated in 5 places with inconsistent messages
- **Action**: Create `require_selected_project(session) → str` helper in `dependencies.py`
- **Files**: `api/chat.py`, `api/workflow.py`, `api/tasks.py`, `api/chores.py`

### 2.5 Consolidate Modal/Dialog Patterns (Frontend)
- **Problem**: 3+ different modal implementations (ConfirmationDialog, IssueDetailModal, AgentPresetSelector) with different ARIA patterns
- **Action**: Use `ConfirmationDialog` as the base wrapper pattern. Refactor embedded dialogs in `AgentPresetSelector` to compose it
- **Files**: `components/board/AgentPresetSelector.tsx`, `components/board/IssueDetailModal.tsx`

### 2.6 Standardize `cn()` Usage (Frontend)
- **Problem**: Mixed use of `cn()` helper and direct template literal classNames
- **Action**: Replace all template literal className constructions with `cn()` from `lib/utils`
- **Files**: Various components across `src/components/` and `src/pages/`

---

## Phase 3: Break Apart God Files

### 3.1 Split `github_projects/service.py` (5,150 LOC → ~5 modules)
- **Problem**: Single file owns all GitHub API operations — projects, issues, PRs, branches, Copilot assignment, board data, completion detection
- **Action**: Extract into focused submodules:
  - `github_projects/issues.py` — Issue CRUD, comments, state management
  - `github_projects/pull_requests.py` — PR creation, merge, review, completion detection
  - `github_projects/copilot.py` — Agent assignment, unassignment, review request
  - `github_projects/board.py` — Board data fetching, reconciliation
  - `github_projects/service.py` — Orchestration facade, shared infra (retry, ETag cache, throttle)
- **Impact**: Highest-value refactor. Improves readability, testability, and merge conflicts

### 3.2 Split `frontend/src/services/api.ts` (1,099 LOC → modules)
- **Problem**: Single file contains 50+ API functions for all domains
- **Action**: Split into:
  - `services/api/client.ts` — `request<T>()`, `ApiError`, auth listener
  - `services/api/projects.ts` — Project endpoints
  - `services/api/chat.ts` — Chat endpoints
  - `services/api/agents.ts` — Agent CRUD
  - `services/api/tools.ts` — MCP tool endpoints
  - `services/api/board.ts` — Board endpoints
  - `services/api/index.ts` — Re-exports

### 3.3 Split Large Hooks (Frontend)
- **Problem**: `usePipelineConfig.ts` (616 LOC), `useChat.ts` (385 LOC), `useBoardControls.ts` (375 LOC) mix concerns
- **Action**: Extract sub-hooks. Example: `usePipelineConfig` → `usePipelineState` + `usePipelineMutations` + `usePipelineValidation`

---

## Phase 4: Type Safety & Strictness

### 4.1 Add Missing Return Type Hints (Backend)
- **Problem**: 24 functions missing return type annotations; generic `dict`/`list` used instead of `TypedDict` or specific types
- **Action**: Add return types to all public functions. Replace `dict` returns with `TypedDict` in service methods (e.g., board data, issue data)
- **Scope**: All files in `src/services/`, `src/api/`

### 4.2 Enable Strict TypeScript Checks (Frontend)
- **Problem**: `noUnusedLocals: false` and `noUnusedParameters: false` allow dead code
- **Action**: Enable both in `tsconfig.json`. Fix resulting errors (prefix unused params with `_`)
- **Files**: `tsconfig.json` + all files with violations

### 4.3 Replace `as unknown as Record<string, unknown>` Casts (Frontend)
- **Problem**: 7 occurrences mostly in hooks for parsing dynamic API data
- **Action**: Define proper discriminated unions or branded types for dynamic API responses
- **Files**: `useChat.ts`, test files

---

## Phase 5: Remove Technical Debt & Legacy Code

### 5.1 Replace Module-Level Singletons with DI (Backend)
- **Problem**: 9 global singleton instances (`_ai_agent_service_instance`, global service in `service.py`, global orchestrator, global DB connection, etc.) complicate testing and prevent proper lifecycle management
- **Action**: Migrate to FastAPI `app.state` or `Depends()` injection. Use factory functions called during lifespan startup
- **Files**: `services/ai_agent.py`, `services/github_projects/service.py`, `services/workflow_orchestrator/orchestrator.py`, `services/database.py`, `services/websocket.py`
- **Impact**: Testability, resource lifecycle, prevents memory leaks

### 5.2 Remove `__import__()` Anti-Pattern (Backend)
- **Problem**: `chores/template_builder.py` uses `__import__("time").time()` instead of standard import
- **Action**: Replace with `import time; time.time()`
- **Files**: `src/services/chores/template_builder.py`

### 5.3 Fix Duplicate Migration Prefixes (Backend)
- **Problem**: TODO notes duplicate migration prefixes (013, 014, 015) in database.py
- **Action**: Audit migration numbering, fix conflicts, add a migration prefix uniqueness check in test suite
- **Files**: `src/services/database.py`, `src/migrations/`

### 5.4 Migrate In-Memory Chat Stores to SQLite (Backend)
- **Problem**: Chat history stored in-memory (unbounded growth, lost on restart). Tagged `TODO(018-codebase-audit-refactor)`
- **Action**: Add SQLite tables for chat messages. Implement async persistence with bounded retention (e.g., last 1000 messages per session)
- **Files**: `api/chat.py`, new migration file

### 5.5 Remove Unused Dependencies (Frontend)
- **Problem**: `jsdom` installed alongside `happy-dom` but tests use `happy-dom`
- **Action**: Remove `jsdom` from `package.json` devDependencies

### 5.6 Consolidate Test Directories (Frontend)
- **Problem**: Two test directories (`src/test/` and `src/tests/`) exist
- **Action**: Merge into `src/test/` (which contains setup files)

### 5.7 Resolve All TODO Comments
- **Problem**: 8 TODO/FIXME comments in backend, including security-tagged items
- **Action**: Convert each to a GitHub issue or fix inline. Priority: `TODO(bug-bash)` items first

---

## Phase 6: Performance & Observability

### 6.1 Add `useMemo` / `React.memo` (Frontend)
- **Problem**: Pages like `AgentsPage` rebuild derived data structures every render. `stageAgentInfoMap` computed on every render without memoization
- **Action**: Wrap expensive computations in `useMemo`. Apply `React.memo` to pure child components (agent cards, board columns, tool cards)
- **Files**: `pages/AgentsPage.tsx`, `pages/ProjectsPage.tsx`, `pages/AgentsPipelinePage.tsx`

### 6.2 Add AbortController for Fetch Cancellation (Frontend)
- **Problem**: No request cancellation on route changes — potential memory leaks and stale state
- **Action**: Pass `AbortSignal` from TanStack Query to the `request<T>()` function in `api.ts`
- **Files**: `services/api.ts`

### 6.3 Cap In-Memory Data Structures (Backend)
- **Problem**: In-memory caches and stores can grow unbounded
- **Action**: Audit all `dict`/`list` stores; apply `BoundedDict` or explicit max-size limits with LRU eviction
- **Files**: `services/cache.py`, `api/chat.py`

### 6.4 Add Bundle Analysis (Frontend)
- **Action**: Add `rollup-plugin-visualizer` to Vite config for CI bundle size tracking
- **Files**: `vite.config.ts`, `package.json`

---

## Phase 7: Testing & Linting Gaps (Ongoing)

### 7.1 Expand Backend Test Specificity
- **Problem**: Broad `except Exception` in 315 locations masks which exceptions tests should cover
- **Action**: After Phase 1 narrowing, add tests for each specific exception type in service methods
- **Target**: Increase coverage in `tests/unit/` for services with complex error flows

### 7.2 Add Frontend Page + Component Tests
- **Problem**: Page components (`AgentsPage`, `ProjectsPage`, `AppPage`) largely untested. Only ~10 of 44 hooks tested
- **Action**: Add render tests for all pages. Add `jest-axe` accessibility assertions to critical user paths
- **Target**: 70%+ coverage for `src/components/`, `src/pages/`

### 7.3 Enhance ESLint Config (Frontend)
- **Problem**: Missing `eslint-plugin-import` (no import sorting) and `eslint-plugin-react` (limited React checks)
- **Action**: Add both plugins. Configure import ordering rules
- **Files**: `eslint.config.js`, `package.json`

### 7.4 Strengthen Accessibility Tests (Frontend)
- **Problem**: Only `button.test.tsx` uses `jest-axe`. Chat messages lack `aria-live` for real-time updates
- **Action**: Add `jest-axe` assertions to modal, form, and page tests. Add `aria-live="polite"` to chat message regions
- **Files**: Test files + `components/chat/`

---

## Priority Summary

| Priority | Phase | Items | Effort | Impact |
|----------|-------|-------|--------|--------|
| **P0** | Phase 1 | Silent failures, security leaks, CORS | 2–3 days | Prevents hidden bugs & security issues |
| **P1** | Phase 2 | DRY consolidation (6 items) | 3–5 days | Removes ~300+ duplicate lines, consistent patterns |
| **P2** | Phase 3 | Break apart god files (3 items) | 5–7 days | Highest structural improvement |
| **P2** | Phase 4 | Type safety (3 items) | 2–3 days | Catches errors at compile time |
| **P3** | Phase 5 | Tech debt removal (7 items) | 5–7 days | Clean architecture, proper lifecycle |
| **P3** | Phase 6 | Performance & observability (4 items) | 3–4 days | Faster UI, bounded memory |
| **P4** | Phase 7 | Testing & linting (4 items) | Ongoing | Long-term maintainability |

---

## Guiding Principles

1. **Every `except` must earn its keep** — no silent swallowing, no bare `Exception` without logged context
2. **One canonical path** — if a utility exists (`resolve_repository`, `safe_error_response`), use it everywhere
3. **Files under 500 LOC** — any file exceeding this is a candidate for extraction
4. **Types at boundaries** — all public functions get full type annotations; `dict` returns become `TypedDict`
5. **Test what you change** — every refactor ships with updated or new tests
6. **No new globals** — new services use FastAPI DI (`Depends()` / `app.state`), not module-level singletons
