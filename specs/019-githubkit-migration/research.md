# Research: Simplify GitHub Service with githubkit v0.14.6

**Feature**: `019-githubkit-migration`
**Date**: 2026-03-06
**Status**: Complete

---

## R-001: githubkit SDK Capabilities and Version Pinning

**Question**: Does githubkit v0.14.x provide stable, well-documented methods for all standard GitHub REST and GraphQL operations referenced in the specification?

**Decision**: Pin to `githubkit>=0.14.0,<0.15.0`

**Rationale**: githubkit v0.14.6 (current latest in the 0.14.x series) provides:
- **Async-native client** via `GitHub(auth=TokenAuthStrategy(token))` — matches the project's existing async/await architecture (FastAPI + httpx).
- **Typed REST methods** for all standard endpoints used in service.py: `rest.issues.create`, `rest.issues.update`, `rest.pulls.request_reviewers`, `rest.git.delete_ref`, `rest.issues.create_comment`, `rest.pulls.list_files` with built-in pagination.
- **GraphQL execution** via `github.graphql(query, variables=...)` accepting raw query strings — all 31 existing query/mutation constants in graphql.py are compatible without modification.
- **Built-in retry** with configurable exponential backoff for rate limit (429) and server error (5xx) responses.
- **HTTP caching** via Hishel integration (`http_cache=True`) supporting ETag/If-None-Match conditional requests.
- **Request throttling** via `LocalThrottler` — replaces the hand-rolled inter-call throttle (`_min_request_interval`).
- **OAuth strategies** via `OAuthWebAuthStrategy` and `OAuthTokenAuthStrategy`.
- Pinning `<0.15.0` prevents unexpected breaking changes during migration stabilization.

**Alternatives Considered**:
- **PyGithub v2.8.1**: Rejected — sync-only (no native async), no GraphQL support, no built-in retry/cache/throttle, LGPL-3.0 license vs MIT, uses `requests` instead of `httpx`.
- **ghapi**: Rejected — thin wrapper without retry/cache/throttle, incomplete typing.
- **Raw httpx (status quo)**: Rejected — the 5,179-line service.py contains ~1,500–2,000 LOC of infrastructure code that githubkit replaces.

---

## R-002: Client Pooling Strategy

**Question**: Should we create a new `GitHub` client per API call (matching current per-call token pattern) or pool clients per user token?

**Decision**: Implement a `BoundedDict[token_hash, GitHub]` client pool capped at 50 entries with LRU eviction.

**Rationale**: The current implementation creates a single shared `httpx.AsyncClient` in `GitHubProjectsService.__init__()` and passes `access_token` per call via headers. With githubkit, each `GitHub(TokenAuthStrategy(token))` instance owns its own httpx connection pool. Creating a new client per API call would:
- Waste TCP connections (no connection reuse across calls for the same user).
- Incur TLS handshake overhead per call.
- Make HTTP caching (ETag) ineffective since each client has its own cache.

The project's `utils.BoundedDict` (already used for OAuth state and in-flight GraphQL dedup) provides exactly the right data structure — an `OrderedDict`-backed dict with FIFO eviction at max capacity. 50 entries is sufficient for expected concurrent user load and limits memory to ~50 httpx connection pools.

**Alternatives Considered**:
- **Per-call client creation**: Rejected — no connection reuse, no ETag cache persistence across calls.
- **Unbounded dict**: Rejected — memory leak risk with many unique tokens over time.
- **LRU cache decorator**: Rejected — doesn't provide explicit capacity control and isn't async-safe for cleanup.

---

## R-003: Rate Limit Visibility After Migration

**Question**: How does `copilot_polling.py` access rate limit state when githubkit manages rate limits internally?

**Decision**: Implement a `RateLimitState` dataclass adapter that captures rate limit headers from httpx response events.

**Rationale**: The polling loop (`copilot_polling/polling_loop.py`) calls `get_last_rate_limit()` at lines 30, 456 and `clear_last_rate_limit()` at lines 70, 374 to:
1. Check remaining API quota before operations.
2. Clear stale caches when quota is exhausted.

githubkit's internal throttler handles rate limits transparently but does not expose `X-RateLimit-Remaining` / `X-RateLimit-Reset` values to callers. Two approaches:
- **Option A (chosen)**: Hook into httpx response events via a custom transport or event hook to capture rate limit headers after each response, storing them in a `RateLimitState` dataclass on the `GitHubClientFactory`. This is non-invasive and doesn't require patching githubkit internals.
- **Option B**: Use `github.request()` return values which include the full `httpx.Response` and extract headers manually. This works but requires changing every call site.

