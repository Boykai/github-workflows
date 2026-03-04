# Data Model: Audit & Refactor FastAPI+React GitHub Projects Copilot Codebase

**Feature**: 018-audit-refactor-codebase
**Date**: 2026-03-04

> This feature is a refactoring effort — no new database tables or persistent data models are introduced. The entities below describe the **in-code abstractions** being created or modified.

## Key Entities

### CopilotClientPool

**Location**: `backend/src/services/completion_providers.py` (added in-place)
**Purpose**: Shared, bounded cache of `CopilotClient` instances keyed by token fingerprint. Eliminates duplicate client-caching logic in `CopilotCompletionProvider` and `GitHubCopilotModelFetcher`.

| Field | Type | Description |
|-------|------|-------------|
| `_clients` | `BoundedDict[str, Any]` | Token-hash → CopilotClient instance cache (maxlen=50) |

| Method | Signature | Description |
|--------|-----------|-------------|
| `token_key` | `@staticmethod (token: str) -> str` | SHA-256 hash of token, truncated to 16 chars |
| `get_or_create` | `async (github_token: str) -> CopilotClient` | Returns cached client or creates new one |
| `cleanup` | `async () -> None` | Stops all cached clients |

**Relationships**:
- Used by `CopilotCompletionProvider.complete()` — gets client for AI completion sessions
- Used by `GitHubCopilotModelFetcher.fetch_models()` — gets client for model listing

**Validation Rules**:
- `github_token` must be non-empty
- Pool is bounded to 50 entries (FIFO eviction via BoundedDict)

---

### _with_fallback Helper

**Location**: `backend/src/services/github_projects/service.py` (added as private method on `GitHubProjectsService`)
**Purpose**: Generic fallback executor that tries a primary async function and falls back to a secondary on failure.

| Parameter | Type | Description |
|-----------|------|-------------|
| `primary_fn` | `Callable[[], Awaitable[T]]` | Primary operation (zero-arg async callable) |
| `fallback_fn` | `Callable[[], Awaitable[T]]` | Fallback operation (zero-arg async callable) |
| `context_msg` | `str` | Descriptive context for logging |

| Return | Type | Description |
|--------|------|-------------|
| result | `T` | Result from whichever function succeeded |

**Behavior**:
1. Call `primary_fn()` — return result on success
2. On `Exception`, log warning with `context_msg` and exception details
3. Call `fallback_fn()` — return result or propagate exception

**Usage Sites**:
- `assign_copilot()`: GraphQL primary → REST fallback
- `add_issue_to_project()`: GraphQL primary → REST fallback
- `request_copilot_review()`: REST primary → GraphQL fallback

---

### Unified Header Builder (Enhanced `_build_headers`)

**Location**: `backend/src/services/github_projects/service.py` (existing method, enhanced)
**Purpose**: Single source of truth for GitHub API HTTP headers.

| Parameter | Type | Description |
|-----------|------|-------------|
| `access_token` | `str` | GitHub access token |
| `graphql_features` | `str \| None` | Optional `GraphQL-Features` header value |

| Return | Type | Description |
|--------|------|-------------|
| headers | `dict[str, str]` | Complete header dict for the request |

**Output always includes**:
- `Authorization: Bearer {access_token}`
- `Accept: application/vnd.github+json`
- `X-GitHub-Api-Version: 2022-11-28`

**Optional additions**:
- `GraphQL-Features: {value}` when `graphql_features` is provided

---

### Parameterized ASSIGN_COPILOT_MUTATION

**Location**: `backend/src/services/github_projects/graphql.py`
**Change**: Replace hardcoded `model: "claude-opus-4.6"` with a GraphQL variable `$model: String!`.

**Before**:
```graphql
mutation($assignableId: ID!, $assigneeIds: [ID!]!) {
  addAssigneesToAssignable(input: { ... model: "claude-opus-4.6" ... })
}
```

**After**:
```graphql
mutation($assignableId: ID!, $assigneeIds: [ID!]!, $model: String!) {
  addAssigneesToAssignable(input: { ... model: $model ... })
}
```

Callers pass `model` from `AgentAssignmentConfig.model`.

---

### Bounded Chat State Dictionaries

**Location**: `backend/src/api/chat.py`
**Change**: Convert plain `dict` to `BoundedDict` and add TODO documentation.

| Cache | Before | After | Max Size |
|-------|--------|-------|----------|
| `_messages` | `dict[str, list[ChatMessage]]` | `BoundedDict[str, list[ChatMessage]]` | 1000 |
| `_proposals` | `dict[str, AITaskProposal]` | `BoundedDict[str, AITaskProposal]` | 1000 |
| `_recommendations` | `dict[str, IssueRecommendation]` | `BoundedDict[str, IssueRecommendation]` | 1000 |

---

### Bounded Workflow Orchestrator Caches

**Location**: `backend/src/services/workflow_orchestrator/transitions.py`
**Change**: Convert plain `dict` to `BoundedDict`.

| Cache | Before | After | Max Size |
|-------|--------|-------|----------|
| `_pipeline_states` | `dict[int, PipelineState]` | `BoundedDict[int, PipelineState]` | 500 |
| `_issue_main_branches` | `dict[int, MainBranchInfo]` | `BoundedDict[int, MainBranchInfo]` | 500 |
| `_issue_sub_issue_map` | `dict[int, dict[str, dict]]` | `BoundedDict[int, dict[str, dict]]` | 500 |

---

## State Transitions

No new state machines are introduced. The existing workflow orchestrator state transitions (`PipelineState` enum) are preserved unchanged — only the backing storage is changed from unbounded `dict` to `BoundedDict`.

## Entity Relationship Summary

```text
CopilotClientPool
  └── used by CopilotCompletionProvider (completion sessions)
  └── used by GitHubCopilotModelFetcher (model listing)

GitHubProjectsService
  ├── _with_fallback() helper
  │   ├── assign_copilot() [GraphQL → REST]
  │   ├── add_issue_to_project() [GraphQL → REST]
  │   └── request_copilot_review() [REST → GraphQL]
  └── _build_headers() unified builder
      └── used by all REST and GraphQL request paths
```
