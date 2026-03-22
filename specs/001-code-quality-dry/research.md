# Research: Phase 2 — Code Quality & DRY Consolidation

**Feature**: 001-code-quality-dry  
**Date**: 2026-03-22  
**Status**: Complete

## Research Task 1: Exception Middleware Behaviour — HTTPException vs AppException

**Context**: 7 error sites in `tools.py` raise `HTTPException` directly. Need to determine whether converting to `AppException` subclasses aligns with existing middleware.

### Findings

- **`main.py:486-498`** registers an `AppException` handler that returns `JSONResponse` with `status_code`, `error`, and `details` fields, plus a `Retry-After` header for `RateLimitError`.
- **`main.py:500-515`** registers a generic `Exception` handler that returns HTTP 500 with `"Internal server error"`.
- FastAPI has a **built-in `HTTPException` handler** that returns `JSONResponse` with `detail` field and the given status code. This handler is separate from the `AppException` handler.
- **Key difference**: `HTTPException` produces `{"detail": "..."}` while `AppException` produces `{"error": "...", "details": {...}}`. These are different response shapes.

### Decision

**Do NOT convert `HTTPException` sites to `AppException` subclasses in tools.py** where doing so would change the response contract. Instead:
- Sites that currently raise `HTTPException` and are consumed by the MCP tools framework (which expects `detail` format) → keep as `HTTPException`.
- Sites that catch a general `Exception` and re-raise as `HTTPException(500, ...)` → can migrate to `handle_service_error()` if the error class and status code have an `AppException` equivalent (e.g., `GitHubAPIError` for 502, `ValidationError` for 422).
- Each of the 7 sites must be evaluated individually based on the caller contract.

### Rationale

Converting blindly would change client response shapes from `{"detail": "..."}` to `{"error": "...", "details": {...}}`, which is a breaking change for MCP tool consumers. The decision must be site-specific.

### Alternatives Considered

1. **Convert all to AppException** — Rejected: breaking change to response contract.
2. **Add an HTTPException-to-AppException adapter** — Rejected: adds complexity without clear benefit; the existing middleware separation is intentional.
3. **Leave all as-is** — Rejected for sites where `handle_service_error()` can be used because the raised type already has an `AppException` equivalent (e.g., `ValueError` → `ValidationError`).

---

## Research Task 2: cached_fetch() Extension Strategy — Backward Compatibility

**Context**: `cached_fetch()` in `cache.py:187-234` needs `rate_limit_fallback` and `data_hash_fn` optional parameters while remaining fully backward-compatible.

### Findings

- Current signature: `cached_fetch[T](cache_instance, key, fetch_fn, ttl_seconds=None, refresh=False, stale_fallback=False)`.
- All existing callers pass positional args for `cache_instance`, `key`, `fetch_fn` and keyword args for optional parameters.
- `InMemoryCache.set()` already accepts a `data_hash` parameter (verified in `cache.py`).
- `InMemoryCache.get_entry()` returns full `CacheEntry` with `data_hash` metadata.
- `compute_data_hash()` exists in `cache.py` and produces deterministic SHA-256 hashes.
- A separate `cached_fetch()` exists in `utils.py:270-302` with a simpler signature — this is a different function used for project-scoped caching in the `utils` module.

### Decision

Add two optional keyword-only parameters to `cached_fetch()` in `cache.py`:
1. `rate_limit_fallback: bool = False` — when `True` and a `RateLimitError` is raised during fetch, return stale data (same as `stale_fallback`) but also log a rate-limit-specific warning.
2. `data_hash_fn: Callable[[T], str] | None = None` — when provided, compute a hash of the fetched data and compare against the cached entry's hash. If identical, refresh TTL only (no re-store). If different, store with the new hash.

### Rationale

- Keyword-only parameters guarantee backward compatibility (no positional arg shift).
- The `rate_limit_fallback` parameter covers the pattern in `board.py` where `RateLimitError` is caught separately from generic exceptions.
- The `data_hash_fn` parameter covers the hash-diffing pattern in `send_tasks()` (`projects.py:365-429`).

### Alternatives Considered

1. **Subclass cached_fetch** — Rejected: adds unnecessary indirection.
2. **Callback hooks (on_error, on_success)** — Rejected: over-generalizes; YAGNI principle.
3. **Decorator pattern** — Rejected: makes the control flow harder to follow.

---

## Research Task 3: Dual-Cache-Key Strategy for list_board_projects()

**Context**: `list_board_projects()` in `board.py:212-305` uses two cache keys: one for board-specific projects and one for the general user-projects cache. The spec requires handling this via a composed `fetch_fn` rather than adding a `fallback_keys` parameter.

### Findings

