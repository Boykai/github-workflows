# Contracts: Find/Fix Bugs & Increase Test Coverage

**Feature Branch**: `050-fix-bugs-test-coverage`
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

# Target (after Phase 3 completion)
fail_under = 80
```

**Enforcement**: `pytest --cov=src --cov-fail-under=80` exits non-zero if coverage < 80%.

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

// Target (after Phase 4 completion)
thresholds: {
  statements: 55,
  branches: 50,
  functions: 45,
  lines: 55,
}
```

**Enforcement**: `vitest run --coverage` exits non-zero if any threshold is not met.

**Verification Command**:
```bash
cd solune/frontend && npm run test:coverage
```

---

### Contract 3: Backend Mutation Testing Gate

**Config File**: `solune/backend/pyproject.toml`
**Section**: `[tool.mutmut]`

```toml
# Current scope
paths_to_mutate = ["src/services/"]

# Expanded scope (after Phase 3 completion)
# Applied dynamically by run_mutmut_shard.py — no pyproject.toml change needed
# New shards added to SHARDS dict in scripts/run_mutmut_shard.py
```

**Target**: Kill rate >60% per shard.

**Verification Command**:
```bash
cd solune/backend && python scripts/run_mutmut_shard.py --shard=<name>
```

---

### Contract 4: Frontend Mutation Testing Gate

**Config File**: `solune/frontend/stryker.config.mjs`

```javascript
// Current
thresholds: { high: 80, low: 60, break: null }
mutate: ['src/hooks/**/*.ts', 'src/lib/**/*.ts']

// No threshold changes planned — kill surviving mutants to meet existing thresholds
```

**Verification Command**:
```bash
cd solune/frontend && npm run test:mutate
```

---

### Contract 5: Flaky Test Detection Gate

**Tool**: `solune/backend/scripts/detect_flaky.py`

**Target**: Zero flaky tests across 10 runs.

**Verification Command**:
```bash
cd solune/backend && python scripts/detect_flaky.py --runs=10
```

---

### Contract 6: Zero AsyncMock Warnings

**Target**: Backend test suite produces zero `AsyncMock`-related warnings.

**Verification Command**:
```bash
cd solune/backend && .venv/bin/python -m pytest tests/ -q 2>&1 | grep -c "AsyncMock" | \
  xargs -I{} test {} -eq 0
```

---

### Contract 7: E2E Test Suite

**Config File**: `solune/frontend/playwright.config.ts`
**Target**: ≥14 passing E2E specs (up from 10).

**Verification Command**:
```bash
cd solune/frontend && npm run test:e2e
```

---

### Contract 8: Pre-commit Hook Coverage

**File**: `solune/scripts/pre-commit`

**Contract**: Pre-commit hooks MUST run the following on changed files:
- Backend: `ruff format` + `ruff check` + `pyright` (already implemented)
- Frontend: `eslint` + `tsc --noEmit` (already implemented)

**Verification**: Manual — commit a file with a lint violation and verify the hook blocks it.

## Phase Gate Contracts

The following gates define when each phase is considered complete:

| Phase | Gate | Pass Criteria |
|-------|------|---------------|
| Phase 1 | Static analysis complete | Lint + type-check reports generated for both codebases |
| Phase 1 | Test execution complete | All test suites run with results captured |
| Phase 1 | Flaky detection complete | `detect_flaky.py` run with ≥5 iterations |
| Phase 2 | Mutmut trampoline fixed | Kill rate >0% on at least one shard |
| Phase 2 | Cache leakage fixed | No stale cache observed across test boundaries |
| Phase 2 | AsyncMock warnings eliminated | Zero `AsyncMock` warnings in test output |
| Phase 2 | Pipeline transitions fixed | Valid transitions accepted, invalid rejected |
| Phase 3 | Backend coverage ≥80% | `--cov-fail-under=80` passes |
| Phase 3 | Mutation kill rate >60%/shard | Each shard exceeds threshold |
| Phase 4 | Frontend coverage ≥55/50/45 | All vitest thresholds pass |
| Phase 4 | E2E specs ≥14 | Playwright reports ≥14 passing specs |
| Phase 5 | Thresholds ratcheted | Config files updated with higher values |
| Phase 5 | Chaos/concurrency tests added | New test files exist and pass |