The adapter exposes `get_rate_limit() -> RateLimitState | None` and `clear_rate_limit()` methods, preserving the existing interface contract with `copilot_polling.py`.

**Alternatives Considered**:
- **Monkey-patching githubkit's throttler**: Rejected — fragile, version-coupled.
- **Dropping rate limit visibility**: Rejected — polling loop needs this for intelligent throttling decisions.
- **Per-response header extraction at call sites**: Rejected — too invasive, duplicates logic across 20+ call sites.

---

## R-004: OAuth Migration Path

**Question**: Can githubkit's OAuth strategies replace the hand-rolled OAuth in `github_auth.py` while preserving SQLite session management?

**Decision**: Partially replace — use githubkit for token exchange and user info retrieval, keep SQLite session management unchanged.

**Rationale**: Examining `github_auth.py` (313 LOC), the OAuth code breaks down as:
- **Token exchange** (~30 LOC): `exchange_code_for_token()` — direct POST to GitHub's OAuth endpoint. githubkit's `OAuthWebAuthStrategy` can replace this.
- **User info retrieval** (~20 LOC): `get_github_user()` — GET to `/user`. Replaceable with `github.rest.users.get_authenticated()`.
- **Token refresh** (~40 LOC): `refresh_token()` — POST to GitHub's token endpoint. Replaceable with githubkit's token refresh.
- **Session management** (~180 LOC): `create_session()`, `get_session()`, `update_session()`, `revoke_session()`, OAuth state storage — all SQLite/application logic that must be preserved.
- **Session from PAT** (~25 LOC): `create_session_from_token()` — development helper, trivially migrated.

The 313 LOC github_auth.py won't shrink to 100 LOC because session management (180 LOC) is application logic, not infrastructure. Realistic reduction: ~90 LOC of httpx-specific code replaced by ~40 LOC of githubkit calls, yielding ~270 LOC total. The spec's "~100 LOC" target was aspirational; ~270 LOC is the achievable target while preserving all session management.

**Alternatives Considered**:
- **Full OAuth replacement with githubkit AppAuthStrategy**: Rejected — githubkit's OAuth flows are designed for GitHub Apps, not the web authorization code grant used here.
- **Keep httpx for auth only**: Rejected — defeats the purpose of removing direct httpx dependency.

---

## R-005: Preview API Compatibility

**Question**: Do Sub-Issues (`/issues/{n}/sub_issues`) and Copilot assignment preview APIs have typed githubkit methods?

**Decision**: Use `github.request("POST", url, json=body)` for preview APIs.

**Rationale**: Sub-Issues and Copilot assignment are preview/experimental GitHub APIs. githubkit's typed methods cover stable GitHub REST API endpoints. For preview APIs:
- `github.request("POST", "/repos/{owner}/{repo}/issues/{n}/sub_issues", json=body)` provides retry, throttling, and authentication automatically.
- `github.request("GET", ...)` works for read endpoints.
- The `headers` parameter allows setting required preview API headers (e.g., `Accept: application/vnd.github.raw+json`).

This is the recommended pattern in githubkit's documentation for endpoints not yet in the typed API.

**Alternatives Considered**:
- **Waiting for typed methods**: Rejected — timeline uncertain, blocks migration.
- **Keeping raw httpx for preview APIs**: Rejected — loses retry/throttle benefits.

---

## R-006: GraphQL Query String Compatibility

**Question**: Can the 31 existing GraphQL query/mutation strings in graphql.py be used directly with githubkit's `github.graphql()` method?

**Decision**: Yes — all existing query strings are compatible without modification.

**Rationale**: githubkit's `github.graphql(query, variables=...)` accepts raw GraphQL query strings and a dict of variables. The existing query constants in graphql.py (e.g., `LIST_USER_PROJECTS_QUERY`, `CREATE_ISSUE_MUTATION`, etc.) are standard GraphQL strings. The only change needed:
- Remove `GITHUB_GRAPHQL_URL` constant (githubkit handles the endpoint).
- Remove `MAX_RETRIES`, `INITIAL_BACKOFF_SECONDS`, `MAX_BACKOFF_SECONDS` (githubkit handles retry).
- Keep all 31 query/mutation string constants unchanged.

**Alternatives Considered**:
- **Rewriting queries as githubkit query builders**: Rejected — no benefit, adds complexity, existing strings work as-is.

---

## R-007: Test Mock Migration Strategy

**Question**: How should test mocks transition from raw httpx to githubkit?

