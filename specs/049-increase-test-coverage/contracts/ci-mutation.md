# CI Contract: Mutation Testing Workflow

**Feature**: `049-increase-test-coverage` | **Date**: 2026-03-17

## Purpose

Define the contract for the scheduled mutation testing workflow that runs weekly for both backend and frontend, publishing results as downloadable artifacts.

## Workflow Definition

```yaml
# New file: .github/workflows/mutation.yml
name: Mutation Testing

on:
  schedule:
    - cron: "0 3 * * 1"  # Every Monday at 03:00 UTC
  workflow_dispatch:       # Allow manual triggering

jobs:
  backend-mutation:
    name: Backend Mutation Testing (4 shards)
    runs-on: ubuntu-latest
    timeout-minutes: 60
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    defaults:
      run:
        working-directory: solune/backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - name: Run mutmut shard ${{ matrix.shard }}
        run: python scripts/run_mutmut_shard.py --shard=${{ matrix.shard }} --total-shards=4
      - name: Upload mutation report
        uses: actions/upload-artifact@v4
        with:
          name: backend-mutation-report-shard-${{ matrix.shard }}
          path: solune/backend/mutation-report-shard-${{ matrix.shard }}.txt
          retention-days: 30

  frontend-mutation:
    name: Frontend Mutation Testing
    runs-on: ubuntu-latest
    timeout-minutes: 60
    defaults:
      run:
        working-directory: solune/frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - run: npm ci
      - name: Run Stryker (hooks + lib)
        run: |
          npm run test:mutate -- --reporters clear-text json || true
      - name: Upload mutation report
        uses: actions/upload-artifact@v4
        with:
          name: frontend-mutation-report
          path: solune/frontend/reports/mutation/
          retention-days: 30
```

## Behavior Contract

| Aspect | Specification |
|--------|--------------|
| **Trigger** | `schedule` (weekly Monday 03:00 UTC) + `workflow_dispatch` (manual) |
| **Backend tool** | `mutmut` (configured in `pyproject.toml` `[tool.mutmut]`) |
| **Backend scope** | `src/services/` (highest-value mutation targets), 4 shards for parallelism |
| **Backend shard runner** | `scripts/run_mutmut_shard.py` — existing shard runner script |
| **Frontend tool** | `@stryker-mutator` (configured via `stryker.config.mjs`) |
| **Frontend scope** | Hooks and lib modules (configured in Stryker config) |
| **Timeout** | 60 minutes per job |
| **Failure behavior** | `|| true` ensures workflow completes even with surviving mutants |
| **Artifacts** | Published as downloadable GitHub Actions artifacts, 30-day retention |
| **PR blocking** | None — mutation testing is informational only |

## Report Format

### Backend (mutmut)

```
Survived mutants:
  - src/services/chat_store.py:42 — replaced == with != → survived
  - src/services/guard_service.py:18 — replaced > with >= → survived
  ...
Total: X survived / Y killed / Z total (mutation score: N%)
```

### Frontend (Stryker)

```json
{
  "files": {
    "src/hooks/useSettings.ts": {
      "mutants": [...],
      "mutationScore": 85.2
    }
  },
  "thresholds": { "high": 80, "low": 60 }
}
```

## Acceptance Criteria

1. ✅ Mutation testing runs weekly on Monday at 03:00 UTC
2. ✅ Manual trigger is available via `workflow_dispatch`
3. ✅ Backend mutates `src/services/` using mutmut with 4 shards
4. ✅ Frontend mutates hooks + lib using Stryker
5. ✅ Results are published as downloadable artifacts with 30-day retention
6. ✅ Mutation testing does not block any PR or deployment
7. ✅ Each job has a 60-minute timeout to prevent runaway execution
