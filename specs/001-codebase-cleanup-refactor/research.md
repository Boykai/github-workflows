# Research: Codebase Cleanup & Refactor

**Feature**: `001-codebase-cleanup-refactor` | **Date**: 2026-02-22

## R1. Module Split Strategy for `github_projects.py`

**Decision**: Convert `github_projects.py` (4,449 lines) into a `github_projects/` Python package with 8 sub-modules plus a re-export `__init__.py` facade.

**Rationale**: The file contains a single `GitHubProjectsService` class with methods that group naturally into 7 responsibility areas. Converting to a package with an `__init__.py` that re-exports the singleton preserves backward compatibility for all importers (`from services.github_projects import github_projects_service`).

**Module decomposition**:

| Module | Responsibility | Methods | ~Lines |
|--------|---------------|---------|--------|
| `client.py` | HTTP client, retry logic, GraphQL executor | `__init__`, `close`, `_request_with_retry`, `_graphql` | 120 |
| `queries.py` | All GraphQL query/mutation string constants | ~20 constants | 200 |
| `projects.py` | Project listing, board data, field updates, change detection | `list_user_projects`, `list_org_projects`, `get_project_items`, `get_board_data`, `get_project_fields`, `update_project_item_field`, `poll_project_changes` | 500 |
| `issues.py` | Issue CRUD, sub-issues, comments, metadata | `create_draft_item`, `create_issue`, `update_issue_body`, `update_issue_state`, `add_issue_to_project`, `assign_issue`, `get_issue_with_comments`, `create_issue_comment`, `create_sub_issue`, `get_sub_issues` | 450 |
| `pull_requests.py` | PR lifecycle, merge, review, file content | `get_linked_pull_requests`, `find_existing_pr_for_issue`, `get_pull_request`, `mark_pr_ready_for_review`, `request_copilot_review`, `merge_pull_request`, `delete_branch`, `link_pull_request_to_issue`, `get_pr_changed_files`, `get_file_content_from_ref`, `check_copilot_pr_completion` | 500 |
| `assignments.py` | Copilot/agent assignment and validation | `get_copilot_bot_id`, `is_copilot_assigned_to_issue`, `assign_copilot_to_issue`, `unassign_copilot_from_issue`, `validate_assignee`, `get_repository_owner` | 400 |
| `status.py` | Status column field updates | `update_item_status`, `update_item_status_by_name`, `update_sub_issue_project_status` | 200 |
| `agents.py` | Agent listing/discovery | `BUILTIN_AGENTS`, `list_available_agents` | 120 |

**Implementation approach**: The `GitHubProjectsService` class is preserved but refactored to delegate to sub-module functions. Each sub-module contains free functions that accept the service's HTTP client (or access token) as a parameter. The class methods become thin wrappers that call the sub-module functions. The `__init__.py` re-exports the class and singleton unchanged.

**Alternatives considered**:
- *Single-file cleanup only* — Rejected: 4,449 lines exceeds any reasonable file-size guideline.
- *Full class decomposition into separate service classes* — Rejected: Would break the `github_projects_service` singleton API that 10+ modules depend on.
- *Mixin classes* — Rejected: Adds unnecessary class hierarchy complexity.

## R2. Module Split Strategy for `copilot_polling.py`

**Decision**: Convert `copilot_polling.py` (3,948 lines) into a `copilot_polling/` Python package with 10 sub-modules plus a re-export `__init__.py` facade.

**Rationale**: The file is entirely module-level functions (no class) with 8 mutable state variables. Functions group cleanly by polling phase (backlog → in-progress → completion → recovery). The module-level state stays in `state.py` and is imported by other sub-modules.

**Module decomposition**:

| Module | Responsibility | Functions | ~Lines |
|--------|---------------|-----------|--------|
| `state.py` | PollingState dataclass + 8 module-level state vars + getters | `PollingState`, `get_polling_status`, state vars | 80 |
| `loop.py` | Polling lifecycle | `start_polling`, `stop_polling`, `_poll_loop` | 120 |
| `backlog.py` | Backlog + Ready issue processing | `check_backlog_issues`, `check_ready_issues` | 300 |
| `in_progress.py` | In-progress issue processing | `check_in_progress_issues`, `process_in_progress_issue`, `check_in_review_issues_for_copilot_review`, `ensure_copilot_review_requested` | 400 |
| `pipeline.py` | Pipeline state reconstruction + advancement | `_advance_pipeline`, `_transition_after_pipeline_complete`, `_reconstruct_pipeline_state`, `_get_or_reconstruct_pipeline` | 500 |
| `completion.py` | PR completion detection + merge | `_check_child_pr_completion`, `_check_main_pr_completion`, `_find_completed_child_pr`, `_merge_child_pr_if_applicable` | 500 |
| `outputs.py` | Agent output posting from PRs | `post_agent_outputs_from_pr` | 300 |
| `recovery.py` | Stalled issue self-healing | `recover_stalled_issues` | 300 |
| `manual.py` | Manual single-issue check | `check_issue_for_copilot_completion` | 60 |

