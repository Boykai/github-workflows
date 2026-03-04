# Research: Audit & Refactor FastAPI+React GitHub Projects Copilot Codebase

**Feature**: 018-audit-refactor-codebase
**Date**: 2026-03-04

## Phase 1 — Dependency Version Research

### R-001: Backend Dependency Versions

| Package | Current Spec | Latest Stable | Action |
|---------|-------------|---------------|--------|
| `fastapi` | `>=0.109.0` | 0.135.1 (2026-03-01) | Bump to `>=0.135.0` |
| `uvicorn[standard]` | `>=0.27.0` | 0.41.0 (2026-02-16) | Bump to `>=0.41.0` |
| `httpx` | `>=0.26.0` | 0.28.1 (2024-12-06) | Bump to `>=0.28.0` |
| `python-jose[cryptography]` | `>=3.3.0` | 3.3.0 (stable) | No change needed |
| `pydantic` | `>=2.5.0` | 2.12.5 (2025-11-26) | Bump to `>=2.12.0` |
| `pydantic-settings` | `>=2.1.0` | Tracks pydantic | Bump to `>=2.7.0` |
| `python-multipart` | `>=0.0.6` | 0.0.20 (latest) | Bump to `>=0.0.20` |
| `pyyaml` | `>=6.0.1` | 6.0.2 (latest) | Bump to `>=6.0.2` |
| `github-copilot-sdk` | `>=0.1.0` | 0.1.29 (2026-02-27) | Bump to `>=0.1.29` |
| `agent-framework-core` | `>=1.0.0a1` | N/A | **REMOVE** (unused) |
| `openai` | `>=1.0.0` | 2.24.0 (2026-02-24) | Bump to `>=2.24.0` |
| `azure-ai-inference` | `>=1.0.0b1` | 1.0.0b9 (latest beta) | Bump to `>=1.0.0b9` |
| `aiosqlite` | `>=0.20.0` | 0.22.1 (2025-12-23) | Bump to `>=0.22.0` |
| `tenacity` | `>=8.2.0` | 9.1.4 (2026-02-07) | Bump to `>=9.1.0` |
| `websockets` | `>=12.0` | 14.2 (latest) | Bump to `>=14.0` |

**Decision**: Bump all to latest stable. Remove `agent-framework-core`.
**Rationale**: All packages maintain backward compatibility within major versions. The Copilot SDK is in preview but actively maintained; bumping to 0.1.29 ensures latest fixes.
**Alternatives considered**: Pinning exact versions rejected — existing `>=` convention preserved for flexibility.

### R-002: Copilot SDK Symbol Verification

**Symbols currently used** (verified by code search):
- `CopilotClient` — `completion_providers.py:83`, `model_fetcher.py:87`
- `CopilotClientOptions` — `completion_providers.py:84`, `model_fetcher.py:88`
- `SessionConfig` — `completion_providers.py:117`
- `MessageOptions` — `completion_providers.py:116`
- `PermissionHandler` — `completion_providers.py:111`
- `SessionEventType` — `completion_providers.py:113` (from `copilot.generated.session_events`)
- `CopilotClient.list_models()` — `model_fetcher.py` (used for model listing)

**Decision**: All symbols exist in SDK 0.1.29. The SDK uses lazy imports (`from copilot import ...`) which is correct for optional-dependency pattern.
**Rationale**: SDK is in technical preview but these are core symbols unlikely to be removed without a major version change.
**Risk**: If a symbol is renamed/removed in a future SDK release, the application will fail at runtime. Mitigation: pin to `>=0.1.29,<0.2.0` range.

### R-003: Frontend Dependency Versions

| Package | Current Spec | Latest Stable | Action |
|---------|-------------|---------------|--------|
| `react` | `^18.3.1` | 18.3.1 (React 19 is out but migration is out of scope per spec assumptions) | No change |
| `react-dom` | `^18.3.1` | 18.3.1 | No change |
| `@tanstack/react-query` | `^5.17.0` | 5.90.7 | Bump to `^5.90.0` |
| `vite` | `^5.4.0` | 5.4.19 (Vite 7.x is a major upgrade, out of scope) | No change needed (^5.4.0 covers 5.4.x) |
| `vitest` | `^4.0.18` | 4.0.18 | Already at latest |
| `@playwright/test` | `^1.58.1` | 1.58.2 | Already covered by `^1.58.1` |
| `typescript` | `~5.4.0` | 5.4.5 | Already covered by `~5.4.0` |

**Decision**: React stays at 18.x (upgrading to React 19 is out of scope per spec assumptions). Vite stays at 5.x (7.x is a major version jump). Bump @tanstack/react-query. Other deps are already at or near latest within their semver ranges.
**Rationale**: The spec explicitly states "Frontend dependency bumps are straightforward and do not require React version migration steps."
**Alternatives considered**: React 19 migration rejected — introduces breaking changes (string refs, propTypes removal) requiring significant refactoring beyond scope.

