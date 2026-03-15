# Data Model: Codebase Improvement Plan — Modern Best Practices Overhaul

**Feature**: `035-best-practices-overhaul` | **Date**: 2026-03-11 | **Plan**: [plan.md](plan.md)

## Entity Definitions

### Pipeline State (Phase 1 — New Persistence)

**Table**: `pipeline_states` (migration: `021_pipeline_state.sql`)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `issue_number` | INTEGER | PRIMARY KEY | GitHub issue number |
| `project_id` | TEXT | NOT NULL | GitHub Project node ID |
| `status` | TEXT | NOT NULL | Current pipeline status (e.g., "Ready", "In Progress") |
| `agent_name` | TEXT | | Currently assigned agent name |
| `agent_instance_id` | TEXT | | Unique instance ID for the assigned agent |
| `pr_number` | INTEGER | | Associated pull request number |
| `pr_url` | TEXT | | Associated pull request URL |
| `sub_issues` | TEXT | | JSON-encoded dict: `{agent_name: {number, node_id, url}}` |
| `metadata` | TEXT | | JSON-encoded additional state |
| `created_at` | TEXT | NOT NULL, DEFAULT NOW | ISO 8601 creation timestamp |
| `updated_at` | TEXT | NOT NULL, DEFAULT NOW | ISO 8601 last-update timestamp |

**Relationships**:
- Belongs to a project (via `project_id`)
- References a GitHub issue (via `issue_number`)
- May reference a pull request (via `pr_number`)
- Has sub-issues (encoded in `sub_issues` JSON field)

**State Transitions**:
- Created when an issue enters the pipeline
- Updated on every status change, agent assignment, or PR association
- Deleted when an issue exits the pipeline (completed/cancelled)
- Survives container restarts via SQLite persistence

**Validation Rules**:
- `issue_number` must be positive integer
- `status` must be a recognized pipeline status string
- `sub_issues` must be valid JSON when present
- `updated_at` must be ≥ `created_at`

---

### Issue Main Branch (Phase 1 — New Persistence)

**Table**: `issue_main_branches` (migration: `021_pipeline_state.sql`)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `issue_number` | INTEGER | PRIMARY KEY | GitHub issue number |
| `branch` | TEXT | NOT NULL | Main PR branch name |
| `pr_number` | INTEGER | NOT NULL | PR number that established this branch |
| `created_at` | TEXT | NOT NULL, DEFAULT NOW | ISO 8601 timestamp |

**Relationships**:
- One-to-one with pipeline state (same `issue_number`)
- References a GitHub pull request

**Validation Rules**:
- `branch` must be non-empty string
- `pr_number` must be positive integer

---

### Issue Sub-Issue Map (Phase 1 — New Persistence)

**Table**: `issue_sub_issue_map` (migration: `021_pipeline_state.sql`)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `issue_number` | INTEGER | NOT NULL | Parent issue number |
| `agent_name` | TEXT | NOT NULL | Agent that owns this sub-issue |
| `sub_issue_number` | INTEGER | NOT NULL | Sub-issue number |
| `sub_issue_node_id` | TEXT | NOT NULL | GitHub GraphQL node ID |
| `sub_issue_url` | TEXT | | Sub-issue URL |
| `created_at` | TEXT | NOT NULL, DEFAULT NOW | ISO 8601 timestamp |
| | | PRIMARY KEY (`issue_number`, `agent_name`) | Composite key |

**Relationships**:
- Many-to-one with parent issue (via `issue_number`)
- One-to-one with sub-issue (via `sub_issue_number`)

**Validation Rules**:
- `issue_number` and `sub_issue_number` must be positive integers
- `agent_name` must be non-empty string
- `sub_issue_node_id` must be non-empty string

---

### Agent Trigger Inflight (Phase 1 — New Persistence)

**Table**: `agent_trigger_inflight` (migration: `021_pipeline_state.sql`)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `trigger_key` | TEXT | PRIMARY KEY | Format: `"issue:status:agent"` |
| `started_at` | TEXT | NOT NULL | ISO 8601 timestamp of trigger start |

**Relationships**:
- References an issue, status, and agent (encoded in key)

**State Transitions**:
- Created when a trigger begins
- Deleted when trigger completes or is stale (>120s per `AGENT_TRIGGER_STALE_SECONDS`)

**Validation Rules**:
- `trigger_key` must match format `"{int}:{string}:{string}"`
- `started_at` must be valid ISO 8601

---

### Chat Message (Phase 1 — Existing Migration 012)

**Table**: `chat_messages` (migration: `012_chat_persistence.sql` — already exists)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `message_id` | TEXT | PRIMARY KEY | Unique message identifier |
| `session_id` | TEXT | NOT NULL, INDEXED | User session ID |
| `sender_type` | TEXT | NOT NULL, CHECK IN ('user','assistant','system') | Message sender type |
| `content` | TEXT | NOT NULL | Message content |
| `action_type` | TEXT | | Optional action type |
| `action_data` | TEXT | | Optional action payload (JSON) |
| `timestamp` | TEXT | NOT NULL, DEFAULT NOW | ISO 8601 timestamp |

**Relationships**:
- Belongs to a session (via `session_id`)
- Ordered by `timestamp` within a session

---

### Chat Proposal (Phase 1 — Existing Migration 012)

