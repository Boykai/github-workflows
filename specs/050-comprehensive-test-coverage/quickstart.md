# Quickstart: Comprehensive Test Coverage to 90%+

**Feature**: `050-comprehensive-test-coverage`
**Date**: 2026-03-17

---

## Prerequisites

- Python 3.12+ with pip
- Node.js 22+ with npm
- Git (for diff-cover branch comparison)

## Quick Verification Commands

### Backend Coverage

```bash
cd solune/backend
pip install -e ".[dev]"
pytest --cov=src --cov-report=term-missing --durations=20
# Expected: ≥71% initially → ≥90% at completion
```

### Frontend Coverage

```bash
cd solune/frontend
npm ci
npm run test:coverage
# Expected: ≥49% statements initially → ≥90% at completion
```

### E2E Tests

```bash
cd solune/frontend
npx playwright install chromium
npm run test:e2e -- --project=chromium
# Expected: All specs pass (68+ tests at completion)
```

### Mutation Testing

```bash
# Backend (per shard)
cd solune/backend
python scripts/run_mutmut_shard.py --shard auth-and-projects

# Frontend
cd solune/frontend
npm run test:mutate
```

### Contract Validation

```bash
bash solune/scripts/validate-contracts.sh
```

### Coverage Baseline Update

```bash
# After intentionally increasing coverage:
bash solune/scripts/update-coverage-baseline.sh
# Review the diff, then commit .coverage-baseline.json
```

---

## Phase Execution Order

```
Phase 1 (Foundation & CI Ratchet)
    │
    ├── Phase 2 (Backend Services & API) ─────────┐
    ├── Phase 3 (Frontend Hooks & Components) ─────┤
    ├── Phase 5 (Property-Based & Fuzz Testing) ───┤
    ├── Phase 6 (E2E & Visual Regression) ─────────┤
    ├── Phase 7 (Contract & Integration Testing) ──┤
    │                                               │
    │   Phase 4 (Mutation Testing Expansion) ───────┤ (after Phases 2-3)
    │                                               │
    └───────────────────────────────────────────────┘
                        │
                Phase 8 (Coverage Ceiling & Maintenance)
```

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `.coverage-baseline.json` | Ratchet baseline (NEW) |
| `solune/backend/pyproject.toml` | Backend coverage config (`fail_under`) |
| `solune/frontend/vitest.config.ts` | Frontend coverage thresholds |
| `solune/frontend/stryker.config.mjs` | Frontend mutation config |
| `.github/workflows/ci.yml` | CI pipeline (ratchet + diff-cover steps) |
| `.github/workflows/mutation.yml` | Mutation testing (expanded shards) |
| `solune/scripts/update-coverage-baseline.sh` | Baseline bump script (NEW) |
| `solune/backend/scripts/detect_flaky.py` | Flaky test detection (NEW) |

---

## Threshold Progression Reference

### Backend `fail_under`

| Phase | Threshold | When |
|-------|-----------|------|
| Current | 71% | Starting point |
| Phase 1 | 75% | After ratchet setup |
| Phase 2 | 85% | After service + API tests |
| Phase 8 | 90% | Final lock |

### Frontend Thresholds

| Phase | Statements | Branches | Functions | Lines |
|-------|-----------|----------|-----------|-------|
| Current | 49% | 44% | 41% | 50% |
| Phase 3 | 80% | 75% | 70% | 80% |
| Phase 8 | 90% | 85% | 85% | 90% |
