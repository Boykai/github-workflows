# Data Model: Code Quality & Technical Debt Overhaul

**Branch**: `033-code-quality-overhaul` | **Date**: 2026-03-10

This document defines the new dataclasses, enums, and service interfaces introduced by the refactoring. No existing models are modified — only new ones are added.

## New Enums

### AgentStepState

**Location**: `backend/src/models/agent.py` (extend existing file)

```python
class AgentStepState(str, Enum):
    """Typed state values from tracking table markdown cells.

    Replaces emoji-based string matching (e.g., "✅ Done", "🔄 Active")
    with exhaustive enum matching.
    """
    DONE = "done"
    ACTIVE = "active"
    QUEUED = "queued"
    ERROR = "error"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"

    @classmethod
    def from_markdown(cls, cell_text: str) -> "AgentStepState":
        """Parse tracking table cell text into typed state.

        Matches emoji prefixes: ✅→DONE, 🔄→ACTIVE, ⏳→QUEUED, ❌→ERROR, ⏭→SKIPPED.
        Returns UNKNOWN for unrecognized patterns.
        """
        text = cell_text.strip()
        if text.startswith("✅"):
            return cls.DONE
        if text.startswith("🔄"):
            return cls.ACTIVE
        if text.startswith("⏳"):
            return cls.QUEUED
        if text.startswith("❌"):
            return cls.ERROR
        if text.startswith("⏭"):
            return cls.SKIPPED
        return cls.UNKNOWN
```

**Used by**: `recovery.py`, `agent_output.py`, `pipeline.py`

---

## New Dataclasses

### CommentScanResult

**Location**: `backend/src/services/copilot_polling/agent_output.py` (module-level)

```python
@dataclass(frozen=True)
class CommentScanResult:
    """Result of scanning PR/issue comments for completion signals."""
    has_done_marker: bool
    done_comment_id: str | None = None
    agent_output_files: list[str] = field(default_factory=list)
    merge_candidates: list[str] = field(default_factory=list)
```

### AgentResolution

**Location**: `backend/src/services/workflow_orchestrator/orchestrator.py` (module-level)

```python
@dataclass(frozen=True)
class AgentResolution:
    """Resolved agent assignment from tracking table or config."""
    agents: list[str]
    source: str  # "tracking_table" | "config" | "fallback"
    base_ref: str
    model: str
```

### PollStep

**Location**: `backend/src/services/copilot_polling/polling_loop.py` (module-level)

```python
@dataclass(frozen=True)
class PollStep:
    """Definition of a single polling loop step."""
    name: str
    execute: Callable[..., Awaitable[None]]
    is_expensive: bool = False
```

### ItemClassification

**Location**: `backend/src/services/cleanup_service.py` (module-level)

```python
@dataclass(frozen=True)
class ItemClassification:
    """Result of classifying a branch/PR for cleanup linking."""
    item_type: str  # "branch" | "pr" | "orphan"
    linked_issue_number: int | None = None
    link_method: str | None = None  # "branch_name" | "pr_body" | "ownership"
    confidence: float = 0.0
```

---

## New Service Interfaces (Phase 4 — God Class Split)

### GitHubBaseClient

**Location**: `backend/src/services/github_projects/base_client.py`

Shared infrastructure extracted from the current `GitHubProjectsService`:

| Attribute/Method | Type | Description |
|-----------------|------|-------------|
| `token` | `str` | GitHub access token |
| `rate_limit` | `RateLimitManager` | Injected rate-limit tracker |
| `_etag_cache` | `dict[str, tuple[str, Any]]` | ETag-based HTTP cache |
| `_request_coalescing` | `dict[str, asyncio.Task]` | Dedup concurrent identical requests |
| `_graphql(query, variables)` | `async → dict` | Execute GraphQL query |
| `_rest(method, path, **kwargs)` | `async → httpx.Response` | Execute REST API call |
| `_request_with_retry(fn)` | `async → T` | Retry with rate-limit backoff |

### RateLimitManager

