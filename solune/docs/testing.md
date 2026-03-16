# Testing

## Overview

| Tool | Scope | Count / Notes |
|------|-------|---------------|
| pytest + pytest-asyncio | Backend unit / integration / e2e | Extensive suite (hundreds of tests, auto-discovered) |
| Vitest + React Testing Library | Frontend unit | Growing suite of frontend unit tests (auto-discovered) |
| Playwright | Frontend E2E | Multiple E2E spec files (auto-discovered) |

## Backend Tests

```bash
cd backend
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_copilot_polling.py -v

# Run specific test by name
pytest tests/ -k "test_pipeline_advancement" -v
```

### Test Structure

```text
backend/tests/
├── conftest.py              # Shared fixtures (db, sessions, mocks)
├── helpers/                 # Test helper utilities
├── unit/                    # 68 unit test files
│   ├── test_admin_authorization.py
│   ├── test_agent_creator.py
│   ├── test_agent_mcp_sync.py
│   ├── test_agent_output.py
│   ├── test_agent_tracking.py
│   ├── test_agents_service.py
│   ├── test_ai_agent.py
│   ├── test_api_auth.py
│   ├── test_api_board.py
│   ├── test_api_chat.py
│   ├── test_api_mcp.py
│   ├── test_api_pipelines.py
│   ├── test_api_projects.py
│   ├── test_api_settings.py
│   ├── test_api_tasks.py
│   ├── test_api_tools.py
│   ├── test_api_workflow.py
│   ├── test_attachment_formatter.py
│   ├── test_auth_security.py
│   ├── test_blocking_removal.py
│   ├── test_board.py
│   ├── test_cache.py
│   ├── test_chores_api.py
│   ├── test_chores_counter.py
│   ├── test_chores_scheduler.py
│   ├── test_chores_service.py
│   ├── test_cleanup_service.py
│   ├── test_completion_false_positive.py
│   ├── test_completion_providers.py
│   ├── test_config.py
│   ├── test_config_validation.py
│   ├── test_copilot_polling.py
│   ├── test_database.py
│   ├── test_error_responses.py
│   ├── test_exceptions.py
│   ├── test_github_auth.py
│   ├── test_github_projects.py
│   ├── test_issue_creation_retry.py
│   ├── test_label_constants.py
│   ├── test_label_fast_path.py
│   ├── test_label_validation.py
│   ├── test_label_write_path.py
│   ├── test_logging_utils.py
│   ├── test_main.py
│   ├── test_mcp_store.py
│   ├── test_middleware.py
│   ├── test_model_fetcher.py
│   ├── test_models.py
│   ├── test_module_boundaries.py
│   ├── test_oauth_state.py
│   ├── test_orchestrator.py
│   ├── test_pipeline_state_store.py
│   ├── test_polling_loop.py
│   ├── test_project_ownership.py
│   ├── test_prompts.py
│   ├── test_rate_limiting.py
│   ├── test_recommendation_models.py
│   ├── test_recovery.py
│   ├── test_session_store.py
│   ├── test_settings_store.py
│   ├── test_signal_chat.py
│   ├── test_token_encryption.py
│   ├── test_tools_service.py
│   ├── test_utils.py
│   ├── test_webhooks.py
│   ├── test_websocket.py
│   ├── test_workflow_orchestrator.py
│   └── test_workflow_orchestrator_config.py
├── integration/             # Integration tests
└── test_api_e2e.py          # API end-to-end tests
```

### Configuration

Backend tests use `pyproject.toml`:

- `pytest-asyncio` for async test support
- `pytest-cov` for coverage reporting
- Test fixtures in `conftest.py` provide mock databases, sessions, and services

## Frontend Tests

### Unit Tests (Vitest)

```bash
cd frontend

# Run all unit tests
npm test

# Watch mode
npm run test:watch

# With coverage
npm run test:coverage
```

Test files are co-located with components:

- `components/auth/LoginButton.test.tsx`
- `components/board/AgentSaveBar.test.tsx`
- `components/board/BoardColumn.test.tsx`
- `components/board/IssueCard.test.tsx`
- `components/board/IssueDetailModal.test.tsx`
- `components/chat/CommandAutocomplete.test.tsx`
- `components/chat/IssueRecommendationPreview.test.tsx`
- `components/chat/MessageBubble.test.tsx`
- `components/chat/StatusChangePreview.test.tsx`
- `components/chat/TaskPreview.test.tsx`
- `components/chores/__tests__/AddChoreModal.test.tsx`
- `components/chores/__tests__/ChoreScheduleConfig.test.tsx`
- `components/chores/__tests__/ChoresPanel.test.tsx`
- `components/chores/__tests__/FeaturedRitualsPanel.test.tsx`
- `components/common/ErrorBoundary.test.tsx`
- `components/settings/DynamicDropdown.test.tsx`
- `components/settings/SettingsSection.test.tsx`
- `components/ThemeProvider.test.tsx`
- `components/ui/button.test.tsx`
- `components/ui/card.test.tsx`
- `components/ui/input.test.tsx`
- `hooks/useAuth.test.tsx`
- `hooks/useBoardRefresh.test.tsx`
- `hooks/useChat.test.tsx`
- `hooks/useChatHistory.test.ts`
- `hooks/useCommands.test.tsx`
- `hooks/useProjectBoard.test.tsx`
- `hooks/useProjects.test.tsx`
- `hooks/useRealTimeSync.test.tsx`
- `hooks/useSettingsForm.test.tsx`
- `hooks/useWorkflow.test.tsx`
- `lib/commands/registry.test.ts`
- `lib/commands/handlers/help.test.ts`
- `lib/commands/handlers/settings.test.ts`
- `lib/buildGitHubMcpConfig.test.ts`
- `components/tools/ToolsEnhancements.test.tsx`

### E2E Tests (Playwright)

```bash
cd frontend

# Run E2E tests
npm run test:e2e

# With browser visible
npm run test:e2e:headed

# Interactive UI mode
npm run test:e2e:ui

# View test report
npm run test:e2e:report
```

E2E specs:

- `e2e/auth.spec.ts`
- `e2e/board-navigation.spec.ts`
- `e2e/chat-interaction.spec.ts`
- `e2e/integration.spec.ts`
- `e2e/responsive-board.spec.ts`
- `e2e/responsive-home.spec.ts`
- `e2e/responsive-settings.spec.ts`
- `e2e/settings-flow.spec.ts`
- `e2e/ui.spec.ts`

## Code Quality

### Backend

```bash
cd backend
source .venv/bin/activate

# Linting
ruff check src/ tests/

# Formatting
ruff format src/ tests/

# Type checking
pyright src/
```

### Frontend

```bash
cd frontend

# Linting
npm run lint
npm run lint:fix

# Formatting
npm run format

# Type checking
npm run type-check
```

### Pre-Commit Hook

Install the git pre-commit hook that runs ruff, pyright, eslint, tsc, vitest, and build:

```bash
./scripts/setup-hooks.sh
```
