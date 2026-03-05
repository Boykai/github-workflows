# Research: Codebase Audit & Refactor

**Feature**: 018-codebase-audit-refactor
**Date**: 2026-03-05

## R1: CopilotClient Caching Duplication

**Context**: `CopilotCompletionProvider` (completion_providers.py L70-99) and `GitHubCopilotModelFetcher` (model_fetcher.py L82-103) both maintain independent `_clients: dict[str, Any]` caches with identical `_token_key()` (SHA-256 of first 16 chars) and `_get_or_create_client()` logic.

**Decision**: Extract a `CopilotClientPool` class into `completion_providers.py` (since it already imports the Copilot SDK). Both services will reference the same pool instance. The pool uses `BoundedDict(maxlen=50)` and exposes `get_or_create(token)`, `cleanup()`, and `remove(token)`.

**Rationale**: Eliminates exact code duplication (~30 lines × 2). The model_fetcher version lacks `cleanup()`, meaning its clients are never stopped — the shared pool fixes this. Using `BoundedDict` adds memory safety (FR-008).

**Alternatives considered**:
- Keep duplication, add cleanup to model_fetcher → fixes the cleanup bug but leaves 30 lines of identical code
- Module-level function instead of class → less composable, harder to inject in tests

## R2: REST/GraphQL Fallback Pattern

**Context**: At least 3 methods in service.py use identical fallback chains:
1. `assign_copilot_to_issue` (L2140): GraphQL → REST fallback
2. `request_copilot_review` (L3228): REST → GraphQL fallback
3. `add_issue_to_project` (L1384): GraphQL → verify → REST fallback

All follow: try primary → catch Exception → log → try fallback → catch Exception → log → return result/raise.

**Decision**: Add an `async _with_fallback(primary_fn, fallback_fn, context_msg)` helper method to `GitHubProjectsService`. Returns a `tuple[Any, str]` (result, strategy_used). Logs both attempts. Raises if both fail (wrapping both exceptions in the error message).

**Rationale**: The 3-way pattern (add_issue_to_project with verify step) still benefits — the verify can be the "primary" and the REST fallback is the "fallback." Reduces ~20 lines of boilerplate per call site.

**Alternatives considered**:
- Decorator-based approach → too implicit, harder to debug
- Leave as-is → bug-prone when error handling needs updating in 3+ places

## R3: Retry Logic Unification

**Context**: `_request_with_retry()` (L178-272) handles HTTP retries with exponential backoff for 429/502/503 and rate-limit detection via `X-RateLimit-Remaining`. `_graphql()` (L274-349) delegates to `_request_with_retry()` — no separate retry logic. The overlap is minimal; `_graphql()` adds ETag caching but uses the shared retry method.

**Decision**: The retry logic is already effectively unified in `_request_with_retry()`. The GraphQL method correctly delegates. **No structural change needed.** However, `_request_with_retry()` should be enhanced to:
1. Respect `retry-after` headers (FR-020) — currently only checks `X-RateLimit-Reset`
2. Add a configurable inter-call delay (FR-018) — 500ms default

**Rationale**: The research showed the perceived duplication was less than expected. `_graphql()` is a wrapper that adds caching, not its own retry. The improvements target the single existing method.

**Alternatives considered**:
- Refactor `_graphql()` to have its own retry → would create actual duplication (worse)
- Third-party retry library (tenacity) → already a dependency but httpx-specific retry needs custom handling anyway

## R4: Header Construction

**Context**: `_build_headers()` (L95-101) returns REST headers. `_graphql()` merges `extra_headers` dict on top. Three call sites pass `GraphQL-Features` headers:
- `get_copilot_bot_id` → `"issues_copilot_assignment_api_support,coding_agent_model_selection"`
- `_assign_copilot_graphql` → same value
- `request_copilot_review` → `"copilot_code_review"`

**Decision**: Add an optional `graphql_features: list[str] | None = None` parameter to `_graphql()`. When provided, it constructs the `GraphQL-Features` header internally (joined by comma). Remove inline `extra_headers` dicts from callers.

**Rationale**: This is simpler than a full "header builder class" — the only varying header is `GraphQL-Features`. The `_build_headers()` method stays as-is for REST. Callers pass a clean list of feature strings instead of constructing dicts.

**Alternatives considered**:
- Full HeaderBuilder class → over-engineered for a single varying header
- String constants for feature combinations → fragile, doesn't compose

## R5: Hardcoded Model in ASSIGN_COPILOT_MUTATION

**Context**: `graphql.py` L267 has `model: "claude-opus-4.6"` hardcoded in the mutation string. The caller (`_assign_copilot_graphql` in service.py) already has the model available in `AgentAssignmentConfig.model`.

