# Research: Audit & Refactor FastAPI + React GitHub Projects V2 Codebase

**Feature**: 018-audit-refactor-codebase | **Date**: 2026-03-05

---

## R1: Backend Dependency Versions (Phase 1)

### R1.1: `agent-framework-core` Usage Audit

- **Decision**: Remove `agent-framework-core>=1.0.0a1` from `pyproject.toml`
- **Rationale**: Grep of entire `backend/src/` confirms zero imports of `agent_framework_core` or `agent-framework-core`. The project implements its own orchestration in `services/workflow_orchestrator/`. The package is an alpha pre-release adding unnecessary install weight.
- **Alternatives considered**: Keep as optional dependency — rejected because it is never imported and creates confusion about the project's architecture.

### R1.2: `github-copilot-sdk` Version Bump

- **Decision**: Bump from `>=0.1.0` to `>=0.1.30`
- **Rationale**: Latest stable is **0.1.30** (March 2026). The codebase uses `CopilotClient`, `CopilotClientOptions`, `client.start()`, and `client.list_models()`. Release notes for 0.1.29–0.1.30 show backward-compatible changes (better exception handling in shutdown, model switching mid-session). The six API surfaces referenced in spec (CopilotClient, SessionConfig, MessageOptions, PermissionHandler, SessionEventType, list_models) remain compatible.
- **Alternatives considered**: Pin exact version `==0.1.30` — rejected because the SDK is still in technical preview and patch updates should be accepted automatically.
- **Risk**: SDK is marked "technical preview"; future 0.2.x may have breaking changes. The `>=0.1.30` floor ensures known-good baseline while accepting patches.

### R1.3: `openai` Version Bump

- **Decision**: Bump from `>=1.0.0` to `>=2.24.0`
- **Rationale**: Latest stable is **2.24.0** (February 2026). The codebase uses the `openai` package through `AzureOpenAICompletionProvider` for the fallback path. The v2.x API is a major version bump from v1.x — the codebase must be verified for compatibility. Key changes in v2: `openai.AzureOpenAI` client API remained stable; `ChatCompletion.create()` pattern preserved. The async client (`AsyncAzureOpenAI`) is compatible.
- **Alternatives considered**: Stay on `>=1.0.0` — rejected because v1 is end-of-life and missing security patches.
- **Risk**: Major version jump (1.x → 2.x). Must verify `AzureOpenAICompletionProvider` imports and API calls still work. If breaking, adapter code needed in `completion_providers.py`.

### R1.4: `azure-ai-inference` Version Bump

- **Decision**: Bump from `>=1.0.0b1` to `>=1.0.0b9`
- **Rationale**: Latest is **1.0.0b9** (February 2025). Still in preview/beta — no GA release exists. The codebase uses this for Azure AI model inference as fallback. API surfaces are backward-compatible within the 1.0.0bX series.
- **Alternatives considered**: Wait for GA — rejected because there is no GA timeline and b9 is the best available.

---

## R2: Frontend Dependency Versions (Phase 1)

### R2.1: React Version

- **Decision**: Keep at `^18.3.1` (do not upgrade to React 19)
- **Rationale**: React 19 (latest 19.2.4) introduces breaking changes: deprecated string refs removed, new `use()` hook semantics, Context API changes. The frontend has `@types/react: ^18.3.0` and `@types/react-dom: ^18.3.0`. Upgrading to 19 would require updating all type definitions, testing for deprecated API usage, and validating all component library compatibility (@dnd-kit, @radix-ui, etc.). This is out of scope for a refactor focused on backend changes.
- **Alternatives considered**: Bump to `^19.0.0` — rejected because the issue says "bump to latest stable" but the scope constraint is "no regressions" and React 19 migration is a separate effort.

### R2.2: `@tanstack/react-query` Version

- **Decision**: Bump from `^5.17.0` to `^5.90.7`
- **Rationale**: Latest is **5.90.7**. Same major version (v5), fully backward compatible. No breaking changes within 5.x line.
- **Alternatives considered**: None — straightforward minor/patch bump within same major.

### R2.3: Vite Version

- **Decision**: Bump from `^5.4.0` to `^7.3.1`
- **Rationale**: Latest stable is **7.3.1**. This is a major version jump (5 → 7). Vite 6 and 7 introduced breaking changes in config API and plugin compatibility. Must verify `vite.config.ts` and `@vitejs/plugin-react` compatibility. The `@vitejs/plugin-react: ^4.2.1` may need bumping to a v7-compatible version.
- **Alternatives considered**: Stay on Vite 5 — viable if Vite 7 migration proves complex. Recommend attempting Vite 7 first, falling back to latest Vite 5.x if breaking.
- **Risk**: Plugin compatibility. `@vitejs/plugin-react` must be updated to match Vite 7.

### R2.4: Vitest Version

