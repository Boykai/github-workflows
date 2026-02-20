# Research: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20

## Research Tasks

### 1. Current Coverage Baseline

**Question**: What is the current test coverage for both frontend and backend?

**Finding**: Coverage cannot be measured at planning time (requires running the full test suite with coverage tools). The baseline will be established as the first implementation task.

**Decision**: Use `vitest run --coverage` for frontend and `pytest --cov=src --cov-report=term-missing` for backend to establish baselines during implementation.

**Rationale**: These are the project's existing coverage tools (Vitest + @vitest/coverage-v8, Pytest + pytest-cov) already configured in package.json and pyproject.toml.

**Alternatives considered**: None — existing tools are the correct choice per the spec's assumptions.

---

### 2. Coverage Gap Analysis

**Question**: Which modules lack test coverage entirely?

**Finding**: Based on source-to-test file mapping:

**Backend — 14 untested source files:**
- Configuration & setup: `config.py`, `main.py`, `constants.py`, `exceptions.py`
- Prompts: `prompts/task_generation.py`, `prompts/issue_generation.py`
- Services: `database.py`, `agent_tracking.py`, `completion_providers.py`, `session_store.py`, `settings_store.py`
- API routes: `api/workflow.py`, `api/chat.py`, `api/settings.py`, `api/auth.py`

**Frontend — 38 untested source files:**
- Core: `App.tsx`, `main.tsx`, `services/api.ts`
- Hooks (6): `useWorkflow`, `useSettings`, `useChat`, `useAgentConfig`, `useProjectBoard`, `useAppTheme`
- Pages (2): `ProjectBoardPage`, `SettingsPage`
- Components (27): All chat (5), settings (7), common (2), auth (1), sidebar (3), board (12 — includes `colorUtils.ts`)

**Backend — 16 tested source files** (via 12 test files):
- Models (6): All model files tested via `test_models.py`
- Services (6): `ai_agent`, `cache`, `copilot_polling`, `github_auth`, `github_projects`, `websocket`, `workflow_orchestrator`
- API routes (2): `board` (unit), `projects`/`tasks` (e2e)
- Integration: `test_custom_agent_assignment.py`

**Frontend — 3 tested source files** (via 3 test files):
- Hooks: `useAuth`, `useProjects`, `useRealTimeSync`

**Decision**: Prioritize testing by impact — services and API routes first (backend), hooks and components with business logic first (frontend). Configuration files, type declarations, and simple re-exports may be excluded from coverage targets.

**Rationale**: Services contain the core business logic and are most likely to harbor bugs. API routes exercise the full request/response cycle. Components with user interaction logic should be tested before purely presentational components.

**Alternatives considered**: Testing alphabetically (rejected — inefficient, doesn't prioritize bug-prone areas); testing only the largest files (rejected — small files can have critical logic).

---

### 3. Testing Patterns and Conventions

**Question**: What test patterns are established in the existing codebase?

**Finding**:

**Backend patterns:**
- Class-based test organization: `class TestCacheEntry`, `class TestInMemoryCache`
- `unittest.mock.patch` decorator for mocking external dependencies
- Async tests supported via `pytest-asyncio` with `asyncio_mode = "auto"`
- Shared fixtures in `conftest.py`: `mock_session` (UserSession), `mock_access_token`
- Descriptive method names: `test_cache_entry_creation`, `test_get_nonexistent_returns_none`

**Frontend patterns:**
- `describe/it/expect` block structure (Vitest globals)
- `vi.mock()` for module mocking
- `renderHook` from `@testing-library/react` for hook testing
- `QueryClientProvider` wrapper for React Query context
- `waitFor` and `act` for async operations
- `happy-dom` environment (configured in vitest.config.ts)

**Decision**: Follow established patterns exactly. Backend: class-based with `@patch`. Frontend: `describe/it` with `vi.mock()` and Testing Library utilities.

**Rationale**: Consistency with existing tests reduces cognitive load and ensures new tests are familiar to the team.

**Alternatives considered**: Switching to `vitest-mock-extended` (rejected — unnecessary change to working patterns); using `pytest-mock` instead of `unittest.mock.patch` (rejected — existing tests use `@patch` consistently).

---

### 4. Test Isolation Strategy

**Question**: How should tests be isolated, particularly for services with external dependencies (GitHub API, AI providers, database)?

**Finding**:

**Backend:**
- GitHub API calls: Mock `httpx.AsyncClient` responses
- AI providers: Mock `completion_providers` module
- Database: Mock `aiosqlite` connections or use in-memory SQLite
- WebSocket: Mock `ConnectionManager` from existing `test_websocket.py` pattern
- Session state: Use `mock_session` fixture from `conftest.py`

**Frontend:**
- API calls: Mock `services/api.ts` module with `vi.mock()`
- React Query: Wrap with fresh `QueryClient` per test
- WebSocket: Mock `socket.io-client` (setup in `test/setup.ts`)
- Router/Navigation: Mock or use `MemoryRouter`

**Decision**: Mock at module boundaries following existing patterns. No integration with real external services for unit tests.

**Rationale**: Existing test infrastructure already provides the mocking patterns needed. Using the same approach ensures deterministic, fast tests.

**Alternatives considered**: Using test containers for real database tests (rejected — overkill for unit coverage target; integration tests already exist).

---

### 5. Coverage Threshold Configuration

**Question**: Should coverage thresholds be enforced in CI configuration?

**Finding**: Neither frontend (package.json/vitest.config.ts) nor backend (pyproject.toml) currently define coverage threshold configurations. The spec requires 85% aggregate coverage.

**Decision**: Document the 85% target in the PR description and quickstart guide. Optionally recommend adding threshold configuration to vitest.config.ts and pytest configuration in a follow-up task (outside scope of this feature).

**Rationale**: The spec requires meeting 85% coverage, not enforcing it in CI. Adding CI enforcement is a separate concern that could block future PRs if coverage dips during unrelated changes.

**Alternatives considered**: Adding `--cov-fail-under=85` to pytest and `coverage.thresholds` to vitest config now (rejected — spec doesn't require CI enforcement, and it could cause unintended build failures in other features).

---

### 6. File Exclusions from Coverage

**Question**: Which files should be excluded from coverage calculations?

**Finding**:
- `frontend/src/vite-env.d.ts` — TypeScript environment declaration, no logic
- `frontend/src/types/index.ts` — Type definitions only
- `frontend/src/main.tsx` — React DOM render entry point (bootstrapping only)
- `backend/src/migrations/__init__.py` — Empty init file
- `backend/src/models/__init__.py`, `backend/src/api/__init__.py` — Re-export modules

**Decision**: Exclude type declarations and empty `__init__.py` files from coverage targets. Entry points (`main.tsx`, `main.py`) should still be tested for startup behavior where practical.

**Rationale**: Type-only files contain no runtime code. Empty init files are structural. Testing entry points validates the application bootstraps correctly.

**Alternatives considered**: Excluding all `__init__.py` files (rejected — some contain re-exports that should be verified); excluding all config files (rejected — `config.py` contains logic that should be tested).

## Summary of Decisions

| Topic | Decision |
|-------|----------|
| Coverage tools | Vitest + @vitest/coverage-v8 (frontend), Pytest + pytest-cov (backend) |
| Priority order | Services → API routes → hooks → components (by business logic density) |
| Test patterns | Follow existing: class-based @patch (backend), describe/it vi.mock (frontend) |
| Isolation | Mock at module boundaries, no real external services |
| Threshold enforcement | Document in PR, do not add to CI config |
| Exclusions | Type declarations, empty __init__.py; include entry points |
