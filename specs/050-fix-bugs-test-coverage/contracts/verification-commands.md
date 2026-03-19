# Contracts: Verification Commands

**Feature Branch**: `050-fix-bugs-test-coverage`
**Date**: 2026-03-19

## Verification Command Reference

This document provides the complete set of commands to verify each phase of the
Find/Fix Bugs & Increase Test Coverage feature. All commands are run from the
monorepo root (`solune/`).

### Phase 1: Static Analysis & Error Discovery

```bash
# Backend lint + type check
cd solune/backend && \
  .venv/bin/ruff check src/ && \
  .venv/bin/pyright src/

# Frontend lint + type check
cd solune/frontend && \
  npx eslint . --max-warnings=0 && \
  npx tsc --noEmit

# Backend test suite with results
cd solune/backend && \
  .venv/bin/python -m pytest tests/ -q --tb=short --junitxml=results.xml

# Frontend test suite
cd solune/frontend && \
  npm run test -- --reporter=verbose

# Frontend E2E
cd solune/frontend && \
  npm run test:e2e

# Flaky test detection
cd solune/backend && \
  python scripts/detect_flaky.py --runs=5
```

### Phase 2: Bug Fix Verification

```bash
# BUG-001: Mutmut trampoline — verify kill rate > 0%
cd solune/backend && \
  python scripts/run_mutmut_shard.py --shard=auth-and-projects

# BUG-002: Cache leakage — run integration + unit together
cd solune/backend && \
  .venv/bin/python -m pytest tests/unit/ tests/integration/ -q --tb=short

# BUG-003: AsyncMock warnings — verify zero warnings
cd solune/backend && \
  .venv/bin/python -m pytest tests/ -q 2>&1 | grep -i "asyncmock" && \
  echo "FAIL: AsyncMock warnings found" || echo "PASS: No AsyncMock warnings"

# BUG-004: Pipeline transitions — verify state machine
cd solune/backend && \
  .venv/bin/python -m pytest tests/unit/test_copilot_polling/ -q --tb=short
```

### Phase 3: Backend Coverage Verification

```bash
# Overall coverage check
cd solune/backend && \
  .venv/bin/python -m pytest tests/ \
    --cov=src --cov-report=term-missing --cov-fail-under=80

# Mutation testing (all shards)
cd solune/backend && \
  for shard in auth-and-projects orchestration app-and-data agents-and-integrations; do \
    echo "=== Shard: $shard ===" && \
    python scripts/run_mutmut_shard.py --shard=$shard; \
  done
```

### Phase 4: Frontend Coverage Verification

```bash
# Coverage check (includes threshold enforcement)
cd solune/frontend && npm run test:coverage

# E2E suite
cd solune/frontend && npm run test:e2e

# Mutation testing
cd solune/frontend && npm run test:mutate
```

### Phase 5: Hardening Verification

```bash
# Flaky test detection (extended)
cd solune/backend && python scripts/detect_flaky.py --runs=10

# Pre-commit hook test (manual)
# 1. Introduce a lint violation
# 2. Attempt to commit
# 3. Verify hook blocks the commit

# Chaos tests
cd solune/backend && \
  .venv/bin/python -m pytest tests/chaos/ -q --tb=short

# Concurrency tests
cd solune/backend && \
  .venv/bin/python -m pytest tests/concurrency/ -q --tb=short
```

### Full Verification Suite

```bash
# Run all verifications in sequence
cd solune/backend && \
  .venv/bin/python -m pytest tests/ \
    --cov=src --cov-report=term-missing --cov-fail-under=80 && \
  echo "✓ Backend coverage passed"

cd solune/frontend && \
  npm run test:coverage && \
  echo "✓ Frontend coverage passed"

cd solune/backend && \
  python scripts/detect_flaky.py --runs=10 && \
  echo "✓ No flaky tests"

cd solune/backend && \
  .venv/bin/python -m pytest tests/ -q 2>&1 | \
    (! grep -qi "asyncmock") && \
  echo "✓ No AsyncMock warnings"

cd solune/frontend && \
  npm run test:e2e && \
  echo "✓ E2E tests passed"

cd solune/backend && \
  python scripts/run_mutmut_shard.py --shard=auth-and-projects && \
  echo "✓ Mutation testing passed"

cd solune/frontend && \
  npm run test:mutate && \
  echo "✓ Frontend mutation testing passed"
```
