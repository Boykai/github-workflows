# Research: Bug Bash — Codebase Quality & Reliability Sweep

**Date**: 2026-02-24 | **Branch**: `010-bug-bash` | **Plan**: [plan.md](plan.md)

## R1: Token Encryption at Rest (FR-003)

**Decision**: Use `cryptography.fernet.Fernet` for application-level symmetric encryption of GitHub OAuth tokens stored in SQLite.

**Rationale**: Fernet provides authenticated encryption (AES-128-CBC + HMAC-SHA256) with a single key. It's already available as a transitive dependency via `python-jose[cryptography]`. Performance overhead is negligible (~50μs per encrypt/decrypt) compared to GitHub API latency. Tokens expand ~57% in size, well within SQLite TEXT columns.

**Alternatives considered**:
- Database-level encryption (SQLCipher): Requires replacing aiosqlite driver — out of scope for bug bash.
- AES-GCM manual implementation: No advantage over Fernet; Fernet bundles IV+HMAC+versioning automatically.
- Store tokens in environment/memory only: Would require re-auth on every restart — poor UX.

**Implementation approach**:
- New module: `backend/src/services/encryption.py` with `init_encryption()`, `encrypt_token()`, `decrypt_token()`.
- Key source: `ENCRYPTION_KEY` env var → `Settings.encryption_key: str | None`. Auto-generate with warning if absent.
- Integration: encrypt on session save, decrypt on session load (`session_store.py`).
- Migration: Heuristic-based — Fernet ciphertext starts with `gAAAAA`, GitHub tokens start with `gho_`/`ghp_`. Detect and encrypt plaintext rows on startup.
- Key rotation: Graceful degradation — `InvalidToken` on decrypt returns None, treated as expired session (user re-authenticates). 8-hour session TTL makes this acceptable.

---

## R2: Request-ID Correlation Middleware (FR-024)

**Decision**: Add a Starlette `BaseHTTPMiddleware` that propagates or generates `X-Request-ID` per request, stored in a `ContextVar` for logging integration.

**Rationale**: Middleware fires on every request (including unmapped routes, errors). A FastAPI `Depends()` only runs when an endpoint function is called — would miss middleware-chain failures and WebSocket upgrades. `ContextVar` makes the ID available to all logging within the request scope without function argument threading.

**Alternatives considered**:
- FastAPI dependency: Doesn't cover non-endpoint requests (static files, middleware errors).
- Custom ASGI middleware (raw): More boilerplate for the same result; `BaseHTTPMiddleware` is simpler.

**Implementation approach**:
- New file: `backend/src/middleware/request_id.py` with `RequestIDMiddleware` and `request_id_ctx: ContextVar[str]`.
- Reads `X-Request-ID` from incoming request headers; generates `uuid4().hex` if absent.
- Sets response header `X-Request-ID` on every response.
- Optional: add `RequestIDFilter` to logging setup for inclusion in log format.
- Register after `CORSMiddleware` in `main.py` (Starlette LIFO order — last added runs outermost).

---

## R3: WebSocket + Polling Coordination (FR-017, FR-018)

**Decision**: Fix `useRealTimeSync.ts` to (a) call `stopPolling()` on `ws.onopen`, (b) use exponential backoff with jitter for reconnection, and (c) prefer TanStack Query's `refetchInterval` over manual `setInterval`.

**Rationale**: The current bug is that `startPolling()` is called on mount and never stopped when WebSocket connects. Both push and poll fire simultaneously, causing duplicate query invalidations and potential UI flicker.

**Alternatives considered**:
- Replace with a library like `socket.io-client` reconnection: Already uses `socket.io-client` for other hooks but `useRealTimeSync` uses native WebSocket — converting would be a larger change than scoped for bug bash.
- Remove polling entirely: Too risky — WebSocket can fail behind proxies. Polling as fallback is correct.

