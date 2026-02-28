# Data Model: Add 'Human' Agent Type to Agent Pipeline

**Feature**: 014-human-agent-pipeline | **Date**: 2026-02-28

## Overview

The Human agent type introduces **no new database entities or tables**. It operates as a thin behavioral extension of the existing agent infrastructure. This document defines the constant definitions, type extensions, and state transitions required.

## Entity: Human Agent (Builtin Constant)

The Human agent is registered as a builtin constant, not a database entity.

### Constants Additions (`backend/src/constants.py`)

| Constant | Key | Value | Notes |
|----------|-----|-------|-------|
| `AGENT_DISPLAY_NAMES` | `"human"` | `"Human"` | Display name in UI and tracking table |
| `DEFAULT_AGENT_MAPPINGS` | *(none)* | *(not added)* | Human is not a default agent in any column; users add it manually |
| `AGENT_OUTPUT_FILES` | *(none)* | *(not added)* | Human agents produce no file artifacts |

### Agent Slug

| Field | Value | Rationale |
|-------|-------|-----------|
| Slug | `human` | Follows builtin naming pattern (lowercase, no dots for non-speckit agents like `copilot-review`). Short and descriptive. |

### AvailableAgent Properties (returned by `/workflow/agents`)

| Field | Value |
|-------|-------|
| `slug` | `"human"` |
| `display_name` | `"Human"` |
| `description` | `"Manual human task — creates a sub-issue assigned to the issue creator"` |
| `avatar_url` | `null` (frontend renders person icon based on slug) |
| `source` | `"builtin"` |

## Entity: AgentAssignment (Existing — No Changes)

The `AgentAssignment` model already supports any agent slug:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `UUID` | auto-generated | Unique instance ID |
| `slug` | `str` | required | Set to `"human"` for Human steps |
| `display_name` | `str \| None` | optional | `"Human"` |
| `config` | `dict \| None` | optional | Reserved; unused for Human |

**No schema changes required.**

## Entity: PipelineState (Existing — No Changes)

The `PipelineState` dataclass already supports blocking behavior:

| Field | Type | Human Agent Behavior |
|-------|------|---------------------|
| `agents` | `list[str]` | Includes `"human"` at the configured position |
| `current_agent_index` | `int` | Points to `"human"` when it's the active step |
| `completed_agents` | `list[str]` | `"human"` added upon completion |
| `agent_sub_issues` | `dict` | Maps `"human"` → `{"number": int, "node_id": str, "url": str}` |

**No schema changes required.**

## Entity: Sub Issue (Human) — Behavioral Extension

Human sub-issues use the same GitHub Sub Issue structure as automated agent sub-issues, with different assignment behavior:

| Attribute | Automated Agent Sub Issue | Human Agent Sub Issue |
|-----------|--------------------------|----------------------|
| Title | `[agent-slug] Parent Title` | `[human] Parent Title` |
| Body | Tailored for agent | Tailored for human (task description) |
| Labels | `ai-generated`, `sub-issue` | `ai-generated`, `sub-issue` |
| Assignee | GitHub Copilot bot | **Parent issue creator** |
| Project | Same as parent | Same as parent |

### Assignment Resolution

```
Parent Issue → issue.user.login → Sub Issue assignee
```

| Scenario | Behavior |
|----------|----------|
| Creator resolved | Sub-issue assigned to `issue.user.login` |
| Creator not resolved | Sub-issue created unassigned; warning comment posted on parent issue |

## Entity: Completion Signal — Behavioral Extension

Two completion signals are supported for Human steps:

### Signal 1: Sub Issue Closed

| Attribute | Value |
|-----------|-------|
| Event source | Sub Issue state change to `closed` |
| Detection method | Poll sub-issue status via GitHub API on each cycle |
| Authorized by | Any user who can close the sub-issue |

### Signal 2: 'Done!' Comment

| Attribute | Value |
|-----------|-------|
| Event source | Comment on parent issue |
| Comment body | Exact match: `Done!` |
| Authorized by | Only the user assigned to the Human sub-issue (FR-012) |
| Detection method | Extend `check_last_comment_for_done()` or add parallel check in helpers |

### Completion Signal Validation Rules

| Rule | Enforcement |
|------|-------------|
| Only exact `Done!` string accepted | Regex: `^Done!$` (no prefix like `agent:`) |
| Only assigned user's comments accepted | Compare comment author with sub-issue assignee |
| Idempotent advancement | `current_agent_index` check prevents double advancement |
| Sub Issue reopened after close | No effect — pipeline has already advanced |
| Sub Issue deleted | Warning surfaced; 'Done!' comment path remains available |

## State Transitions

### Human Step Lifecycle

```
┌──────────────┐
│   ⏳ Pending  │ ← Step exists in pipeline, not yet active
└──────┬───────┘
       │ Previous step completes (or pipeline starts here)
       ▼
┌──────────────┐
│  🔄 Active   │ ← Sub-issue created & assigned; pipeline blocked
└──────┬───────┘
       │ Sub Issue closed OR 'Done!' comment from assigned user
       ▼
┌──────────────┐
│   ✅ Done    │ ← Pipeline advances to next step
└──────────────┘
```

### Transition Triggers

| From | To | Trigger |
|------|----|---------|
| Pending | Active | Pipeline reaches this step's position (automatic) |
| Active | Done | Sub Issue closed **OR** assigned user comments 'Done!' on parent |
| Done | *(terminal)* | No further transitions |

## Validation Rules

| Rule | Applies To | Enforcement Point |
|------|-----------|-------------------|
| Human slug must be `"human"` | Agent registration | `constants.py` |
| Human agent must not be assigned to Copilot | Agent assignment | `orchestrator.py` / `pipeline.py` |
| Only issue creator assigned to Human sub-issue | Sub-issue creation | `orchestrator.py` |
| Only assigned user's 'Done!' accepted | Completion detection | `helpers.py` |
| Exact 'Done!' match (case-sensitive, no whitespace) | Completion detection | `agent_tracking.py` or `helpers.py` |
| Idempotent advancement | Pipeline advancement | `pipeline.py` (existing behavior) |

## Migration Requirements

**None.** No new database tables, columns, or migrations are required. All changes are in-memory constants, conditional logic branches, and frontend rendering.
