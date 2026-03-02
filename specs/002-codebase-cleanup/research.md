# Research: Codebase Cleanup — Reduce Technical Debt and Improve Maintainability

**Date**: 2026-03-02  
**Feature**: 002-codebase-cleanup  
**Status**: Complete

## Research Summary

Analysis was conducted via static analysis tools (ruff, pyright, tsc, eslint), grep-based code search, and manual cross-referencing of all imports, call sites, and test targets. Each finding was verified by confirming zero references from production code (and in some cases zero references from test code) before classifying as dead/stale.

---

## Category 1: Dead Code Paths

### Decision: Remove all confirmed dead functions, models, and unused artifacts

**Rationale**: Each item was confirmed unreachable by checking all import statements and call sites across the full codebase. No dynamic loading patterns reference any of these symbols.

**Alternatives considered**: Marking as deprecated with warnings — rejected because there is no deprecation window needed (code is already unused).

### Backend Dead Code

| Item | Location | Lines | Confirmation |
|------|----------|-------|-------------|
| `handle_copilot_pr_ready()` | `backend/src/api/webhooks.py:98` | ~93 lines | Zero production callers. `handle_pull_request_event` calls `update_issue_status_for_copilot_pr` directly. |
| `determine_next_action()` | `backend/src/services/agent_tracking.py:304` | ~74 lines | Zero production or test callers (only tested in isolation). |
| `PipelineAction` dataclass | `backend/src/services/agent_tracking.py:293` | ~10 lines | Only used by `determine_next_action()` (which is dead). |
| `is_threshold_met()` | `backend/src/services/housekeeping/counter.py:4` | Entire file (~23 lines) | Zero references anywhere in codebase. |
| `reset_ai_agent_service()` | `backend/src/services/ai_agent.py:831` | ~10 lines | Only called from tests, never from production code. Test-only utility. |
| `TTLCache.get_entry()` | `backend/src/services/cache.py:83` | ~12 lines | Zero callers. |
| `TTLCache.refresh_ttl()` | `backend/src/services/cache.py:95` | ~15 lines | Zero callers. |
| `TTLCache.clear_expired()` | `backend/src/services/cache.py:135` | ~15 lines | Zero callers. |
| `UserPreferencesRow` | `backend/src/models/settings.py:222` | ~20 lines | Only in tests; production constructs raw dicts. |
| `GlobalSettingsRow` | `backend/src/models/settings.py:242` | ~20 lines | Same as above. |
| `ProjectSettingsRow` | `backend/src/models/settings.py:263` | ~20 lines | Same as above. |
| MagicMock artifact files | `backend/` root | 143 zero-byte files | Test artifacts from unmocked `get_settings().database_path`. |

### Frontend Dead Code

| Item | Location | Confirmation |
|------|----------|-------------|
| `HousekeepingTaskForm` component | `frontend/src/components/housekeeping/HousekeepingTaskForm.tsx` | Zero imports |
| `HousekeepingTaskList` component | `frontend/src/components/housekeeping/HousekeepingTaskList.tsx` | Zero imports |
| `RunNowButton` component | `frontend/src/components/housekeeping/RunNowButton.tsx` | Zero imports |
| `TemplateLibrary` component | `frontend/src/components/housekeeping/TemplateLibrary.tsx` | Zero imports |
| `TriggerHistoryLog` component | `frontend/src/components/housekeeping/TriggerHistoryLog.tsx` | Zero imports |
| `AIPreferences` component | `frontend/src/components/settings/AIPreferences.tsx` | Zero imports; superseded by `PrimarySettings` |
| 45 unused type exports | `frontend/src/types/index.ts` | Zero imports outside file |
| `projectsApi.get()` | `frontend/src/services/api.ts:149` | Zero callers |
| `tasksApi.create()` | `frontend/src/services/api.ts:176` | Zero callers |
| `statusColorToBg()` | `frontend/src/components/board/colorUtils.ts:41` | Zero callers |
| `registerCommand()` | `frontend/src/lib/commands/registry.ts:18` | Only used at module init, never externally |
| `unregisterCommand()` | `frontend/src/lib/commands/registry.ts:23` | Zero callers |
| `ParameterSchema` type | `frontend/src/lib/commands/types.ts:8` | Zero references |
| `CommandHandler` type | `frontend/src/lib/commands/types.ts:32` | Zero references |
| `BOARD_POLL_INTERVAL_MS` | `frontend/src/constants.ts:22` | Zero references |
| `WS_RECONNECT_DELAY_MS` | `frontend/src/constants.ts:28` | Zero references |

### Frontend Dead Dependencies

| Package | Status | Confirmation |
|---------|--------|-------------|
| `socket.io-client` | Unused | Zero imports; app uses native `WebSocket` API |

---

## Category 2: Stale Tests

### Decision: Remove tests for dead code; update tests that use compatibility shims

**Rationale**: Tests targeting dead functions provide false coverage signals. Tests coupled to backward-compat import paths will break when shims are removed.

