# Quickstart: Bug Bash Implementation Guide

## Prerequisites

- Python 3.12+ with backend dependencies installed (`cd backend && pip install -e ".[dev]"`)
- Node 20+ with frontend dependencies installed (`cd frontend && npm install`)
- Familiarity with the project structure: `backend/src/` (FastAPI + aiosqlite), `frontend/src/` (React + Vite)
- Read `specs/016-codebase-bug-bash/contracts/audit-standards.md` for commit and comment conventions

## Baseline Verification

Before starting any audit work, establish that the codebase is in a clean state:

```bash
# Backend: tests + lint + type check
cd backend
pytest -v
ruff check src tests
ruff format --check src tests
pyright

# Frontend: tests + lint + type check
cd frontend
npm test
npm run lint
npm run type-check
```

If any pre-existing failures exist, document them and exclude from findings.

## Implementation Order

The audit follows strict priority ordering. Within each phase, audit backend first, then frontend, then infrastructure.

### Phase 1 — 🔴 Security Audit (P1)

**Key files to review** (in order):

| # | File | What to look for |
|---|------|------------------|
| 1 | `backend/src/api/auth.py` | OAuth flow, session cookies, redirect validation, token handling |
| 2 | `backend/src/dependencies.py` | Admin authorization, session validation, TOCTOU races |
| 3 | `backend/src/config.py` | Secret management, env var handling, cookie security defaults |
| 4 | `backend/src/services/database.py` | SQL injection in query construction, parameterized queries |
| 5 | `backend/src/services/github_projects/service.py` | Token usage, API call security, input validation |
| 6 | `backend/src/api/chat.py` | User input handling, command injection, XSS in responses |
| 7 | `backend/src/api/*.py` (remaining) | Input validation, authentication enforcement |
| 8 | `frontend/src/services/api.ts` | Credential handling, CORS, sensitive data in URLs |
| 9 | `frontend/src/components/**` | XSS via dangerouslySetInnerHTML, unsanitized user content |
| 10 | `.github/workflows/*.yml` | Secret exposure, insecure action versions |

**Verification**: `cd backend && pytest tests/ -v && cd ../frontend && npm test`

### Phase 2 — 🟠 Runtime Error Audit (P1)

**Key patterns to check**:

| Pattern | Where to look | What to verify |
|---------|---------------|----------------|
| Unhandled async exceptions | `backend/src/api/*.py`, `backend/src/services/*.py` | All async functions have proper try/except |
| SQLite connection leaks | `backend/src/services/database.py`, all `get_db()` callers | `async with` or proper cleanup |
| Null reference access | `backend/src/services/github_projects/service.py` | Optional fields checked before access |
| Missing imports | All Python files | Pyright should catch these |
| WebSocket lifecycle | `frontend/src/hooks/useSocket*.ts` | Cleanup on unmount, reconnection handling |
| React error boundaries | `frontend/src/components/common/ErrorBoundary.tsx` | Coverage of all major component trees |

**Verification**: `cd backend && pytest -v && cd ../frontend && npm test`

### Phase 3 — 🟡 Logic Bug Audit (P2)

**Key patterns to check**:

| Pattern | Where to look | What to verify |
|---------|---------------|----------------|
| Off-by-one errors | Pagination, list slicing, loop boundaries | Boundary values tested |
| Wrong comparisons | Status checks, permission checks | Correct operators (==, !=, in) |
| State transitions | Board column moves, task status changes | Valid transitions enforced |
| Return value errors | Service methods, API handlers | Correct types and values returned |
| Boolean logic | Permission checks, feature flags | De Morgan's laws, short-circuit evaluation |

**Verification**: `cd backend && pytest -v && cd ../frontend && npm test`

### Phase 4 — 🔵 Test Gap Audit (P2)

**Key files to review**:

| # | Area | What to look for |
|---|------|------------------|
| 1 | `backend/tests/unit/*.py` | Assertions against mocks, never-failing asserts, mock leaks |
| 2 | `backend/tests/integration/*.py` | Proper test isolation, shared state contamination |
| 3 | `frontend/src/**/*.test.tsx` | Missing async waits, incomplete mock cleanup |
| 4 | `frontend/e2e/*.spec.ts` | Flaky selectors, missing assertions |
| 5 | Untested code paths | Compare source files against test files for coverage gaps |

**Verification**: `cd backend && pytest -v --cov=src && cd ../frontend && npm run test:coverage`

### Phase 5 — ⚪ Code Quality Audit (P3)

**Key patterns to check**:

| Pattern | Where to look | What to verify |
|---------|---------------|----------------|
| Dead code | All source files | Unreferenced functions, unused imports |
| Empty except blocks | `backend/src/**/*.py` | Silent error swallowing |
| Hardcoded values | Config-like values in source files | Should be in config.py or constants.py |
| Duplicated logic | Cross-file comparison | DRY violations |
| Unreachable branches | Complex conditionals | Dead else/elif paths |

**Verification**: `cd backend && ruff check src tests && cd ../frontend && npm run lint`

### Phase 6 — Summary Report

After all phases complete:

1. Compile all findings into the summary table (see format in `contracts/audit-standards.md`)
2. Run full verification suite:
   ```bash
   cd backend && pytest -v && ruff check src tests && ruff format --check src tests
   cd ../frontend && npm test && npm run lint && npm run type-check
   ```
3. Verify every Fix commit has a matching summary entry
4. Verify every TODO(bug-bash) comment has a matching summary entry
5. Report zero-finding categories explicitly

## Key Files Summary

| Area | File Count | Risk Level | Audit Priority |
|------|-----------|------------|----------------|
| Backend API (`backend/src/api/`) | ~14 files | High | All phases |
| Backend Services (`backend/src/services/`) | ~25 files | High | All phases |
| Backend Models (`backend/src/models/`) | ~12 files | Medium | Logic, Quality |
| Backend Tests (`backend/tests/`) | ~55 files | Medium | Test Quality |
| Frontend Components (`frontend/src/components/`) | ~50 files | Medium | Security (XSS), Runtime |
| Frontend Hooks (`frontend/src/hooks/`) | ~18 files | Medium | Runtime, Logic |
| Frontend Tests (`frontend/src/**/*.test.*`) | ~29 files | Medium | Test Quality |
| Infrastructure (Docker, CI, scripts) | ~8 files | Low | Security, Quality |
| SQL Migrations (`backend/src/migrations/`) | 9 files | Low | Security, Logic |
| Config files | ~10 files | Low | Security |

## Testing Commands Reference

```bash
# Backend — full suite
cd backend && pytest -v

# Backend — specific test file
cd backend && pytest tests/unit/test_auth.py -v

# Backend — with coverage
cd backend && pytest -v --cov=src --cov-report=term-missing

# Backend — lint + format
cd backend && ruff check src tests && ruff format --check src tests

# Backend — type check
cd backend && pyright

# Frontend — full suite
cd frontend && npm test

# Frontend — with coverage
cd frontend && npm run test:coverage

# Frontend — lint
cd frontend && npm run lint

# Frontend — type check
cd frontend && npm run type-check

# Frontend — E2E (requires running app)
cd frontend && npm run test:e2e
```
