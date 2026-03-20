# Contracts: Verification Commands

**Feature Branch**: `051-fix-bugs-test-coverage`
**Date**: 2026-03-19

## Verification Command Reference

This document provides the complete set of commands to verify each phase of the
Find & Fix Bugs, Increase Test Coverage (Phase 2) feature. All commands are run
from the repository root (the directory containing `solune/`).

### Phase A: Static Analysis Completion

```bash
# Frontend lint (expect zero violations)
cd solune/frontend && \
  npx eslint . --max-warnings=0

# Frontend type-check (expect zero errors)
cd solune/frontend && \
  npx tsc --noEmit

# Backend lint (expect zero violations)
cd solune/backend && \
  .venv/bin/ruff check src/

# Backend type-check (expect zero errors)
cd solune/backend && \
  .venv/bin/pyright src/

# Backend security scan (expect zero issues)
cd solune/backend && \
  .venv/bin/bandit -r src/ -c pyproject.toml

# Flaky test detection — backend
cd solune/backend && \
  python scripts/detect_flaky.py --runs=5

# Flaky test detection — frontend (run 5 times, compare)
cd solune/frontend && \
  for i in 1 2 3 4 5; do \
    echo "=== Run $i ===" && \
    npm run test -- --reporter=verbose 2>&1 | tail -5; \
  done
```

### Phase B: Backend Coverage Verification

```bash
# Overall coverage check (expect ≥80%)
cd solune/backend && \
  .venv/bin/python -m pytest tests/ \
    --cov=src --cov-report=term-missing --cov-fail-under=80

# Integration test verification (API routes)
cd solune/backend && \
  .venv/bin/python -m pytest tests/integration/ -q --tb=short

# Property-based test verification
cd solune/backend && \
  .venv/bin/python -m pytest tests/property/ -q --tb=short

# Dependency injection module coverage
cd solune/backend && \
  .venv/bin/python -m pytest tests/unit/test_dependencies.py \
    --cov=src/dependencies --cov-report=term-missing

# Mutation testing (all 4 shards)
cd solune/backend && \
  for shard in auth-and-projects orchestration app-and-data agents-and-integrations; do \
    echo "=== Shard: $shard ===" && \
    python scripts/run_mutmut_shard.py --shard=$shard; \
  done
```

### Phase C: Frontend Coverage Verification

```bash
# Overall coverage check (expect ≥55/50/45)
cd solune/frontend && \
  npm run test:coverage

# Board component tests
cd solune/frontend && \
  npx vitest run src/components/board/__tests__/ --reporter=verbose

# Hook tests
cd solune/frontend && \
  npx vitest run src/hooks/__tests__/ --reporter=verbose

# Utility library tests
cd solune/frontend && \
  npx vitest run src/lib/__tests__/ --reporter=verbose

# Mutation testing (Stryker)
cd solune/frontend && \
  npx stryker run
```

### Phase D: Mutation Verification

```bash
# Backend mutation — all shards (expect ≥60% each)
cd solune/backend && \
  for shard in auth-and-projects orchestration app-and-data agents-and-integrations; do \
    echo "=== Shard: $shard ===" && \
    python scripts/run_mutmut_shard.py --shard=$shard; \
  done

# Frontend mutation (expect ≥80% high / 60% low)
cd solune/frontend && \
  npx stryker run

# Review surviving mutants
cd solune/backend && \
  python scripts/run_mutmut_shard.py --shard=auth-and-projects --show-surviving
```

### Phase E: Final Verification

```bash
# Complete backend verification
cd solune/backend && \
  .venv/bin/ruff check src/ && \
  .venv/bin/pyright src/ && \
  .venv/bin/bandit -r src/ -c pyproject.toml && \
  .venv/bin/python -m pytest tests/ \
    --cov=src --cov-report=term-missing --cov-fail-under=80

# Complete frontend verification
cd solune/frontend && \
  npx eslint . --max-warnings=0 && \
  npx tsc --noEmit && \
  npm run test:coverage

# AsyncMock warning check (expect zero matches)
cd solune/backend && \
  set -o pipefail && \
  .venv/bin/python -m pytest tests/ -q 2>&1 | tee /dev/stderr | \
  { ! grep -qi "asyncmock"; } && \
  echo "PASS: No AsyncMock warnings" || \
  { echo "FAIL: AsyncMock warnings found"; exit 1; }

# Pre-commit hook timing (expect <30 seconds)
cd solune && \
  time scripts/pre-commit

# Final flaky test detection
cd solune/backend && \
  python scripts/detect_flaky.py --runs=5
cd solune/frontend && \
  for i in 1 2 3 4 5; do npm run test 2>&1 | tail -3; done
```

## Quick Reference

| Phase | Gate | Command | Expected |
|-------|------|---------|----------|
| A | Frontend lint | `npx eslint . --max-warnings=0` | 0 violations |
| A | Frontend types | `npx tsc --noEmit` | 0 errors |
| A | Backend lint | `ruff check src/` | 0 violations |
| A | Backend types | `pyright src/` | 0 errors |
| A | Backend security | `bandit -r src/ -c pyproject.toml` | 0 issues |
| A | Flaky tests | `detect_flaky.py --runs=5` | 0 flaky |
| B | Backend coverage | `pytest --cov-fail-under=80` | ≥80% |
| B | Backend mutation | `run_mutmut_shard.py --shard=*` | ≥60% each |
| C | Frontend coverage | `npm run test:coverage` | ≥55/50/45 |
| C | Frontend mutation | `npx stryker run` | ≥80% high |
| E | Pre-commit hooks | `time scripts/pre-commit` | <30s |
| E | AsyncMock warnings | `grep -qi asyncmock` | 0 matches |
