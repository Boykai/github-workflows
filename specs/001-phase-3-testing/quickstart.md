# Quickstart: Phase 3 — Testing

**Feature**: `001-phase-3-testing` | **Date**: 2026-03-22 | **Plan**: [plan.md](./plan.md)

## Prerequisites

All testing infrastructure is already installed. No new tooling or dependency installation is required.

**Verify tools are available**:

```bash
# Frontend
cd solune/frontend
npm run test -- --version          # Vitest
npx playwright --version           # Playwright
npx stryker --version              # Stryker mutation testing

# Backend
cd solune/backend
pytest --version                   # pytest
python -c "import hypothesis; print(hypothesis.__version__)"  # Hypothesis
python -c "import mutmut; print(mutmut.__version__)"          # mutmut
```

## Running Tests

### Frontend Unit Tests (with coverage)

```bash
cd solune/frontend
npm run test:coverage
```

Current thresholds: 50/44/41/50 (statements/branches/functions/lines).
Phase 1 target: 65/55/55/65. Phase 2 target: 75/65/65/75.

### Frontend E2E Tests

```bash
cd solune/frontend
npx playwright install --with-deps chromium  # First time only
npm run test:e2e -- --project=chromium

# Run specific keyboard navigation suite
npx playwright test keyboard-navigation.spec.ts
```

### Backend Unit Tests (with coverage)

```bash
cd solune/backend

# Full test suite with coverage
pytest --cov=src --cov-report=term-missing --durations=20

# Per-file coverage checks
pytest --cov=src/api/board --cov-report=term-missing
pytest --cov=src/api/pipelines --cov-report=term-missing
pytest --cov=src/services/copilot_polling/pipeline --cov-report=term-missing
pytest --cov=src/services/agent_creator --cov-report=term-missing
```

### Backend Integration Tests

```bash
cd solune/backend
pytest tests/integration/test_full_workflow.py -v
pytest tests/unit/test_queue_mode.py -v
```

### Property-Based Tests

```bash
cd solune/backend

# Run with dev profile (20 examples, fast iteration)
pytest tests/property/ -v

# Run with CI profile (200 examples, thorough)
HYPOTHESIS_PROFILE=ci pytest tests/property/ -v
```

### Mutation Testing

```bash
# Frontend (Stryker)
cd solune/frontend
npx stryker run
# Exits non-zero if mutation score < 50 (after Phase 3)

# Backend (mutmut) — single shard
cd solune/backend
python scripts/run_mutmut_shard.py --shard orchestration --max-children 1
python -m mutmut results
```

## Writing New Tests

### Frontend Hook Test Pattern

```typescript
// src/hooks/useMyHook.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect } from 'vitest';
import { useMyHook } from './useMyHook';
import { createMockApi } from '@/test/helpers';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useMyHook', () => {
  it('should fetch data', async () => {
    const mockApi = createMockApi();
    mockApi.getData.mockResolvedValue({ items: [] });

    const { result } = renderHook(() => useMyHook(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ items: [] });
  });
});
```

### Backend Test Pattern (httpx.ASGITransport)

```python
# tests/integration/test_my_feature.py
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.anyio
async def test_my_endpoint(thin_mock_client):
    """Test using the integration conftest thin_mock_client fixture."""
    response = await thin_mock_client.get("/api/v1/my-endpoint")
    assert response.status_code == 200
```

### Property Test Pattern (Hypothesis)

```python
# tests/property/test_my_property.py
from hypothesis import given, settings
from hypothesis import strategies as st

@settings(max_examples=200)
@given(values=st.lists(st.integers(min_value=0, max_value=100)))
def test_my_property(values):
    # Property assertion
    result = my_function(values)
    assert invariant_holds(result)
```

### E2E Accessibility Test Pattern (Playwright + axe-core)

```typescript
// e2e/my-feature.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('should have no accessibility violations', async ({ page }) => {
  await page.goto('/my-page');
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});

test('keyboard navigation', async ({ page }) => {
  await page.goto('/my-page');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'First' })).toBeFocused();
});
```

## Verification Checklist

Run these commands to verify Phase 3 is complete:

```bash
# 1. Frontend coverage at 75/65/65/75
cd solune/frontend && npm run test:coverage

# 2. Backend per-file coverage
cd solune/backend
pytest --cov=src/api/board --cov-fail-under=80
pytest --cov=src/api/pipelines --cov-fail-under=80
pytest --cov=src/services/copilot_polling/pipeline --cov-fail-under=85
pytest --cov=src/services/agent_creator --cov-fail-under=70

# 3. Full-workflow integration
pytest tests/integration/test_full_workflow.py -v

# 4. Mutation testing exits non-zero on low scores
cd solune/frontend && npx stryker run

# 5. Property tests pass (200 examples)
cd solune/backend && HYPOTHESIS_PROFILE=ci pytest tests/property/ -v

# 6. Keyboard navigation E2E
cd solune/frontend && npx playwright test keyboard-navigation.spec.ts

# 7. FIFO queue ordering
cd solune/backend && pytest tests/unit/test_queue_mode.py -v
```
