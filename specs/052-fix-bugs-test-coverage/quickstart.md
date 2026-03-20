# Quickstart: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Feature**: `052-fix-bugs-test-coverage`
**Date**: 2026-03-19

## Prerequisites

- Python ≥3.12 with virtual environment activated (`source backend/.venv/bin/activate`)
- Node.js with frontend dependencies installed (`cd frontend && npm install`)
- All existing tests pass (`cd backend && pytest` and `cd frontend && npx vitest run`)

## Implementation Order

Work through phases sequentially. Within each phase, steps are parallelizable unless noted.

### Phase A: Static Analysis Sweep

1. **Fix lint violations** (frontend + backend in parallel):
   ```bash
   cd apps/solune/frontend && npx eslint . --fix
   cd apps/solune/backend && ruff check src/ --fix
   ```

2. **Fix type errors** (frontend + backend in parallel):
   ```bash
   cd apps/solune/frontend && npx tsc --noEmit
   cd apps/solune/backend && pyright
   ```

3. **Fix security issues**:
   ```bash
   cd apps/solune/backend && bandit -r src/ -s B104,B608
   ```

4. **Detect and quarantine flaky tests**:
   ```bash
   cd apps/solune/backend && python scripts/detect_flaky.py
   ```
   For each flaky test: add `@pytest.mark.skip(reason="flaky: <root-cause>")` and file an issue.

5. **Verify zero AsyncMock warnings**:
   ```bash
   cd apps/solune/backend && pytest 2>&1 | grep -c "AsyncMock"
   ```

### Phase B: Backend Coverage (add tests to `backend/tests/`)

**Pattern for integration tests** (follow `tests/integration/test_health_endpoint.py`):
```python
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_route_happy_path(client: AsyncClient):
    response = await client.get("/api/endpoint")
    assert response.status_code == 200
    data = response.json()
    assert "expected_key" in data

@pytest.mark.asyncio
async def test_route_error_path(client: AsyncClient):
    with patch("src.services.module.method", side_effect=Exception("fail")):
        response = await client.get("/api/endpoint")
        assert response.status_code == 500
```

**Pattern for edge-case tests**:
```python
@pytest.mark.asyncio
async def test_recovery_crash_mid_recovery():
    """Test that recovery handles crash during recovery attempt."""
    # Arrange: set up state where recovery is in progress
    # Act: simulate crash
    # Assert: system returns to consistent state

@pytest.mark.asyncio
async def test_recovery_empty_state():
    """Test recovery when no active issues exist."""
    # Assert: recovery completes without errors
```

**Pattern for property-based tests** (follow `tests/property/test_pipeline_state_machine.py`):
```python
from hypothesis import given, settings
from hypothesis import strategies as st

@settings(max_examples=100)
@given(st.data())
def test_state_transitions_valid(data):
    # Generate random state + transition
    # Assert: transition is valid or raises expected error
```

### Phase C: Frontend Coverage (add tests to `frontend/src/`)

**Pattern for board component tests** (follow `BoardColumn.test.tsx`):
```tsx
import { render, screen } from "@testing-library/react";
import { DndContext } from "@dnd-kit/core";
import { describe, it, expect, vi } from "vitest";

describe("ProjectBoard", () => {
  const renderWithProviders = (ui: React.ReactElement) =>
    render(<DndContext>{ui}</DndContext>);

  it("renders board with columns", () => {
    renderWithProviders(<ProjectBoard {...defaultProps} />);
    expect(screen.getByRole("region")).toBeInTheDocument();
  });

  it("renders empty state when no items", () => {
    renderWithProviders(<ProjectBoard {...emptyProps} />);
    expect(screen.getByText(/no items/i)).toBeInTheDocument();
  });
});
```

**Pattern for hook tests** (follow `useBoardControls.test.tsx`):
```tsx
import { renderHook, act } from "@testing-library/react";
import { describe, it, expect } from "vitest";

describe("useBoardDragDrop", () => {
  it("handles successful drag end", () => { /* success branch */ });
  it("handles drag end with error", () => { /* error branch */ });
  it("returns loading state during mutation", () => { /* loading branch */ });
  it("handles empty column drag", () => { /* empty branch */ });
  it("handles drag to same column", () => { /* edge-case branch */ });
});
```

### Phase D: Mutation Verification

Run each shard and triage survivors:
```bash
cd apps/solune/backend
python scripts/run_mutmut_shard.py --shard auth-and-projects
python scripts/run_mutmut_shard.py --shard orchestration
python scripts/run_mutmut_shard.py --shard app-and-data
python scripts/run_mutmut_shard.py --shard agents-and-integrations
python scripts/run_mutmut_shard.py --shard api-and-middleware
mutmut results

cd apps/solune/frontend
npx stryker run
```

For each surviving mutant, classify and resolve:
- **Killable**: Write a targeted assertion in the relevant test file
- **Equivalent**: Document why the mutation doesn't change behavior
- **Non-killable**: Document why it's impractical to test

### Phase E: Lock In

1. Ratchet thresholds in config:
   - `pyproject.toml`: `fail_under = 80`
   - `vitest.config.ts`: `statements: 55, branches: 50, functions: 45, lines: 55`

2. Verify pre-commit timing: `time scripts/pre-commit` (must be < 30s)

3. Document `SKIP_COVERAGE=1` emergency override with audit trail

4. Generate final reports:
   ```bash
   cd apps/solune/backend && pytest --cov=src --cov-report=html
   cd apps/solune/frontend && npx vitest run --coverage
   ```

## Key Decisions

- **Characterization tests only** — document current behavior, no DRY refactoring
- **Thresholds ratchet upward only** — never decrease
- **5-run flaky detection** — standard practice per Google Testing Blog
- **≥100 Hypothesis examples** — meaningful state space coverage
- **Existing tools only** — pytest, vitest, mutmut, Stryker (no new adoption)
