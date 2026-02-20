# Quickstart: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20

## Prerequisites

- Node.js 18+ and npm (for frontend)
- Python 3.11+ and pip (for backend)
- Git

## Setup

```bash
# Clone and checkout the feature branch
git checkout 001-test-coverage-bugfix

# Install frontend dependencies
cd frontend && npm install

# Install backend dependencies (with dev extras)
cd ../backend && pip install -e ".[dev]"
```

## Running Tests

### Frontend

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode (during development)
npm run test:watch

# Run tests with coverage report
npm run test:coverage
```

### Backend

```bash
cd backend

# Run all tests
python -m pytest

# Run tests with coverage report
python -m pytest --cov=src --cov-report=term-missing

# Run only unit tests
python -m pytest tests/unit/

# Run a specific test file
python -m pytest tests/unit/test_board.py
```

## Measuring Coverage Baseline

Before writing any new tests, capture the baseline:

```bash
# Frontend baseline
cd frontend && npm run test:coverage 2>&1 | tee /tmp/frontend-baseline.txt

# Backend baseline
cd backend && python -m pytest --cov=src --cov-report=term-missing 2>&1 | tee /tmp/backend-baseline.txt
```

## Writing New Tests

### Frontend Test Pattern

```typescript
// src/hooks/useExample.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock dependencies
vi.mock('@/services/api', () => ({
  exampleApi: { getData: vi.fn() },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useExample', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns data on success', async () => {
    // Arrange
    const mockData = { id: 1, name: 'test' };
    (exampleApi.getData as Mock).mockResolvedValue(mockData);

    // Act
    const { result } = renderHook(() => useExample(), { wrapper: createWrapper() });

    // Assert
    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });
  });
});
```

### Backend Test Pattern

```python
# tests/unit/test_example.py
import pytest
from unittest.mock import AsyncMock, patch

from src.services.example import ExampleService


class TestExampleService:
    """Tests for ExampleService."""

    @pytest.fixture
    def service(self):
        """Create a fresh ExampleService for each test."""
        return ExampleService()

    async def test_get_data_returns_expected_result(self, service):
        """Verify get_data returns formatted data."""
        # Arrange
        mock_response = {"id": 1, "name": "test"}

        # Act
        with patch.object(service, '_fetch', new_callable=AsyncMock, return_value=mock_response):
            result = await service.get_data()

        # Assert
        assert result == mock_response
```

## Verifying the 85% Target

After writing tests, confirm the overall coverage:

```bash
# Frontend
cd frontend && npm run test:coverage
# Look for "All files" row — must be ≥ 85%

# Backend
cd backend && python -m pytest --cov=src --cov-report=term-missing
# Look for "TOTAL" row — must be ≥ 85%
```

## Committing Changes

Follow these conventions for commit messages:

- **Test additions**: `test: add tests for <module name>`
- **Bug fixes**: `fix: <description of bug fixed>`
- **Mixed**: Separate into distinct commits where possible