**Table**: `chat_proposals` (migration: `012_chat_persistence.sql` — already exists)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `proposal_id` | TEXT | PRIMARY KEY | Unique proposal identifier |
| `session_id` | TEXT | NOT NULL, INDEXED | User session ID |
| `original_input` | TEXT | NOT NULL | User's original input |
| `proposed_title` | TEXT | NOT NULL | AI-proposed issue title |
| `proposed_description` | TEXT | NOT NULL | AI-proposed issue description |
| `status` | TEXT | NOT NULL, DEFAULT 'pending', CHECK IN ('pending','confirmed','edited','cancelled') | Proposal lifecycle status |
| `edited_title` | TEXT | | User-edited title (if status='edited') |
| `edited_description` | TEXT | | User-edited description (if status='edited') |
| `created_at` | TEXT | NOT NULL, DEFAULT NOW | ISO 8601 creation timestamp |
| `expires_at` | TEXT | | Optional expiration timestamp |

**State Transitions**:
- `pending` → `confirmed` (user accepts as-is)
- `pending` → `edited` (user modifies and accepts)
- `pending` → `cancelled` (user rejects)

---

### Chat Recommendation (Phase 1 — Existing Migration 012)

**Table**: `chat_recommendations` (migration: `012_chat_persistence.sql` — already exists)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `recommendation_id` | TEXT | PRIMARY KEY | Unique recommendation identifier |
| `session_id` | TEXT | NOT NULL, INDEXED | User session ID |
| `data` | TEXT | NOT NULL | JSON-encoded recommendation data |
| `status` | TEXT | NOT NULL, DEFAULT 'pending', CHECK IN ('pending','accepted','rejected') | Recommendation status |
| `created_at` | TEXT | NOT NULL, DEFAULT NOW | ISO 8601 creation timestamp |

**State Transitions**:
- `pending` → `accepted`
- `pending` → `rejected`

---

### Shared Protocol Interfaces (Phase 4 — New Module)

**File**: `backend/src/interfaces.py`

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class GitHubClientFactoryProtocol(Protocol):
    """Protocol for creating authenticated GitHub API clients."""
    def create_client(self, access_token: str) -> Any: ...

@runtime_checkable
class GitHubProjectsServiceProtocol(Protocol):
    """Protocol for GitHub Projects API operations."""
    async def get_project_repository(self, access_token: str, project_id: str) -> tuple[str, str] | None: ...
    async def get_project_items(self, access_token: str, project_id: str, **kwargs: Any) -> Any: ...

@runtime_checkable
class SessionDependencyProtocol(Protocol):
    """Protocol for session dependency injection."""
    async def __call__(self, request: Any) -> Any: ...
```

**Rationale**: These protocols break the circular import chains between `dependencies.py` ↔ `api/auth.py` and `github_projects/service.py` ↔ `github_projects/__init__.py` by providing type-only contracts that both sides can import without runtime coupling.

---

### Pydantic Input Models (Phase 3 — New Models)

**File**: `backend/src/models/api_inputs.py`

```python
from pydantic import BaseModel, Field

class SettingsUpdate(BaseModel):
    """Typed model for settings update API input."""
    # Fields derived from current dict usage patterns
    ...

class WebhookPRData(BaseModel):
    """Typed model for pull request webhook payload."""
    number: int
    head: PRHead
    base: PRBase
    ...

class WebhookPayload(BaseModel):
    """Discriminated union for webhook event payloads."""
    action: str
    ...
```

**Validation Rules**:
- All fields have explicit types and optional `Field()` constraints
- Webhook payloads use discriminated unions on the `action` field
- FastAPI auto-validates and returns 422 on invalid input

---

## Entity Relationship Diagram

```text
┌───────────────────┐     ┌──────────────────────┐
│  pipeline_states  │────>│  issue_main_branches  │
│  (issue_number PK)│     │  (issue_number PK)    │
└───────┬───────────┘     └────────────────────────┘
        │ 1:N
        v
┌───────────────────────┐
│  issue_sub_issue_map  │
│  (issue_number,       │
│   agent_name PK)      │
└───────────────────────┘

┌───────────────────────┐
│ agent_trigger_inflight│     (independent — guard table)
│ (trigger_key PK)      │
└───────────────────────┘

┌─────────────────┐  1:N  ┌─────────────────┐  1:N  ┌──────────────────────┐
│  user_sessions  │──────>│  chat_messages   │       │  chat_proposals      │
│  (session_id PK)│──────>│  (message_id PK) │       │  (proposal_id PK)    │
│                 │──────>└─────────────────┘       └──────────────────────┘
│                 │  1:N  ┌──────────────────────┐
│                 │──────>│  chat_recommendations │
│                 │       │  (recommendation_id)  │
└─────────────────┘       └──────────────────────┘
```

## Cache Architecture

```text
┌─────────────┐    read     ┌──────────────────┐
│  API/Service │◄───────────│  BoundedDict L1  │
│   Layer      │            │  (maxlen=500)    │
└──────┬───────┘            └────────┬─────────┘
       │ write                       │ miss / write-through
       v                            v
┌──────────────────────────────────────────────┐
│            SQLite (aiosqlite)                │
│  pipeline_states | issue_main_branches | ... │
└──────────────────────────────────────────────┘

Read path:  L1 hit → return immediately
            L1 miss → query SQLite → populate L1 → return
Write path: Write to L1 + SQLite atomically (under asyncio.Lock)
Startup:    Load all active rows from SQLite → populate L1
```
