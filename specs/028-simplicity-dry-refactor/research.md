# Research: Simplicity & DRY Refactoring Across Backend and Frontend

**Feature**: 028-simplicity-dry-refactor | **Date**: 2026-03-07

## R1: Repository Resolution Consolidation Strategy

**Decision**: Replace all duplicate repository resolution implementations with the canonical `resolve_repository()` in `backend/src/utils.py` (lines 145–187).

**Rationale**: The canonical function already implements the correct 3-step fallback (project items → workflow config → default repository) and raises `ValidationError` on failure. The duplicate `_get_repository_info()` in `api/workflow.py` (line 86) is a sync helper that attempts a different resolution strategy by parsing cached project data. The canonical async version is more reliable and consistent.

**Alternatives Considered**:
- **Keep both, add adapter**: Rejected — maintaining two resolution paths creates divergence risk and doubles test surface.
- **Merge logic from both into a new function**: Rejected — the canonical function already handles all known cases; the workflow variant adds no additional capability.

**Findings**:
- `_get_repository_info()` exists only in `api/workflow.py` (line 86) with 5 test references in `test_api_workflow.py`
- The canonical `resolve_repository()` is already used by `api/chat.py` (via `_resolve_repository` wrapper)
- All callers pass `session.access_token` and `session.selected_project_id` — the canonical signature matches
- Tests that mock `_get_repository_info` must be updated to mock `resolve_repository` instead

---

## R2: Error Handling Helper Adoption Strategy

**Decision**: Wire up the existing `handle_service_error()` (logging_utils.py line 241) and `safe_error_response()` (line 215) to replace inline catch→log→raise patterns. Do not modify the helper signatures.

**Rationale**: Both helpers are already implemented and tested. `handle_service_error()` centralizes the pattern of logging an exception and raising a structured `AppException` subclass with a safe user-facing message. `safe_error_response()` returns a generic string suitable for JSON responses. The helpers exist but are unused in 5+ API modules.

**Alternatives Considered**:
- **Middleware-based error handling**: Rejected — too broad; some endpoints need specific fallback logic (e.g., stale cache on rate limit). Middleware cannot distinguish these cases.
- **Decorator-based error wrapping**: Rejected — adds implicit behavior that's harder to debug; explicit helper calls are more readable per Constitution Principle V (Simplicity).

**Findings**:
- `handle_service_error(exc, operation, error_cls=None)` logs exception, raises `AppException` subclass (default: `GitHubAPIError`)
- `safe_error_response(exc, operation)` logs exception, returns generic message string
- Target adoption: `api/auth.py` (2 catch blocks), `api/workflow.py` (3+ catch blocks), `api/projects.py` (rate-limit-aware catch), `api/board.py` (1 catch block)
- `api/projects.py` has complex error handling with stale-cache fallback — this should use `handle_service_error()` for the simple path but keep rate-limit-specific logic inline

---

## R3: Session Validation Dependency Design

**Decision**: Add `require_selected_project(session: UserSession) -> str` to `dependencies.py` as a FastAPI dependency. It validates `session.selected_project_id` is not None/empty and returns the project ID string.

**Rationale**: 12 inline guard clauses across 4 API files (`chat.py`, `workflow.py`, `tasks.py`, `chores.py`) all check `if not session.selected_project_id: raise ValidationError(...)`. Extracting this to a dependency eliminates duplication and ensures consistent error messages.

**Alternatives Considered**:
- **Middleware that auto-injects project_id**: Rejected — not all endpoints require a selected project (e.g., auth, health, project listing). Middleware would need an exclusion list, adding complexity.
- **Add to UserSession model as a method**: Rejected — model should not raise HTTP-level errors; separation of concerns.

**Findings**:
- Guard messages vary: "No project selected", "Please select a project first", "No project selected. Please select a project first." — standardize to "No project selected. Please select a project first."
- `tasks.py` has a special case: it accepts an explicit `project_id` parameter and only falls back to session — the dependency can still be used with a conditional override
- The dependency should be a plain function (not a FastAPI `Depends()` class) to match the existing pattern in `dependencies.py`

---

## R4: Generic Cache Wrapper Design

**Decision**: Add `cached_fetch(cache, cache_key, fetch_fn, refresh=False, ttl_seconds=300, *args, **kwargs)` to `services/cache.py`. It encapsulates the check → get → set pattern with optional stale-data fallback on fetch failure.

