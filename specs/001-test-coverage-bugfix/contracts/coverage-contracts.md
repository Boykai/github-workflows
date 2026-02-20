# Contracts: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20 | **Phase**: 1

## Overview

This feature does not introduce new API endpoints, modify existing contracts, or change data exchange formats. The work is test-only (new test files) and bug-fix-only (corrections to existing behavior). This document defines the **test contracts** — the coverage thresholds and quality gates that constitute the deliverable.

## Coverage Contract

### Aggregate Threshold

| Metric | Target | Scope |
|--------|--------|-------|
| Line coverage | ≥ 85% | Frontend + Backend combined |
| Branch coverage | ≥ 85% | Frontend + Backend combined |
| Statement coverage | ≥ 85% | Frontend + Backend combined |

### Coverage Tool Configuration

**Frontend** (Vitest + @vitest/coverage-v8):
- Report formats: text, lcov, json-summary
- Exclusions: `vite-env.d.ts`, `main.tsx` (entry point), `types/index.ts` (type-only)

**Backend** (pytest-cov):
- Report formats: term-missing, xml, json
- Exclusions: `migrations/`, `__init__.py`, `config.py` (environment-dependent)

## Test Quality Contract

All new tests MUST satisfy:

| Requirement | Validation Method |
|-------------|-------------------|
| AAA pattern | Code review — each test has clear Arrange/Act/Assert sections |
| Isolation | No shared mutable state; each test sets up and tears down independently |
| Determinism | No timing-dependent assertions; all external calls mocked |
| Meaningful | Each test validates a real behavior, not just code path traversal |

## File Change Contract

### New Files (Tests Only)

| Location | Pattern | Description |
|----------|---------|-------------|
| `frontend/src/hooks/` | `use*.test.tsx` | Hook unit tests |
| `frontend/src/components/*/` | `*.test.tsx` | Component unit tests |
| `frontend/src/services/` | `*.test.ts` | Service layer tests |
| `frontend/src/pages/` | `*.test.tsx` | Page integration tests |
| `backend/tests/unit/` | `test_*.py` | Backend unit tests |
| `backend/tests/integration/` | `test_*.py` | Backend integration tests |

### Modified Files (Bug Fixes Only)

Bug fixes modify existing source files. Each modification:
- Is accompanied by a test that exposes the bug
- Has a separate commit message prefixed with `fix:`
- Is documented in the PR description

### No Deleted Files

This feature does not delete any files.
