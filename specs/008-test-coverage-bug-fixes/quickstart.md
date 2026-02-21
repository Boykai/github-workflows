# Quickstart: Test Coverage & Bug Fixes

**Feature**: `008-test-coverage-bug-fixes`  
**Date**: 2026-02-20

---

## Prerequisites

- Python ≥3.11 with virtualenv activated (`source backend/.venv/bin/activate`)
- Node.js with dependencies installed (`cd frontend && npm install`)

## Running Backend Tests

```bash
# Run all tests
cd backend
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run a specific test file
pytest tests/unit/test_agent_tracking.py

# Run with verbose output
pytest -v --cov=src --cov-report=term-missing
```

### Expected output (post-implementation)

```
TOTAL                           85%+
```

Coverage report will show per-file coverage with missing lines. The test suite should fail (`exit code 2`) if aggregate coverage drops below 85%.

## Running Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run a specific test file
npx vitest run src/hooks/useChat.test.tsx

# Run in watch mode during development
npm run test:watch
```

### Expected output (post-implementation)

```
% Coverage report from v8
All files        |   85+  |   70+  |   80+  |   85+
```

## Verifying Coverage Thresholds

### Backend

```bash
cd backend
pytest --cov=src --cov-report=term-missing --cov-fail-under=85
echo $?  # Should be 0 if ≥85%, non-zero otherwise
```

### Frontend

```bash
cd frontend
npm run test:coverage
echo $?  # Should be 0 if thresholds pass
```

## Writing New Tests

### Backend pattern

```python
# tests/unit/test_<module>.py
import pytest
from unittest.mock import AsyncMock, patch

async def test_function_does_something(mock_db, mock_session):
    """Test that function does the expected thing."""
    # Arrange — use shared fixtures from conftest.py
    # Act — call the function under test
    # Assert — verify the outcome
    pass
```

### Frontend pattern

```tsx
// src/<path>/<Component>.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
// or: import { render, screen } from '@testing-library/react';

vi.mock('@/services/api', () => ({ /* mock exports */ }));

describe('ComponentName', () => {
  beforeEach(() => vi.clearAllMocks());
  
  it('renders correctly', () => {
    // Arrange-Act-Assert
  });
});
```

## Troubleshooting

| Issue | Solution |
|-------|---------|
| `ModuleNotFoundError` in backend tests | Ensure virtualenv is activated and `pip install -e ".[dev]"` was run |
| Coverage below 85% | Run with `--cov-report=term-missing` to identify uncovered lines |
| Frontend test timeouts | Check that `vi.mock()` calls are at file top level, not inside tests |
| `act()` warnings in React tests | Wrap state-changing operations in `act()` or use `waitFor()` |
| Import errors for `@/` paths | Ensure `vitest.config.ts` has the `resolve.alias` matching `tsconfig.json` |
