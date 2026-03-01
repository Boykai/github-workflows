# Human Agent Events & API Contract

**Feature**: 014-human-agent-pipeline | **Date**: 2026-02-28

## Overview

The Human agent type does not introduce new REST API endpoints. It hooks into existing endpoints and event flows. This contract documents the behavioral extensions to existing APIs and the event detection patterns.

## 1. Agent Listing — Existing Endpoint Extended

### `GET /api/v1/workflow/agents`

**Change**: The Human agent is automatically included in the response as a builtin agent.

**Response** (excerpt showing new entry):

```json
{
  "agents": [
    {
      "slug": "human",
      "display_name": "Human",
      "description": "Manual human task — creates a sub-issue assigned to the issue creator",
      "avatar_url": null,
      "source": "builtin"
    }
  ]
}
```

**No endpoint code changes required** — the `list_available_agents()` service already returns all builtin agents from `AGENT_DISPLAY_NAMES`.

## 2. Workflow Configuration — Existing Endpoint Extended

### `POST /api/v1/workflow/config`

**Change**: The `"human"` slug is now a valid value in agent assignment mappings.

**Request** (excerpt):

```json
{
  "agent_mappings": {
    "In Progress": [
      { "slug": "human", "display_name": "Human" }
    ]
  }
}
```

**Validation**: No changes needed. The existing configuration endpoint accepts any valid `AgentAssignment` with a `slug` string.

## 3. Sub-Issue Creation — Behavioral Change

### Existing Flow: `WorkflowOrchestrator.create_all_sub_issues()`

**Change**: When creating a sub-issue for an agent with slug `"human"`:

1. Resolve parent issue creator: `issue.user.login`
2. Create sub-issue with same mechanism as automated agents
3. Assign sub-issue to issue creator (instead of Copilot bot)
4. If creator cannot be resolved: create unassigned sub-issue + post warning comment

**Sub-Issue Title Format**: `[human] {parent_issue_title}`

**Sub-Issue Body** (example):

```markdown
## 🤖 Agent Task: `human`

This is a manual human task. Complete the work described below, then close this issue or comment 'Done!' on the parent issue to continue the pipeline.

---

## Parent Issue Context

{parent_issue_body_excerpt}

---
*Sub-issue created for agent `human` — see parent issue #{parent_number} for full context*
```

**Sub-Issue Assignment**:

| Scenario | Assignee | Additional Action |
|----------|----------|-------------------|
| Creator resolved | `issue.user.login` | None |
| Creator unresolved | *(unassigned)* | Warning comment on parent issue: `⚠️ Could not resolve issue creator for Human step assignment. Please manually assign the sub-issue.` |

## 4. Completion Detection — Behavioral Change

### Signal 1: Sub Issue State Change (NEW)

**Detection**: On each polling cycle, for the active Human agent step, check the sub-issue's state via GitHub API.

```
GET /repos/{owner}/{repo}/issues/{sub_issue_number}
→ response.state == "closed"
```

**Trigger condition**: `sub_issue.state == "closed"`

**Pipeline action**: Call `_advance_pipeline()` to mark Human step as Done and continue.

### Signal 2: 'Done!' Comment on Parent Issue (EXTENDED)

**Detection**: Extend the existing comment-checking logic to support Human agent completion.

**Current pattern** (automated agents):
```
^(.+?):\s*Done!\s*$    →  e.g., "speckit.specify: Done!"
```

**New pattern** (Human agent only):
```
^Done!$                 →  exact match, no agent prefix
```

**Authorization check** (Human agent only):
- Comment author must match the Human sub-issue's assignee
- If comment author ≠ assignee → ignore (do not trigger completion)

**Pipeline action**: Same as Signal 1 — call `_advance_pipeline()`.

### Idempotency

Both signals may fire in the same or consecutive polling cycles. The pipeline must advance only once.

**Mechanism**: Before advancing, check `pipeline.current_agent == "human"`. If the pipeline has already advanced past the Human step (index incremented), the second signal is a no-op.

## 5. Agent Assignment — Behavioral Change

### Existing Flow: `WorkflowOrchestrator.assign_agent_for_status()`

**Change**: When the active agent slug is `"human"`:

1. **Skip** Copilot workspace assignment (no PR creation needed)
2. **Skip** Copilot bot assignment on the sub-issue
3. **Mark** the Human step as 🔄 Active in the tracking table
4. The sub-issue is already assigned to the issue creator (done during creation in step 3 above)

**No GitHub Copilot API calls** are made for Human steps.

## 6. WebSocket Notifications — Existing Events Extended

### `agent_assigned` Event

**Change**: Emitted when a Human step becomes active.

```json
{
  "type": "agent_assigned",
  "agent_name": "human",
  "issue_number": 123,
  "project_id": "PVT_xxx"
}
```

### `agent_completed` Event

**Change**: Emitted when a Human step is marked as complete.

```json
{
  "type": "agent_completed",
  "agent_name": "human",
  "issue_number": 123,
  "project_id": "PVT_xxx"
}
```

**No changes to WebSocket event schema** — the existing event structure already supports any agent name string.

## 7. Error Scenarios

| Error | HTTP Status / Behavior | Response / Action |
|-------|----------------------|-------------------|
| Human agent added to pipeline but no issue triggered | N/A | Human step sits in pipeline config; no sub-issue created until pipeline runs |
| Issue creator account deleted | N/A (sub-issue creation) | Sub-issue created unassigned + warning comment posted |
| Sub-issue deleted while pipeline active | N/A (polling) | Warning logged; 'Done!' comment path remains available |
| Non-assigned user comments 'Done!' | N/A (polling) | Comment ignored; pipeline does not advance |
| 'Done!' with wrong casing/whitespace | N/A (polling) | Comment ignored; only exact `Done!` accepted |
| Both completion signals simultaneous | N/A (polling) | Pipeline advances once (idempotent) |
