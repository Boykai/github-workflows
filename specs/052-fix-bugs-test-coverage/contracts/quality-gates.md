# Quality Gates: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Feature**: `052-fix-bugs-test-coverage`
**Date**: 2026-03-19

## Phase A Gates (Static Analysis)

### GA-01: Frontend Lint Clean

- **Metric**: Zero lint violations
- **Threshold**: Exit code 0
- **Tool**: ESLint with TypeScript, React hooks, jsx-a11y, and security plugins
- **Scope**: All `.ts` and `.tsx` files under `apps/solune/frontend/src/`
- **Blocking**: Phases B, C

### GA-02: Frontend Type-Check Clean

- **Metric**: Zero type errors in strict mode
- **Threshold**: Exit code 0
- **Tool**: TypeScript compiler (`tsc --noEmit`, strict: true, target: ES2022)
- **Scope**: All TypeScript files under `apps/solune/frontend/`
- **Blocking**: Phases B, C

### GA-03: Backend Lint Clean

- **Metric**: Zero lint violations
- **Threshold**: Exit code 0
- **Tool**: Ruff (target: py313, rules: E/W/F/I/B/C4/UP/FURB/PTH/PERF/RUF)
- **Scope**: All Python files under `apps/solune/backend/src/`
- **Blocking**: Phases B, C

### GA-04: Backend Type-Check Clean

- **Metric**: Zero type errors
- **Threshold**: Exit code 0
- **Tool**: Pyright (standard mode, Python 3.13)
- **Scope**: All Python files under `apps/solune/backend/src/`
- **Blocking**: Phases B, C

### GA-05: Backend Security Scan Clean

- **Metric**: Zero security issues (excluding documented false positive suppressions B104, B608)
- **Threshold**: Exit code 0
- **Tool**: Bandit (severity: medium, confidence: medium)
- **Scope**: `apps/solune/backend/src/` (excluding `tests/`)
- **Blocking**: Phases B, C

### GA-06: Zero Flaky Tests

- **Metric**: Zero tests with mixed pass/fail across 5 iterations
- **Threshold**: Empty flaky test list
- **Tool**: `detect_flaky.py` (backend), `vitest run` ×5 diff (frontend)
- **Scope**: All test suites
- **Blocking**: Phases B, C

### GA-07: Zero AsyncMock Warnings

- **Metric**: Zero deprecation warnings related to AsyncMock
- **Threshold**: `grep -c "AsyncMock" == 0` in test output
- **Scope**: Backend test suite
- **Blocking**: Phases B, C

## Phase B Gate (Backend Coverage)

### GB-01: Backend Line Coverage ≥ 80%

- **Metric**: Line coverage percentage
- **Threshold**: ≥ 80% (current: 75%)
- **Tool**: pytest-cov with `--cov-fail-under=80`
- **Scope**: `apps/solune/backend/src/`
- **Blocking**: Phase D

## Phase C Gate (Frontend Coverage)

### GC-01: Frontend Coverage ≥ 55/50/45/55

- **Metric**: Statement / Branch / Function / Line coverage
- **Threshold**: ≥ 55% statements, ≥ 50% branches, ≥ 45% functions, ≥ 55% lines
- **Tool**: Vitest with @vitest/coverage-v8
- **Scope**: `apps/solune/frontend/src/`
- **Blocking**: Phase D

## Phase D Gates (Mutation)

### GD-01: Mutation Kill Rate > 60% Per Shard

- **Metric**: Percentage of mutants killed
- **Threshold**: > 60% per shard (5 backend shards + 1 frontend Stryker)
- **Tools**: mutmut (backend), Stryker (frontend)
- **Scope**: All mutation shards
- **Blocking**: Phase E

### GD-02: All Killable Survivors Addressed

- **Metric**: Zero unresolved killable mutant survivors
- **Threshold**: Every killable survivor has a targeted assertion
- **Scope**: All shards
- **Blocking**: Phase E

## Phase E Gates (CI Enforcement)

### GE-01: Thresholds Ratcheted in Configuration

- **Metric**: Configuration files updated with new thresholds
- **Verification**: `fail_under = 80` in `pyproject.toml`, thresholds 55/50/45/55 in `vitest.config.ts`
- **Blocking**: Final report

### GE-02: Pre-Commit Hooks Under 30 Seconds

- **Metric**: Wall-clock time for pre-commit on changed files
- **Threshold**: < 30 seconds
- **Tool**: `time scripts/pre-commit`
- **Blocking**: Final report

### GE-03: CI Ratchet Enforcement Verified

- **Metric**: CI rejects coverage-lowering commits
- **Verification**: Push a test commit that lowers coverage → CI must fail
- **Blocking**: Final report

### GE-04: Emergency Override Documented

- **Metric**: `SKIP_COVERAGE=1` bypass process documented with audit trail
- **Verification**: Documentation exists in project docs
- **Blocking**: Final report
