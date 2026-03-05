# Data Model: Audit & Refactor FastAPI + React GitHub Projects V2 Codebase

**Feature**: 018-audit-refactor-codebase | **Date**: 2026-03-05

---

## Overview

This refactor introduces no new persistent data models. All changes are to in-memory abstractions and internal helper APIs. The entities below describe the **new or modified runtime objects** introduced by the DRY consolidation (Phase 2) and anti-pattern fixes (Phase 3).

---

## Entity: CopilotClientPool

**Location**: `backend/src/services/completion_providers.py`
**Type**: New class (extracted from duplicated logic)

| Field | Type | Description |
|-------|------|-------------|
| `_clients` | `dict[str, CopilotClient]` | Cache of initialized clients, keyed by token fingerprint |

**Methods**:

| Method | Signature | Description |
|--------|-----------|-------------|
| `token_key` | `@staticmethod (github_token: str) -> str` | SHA-256 hash of token, truncated to 16 chars |
| `get_or_create` | `async (github_token: str) -> CopilotClient` | Returns cached client or creates new one |
| `remove` | `(github_token: str) -> None` | Removes a cached client (for cleanup) |
| `clear` | `() -> None` | Clears all cached clients |

**Relationships**:
- Used by `CopilotCompletionProvider` (completion requests)
- Used by `GitHubCopilotModelFetcher` (model listing)

**Validation Rules**:
- `github_token` must be non-empty string
- Cache key collision risk is negligible (SHA-256 truncated to 16 hex chars = 64 bits)

---

## Entity: FallbackHelper (inline pattern)

**Location**: `backend/src/services/github_projects/service.py`
**Type**: New private async method on `GitHubProjectsService`

| Parameter | Type | Description |
|-----------|------|-------------|
| `primary_fn` | `Callable[[], Awaitable[T]]` | Primary operation to attempt |
| `fallback_fn` | `Callable[[], Awaitable[T]]` | Fallback operation if primary fails |
| `context_msg` | `str` | Descriptive context for logging |

**Return**: `T` — result of whichever function succeeds

**State Transitions**:
```
IDLE → PRIMARY_ATTEMPT → SUCCESS (return primary result)
                       → PRIMARY_FAILED → FALLBACK_ATTEMPT → SUCCESS (return fallback result)
                                                            → FALLBACK_FAILED (raise with context)
```

**Validation Rules**:
- Both functions must be async callables
- `context_msg` used in log messages only (no operational impact)
- If primary raises, the exception is logged at WARNING level
- If fallback also raises, a combined error is raised preserving both exception messages

---

## Entity: Unified Retry Configuration

**Location**: `backend/src/services/github_projects/service.py`
**Type**: Enhancement to existing `_request_with_retry()` method

| Constant | Value | Description |
|----------|-------|-------------|
| `MAX_RETRIES` | `3` | Maximum retry attempts (unchanged) |
| `INITIAL_BACKOFF_SECONDS` | `1` | Initial backoff delay (unchanged) |
| `MAX_BACKOFF_SECONDS` | `30` | Maximum backoff cap (unchanged) |

**Retryable Conditions** (unified):
- HTTP 429 (Too Many Requests)
- HTTP 502 (Bad Gateway)
- HTTP 503 (Service Unavailable)
- HTTP 403 with `X-RateLimit-Remaining: 0` (primary rate limit)
- Secondary rate limit (detected via response body or headers)

**Non-Retryable** (fail fast):
- HTTP 401 (Unauthorized)
- HTTP 404 (Not Found)
- HTTP 422 (Unprocessable Entity)
- Any other 4xx client error

---

## Entity: Enhanced Header Builder

**Location**: `backend/src/services/github_projects/service.py`
**Type**: Enhancement to existing `_build_headers()` static method

| Parameter | Type | Description |
|-----------|------|-------------|
| `access_token` | `str` | GitHub access token (required) |
| `extra_headers` | `dict[str, str] \| None` | Additional headers to merge (optional) |
| `graphql_features` | `list[str] \| None` | GraphQL feature flags for `GraphQL-Features` header (optional) |

**Base Headers** (always included):
```
Authorization: Bearer {access_token}
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

**GraphQL Feature Flags** (when provided):
```
GraphQL-Features: {comma-separated feature flags}
```

---

## Entity: ASSIGN_COPILOT_MUTATION (modified)

**Location**: `backend/src/services/github_projects/graphql.py`
**Type**: Modified GraphQL mutation string

**Change**: Add `$model: String!` variable, replacing hardcoded `model: "claude-opus-4.6"`

**New Variables**:

| Variable | Type | Description |
|----------|------|-------------|
| `$issueId` | `ID!` | Issue node ID (unchanged) |
| `$assigneeIds` | `[ID!]!` | Assignee IDs (unchanged) |
| `$repoId` | `ID!` | Repository ID (unchanged) |
| `$baseRef` | `String!` | Base branch reference (unchanged) |
| `$customInstructions` | `String!` | Custom instructions (unchanged) |
| `$customAgent` | `String!` | Custom agent identifier (unchanged) |
| `$model` | `String!` | **NEW** — AI model identifier (was hardcoded) |

---

## Entity: Bounded In-Memory Caches (audit)

**Type**: Modification of existing module-level variables

All caches below are converted from plain `dict` to `BoundedDict` with FIFO eviction:

| Cache | Module | Max Size | Key Type | Value Type |
|-------|--------|----------|----------|------------|
| `_messages` | `api/chat.py` | 500 | `str` (session_id) | `list[ChatMessage]` |
| `_proposals` | `api/chat.py` | 500 | `str` (proposal_id) | `AITaskProposal` |
| `_recommendations` | `api/chat.py` | 500 | `str` (rec_id) | `IssueRecommendation` |
| `_recent_requests` | `api/workflow.py` | 1000 | `str` | `tuple[datetime, str]` |
| `_conversations` | `services/chores/chat.py` | 200 | `str` | `dict` |
| `_pipeline_states` | `workflow_orchestrator/transitions.py` | 500 | `int` (issue_id) | `PipelineState` |
| `_issue_main_branches` | `workflow_orchestrator/transitions.py` | 1000 | `int` (issue_id) | `MainBranchInfo` |
| `_issue_sub_issue_map` | `workflow_orchestrator/transitions.py` | 1000 | `int` (issue_id) | `dict[str, dict]` |
| `_workflow_configs` | `workflow_orchestrator/config.py` | 100 | `str` | `WorkflowConfiguration` |
| `_chat_sessions` | `services/agents/service.py` | 200 | `str` | `list[dict]` |
| `_chat_session_timestamps` | `services/agents/service.py` | 200 | `str` | `float` |
| `_signal_pending` | `services/signal_chat.py` | 500 | `str` | `dict` |

---

## Entity: CommitWorkflowResult (unchanged, file deletions added)

**Location**: `backend/src/services/github_commit_workflow.py`
**Type**: Enhancement to existing `commit_files_workflow()` function

**Change**: The `delete_files: list[str] | None` parameter will now be implemented. File paths in `delete_files` are mapped to `fileChanges.deletions` in the GraphQL `createCommitOnBranch` mutation.

**GraphQL Input Structure**:
```graphql
fileChanges: {
  additions: [{ path: "...", contents: "..." }, ...],
  deletions: [{ path: "..." }, ...]
}
```
