# Quickstart: Find/Fix Bugs & Increase Test Coverage

**Feature Branch**: `050-fix-bugs-test-coverage`
**Date**: 2026-03-19
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Prerequisites

- Python 3.12+ with virtual environment at `solune/backend/.venv/`
- Node.js 18+ with dependencies installed in `solune/frontend/`
- Backend dev dependencies: `cd solune/backend && uv pip install -e ".[dev]"`
- Frontend dev dependencies: `cd solune/frontend && npm install`

## Quick Verification

Run these commands to verify the current state of the codebase:

```bash
# 1. Backend tests + coverage
cd solune/backend
.venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing

# 2. Frontend tests + coverage
cd solune/frontend
npm run test:coverage

# 3. Backend lint + type check
cd solune/backend
.venv/bin/ruff check src/
.venv/bin/pyright src/

# 4. Frontend lint + type check
cd solune/frontend
npx eslint . --max-warnings=0
npx tsc --noEmit
```

## Implementation Order

### Phase 1: Static Analysis & Error Discovery
*(Parallel execution — steps 1 & 2 can run simultaneously)*

1. Run backend lint + type check sweep → generate violation report
2. Run all test suites and capture failures → generate results.xml
3. Run flaky test detection (depends on step 2) → quarantine flaky tests

### Phase 2: Fix Known Bugs
*(Sequential — each fix should be verified before moving on)*

4. Fix mutmut trampoline name-resolution bug
   - **Files**: `backend/scripts/run_mutmut_shard.py`, `backend/pyproject.toml`
   - **Verify**: `python scripts/run_mutmut_shard.py --shard=auth-and-projects` → kill rate >0%

5. Fix cache leakage between test suites
   - **Files**: `backend/tests/conftest.py`, `backend/src/services/cache.py`
   - **Verify**: Run unit + integration tests together without stale state

6. Fix AsyncMock warnings
   - **Files**: `backend/tests/integration/conftest.py`
   - **Verify**: `pytest tests/ -q 2>&1 | grep AsyncMock` → no matches

7. Fix pipeline "stuck in In Progress"
   - **Files**: `backend/src/services/copilot_polling/state_validation.py`,
     `backend/src/services/copilot_polling/pipeline.py`
   - **Verify**: State transition tests pass

### Phase 3: Backend Coverage Expansion
*(Can be parallelized across developers)*

8. Add API route integration tests
   - **Target**: `backend/tests/integration/`
   - **Pattern**: `httpx.AsyncClient` + `ASGITransport`

9. Cover high-risk service modules
   - **Targets**: `recovery.py`, `state_validation.py`, `transitions.py`,
     `signal_bridge.py`, `signal_delivery.py`, `guard_service.py`
   - **Pattern**: Hypothesis property-based tests for state machines

10. Expand mutation testing targets
    - **File**: `backend/scripts/run_mutmut_shard.py` (add new shards)

11. Add characterization tests for DRY candidates
    - **File**: `backend/tests/unit/test_regression_bugfixes.py`

### Phase 4: Frontend Coverage Expansion
*(Can be parallelized across developers)*

12. Cover App.tsx → `frontend/src/__tests__/App.test.tsx`
13. Cover board components → `frontend/src/components/board/` tests
14. Increase branch coverage → `frontend/src/hooks/` tests
15. Expand E2E suite → `frontend/e2e/` new specs
16. Run Stryker and kill survivors → targeted assertions

### Phase 5: Hardening & CI Gates
*(Sequential — thresholds only after coverage consistently met)*

17. Ratchet coverage thresholds
18. Verify pre-commit hooks
19. Add chaos/concurrency test scenarios

## Key Files Reference

| Purpose | Path |
|---------|------|
| Backend test config | `solune/backend/pyproject.toml` |
| Backend coverage config | `solune/backend/pyproject.toml` `[tool.coverage.report]` |
| Backend mutation script | `solune/backend/scripts/run_mutmut_shard.py` |
| Backend test conftest | `solune/backend/tests/conftest.py` |
| Backend integration conftest | `solune/backend/tests/integration/conftest.py` |
| Frontend test config | `solune/frontend/vitest.config.ts` |
| Frontend mutation config | `solune/frontend/stryker.config.mjs` |
| Frontend E2E config | `solune/frontend/playwright.config.ts` |
| Pre-commit hooks | `solune/scripts/pre-commit` |
| Cache service | `solune/backend/src/services/cache.py` |
| State validation | `solune/backend/src/services/copilot_polling/state_validation.py` |
| Pipeline service | `solune/backend/src/services/copilot_polling/pipeline.py` |
| Flaky test detector | `solune/backend/scripts/detect_flaky.py` |

## Decisions Summary

| Decision | Rationale |
|----------|-----------|
| Fix before expand | Broken infrastructure wastes effort |
| Risk-first coverage | Target critical-path code, not easy files |
| Mutation testing: gradual expansion | services → API → middleware |
| AsyncMock → plain async stubs | Repo best practice, clearer errors |
| Threshold ratcheting: only after consistent | Prevents blocking hotfixes |
| No DRY refactoring | Characterization tests first, refactor separately |