**Implementation approach**:
- `ws.onopen`: add `stopPolling()`, reset reconnect attempts.
- `ws.onclose`: add `startPolling()`, apply `delay = min(1000 * 2^attempt, 30000) + random(0, 1000)`.
- Replace `window.setInterval` with TanStack Query `refetchInterval` toggled by connection status (disabled when WS connected).

---

## R4: GraphQL Comment Pagination (FR-021)

**Decision**: Add cursor-based pagination to `GET_ISSUE_WITH_COMMENTS_QUERY`, fetching all pages eagerly in a `while hasNextPage` loop with a safety cap of 10 pages (1000 comments).

**Rationale**: The current query fetches `comments(first: 100)` with no pagination. Issues with >100 comments silently lose data, which breaks pipeline reconstruction that scans comments for "Done!" markers. Eager fetching is necessary because the marker can be on any comment.

**Alternatives considered**:
- Lazy pagination (stop when marker found): Risky — marker could be modified/missing and we'd need full scan for reconstruction anyway.
- Increase limit to 1000: GitHub GraphQL API caps `first` at 100.

**Implementation approach**:
- Update `GET_ISSUE_WITH_COMMENTS_QUERY` in `graphql.py` to accept `$after: String` parameter.
- Update `get_issue_with_comments` in `service.py` to loop with cursor until `hasNextPage` is false.
- Add `max_pages=10` safety guard to prevent unbounded loops.
- All existing callers get paginated results automatically.

---

## R5: Webhook Signature Verification (FR-004)

**Decision**: Enforce the existing `verify_webhook_signature()` function as mandatory. The current code structure is correct (reads body bytes, computes HMAC-SHA256, uses `compare_digest`). The fix is to make verification non-skippable in production.

**Rationale**: The function exists but may be bypassed when `github_webhook_secret` is unset. In production, webhook processing without verification allows payload spoofing.

**Alternatives considered**:
- Move to middleware: Overkill — only one endpoint receives webhooks.
- FastAPI dependency: Would consume request body, preventing the handler from reading it again (Starlette single-read stream). The current inline pattern avoids this.

**Implementation approach**:
- In the webhook handler: if `settings.github_webhook_secret` is not set AND `settings.debug` is False, reject the request with 401.
- If secret is set, verify signature as already implemented.
- In debug mode with no secret, log a warning and allow (for local development).

---

## R6: Health Check Enhancement (FR-020)

**Decision**: Replace the static `{"status": "ok"}` with a structured response checking database, GitHub API, and polling loop in parallel using `asyncio.gather`. Use IETF Health Check Response Format (draft-inadarei-api-health-check) structure.

**Rationale**: A health endpoint that always returns "ok" masks real failures. Docker Compose already uses this endpoint for container health checks — returning 503 on failure enables proper orchestration.

**Alternatives considered**:
- Separate `/health/ready` and `/health/live` endpoints: Overkill for Docker Compose — a single endpoint with `200/503` is sufficient.
- External health check tool: Adds operational complexity for no benefit.

**Implementation approach**:
- Database check: `SELECT 1` via existing aiosqlite connection, 2s timeout.
- GitHub API check: `GET https://api.github.com/rate_limit` (unauthenticated, lightweight), 3s timeout.
- Polling loop check: inspect `asyncio.Task.done()` on the polling task stored in `app.state`.
- Run all three with `asyncio.gather(return_exceptions=True)`.
- Response: `{"status": "pass|warn|fail", "checks": {...}}`, HTTP 200 for pass/warn, 503 for fail.
- Update Docker Compose healthcheck command to expect the new response format.

---

## R7: Session-Owner Admin Authorization (FR-005)

**Decision**: Store `admin_github_user_id` in the `global_settings` table. First authenticated user auto-promotes to admin. Create a `require_admin` FastAPI dependency that compares current session user ID against stored admin ID.

**Rationale**: Simplest pattern for single-tenant deployment. No external role lookup, no config file, no separate setup step. The dependency composes naturally with the existing `get_session_dep`.