**Location**: `backend/src/services/github_projects/rate_limit.py`

| Attribute/Method | Type | Description |
|-----------------|------|-------------|
| `remaining` | `int` | Remaining API calls |
| `reset_at` | `datetime \| None` | When rate limit resets |
| `extract_from_headers(headers)` | `→ None` | Parse X-RateLimit-* headers |
| `should_throttle()` | `→ bool` | Check if near limit |
| `wait_if_needed()` | `async → None` | Sleep until reset if throttled |

### Domain Services

Each domain service inherits `GitHubBaseClient` and exposes only its domain methods:

| Service | File | Key Methods (from current service.py) |
|---------|------|---------------------------------------|
| `GitHubIssuesService` | `issues.py` | `create_issue`, `update_issue`, `get_issue_with_comments`, `link_pr_to_issue`, `add_issue_comment`, `get_issue_body` |
| `GitHubPullRequestService` | `pull_requests.py` | `get_linked_pull_requests`, `merge_pull_request`, `mark_ready_for_review`, `request_review`, `get_pr_comments` |
| `GitHubBranchService` | `branches.py` | `create_branch`, `create_commit_on_branch`, `create_pull_request`, `get_default_branch` |
| `GitHubProjectBoardService` | `projects.py` | `get_project_items`, `update_item_status`, `list_board_projects`, `get_board_data`, `get_status_columns` |
| `GitHubIdentities` | `identities.py` | `is_copilot_author`, `is_copilot_swe_agent`, `is_copilot_reviewer_bot` (all static) |

### Dependency Injection Updates

`dependencies.py` will provide new getters:

```python
def get_github_issues_service(request: Request) -> GitHubIssuesService: ...
def get_github_pr_service(request: Request) -> GitHubPullRequestService: ...
def get_github_branch_service(request: Request) -> GitHubBranchService: ...
def get_github_board_service(request: Request) -> GitHubProjectBoardService: ...
```

Each follows the existing pattern: read from `request.app.state`, fallback to module-level singleton.

---

## Chat Message Storage Schema

**Location**: Added to existing SQLite database via migration in `backend/src/migrations/`

```sql
CREATE TABLE IF NOT EXISTS chat_messages (
    session_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    messages TEXT NOT NULL,         -- JSON array of message objects
    updated_at REAL NOT NULL,       -- Unix timestamp for TTL
    PRIMARY KEY (session_id, conversation_id)
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_updated
    ON chat_messages (updated_at);
```

**TTL cleanup query** (run on startup and periodically):
```sql
DELETE FROM chat_messages WHERE updated_at < ?;  -- ? = now - 24h
```

---

## DRY Helpers (Phase 2)

### New Functions

| Function | Location | Replaces |
|----------|----------|----------|
| `require_selected_project(request)` | `dependencies.py` | 5 inline checks in chat.py, workflow.py, tasks.py, chores.py |
| `cached_fetch(cache, key, fetch_fn, refresh=False)` | `utils.py` | 4 inline cache patterns in projects.py, board.py, chat.py |
| `case_insensitive_get(obj, key)` | `frontend/src/lib/case-utils.ts` | 5 inline `Object.keys().find()` in useAgentConfig.ts |
| `msToReadable(ms)`, `daysToMs(d)` | `frontend/src/lib/time-utils.ts` | Inline calculations in FeaturedRitualsPanel.tsx, ChoreCard.tsx |

---

## Entity Relationship Summary

```
GitHubBaseClient
  ├── GitHubIssuesService
  ├── GitHubPullRequestService
  ├── GitHubBranchService
  └── GitHubProjectBoardService
  └── has-a → RateLimitManager

AgentStepState (enum)
  └── used-by → recovery.py, agent_output.py, pipeline.py

CommentScanResult (dataclass)
  └── used-by → agent_output.py helpers

AgentResolution (dataclass)
  └── used-by → orchestrator.py helpers

PollStep (dataclass)
  └── used-by → polling_loop.py step list

ChatMessage storage (SQLite)
  └── replaces → _messages dict in chat.py
```
