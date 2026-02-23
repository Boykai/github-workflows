# Research: Codebase Cleanup & Refactor

**Feature**: `009-codebase-cleanup-refactor` | **Date**: 2026-02-22

## R1: Python Module Decomposition Strategy

### Decision
Use the **"Extract & Re-export" pattern** — convert large files into packages, move code into sub-modules, and re-export all public names from `__init__.py` for backward compatibility.

### Rationale
- Existing import sites (14+ for `github_projects`, 10+ for `copilot_polling`, 5+ for `workflow_orchestrator`) continue working unchanged.
- `__init__.py` re-exports with explicit `__all__` make the public surface lintable and self-documenting.
- No blast radius on tests or other modules during decomposition.

### Decomposition Targets

| File | Lines | Proposed Sub-modules |
|------|-------|---------------------|
| `github_projects.py` | 4,448 | `github_projects/service.py` (main class + singleton), `github_projects/graphql.py` (queries + fragments), `github_projects/issue_ops.py` (create/update issue), `github_projects/pr_ops.py` (PR detection, completion), `github_projects/board_ops.py` (board data transform), `github_projects/copilot_assignment.py` (agent assignment) |
| `copilot_polling.py` | 4,044 | `copilot_polling/state.py` (global state dicts/sets), `copilot_polling/polling_loop.py` (start/stop/poll lifecycle), `copilot_polling/agent_output.py` (extract + post agent outputs), `copilot_polling/pipeline.py` (advance pipeline, transition logic), `copilot_polling/recovery.py` (stalled issue recovery, cooldown), `copilot_polling/completion.py` (PR completion detection) |
| `workflow_orchestrator.py` | 2,048 | `workflow_orchestrator/models.py` (WorkflowContext, PipelineState, WorkflowState data classes), `workflow_orchestrator/config.py` (workflow config load/persist), `workflow_orchestrator/transitions.py` (status transitions, review logic), `workflow_orchestrator/orchestrator.py` (main WorkflowOrchestrator class) |

### Alternatives Considered
- **In-place sibling module splitting** — Rejected: breaks all existing import paths immediately.
- **Facade pattern** — Unnecessarily complex; `__init__.py` achieves the same natively.
- **Monorepo-style separate packages** — Over-engineered for internal modules.

---

## R2: Circular Import Resolution (`copilot_polling` ↔ `workflow_orchestrator`)

### Decision
Break the circular dependency using three techniques:
1. **Extract shared data classes** (`WorkflowContext`, `PipelineState`, `WorkflowState`) to `workflow_orchestrator/models.py` — both modules import from this leaf module.
2. **`TYPE_CHECKING`-guarded imports** for type annotations only.
3. **Runtime lazy imports** inside function bodies for the remaining function references.

### Rationale
- The codebase already uses `TYPE_CHECKING` guards in `workflow_orchestrator.py` (lines 22–24).
- `copilot_polling.py` imports 16 names from `workflow_orchestrator` at module level (line 36). The shared data classes account for ~6 of those; extracting them to a leaf module breaks the primary cycle.
- `workflow_orchestrator.py` imports from `copilot_polling` only inside 4 function bodies (lines 1331, 1456, 1471, 1940) — these are already lazy and safe.

### Alternatives Considered
- **Merging both modules** — Rejected: creates a 6,000+ line monolith.
- **Dependency inversion (pass callables)** — Higher refactor cost for 16 imported names.
- **Intermediary bridge module** — Overly abstract; shared models + lazy imports is simpler.

---

## R3: `datetime.utcnow()` → `datetime.now(UTC)` Migration

### Decision
Replace all 30+ occurrences of `datetime.utcnow()` with `datetime.now(UTC)` using `from datetime import UTC`. Introduce a helper `utcnow()` in a shared module for a single chokepoint.

### Rationale
- `datetime.utcnow()` is deprecated since Python 3.12 and will be removed.
- `datetime.now(UTC)` returns an **aware** datetime (`tzinfo=UTC`) vs. **naive** from `utcnow()`.
- Key difference: `.isoformat()` output includes `+00:00` suffix with aware datetimes.
- `requires-python = ">=3.11"` confirms `UTC` sentinel is available.
- **Must migrate all 32 sites atomically** — mixing naive and aware datetimes raises `TypeError` on comparison.

### Compatibility

| Library | Impact |
|---------|--------|
| Pydantic 2.x | Fully supports aware datetimes; serializes with timezone offset |
| httpx | No datetime interaction — no impact |
| aiosqlite | Stores TEXT; aware datetimes serialize with `+00:00`; `fromisoformat()` handles both since Python 3.11 |
| python-jose (JWT) | Uses Unix timestamps (integers) — no impact |

### Migration Approach
1. Add helper: `def utcnow() -> datetime: return datetime.now(UTC)` in `backend/src/utils.py` or `constants.py`
2. Replace all `datetime.utcnow()` → `utcnow()` in one atomic change
3. Single grep-friendly chokepoint for future changes

### Alternatives Considered
- **Direct `datetime.now(UTC)` everywhere** — Fine but more characters and no single chokepoint.
- **Suppress deprecation warning** — Rejected: deprecated API will be removed.

---

## R4: FastAPI Dependency Injection for Singleton Services

### Decision
Use **`lifespan` + `app.state`** for service instantiation, accessed via `Depends()` functions in a dedicated `dependencies.py` module.

