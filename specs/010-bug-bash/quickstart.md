# Quickstart: Bug Bash Implementation Guide

**Date**: 2026-02-24 | **Branch**: `010-bug-bash`

## Prerequisites

- Python 3.11+, Node.js 18+, Docker & Docker Compose
- Clone and checkout: `git checkout 010-bug-bash`
- Copy `.env.example` to `.env` (if available) or set env vars below

## Environment Variables (New / Changed)

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ENCRYPTION_KEY` | No | Auto-generated (warn) | Fernet key for encrypting tokens at rest |

Generate a key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

## Running Locally

```bash
docker compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Implementation Order

Work through these phases sequentially. Each phase is independently testable.

### Phase A — Foundation (No Breaking Changes)

1. **`backend/src/utils.py`** — Add `BoundedSet` and `BoundedDict` classes.
2. **`backend/src/services/encryption.py`** — Create `EncryptionService` with Fernet encrypt/decrypt and passthrough mode.
3. **`backend/src/middleware/request_id.py`** — Create `RequestIDMiddleware` with `request_id_var` ContextVar.
4. **`backend/src/config.py`** — Add `encryption_key: str | None = None` to Settings.
5. **`backend/src/main.py`** — Register `RequestIDMiddleware`.

**Test**: Run `pytest` — all existing tests should pass. Middleware + encryption are additive, not breaking.

### Phase B — Security Fixes

6. **`backend/src/migrations/003_add_admin_column.sql`** — Add `admin_github_user_id` column.
7. **`backend/src/services/session_store.py`** — Integrate `EncryptionService` for token encrypt/decrypt.
8. **`backend/src/api/auth.py`** — Move session token from URL param to `Set-Cookie` (HttpOnly, Secure, SameSite=Lax).
9. **`backend/src/api/auth.py`** — Gate `/dev-login` behind `Settings.debug`.
10. **`backend/src/dependencies.py`** — Add `require_admin()` dependency.
11. **`backend/src/api/settings.py`** — Apply `require_admin` to global settings PUT.
12. **`backend/src/api/webhooks.py`** — Enforce webhook signature verification in production.
13. **`backend/src/services/github_auth.py`** — Replace unbounded `_oauth_states` dict with `BoundedDict(1000)` + TTL.

**Test**: Run `pytest` — update auth tests for cookie-based flow. Verify dev-login returns 404 when `debug=False`.

### Phase C — DRY & Correctness

14. **`backend/src/api/workflow.py`** — Replace 4+ inline repo resolution with `resolve_repository()` calls.
15. **`backend/src/api/projects.py`** — Same: use `resolve_repository()`.
16. **`backend/src/services/github_projects/service.py`** — Extract `_build_headers()` method, replace 10+ inline dicts.
17. **`backend/src/services/github_projects/service.py`** — Extract `_filter_pull_requests()`, replace 3 inline filters.
18. **`backend/src/services/github_projects/graphql.py`** — Implement cursor-based pagination for comments (currently hardcoded `first: 100`).
19. **`backend/src/services/copilot_polling/completion.py`** — Fix false-positive Signal 3 (require SHA advance, not just unassignment).
20. **`backend/src/services/copilot_polling/state.py`** — Replace 8 global mutable variables with `BoundedSet`/`BoundedDict`.
21. **`backend/src/services/workflow_orchestrator/orchestrator.py`** — Remove circular import try/except; use lazy import in factory.
22. **`backend/src/api/chat.py`** — Replace direct service imports with DI pattern.

**Test**: Run full test suite. Existing behavior should be identical; only internal structure changes.

### Phase D — Resilience & Observability

23. **`backend/src/main.py`** — Add `Retry-After` header to 429 error handler.
24. **`backend/src/main.py`** — Implement structured health check at `/api/v1/health`.
25. **`backend/src/api/tasks.py`** — Return 501 for unimplemented task status endpoint.
26. **`frontend/src/hooks/useRealTimeSync.ts`** — Stop polling when WebSocket connects; add exponential backoff with jitter on WS reconnect.

**Test**: Full backend + frontend test suite. Verify health endpoint returns structured response.

### Phase E — Confirmation

27. Run `pytest --tb=short -q` — all tests pass.
28. Run `npm run test` in `frontend/` — all tests pass.
29. Run `docker compose up --build` — verify end-to-end functionality.

## Key Testing Commands

```bash
# Backend
cd backend && python -m pytest tests/ -v --tb=short

# Frontend
cd frontend && npm run test

# E2E
cd frontend && npx playwright test
```

## Verification Checklist

- [x] Session token no longer appears in URL/logs
- [x] `/dev-login` returns 404 when `debug=False`
- [x] Health endpoint returns structured JSON with component statuses
- [x] 429 responses include `Retry-After` header
- [x] All responses include `X-Request-ID` header
- [x] Global settings require admin authorization
- [x] Webhook signature verified in production mode
- [x] Task status endpoint returns 501
- [x] No inline repo resolution patterns remain in route handlers
- [x] No inline header dicts remain in `GitHubProjectsService`
