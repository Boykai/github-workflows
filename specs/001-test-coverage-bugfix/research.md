# Research: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20 | **Phase**: 0

## Research Task 1: Current Coverage Baseline

**Question**: What is the current test coverage for the frontend and backend?

**Decision**: Measure baseline coverage using existing tooling before writing new tests.

**Rationale**: The spec (FR-001, SC-005) requires a before-and-after comparison. Vitest with `@vitest/coverage-v8` and pytest with `pytest-cov` are already configured as dev dependencies. The frontend has 3 test files covering hooks (`useAuth`, `useProjects`, `useRealTimeSync`) out of ~35 source files. The backend has 11 test files covering services, models, and API routes out of ~35 source files. Expected baseline is well below 85%.

**Alternatives considered**:
- Istanbul/nyc for frontend: Rejected — Vitest already bundles v8 coverage provider
- coverage.py standalone for backend: Rejected — pytest-cov integrates coverage.py with pytest and is already a dependency

## Research Task 2: Frontend Testing Strategy (Vitest + React)

**Question**: What are the best practices for testing React components and hooks with Vitest?

**Decision**: Use `@testing-library/react` for component tests and `renderHook` from the same library for hook tests. Use `vi.mock()` for module mocking. Follow AAA pattern per spec FR-003.

**Rationale**: The project already uses `@testing-library/react` (in devDependencies) and Vitest globals. The existing test files (`useAuth.test.tsx`, `useProjects.test.tsx`, `useRealTimeSync.test.tsx`) demonstrate the established patterns: `renderHook` with `QueryClientProvider` wrapper, `vi.mock()` for service mocking, and async `waitFor` assertions. New tests should follow these patterns for consistency.

**Alternatives considered**:
- Enzyme: Rejected — deprecated, not compatible with React 18
- React Test Renderer: Rejected — lower-level API, `@testing-library/react` is already in use and preferred

## Research Task 3: Backend Testing Strategy (pytest + FastAPI)

**Question**: What are the best practices for testing FastAPI applications with pytest?

**Decision**: Use pytest with `pytest-asyncio` (auto mode) for async test support. Use `unittest.mock.AsyncMock` and `patch` for mocking dependencies. Use `httpx.AsyncClient` with FastAPI's `TestClient` for API route tests. Follow existing `conftest.py` fixture patterns.

**Rationale**: The project's `pyproject.toml` sets `asyncio_mode = "auto"`, meaning all async test functions are automatically handled. The existing test files demonstrate patterns with `@patch` decorators, `AsyncMock` for async dependencies, and direct function calls for unit tests. The `conftest.py` provides shared fixtures (`mock_session`, `mock_access_token`) that new tests should reuse.

**Alternatives considered**:
- anyio backend switching: The project uses `anyio_backend` fixture defaulting to asyncio — no need to change
- Factory Boy for fixtures: Rejected — overkill for current test complexity; simple fixture functions suffice

## Research Task 4: Coverage Configuration and Exclusions

**Question**: How should coverage be configured to exclude untestable files?

**Decision**: Configure coverage exclusions in `vitest.config.ts` (frontend) and `pyproject.toml` (backend) to exclude type declarations, configuration files, migration files, and generated code.

**Rationale**: The spec (Edge Cases section) identifies that configuration files, type declarations, and generated code should be excluded from coverage calculations. For frontend: exclude `vite-env.d.ts`, `types/index.ts` (type-only), `main.tsx` (entry point with side effects). For backend: exclude `migrations/`, `__init__.py` files, and `config.py` (environment-dependent configuration).

**Alternatives considered**:
- Including all files with lower threshold: Rejected — would require testing environment-dependent code paths that are inherently non-deterministic
- Per-file thresholds: Rejected — the spec targets aggregate coverage (Assumption in spec.md)

## Research Task 5: Frontend Under-Tested Modules

**Question**: Which frontend modules lack test coverage and need new tests?

**Decision**: Priority test targets for the frontend (currently untested):

