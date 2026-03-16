# Quick Start: Increase Test Coverage & Surface Unknown Bugs

**Feature**: `048-test-coverage-bugs` | **Date**: 2026-03-16

## Prerequisites

- Python ≥3.12 (target 3.13)
- Node.js 20+
- Git

## Setup

```bash
# Clone and navigate to the repository
cd solune/backend
pip install -e ".[dev]"

cd ../frontend
npm ci
```

## Running Existing Tests

### Backend

```bash
cd solune/backend

# Run all unit tests with coverage
pytest --cov=src --cov-report=term-missing --durations=20

# Run with HTML coverage report (inspect uncovered branches)
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in a browser

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/property/                # Property-based tests
pytest tests/fuzz/                    # Fuzz tests
pytest tests/chaos/                   # Chaos tests
pytest tests/concurrency/             # Concurrency tests

# Run advanced tests with CI-like settings
HYPOTHESIS_PROFILE=ci pytest tests/property/ tests/fuzz/ tests/chaos/ tests/concurrency/ --timeout=120
```

### Frontend

```bash
cd solune/frontend

# Run all tests with coverage
npm run test:coverage

# Run tests in watch mode (for development)
npm run test:watch

# Run mutation testing
npm run test:mutate

# Run E2E tests
npm run test:e2e
```

## Writing New Tests

### Backend: API Route Tests

Follow the pattern in `tests/unit/test_api_chat.py`:

```python
"""Tests for <module> API routes (src/api/<module>.py)."""

import pytest
from unittest.mock import AsyncMock, patch


class TestEndpointName:
    async def test_happy_path(self, client):
        resp = await client.get("/api/v1/<endpoint>")
        assert resp.status_code == 200
        assert resp.json()["key"] == "expected_value"

    async def test_error_case(self, client):
        # Configure mock to raise
        resp = await client.get("/api/v1/<endpoint>")
        assert resp.status_code == 404
```

Key fixtures available from `tests/conftest.py`:
- `client` — httpx.AsyncClient with all dependencies overridden
- `mock_session` — UserSession stub
- `mock_db` — In-memory SQLite with migrations
- `mock_github_service` — AsyncMock of GitHubProjectsService
- `mock_github_auth_service` — AsyncMock of GitHubAuthService

### Backend: Service Tests

Follow the pattern in `tests/unit/test_pipeline_state_store.py`:

```python
"""Tests for <service> (src/services/<service>.py)."""

import pytest
import aiosqlite


# Helper factory
def _make_entity(**overrides):
    defaults = {"field": "value"}
    defaults.update(overrides)
    return Entity(**defaults)


class TestServiceFunction:
    async def test_creates_entity(self, mock_db):
        result = await service_function(mock_db)
        assert result is not None
```

### Backend: Time-Controlled Tests

```python
"""Time-controlled tests using freezegun."""

from freezegun import freeze_time
from datetime import datetime, timedelta


class TestSessionExpiry:
    @freeze_time("2026-03-16 12:00:00")
    async def test_session_valid_before_expiry(self):
        session = create_session(expires_at=datetime(2026, 3, 16, 13, 0, 0))
        assert session.is_valid()

    @freeze_time("2026-03-16 13:00:01")
    async def test_session_expired_after_expiry(self):
        session = create_session(expires_at=datetime(2026, 3, 16, 13, 0, 0))
        assert not session.is_valid()
```

### Frontend: Hook Tests

Follow the pattern in `src/hooks/useAuth.test.tsx`:

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the API
vi.mock('@/services/api', () => ({
  someApi: { getData: vi.fn() },
}));

describe('useMyHook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns data on success', async () => {
    const mockData = { id: 1, name: 'test' };
    someApi.getData.mockResolvedValueOnce(mockData);

    const { result } = renderHook(() => useMyHook(), { wrapper: TestWrapper });
    await waitFor(() => expect(result.current.data).toEqual(mockData));
  });
});
```

### Frontend: Component Tests

Follow the pattern in `src/components/ui/button.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<MyComponent onClick={onClick} />);
    await user.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
```

### Architecture Tests

```python
"""Architecture fitness tests — import direction enforcement."""

import ast
import os


def test_services_never_import_api():
    """Services layer must not import from API layer."""
    violations = []
    for root, _, files in os.walk("src/services"):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                tree = ast.parse(open(path).read())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        module = getattr(node, "module", "") or ""
                        if module.startswith("src.api"):
                            violations.append(f"{path}: imports {module}")
    assert violations == [], f"Layer violations found:\n" + "\n".join(violations)
```

## Coverage Threshold Updates

After each phase, update thresholds:

### Backend (`solune/backend/pyproject.toml`)

```toml
[tool.coverage.run]
fail_under = 74  # Phase 1: was 69, now 74
```

### Frontend (`solune/frontend/vitest.config.ts`)

```typescript
thresholds: {
  statements: 53,  // Phase 4: was 46, now 53
  branches: 48,    // Phase 4: was 41, now 48
  functions: 45,   // Phase 4: was 38, now 45
  lines: 54,       // Phase 4: was 47, now 54
},
```

## Execution Order (Recommended)

1. **Phase 7** — Promote advanced tests to CI (zero new test code)
2. **Phase 1** — Backend GitHub integration layer (highest ROI)
3. **Phase 4** — Frontend services & hooks (pure logic, no JSX)
4. **Phase 9** — Production-mode tests (security-critical)
5. **Phase 8** — Time-controlled tests (temporal boundaries)
6. **Phase 2** → Phase 3 → Phase 5 → Phase 6 → Phase 10 → Phase 11 → Phase 12

## Verification

```bash
# Backend: Check current coverage
cd solune/backend
pytest --cov=src --cov-report=term-missing | tail -5

# Frontend: Check current coverage
cd solune/frontend
npm run test:coverage 2>&1 | grep -A5 "Coverage summary"

# Verify advanced tests run in CI
# Check the "Backend Advanced Tests" job in GitHub Actions

# Verify mutation testing
# Check the "Mutation Testing" workflow runs on Monday
```
