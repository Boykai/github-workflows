# Test Coverage Contract

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20

## Coverage Thresholds

This contract defines the minimum coverage requirements that must be met before the feature branch can be merged.

### Aggregate Coverage Target

| Metric | Minimum | Scope |
|--------|---------|-------|
| Line coverage | 85% | All frontend + backend source files combined |
| Branch coverage | Best effort | Not a hard gate; tracked for visibility |
| Statement coverage | 85% | All frontend + backend source files combined |

### Frontend Coverage (Vitest)

**Command**: `cd frontend && npm run test:coverage`

| Category | Files | Minimum Coverage |
|----------|-------|-----------------|
| Hooks | `src/hooks/*.ts` | 85% (high logic density) |
| Services | `src/services/*.ts` | 85% (API integration layer) |
| Components | `src/components/**/*.tsx` | Best effort (UI rendering, lower priority) |
| Pages | `src/pages/*.tsx` | Best effort |

**Excluded from coverage**: `src/vite-env.d.ts`, `src/main.tsx` (entry point with no logic), `src/types/index.ts` (type-only)

### Backend Coverage (pytest-cov)

**Command**: `cd backend && python -m pytest --cov=src --cov-report=term-missing`

| Category | Files | Minimum Coverage |
|----------|-------|-----------------|
| API routes | `src/api/*.py` | 85% |
| Services | `src/services/*.py` | 85% (where feasible without external dependencies) |
| Models | `src/models/*.py` | 85% |
| Config/Exceptions | `src/config.py`, `src/exceptions.py`, `src/constants.py` | Best effort |

**Excluded from coverage**: `src/migrations/`, `src/prompts/` (static templates)

## Test Quality Requirements

| Requirement | Enforcement |
|-------------|-------------|
| AAA pattern (Arrange-Act-Assert) | Code review |
| Test isolation (no shared mutable state) | Each test sets up its own fixtures via `beforeEach`/`setUp` |
| Determinism (same result every run) | No time-dependent, network-dependent, or order-dependent tests |
| No coverage inflation | Each test must validate a real behavior or user flow |

## Verification Commands

```bash
# Frontend coverage
cd frontend && npm run test:coverage

# Backend coverage
cd backend && python -m pytest --cov=src --cov-report=term-missing

# Full test suite (no regressions)
cd frontend && npm test
cd backend && python -m pytest
```
