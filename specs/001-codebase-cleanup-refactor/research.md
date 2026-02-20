# Research: Codebase Cleanup & Refactor

**Feature**: `001-codebase-cleanup-refactor` | **Date**: 2026-02-20

## R1: Module Split Strategy for `github_projects.py` (4,448 lines)

**Decision**: Split `GitHubProjectsService` class into a package `backend/src/services/github_projects/` with focused sub-modules grouped by responsibility. The original `github_projects.py` file becomes a thin re-export facade.

**Rationale**: The service class has 57 methods spanning 11 distinct responsibility groups. The largest group (PR Detection & Management) accounts for ~745 lines. Splitting by responsibility keeps each module under ~500 lines while maintaining cohesive units.

**Proposed Sub-modules**:

| Module | Responsibility | Est. Lines | Methods |
|--------|---------------|-----------|---------|
| `_client.py` | HTTP/GraphQL communication, retry logic | ~125 | `__init__`, `close`, `_request_with_retry`, `_graphql` |
| `_projects.py` | Project listing, board data retrieval | ~550 | `list_user_projects`, `list_org_projects`, `_parse_projects`, `get_project_items`, `list_board_projects`, `get_board_data` |
| `_issues.py` | Issue CRUD, project item management | ~293 | `create_draft_item`, `update_item_status`, `create_issue`, `update_issue_body`, `update_issue_state`, `add_issue_to_project`, `assign_issue` |
| `_copilot_assignment.py` | Copilot bot assignment & agent routing | ~623 | `get_copilot_bot_id`, `get_issue_with_comments`, `format_issue_context_as_prompt`, `check_agent_completion_comment`, `unassign_copilot_from_issue`, `is_copilot_assigned_to_issue`, `assign_copilot_to_issue`, `_assign_copilot_rest`, `_assign_copilot_graphql`, `validate_assignee`, `get_repository_owner`, `get_project_repository` |
| `_fields.py` | Project field & metadata management | ~359 | `update_item_status_by_name`, `update_sub_issue_project_status`, `get_project_fields`, `update_project_item_field`, `set_issue_metadata` |
| `_pull_requests.py` | PR detection, merge, review, branch ops | ~745 | `_search_open_prs_for_issue_rest`, `find_existing_pr_for_issue`, `get_linked_pull_requests`, `get_pull_request`, `mark_pr_ready_for_review`, `request_copilot_review`, `merge_pull_request`, `delete_branch`, `update_pr_base`, `link_pull_request_to_issue` |
| `_pr_completion.py` | PR completion detection & timeline events | ~282 | `has_copilot_reviewed_pr`, `get_pr_timeline_events`, `_check_copilot_finished_events`, `check_copilot_pr_completion` |
| `_sub_issues.py` | Sub-issue creation, retrieval, file content | ~500 | `create_sub_issue`, `get_sub_issues`, `tailor_body_for_agent`, `create_issue_comment`, `get_pr_changed_files`, `get_file_content_from_ref`, `poll_project_changes`, `_detect_changes`, `list_available_agents` |
| `__init__.py` | Re-export facade preserving public API | ~60 | Re-exports `GitHubProjectsService` class with all public methods |

**Alternatives Considered**:
- **Mixin classes**: Would keep a single class but split across files using mixins. Rejected because Python mixin patterns are fragile for method resolution order (MRO) and harder to test in isolation.
- **Functional decomposition**: Breaking methods into standalone functions. Rejected because the shared `httpx.AsyncClient` state and retry logic benefit from class encapsulation.

---

## R2: Module Split Strategy for `copilot_polling.py` (3,987 lines)

**Decision**: Split into a package `backend/src/services/copilot_polling/` with focused sub-modules grouped by responsibility. The original `copilot_polling.py` file becomes a thin re-export facade.

**Rationale**: The file contains 29 functions spanning 10 responsibility groups, with the completion & advancement logic being the largest block (~2,200 lines). Functions are module-level (not class-based), making package splitting straightforward.

**Proposed Sub-modules**:

| Module | Responsibility | Est. Lines | Functions |
|--------|---------------|-----------|-----------|
| `_lifecycle.py` | Polling start/stop, status, main loop | ~200 | `poll_for_copilot_completion`, `_poll_loop`, `stop_polling`, `get_polling_status`, `check_issue_for_copilot_completion`, `PollingState` |
| `_issue_tracking.py` | Issue body/comment tracking, sub-issue mapping | ~200 | `_get_sub_issue_number`, `_check_agent_done_on_sub_or_parent`, `_update_issue_tracking`, `_get_tracking_state_from_issue`, `_reconstruct_sub_issue_mappings` |
| `_pipeline.py` | Pipeline state management, reconstruction, advancement | ~500 | `_get_or_reconstruct_pipeline`, `_process_pipeline_completion`, `_reconstruct_pipeline_state`, `_advance_pipeline`, `_transition_after_pipeline_complete` |
| `_agent_outputs.py` | PR output posting, Done! markers | ~570 | `post_agent_outputs_from_pr` |
| `_status_checks.py` | Status-specific issue checks (Steps 1–4) | ~500 | `check_backlog_issues`, `check_ready_issues`, `check_in_progress_issues`, `check_in_review_issues_for_copilot_review`, `ensure_copilot_review_requested` |
| `_pr_completion.py` | Child/main PR completion detection | ~500 | `_merge_child_pr_if_applicable`, `_find_completed_child_pr`, `_check_child_pr_completion`, `_check_main_pr_completion`, `_filter_events_after` |
| `_recovery.py` | Stalled issue recovery, legacy handling | ~500 | `recover_stalled_issues`, `process_in_progress_issue` |
| `__init__.py` | Re-export facade preserving public API | ~40 | Re-exports all public functions |

