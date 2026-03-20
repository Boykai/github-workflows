# Verification Commands: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Feature**: `052-fix-bugs-test-coverage`
**Date**: 2026-03-19

All commands are run from the repository root (`apps/solune/`).

## Phase A: Static Analysis

```bash
# GA-01: Frontend lint
cd frontend && npx eslint .

# GA-02: Frontend type-check
cd frontend && npx tsc --noEmit

# GA-03: Backend lint
cd backend && ruff check src/

# GA-04: Backend type-check
cd backend && pyright

# GA-05: Backend security scan
cd backend && bandit -r src/ -s B104,B608

# GA-06: Flaky test detection (backend)
cd backend && python scripts/detect_flaky.py

# GA-06: Flaky test detection (frontend)
cd frontend && for i in 1 2 3 4 5; do npx vitest run --reporter=json > "run-$i.json" 2>&1; done
# Compare results across runs for inconsistencies

# GA-07: Zero AsyncMock warnings
cd backend && pytest 2>&1 | grep -c "AsyncMock"
# Expected output: 0
```

## Phase B: Backend Coverage

```bash
# GB-01: Backend line coverage ≥ 80%
cd backend && pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Coverage with HTML report
cd backend && pytest --cov=src --cov-report=html --cov-fail-under=80
```

## Phase C: Frontend Coverage

```bash
# GC-01: Frontend coverage ≥ 55/50/45/55
cd frontend && npx vitest run --coverage

# Thresholds are enforced in vitest.config.ts:
# statements: 55, branches: 50, functions: 45, lines: 55
```

## Phase D: Mutation Testing

```bash
# GD-01: Backend mutation shards (run each independently)
cd backend && python scripts/run_mutmut_shard.py --shard auth-and-projects
cd backend && python scripts/run_mutmut_shard.py --shard orchestration
cd backend && python scripts/run_mutmut_shard.py --shard app-and-data
cd backend && python scripts/run_mutmut_shard.py --shard agents-and-integrations
cd backend && python scripts/run_mutmut_shard.py --shard api-and-middleware

# View results
cd backend && mutmut results

# GD-01: Frontend mutation (Stryker)
cd frontend && npx stryker run
```

## Phase E: CI Enforcement

```bash
# GE-01: Verify threshold configuration
grep "fail_under" backend/pyproject.toml
# Expected: fail_under = 80

grep -A4 "thresholds" frontend/vitest.config.ts
# Expected: statements: 55, branches: 50, functions: 45, lines: 55

# GE-02: Pre-commit timing
time scripts/pre-commit
# Expected: < 30 seconds

# GE-03: CI ratchet enforcement
# Push a commit that removes a test file → CI must reject

# GE-04: Emergency override documentation
cat docs/emergency-override.md  # or equivalent location
```

## Full Verification Sequence

Run all gates in order to verify complete implementation:

```bash
cd apps/solune

# Phase A
cd frontend && npx eslint . && npx tsc --noEmit && cd ..
cd backend && ruff check src/ && pyright && bandit -r src/ -s B104,B608 && cd ..
cd backend && python scripts/detect_flaky.py && cd ..
cd backend && pytest 2>&1 | grep -c "AsyncMock" && cd ..

# Phase B
cd backend && pytest --cov=src --cov-report=term-missing --cov-fail-under=80 && cd ..

# Phase C
cd frontend && npx vitest run --coverage && cd ..

# Phase D
cd backend && python scripts/run_mutmut_shard.py --shard auth-and-projects && cd ..
cd backend && python scripts/run_mutmut_shard.py --shard orchestration && cd ..
cd backend && python scripts/run_mutmut_shard.py --shard app-and-data && cd ..
cd backend && python scripts/run_mutmut_shard.py --shard agents-and-integrations && cd ..
cd backend && python scripts/run_mutmut_shard.py --shard api-and-middleware && cd ..
cd frontend && npx stryker run && cd ..

# Phase E
grep "fail_under" backend/pyproject.toml
time scripts/pre-commit
```
