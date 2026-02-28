# Quickstart: Increase Meaningful Test Coverage, Fix Discovered Bugs, and Enforce DRY Best Practices

**Feature**: 013-test-coverage-dry | **Date**: 2026-02-28

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm (ships with Node.js)

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
```

### Frontend

```bash
cd frontend
npm ci
```

## Running Tests

### Backend Tests

```bash
# Run all backend tests
cd backend
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run a specific test file
pytest tests/unit/test_api_auth.py

# Run a specific test class
pytest tests/unit/test_api_auth.py::TestGetCurrentUser

# Run a specific test method
pytest tests/unit/test_api_auth.py::TestGetCurrentUser::test_returns_user_info

# Run only integration tests
pytest tests/integration/ -m integration

# Run with verbose output
pytest -v
```

### Frontend Unit Tests

```bash
# Run all frontend unit tests
cd frontend
npm test

# Run in watch mode (re-runs on file changes)
npm run test:watch

# Run with coverage
npm run test:coverage

# Run a specific test file
npx vitest run src/hooks/useAuth.test.tsx
```

### Frontend E2E Tests

```bash
# Install Playwright browsers (first time only)
cd frontend
npx playwright install

# Run E2E tests
npm run test:e2e

# Run with visible browser
npm run test:e2e:headed

# Run with Playwright UI
npm run test:e2e:ui

# View last test report
npm run test:e2e:report
```

## Linting and Type Checking

### Backend

```bash
cd backend

# Lint
ruff check src tests

# Format check
ruff format --check src tests

# Type check
pyright src
```

### Frontend

```bash
cd frontend

# Lint
npm run lint

# Type check
npm run type-check

# Build (also validates types)
npm run build
```

## Key Directories

| Path | Description |
|------|-------------|
| `backend/tests/conftest.py` | Shared pytest fixtures (mock_session, mock_db, client) |
| `backend/tests/helpers/` | Shared test factories, assertions, mock builders (NEW) |
| `backend/tests/unit/` | Backend unit tests mirroring `src/` structure |
| `backend/tests/integration/` | Backend integration tests |
| `frontend/src/test/setup.ts` | Vitest global setup (mock factories, polyfills) |
| `frontend/src/test/test-utils.tsx` | React render helpers for testing |
| `frontend/src/test/factories/` | Frontend test data factories (NEW) |
| `frontend/e2e/` | Playwright E2E tests |

## Workflow for This Feature

### 1. Audit Phase (User Stories 1)
- Run all existing tests to establish baseline
- Classify each test as meaningful, redundant, or misaligned
- Document findings in audit report

### 2. Cleanup Phase (User Stories 1, 4)
- Remove redundant tests
- Rewrite misaligned tests
- Extract shared utilities to helpers modules

### 3. Coverage Phase (User Story 2)
- Add missing tests for critical flows
- Use factories and helpers from step 2
- Verify coverage improvement with `pytest-cov` and `vitest --coverage`

### 4. Bug Fix Phase (User Story 3)
- For each discovered bug: write failing test → fix → verify
- Each fix gets a dedicated regression test

### 5. Best Practices Phase (User Stories 5, 6)
- Apply AAA pattern to all tests
- Ensure descriptive naming
- Verify test isolation
- Re-enable backend tests in CI

### 6. Verification
- Run full suite: `cd backend && pytest && cd ../frontend && npm test`
- Verify CI: All tests pass in CI pipeline
- Run 5+ times to confirm no flakiness