**Rationale**: 3+ API modules (`projects.py`, `board.py`, `chat.py`) repeat the same pattern: check cache → return if hit → fetch from service → store in cache → on error, try stale cache. This is 15–25 lines per instance that can be reduced to a single function call.

**Alternatives Considered**:
- **Decorator-based caching (@cached)**: Rejected — the cache key depends on runtime parameters (user ID, project ID) and the refresh flag is passed per-request. A decorator would need complex parameter extraction.
- **Integrate caching into the service layer**: Rejected — caching is a presentation/API concern, not a domain concern. The service should remain cache-unaware for testability.

**Findings**:
- Current cache patterns use `cache.get()`, `cache.set()`, and `cache.get_stale()` from `InMemoryCache`
- TTL values vary: projects use default, board uses 300s explicit — the wrapper should accept a `ttl_seconds` parameter
- Rate-limit-aware error handling in `projects.py` is a special case — the wrapper should support an optional `on_error` callback or the caller should handle the outer try/except
- The wrapper should return the cached/fetched value directly, not wrap it in a response model

---

## R5: Service Decomposition Module Boundaries

**Decision**: Split `service.py` (4,913 lines, 79 methods) into 8 modules based on domain responsibility. Use composition: each module receives a `client` reference (the HTTP/GraphQL executor) rather than inheriting from a base class.

**Rationale**: The current monolith mixes HTTP client management, project listing, issue CRUD, PR operations, Copilot integration, field management, board views, and repository file operations. Each domain area has distinct dependencies and change frequencies.

**Alternatives Considered**:
- **Inheritance hierarchy (BaseService → subclasses)**: Rejected — creates coupling between unrelated domains; changes to base class affect all subclasses. Composition is explicitly confirmed in the issue.
- **4 larger modules instead of 8**: Rejected — would still produce modules >1,000 LOC. The 800-LOC target requires finer granularity.
- **Microservices/separate processes**: Rejected — out of scope; this is an internal refactoring, not an architectural change.

**Findings**:
- **client.py** (~400 LOC): `__init__`, `_rest`, `_rest_response`, `rest_request`, `_graphql`, `_with_fallback`, `close`, `get_last_rate_limit`, `clear_last_rate_limit`, `clear_cycle_cache`, `_invalidate_cycle_cache`
- **projects.py** (~600 LOC): `list_user_projects`, `list_org_projects`, `_parse_projects`, `get_project_items`, `list_board_projects`, `get_board_data`, `get_project_field_options`, `update_project_item_field`, `move_project_item`, `get_project_repository`
- **issues.py** (~700 LOC): `create_issue`, `update_issue`, `get_issue_details`, `add_issue_to_project`, `remove_issue_from_project`, `close_issue`, `reopen_issue`, `add_labels_to_issue`, `list_issue_comments`, `create_issue_comment`, `update_issue_comment`, `get_issue_timeline`
- **pull_requests.py** (~500 LOC): `list_pull_requests`, `get_pull_request`, `create_pull_request`, `merge_pull_request`, `list_pr_reviews`, `list_pr_files`
- **copilot.py** (~500 LOC): `is_copilot_author`, `is_copilot_swe_agent`, `list_available_agents`, `get_copilot_metrics`, plus Copilot-specific methods
- **fields.py** (~400 LOC): `get_project_fields`, `get_field_values`, `update_field_value`, `create_field`, `delete_field`
- **board.py** (~500 LOC): `get_board_data`, `get_board_columns`, `get_board_items`, board view transformations
- **repository.py** (~700 LOC): `get_repository_info`, `get_directory_contents`, `get_file_content`, `get_file_content_from_ref`, `create_branch`, `get_branch_head_oid`, `commit_files`, `_detect_changes`

**Facade Strategy**: `__init__.py` will import and re-export `GitHubProjectsService` (which becomes a thin composition class) and `github_projects_service` singleton. All 15+ existing import sites continue to work unchanged.

---

## R6: Initialization Consolidation Path

