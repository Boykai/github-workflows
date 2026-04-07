# API Contract: Agent Tool Schemas

**Feature**: 001-intelligent-chat-agent | **Date**: 2026-04-07

## Overview

This document defines the JSON schemas for each agent tool function. These schemas represent the parameters that are **visible to the LLM** — the agent uses them to decide which tool to call and how to populate the arguments. Runtime context parameters (project_id, github_token, session_id, etc.) are injected via `FunctionInvocationContext.kwargs` and are **not** part of these schemas.

---

## Tool: create_task_proposal

**Purpose**: Creates a task proposal with AI-generated title and description for user confirmation.
**Maps to**: Existing `generate_task_from_description()` in `ai_agent.py`
**Triggers**: FR-001, FR-002, FR-017

### LLM-Visible Parameters

```json
{
  "name": "create_task_proposal",
  "description": "Create a task proposal for the user to confirm. Use when the user wants to create a new task, work item, or TODO.",
  "parameters": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string",
        "maxLength": 256,
        "description": "Concise, action-oriented task title starting with a verb (e.g., 'Fix login page validation')"
      },
      "description": {
        "type": "string",
        "maxLength": 65536,
        "description": "Detailed task description with markdown formatting including Overview, Technical Details, and Acceptance Criteria sections"
      }
    },
    "required": ["title", "description"]
  }
}
```

### Injected Context

| Parameter | Type | Source |
|-----------|------|--------|
| project_id | UUID | From session's selected project |
| session_id | UUID | From Solune session |
| pipeline_id | str \| None | From chat request |

### Return Schema

```json
{
  "action_type": "task_create",
  "action_data": {
    "proposal_id": "uuid",
    "proposed_title": "string",
    "proposed_description": "string",
    "status": "pending",
    "expires_at": "datetime"
  },
  "content": "I've created a task proposal: **{title}**. Please review and confirm or reject.",
  "requires_confirmation": true
}
```

---

## Tool: create_issue_recommendation

**Purpose**: Creates a GitHub issue recommendation from a feature request or user story.
**Maps to**: Existing `detect_feature_request_intent()` + `generate_issue_recommendation()` in `ai_agent.py`
**Triggers**: FR-001, FR-002, FR-017

### LLM-Visible Parameters

```json
{
  "name": "create_issue_recommendation",
  "description": "Create a GitHub issue recommendation from a feature request. Use when the user describes a feature idea, improvement, or bug report that should become a tracked issue.",
  "parameters": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string",
        "maxLength": 256,
        "description": "Issue title"
      },
      "user_story": {
        "type": "string",
        "description": "User story in 'As a [role], I want [capability] so that [benefit]' format"
      },
      "acceptance_criteria": {
        "type": "array",
        "items": { "type": "string" },
        "description": "List of acceptance criteria for the issue"
      },
      "labels": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Suggested labels (e.g., 'enhancement', 'bug', 'documentation')"
      },
      "priority": {
        "type": "string",
        "enum": ["low", "medium", "high", "critical"],
        "description": "Issue priority"
      },
      "size": {
        "type": "string",
        "enum": ["xs", "s", "m", "l", "xl"],
        "description": "Estimated issue size"
      }
    },
    "required": ["title", "user_story", "acceptance_criteria"]
  }
}
```

### Injected Context

| Parameter | Type | Source |
|-----------|------|--------|
| project_id | UUID | From session's selected project |
| github_token | str | From encrypted session store |
| pipeline_id | str \| None | From chat request |
| session_id | UUID | From Solune session |

### Return Schema

```json
{
  "action_type": "issue_create",
  "action_data": {
    "recommendation_id": "uuid",
    "title": "string",
    "body": "string (markdown)",
    "labels": ["string"],
    "priority": "string",
    "size": "string",
    "status": "pending"
  },
  "content": "I've prepared an issue recommendation: **{title}**. Please review and confirm or reject.",
  "requires_confirmation": true
}
```

---

## Tool: update_task_status

**Purpose**: Updates the status of an existing task (e.g., move to "In Progress", "Done").
**Maps to**: Existing `parse_status_change_request()` in `ai_agent.py`
**Triggers**: FR-001, FR-002

### LLM-Visible Parameters

```json
{
  "name": "update_task_status",
  "description": "Update the status of an existing task. Use when the user wants to move a task to a different status column (e.g., 'move task #15 to done').",
  "parameters": {
    "type": "object",
    "properties": {
      "task_reference": {
        "type": "string",
        "description": "Task identifier — can be a number (e.g., '#15'), title fragment, or description"
      },
      "target_status": {
        "type": "string",
        "description": "Target status column name (e.g., 'In Progress', 'Done', 'Todo')"
      }
    },
    "required": ["task_reference", "target_status"]
  }
}
```

