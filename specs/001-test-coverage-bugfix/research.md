# Research: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20

## Coverage Baseline Analysis

### Frontend (Vitest + @vitest/coverage-v8)

**Current State**: 3 test files exist covering 3 of ~9 hooks. No component tests, no service tests, no page tests.

- **Tested modules**: `useAuth`, `useProjects`, `useRealTimeSync`
- **Untested modules**: `useWorkflow`, `useSettings`, `useChat`, `useAgentConfig`, `useProjectBoard`, `useAppTheme`, all components (~25 files), services (`api.ts`), pages (2 files), types, `App.tsx`

**Decision**: Prioritize hooks (high logic density), services (API layer), and components with complex behavior for coverage improvement.

**Rationale**: Hooks contain the bulk of frontend business logic (state management, API integration, side effects). Testing hooks gives the highest coverage-per-test ROI. Component tests are secondary because they often exercise hook logic indirectly.

**Alternatives considered**: Testing every component individually was rejected as it would produce many shallow snapshot tests that inflate coverage without testing real behavior (violates FR-006).

### Backend (pytest + pytest-cov)

**Current State**: ~10 test files covering models, board, cache, webhooks, AI agent, websocket, copilot polling, GitHub auth, GitHub projects, workflow orchestrator, and one integration test.

- **Tested modules**: `models/*`, `api/board`, `services/cache`, `api/webhooks`, `services/ai_agent`, `services/websocket`, `services/copilot_polling`, `services/github_auth`, `services/github_projects`, `services/workflow_orchestrator`
- **Untested modules**: `api/auth`, `api/chat`, `api/projects`, `api/settings`, `api/tasks`, `api/workflow`, `services/settings_store`, `services/session_store`, `services/database`, `services/agent_tracking`, `services/completion_providers`, `config.py`, `constants.py`, `exceptions.py`, `main.py`, `prompts/*`, `migrations/*`

**Decision**: Focus on API route handlers, service modules with business logic, and configuration/exception modules for maximum coverage gain.

**Rationale**: API routes and services form the application's core behavior. Configuration and exception modules are straightforward to test and provide quick coverage wins.

**Alternatives considered**: Testing prompts and migrations was deprioritized as they contain static templates and schema definitions respectively, contributing less to behavioral coverage.

## Testing Best Practices

### Vitest + React Testing Library (Frontend)

**Decision**: Follow existing patterns — use `renderHook()` with a `QueryClientProvider` wrapper, `vi.mock()` for API modules, `waitFor()` for async state.

**Rationale**: Consistency with the 3 existing test files reduces cognitive overhead and ensures patterns are already validated by the team.

**Alternatives considered**: Using `msw` (Mock Service Worker) for API mocking was considered but rejected because the codebase already uses `vi.mock()` consistently, and introducing a new mocking paradigm mid-feature adds unnecessary complexity (violates Principle V: Simplicity).

### pytest + pytest-asyncio (Backend)

**Decision**: Follow existing patterns — class-based test organization, `pytest.fixture` for shared setup, `unittest.mock.patch` / `AsyncMock` for external dependencies, `pytest.raises` for error paths.

**Rationale**: Consistency with existing backend tests. The `conftest.py` already provides `mock_session` and `mock_access_token` fixtures that new tests can reuse.

**Alternatives considered**: Using `factory_boy` for test data generation was considered but rejected as the existing fixture pattern is sufficient for the project's scale (~30 source files).

## Coverage Tool Configuration

### Frontend

**Decision**: Use `vitest run --coverage` which is already configured in `package.json` as the `test:coverage` script. Coverage provider is `@vitest/coverage-v8`.

**Rationale**: Already configured and working. No changes needed to the tooling.

### Backend

**Decision**: Use `pytest --cov=src --cov-report=term-missing` with the existing `pytest-cov` dependency.

**Rationale**: `pytest-cov` is already listed as a dev dependency. The `--cov=src` flag targets only the application source code, excluding test files from coverage calculations.

## Coverage Exclusion Strategy

**Decision**: Exclude configuration-only files (`vite-env.d.ts`, `main.tsx` entry point), type declarations (`types/index.ts`), and migration boilerplate from coverage targets. Focus the 85% target on aggregate coverage, not per-file.

**Rationale**: Per the spec assumptions, "configuration files, type declarations, and generated code may be excluded from coverage calculations per existing tool configuration."

**Alternatives considered**: Requiring 85% per-file was rejected as it would force testing of trivial files (e.g., re-export barrels, type-only modules) without behavioral value.

## Bug Discovery Process

**Decision**: When a test reveals unexpected behavior, document the bug inline (test comment describing expected vs. actual behavior), fix the source code, and ensure the test passes with the fix. Commit bug fixes separately from test additions.

**Rationale**: Aligns with FR-007 (fix bugs in same branch) and FR-008 (distinguish bug fix commits from test commits).