**Decision**: Consolidate all service initialization into `lifespan()` → `app.state` → `Depends(get_xxx_service)`. Remove the module-level singleton from `service.py` and the module-level `github_auth_service` from `github_auth.py`. Keep the `InMemoryCache` singleton as-is (it's stateless and safe).

**Rationale**: Three competing patterns create ambiguity: (1) module-level `github_projects_service = GitHubProjectsService()` at import time, (2) lazy fallback in `GitHubProjectsService.__init__` for `client_factory`, (3) lifespan registration on `app.state`. Consolidating to pattern (3) makes the lifecycle explicit and testable.

**Alternatives Considered**:
- **Keep module-level singletons with deprecation warnings**: Rejected — doesn't solve the core problem of multiple instances; deprecation warnings create noise.
- **Dependency injection container (e.g., dependency-injector library)**: Rejected — adds a third-party dependency for a problem solvable with FastAPI's built-in DI. Violates Constitution Principle V (Simplicity).

**Findings**:
- Background tasks (`copilot_polling`, `signal_bridge`, `agent_creator`) import `github_projects_service` directly because they lack request context — these need access to `app.state` via the app reference passed to background tasks
- The `dependencies.py` fallback pattern (`getattr(request.app.state, "github_service", None)` → module-level import) already exists and provides the migration bridge
- During the transition window, the facade ensures both `app.state.github_service` and the module-level import resolve to the same instance
- `connection_manager` and `cache` singletons are stateless/simple enough to remain as module-level globals

---

## R7: Frontend CRUD Hook Factory Design

**Decision**: Create `useCrudResource<T>(config)` in `hooks/useCrudResource.ts` that generates `useList`, `useCreate`, `useUpdate`, `useDelete` hooks from a configuration object specifying API methods, query keys, and stale times.

**Rationale**: `useAgents.ts` (89 lines) and `useChores.ts` (120 lines) share ~90% of their structure: TanStack Query setup, query key definitions, CRUD mutations with cache invalidation. A factory eliminates this duplication while preserving type safety.

**Alternatives Considered**:
- **Shared base hook with overrides**: Rejected — TypeScript generics make a factory pattern cleaner than hook inheritance; base hooks require awkward forwarding of all parameters.
- **Code generation from schema**: Rejected — over-engineering for 2–3 resource types; a runtime factory is simpler and more maintainable.

**Findings**:
- Both hooks use `useQuery` with `enabled: !!projectId`, `staleTime` from constants, and `queryKey` arrays
- Both hooks use `useMutation` with `onSuccess` that calls `queryClient.invalidateQueries`
- `useAgents.ts` has 6 exports; `useChores.ts` has 7 exports — the factory should support optional extra hooks via a configuration extension point
- The factory should accept a `customHooks` map for resource-specific operations (e.g., `useTriggerChore`, `useAgentChat`)

---

## R8: Frontend API Endpoint Factory Design

**Decision**: Create `createApiGroup<T>(basePath, methods)` in `services/api.ts` that generates typed API call functions from a base path and method definitions map.

**Rationale**: 17 API endpoint groups in `api.ts` (915 lines) repeat the same `request<T>(path, options)` pattern. A factory can generate standard CRUD methods from a configuration, reducing the file by ~300 lines.

**Alternatives Considered**:
- **OpenAPI code generation (e.g., openapi-typescript)**: Rejected — requires maintaining an OpenAPI spec file and adds a build step. The backend doesn't currently export an OpenAPI spec in a format suitable for client generation.
- **Class-based API clients**: Rejected — objects with methods are the existing pattern and work well with tree-shaking; classes add unnecessary overhead.

**Findings**:
- Standard methods across groups: `list()`, `get(id)`, `create(data)`, `update(id, data)`, `delete(id)`
- Non-standard methods exist: `authApi.login()` (redirect), `chatApi.sendMessage()` (streaming), `boardApi.getBoardData()` (complex params) — the factory must support custom method definitions alongside standard CRUD
- The factory should produce a plain object (not a class) matching the existing `const xxxApi = { ... }` pattern
- Type safety: the factory should be generic over request/response types per method

---

## R9: ChatInterface Decomposition Strategy

**Decision**: Extract `ChatMessageList` (message rendering + auto-scroll) and `ChatInput` (textarea + command autocomplete + history navigation) from `ChatInterface.tsx` (417 lines). The parent component becomes a layout coordinator.

**Rationale**: ChatInterface mixes three concerns: message display, input handling, and proposal/preview rendering. Extracting the message list and input reduces each component to <200 lines (per SC-011).

**Alternatives Considered**:
- **Extract only ChatInput**: Rejected — message list rendering (auto-scroll, message grouping) is also a distinct concern worth separating.
- **Full decomposition into 5+ components**: Rejected — over-decomposition; the parent already delegates preview rendering to TaskPreview, StatusChangePreview, and IssueRecommendationPreview. Two extractions are sufficient.

**Findings**:
- Message list logic: `useEffect` for auto-scroll, `.map()` over messages, conditional rendering of MessageBubble vs SystemMessage (~100 lines)
- Input logic: textarea state, `useCommands()` hook, `useChatHistory()` hook, keyboard event handlers, send button (~150 lines)
- Parent coordinator: props forwarding, layout (flex column), proposal rendering via existing sub-components (~150 lines)
- The extracted components receive callbacks via props; no new context providers needed

---

## R10: Query Key Registry Strategy

**Decision**: Create `hooks/queryKeys.ts` as a single registry exporting all query key factories. Refactor existing hooks to import keys from the registry instead of defining them locally.

**Rationale**: 9 query key objects are scattered across 7 hook files. A central registry prevents key collisions, enables consistent cache invalidation patterns, and makes it easy to audit all query keys.

**Alternatives Considered**:
- **Enum-based keys**: Rejected — TanStack Query expects arrays, not strings; enum values would need wrapping, adding indirection.
- **Keep keys colocated with hooks**: Rejected — cross-hook invalidation (e.g., agents invalidating chores) requires importing keys from other hooks, creating circular dependency risk.

**Findings**:
- Current key objects: `agentKeys`, `agentToolKeys`, `choreKeys`, `mcpKeys`, `modelKeys`, `pipelineKeys`, `settingsKeys`, `signalKeys`, `toolKeys`
- Key pattern: `{ all: ['domain'] as const, list: (id) => [...all, 'list', id] as const }`
- Migration: export from registry, update hook imports, deprecate local exports
- No key collisions exist currently, but centralization prevents future ones

---

## R11: Shared UI Component Strategy

**Decision**: Create three shared components: `Modal.tsx` (dialog wrapper), `PreviewCard.tsx` (action card with confirm/reject), `ErrorAlert.tsx` (error display). Place in `components/common/`.

**Rationale**: 7 modal components (1,477 lines total) share open/close state management, form submission, and button pairs. 3 preview components share confirm/reject buttons and content summary display. Error alerts are repeated inline across settings and form components.

**Alternatives Considered**:
- **Use Radix UI Dialog directly**: Rejected — already used as a primitive; the shared Modal adds project-specific styling and behavior (loading states, form validation) on top of Radix.
- **Full component library with Storybook**: Rejected — over-engineering for internal use; simple shared components are sufficient per Constitution Principle V.

**Findings**:
- `AddAgentModal.tsx` (~280 lines) and `AddChoreModal.tsx` (~275 lines) are structurally identical: title, form fields, validation, submit/cancel buttons
- `TaskPreview`, `StatusChangePreview`, `IssueRecommendationPreview` share: content area + confirm/reject button pair
- Error patterns: inline `{error && <div className="text-red-500">...</div>}` repeated across forms
- The `Modal.tsx` wrapper should accept `title`, `isOpen`, `onClose`, `children`, `footer` props
- The `PreviewCard.tsx` should accept `title`, `children`, `onConfirm`, `onReject`, `confirmLabel`, `rejectLabel` props

---

## R12: Settings Hook Unification Strategy

**Decision**: Extract a generic `useSettingsHook<T>(apiGet, apiUpdate, queryKey, options?)` from `useSettings.ts` (305 lines). Refactor `useUserSettings`, `useGlobalSettings`, `useProjectSettings` to use it.

**Rationale**: The three settings hooks in `useSettings.ts` share identical structure: `useQuery` for fetch, `useMutation` for update with optimistic updates and cache invalidation. Only the API methods and query keys differ.

**Alternatives Considered**:
- **Merge all settings into a single hook**: Rejected — user, global, and project settings have different lifecycles and enable conditions; merging would complicate the interface.
- **Settings context provider**: Rejected — adds unnecessary re-render scope; individual hooks are more efficient for components that only need one settings type.

**Findings**:
- `useUserSettings()`: `settingsApi.getUserSettings` + `settingsApi.updateUserSettings`, key: `settingsKeys.user`
- `useGlobalSettings()`: `settingsApi.getGlobalSettings` + `settingsApi.updateGlobalSettings`, key: `settingsKeys.global`
- `useProjectSettings(projectId)`: `settingsApi.getProjectSettings` + `settingsApi.updateProjectSettings`, key: `settingsKeys.project(projectId)`, enabled: `!!projectId`
- The generic hook should support: optional `enabled` gate, optimistic updates, and `onSuccess` callback
- Signal-related hooks in `useSettings.ts` do NOT fit this pattern (different shapes) — they remain as-is