### R-004: `agent-framework-core` Removal Verification

**Search results**: Zero imports of `agent-framework-core` or `agent_framework_core` found in the entire codebase. The system uses its own `workflow_orchestrator/` module for orchestration.

**Decision**: Safe to remove from `pyproject.toml`.
**Rationale**: Package was never imported; the system has its own orchestration layer.

---

## Phase 2 — DRY Consolidation Research

### R-005: CopilotClientPool Design

**Current duplication** (verified):
- `CopilotCompletionProvider` (`completion_providers.py:67-94`): `_clients: dict[str, Any]`, `_token_key()`, `_get_or_create_client()`
- `GitHubCopilotModelFetcher` (`model_fetcher.py:76-98`): Identical `_clients: dict[str, Any]`, `_token_key()`, `_get_or_create_client()`

Both implementations:
1. Use `hashlib.sha256(token.encode()).hexdigest()[:16]` for key derivation
2. Lazy-import `CopilotClient` and `CopilotClientOptions`
3. Call `client.start()` on creation
4. Cache by token hash in an unbounded `dict`

**Decision**: Extract a `CopilotClientPool` class in `completion_providers.py` (the first file that uses it). Both consumers reference this single pool. The pool uses a `BoundedDict` to prevent unbounded growth (maxlen=50, sufficient for multi-tenant token scenarios).
**Rationale**: Identical code in two files; single pool eliminates drift risk.
**Alternatives considered**: Module-level function rejected — class encapsulation is cleaner for lifecycle management (`cleanup()`).

### R-006: `_with_fallback()` Helper Design

**Current fallback patterns** (verified in `service.py`):

1. **Copilot assignment** (lines ~2162-2188): `_assign_copilot_graphql()` → `_assign_copilot_rest()` on failure
2. **Add issue to project** (lines ~1404-1443): GraphQL mutation → verify → REST fallback
3. **Review request**: REST/GraphQL fallback pattern

**Decision**: Extract `_with_fallback(primary_fn, fallback_fn, context_msg)` as a private method on `GitHubProjectsService`. The helper:
- Calls `primary_fn()`, returns result on success
- On specified exception types (e.g., `httpx.HTTPStatusError`, `Exception`), logs warning with `context_msg` and calls `fallback_fn()`
- Propagates unrecoverable errors immediately

**Rationale**: Three+ instances of the same try/primary/except/fallback pattern. Single helper reduces boilerplate and ensures consistent logging.
**Alternatives considered**: Decorator pattern rejected — the fallback functions have different signatures requiring closures anyway; a simple helper is more readable.

### R-007: Retry Logic Unification

**Current state** (verified):
- `_request_with_retry()` (lines 164-258): Handles 429/502/503 with exponential backoff, rate limit headers, max 3 retries
- `_graphql()` (lines 260-329): Delegates to `_request_with_retry()` internally, adds ETag caching layer

**Finding**: The retry logic is already largely unified — `_graphql()` calls `_request_with_retry()`. The "overlap" is architectural, not duplicated code. The ETag caching in `_graphql()` is an optimization layer on top of the retry mechanism.

**Decision**: No major refactoring needed. Document the relationship clearly with code comments. The retry strategy in `_request_with_retry()` IS the single retry mechanism; `_graphql()` is a higher-level wrapper that adds caching.
**Rationale**: Extracting further would be premature abstraction (violates Constitution Principle V). The two methods have different responsibilities.
**Alternatives considered**: Merging into one method rejected — would conflate caching concern with retry concern, reducing clarity.

### R-008: Header Construction Consolidation

**Current state** (verified):
- `_build_headers(access_token)` (line 95): Standard REST headers
- Various `extra_headers` passed to `_graphql()` (e.g., `GraphQL-Features` for Copilot assignment)
- Inline header construction in REST fallback paths (lines ~1570-1574)

**Decision**: Keep `_build_headers()` as the single builder. Eliminate inline header construction in REST fallback paths by calling `_build_headers()` instead. The `extra_headers` pattern in `_graphql()` already supports feature flags cleanly.
**Rationale**: `_build_headers()` is already the canonical builder; the issue is scattered inline alternatives that don't use it.
**Alternatives considered**: Single mega-builder with all flag combinations rejected — would be over-engineered for the current use cases.

---

## Phase 3 — Anti-Pattern Research

### R-009: Hardcoded Model Parameterization

**Current state**: `"claude-opus-4.6"` hardcoded in:
1. `graphql.py` line 266: Inside `ASSIGN_COPILOT_MUTATION` GraphQL string
2. `service.py` line ~2223: Inside REST API payload

**Decision**: Replace the GraphQL mutation with a parameterized version using a `$model` variable. Pass the model value from `AgentAssignmentConfig.model` through the calling code. Apply same fix to REST payload.
**Rationale**: Hardcoded model names prevent configuration changes and will silently break when models are renamed/deprecated.

### R-010: Chat State Documentation vs. Persistence