**Decision**: Add `$model: String!` as a GraphQL variable to `ASSIGN_COPILOT_MUTATION`. Replace `model: "claude-opus-4.6"` with `model: $model`. Update the caller to pass `model` in the variables dict.

**Rationale**: Straightforward parameterization. The GraphQL spec supports string variables for this field. No risk — the same value flows through, just as a variable instead of a literal.

**Alternatives considered**: None — this is a clear bug fix with one correct approach.

## R6: File Deletion in Commit Workflow

**Context**: `github_commit_workflow.py` L48 accepts `delete_files: list[str] | None = None`. L124-129 logs a warning that deletion is not implemented. The `CREATE_COMMIT_ON_BRANCH_MUTATION` (graphql.py L851) structures `fileChanges` with `additions` but currently has no `deletions` field.

**Decision**: Extend the `commit_files()` method in `service.py` to accept an optional `deletions: list[str]` parameter. Add `deletions: [{path: $path}]` to the `fileChanges` input in `CREATE_COMMIT_ON_BRANCH_MUTATION`. Update `github_commit_workflow.py` to forward `delete_files` as deletions.

**Rationale**: GitHub's `createCommitOnBranch` mutation supports `deletions` in `fileChanges` (documented at https://docs.github.com/en/graphql/reference/input-objects#filechanges). Implementation is additive — adding a `deletions` array alongside `additions`.

**Alternatives considered**:
- Remove the parameter → discards a useful API surface the caller already set up for

## R7: Chat State Persistence

**Context**: `api/chat.py` L51-55 uses three unbounded module-level dicts: `_messages`, `_proposals`, `_recommendations`. Models exist: `ChatMessage` (chat.py L72), `AITaskProposal` (recommendation.py L33), `IssueRecommendation` (recommendation.py). Database service uses `aiosqlite` with migration system (10 existing migrations).

**Decision**: Create migration `011_chat_persistence.sql` with three tables:
- `chat_messages` (message_id TEXT PK, session_id TEXT, sender_type TEXT, content TEXT, action_type TEXT, action_data TEXT, timestamp TEXT)
- `chat_proposals` (proposal_id TEXT PK, session_id TEXT, original_input TEXT, proposed_title TEXT, proposed_description TEXT, status TEXT, edited_title TEXT, edited_description TEXT, created_at TEXT, expires_at TEXT)
- `chat_recommendations` (recommendation_id TEXT PK, session_id TEXT, data TEXT, status TEXT, created_at TEXT)

Refactor `api/chat.py` to read/write from SQLite via `get_db()`. Remove module-level dicts.

**Rationale**: Pydantic models already define the schema. SQLite is the existing storage layer with proven migration tooling. The `recommendation_id` as TEXT PK matches existing patterns (see `chores` table with `id TEXT PRIMARY KEY`).

**Alternatives considered**:
- JSON file persistence → fragile, no concurrent access safety
- Keep in-memory with TODO comments → user explicitly chose SQLite persistence in clarification

## R8: Service Initialization Pattern

**Context**: Three module-level singleton instances exist:
- `service.py` L4832: `github_projects_service = GitHubProjectsService()`
- `github_auth.py` L310: `github_auth_service = GitHubAuthService()`
- `websocket.py` L105: `connection_manager = ConnectionManager()`

`dependencies.py` tries `app.state` first, falls back to these globals. Many files import the globals directly (e.g., `copilot_polling/__init__.py` L37).

**Decision**: Remove module-level service instantiations. Keep `app.state` as the sole registration point. Update `dependencies.py` to remove fallbacks (raise `RuntimeError` if `app.state` not populated). Update all direct imports to use dependency injection via `dependencies.py` functions.

**Rationale**: Dual initialization creates confusion about which instance is "real." The `app.state` pattern is idiomatic FastAPI and enables clean test overrides. Direct imports of module globals bypass the lifespan entirely.

**Alternatives considered**:
- Keep globals as default, document → perpetuates the dual-init anti-pattern

## R9: Bounded Collection Audit

**Context**: Research identified the following **unbounded** collections:

| Location | Variable | Current Type |
|----------|----------|-------------|
| `copilot_polling/state.py` L13 | `processed_issues` (in `PollingState`) | `dict[int, datetime]` |
| `workflow_orchestrator/transitions.py` L10 | `_pipeline_states` | `dict[int, PipelineState]` |
| `workflow_orchestrator/transitions.py` L15 | `_issue_main_branches` | `dict[int, MainBranchInfo]` |
| `workflow_orchestrator/transitions.py` L22 | `_issue_sub_issue_map` | `dict[int, dict]` |
| `workflow_orchestrator/config.py` L18 | `_transitions` | `list[WorkflowTransition]` |
| `workflow_orchestrator/config.py` L21 | `_workflow_configs` | `dict[str, WorkflowConfiguration]` |
| `workflow_orchestrator/orchestrator.py` L47 | `_tracking_table_cache` | `dict[int, list]` |
| `api/chat.py` L49-52 | `_messages`, `_proposals`, `_recommendations` | `dict` |
| `api/workflow.py` L42 | `_recent_requests` | `dict` |