- **Primary key**: `CACHE_PREFIX_BOARD_PROJECTS:{user_id}` — board-formatted project list.
- **Secondary key**: `user_projects:{user_id}` — raw project list (shared with `list_projects()`).
- Current flow: check primary cache → check secondary cache (transform via `_to_board_projects()`) → fetch fresh → cache both.
- The secondary cache acts as a warm-data fallback, not a separate fetch.

### Decision

Compose a `fetch_fn` that:
1. First checks the secondary cache (`user_projects` key) and transforms if present.
2. If no secondary cache hit, calls the GitHub API to fetch projects.
3. Caches the raw result under the secondary key as a side effect.
4. Returns the board-formatted result for `cached_fetch()` to cache under the primary key.

This keeps `cached_fetch()` single-key and moves the dual-key orchestration into the caller's `fetch_fn`.

### Rationale

Adding a `fallback_keys` parameter to `cached_fetch()` would violate the Simplicity principle and complicate the utility's contract for a single use case. The composed function approach keeps the utility generic.

### Alternatives Considered

1. **Add `fallback_keys` to `cached_fetch()`** — Rejected per spec requirement; violates YAGNI.
2. **Two separate `cached_fetch()` calls** — Rejected: creates race conditions between the two caches.
3. **Pre-populate primary cache from secondary cache before calling `cached_fetch()`** — Rejected: leaks cache management logic outside the utility.

---

## Research Task 4: _with_fallback() Soft-Failure Contract

**Context**: The `_with_fallback()` abstraction must return `None` on total failure and never raise exceptions.

### Findings

- `add_issue_to_project()` in `issues.py:167-240` implements: GraphQL attempt → verify → REST fallback → return best-available result.
- The function currently returns `item_id` (possibly empty string) even if verification and fallback both fail — it does NOT return `None`.
- `find_existing_pr_for_issue()` in `pull_requests.py:109-160` returns `dict | None`.
- `assign_copilot_to_issue()` in `copilot.py:258-373` returns `bool` (True/False, not None).

### Decision

`_with_fallback()` signature:
```python
async def _with_fallback(
    self,
    primary_fn: Callable[[], Awaitable[T]],
    fallback_fn: Callable[[], Awaitable[T]],
    operation: str,
    verify_fn: Callable[[], Awaitable[bool]] | None = None,
) -> T | None:
```

Contract:
- Calls `primary_fn()`. If it succeeds, optionally calls `verify_fn()`. If verify passes (or no verify_fn), returns result.
- If primary fails or verify fails, calls `fallback_fn()`. If it succeeds, returns result.
- If both fail, returns `None`. Never raises.
- All exceptions in primary, verify, and fallback are caught and logged.

### Rationale

The soft-failure contract matches the existing pattern in `add_issue_to_project()` where a failure to add an issue should not crash the caller — the caller handles `None` or empty-string results gracefully. The generic type parameter `T` allows reuse across different return types.

### Alternatives Considered

1. **Return a Result/Either monad** — Rejected: over-engineering for the current use cases; YAGNI.
2. **Accept a default value parameter** — Rejected: `None` is the universal "no result" signal in this codebase.
3. **Raise on total failure with an opt-in flag** — Rejected per spec: violates soft-failure contract.

---

## Research Task 5: REST Repository Lookup Pattern

**Context**: Need to add a REST-based repository lookup to `resolve_repository()` between the GraphQL project-items step and the workflow-config step.

### Findings

- The REST pattern in `issues.py:282-350` (`_add_issue_to_project_rest()`) uses `_get_project_rest_info()` to get project number, owner type, and owner login via REST, then constructs REST API paths.
- `_get_project_rest_info()` internally calls `_rest()` to fetch project details.
- For repository resolution, the equivalent REST endpoint is `GET /repos/{owner}/{repo}` or project-level queries.
- The GitHub REST API for Projects V2 is at `/orgs/{login}/projects` or `/users/{login}/projects`.
- **Key insight**: `resolve_repository()` goes from project_id → (owner, repo). The REST API can query project items to find linked repositories.
- The existing `get_project_repository()` uses GraphQL `projectV2` query to get items and extract repository info from issue URLs.

### Decision

Add a REST-based step that:
1. Uses `_get_project_rest_info()` to get the project's owner login.
2. Queries the project items via REST: `GET /orgs/{login}/projectsV2/{number}/items` or `/users/{login}/projectsV2/{number}/items`.
3. Extracts repository owner/name from the first issue item's `content_url` field.
4. Returns `(owner, repo)` if successful, `None` if not.

This mirrors the GraphQL approach but uses REST endpoints, providing resilience against GraphQL-specific failures (rate limits, schema changes).

### Rationale

The REST fallback provides an independent code path that can succeed when GraphQL is rate-limited or unavailable. The pattern is consistent with the GraphQL→REST fallback used throughout the service layer.

### Alternatives Considered