**Decision**: Use `pytest-httpx` or githubkit's built-in mock support to intercept HTTP calls at the transport level.

**Rationale**: The existing test suite mocks `httpx.AsyncClient` methods directly. With githubkit:
- githubkit uses httpx internally, so `pytest-httpx` (if already in use) continues to work at the transport layer.
- Alternatively, mock the `GitHub` instance's methods directly (e.g., `github.rest.issues.create`, `github.graphql`).
- The `GitHubClientFactory` can be injected with a mock factory in tests that returns pre-configured mock clients.

The most pragmatic approach: mock at the `GitHubProjectsService` method level (which is how most tests already work based on the test structure), and update only tests that directly mock httpx internals.

**Alternatives Considered**:
- **VCR/cassette-based recording**: Rejected — requires network access during recording, brittle.
- **Full integration test rewrite**: Rejected — excessive scope, existing mocks mostly work at service level.

---

## R-008: Concurrency Safety of Client Pool

**Question**: Is `BoundedDict` safe for concurrent async access from multiple FastAPI request handlers?

**Decision**: Safe for single-threaded async (asyncio), which is the project's execution model.

**Rationale**: `BoundedDict` is backed by `OrderedDict` with `__setitem__` doing capacity check + eviction. In asyncio's cooperative multitasking model, dict operations are atomic (no `await` between read-check-write). The `GitHubClientFactory.get_client(token)` method:
1. Hashes token (CPU-bound, no await).
2. Checks dict (no await).
3. Creates client if missing (no await — `GitHub()` constructor is sync).
4. Stores in dict (no await).

No `await` points exist between the check and store, so no race conditions are possible in single-threaded asyncio. If the project ever moves to multi-threaded execution, an `asyncio.Lock` would be needed.

**Alternatives Considered**:
- **Adding asyncio.Lock preemptively**: Rejected — unnecessary overhead for current execution model, violates YAGNI.
- **Using thread-safe collections**: Rejected — asyncio is single-threaded.

---

## R-009: httpx Dependency After Migration

**Question**: Can httpx be fully removed from `pyproject.toml` after migration?

**Decision**: Remove httpx as a direct dependency. It remains as a transitive dependency of githubkit.

**Rationale**: httpx is used directly in 7 files currently:
- `service.py` — primary target, fully replaced by githubkit.
- `github_auth.py` — replaced by githubkit OAuth strategies.
- `metadata_service.py` — uses httpx for GitHub API calls, can migrate to githubkit's client.
- `signal_bridge.py`, `signal_delivery.py` — uses httpx for Signal messaging (non-GitHub). These remain as httpx users.
- `api/board.py` — error handling for `httpx.HTTPStatusError`.
- `api/health.py` — health check endpoint.

**Important**: Signal messaging services (`signal_bridge.py`, `signal_delivery.py`) use httpx for non-GitHub HTTP calls. These cannot be replaced by githubkit. Therefore, httpx must remain as a direct dependency OR these services must use a different HTTP client.

Given that githubkit depends on httpx (it's a transitive dependency), signal services can continue importing httpx even if it's removed from the direct dependencies list. However, for clarity and explicit dependency management, it's better to keep httpx in `pyproject.toml` until signal services are also refactored. The spec requirement of "zero httpx imports outside test mocks" applies specifically to GitHub API integration code, not to unrelated services.

**Alternatives Considered**:
- **Removing httpx entirely**: Not possible — signal services need it.
- **Replacing signal services with aiohttp**: Out of scope for this migration.

---

## R-010: _with_fallback() Helper Consolidation

**Question**: Which GraphQL→REST fallback chains exist and how should they be consolidated?

**Decision**: Audit all fallback patterns and ensure they all use `_with_fallback()`.

**Rationale**: The existing `_with_fallback()` helper (lines 227–260 of service.py) provides a clean try/except pattern with logging. Current fallback chains in service.py:
- `add_issue_to_project()` — GraphQL → REST fallback (already uses `_with_fallback`-like pattern at line 1646).
- `assign_copilot_to_issue()` — REST → GraphQL fallback (line 2399).
- `find_existing_pr_for_issue()` — GraphQL → REST search fallback (line 3183).

These should all be consolidated to use `_with_fallback()` for consistency. The helper already handles logging, error context, and result tagging.

**Alternatives Considered**:
- **Separate fallback helpers per domain**: Rejected — duplicates logic, harder to maintain.
- **Removing fallback patterns**: Rejected — they provide critical resilience for flaky API endpoints.