**State sharing**: `state.py` exports all mutable state variables. Other sub-modules import from `state.py`. This preserves the current pattern of module-level shared state without introducing new abstractions.

**Alternatives considered**:
- *Convert to a class with instance state* — Rejected: Would require significant refactoring of all callers that import functions directly.
- *Keep as single file with better organization* — Rejected: 3,948 lines is unmanageable.

## R3. Shared Utility Extraction Strategy

**Decision**: Create `services/shared/` package with 5 focused utility modules extracted from proven-duplicated code.

**Utilities to extract**:

| Utility | Source of Duplication | Callers |
|---------|----------------------|---------|
| `github_headers.py` | GitHub REST headers constructed inline 20+ times in `github_projects.py` (Authorization, Accept, X-GitHub-Api-Version) | All `github_projects/` sub-modules, `webhooks.py` |
| `bounded_set.py` | "If size > N, prune oldest" pattern in `_processed_issue_prs`, `_processed_delivery_ids`, `_recovery_last_attempt` | `copilot_polling/state.py`, `webhooks.py` |
| `datetime_utils.py` | ISO 8601 parsing + timezone normalization duplicated in `_filter_events_after`, `check_copilot_pr_completion`, `_check_main_pr_completion` | `copilot_polling/completion.py`, `github_projects/pull_requests.py` |
| `cache_keys.py` | Cache key construction scattered across `constants.py`, `cache.py`, `board.py` | All cache consumers |
| `issue_parsing.py` | Issue-number extraction from PR branch/body in `webhooks.py` and `github_projects.py` | `webhooks.py`, `github_projects/pull_requests.py` |

**Alternatives considered**:
- *Inline utilities in each package* — Rejected: Defeats the purpose of DRY.
- *Top-level `utils/` directory* — Rejected: These utilities are service-layer concerns.

## R4. Error Handling Standardization

**Decision**: Standardize on the existing `AppException` hierarchy in `exceptions.py`. Replace all 9 direct `HTTPException` raises with `AppException` subclasses. Update the generic exception handler to log full details server-side while returning sanitized responses. Address the 73 bare `except Exception` blocks.

**Current state**:
- `exceptions.py` defines a clean hierarchy: `AppException` → `AuthenticationError`(401), `AuthorizationError`(403), `NotFoundError`(404), `ValidationError`(422), `GitHubAPIError`(502), `RateLimitError`(429)
- `main.py` has handlers for `AppException` and generic `Exception`
- `auth.py` mixes `HTTPException(400)` with `AuthenticationError`
- `webhooks.py` uses `HTTPException` directly
- 73 bare `except Exception` blocks across services (31 in `copilot_polling.py`, 22 in `github_projects.py`, 8 in `workflow_orchestrator.py`, 5 in `completion_providers.py`)

**Changes**:
1. Replace all `HTTPException` raises with appropriate `AppException` subclasses
2. Add `traceback.format_exc()` to the generic exception handler's server-side logging
3. Generic handler returns only `{"error": "Internal server error"}` (sanitized)
4. In service modules: convert silent catches to `logger.warning()` + return sentinel for non-critical checks, or re-raise as `GitHubAPIError` for operations that should surface failures

**Alternatives considered**:
- *New exception hierarchy* — Rejected: Existing one is well-designed, just under-utilized.
- *Middleware-only approach* — Rejected: FastAPI's exception handlers already serve this purpose.

## R5. Constants Consolidation

**Decision**: Consolidate all magic numbers into `constants.py` (backend) and a new `frontend/src/constants.ts` (frontend), organized by domain.

**Backend constants to consolidate**:

| Constant | Current Location | New Name |
|----------|-----------------|----------|
| `MAX_RETRIES = 3` | `github_projects.py` | `GITHUB_API_MAX_RETRIES` |
| `INITIAL_BACKOFF_SECONDS = 1` | `github_projects.py` | `GITHUB_API_INITIAL_BACKOFF_SECONDS` |
| `MAX_BACKOFF_SECONDS = 30` | `github_projects.py` | `GITHUB_API_MAX_BACKOFF_SECONDS` |
| `ASSIGNMENT_GRACE_PERIOD_SECONDS = 120` | `copilot_polling.py` | `POLLING_ASSIGNMENT_GRACE_SECONDS` |
| `RECOVERY_COOLDOWN_SECONDS = 300` | `copilot_polling.py` | `POLLING_RECOVERY_COOLDOWN_SECONDS` |
| `MAX_DELIVERY_IDS = 1000` | `webhooks.py` | `WEBHOOK_MAX_DELIVERY_IDS` |
| Dedup set sizes (1000, 500, 200, 100) | `copilot_polling.py` | `POLLING_*_MAX_SIZE`, `POLLING_*_PRUNE_SIZE` |
| `asyncio.sleep(2)` | `copilot_polling.py` | `POLLING_STATUS_TRANSITION_DELAY` |
| `"2022-11-28"` | `github_projects.py` (20+ times) | `GITHUB_API_VERSION` |