**Current state**: `_messages`, `_proposals`, `_recommendations` in `api/chat.py` (lines 49-52) are plain unbounded `dict`s.

**Decision**: Add explicit TODO documentation noting intentional MVP in-memory behavior, AND convert to `BoundedDict` (maxlen=1000) to prevent unbounded memory growth. This is a low-risk change that addresses both the documentation gap and the memory safety issue.
**Rationale**: Migrating to SQLite is a significant effort (new schema, async queries, migration) disproportionate to MVP. Documenting + bounding is the right balance.

### R-011: `delete_files` Resolution

**Current state**: Parameter accepted but logged as warning and ignored (`github_commit_workflow.py` lines 118-127). The GraphQL `createCommitOnBranch` mutation supports `fileChanges.deletions`.

**Decision**: Implement file deletion support. The `createCommitOnBranch` mutation already used by the codebase supports a `deletions` field in `fileChanges`. Add the deletion entries when `delete_files` is provided.
**Rationale**: The infrastructure is already in place (GraphQL mutation supports it). Implementation is ~10 lines. Removing the parameter would break any callers that pass it.
**Alternatives considered**: Removing the parameter rejected — it's better to fulfill the documented contract.

### R-012: OAuth State Documentation

**Current state**: `_oauth_states` in `github_auth.py` (line 31) is already a `BoundedDict(maxlen=1000)`.

**Decision**: Add documentation comments explaining the single-instance limitation and the 1000-entry cap. No migration to SQLite needed.
**Rationale**: OAuth state is inherently ephemeral (short-lived verification tokens). Persisting to SQLite adds unnecessary complexity for a flow that completes in seconds.

### R-013: Singleton Registration Pattern

**Current state**: Three services use dual registration:
1. `github_service`: module-level instance + `app.state.github_service`
2. `connection_manager`: module-level instance + `app.state.connection_manager`
3. `db`: module-level connection + `app.state.db`

`dependencies.py` checks `app.state` first, falls back to module-level.

**Decision**: Consolidate to `app.state` only (preferred per spec for testability). Remove module-level fallbacks in `dependencies.py`. Ensure `main.py` always sets `app.state` before any routes are served.
**Rationale**: Dual registration is confusing and makes it unclear which instance is actually being used. `app.state` is the FastAPI-idiomatic pattern.

### R-014: In-Memory Cache Audit

| Cache | File | Type | Bounded? | Action |
|-------|------|------|----------|--------|
| `_pipeline_states` | `workflow_orchestrator/transitions.py:10` | `dict[int, PipelineState]` | ❌ | Convert to `BoundedDict(maxlen=500)` |
| `_issue_main_branches` | `workflow_orchestrator/transitions.py:15` | `dict[int, MainBranchInfo]` | ❌ | Convert to `BoundedDict(maxlen=500)` |
| `_issue_sub_issue_map` | `workflow_orchestrator/transitions.py:22` | `dict[int, dict]` | ❌ | Convert to `BoundedDict(maxlen=500)` |
| `_messages` | `api/chat.py:49` | `dict` | ❌ | Convert to `BoundedDict(maxlen=1000)` |
| `_proposals` | `api/chat.py:50` | `dict` | ❌ | Convert to `BoundedDict(maxlen=1000)` |
| `_recommendations` | `api/chat.py:51` | `dict` | ❌ | Convert to `BoundedDict(maxlen=1000)` |
| `_clients` | `completion_providers.py:67` | `dict` | ❌ | Replaced by `CopilotClientPool` with `BoundedDict(maxlen=50)` |
| `_clients` | `model_fetcher.py:76` | `dict` | ❌ | Replaced by shared `CopilotClientPool` |
| `_processed_issue_prs` | `copilot_polling/state.py:32` | `BoundedSet` | ✅ | No change |
| `_posted_agent_outputs` | `copilot_polling/state.py:35` | `BoundedSet` | ✅ | No change |
| `_claimed_child_prs` | `copilot_polling/state.py:41` | `BoundedSet` | ✅ | No change |
| `_pending_agent_assignments` | `copilot_polling/state.py:47` | `BoundedDict` | ✅ | No change |
| `_system_marked_ready_prs` | `copilot_polling/state.py:59` | `BoundedSet` | ✅ | No change |
| `_recovery_last_attempt` | `copilot_polling/state.py:63` | `BoundedDict` | ✅ | No change |
| `_oauth_states` | `github_auth.py:31` | `BoundedDict` | ✅ | Add documentation only |
| `_processed_delivery_ids` | `api/webhooks.py` | `BoundedSet` | ✅ | No change |
| `_agent_sessions` | `services/agent_creator.py` | `BoundedDict` | ✅ | No change |

**Decision**: Convert all 6 unbounded caches to bounded equivalents. The `maxlen` values are chosen to be generous enough for normal operation while preventing runaway growth.
**Rationale**: Unbounded in-memory caches are a production risk — a long-running server processing many issues/projects will eventually exhaust memory.
