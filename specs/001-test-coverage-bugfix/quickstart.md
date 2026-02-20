# Quickstart: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20
**Purpose**: Step-by-step guide to get started with the coverage improvement effort.

## Prerequisites

- Node.js (for frontend development)
- Python 3.11+ (for backend development)
- Frontend dependencies installed (`cd frontend && npm install`)
- Backend dependencies installed (`cd backend && pip install -e ".[dev]"`)

## Step 1: Measure Baseline Coverage

### Frontend

```bash
cd frontend
npm run test:coverage
```

This runs `vitest run --coverage` and outputs a per-file and aggregate coverage report to the terminal.

### Backend

```bash
cd backend
pytest --cov=src --cov-report=term-missing
```

This runs all tests with coverage enabled and shows uncovered lines per file.

**Record the baseline percentages** — these will be compared against final coverage in the PR description.

## Step 2: Identify Under-Tested Modules

Review the coverage reports from Step 1. Look for:

- Files with **0% coverage** (no tests at all)
- Files with coverage **below 85%** (need more tests)
- Files with **low branch coverage** (missing edge cases)

### Frontend — Files Likely Needing Tests

| Category | Files | Existing Tests? |
|----------|-------|-----------------|
| Hooks | useAgentConfig, useAppTheme, useChat, useProjectBoard, useSettings, useWorkflow | No |
| Hooks | useAuth, useProjects, useRealTimeSync | Yes (expand) |
| Services | api.ts | No |
| Components | All under components/ | No |
| Pages | ProjectBoardPage, SettingsPage | No |
| Utilities | colorUtils.ts | No |

### Backend — Files Likely Needing Tests

| Category | Files | Existing Tests? |
|----------|-------|-----------------|
| Services | agent_tracking, completion_providers, database, session_store, settings_store | No |
| Services | ai_agent, cache, copilot_polling, github_auth, github_projects, websocket, workflow_orchestrator | Yes (expand) |
| API routes | auth, board, chat, projects, settings, tasks, webhooks, workflow | Partial |
| Models | board, chat, project, settings, task, user | Partial (test_models.py) |
| Other | config, constants, exceptions | No |

## Step 3: Write Tests

Follow the AAA (Arrange-Act-Assert) pattern for every test. See `contracts/coverage-contract.md` for exact patterns.

### Frontend test example

Create a new test file co-located with the source:

```bash
# Example: frontend/src/hooks/useAppTheme.test.ts
```

```typescript
import { renderHook, act } from '@testing-library/react';
import { useAppTheme } from './useAppTheme';

describe('useAppTheme', () => {
  it('should return default theme on initial render', () => {
    // Arrange & Act
    const { result } = renderHook(() => useAppTheme());

    // Assert
    expect(result.current.isDarkMode).toBeDefined();
  });
});
```

### Backend test example

Create a new test file in the appropriate test directory:

```bash
# Example: backend/tests/unit/test_settings_store.py
```

```python
import pytest
from src.services.settings_store import SettingsStore

class TestSettingsStore:
    @pytest.fixture
    def store(self):
        # Arrange
        return SettingsStore()

    def test_get_default_settings(self, store):
        # Act
        settings = store.get_defaults()

        # Assert
        assert settings is not None
```

## Step 4: Run Tests Frequently

### Frontend

```bash
cd frontend
npm run test          # Run all tests
npm run test:coverage # Run with coverage report
npm run test:watch    # Watch mode during development
```

### Backend

```bash
cd backend
pytest                                         # Run all tests
pytest --cov=src --cov-report=term-missing     # Run with coverage
pytest tests/unit/test_specific.py -v          # Run single test file
```

## Step 5: Fix Bugs

When a test reveals a bug:

1. Keep the failing test
2. Fix the source code
3. Verify the test passes
4. Commit the fix separately: `fix: [module] description`

## Step 6: Document and Submit

Before submitting the PR:

1. Run the full test suite for both frontend and backend
2. Generate final coverage reports
3. Compare against baseline from Step 1
4. Include before/after coverage table in PR description
5. List any bugs discovered and fixed