**Frontend constants to consolidate**:

| Constant | Current Location | New Name |
|----------|-----------------|----------|
| `5000` ms | `useRealTimeSync.ts` | `WS_POLLING_FALLBACK_MS` |
| `15000` ms | `useProjectBoard.ts` | `BOARD_POLL_INTERVAL_MS` |
| `3` | `useRealTimeSync.ts` | `WS_MAX_RECONNECT_ATTEMPTS` |
| `5 * 60 * 1000` ms | `useAuth.ts`, `useProjects.ts`, `useSettings.ts`, `useProjectBoard.ts` | `AUTH_STALE_TIME_MS` |
| `60 * 1000` ms | `useProjects.ts` | `TASKS_STALE_TIME_MS` |
| `10 * 1000` ms | `useChat.ts`, `useProjectBoard.ts` | `DATA_STALE_TIME_MS` |
| `10 * 60 * 1000` ms | `useChat.ts` | `CHAT_EXPIRES_OFFSET_MS` |

## R6. Frontend API Client Enhancement

**Decision**: Enhance the existing `api.ts` `request<T>()` function and migrate raw `fetch()` calls from `useWorkflow.ts` (4 calls) and `useAgentConfig.ts` (1 call) into centralized API functions.

**Key finding**: The frontend uses cookie-based authentication (`credentials: 'include'`), NOT bearer tokens. The session cookie is set by the backend's `set_session_cookie`. No token management is needed in the frontend — `fetch` with `credentials: 'include'` handles it.

**Changes**:
1. Add new API functions in `api.ts` for workflow and agent config operations
2. Add centralized error interceptor to `request<T>()`: on 401, clear auth cache and redirect
3. Add network error handling (catch `TypeError` from failed `fetch`)
4. Migrate all raw `fetch()` calls in `useWorkflow.ts` and `useAgentConfig.ts` to use the shared client

**Alternatives considered**:
- *Replace with axios* — Rejected: Adding a dependency for marginal benefit.
- *Full API client class* — Rejected: Function-based approach is simpler and matches existing patterns.

## R7. WebSocket/Polling Unification

**Decision**: Make `useRealTimeSync` the single source of real-time updates. Remove the independent 15s `refetchInterval` from `useProjectBoard`.

**Current overlap**: `useProjectBoard` has `refetchInterval: 15000` that runs independently of `useRealTimeSync`'s WebSocket. When WS is connected, the board gets double-refreshed.

**Change**:
1. Remove `refetchInterval` from `useProjectBoard`
2. `useRealTimeSync` invalidates board-related query keys on WS events (already implemented)
3. WS disconnect activates polling fallback (already implemented, 5s interval)
4. WS reconnect stops polling (already implemented)

## R8. sessionStorage State Persistence

**Decision**: Create `sessionState.ts` with typed get/set wrappers around `sessionStorage`. Persist selected project ID and board filters. Read on mount.

**Implementation**:
- `getPersistedState<T>(key): T | null` + `setPersistedState<T>(key, value): void` + `clearPersistedState(key): void`
- Hooks write on state change; components read on mount
- Uses `sessionStorage` (per-tab, clears on tab close, no cross-tab leakage) per spec clarification

## R9. Error Boundary

**Decision**: Single `ErrorBoundary` React class component in `components/common/ErrorBoundary.tsx`. Wrap main content in `App.tsx`. Friendly fallback with "Reload" button.

**Alternatives considered**:
- *react-error-boundary library* — Rejected: Standard React class component API is sufficient for this use case.

## R10. Test Coverage Strategy

**Decision**: Add unit tests for 4 untested backend services and 6 untested frontend hooks using existing test infrastructure.

**Backend** (pytest + pytest-asyncio): Follow patterns from existing test files (`test_github_projects.py`, `test_ai_agent.py`) — mock external dependencies, test core logic.

Target services: `completion_providers.py`, `session_store.py`, `settings_store.py`, `agent_tracking.py`

**Frontend** (Vitest + @testing-library/react): Follow patterns from existing test files (`useAuth.test.tsx`, `useProjects.test.tsx`, `useRealTimeSync.test.tsx`) — mock API module, test hook state transitions.

Target hooks: `useSettings`, `useWorkflow`, `useAgentConfig`, `useChat`, `useProjectBoard`, `useAppTheme`

**Note**: `test_workflow_orchestrator.py` already exists. Only the 4 services above need new test files.

## R11. `workflow_orchestrator.py` Reduction

**Decision**: At 2,049 lines, this file will reduce after extracting shared patterns (pipeline state helpers, cache keys) but may remain over 500 lines. If substantially over, split following the same package pattern. The orchestrator's complexity is inherent (multi-step workflow coordination), so a module at ~800 lines with clear single responsibility is acceptable per the spec's Assumptions section ("~500 lines is a guideline, not a hard rule — a module may slightly exceed this if splitting further would harm cohesion").
