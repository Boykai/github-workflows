# Data Model: Intelligent Chat Agent (Microsoft Agent Framework)

**Feature Branch**: `001-intelligent-chat-agent`  
**Date**: 2026-04-07  
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

## Entity Inventory

### Existing Entities (UNCHANGED)

These entities are defined in the current codebase and remain unmodified. The agent integration consumes and produces them without schema changes.

#### ChatMessage

**Location**: `solune/backend/src/models/chat.py`

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | `UUID` | Unique message identifier |
| `session_id` | `UUID` | Session this message belongs to |
| `sender_type` | `SenderType` (user / assistant / system) | Who sent the message |
| `content` | `str` (max 100,000) | Message text content |
| `action_type` | `ActionType \| None` | Optional action classification |
| `action_data` | `dict[str, Any] \| None` | Action-specific payload |
| `timestamp` | `datetime` | When message was created |

**Relationships**: Belongs to a session (via `session_id`). References proposals/recommendations via `action_data`.

#### AITaskProposal

**Location**: `solune/backend/src/models/recommendation.py`

| Field | Type | Description |
|-------|------|-------------|
| `proposal_id` | `UUID` | Unique proposal identifier |
| `session_id` | `UUID` | Session this proposal belongs to |
| `original_input` | `str` | User's raw input |
| `proposed_title` | `str` | AI-generated task title |
| `proposed_description` | `str` | AI-generated task description |
| `status` | `ProposalStatus` | pending / confirmed / edited / cancelled |
| `edited_title` | `str \| None` | User-edited title |
| `edited_description` | `str \| None` | User-edited description |
| `created_at` | `datetime` | Creation timestamp |
| `expires_at` | `datetime` | Auto-expiry (10 minutes) |
| `selected_pipeline_id` | `str \| None` | Pipeline for the task |
| `file_urls` | `list[str]` | Attached file URLs |

**Computed**: `final_title` (edited or proposed), `final_description` (edited or proposed).

#### IssueRecommendation

**Location**: `solune/backend/src/models/recommendation.py`

| Field | Type | Description |
|-------|------|-------------|
| `recommendation_id` | `UUID` | Unique recommendation identifier |
| `session_id` | `UUID` | Session this recommendation belongs to |
| `original_input` | `str` | User's raw input |
| `original_context` | `str` | Preserved verbatim context |
| `title` | `str` | Issue title |
| `user_story` | `str` | User story format |
| `ui_ux_description` | `str` | Design guidance |
| `functional_requirements` | `list[str]` | MUST/SHOULD requirements |
| `technical_notes` | `str` | Implementation hints |
| `metadata` | `IssueMetadata` | Priority, size, labels, etc. |
| `status` | `RecommendationStatus` | pending / confirmed / rejected |
| `created_at` | `datetime` | Creation timestamp |
| `confirmed_at` | `datetime \| None` | When confirmed |
| `file_urls` | `list[str]` | Attached file URLs |

#### ActionType (enum)

| Value | Description |
|-------|-------------|
| `TASK_CREATE` | Task creation proposal |
| `STATUS_UPDATE` | Task status change |
| `ISSUE_CREATE` | GitHub issue creation |
| `PROJECT_SELECT` | Project selection change |

#### SenderType (enum)

| Value | Description |
|-------|-------------|
| `USER` | Human user message |
| `ASSISTANT` | AI agent response |
| `SYSTEM` | System notification |

---

### New Entities (CREATED)

These entities are introduced by the agent migration. They exist at the service layer and are not persisted in new database tables.

#### AgentSessionMapping

**Location**: `solune/backend/src/services/chat_agent.py` (in-memory)

| Field | Type | Description |
|-------|------|-------------|
| `solune_session_id` | `UUID` | Solune application session ID |
| `agent_session` | `AgentSession` | Agent Framework session instance |
| `created_at` | `datetime` | When the mapping was created |
| `last_accessed` | `datetime` | Last interaction timestamp |

**Relationships**: 1:1 with Solune session. Contains an `AgentSession` from the framework.

**Lifecycle**:
- Created on first `ChatAgentService.run()` call for a session
- Updated (`last_accessed`) on each interaction
- Evicted via LRU when pool exceeds `max_sessions` (default: 200)
- Context summary persisted to SQLite on eviction

#### ToolResult

**Location**: `solune/backend/src/services/agent_tools.py` (return type)

| Field | Type | Description |
|-------|------|-------------|
| `action_type` | `str` | One of ActionType values |
| `action_data` | `dict[str, Any]` | Tool-specific structured output |
| `message` | `str` | Human-readable response text |

**Relationships**: Produced by tool functions, consumed by `ChatAgentService` response converter.

**Validation rules**:
- `action_type` must be a valid `ActionType` value or `None` (for informational responses)
- `action_data` must conform to the schema expected by the frontend for the given action type

---

## State Transitions

### Proposal Lifecycle (UNCHANGED)

```
                    ┌────────────┐
                    │   PENDING  │ ← Agent creates proposal
                    └─────┬──────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌───────────┐
        │CONFIRMED │ │  EDITED  │ │ CANCELLED │
        └──────────┘ └────┬─────┘ └───────────┘
                          │
                          ▼
                    ┌──────────┐
                    │CONFIRMED │
                    └──────────┘
```