**Alternatives considered**:
- Environment variable with admin username: Requires config change to change admin — less flexible.
- GitHub org role check: Adds API call per request — unnecessary for single-tenant.
- Allow-list in config: Adds complexity for multi-admin support we don't need.

**Implementation approach**:
- Migration `003_add_admin_column.sql`: `ALTER TABLE global_settings ADD COLUMN admin_github_user_id INTEGER DEFAULT NULL`.
- New dependency `require_admin` in `dependencies.py`: reads admin ID from DB, compares with session user, auto-promotes on first use if NULL.
- Gate `PUT`/`DELETE` settings endpoints with `Depends(require_admin)`. `GET` remains open to all authenticated users.

---

## R8: DRY Consolidation Patterns (FR-011 through FR-014)

**Decision**: Use existing `resolve_repository()` in `utils.py` as the canonical repo resolver. Extract remaining shared utilities into `utils.py` (cache pruning) and as methods on `GitHubProjectsService` (header builder, PR filtering).

**Rationale**: `utils.py` already contains `resolve_repository()` — the intended shared implementation — but 4+ call sites in `workflow.py` bypass it with inline logic. Consolidation is straightforward.

**Implementation approach**:

| Pattern | Current State | Target |
|---------|--------------|--------|
| Repo resolution | `resolve_repository()` in `utils.py` exists but bypassed 5+ times in `workflow.py`, `projects.py` | Replace all inline 3-step resolution with `await resolve_repository()` calls |
| REST headers | Inline `{"Authorization": f"Bearer {token}", ...}` dict constructed 10+ times in `service.py` | Extract `_build_rest_headers(token)` method on `GitHubProjectsService` |
| Cache pruning | 3 variants with different thresholds (200, 200, 100) across `pipeline.py`, `recovery.py`, `agent_output.py` | Extract `prune_bounded_set(s: set, max_size: int)` and `prune_bounded_dict(d: dict, max_size: int)` in `utils.py` |
| PR filtering | Copilot-author check repeated 3x in `service.py` `find_existing_pr_for_issue()` | Extract `_is_copilot_authored(pr: dict) -> bool` helper method |

---

## R9: False-Positive Completion Fix (FR-007)

**Decision**: In Signal 3 of `_check_main_pr_completion()`, require that the branch's HEAD SHA has **advanced** from the initially-recorded `agent_assigned_sha` before marking completion. Agent unassignment alone is insufficient.

**Rationale**: Currently, if Copilot is unassigned but the SHA hasn't changed (agent failed without pushing code), Signal 3 still returns `True`. This silently advances the pipeline with no work done.

**Implementation approach**:
- In `completion.py`, Signal 3: change the condition from `copilot_unassigned → True` to `copilot_unassigned AND sha_changed → True`.
- If `copilot_unassigned AND NOT sha_changed`: log a warning, return `False`, optionally mark the stage as "stalled" for recovery.
- This is a one-line conditional change with significant correctness impact.

---

## R10: Circular Dependency Resolution (FR-016)

**Decision**: Replace runtime `try/except ImportError` blocks in `orchestrator.py` with lazy imports inside the singleton factory function. The existing `get_workflow_orchestrator()` pattern (lazy import inside factory) is acceptable; the scattered `try/except` blocks elsewhere are not.

**Rationale**: The `get_workflow_orchestrator()` factory already uses lazy imports correctly — this is a standard Python pattern for circular dependencies. The problem is the 3+ `try/except ImportError` blocks in methods like `assign_agent_for_status()` that silently swallow real import errors.

**Implementation approach**:
- Move the copilot_polling imports from scattered `try/except` blocks to the top of the methods that need them, using the `TYPE_CHECKING` guard for type hints.
- For runtime access: pass copilot_polling functions as parameters to the orchestrator constructor or resolve them in the factory function.
- Alternative: extract the shared state/constants into a separate module that both packages can import without circularity.
