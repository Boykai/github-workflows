# Coverage Contracts: Phase 3 — Testing

**Feature**: `001-phase-3-testing` | **Date**: 2026-03-22 | **Plan**: [plan.md](../plan.md)

## Overview

Phase 3 does not introduce new API endpoints or external-facing contracts. Instead, it establishes **coverage contracts** — enforceable numeric thresholds that CI validates on every PR. These contracts define the minimum quality bar for test suites.

## Frontend Coverage Contract

**Enforcement mechanism**: `vitest.config.ts` → `test.coverage.thresholds`
**Verification command**: `npm run test:coverage`

### Phase 1 Thresholds

```json
{
  "statements": 65,
  "branches": 55,
  "functions": 55,
  "lines": 65
}
```

### Phase 2 Thresholds (Final)

```json
{
  "statements": 75,
  "branches": 65,
  "functions": 65,
  "lines": 75
}
```

### CI Integration

The `frontend` job in `ci.yml` runs `npm run test:coverage` which executes Vitest with coverage enforcement. If any threshold is not met, the job fails and the PR is blocked.

## Backend Coverage Contract

**Enforcement mechanism**: `pyproject.toml` → `[tool.coverage.report].fail_under` (global), per-file verification via targeted pytest commands
**Verification commands**:
- `pytest --cov=src/api/board --cov-fail-under=80`
- `pytest --cov=src/api/pipelines --cov-fail-under=80`
- `pytest --cov=src/services/copilot_polling/pipeline --cov-fail-under=85`
- `pytest --cov=src/services/agent_creator --cov-fail-under=70`

### Per-File Floors

| Module | Minimum Coverage | Verification |
|--------|-----------------|--------------|
| `src/api/board.py` | 80% | `pytest --cov=src/api/board` |
| `src/api/pipelines.py` | 80% | `pytest --cov=src/api/pipelines` |
| `src/services/copilot_polling/pipeline.py` | 85% | `pytest --cov=src/services/copilot_polling/pipeline` |
| `src/services/agent_creator.py` | 70% | `pytest --cov=src/services/agent_creator` |

### Exclusions

The following are explicitly excluded from coverage enforcement:
- `health.py` error paths (intentionally non-raising)
- WebSocket handlers
- Error-returning webhooks (intentionally non-raising)

## Mutation Testing Contract

### Frontend (Stryker)

**Enforcement mechanism**: `stryker.config.mjs` → `thresholds.break`
**Verification command**: `npx stryker run`

```json
{
  "thresholds": {
    "high": 80,
    "low": 60,
    "break": 50
  }
}
```

**Contract**: If the mutation score drops below 50%, Stryker exits with a non-zero code and the CI job fails.

### Backend (mutmut)

**Enforcement mechanism**: Aggregation step in `mutation-testing.yml`
**Verification**: CI job parses kill ratios from 4 shard reports

**Contract**: If any mutmut shard reports a kill ratio below 60%, the aggregation job fails and the workflow is marked as failed.

### CI Integration

The `mutation-testing.yml` workflow runs weekly (Sundays 2 AM UTC) and on manual dispatch. After Phase 3:
- `continue-on-error` is removed from both mutation jobs
- Frontend Stryker job fails on score < 50%
- Backend mutmut aggregation job fails on kill ratio < 60% in any shard

## Property Test Contract

**Enforcement mechanism**: Hypothesis settings profile in `tests/property/conftest.py`
**Verification command**: `pytest tests/property/ -v`

**Contract**: All property-based tests must pass with `max_examples=200` in CI (HYPOTHESIS_PROFILE=ci). Queue invariants enforced:
1. FIFO order preserved across all state transitions
2. Queued pipelines never have an assigned agent
3. At most 1 active (non-queued) pipeline per project
4. `should_skip_agent_trigger()` skips within grace period
5. `should_skip_agent_trigger()` allows stale reclaim after 120 seconds

## Accessibility Contract

**Enforcement mechanism**: `@axe-core/playwright` AxeBuilder in Playwright specs
**Verification command**: `npx playwright test`

**Contract**: axe-core accessibility scans must be present in at least 8 Playwright spec files (up from 3). Any accessibility violation causes the test to fail.

### Files with axe-core (current: 3)

1. `board-navigation.spec.ts` ✅
2. `ui.spec.ts` ✅
3. `protected-routes.spec.ts` ✅

### Files with axe-core (target: 8+)

4. `agent-creation.spec.ts` (to be added)
5. `pipeline-monitoring.spec.ts` (to be added)
6. `mcp-tool-config.spec.ts` (to be added)
7. `chat-interaction.spec.ts` (to be added)
8. `keyboard-navigation.spec.ts` (new file)

## Integration Test Contract

**Enforcement mechanism**: pytest test at `tests/integration/test_full_workflow.py`
**Verification command**: `pytest tests/integration/test_full_workflow.py -v`

**Contract**: The full-workflow integration test must verify:
1. Issue creation → project add → pipeline launch → agent assignment
2. Status transitions: Backlog → Ready → In Progress → In Review
3. PR creation webhook → pipeline state update
4. PR merge webhook → cleanup trigger → dequeue next pipeline

All 4 status transitions must complete successfully in a single test run.