| Module Category | Files | Priority |
|----------------|-------|----------|
| Hooks (untested) | `useWorkflow.ts`, `useSettings.ts`, `useChat.ts`, `useAgentConfig.ts`, `useProjectBoard.ts`, `useAppTheme.ts` | P1 — high logic density |
| Services | `api.ts` | P1 — core data layer |
| Components (board) | `ProjectBoard.tsx`, `BoardColumn.tsx`, `IssueCard.tsx`, `IssueDetailModal.tsx`, `AgentConfigRow.tsx`, `AgentPresetSelector.tsx`, `AgentTile.tsx`, `AddAgentPopover.tsx`, `AgentSaveBar.tsx`, `AgentColumnCell.tsx`, `colorUtils.ts` | P1 — primary UI |
| Components (chat) | `ChatInterface.tsx`, `MessageBubble.tsx`, `TaskPreview.tsx`, `StatusChangePreview.tsx`, `IssueRecommendationPreview.tsx` | P2 |
| Components (settings) | `GlobalSettings.tsx`, `ProjectSettings.tsx`, `AIPreferences.tsx`, `DisplayPreferences.tsx`, `NotificationPreferences.tsx`, `WorkflowDefaults.tsx`, `SettingsSection.tsx` | P2 |
| Components (common) | `ErrorDisplay.tsx`, `RateLimitIndicator.tsx` | P2 |
| Components (auth) | `LoginButton.tsx` | P2 |
| Components (sidebar) | `ProjectSelector.tsx`, `ProjectSidebar.tsx`, `TaskCard.tsx` | P2 |
| Pages | `ProjectBoardPage.tsx`, `SettingsPage.tsx` | P3 |
| App | `App.tsx` | P3 |

**Rationale**: Hooks and services contain the most business logic and are easiest to unit test in isolation. Components require more setup (rendering, mocking) but are essential for coverage. Pages are integration-level and lower priority.

## Research Task 6: Backend Under-Tested Modules

**Question**: Which backend modules lack test coverage and need new tests?

**Decision**: Priority test targets for the backend (currently untested or under-tested):

| Module Category | Files | Priority |
|----------------|-------|----------|
| Services (untested) | `database.py`, `session_store.py`, `settings_store.py`, `agent_tracking.py`, `completion_providers.py` | P1 — core business logic |
| API routes (untested) | `auth.py`, `board.py`, `chat.py`, `projects.py`, `settings.py`, `tasks.py`, `workflow.py` | P1 — user-facing endpoints |
| Models (partial) | `board.py`, `chat.py`, `project.py`, `settings.py`, `task.py`, `user.py` | P2 — validation logic |
| Prompts | `task_generation.py`, `issue_generation.py` | P3 — template strings |
| Core | `main.py`, `exceptions.py`, `constants.py` | P3 — infrastructure |

**Rationale**: Existing tests cover `github_auth`, `models` (partially), `workflow_orchestrator`, `ai_agent`, `websocket`, `copilot_polling`, `github_projects`, `webhooks`, `cache`, and `board`. The untested services and API routes represent the largest coverage gaps. API route tests should use FastAPI's `TestClient` pattern.

## Research Task 7: Handling Flaky Tests

**Question**: How should flaky tests be identified and prevented?

**Decision**: Ensure all tests are deterministic by:
1. Mocking all external dependencies (GitHub API, WebSocket, database)
2. Using fixed timestamps and deterministic data in fixtures
3. Avoiding `time.sleep()` or timing-dependent assertions
4. Running tests in random order with `pytest-randomly` (if available) to detect order dependencies

**Rationale**: The spec (FR-004, FR-005) mandates isolation and determinism. The existing test setup already mocks WebSocket and window objects (frontend `setup.ts`). Backend tests use `@patch` and `AsyncMock` for external dependencies. New tests should follow these established mocking patterns.

**Alternatives considered**:
- pytest-rerunfailures for retry: Rejected — masks flakiness rather than fixing it
- Test timeouts: Useful as a safety net but not a substitute for proper mocking

## Research Task 8: Bug Discovery and Fix Workflow

**Question**: How should bugs discovered during testing be tracked and fixed?

**Decision**: Follow the spec requirement (FR-007, FR-008):
1. When a test reveals a bug, write the failing test first (Red)
2. Fix the bug to make the test pass (Green)
3. Use separate commit messages: `test: add test for X` vs `fix: resolve bug in Y`
4. Document each bug in the PR description with affected module, description, and resolution

**Rationale**: This approach aligns with TDD principles and the spec's requirement for clear commit separation. The PR description summary (FR-011) ensures reviewers can quickly understand what was fixed.

**Alternatives considered**:
- Separate bug-fix branch: Rejected — spec explicitly requires fixes in the same branch (FR-007)
- Issue-per-bug tracking: Rejected — overhead for bugs found during testing; PR description summary is sufficient per spec
