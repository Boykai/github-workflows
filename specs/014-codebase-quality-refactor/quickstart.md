# Quickstart: Codebase Quality Refactor Implementation Guide

## Prerequisites

- Python 3.12+ with backend dependencies installed (`cd backend && pip install -e ".[dev]"`)
- Node 20+ with frontend dependencies installed (`cd frontend && npm install`)
- Familiarity with the project structure: `backend/src/` (FastAPI), `frontend/src/` (React/Vite)

## Implementation Order

All user stories are independent and can be implemented in any order. The recommended order below groups by priority and minimizes context switching.

### Phase A — High Priority Bug Fixes (P1)

1. **`backend/src/constants.py`** (US1) — Replace `DEFAULT_STATUS_COLUMNS` values with `StatusNames` references.
   - Change: `["Todo", "In Progress", "Done"]` → `[StatusNames.BACKLOG, StatusNames.IN_PROGRESS, StatusNames.DONE]`
   - Update test in `backend/tests/unit/test_config.py` to match new values.
   - Verify: `cd backend && pytest tests/unit/test_config.py::TestConstants -v`

2. **`backend/src/dependencies.py`** (US2) — Fix admin auto-promotion race condition.
   - Replace SELECT + UPDATE with atomic `UPDATE ... WHERE admin_github_user_id IS NULL`
   - Check `cursor.rowcount` to determine if promotion succeeded
   - On `rowcount == 0`: re-read admin_user_id, compare with session, raise 403 if mismatch
   - Verify: `cd backend && pytest tests/unit/test_admin_authorization.py -v`

### Phase B — Medium Priority Reliability (P2)

3. **`backend/src/main.py`** (US3) — Wrap lifespan startup in try/finally.
   - Initialize `cleanup_task = None` before try block
   - Move `yield` inside try block
   - Move all cleanup (stop listener, cancel task, close DB) into finally block
   - Guard each cleanup step: only run if resource was initialized
   - Verify: `cd backend && pytest tests/unit/test_main.py::TestLifespan -v`

4. **`backend/Dockerfile`** + **`docker-compose.yml`** (US4) — Replace httpx healthcheck with urllib.
   - In `backend/Dockerfile` line 37: replace `import httpx; httpx.get(...)` with `import urllib.request; urllib.request.urlopen(...)`
   - In `docker-compose.yml` backend healthcheck: same replacement
   - Verify: `docker compose build backend && docker compose up -d backend && docker compose ps` (check health status)

5. **`backend/src/config.py`** + **`backend/src/api/auth.py`** (US5) — Add effective_cookie_secure.
   - Add `@property effective_cookie_secure` to `Settings` class
   - Update `_set_session_cookie()` in `auth.py`: `secure=settings.effective_cookie_secure`
   - Verify: `cd backend && pytest tests/unit/test_config.py::TestSettings -v`

### Phase C — Low Priority Quality (P3)

6. **`backend/src/utils.py`** (US6) — BoundedDict already complete.
   - **No code changes needed** — all methods already implemented.
   - Verify: `cd backend && pytest tests/unit/test_utils.py::TestBoundedDict -v`

7. **`frontend/package.json`** (US7) — Remove jsdom.
   - Remove `"jsdom": "^27.4.0"` from devDependencies
   - Run `cd frontend && npm install` to update lockfile
   - Verify: `cd frontend && npm test`

8. **`backend/src/config.py`** (US8) — Add clear_settings_cache().
   - Add function below `get_settings()`: `def clear_settings_cache() -> None: get_settings.cache_clear()`
   - Verify: `cd backend && pytest tests/unit/test_config.py::TestGetSettings -v`

9. **`backend/src/main.py`** (US9) — Add exponential backoff to cleanup loop.
   - Add `consecutive_failures = 0` counter
   - Compute `backoff = min(interval * (2 ** consecutive_failures), 300)` for sleep
   - Reset counter on success, increment on failure
   - Verify: `cd backend && pytest tests/unit/test_main.py::TestSessionCleanupLoop -v`

10. **`backend/src/config.py`** (US10) — Update env_file to check both paths.
    - Change `env_file="../.env"` to `env_file=("../.env", ".env")`
    - Verify: `cd backend && pytest tests/unit/test_config.py::TestSettings -v`

## Testing Strategy

### Backend
```bash
cd backend

# Run all tests
pytest -v

# Run specific test classes
pytest tests/unit/test_config.py -v           # US1, US5, US8, US10
pytest tests/unit/test_admin_authorization.py -v  # US2
pytest tests/unit/test_main.py -v               # US3, US9
pytest tests/unit/test_utils.py -v              # US6 (verification only)

# Lint
ruff check src tests && ruff format --check src tests
```

### Frontend
```bash
cd frontend

# Run all tests
npm test

# Lint
npm run lint
```

## Key Files Summary

| File | User Story | Change Type |
|------|-----------|-------------|
| `backend/src/constants.py` | US1 | Bug fix — replace invalid status name |
| `backend/src/dependencies.py` | US2 | Bug fix — atomic SQL for race condition |
| `backend/src/main.py` | US3, US9 | Reliability — try/finally + backoff |
| `backend/Dockerfile` | US4 | Performance — lightweight healthcheck |
| `docker-compose.yml` | US4 | Performance — lightweight healthcheck |
| `backend/src/config.py` | US5, US8, US10 | Feature — cookie security, cache util, env paths |
| `backend/src/api/auth.py` | US5 | Feature — use effective_cookie_secure |
| `backend/src/utils.py` | US6 | None — already complete |
| `frontend/package.json` | US7 | Cleanup — remove unused dependency |
| `backend/tests/unit/test_config.py` | US1 | Test update — match new default values |