| Test | Target | Status | Action |
|------|--------|--------|--------|
| `TestDetermineNextAction` (7 methods) | `agent_tracking.py:determine_next_action` | STALE — tests dead function | Remove |
| `TestHandleCopilotPrReady` (3+ methods) | `webhooks.py:handle_copilot_pr_ready` | STALE — tests dead function | Remove |
| Tests importing via `src.models.chat` | Re-export shim | Valid behavior, stale import path | Update imports to canonical modules |
| `backend/tests/helpers/` | Shared factories/mocks/assertions | DEAD — never imported by any test | Remove entire helpers directory |

---

## Category 3: Duplicated Logic

### Decision: Consolidate duplicates into canonical implementations

**Rationale**: Duplicate implementations diverge over time and increase maintenance burden.

| Duplicate | Canonical Location | Duplicated In | Action |
|-----------|-------------------|---------------|--------|
| `formatTimeAgo()` | `frontend/src/utils/formatTime.ts:9` | `DynamicDropdown.tsx:34` (local version takes ISO string) | Consolidate: extend canonical to accept Date or string |
| `STALE_TIME_MEDIUM` / `STALE_TIME_SHORT` | `frontend/src/constants.ts:14,17` | Both set to `60 * 1000` | Differentiate values or merge into one constant |
| `_make_board_project()` | `backend/tests/helpers/factories.py:90` | `test_api_board.py` (inline helper) | Note: since helpers/ is dead, the inline version stays. If helpers were used, consolidate. |

### Decision on `hasattr(agent, "slug")` patterns: Defer

**Rationale**: 11 instances of `if hasattr(agent, "slug")` across orchestrator/tracking code are defensive typing patterns, not classic duplication. They guard against two possible types (`AgentAssignment` vs plain string). Cleaning these up requires a type-narrowing refactor that changes internal signatures — deferred to avoid scope creep. This is a valid future improvement but not a dead-code cleanup item.

---

## Category 4: Backwards-Compatibility Shims

### Decision: Remove unnecessary shims; keep still-needed aliases

| Shim | Location | Status | Action |
|------|----------|--------|--------|
| 19 re-exports in `chat.py` | `backend/src/models/chat.py:16-44` | Dead (only tests use this path) | Remove re-exports; update test imports |
| `PREDEFINED_LABELS = LABELS` | `backend/src/prompts/issue_generation.py:9` | Only used by `test_prompts.py` | Remove alias; update test import |
| `get_session_dep = get_current_session` | `backend/src/api/auth.py:56` | Actively used by conftest and many tests | Keep (still needed) |
| Orchestrator `__init__.py` re-exports | `backend/src/services/workflow_orchestrator/__init__.py:10` | Used by copilot_polling | Keep (still needed) |
| Legacy `process_in_progress_issue` path | `backend/src/services/copilot_polling/pipeline.py` | Legacy path for issues without agent pipelines | Defer — requires careful analysis of edge cases |

### Decision on legacy pipeline path: Defer

**Rationale**: The legacy `process_in_progress_issue` code path in `pipeline.py` handles issues that lack agent pipeline state. Removing it requires confirming that ALL in-progress issues now have pipeline state, which is a runtime assertion that cannot be verified statically. This is a candidates for feature-flag-based removal with monitoring, not a static cleanup.

---

## Category 5: General Hygiene

### Decision: Remove unused deps and clean up metadata

| Item | Location | Action |
|------|----------|--------|
| `python-jose[cryptography]` | `backend/pyproject.toml` | Remove — no imports found |
| `agent-framework-core` | `backend/pyproject.toml` | Remove — no imports found |
| `python-multipart` | `backend/pyproject.toml` | Keep — implicit FastAPI requirement for form parsing |
| `github-copilot-sdk` | `backend/pyproject.toml` | Keep — dynamically loaded by completion_providers |
| `socket.io-client` | `frontend/package.json` | Remove — app uses native WebSocket |
| TODO comment in `projects.py:54` | `backend/src/api/projects.py` | Keep — references genuinely outstanding work (org project support) |
| MagicMock files root cause | Test mocking configuration | Fix: ensure `get_settings().database_path` is properly mocked in test fixtures |
| `.gitignore` entry | `backend/<MagicMock *` | Already present; delete accumulated files |

### Deferred Items

| Item | Reason for Deferral |
|------|-------------------|
| `hasattr(agent, "slug")` defensive patterns | Type-narrowing refactor changes internal signatures; out of scope |
| Legacy `process_in_progress_issue` path | Runtime behavior cannot be verified statically; needs monitoring |
| `test_api_e2e.py` fixture duplication | Refactoring to use conftest is improvement, not cleanup; could break test isolation |

---

## Research Completion Status

All NEEDS CLARIFICATION items resolved:

- **Dynamic loading check**: `github-copilot-sdk` and `azure-ai-inference` are dynamically imported — confirmed used. `agent-framework-core` has zero dynamic references — confirmed unused.
- **`python-multipart` check**: Required by FastAPI internals for form data parsing — confirmed needed even without explicit import.
- **Test helpers decision**: Since `backend/tests/helpers/` is completely unused, removing it does not affect any tests. Tests that inline their own setup are preserved.
- **Legacy pipeline path**: Confirmed as too risky for static removal — deferred.
- **`get_session_dep` alias**: Confirmed actively used — keep.
