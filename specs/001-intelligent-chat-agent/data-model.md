# Data Model: Intelligent Chat Agent (Microsoft Agent Framework)

**Feature**: 001-intelligent-chat-agent | **Date**: 2026-04-07

## Overview

This document defines the entities, relationships, and state transitions for the intelligent chat agent feature. The core design principle is **preservation**: the existing `ChatMessage`, `AITaskProposal`, and `IssueRecommendation` models remain unchanged. New entities are internal to the agent layer and do not surface in the REST API.

---

## Entities

### 1. ChatMessage (UNCHANGED)

**Location**: `src/models/chat.py`
**Status**: No changes — API contract preserved (FR-007)

| Field | Type | Description |
|-------|------|-------------|
| message_id | UUID | Unique message identifier (auto-generated) |
| session_id | UUID | Parent session ID (FK) |
| sender_type | SenderType (enum) | "user", "assistant", "system" |
| content | str (max 100,000) | Message text content |
| action_type | ActionType \| None | "task_create", "status_update", "project_select", "issue_create" |
| action_data | dict \| None | Action-specific payload (proposal details, status change, etc.) |
| timestamp | datetime | Message timestamp (UTC) |

**Validation rules**: `content` max length 100,000 chars. `action_type` must be a valid `ActionType` enum value if present.

---

### 2. AITaskProposal (UNCHANGED)

**Location**: `src/models/recommendation.py`
**Status**: No changes — tools return structured dicts that populate the same model

| Field | Type | Description |
|-------|------|-------------|
| proposal_id | UUID | Unique proposal identifier |
| session_id | UUID | Parent session ID |
| original_input | str | User's original message |
| proposed_title | str (max 256) | AI-generated task title |
| proposed_description | str (max 65,536) | AI-generated task description |
| status | ProposalStatus | "pending", "confirmed", "edited", "cancelled" |
| edited_title | str \| None | User-modified title |
| edited_description | str \| None | User-modified description |
| created_at | datetime | Proposal creation time |
| expires_at | datetime | Auto-expiration (10 min default) |
| pipeline_name | str \| None | Applied agent pipeline name |
| pipeline_source | str \| None | Pipeline resolution source |
| selected_pipeline_id | str \| None | Saved pipeline ID |
| file_urls | list[str] | Attached file URLs |

**State transitions**: `pending` → `confirmed` | `edited` | `cancelled`

---

### 3. IssueRecommendation (UNCHANGED)

**Location**: `src/models/recommendation.py`
**Status**: No changes — `create_issue_recommendation` tool returns same structure

| Field | Type | Description |
|-------|------|-------------|
| recommendation_id | UUID | Unique identifier |
| session_id | UUID | Parent session ID |
| title | str | Recommended issue title |
| body | str | Recommended issue body (markdown) |
| labels | list[IssueLabel] | Suggested labels |
| priority | IssuePriority | "low", "medium", "high", "critical" |
| size | IssueSize | "xs", "s", "m", "l", "xl" |
| status | RecommendationStatus | "pending", "confirmed", "rejected" |
| metadata | IssueMetadata | Additional metadata |
| created_at | datetime | Creation time |
| expires_at | datetime | Auto-expiration |

**State transitions**: `pending` → `confirmed` | `rejected`

---

### 4. AgentSessionState (NEW — internal)

**Location**: `src/services/chat_agent.py` (in-memory, not persisted to SQLite)
**Status**: New internal entity — manages Agent Framework session lifecycle

| Field | Type | Description |
|-------|------|-------------|
| session_id | UUID | Maps to Solune session_id |
| agent_session | AgentSession | Agent Framework session object |
| created_at | datetime | When the agent session was created |
| last_active | datetime | Last interaction timestamp |
| message_count | int | Number of messages processed (for context window management) |

**Relationships**: 1:1 with Solune UserSession. Created lazily on first agent interaction per session.

**Lifecycle**:
- Created: First `ChatAgentService.run()` call for a session_id
- Active: Updated on each subsequent `run()` call
- Evicted: When session expires or memory pressure triggers cleanup

**Context window management** (FR-019): When `message_count` exceeds a threshold (configurable, default 50), older messages in the AgentSession are summarized rather than carried verbatim. Solune's SQLite retains the full history.

---

### 5. AgentToolResult (NEW — internal)

