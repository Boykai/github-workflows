# CI Contract: Coverage Enforcement & Ratchet

**Feature**: `049-increase-test-coverage` | **Date**: 2026-03-17

## Purpose

Define the contract for coverage threshold enforcement in CI, including the ratchet pattern that ensures thresholds increase monotonically across phases.

## Backend Coverage Enforcement

### Producer

`pytest --cov=src --cov-report=term-missing`

### Consumer

CI backend job (`.github/workflows/ci.yml`)

### Configuration

```toml
# solune/backend/pyproject.toml
[tool.coverage.run]
source = ["src"]

[tool.coverage.report]
fail_under = 71  # Current threshold — bumped after each phase
show_missing = true
```

### Contract Rules

- `fail_under` MUST be a float between 0 and 100
- Any value below the threshold produces a non-zero exit code (CI fails)
- Report MUST include file paths and missing line numbers
- Threshold MUST only increase, never decrease (ratchet pattern)

### Ratchet Schedule

| Phase | Trigger | New `fail_under` |
|-------|---------|-------------------|
| Phase 2 complete | Backend high-ROI gaps merged | 76 |
| Phase 5 complete | Mutation-hardened tests merged | 80 |

## Frontend Coverage Enforcement

### Producer

`npm run test:coverage` (Vitest with `@vitest/coverage-v8`)

### Consumer

CI frontend job (`.github/workflows/ci.yml`)

### Configuration

```typescript
// solune/frontend/vitest.config.ts
coverage: {
  provider: 'v8',
  thresholds: {
    statements: 50,  // Current — bumped after each phase
    branches: 45,
    functions: 42,
    lines: 51,
  },
},
```

### Contract Rules

- All four metrics (statements, branches, functions, lines) MUST be enforced
- Any metric below its threshold produces a non-zero exit code (CI fails)
- Thresholds MUST only increase, never decrease (ratchet pattern)
- Each threshold is set 2% below actual achieved coverage to absorb minor fluctuations

### Ratchet Schedule

| Phase | Trigger | New thresholds (stmt/branch/func/lines) |
|-------|---------|----------------------------------------|
| Phase 3 complete | Hooks & services tested | 53/48/45/54 |
| Phase 4 complete | Components tested | 60/55/52/60 |

## Architecture Fitness Enforcement

### Producer

`pytest tests/architecture/ -v` (backend) and architecture test in frontend test suite

### Consumer

CI backend and frontend jobs

### Contract Rules

- Import boundary violations produce test failures
- Known-violations allowlist permits documented exceptions
- Allowlist can only shrink (violations removed) after initial baseline, never grow
- New violations must be fixed or explicitly justified and added to the plan

## Contract Validation

### Producer

`solune/scripts/validate-contracts.sh`

### Consumer

CI build job

### Contract Rules

- `createMockApi()` types MUST align with `openapi.json` schemas
- Exit code 0 on success, non-zero on contract drift
- Runs on every CI build to catch drift immediately

## Acceptance Criteria

1. ✅ Backend coverage threshold is enforced on every PR
2. ✅ Frontend coverage thresholds (4 metrics) are enforced on every PR
3. ✅ Thresholds never decrease across phases (ratchet pattern)
4. ✅ 2% buffer below actual coverage prevents false failures from code churn
5. ✅ Architecture tests run on every PR
6. ✅ Contract validation runs on every CI build
