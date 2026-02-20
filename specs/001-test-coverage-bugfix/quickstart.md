# Quickstart: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20

## Prerequisites

- Node.js 18+ and npm (for frontend)
- Python 3.11+ and pip (for backend)
- Project dependencies installed (`npm install` in frontend, `pip install -e ".[dev]"` in backend)

## Step 1: Establish Baseline Coverage

### Frontend

```bash
cd frontend
npx vitest run --coverage
```

Note the overall coverage percentages for lines, branches, functions, and statements.

### Backend

```bash
cd backend
python -m pytest --cov=src --cov-report=term-missing tests/
```

Note the total coverage percentage and identify files with the lowest coverage.

## Step 2: Identify Coverage Gaps

Review the coverage reports from Step 1. Focus on files with:
- 0% coverage (no tests at all)
- Below 85% coverage (need additional tests)

Priority order for writing new tests:
1. **Services** (core business logic — highest bug density)
2. **API routes** (request/response validation)
3. **Hooks** (frontend state management and data fetching)
4. **Components** (UI behavior and user interactions)

## Step 3: Write Tests

### Frontend Test Pattern

Create test files co-located with source files:

```bash
# Example: testing a hook
touch frontend/src/hooks/useSettings.test.tsx
```

Use the established pattern:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock dependencies
vi.mock('@/services/api', () => ({ /* mock functions */ }));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useSettings', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('should return settings when loaded', async () => {
    // Arrange - set up mocks and test data
    // Act - render the hook
    // Assert - verify expected behavior
  });
});
```

### Backend Test Pattern

Create test files in the appropriate tests directory:

```bash
# Example: testing a service
touch backend/tests/unit/test_settings_store.py
```

Use the established pattern:

```python
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

class TestSettingsStore:
    @patch("src.services.settings_store.dependency")
    async def test_get_settings_returns_defaults(self, mock_dep):
        # Arrange
        mock_dep.return_value = mock_data

        # Act
        result = await get_settings()

        # Assert
        assert result.key == expected_value
```

## Step 4: Run Tests and Verify

### Run Frontend Tests

```bash
cd frontend
npx vitest run              # Quick pass/fail check
npx vitest run --coverage   # Full coverage report
```

### Run Backend Tests

```bash
cd backend
python -m pytest tests/                                    # Quick pass/fail check
python -m pytest --cov=src --cov-report=term-missing tests/ # Full coverage report
```

## Step 5: Fix Discovered Bugs

When a test exposes a bug:

1. Write the test that demonstrates the bug (it should fail)
2. Fix the bug in the source code
3. Verify the test now passes
4. Run the full test suite to check for regressions

## Step 6: Measure Final Coverage

Re-run coverage for both frontend and backend (same commands as Step 1). Verify:

- [ ] Overall coverage ≥ 85% (aggregate across frontend and backend)
- [ ] All tests pass (exit code 0)
- [ ] No regressions in existing tests

## Common Commands Reference

| Action | Frontend | Backend |
|--------|----------|---------|
| Run all tests | `npx vitest run` | `python -m pytest tests/` |
| Run with coverage | `npx vitest run --coverage` | `pytest --cov=src --cov-report=term-missing` |
| Run single test file | `npx vitest run src/hooks/useAuth.test.tsx` | `pytest tests/unit/test_cache.py` |
| Watch mode | `npx vitest` | `pytest-watch` (if installed) |
| Run only unit tests | N/A (all co-located) | `pytest tests/unit/` |
| Run only integration | N/A | `pytest tests/integration/` |
