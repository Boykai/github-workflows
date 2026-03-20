# Quickstart: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Feature Branch**: `051-fix-bugs-test-coverage`
**Date**: 2026-03-19
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Predecessor**: `050-fix-bugs-test-coverage` (Phase 1 complete — bugs fixed, infrastructure ready)

## Prerequisites

- Python 3.12+ with virtual environment at `solune/backend/.venv/`
- Node.js 18+ with dependencies installed in `solune/frontend/`
- Backend dev dependencies: `cd solune/backend && uv pip install -e ".[dev]"`
- Frontend dev dependencies: `cd solune/frontend && npm install`
- All 4 critical bugs from spec 050 are fixed (mutmut trampoline, cache leakage, AsyncMock warnings, pipeline stuck state)

## Quick Verification

Run these commands to verify the current baseline state:

```bash
# 1. Backend tests + coverage (expect ~75%)
cd solune/backend
.venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing

# 2. Frontend tests + coverage (expect ~51%/44%/41%)
cd solune/frontend
npm run test:coverage

# 3. Backend lint + type check (expect clean)
cd solune/backend
.venv/bin/ruff check src/
.venv/bin/pyright src/

# 4. Frontend lint + type check
cd solune/frontend
npx eslint . --max-warnings=0
npx tsc --noEmit

# 5. Backend security scan
cd solune/backend
.venv/bin/bandit -r src/ -c pyproject.toml
```

## Implementation Order

### Phase A: Static Analysis Completion (User Story 1)
*(Finish the sweep started in spec 050)*

1. Run frontend lint sweep → triage all violations (fix-now / fix-later / false-positive)
2. Fix all fix-now violations
3. Run frontend `tsc --noEmit` in strict mode → fix all type errors
4. Run backend `ruff check src/` → fix violations
5. Run backend `pyright src/` → fix type errors
6. Run backend `bandit -r src/` → fix security issues
7. Run flaky test detection — backend: `python scripts/detect_flaky.py --runs=5`
8. Run flaky test detection — frontend: run `npm run test` 5 times and compare
9. Quarantine any confirmed flaky tests with root cause documentation
10. Resolve remaining frontend test warnings

**⚠️ GATE**: All static analysis clean before proceeding to Phase B.

### Phase B: Backend Coverage Expansion (User Story 2)
*(75% → 80% line coverage)*

11. Add integration tests for auth callback, webhook dispatch, pipeline launch, chat confirm routes
    - Pattern: `httpx.AsyncClient` + `ASGITransport`
    - Cover: valid input, invalid input, authorization checks
12. Add unit tests for `dependencies.py` and request ID middleware (target 90%+ each)
13. Add edge-case tests for recovery logic, state validation boundaries, signal bridge errors
14. Add property-based tests (Hypothesis) for pipeline state machine and markdown parser
15. Expand mutation testing targets to API routes, middleware, utilities
16. Verify backend line coverage ≥ 80%

### Phase C: Frontend Coverage Expansion (User Story 3)
*(51%/44%/41% → 55%/50%/45%)*

17. Add tests for top 5 board components: ProjectBoard, BoardToolbar, CleanUpConfirmModal, AgentColumnCell, BoardDragOverlay
    - Use `@testing-library/react` + `DndContext` wrapper
    - Cover: rendering, user interactions, conditional branches
18. Add tests for 3 untested hooks: useBoardDragDrop, useConfirmation, useUnsavedPipelineGuard
    - Use `renderHook` with provider wrappers
    - Cover: success, error, loading, empty data, API failure
19. Add tests for utility modules: lazyWithRetry, commands directory, formatAgentName, generateId
    - Target 90%+ line coverage per module
20. Add branch coverage tests for hooks targeting error/loading/empty paths
21. Verify frontend coverage ≥ 55/50/45

### Phase D: Mutation Verification (User Story 4)

22. Execute all 4 backend mutation shards → verify ≥60% kill rate each
23. Execute frontend Stryker → verify ≥80% high / 60% low thresholds
24. Review surviving mutants → kill with targeted assertions or document as equivalent

### Phase E: Final Verification and CI Enforcement (User Story 5)

25. Ratchet coverage thresholds in config files
26. Run final flaky detection (5 runs each suite) → zero flaky
27. Verify zero AsyncMock deprecation warnings
28. Verify pre-commit hooks complete in <30 seconds
29. Document emergency hotfix override process
30. Generate final coverage and mutation reports

## Key Files Reference

| Area | File | Purpose |
|------|------|---------|
| Backend coverage config | `solune/backend/pyproject.toml` | `fail_under` threshold |
| Frontend coverage config | `solune/frontend/vitest.config.ts` | `thresholds` object |
| Backend mutation shards | `solune/backend/scripts/run_mutmut_shard.py` | Shard runner script |
| Frontend mutation config | `solune/frontend/stryker.config.mjs` | Stryker configuration |
| Flaky detection | `solune/backend/scripts/detect_flaky.py` | Flaky test detector |
| Pre-commit hooks | `solune/scripts/pre-commit` | Lint + type-check on changed files |
| Backend integration tests | `solune/backend/tests/integration/` | API route tests (add here) |
| Backend property tests | `solune/backend/tests/property/` | Hypothesis tests (add here) |
| Frontend component tests | `solune/frontend/src/components/board/__tests__/` | Board component tests |
| Frontend hook tests | `solune/frontend/src/hooks/__tests__/` | Hook tests |

## Verification Checklist

- [ ] Frontend lint: zero violations (`npx eslint . --max-warnings=0`)
- [ ] Frontend types: zero errors (`npx tsc --noEmit`)
- [ ] Backend lint: zero violations (`ruff check src/`)
- [ ] Backend types: zero errors (`pyright src/`)
- [ ] Backend security: zero issues (`bandit -r src/`)
- [ ] Backend coverage: ≥80% (`pytest --cov-fail-under=80`)
- [ ] Frontend coverage: ≥55/50/45 (`npm run test:coverage`)
- [ ] Backend mutation: ≥60% per shard
- [ ] Frontend mutation: ≥80% high / 60% low
- [ ] Flaky tests: zero detected across 5 runs
- [ ] Pre-commit hooks: <30 seconds
- [ ] AsyncMock warnings: zero
