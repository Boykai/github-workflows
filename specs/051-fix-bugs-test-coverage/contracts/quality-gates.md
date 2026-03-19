# Contracts: Quality Gates

**Feature Branch**: `051-fix-bugs-test-coverage`
**Date**: 2026-03-19

## Overview

This feature does not introduce new API endpoints or modify existing API contracts. It operates
entirely on the existing codebase's testing infrastructure, CI configuration, and quality tooling.

The "contracts" for this feature are the **quality gates and verification commands** that define
the interface between the development process and CI enforcement.

## Quality Gate Contracts

### Contract 1: Backend Coverage Gate

**Config File**: `solune/backend/pyproject.toml`
**Section**: `[tool.coverage.report]`

```toml
# Baseline (pre-change)
fail_under = 75

# Target (after Phase B completion)
fail_under = 80
```

**Enforcement**: `pytest --cov=src --cov-fail-under=80` exits non-zero if line coverage < 80%.

**Branch coverage**: Backend branch coverage SHOULD target at least 75% as a stretch goal.
This metric is tracked for visibility but is NOT a blocking gate. It will not cause CI to fail
if not met. Branch coverage is reported alongside line coverage for monitoring purposes only.

**Verification Command**:
```bash
cd solune/backend && .venv/bin/python -m pytest tests/ \
  --cov=src --cov-report=term-missing --cov-fail-under=80
```

---

### Contract 2: Frontend Coverage Gate

**Config File**: `solune/frontend/vitest.config.ts`
**Section**: `test.coverage.thresholds`

```typescript
// Baseline (pre-change)
thresholds: {
  statements: 50,
  branches: 44,
  functions: 41,
  lines: 50,
}

// Target (after Phase C completion)
thresholds: {
  statements: 55,
  branches: 50,
  functions: 45,
  lines: 55,
}
```

**Enforcement**: Vitest exits non-zero if any threshold is not met.

**Verification Command**:
```bash
cd solune/frontend && npm run test:coverage
```

---

### Contract 3: Backend Mutation Gate

**Config File**: `solune/backend/pyproject.toml`
**Section**: `[tool.mutmut]`

**Threshold**: Each of the 4 backend mutation shards MUST report a kill rate ≥ 60%.

**Shards**: `auth-and-projects`, `orchestration`, `app-and-data`, `agents-and-integrations`

**Enforcement**: Manual verification via shard runner script. CI reports kill rate per shard.

**Verification Command**:
```bash
cd solune/backend && \
  for shard in auth-and-projects orchestration app-and-data agents-and-integrations; do \
    echo "=== Shard: $shard ===" && \
    python scripts/run_mutmut_shard.py --shard=$shard; \
  done
```

---

### Contract 4: Frontend Mutation Gate

**Config File**: `solune/frontend/stryker.config.mjs`
**Section**: `thresholds`

```javascript
thresholds: {
  high: 80,
  low: 60,
  break: null  // advisory, not blocking
}
```

**Enforcement**: Stryker reports mutation score. Score ≥ 80% = green, 60–80% = yellow, < 60% = red.

**Verification Command**:
```bash
cd solune/frontend && npx stryker run
```

---

### Contract 5: Static Analysis Gate

**Scope**: Both backend and frontend codebases must produce zero lint and type-check errors.

**Backend**:
- `ruff check src/` → zero violations
- `pyright src/` → zero errors
- `bandit -r src/ -c pyproject.toml` → zero issues

**Frontend**:
- `npx eslint . --max-warnings=0` → zero violations
- `npx tsc --noEmit` → zero errors

**Enforcement**: Pre-commit hooks and CI both run these checks. Non-zero exit blocks merge.

---

### Contract 6: Flaky Test Gate

**Threshold**: Zero flaky tests detected across 5 consecutive runs of each test suite.

**Detection Method**:
- Backend: `python scripts/detect_flaky.py --runs=5`
- Frontend: Run `npm run test` 5 times, compare results

**Enforcement**: Any test producing inconsistent results across 5 runs must be quarantined with:
1. Root cause category (async-timing, shared-state, environment, non-deterministic-ordering)
2. Tracking reference (issue or task ID)
3. Re-enablement condition

---

### Contract 7: Pre-commit Hook Performance Gate

**Threshold**: Pre-commit hooks complete in under 30 seconds for typical changesets.

**Definition of "typical changeset"**: 1–10 files modified across backend and/or frontend.

**Enforcement**: Hooks run only on changed files (not entire codebase). Measured via `time scripts/pre-commit`.

**Verification Command**:
```bash
cd solune && time scripts/pre-commit
```
