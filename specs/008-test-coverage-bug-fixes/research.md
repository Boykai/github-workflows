# Research: Test Coverage & Bug Fixes

**Feature**: `008-test-coverage-bug-fixes`  
**Date**: 2026-02-20  
**Purpose**: Resolve all Technical Context unknowns and establish best practices for test implementation.

---

## R-001: Backend API Route Testing Strategy

**Decision**: Use `httpx.AsyncClient` with FastAPI's `TestClient` pattern via `app.router`.

**Rationale**: The backend has no existing API route test pattern. FastAPI's recommended approach is `httpx.AsyncClient` with `ASGITransport(app=app)`, which provides full async support and tests the real ASGI stack (middleware, exception handlers, dependency overrides). This is preferred over `TestClient` (which uses `anyio`) because the project already uses `pytest-asyncio` in auto mode.

**Alternatives considered**:
- `TestClient` (sync, uses anyio under the hood) — rejected because all route handlers are async and the project uses `asyncio_mode=auto`
- Direct function calls bypassing FastAPI — rejected because it skips middleware, dependency injection, and HTTP serialization

**Implementation**:
```python
# conftest.py fixture pattern
@pytest.fixture
async def client(mock_db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_session_dep] = lambda: mock_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

---

## R-002: Database Mocking Strategy

**Decision**: Use real in-memory SQLite (`aiosqlite.connect(":memory:")`) with migrations applied, not mock objects.

**Rationale**: The `session_store.py`, `settings_store.py`, and `database.py` modules issue raw SQL against an `aiosqlite.Connection`. Mocking the Connection would require replicating SQL behavior, which is brittle and doesn't catch SQL bugs. In-memory SQLite is fast, isolated per test, and validates real SQL queries.

**Alternatives considered**:
- `unittest.mock.AsyncMock` for Connection — rejected because it can't validate SQL correctness
- Shared file-based test database — rejected because it breaks test isolation

**Implementation**:
```python
@pytest.fixture
async def mock_db():
    async with aiosqlite.connect(":memory:") as db:
        db.row_factory = aiosqlite.Row
        # Run migrations to create schema
        migrations_dir = Path(__file__).parent.parent / "src" / "migrations"
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            await db.executescript(sql_file.read_text())
        await db.commit()
        yield db
```

---

## R-003: Completion Providers Testing Approach

**Decision**: Mock the SDK clients (`CopilotClient`, `AzureOpenAI`, `ChatCompletionsClient`) at the import boundary and test the provider logic (token caching, session management, error handling).

**Rationale**: `completion_providers.py` is the most complex untested module (302 lines, 3 provider implementations with async SDK calls). The Copilot SDK uses an event-based authentication model that cannot be replicated without the real service. Testing should focus on: factory function dispatch, provider initialization, error handling, and message formatting.

**Alternatives considered**:
- Skip testing this module — rejected because it would make the 85% target harder to reach and leave critical AI integration untested
- Integration test with real API keys — rejected per FR-015 (no network access)

---

## R-004: Frontend Component Testing Strategy

**Decision**: Use `render()` + DOM assertions for high-value components; skip snapshot tests. Focus on user interactions and conditional rendering, not visual output.

**Rationale**: The 28 untested components total ~3,211 lines. Testing every component at the same depth isn't practical for 85% coverage. Priority order:
1. Components with conditional logic (modals, forms, error states) — full test with user events
2. Container components (ProjectBoard, ChatInterface, GlobalSettings) — test data flow and child rendering
3. Presentational components (MessageBubble, TaskCard, IssueCard) — test prop rendering and edge cases

**Alternatives considered**:
- Snapshot testing — rejected because snapshots are brittle, catch irrelevant changes, and don't validate behavior
- E2E tests via Playwright — rejected per scope (unit/component tests are primary vehicle)

---

## R-005: Coverage Threshold Configuration

**Decision**: Configure `fail_under = 85` (aggregate) in both toolchains. Use per-file configuration where supported.

**Rationale**: Both pytest-cov and vitest/v8 support aggregate thresholds natively. Per-file 70% minimum is supported by vitest via `coverage.thresholds.perFile`, and by pytest-cov with custom configuration.

**Backend (pyproject.toml)**:
```toml
[tool.coverage.run]
source = ["src"]
omit = ["src/__pycache__/*", "src/migrations/*"]