1. **Use GitHub Search API** — Rejected: search has separate rate limits and may not return project-associated repos.
2. **Cache project metadata in the database** — Rejected: adds persistence complexity for a transient lookup.
3. **Skip REST fallback entirely** — Rejected per spec requirement FR-017.

---

## Research Task 6: send_tasks() Migration Evaluation

**Context**: Evaluate whether `send_tasks()` in `projects.py:365-429` can be migrated to `cached_fetch()` with the extended signature.

### Findings

The `send_tasks()` function has these distinctive patterns:
1. **Stale revalidation counter**: A module-level counter tracks how many times stale data has been served. After `STALE_REVALIDATION_LIMIT` stale serves, the next request forces a fresh fetch. This is a **stateful, cross-request** pattern.
2. **Data hash-diffing**: After fetching, computes a hash of the response. If the hash matches the cached entry, only refreshes the TTL (avoids WebSocket push of unchanged data).
3. **Counter reset on fresh fetch**: The stale revalidation counter resets to 0 after a successful fresh fetch.

Assessment against `cached_fetch()` extended signature:
- ✅ `data_hash_fn` parameter covers the hash-diffing pattern.
- ❌ **Stale revalidation counter** is stateful across calls and requires external state management. `cached_fetch()` is stateless by design.
- ❌ The counter controls **when** to bypass cache, not **what** to return — it's a fetch-scheduling concern, not a cache-aside concern.

### Decision

**Do NOT migrate `send_tasks()` to `cached_fetch()`.** The stale-revalidation counter pattern is fundamentally different from cache-aside with stale fallback. The counter introduces call-frequency-dependent state that `cached_fetch()` should not own.

Add a justification comment in `send_tasks()` documenting why it was evaluated and not migrated.

### Rationale

Forcing the counter pattern into `cached_fetch()` would require adding `revalidation_counter` and `revalidation_limit` parameters, which violates YAGNI — only one caller would use them. The `data_hash_fn` extension is the general-purpose part; the counter is specific to WebSocket polling.

### Alternatives Considered

1. **Add counter parameters to `cached_fetch()`** — Rejected: single-caller feature, violates YAGNI.
2. **Wrap `cached_fetch()` with counter logic in `send_tasks()`** — Rejected: still requires `send_tasks()` to manage its own cache check before calling `cached_fetch()`, eliminating the DRY benefit.
3. **Extract counter into a `PollingCacheStrategy` class** — Rejected: premature abstraction for one use case.

---

## Research Task 7: _with_fallback() Applicability — copilot.py and pull_requests.py

**Context**: Evaluate whether `_with_fallback()` simplifies `assign_copilot_to_issue()` and `find_existing_pr_for_issue()`.

### Findings

**`assign_copilot_to_issue()` (copilot.py:258-373)**:
- Has a pre-step (unassign if custom agent) before the primary/fallback flow.
- Primary: `_assign_copilot_graphql()` → returns `bool`.
- Fallback: `_assign_copilot_rest()` → returns `bool`.
- No verify step between primary and fallback.
- Returns `bool`, not `T | None`. Would need adaptation or the caller to handle `None` as `False`.
- The pre-step (conditional unassign) makes this not a clean fit — `_with_fallback()` doesn't model "do X before trying primary".

**`find_existing_pr_for_issue()` (pull_requests.py:109-160)**:
- Primary: `get_linked_pull_requests()` via GraphQL → returns list.
- Fallback: `_search_open_prs_for_issue_rest()` via REST → returns list.
- Post-processing: filters by Copilot author, picks first match.
- Returns `dict | None` — compatible with `_with_fallback()` return type.
- However, the post-processing (filter by author) is different for primary vs fallback results, making a unified `_with_fallback()` awkward.

### Decision

- **`assign_copilot_to_issue()`**: Do NOT apply `_with_fallback()`. The pre-step logic and `bool` return type make it a poor fit. Document rationale.
- **`find_existing_pr_for_issue()`**: Do NOT apply `_with_fallback()`. The divergent post-processing between primary and fallback paths means the function bodies can't be trivially extracted into `primary_fn` / `fallback_fn` lambdas without losing clarity. Document rationale.

### Rationale

Both functions have control flow that doesn't map cleanly to the `primary → verify → fallback` pattern. Forcing them into `_with_fallback()` would require either:
- Wrapping pre/post-processing into the lambdas (hiding important logic).
- Adding parameters to `_with_fallback()` for pre-steps or post-processing (violating Simplicity).

The current inline implementations are already clear and concise. Applying `_with_fallback()` would increase indirection without reducing code or improving clarity.

### Alternatives Considered

1. **Apply to both** — Rejected: adds indirection without simplification.
2. **Apply to `find_existing_pr_for_issue()` only** — Rejected: post-processing divergence makes it awkward.
3. **Create a `_with_fallback_bool()` variant** — Rejected: YAGNI; single caller.
