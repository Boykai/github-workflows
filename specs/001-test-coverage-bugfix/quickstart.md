# Quickstart: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20 | **Phase**: 1

## Prerequisites

- Node.js (for frontend Vitest tests)
- Python 3.11+ (for backend pytest tests)
- Frontend dependencies installed: `cd frontend && npm install`
- Backend dependencies installed: `cd backend && pip install -e ".[dev]"`

## Running Tests

### Frontend

```bash
# Run all frontend tests
cd frontend
npm run test

# Run tests with coverage report
npm run test:coverage

# Run tests in watch mode (development)
npm run test:watch
```

### Backend

```bash
# Run all backend tests
cd backend
python -m pytest

# Run tests with coverage report
python -m pytest --cov=src --cov-report=term-missing

# Run only unit tests
python -m pytest tests/unit/

# Run only integration tests
python -m pytest -m integration tests/integration/
```

## Measuring Coverage Baseline

Before writing new tests, capture the baseline:

```bash
# Frontend baseline
cd frontend && npm run test:coverage 2>&1 | tee /tmp/frontend-baseline.txt

# Backend baseline
cd backend && python -m pytest --cov=src --cov-report=term-missing 2>&1 | tee /tmp/backend-baseline.txt
```

## Writing New Tests

### Frontend Test Pattern (Vitest + React Testing Library)

```tsx
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';

describe('useExample', () => {
  it('should return expected value', async () => {
    // Arrange
    const mockData = { id: 1, name: 'test' };
    vi.mock('../services/api', () => ({ fetchData: vi.fn().mockResolvedValue(mockData) }));

    // Act
    const { result } = renderHook(() => useExample());

    // Assert
    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });
  });
});
```

### Backend Test Pattern (pytest + AsyncMock)

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestExampleService:
    """Tests for ExampleService."""

    @patch("src.services.example.dependency", new_callable=AsyncMock)
    async def test_example_method(self, mock_dep):
        # Arrange
        mock_dep.return_value = {"key": "value"}

        # Act
        result = await example_method()

        # Assert
        assert result == {"key": "value"}
        mock_dep.assert_called_once()
```

## Verifying Coverage Target

After writing tests, confirm the 85% threshold:

```bash
# Frontend — check overall coverage percentage
cd frontend && npm run test:coverage

# Backend — check overall coverage percentage
cd backend && python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=85
```

## Bug Fix Workflow

1. Write a test that exposes the bug (test should fail)
2. Fix the bug in the source code (test should now pass)
3. Commit separately: `git commit -m "test: add test for X"` then `git commit -m "fix: resolve bug in Y"`
4. Document the bug in the PR description