### Rationale
- The codebase already has a `lifespan` handler in `main.py` that initializes the database on `app.state.db` — extend this existing pattern.
- `app.dependency_overrides` enables clean test mocking without import-path fragility.
- Async service initialization (e.g., `httpx.AsyncClient` lifecycle) fits naturally in the lifespan context manager.

### Implementation Pattern
```python
# main.py lifespan (extend existing)
@asynccontextmanager
async def lifespan(app: FastAPI):
    db = await init_database()
    app.state.db = db
    app.state.github_service = GitHubProjectsService()
    app.state.connection_manager = ConnectionManager()
    yield
    await close_database()

# dependencies.py (new file)
def get_github_service(request: Request) -> GitHubProjectsService:
    return request.app.state.github_service
```

### Migration Path
Keep module-level globals as thin wrappers during transition for backward compatibility. Remove once all callers use DI.

### Alternatives Considered
- **`functools.lru_cache` on factory** — Awkward for async init; not testable via `dependency_overrides`.
- **Module-level globals (current)** — No lifecycle control; import-time side effects; harder to test.

---

## R5: React Error Boundary Pattern

### Decision
Custom class component in `components/common/ErrorBoundary.tsx` — no external library dependency. Wrap with TanStack Query's `QueryErrorResetBoundary`.

### Rationale
- React 18 still requires class components for `componentDidCatch` / `getDerivedStateFromError` — no hooks API exists.
- The app has no UI component library; a 40-line class component avoids the `react-error-boundary` package dependency.
- `QueryErrorResetBoundary` from TanStack Query resets failed queries when the error boundary resets, preventing stale error states.

### Integration Pattern
```tsx
<QueryClientProvider client={queryClient}>
  <QueryErrorResetBoundary>
    {({ reset }) => (
      <ErrorBoundary onReset={reset}>
        <AppContent />
      </ErrorBoundary>
    )}
  </QueryErrorResetBoundary>
</QueryClientProvider>
```

### Note on `throwOnError`
TanStack Query v5 defaults `throwOnError: false`. For errors to propagate to the boundary, either set it globally or per-query. Recommendation: keep default `false` and let individual queries opt in — the error boundary primarily catches rendering errors and explicitly-thrown query errors.

### Alternatives Considered
- **`react-error-boundary` library** — Adds a dependency for a 40-line component.
- **Multiple granular boundaries per route** — Overkill for current app size; can be added later.

---

## R6: TanStack Query Migration for Raw Fetch Hooks

### Decision
Migrate `useWorkflow` and `useAvailableAgents` from raw `fetch` + `useState`/`useEffect` to `useQuery`/`useMutation` with the existing centralized API client.

### Rationale
- Every other hook already uses TanStack Query (`useAuth`, `useProjects`, `useChat`, `useSettings`, `useProjectBoard`).
- TanStack Query eliminates manual `isLoading`/`error`/`data` state management (4 x `useState` calls per hook).
- Cache integration: `updateConfig` mutation can `invalidateQueries(['workflow', 'config'])`.
- `useAvailableAgents` with `staleTime: Infinity` replaces the manual `useRef` cache.

### Migration Map

**`useWorkflow` (4 operations):**
| Current Operation | TanStack Pattern |
|-------------------|-----------------|
| `getConfig` (GET) | `useQuery` with `enabled: false` + `refetch()` |
| `updateConfig` (PUT) | `useMutation` + `invalidateQueries` |
| `confirmRecommendation` (POST) | `useMutation` |
| `rejectRecommendation` (POST) | `useMutation` |

**`useAvailableAgents` (1 operation):**
| Current | TanStack Pattern |
|---------|-----------------|
| Fetch once per `projectId`, cache in `useRef` | `useQuery` with `staleTime: Infinity`, `gcTime: 10 * 60 * 1000` |

### API Client Integration
All migrated hooks should use the existing `request<T>()` wrapper from `services/api.ts` instead of raw `fetch()`, gaining consistent error handling, `credentials: 'include'`, and content-type headers.

### Alternatives Considered
- **Keep raw `fetch` for these two hooks** — Rejected: inconsistency with rest of codebase.
- **`staleTime: 30min` for agents** — Acceptable variant if agent lists change during sessions.

---

## R7: Retry/Backoff Scoping for HTTP Calls

### Decision
Apply retry logic to **read-only operations (GET, GraphQL queries) and idempotent writes** only. Non-idempotent mutations (POST create issue, POST merge PR) fail fast without retry.

### Rationale
- Clarified in spec session 2026-02-22: retrying non-idempotent mutations risks duplicate side effects (e.g., double issue creation).
- `github_projects.py` already has `_request_with_retry()` but only uses it for some REST calls. GraphQL queries via `_graphql()` call `self._client.post()` directly with no retry.
- Safe to retry: all GET endpoints, GraphQL queries (read-only), PUT/PATCH updates (idempotent).
- Unsafe to retry: POST create-issue, POST merge-PR, POST assign-copilot.

### Implementation
Classify HTTP methods/operations at the call site:
```python
async def _request_with_retry(self, method, url, *, idempotent=True, **kwargs):
    if not idempotent:
        return await self._client.request(method, url, **kwargs)
    # existing retry logic...
```

### Alternatives Considered
- **Retry everything with idempotency keys** — Adds implementation complexity; GitHub API doesn't support idempotency keys on all endpoints.
- **No retry at all** — Rejected: transient failures on reads are common with GitHub API rate limits.
