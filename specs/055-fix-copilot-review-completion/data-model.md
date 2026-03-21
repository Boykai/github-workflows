# Data Model: Fix Premature Copilot Review Completion in Agent Pipeline

**Feature**: `055-fix-copilot-review-completion` | **Date**: 2026-03-21

## Entities

### PipelineState (existing — no changes)

Represents the sequential execution plan for an issue. Used by guards to determine whether copilot-review is the current active agent.

| Field | Type | Description |
|-------|------|-------------|
| `issue_number` | `int` | GitHub issue number (pipeline key) |
| `project_id` | `str` | GitHub Project V2 node ID |
| `status` | `str` | Current pipeline status (e.g., "In Progress", "In Review") |
| `agents` | `list[str]` | Ordered list of agent slugs for the current status |
| `current_agent_index` | `int` | Index of the currently active agent |
| `current_agent` | `str \| None` | Name of the currently active agent (derived from index) |
| `completed_agents` | `list[str]` | Agents that have completed in the current status |
| `is_complete` | `bool` | Whether all agents for the current status are done |
| `groups` | `list[AgentGroup] \| None` | Optional parallel agent groups |
| `current_group_index` | `int` | Index of the current group (for parallel execution) |
| `agent_sub_issues` | `dict[str, dict] \| None` | Mapping of agent name → sub-issue metadata |

**Source**: `solune/backend/src/services/copilot_polling/__init__.py` (PipelineState dataclass)

**Guard usage**: `pipeline.current_agent == "copilot-review"` is the primary check in all new guards.

### CopilotReviewRequest (new — SQLite table)

Persists the timestamp of when Solune explicitly requested a Copilot code review. Survives server restarts.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `issue_number` | `INTEGER` | PRIMARY KEY | Parent GitHub issue number |
| `requested_at` | `TEXT` | NOT NULL | ISO 8601 UTC timestamp of when review was requested |
| `project_id` | `TEXT` | — | GitHub Project V2 node ID (for debugging/multi-project) |

**Source**: New migration `solune/backend/src/migrations/033_copilot_review_requests.sql`

**Write path**: `_record_copilot_review_request_timestamp()` in `helpers.py` → `INSERT OR REPLACE INTO copilot_review_requests`
**Read path**: `_check_copilot_review_done()` in `helpers.py` → `SELECT requested_at FROM copilot_review_requests WHERE issue_number = ?`

### _copilot_review_requested_at (existing — in-memory, no changes)

In-memory cache of review-request timestamps for fast access during normal operation.

| Field | Type | Description |
|-------|------|-------------|
| key | `int` | Parent issue number |
| value | `datetime` | UTC timestamp of review request |

**Source**: `solune/backend/src/services/copilot_polling/state.py` (line 101)
**Max entries**: 200 (BoundedDict)
**Cleared on**: Server restart

### _copilot_review_first_detected (existing — in-memory, no changes)

Tracks first detection of a Copilot review for confirmation-delay enforcement (two consecutive poll cycles).

| Field | Type | Description |
|-------|------|-------------|
| key | `int` | Issue number |
| value | `datetime` | First detection timestamp |

**Source**: `solune/backend/src/services/copilot_polling/state.py` (line 80)
**Max entries**: 200 (BoundedDict)
**Confirmation delay**: 30 seconds (`COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS`)

## Relationships

```text
PipelineState (in-memory)
  ├── current_agent: str           ← Used by all guards
  ├── status: str                  ← Used by webhook/poller guards
  └── is_complete: bool            ← Used to skip guard for completed pipelines

CopilotReviewRequest (SQLite)
  └── issue_number → PipelineState.issue_number  (logical, not FK)

_copilot_review_requested_at (in-memory)
  └── mirrors CopilotReviewRequest.requested_at for fast access
```

## State Transitions

### Guard Decision Flow

```text
_check_copilot_review_done(pipeline) called
  │
  ├── pipeline provided AND pipeline.current_agent != "copilot-review"
  │     → return False (short-circuit, no API calls)
  │
  ├── pipeline is None (no context)
  │     → proceed with existing logic (backward compat)
  │
  └── pipeline.current_agent == "copilot-review"
        → proceed with existing completion-detection logic
```

### Webhook Guard Decision Flow

```text
update_issue_status_for_copilot_pr() called
  │
  ├── No pipeline cached for issue_number
  │     → proceed with status move (backward compat)
  │
  ├── Pipeline exists AND pipeline.current_agent == "copilot-review"
  │     → proceed with status move (correct timing)
  │
  └── Pipeline exists AND pipeline.current_agent != "copilot-review"
        → skip status move, log warning, return "skipped"
```

### Timestamp Recovery Chain

```text
_check_copilot_review_done() needs request_ts
  │
  ├── _copilot_review_requested_at.get(issue_number)  → found → use it
  │
  ├── SELECT FROM copilot_review_requests              → found → cache + use
  │
  ├── _extract_copilot_review_requested_at(issue_body) → found → cache + use
  │
  └── marker_request_ts from Done! comment             → found → cache + use
       (existing fallback chain preserved)
```