[tool.coverage.report]
fail_under = 85
show_missing = true
```

**Frontend (vitest.config.ts)**:
```typescript
coverage: {
  provider: 'v8',
  include: ['src/**/*.{ts,tsx}'],
  exclude: ['src/test/**', 'src/**/*.test.*', 'src/vite-env.d.ts', 'src/main.tsx'],
  thresholds: {
    lines: 85,
    perFile: true,      // enforces per-file checking
    // Per-file minimum is set via the lines threshold on perFile
  }
}
```

Note: vitest's `perFile: true` applies the same threshold to each file. Since we need aggregate 85% but per-file 70%, we'll set the global threshold to 70 with `perFile: true` and rely on aggregate check separately, or use vitest's `100` option with `watermarks`. Research shows the simplest approach is: set `thresholds.lines = 85` globally (aggregate), and add a custom reporter or CI step for per-file 70%. For MVP, aggregate 85% is the enforced gate.

---

## R-006: Shared Test Utility Patterns

**Decision**: Backend uses `conftest.py` fixtures (pytest auto-discovery); frontend uses a `test-utils.tsx` module alongside `setup.ts`.

**Rationale**: Following existing project conventions. pytest fixtures are the idiomatic way to share setup in Python. React Testing Library recommends a custom `render` wrapper that includes providers.

**Backend fixtures to add** (in `conftest.py`):
- `mock_db` — in-memory SQLite with migrations
- `client` — `httpx.AsyncClient` with dependency overrides
- `mock_github_service` — `AsyncMock` of `GitHubProjectsService`
- `mock_ai_agent` — `AsyncMock` of AI agent service
- `mock_settings` — `Settings` instance with test defaults

**Frontend utilities to add** (in `test-utils.tsx`):
- `renderWithProviders()` — wraps component in `QueryClientProvider` + `MemoryRouter`
- `createMockApi()` — returns typed mock of all api module exports
- `createMockWebSocket()` — factory for mock WebSocket instances (already partially in setup.ts)

---

## R-007: Test File Organization

**Decision**: Backend tests go in `tests/unit/test_<module>.py`. Frontend tests are co-located as `<Component>.test.tsx` next to the source file.

**Rationale**: Follows existing patterns in the project. Backend already has 10 unit test files in `tests/unit/`. Frontend's 3 existing hook tests are co-located as `useAuth.test.tsx`, etc.

**New backend test files** (13 total):
- `tests/unit/test_agent_tracking.py`
- `tests/unit/test_completion_providers.py`
- `tests/unit/test_database.py`
- `tests/unit/test_session_store.py`
- `tests/unit/test_settings_store.py`
- `tests/unit/test_api_auth.py`
- `tests/unit/test_api_chat.py`
- `tests/unit/test_api_projects.py`
- `tests/unit/test_api_settings.py`
- `tests/unit/test_api_tasks.py`
- `tests/unit/test_api_workflow.py`
- `tests/unit/test_prompts.py`
- `tests/unit/test_config.py`

**New frontend test files** (priority-ordered, minimum set for 85%):
- `src/services/api.test.ts`
- `src/hooks/useAgentConfig.test.tsx`
- `src/hooks/useAppTheme.test.tsx`
- `src/hooks/useChat.test.tsx`
- `src/hooks/useProjectBoard.test.tsx`
- `src/hooks/useSettings.test.tsx`
- `src/hooks/useWorkflow.test.tsx`
- `src/components/auth/LoginButton.test.tsx`
- `src/components/board/ProjectBoard.test.tsx`
- `src/components/board/IssueCard.test.tsx`
- `src/components/chat/ChatInterface.test.tsx`
- `src/components/chat/MessageBubble.test.tsx`
- `src/components/common/ErrorDisplay.test.tsx`
- `src/components/settings/GlobalSettings.test.tsx`
- `src/components/sidebar/ProjectSidebar.test.tsx`
- `src/pages/ProjectBoardPage.test.tsx`
- `src/pages/SettingsPage.test.tsx`

Additional component tests added as needed to reach 85%.