**Decision**: Convert all to `BoundedDict` or `BoundedSet` with appropriate capacities:
- `processed_issues` → `BoundedDict(maxlen=2000)` (tracks issue IDs, high cardinality)
- `_pipeline_states` → `BoundedDict(maxlen=500)` (active pipelines)
- `_issue_main_branches` → `BoundedDict(maxlen=500)`
- `_issue_sub_issue_map` → `BoundedDict(maxlen=500)`
- `_workflow_configs` → `BoundedDict(maxlen=100)` (config objects, low cardinality)
- `_tracking_table_cache` → `BoundedDict(maxlen=200)`
- `_recent_requests` → `BoundedDict(maxlen=1000)`
- Chat dicts → removed (migrated to SQLite per R7)
- `_transitions` → keep as `list` (loaded once from config, static after init; bounding a config list is inappropriate)

**Rationale**: `BoundedDict`/`BoundedSet` already exist in `utils.py` with FIFO eviction. Capacities chosen based on expected cardinality in single-instance deployment.

**Alternatives considered**:
- TTL-based eviction → more complex, `BoundedDict` FIFO is simpler and sufficient
- No change → violates FR-017

## R10: Adaptive Polling

**Context**: `polling_loop.py` currently has a fixed `interval_seconds=60` default with rate-limit-reactive behaviors:
- Doubles interval when `remaining ≤ 200` (RATE_LIMIT_SLOW_THRESHOLD)
- Pauses until reset when `remaining ≤ 50` (RATE_LIMIT_PAUSE_THRESHOLD)
- Skips expensive steps when `remaining ≤ 100`

There is **no activity-based adaptive polling** — the interval doesn't change based on whether state changes were detected.

**Decision**: Add a `_consecutive_idle_polls` counter. After each poll cycle, if no state changes were detected (no PRs merged, no statuses advanced, no agent outputs posted), increment the counter. The effective interval becomes `base_interval * (2 ** min(consecutive_idle, max_doublings))`, capping at `MAX_POLL_INTERVAL_SECONDS = 300` (5 min). On any state change, reset `_consecutive_idle_polls = 0` and return to base interval.

**Rationale**: Matches FR-019 exactly (60s base, 2x backoff, 5min cap). The existing rate-limit-based adjustments remain as a separate concern — they can override (extend) the interval further when rate limits are low.

**Alternatives considered**:
- Linear backoff → less aggressive, takes longer to reduce API load during idle periods
- Exponential but different base/multiplier → user chose conservative (C option: 500ms/60s/2x)

## R11: Inter-Call Timing Buffers

**Context**: `_request_with_retry()` makes calls immediately. Bulk operations (e.g., assigning agents to multiple issues) can fire many requests in rapid succession.

**Decision**: Add a class-level `_last_request_time: float` (monotonic clock) and `_min_request_interval: float = 0.5` to `GitHubProjectsService`. At the start of `_request_with_retry()`, calculate elapsed time since last request. If < 0.5s, `await asyncio.sleep(remaining)`. Update `_last_request_time` after each request.

**Rationale**: Simple throttle that applies to all GitHub API calls uniformly. 500ms spacing allows ~7,200 calls/hour — well within the 5,000/hour limit even before considering that not all time is spent making API calls.

**Alternatives considered**:
- Token bucket algorithm → more complex, unnecessary for single-instance deployment
- Only throttle specific methods → fragile, easy to miss a call site

## R12: Dependency Version Audit

**Context**: Current backend versions from `pyproject.toml`:
- `github-copilot-sdk>=0.1.0`
- `agent-framework-core>=1.0.0a1` (UNUSED)
- `openai>=1.0.0`
- `azure-ai-inference>=1.0.0b1`

Current frontend versions from `package.json`:
- `react: ^18.3.1`, `@tanstack/react-query: ^5.17.0`
- `vite: ^5.4.0`, `vitest: ^4.0.18`, `@playwright/test: ^1.58.1`

**Decision**: 
- Remove `agent-framework-core` entirely
- Bump lower bounds for other packages to latest stable at time of implementation (exact versions determined during implementation by checking PyPI/npm)
- Keep `>=` style for backend (pip-style), `^` style for frontend (npm-style) per existing conventions

**Rationale**: The spec supports latest stable. `agent-framework-core` is confirmed unused (grep for all imports in the codebase returns zero matches). Version bumps use minimum-version constraints consistent with project style.

**Alternatives considered**:
- Pin exact versions → project uses `>=` style, switching would be a style change outside scope
- Keep `agent-framework-core` → confirmed unused, adds unnecessary install time