**Transitions**:
- PENDING → CONFIRMED: User approves proposal as-is
- PENDING → EDITED: User modifies proposal fields
- PENDING → CANCELLED: User rejects or proposal expires (10 min)
- EDITED → CONFIRMED: User approves edited proposal

### Recommendation Lifecycle (UNCHANGED)

```
        ┌──────────┐
        │ PENDING  │ ← Agent creates recommendation
        └────┬─────┘
             │
       ┌─────┼─────┐
       ▼           ▼
  ┌──────────┐ ┌──────────┐
  │CONFIRMED │ │ REJECTED │
  └──────────┘ └──────────┘
```

### Agent Session Lifecycle (NEW)

```
        ┌──────────┐
        │  EMPTY   │ ← Session created, no context
        └────┬─────┘
             │ first message
             ▼
        ┌──────────┐
        │  ACTIVE  │ ← Multi-turn conversation
        └────┬─────┘
             │ LRU eviction or session end
             ▼
        ┌──────────┐
        │ EVICTED  │ ← Summary persisted to SQLite
        └────┬─────┘
             │ next message for this session
             ▼
        ┌──────────┐
        │ RESTORED │ → ACTIVE (summary loaded, new AgentSession)
        └──────────┘
```

**Transitions**:
- EMPTY → ACTIVE: First user message triggers session creation
- ACTIVE → ACTIVE: Each message interaction
- ACTIVE → EVICTED: LRU cache eviction when pool is full
- EVICTED → RESTORED → ACTIVE: Next message for evicted session restores from SQLite summary

---

## Relationship Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ChatAgentService                              │
│  ┌──────────────────────┐    ┌───────────────────────────────┐      │
│  │ AgentSessionMapping  │    │  Agent (singleton)             │      │
│  │  session_id → session│    │  ├── tools: [7 @tool funcs]   │      │
│  │  (LRU cache, max 200)│    │  ├── instructions: str        │      │
│  └──────────┬───────────┘    │  ├── middleware: [Log, Sec]   │      │
│             │                 │  └── client: Provider          │      │
│             │ provides        │      ├── GitHubCopilotAgent   │      │
│             ▼                 │      └── AzureOpenAI Agent    │      │
│  ┌──────────────────────┐    └───────────────┬───────────────┘      │
│  │     AgentSession     │                     │                      │
│  │  (framework object)  │◄────────────────────┘ uses per-run        │
│  └──────────────────────┘                                            │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ produces
                       ▼
            ┌──────────────────┐
            │   ChatMessage    │ ← Existing model, unchanged
            │  action_type     │
            │  action_data ────┼──► AITaskProposal
            │                  │──► IssueRecommendation
            └──────────────────┘
```

---

## Tool Input/Output Schemas

### create_task_proposal

**Input** (LLM-visible):
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | `str` | Yes | Proposed task title |
| `description` | `str` | Yes | Proposed task description (markdown) |

**Context** (injected via `FunctionInvocationContext.kwargs`):
- `project_id: str`
- `session_id: str`
- `github_token: str`
- `pipeline_id: str | None`
- `file_urls: list[str]`

**Output**: `ToolResult` with `action_type="task_create"`, `action_data` containing `AITaskProposal` fields.

### create_issue_recommendation

**Input** (LLM-visible):
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | `str` | Yes | Issue title |
| `user_story` | `str` | Yes | User story format |
| `ui_ux_description` | `str` | No | Design guidance |
| `functional_requirements` | `list[str]` | Yes | Requirements list |
| `technical_notes` | `str` | No | Implementation hints |
| `priority` | `str` | No | P0–P3 |
| `size` | `str` | No | XS–XL |

**Context**: Same as `create_task_proposal`.

**Output**: `ToolResult` with `action_type="issue_create"`, `action_data` containing `IssueRecommendation` fields.

### update_task_status

**Input** (LLM-visible):
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_reference` | `str` | Yes | Task title or identifier |
| `target_status` | `str` | Yes | Target status column name |

**Context**: Same plus `available_tasks: list[dict]`, `available_statuses: list[str]`.

**Output**: `ToolResult` with `action_type="status_update"`, `action_data` containing matched task and new status.

### analyze_transcript

**Input** (LLM-visible):
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `transcript_content` | `str` | Yes | Full transcript text |

**Context**: Same as `create_task_proposal` plus `metadata_context: dict`.

**Output**: `ToolResult` with `action_type="issue_create"`, `action_data` containing `IssueRecommendation` derived from transcript.

### ask_clarifying_question

**Input** (LLM-visible):
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question` | `str` | Yes | The clarifying question to ask |

**Context**: None (informational only).

**Output**: `ToolResult` with `action_type=None`, `message` containing the question.

### get_project_context

**Input**: None (LLM-visible).

**Context**: `project_id: str`, `github_token: str`.

**Output**: `ToolResult` with `action_type=None`, `action_data` containing project name, labels, branches, milestones, collaborators.

### get_pipeline_list

**Input**: None (LLM-visible).

**Context**: `project_id: str`.

**Output**: `ToolResult` with `action_type=None`, `action_data` containing list of available pipelines.