### Injected Context

| Parameter | Type | Source |
|-----------|------|--------|
| project_id | UUID | From session's selected project |
| current_tasks | list[Task] | From project items cache |
| status_columns | list[str] | From project configuration |
| cached_projects | list[Project] | From user projects cache |

### Return Schema

```json
{
  "action_type": "status_update",
  "action_data": {
    "task_title": "string",
    "old_status": "string",
    "new_status": "string",
    "task_id": "string"
  },
  "content": "Updated **{task_title}** from {old_status} to {new_status}.",
  "requires_confirmation": false
}
```

---

## Tool: analyze_transcript

**Purpose**: Analyzes meeting transcript content and generates issue recommendations.
**Maps to**: Existing `analyze_transcript()` in `ai_agent.py`
**Triggers**: FR-002, FR-018

### LLM-Visible Parameters

```json
{
  "name": "analyze_transcript",
  "description": "Analyze meeting transcript content to extract action items and generate issue recommendations. Use when the user uploads or pastes transcript content.",
  "parameters": {
    "type": "object",
    "properties": {
      "transcript_content": {
        "type": "string",
        "description": "The transcript text content to analyze"
      }
    },
    "required": ["transcript_content"]
  }
}
```

### Injected Context

| Parameter | Type | Source |
|-----------|------|--------|
| project_id | UUID | From session's selected project |
| session_id | UUID | From Solune session |

### Return Schema

```json
{
  "action_type": "issue_create",
  "action_data": {
    "recommendation_id": "uuid",
    "title": "string",
    "body": "string (markdown with extracted action items)",
    "labels": ["meeting-notes"],
    "priority": "medium",
    "size": "m",
    "status": "pending"
  },
  "content": "I've analyzed the transcript and created an issue recommendation with the key action items.",
  "requires_confirmation": true
}
```

---

## Tool: ask_clarifying_question

**Purpose**: Asks the user a clarifying question when intent is ambiguous.
**Maps to**: New capability (FR-011)
**Triggers**: FR-011

### LLM-Visible Parameters

```json
{
  "name": "ask_clarifying_question",
  "description": "Ask the user a clarifying question when their request is ambiguous. Use this before taking action when you're unsure about the user's intent. Ask 2-3 focused questions.",
  "parameters": {
    "type": "object",
    "properties": {
      "question": {
        "type": "string",
        "description": "The clarifying question to ask the user"
      }
    },
    "required": ["question"]
  }
}
```

### Injected Context

None — this tool only produces text output.

### Return Schema

```json
{
  "action_type": null,
  "action_data": null,
  "content": "{question}",
  "requires_confirmation": false
}
```

---

## Tool: get_project_context

**Purpose**: Retrieves current project information for context-aware responses.
**Maps to**: New capability (FR-002)
**Triggers**: FR-002

### LLM-Visible Parameters

```json
{
  "name": "get_project_context",
  "description": "Get information about the user's current project including name, status columns, and recent tasks. Use to provide context-aware responses.",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

### Injected Context

| Parameter | Type | Source |
|-----------|------|--------|
| project_id | UUID | From session's selected project |

### Return Schema

```json
{
  "project_name": "string",
  "status_columns": ["string"],
  "recent_tasks": [{"title": "string", "status": "string"}],
  "task_count": 0
}
```

---

## Tool: get_pipeline_list

**Purpose**: Lists available agent pipelines for the current project.
**Maps to**: New capability (FR-002)
**Triggers**: FR-002

### LLM-Visible Parameters

```json
{
  "name": "get_pipeline_list",
  "description": "List available agent pipelines for the current project. Use when the user asks about available workflows or pipelines.",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

### Injected Context

| Parameter | Type | Source |
|-----------|------|--------|
| project_id | UUID | From session's selected project |

### Return Schema

```json
{
  "pipelines": [
    {
      "pipeline_id": "string",
      "name": "string",
      "description": "string",
      "step_count": 0
    }
  ]
}
```

---

## Traceability Matrix

| Tool | Functional Requirements | User Stories |
|------|------------------------|--------------|
| create_task_proposal | FR-001, FR-002, FR-003, FR-017 | US-1 |
| create_issue_recommendation | FR-001, FR-002, FR-003, FR-017 | US-1 |
| update_task_status | FR-001, FR-002, FR-003 | US-1 |
| analyze_transcript | FR-002, FR-003, FR-018 | US-1 |
| ask_clarifying_question | FR-011 | US-1 (scenario 3) |
| get_project_context | FR-002 | US-2 |
| get_pipeline_list | FR-002 | US-1 |
