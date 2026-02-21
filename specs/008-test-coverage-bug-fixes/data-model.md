# Data Model: Test Coverage & Bug Fixes

**Feature**: `008-test-coverage-bug-fixes`  
**Date**: 2026-02-20

---

This feature does not introduce new application data models. It introduces **test infrastructure entities** — shared fixtures, mocks, and configuration that enable test authoring.

## Backend Test Fixtures (conftest.py)

### Entity: `mock_db` (pytest fixture)

| Field | Type | Description |
|-------|------|-------------|
| connection | `aiosqlite.Connection` | In-memory SQLite with migrations applied |
| row_factory | `aiosqlite.Row` | Dict-like row access |

**Lifecycle**: Created per-test (function scope). Schema created via migration SQL files. Destroyed after test.

### Entity: `client` (pytest fixture)

| Field | Type | Description |
|-------|------|-------------|
| client | `httpx.AsyncClient` | Async HTTP client bound to test FastAPI app |
| base_url | `str` | `http://test` |

**Lifecycle**: Created per-test. Depends on `mock_db` and `mock_session`. FastAPI dependency overrides injected.

**Dependencies**: `mock_db`, `mock_session` (existing), `mock_settings`

### Entity: `mock_settings` (pytest fixture)

| Field | Type | Description |
|-------|------|-------------|
| settings | `Settings` | Pydantic Settings instance with test defaults |

**Lifecycle**: Created per-test. Overrides `get_settings()` lru_cache.

### Entity: `mock_github_service` (pytest fixture)

| Field | Type | Description |
|-------|------|-------------|
| service | `AsyncMock` | Mock of `GitHubProjectsService` singleton |

**Lifecycle**: Created per-test. Patches the service at import path.

### Entity: `mock_ai_agent` (pytest fixture)

| Field | Type | Description |
|-------|------|-------------|
| agent | `AsyncMock` | Mock of AI agent service |

**Lifecycle**: Created per-test. Patches `get_ai_agent_service()`.

---

## Frontend Test Utilities (test-utils.tsx)

### Entity: `renderWithProviders` (function)

| Parameter | Type | Description |
|-----------|------|-------------|
| ui | `ReactElement` | Component to render |
| options.queryClient | `QueryClient?` | Optional custom QueryClient (default: `retry: false`) |
| options.initialEntries | `string[]?` | Optional MemoryRouter initial entries |

**Returns**: React Testing Library `RenderResult` + `queryClient` for inspection.

### Entity: `createMockApi` (function)

| Returns | Type | Description |
|---------|------|-------------|
| authApi | `MockedObject` | vi.fn() for each method: `getCurrentUser`, `login`, `logout` |
| projectsApi | `MockedObject` | vi.fn() for: `listProjects`, `getProject`, `selectProject`, `getProjectTasks` |
| chatApi | `MockedObject` | vi.fn() for: `getMessages`, `sendMessage`, `clearMessages`, `confirmProposal`, `cancelProposal` |
| boardApi | `MockedObject` | vi.fn() for: `getBoard`, `getProjects` |
| tasksApi | `MockedObject` | vi.fn() for: `createTask`, `updateTaskStatus` |
| settingsApi | `MockedObject` | vi.fn() for: `getUserSettings`, `updateUserSettings`, `getGlobalSettings`, `updateGlobalSettings`, `getProjectSettings`, `updateProjectSettings` |

**Lifecycle**: Created per `vi.mock('@/services/api')` call. Reset via `vi.clearAllMocks()` in `beforeEach`.

---

## Relationships

```
mock_db ──> client (dependency override)
mock_session ──> client (dependency override)
mock_settings ──> client (dependency override)
mock_github_service ──> API route tests (patched in)
mock_ai_agent ──> API route tests (patched in)

createMockApi ──> hook tests (vi.mock)
renderWithProviders ──> component tests (wraps render)
```

## Validation Rules

- `mock_db` MUST have all migrations applied (schema matches production)
- `client` MUST have all dependencies overridden (no real service calls)
- `createMockApi` MUST match the real `api.ts` export shape (type-safe)
- All fixtures/utilities MUST be stateless between tests (no shared mutable state)