- **Decision**: Keep at `^4.0.18` (already at latest)
- **Rationale**: Current version `^4.0.18` and `@vitest/coverage-v8: ^4.0.18` are already at the latest stable (4.0.18). No action needed.
- **Alternatives considered**: None — already current.

### R2.5: Playwright Version

- **Decision**: Keep at `^1.58.1` (already near-latest)
- **Rationale**: Current `@playwright/test: ^1.58.1`, latest stable is **1.58.2**. The `^1.58.1` range already accepts 1.58.2. No manifest change needed.
- **Alternatives considered**: None — already effectively current.

---

## R3: DRY Consolidation Design (Phase 2)

### R3.1: CopilotClientPool Extraction (2A)

- **Decision**: Add a `CopilotClientPool` class to `completion_providers.py` (the module that already owns the primary client caching). Both `CopilotCompletionProvider` and `GitHubCopilotModelFetcher` will import and use it.
- **Rationale**: Both modules have identical `_token_key()` (SHA-256 truncated to 16 chars) and `_get_or_create_client()` methods. The pool encapsulates: token hashing, client creation, caching, and lifecycle. Placing it in `completion_providers.py` avoids creating a new file (FR-015).
- **Alternatives considered**: (a) Put pool in `utils.py` — rejected because it's domain-specific to Copilot, not a general utility. (b) Create `copilot_pool.py` — rejected per FR-015 (no new files).

### R3.2: Fallback Helper (2B)

- **Decision**: Add `async def _with_fallback(primary_fn, fallback_fn, context_msg)` to `service.py` in the `GitHubProjectsService` class as a private method.
- **Rationale**: Three identified fallback patterns: (1) `assign_copilot_to_issue` tries GraphQL then REST, (2) review request tries REST then GraphQL, (3) `add_issue_to_project` tries GraphQL, verify, then REST. The helper captures the pattern: call primary, log + call fallback on exception, propagate fallback failure with both error contexts.
- **Alternatives considered**: Standalone module function — rejected because it needs access to logging context and the patterns are all within the same service class.

### R3.3: Unified Retry Strategy (2C)

- **Decision**: Consolidate into the existing `_request_with_retry()` method by ensuring it handles both primary rate limits (429) and secondary rate limits (403 with `X-RateLimit-Remaining: 0`) consistently. Remove any inline retry logic in `_graphql()` that duplicates this.
- **Rationale**: Currently `_request_with_retry()` handles 429/503 with exponential backoff, and separately handles 403 rate limits. The `_graphql()` method adds its own layer. Unification means all retries go through one path.
- **Alternatives considered**: Use `tenacity` library (already a dependency) — viable but would require rewriting all call sites. The existing `_request_with_retry()` is well-structured; extending it is less disruptive.

### R3.4: Header Builder Consolidation (2D)

- **Decision**: Extend `_build_headers()` to accept an optional `extra_headers: dict[str, str] | None = None` and optional `graphql_features: list[str] | None = None` parameter. Remove `_build_graphql_headers()` if it exists, and inline custom header dicts.
- **Rationale**: Currently `_build_headers()` returns base REST headers. GraphQL and Copilot mutations add extra headers inline. A single builder with optional feature flags unifies this without over-engineering.
- **Alternatives considered**: Create a `HeaderBuilder` class with fluent API — rejected per Principle V (simplicity over cleverness).

---

## R4: Anti-Pattern Remediation Design (Phase 3)

### R4.1: Parameterize Hardcoded Model (3A)

- **Decision**: Add `$model` GraphQL variable to `ASSIGN_COPILOT_MUTATION`. Pass `model` from `AgentAssignmentConfig.model` (or a default constant) at the call site in `assign_copilot_to_issue()` / `_assign_copilot_graphql()`.
- **Rationale**: The hardcoded `"claude-opus-4.6"` prevents using different models. GraphQL variables are the standard way to parameterize mutations.
- **Alternatives considered**: String interpolation in the mutation — rejected because it introduces injection risk.

### R4.2: In-Memory Chat State (3B)

- **Decision**: Add explicit TODO comments documenting the MVP in-memory approach. Full SQLite migration is deferred as a separate feature.
- **Rationale**: Migrating `_messages`, `_proposals`, `_recommendations` to SQLite requires: new migration script, new database table(s), async CRUD operations, and comprehensive testing of chat flows. This is a significant effort beyond the scope of an "audit & refactor" — it's new feature work. The spec allows "explicitly document as intentional MVP decision with a TODO comment" (FR-010). Additionally, convert these dicts to `BoundedDict` to address FR-014.
- **Alternatives considered**: Full SQLite migration — rejected for scope; will be a separate user story.

### R4.3: File Deletion Implementation (3C)