**Location**: `src/services/agent_tools.py` (returned by tool functions)
**Status**: New internal entity — bridges tool output to ChatMessage

| Field | Type | Description |
|-------|------|-------------|
| action_type | ActionType \| None | Maps to ChatMessage.action_type |
| action_data | dict \| None | Maps to ChatMessage.action_data |
| content | str | Human-readable response text |
| requires_confirmation | bool | Whether the result needs user confirm/reject |

**Conversion flow**: Tool function → `AgentToolResult` → `ChatAgentService` converts to `ChatMessage` with appropriate `action_type` and `action_data`.

---

### 6. AgentProviderConfig (NEW — internal)

**Location**: `src/services/agent_provider.py`
**Status**: New internal entity — encapsulates provider-specific configuration

| Field | Type | Description |
|-------|------|-------------|
| provider_type | str | "copilot" or "azure_openai" |
| model_name | str | Model identifier (e.g., "gpt-4o", "gpt-4") |
| tools | list[AIFunction] | Registered tool functions |
| instructions | str | System instructions (from agent_instructions.py) |
| middleware | list[AgentMiddleware] | Middleware chain (logging, security) |

**Not a Pydantic model** — this is a configuration object used internally by the factory to construct an Agent instance.

---

## Relationships

```text
UserSession (existing)
  └── 1:1 ── AgentSessionState (new, in-memory)
                └── contains AgentSession (Agent Framework)

ChatMessage (existing, unchanged)
  ├── may reference AITaskProposal (via action_data.proposal_id)
  └── may reference IssueRecommendation (via action_data.recommendation_id)

Agent (Agent Framework)
  ├── has many AIFunction (tools)
  ├── has one instruction set
  └── has many AgentMiddleware

AgentToolResult (new, transient)
  └── converted to ChatMessage by ChatAgentService
```

---

## State Transitions

### Agent Interaction Flow

```text
User Message
  │
  ▼
ChatAgentService.run()
  │
  ├─► Look up / create AgentSessionState
  │
  ├─► SecurityMiddleware.process()
  │     ├─ PASS → continue
  │     └─ BLOCK → return safe fallback ChatMessage
  │
  ├─► Agent.run(message, session, tools, context)
  │     │
  │     ├─► Agent reasons about intent
  │     │     ├─ Ambiguous → ask_clarifying_question tool
  │     │     ├─ Task creation → create_task_proposal tool
  │     │     ├─ Feature request → create_issue_recommendation tool
  │     │     ├─ Status change → update_task_status tool
  │     │     ├─ Transcript → analyze_transcript tool
  │     │     └─ Conversational → no tool (text response)
  │     │
  │     └─► AgentResponse (messages + tool results)
  │
  ├─► LoggingMiddleware.process() — emit timing, tokens, tool name
  │
  ├─► Convert AgentResponse → ChatMessage (preserve action_type/action_data)
  │
  └─► Persist to SQLite via chat_store.py
```

### Proposal Confirm/Reject Flow (UNCHANGED)

```text
ChatMessage (action_type=task_create, action_data={proposal_id})
  │
  ├─► User clicks "Confirm" → POST /chat/proposals/{id}/confirm
  │     └─► Creates GitHub issue, updates proposal status → "confirmed"
  │
  └─► User clicks "Reject" → DELETE /chat/proposals/{id}
        └─► Updates proposal status → "cancelled"
```

---

## Validation Rules

| Entity | Rule | Source |
|--------|------|--------|
| ChatMessage.content | Max 100,000 characters | Existing Pydantic validation |
| Tool: create_task_proposal.title | Max 256 characters | Existing AITaskProposal.proposed_title constraint |
| Tool: create_task_proposal.description | Max 65,536 characters | Existing AITaskProposal.proposed_description constraint |
| Tool: update_task_status.target_status | Must be one of the project's configured status columns | Validated at runtime via injected context |
| Tool: create_issue_recommendation.priority | Must be valid IssuePriority enum value | Validated by Pydantic |
| Tool: create_issue_recommendation.size | Must be valid IssueSize enum value | Validated by Pydantic |
| SecurityMiddleware | Rejects messages matching prompt injection patterns | FR-014 |
| AgentSessionState.message_count | Triggers summarization at threshold (default 50) | FR-019 |
