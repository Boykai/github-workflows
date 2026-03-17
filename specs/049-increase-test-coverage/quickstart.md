# Quick Start: Increase Test Coverage to Surface Unknown Bugs

**Feature**: `049-increase-test-coverage` | **Date**: 2026-03-17

## Prerequisites

- Python ≥3.12 (target 3.13)
- Node.js 22+
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

# Run with HTML coverage report (inspect uncovered lines/branches)
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
- `mock_ai_agent_service` — AsyncMock of AIAgentService

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

### Backend: GitHub Integration Tests

Follow the pattern in `tests/unit/test_issues.py`:

```python
"""Tests for GitHub agents (src/services/github_projects/agents.py)."""

import pytest
from unittest.mock import AsyncMock, patch

class TestGitHubAgents:
    async def test_request_construction(self, mock_github_service):
        # Mock the GitHub API client
        mock_github_service.some_method.return_value = expected_response
        result = await mock_github_service.some_method(params)
        assert result == expected_response

    async def test_rate_limit_429(self, mock_github_service):
        mock_github_service.some_method.side_effect = RateLimitError(429)
        with pytest.raises(RateLimitError):
            await mock_github_service.some_method(params)

    async def test_timeout_error(self, mock_github_service):
        mock_github_service.some_method.side_effect = TimeoutError()
        with pytest.raises(TimeoutError):
            await mock_github_service.some_method(params)

    async def test_not_found_404(self, mock_github_service):
        mock_github_service.some_method.side_effect = NotFoundError(404)
        with pytest.raises(NotFoundError):
            await mock_github_service.some_method(params)
```

### Backend: Time-Controlled Tests

```python
"""Time-controlled tests using freezegun."""

from freezegun import freeze_time
from datetime import datetime, timedelta


class TestSessionExpiry:
    @freeze_time("2026-03-17 12:00:00")
    async def test_session_valid_before_expiry(self):
        session = create_session(expires_at=datetime(2026, 3, 17, 13, 0, 0))
        assert session.is_valid()

    @freeze_time("2026-03-17 13:00:01")
    async def test_session_expired_after_expiry(self):
        session = create_session(expires_at=datetime(2026, 3, 17, 13, 0, 0))
        assert not session.is_valid()
```

### Backend: Architecture Tests

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

  it('handles error state', async () => {
    someApi.getData.mockRejectedValueOnce(new Error('fail'));

    const { result } = renderHook(() => useMyHook(), { wrapper: TestWrapper });
    await waitFor(() => expect(result.current.error).toBeTruthy());
  });
});
```

### Frontend: Component Tests

Follow the pattern in `src/components/settings/SettingsSection.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { renderWithProviders } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';

describe('MyComponent', () => {
  it('renders correctly', () => {
    renderWithProviders(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    renderWithProviders(<MyComponent onClick={onClick} />);
    await user.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('has no accessibility violations', async () => {
    const { container } = renderWithProviders(<MyComponent />);
    await expectNoA11yViolations(container);
  });
});
```

### Frontend: Schema Tests

```typescript
import { describe, it, expect } from 'vitest';
import { mySchema } from '@/services/schemas/mySchema';

describe('mySchema', () => {
  it('validates correct input', () => {
    const result = mySchema.safeParse({ field: 'valid' });
    expect(result.success).toBe(true);
  });

  it('rejects invalid input', () => {
    const result = mySchema.safeParse({ field: 123 });
    expect(result.success).toBe(false);
  });

  it('applies default values', () => {
    const result = mySchema.parse({});
    expect(result.field).toBe('default');
  });
});
```

## Coverage Threshold Updates

After each phase, update thresholds:

### Backend (`solune/backend/pyproject.toml`)

```toml
# Phase 2: Backend Coverage Growth (71% → 76%)
[tool.coverage.report]
fail_under = 76

# Phase 5 + final: Backend at 80%
[tool.coverage.report]
fail_under = 80
```

### Frontend (`solune/frontend/vitest.config.ts`)

```typescript
// Phase 3: Hooks & Services
thresholds: {
  statements: 53,
  branches: 48,
  functions: 45,
  lines: 54,
},

// Phase 4: Components (final)
thresholds: {
  statements: 60,
  branches: 55,
  functions: 52,
  lines: 60,
},
```

## Execution Order (Recommended)

1. **Phase 1** — Promote advanced tests to CI (zero new test code, highest leverage)
2. **Phase 2** — Backend high-ROI gaps (steps 5–8 in parallel)
3. **Phase 3** — Frontend schemas + hooks (steps 10–11 in parallel)
4. **Phase 4** — Frontend components (steps 13–16 in parallel)
5. **Phase 5** — Mutation-hardened tests (steps 18–19 in parallel)
6. **Phase 6** — Production-parity + time-controlled tests (steps 20–22 in parallel)
7. **Phase 7** — Architecture fitness + structural guards (steps 23–25 in parallel)

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
# Check the "Mutation Testing" workflow runs weekly

# Run architecture fitness tests
cd solune/backend
pytest tests/architecture/ -v

# Run contract validation
solune/scripts/validate-contracts.sh
```