- **Decision**: Implement `delete_files` using `fileChanges.deletions` in the GraphQL `createCommitOnBranch` mutation.
- **Rationale**: The GitHub GraphQL API supports `fileChanges: { additions: [...], deletions: [...] }`. The current code only passes `additions`. Adding `deletions` is straightforward: map each `delete_files` path to `{ path: "..." }` in the `deletions` array. The parameter already exists and is documented; implementing it completes the API contract.
- **Alternatives considered**: Remove the parameter — rejected because file deletion is a useful capability and the implementation is simple.

### R4.4: OAuth State Documentation (3D)

- **Decision**: Add code comments to `_oauth_states` documenting: (1) BoundedDict(maxlen=1000) provides FIFO eviction, (2) states are lost on restart, (3) 10-minute TTL provides additional pruning, (4) future migration to SQLite is optional.
- **Rationale**: The code already uses `BoundedDict(maxlen=1000)` — the FR-012 requirement is primarily about documentation. The bounded nature is already correct; we just need to make the design decision explicit.
- **Alternatives considered**: Migrate to SQLite — deferred as optional enhancement (states are ephemeral by nature).

### R4.5: Singleton Registration Standardization (3E)

- **Decision**: Remove the fallback-to-module-global pattern in `dependencies.py`. All service access goes through `app.state` exclusively. Update tests to properly set `app.state` attributes instead of relying on module globals.
- **Rationale**: The current pattern (`getattr(app.state, ..., None)` → fallback to module import) creates hidden coupling and test pollution. Using `app.state` exclusively provides clean test isolation via `TestClient` with custom `app.state` overrides.
- **Alternatives considered**: Keep dual pattern — rejected because it defeats the purpose of `app.state` DI.

### R4.6: Bounded Cache Audit (3F)

- **Decision**: Convert all 12 identified unbounded caches to `BoundedDict` or `BoundedSet` with appropriate capacity limits.
- **Rationale**: Unbounded caches cause OOM in long-running processes. The existing `BoundedDict`/`BoundedSet` in `utils.py` are production-ready.

**Capacity assignments:**

| Cache | Location | Current Type | New Type | Max Size | Rationale |
|-------|----------|-------------|----------|----------|-----------|
| `_messages` | `api/chat.py` | `dict` | `BoundedDict` | 500 | Chat sessions; old sessions evicted |
| `_proposals` | `api/chat.py` | `dict` | `BoundedDict` | 500 | Proposals; bounded with sessions |
| `_recommendations` | `api/chat.py` | `dict` | `BoundedDict` | 500 | Recommendations; bounded with sessions |
| `_recent_requests` | `api/workflow.py` | `dict` | `BoundedDict` | 1000 | Dedup cache; high throughput |
| `_conversations` | `services/chores/chat.py` | `dict` | `BoundedDict` | 200 | Chore conversations; lower volume |
| `_pipeline_states` | `workflow_orchestrator/transitions.py` | `dict` | `BoundedDict` | 500 | Active pipelines |
| `_issue_main_branches` | `workflow_orchestrator/transitions.py` | `dict` | `BoundedDict` | 1000 | Branch mappings |
| `_issue_sub_issue_map` | `workflow_orchestrator/transitions.py` | `dict` | `BoundedDict` | 1000 | Sub-issue mappings |
| `_workflow_configs` | `workflow_orchestrator/config.py` | `dict` | `BoundedDict` | 100 | Config objects; few unique configs |
| `_chat_sessions` | `services/agents/service.py` | `dict` | `BoundedDict` | 200 | Agent chat sessions |
| `_chat_session_timestamps` | `services/agents/service.py` | `dict` | `BoundedDict` | 200 | Paired with _chat_sessions |
| `_signal_pending` | `services/signal_chat.py` | `dict` | `BoundedDict` | 500 | Pending signal messages |

---

## R5: Copilot SDK API Compatibility Verification

- **Decision**: The following APIs from `github-copilot-sdk` 0.1.30 remain compatible:
  - `CopilotClient` — constructor accepts `CopilotClientOptions`
  - `client.start()` — async initialization
  - `client.list_models()` — returns available models
  - `SessionConfig` — session configuration dataclass
  - `MessageOptions` — message sending options
  - `PermissionHandler` — permission callback interface
  - `SessionEventType` — event type enum
- **Rationale**: Release notes for 0.1.x series show additive changes only. No removed or renamed APIs within the 0.1.x line.
- **Risk**: Low. Pin floor at `>=0.1.30` to ensure the tested version is minimum.

---

## R6: In-Place Refactoring Strategy

- **Decision**: All new shared code (CopilotClientPool, _with_fallback, header builder enhancements) is added to existing modules.
  - `CopilotClientPool` → `completion_providers.py`
  - `_with_fallback()` → `service.py`
  - Header builder enhancement → `service.py` `_build_headers()` static method
- **Rationale**: FR-015 mandates no new files. Each piece of shared code is placed in the module closest to its primary consumer.
- **Alternatives considered**: Create utility modules — rejected per FR-015.