**Alternatives Considered**:
- **Class-based refactor**: Wrapping functions in a `CopilotPollingService` class. Rejected because the existing code is functional-style with module-level state (`PollingState`), and introducing a class would change the calling convention for all importers.
- **Fewer, larger modules**: Merging related groups (e.g., pipeline + completion). Rejected because the ~500-line target is a spec requirement and logical separation aids understanding.

---

## R3: Duplicate Code Consolidation Strategy

### R3a: Repository Resolution

**Decision**: Extract a shared `resolve_repository(repo_data: dict) -> tuple[str, str]` utility in `backend/src/services/shared/repo_utils.py`.

**Rationale**: Repository owner/name extraction appears in three locations with slight variations:
- `github_projects.py`: `repo_info.get("owner", {}).get("login")` (multiple instances)
- `webhooks.py`: `repo_data.get("owner", {}).get("login", "")` (lines 48, 81-82)
- `copilot_polling.py`: `task_owner = task.repository_owner or owner` (7 instances)

**Alternatives Considered**: Keeping extraction inline but standardizing the pattern. Rejected because a shared utility eliminates the risk of divergent implementations.

### R3b: Polling Initialization

**Decision**: Consolidate polling start logic into a single entry point in the polling lifecycle module.

**Rationale**: Polling is invoked from `projects.py:99`, `workflow.py:38`, and `chat.py:124` with similar patterns. A single `start_polling_if_needed()` function with idempotent checks eliminates duplication.

### R3c: Session Reconstruction

**Decision**: The existing `auth.py:get_current_session()` / `get_session_dep()` pattern is already reasonably centralized via FastAPI dependency injection. The `from_session()` conversion pattern is a model method, not duplication. No major extraction needed — document the canonical pattern.

**Rationale**: Session retrieval uses FastAPI's `Depends()` mechanism consistently. The repeated `UserResponse.from_session(session)` calls are intentional model conversion at the API boundary.

### R3d: Cache Key Construction

**Decision**: Extend the existing `cache.py` helpers and `constants.py` cache key functions to cover all inline cache key construction patterns found in `copilot_polling.py`.

**Rationale**: `constants.py` already has `cache_key_issue_pr()`, `cache_key_agent_output()`, `cache_key_review_requested()` and `cache.py` has `get_cache_key()`, `get_user_projects_cache_key()`, `get_project_items_cache_key()`. The remaining inline patterns in copilot_polling.py (e.g., `f"{task.issue_number}:{current_agent}"`) should be migrated to use these centralized helpers.

---

## R4: Error Handling Strategy

**Decision**: Use the existing `AppException` hierarchy with the global `@app.exception_handler(AppException)` in `main.py`. Add a catch-all handler for unexpected exceptions. Replace direct `HTTPException` raises with domain-specific `AppException` subclasses.

**Rationale**: The exception hierarchy already exists (`AppException`, `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ValidationError`, `GitHubAPIError`, `RateLimitError`). The global handler in `main.py:73-77` already translates these to JSON responses. The gap is: (1) some routes still raise `HTTPException` directly, and (2) there is no catch-all for unexpected exceptions. Adding a generic `Exception` handler ensures consistent 500 responses with server-side-only logging.

**Error Response Structure** (standardized):
```json
{
  "error": "User-safe error message",
  "detail": "Optional additional context (never internal details)",
  "status_code": 500
}
```

**Alternatives Considered**: FastAPI middleware-based approach. Rejected because exception handlers are already in use and more explicit; middleware would add overhead for every request.

---

## R5: Magic Numbers & Constants Consolidation

**Decision**: Extend `backend/src/constants.py` with new named constants for all operational parameters. Group by category.

**Rationale**: The existing `constants.py` (93 lines) already defines cache prefixes, status names, and agent config. The following hardcoded values need to be centralized:

