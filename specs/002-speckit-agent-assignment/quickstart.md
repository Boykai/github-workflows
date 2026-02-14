# Quickstart: Spec Kit Custom Agent Assignment by Status

**Feature**: 002-speckit-agent-assignment  
**Date**: 2026-02-13

## Overview

This feature replaces the single Copilot custom agent assignment with a per-status agent mapping that orchestrates Spec Kit agents across the full issue lifecycle:

| Status | Agent(s) | Completion Signal |
|--------|----------|-------------------|
| Backlog | `speckit.specify` | Comment: `speckit.specify: All done!>` |
| Ready | `speckit.plan` → `speckit.tasks` | Comments: `speckit.plan: All done!>`, `speckit.tasks: All done!>` |
| In Progress | `speckit.implement` | PR un-drafted (existing) |
| In Review | *(no agent — reviewer assigned)* | — |

## Prerequisites

1. **Spec Kit installed** in the target repository (`specify init` completed)
2. **GitHub Copilot** with custom agent support enabled
3. **Backend running** at `http://localhost:8000`
4. **Frontend running** at `http://localhost:5173`

## Configuration

### Default Agent Mappings

The system ships with default mappings that match the Spec Kit workflow:

```json
{
  "agent_mappings": {
    "Backlog": ["speckit.specify"],
    "Ready": ["speckit.plan", "speckit.tasks"],
    "In Progress": ["speckit.implement"]
  }
}
```

### Customizing Agent Mappings

Update via the workflow config API:

```bash
curl -X PUT http://localhost:8000/api/v1/workflow/config \
  -H "Content-Type: application/json" \
  -d '{
    "agent_mappings": {
      "Backlog": ["speckit.specify"],
      "Ready": ["speckit.plan", "speckit.tasks"],
      "In Progress": ["speckit.implement"]
    }
  }'
```

To clear agents for a status (fall back to configured assignee):

```bash
curl -X PUT http://localhost:8000/api/v1/workflow/config \
  -H "Content-Type: application/json" \
  -d '{
    "agent_mappings": {
      "Backlog": [],
      "Ready": ["speckit.plan", "speckit.tasks"],
      "In Progress": ["speckit.implement"]
    }
  }'
```

## End-to-End Workflow

### 1. Issue Creation (User Action)

User confirms an AI-generated issue recommendation in the chat interface.

**What happens**:
- GitHub Issue is created
- Issue is added to the project in **Backlog** status
- `speckit.specify` agent is assigned to the issue
- User receives a real-time notification: *"speckit.specify assigned to issue #42"*

### 2. Specification Phase (Automatic)

The `speckit.specify` agent works on the issue, posting specification artifacts as comments.

**What happens when complete**:
- Agent posts `speckit.specify: All done!>` comment
- Polling service detects the completion marker
- Issue auto-transitions to **Ready** status
- `speckit.plan` agent is assigned
- User receives notification: *"speckit.specify completed, speckit.plan assigned"*

### 3. Planning Phase (Automatic)

The `speckit.plan` agent generates an implementation plan.

**What happens when complete**:
- Agent posts `speckit.plan: All done!>` comment
- Polling service detects the marker
- `speckit.tasks` agent is assigned (issue stays in **Ready**)
- User receives notification: *"speckit.plan completed, speckit.tasks assigned"*

### 4. Task Breakdown Phase (Automatic)

The `speckit.tasks` agent breaks the plan into actionable tasks.

**What happens when complete**:
- Agent posts `speckit.tasks: All done!>` comment
- Polling service detects the marker
- Issue transitions to **In Progress** status
- `speckit.implement` agent is assigned
- User receives notification: *"speckit.tasks completed, speckit.implement assigned"*

### 5. Implementation Phase (Automatic)

The `speckit.implement` agent writes code and creates a PR.

**What happens when complete**:
- Agent creates/un-drafts a PR linked to the issue
- Polling service detects the PR (existing mechanism)
- Issue transitions to **In Review** status
- Project owner is assigned as reviewer

## Monitoring

### Check Pipeline States

View all active pipelines:

```bash
curl http://localhost:8000/api/v1/workflow/pipeline-states
```

Check a specific issue:

```bash
curl http://localhost:8000/api/v1/workflow/pipeline-states/42
```

### Manual Completion Check

Trigger a single-issue check:

```bash
curl -X POST http://localhost:8000/api/v1/workflow/polling/check-issue/42
```

Trigger a full poll cycle:

```bash
curl -X POST http://localhost:8000/api/v1/workflow/polling/check-all
```

### Polling Status

```bash
curl http://localhost:8000/api/v1/workflow/polling/status
```

## Error Handling

| Scenario | System Behavior |
|----------|-----------------|
| Agent assignment fails | Error logged, user notified, issue stays in current status |
| Completion marker not found | Polling retries on next cycle (configurable interval) |
| Pipeline agent fails mid-sequence | Issue stays in status, user notified for manual intervention |
| System restart | Pipeline state reconstructed from issue comments |
| Invalid agent name | Warning logged, falls back to `copilot_assignee` if configured |

## Key Files Modified

| File | Change |
|------|--------|
| `backend/src/models/chat.py` | Replace `custom_agent` with `agent_mappings` on `WorkflowConfiguration` |
| `backend/src/services/workflow_orchestrator.py` | Refactor to stop at Backlog, add pipeline state tracking |
| `backend/src/services/copilot_polling.py` | Extend to poll Backlog/Ready for comment-based completion |
| `backend/src/services/github_projects.py` | Add `check_agent_completion_comment()` method |
| `backend/src/api/workflow.py` | Add pipeline state endpoints, update config endpoints |
| `frontend/src/types/index.ts` | Update `WorkflowConfiguration` type with `agent_mappings` |