| Value | Current Location | Proposed Constant |
|-------|-----------------|-------------------|
| `60` (polling interval seconds) | copilot_polling.py:815 | `POLLING_INTERVAL_SECONDS` |
| `300` (recovery cooldown) | copilot_polling.py:60 | `RECOVERY_COOLDOWN_SECONDS` (already named) |
| `30.0` (HTTP timeout) | github_projects.py, github_auth.py | `HTTP_TIMEOUT_SECONDS` |
| `5000` (SQLite busy timeout) | database.py, workflow_orchestrator.py | `SQLITE_BUSY_TIMEOUT_MS` |
| `120` (completion provider timeout) | completion_providers.py:84 | `COMPLETION_TIMEOUT_SECONDS` |
| `500` (collection size limit) | copilot_polling.py:211-232 | `MAX_COLLECTION_SIZE` |
| `250` (collection trim count) | copilot_polling.py:211-232 | `COLLECTION_TRIM_SIZE` |
| `3` (retry count) | workflow_orchestrator.py | `MAX_RETRY_ATTEMPTS` |

**Alternatives Considered**: Using `config.py` (Pydantic settings) for all values. Rejected because most values are operational constants (not user-configurable) and belong in `constants.py`. Only values that should vary by environment (like `cache_ttl_seconds`) belong in `config.py`.

---

## R6: Frontend Shared HTTP Client

**Decision**: The existing `frontend/src/services/api.ts` already provides a centralized `request<T>()` function with error handling. The work is to migrate the remaining direct `fetch()` calls (in `useWorkflow.ts` and `useAgentConfig.ts`) to use this client.

**Rationale**: The api.ts client already handles `credentials: 'include'`, base URL configuration, typed responses, and a custom `ApiError` class. Authentication is cookie-based (not bearer token), so "lazy auth lookup" means the client sends cookies automatically. The gaps are: (1) `useWorkflow.ts` makes 4 direct fetch() calls, and (2) `useAgentConfig.ts` makes 2 direct fetch() calls.

**Alternatives Considered**: Creating a new HTTP client (e.g., using axios). Rejected because the existing `api.ts` pattern is well-established and works; the issue is adoption, not architecture.

---

## R7: Frontend Error Boundaries

**Decision**: Create a React `ErrorBoundary` class component wrapping major UI sections. Display a fallback card with error message and Reload button.

**Rationale**: No `ErrorBoundary` components currently exist. React's `componentDidCatch` lifecycle is the only way to catch rendering errors in React 18 (hooks cannot catch render errors). A single reusable `ErrorBoundary` component with configurable fallback UI addresses FR-012.

---

## R8: Frontend State Persistence (sessionStorage)

**Decision**: Use `sessionStorage` for persisting essential navigation state (selected project ID, board context). Implement via a custom `useSessionState` hook that mirrors `useState` but syncs to `sessionStorage`.

**Rationale**: Currently no `sessionStorage` usage exists. The existing `useAppTheme.ts` uses `localStorage` for theme persistence, establishing a precedent. `sessionStorage` is scoped per-tab (as specified) and clears on tab close.

---

## R9: WebSocket-Primary / Polling-Fallback

**Decision**: Modify `useRealTimeSync.ts` to make WebSocket the primary channel and polling the automatic fallback. Currently the hook starts polling immediately then upgrades to WebSocket — this should be reversed so WebSocket connects first and polling only activates on WebSocket failure.

**Rationale**: The existing `useRealTimeSync.ts` (168 lines) already implements both WebSocket and polling with status tracking (`disconnected`, `connecting`, `connected`, `polling`). The change is to the initialization order: attempt WebSocket first, fall back to polling only on connection failure/timeout, and stop polling when WebSocket reconnects.

---

## R10: Test Coverage for Untested Backend Services

**Decision**: Add unit tests following existing patterns (class-based test organization, pytest fixtures from `conftest.py`, pytest-asyncio for async).

**Services needing tests**:
- `completion_providers.py` (302 lines) — test provider initialization, completion waiting, timeout handling
- `session_store.py` (150 lines) — test CRUD operations, expiry, SQLite operations
- `settings_store.py` (413 lines) — test get/set for user, global, and project settings
- `agent_tracking.py` (365 lines) — test agent status tracking, assignment records
- `workflow_orchestrator.py` (1,959 lines) — already has `test_workflow_orchestrator.py` (verify existing coverage)

**Note**: `test_workflow_orchestrator.py` already exists in the unit tests directory. The spec lists it as untested, but a test file exists. Research confirms the file is present; coverage may be incomplete but the file exists.

---

## R11: Test Coverage for Untested Frontend Hooks

**Decision**: Add hook tests following existing patterns (`renderHook()` with `QueryClientProvider` wrapper, `vi.mock()` for API mocking, `waitFor()` for async state).

**Hooks needing tests**:
- `useSettings.ts` (113 lines) — test settings loading, updates, error handling
- `useWorkflow.ts` (163 lines) — test workflow operations, state management
- `useAgentConfig.ts` (237 lines) — test agent config CRUD, validation
- `useChat.ts` (238 lines) — test message sending, history loading, proposals
- `useProjectBoard.ts` (98 lines) — test board data loading, filtering
- `useAppTheme.ts` (63 lines) — test theme toggle, localStorage persistence

**Test pattern** (from existing `useAuth.test.tsx`):
```tsx
const wrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);
const { result } = renderHook(() => useHookUnderTest(), { wrapper });
await waitFor(() => expect(result.current.data).toBeDefined());
```
