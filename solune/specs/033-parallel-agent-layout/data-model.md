# Data Model: Parallel Agent Layout in Pipelines

**Feature Branch**: `033-parallel-agent-layout`
**Date**: 2026-03-10
**Status**: Complete

## Entity Overview

```text
Pipeline 1──* Stage 1──* AgentNode
                │
                └── execution_mode: "sequential" | "parallel"

PipelineRun 1──* StageRun 1──* AgentRun
```

## Entity: PipelineStage (updated)

Extends the existing `PipelineStage` with a single new field.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | `string` (UUID) | Yes | — | Unique identifier |
| `name` | `string` (1–100) | Yes | — | Display name for the stage |
| `order` | `integer` (≥0) | Yes | — | Sequential position in pipeline |
| `agents` | `PipelineAgentNode[]` | No | `[]` | Ordered list of agents in this stage |
| **`execution_mode`** | `string` enum | No | `"sequential"` | **NEW** — `"sequential"` or `"parallel"` |

### Validation Rules

- `execution_mode` MUST be one of `"sequential"` or `"parallel"`
- When `execution_mode` is `"parallel"` and `agents.length < 2`, the mode SHOULD auto-revert to `"sequential"` on save (edge case from spec)
- When `execution_mode` is `"sequential"`, agents execute in array order (index 0, then 1, etc.)
- When `execution_mode` is `"parallel"`, all agents start simultaneously; array order determines visual left-to-right positioning only

### State Transitions

```text
  ┌─────────────────┐       add 2nd agent        ┌────────────────┐
  │   sequential     │ ──────────────────────────► │    parallel     │
  │ (agents.length≤1)│                             │ (agents.length≥2│
  └─────────────────┘ ◄────────────────────────── └────────────────┘
                        remove agent → length < 2
```

- Adding a second agent to a sequential stage prompts the user to switch to parallel mode (or automatically switches via the "Add Parallel Agent" button)
- Removing agents from a parallel stage until only 1 remains auto-reverts to sequential

### Backward Compatibility

Existing stages stored in `pipeline_configs.stages` JSON column do **not** include `execution_mode`. Pydantic deserialization with `default="sequential"` ensures these stages behave identically to before. No SQL migration required.

---

## Entity: PipelineAgentNode (unchanged)

No changes to this entity. Included for completeness.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | `string` (UUID) | Yes | — | Unique identifier |
| `agent_slug` | `string` | Yes | — | Agent type identifier |
| `agent_display_name` | `string` | No | `""` | Human-readable agent name |
| `model_id` | `string` | No | `""` | Override AI model ID |
| `model_name` | `string` | No | `""` | Override AI model name |
| `tool_ids` | `string[]` | No | `[]` | MCP tool IDs assigned to agent |
| `tool_count` | `integer` | No | `0` | Count of assigned tools |
| `config` | `object` | No | `{}` | Agent-specific configuration |

---

## Entity: PipelineConfig (unchanged)

No changes. The `stages` array already supports variable-length agent lists per stage.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | `string` (UUID) | Yes | — | Unique identifier |
| `project_id` | `string` | Yes | — | Owning project |
| `name` | `string` (1–100) | Yes | — | Pipeline name (unique per project) |
| `description` | `string` (0–500) | No | `""` | Pipeline description |
| `stages` | `PipelineStage[]` | No | `[]` | Ordered stages |
| `is_preset` | `boolean` | No | `false` | Whether this is a system preset |
| `preset_id` | `string` | No | `""` | Preset identifier for idempotent seeding |
| `blocking` | `boolean` | No | `false` | Whether issues block in a queue |
| `created_at` | `string` (ISO 8601) | Yes | — | Creation timestamp |
| `updated_at` | `string` (ISO 8601) | Yes | — | Last update timestamp |

---

## Entity: PipelineState (runtime, extended)

The in-memory execution state tracked during pipeline runs. Extended with parallel tracking fields.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `issue_number` | `integer` | Yes | — | GitHub issue being processed |
| `project_id` | `string` | Yes | — | Project context |
| `status` | `string` | Yes | — | Current board status/column |
| `agents` | `string[]` | Yes | — | Agent slugs for current status |
| `current_agent_index` | `integer` | No | `0` | Sequential mode: current agent position |
| `completed_agents` | `string[]` | No | `[]` | Agents that have completed |
| `started_at` | `datetime` | No | `null` | When this status was entered |
| `error` | `string` | No | `null` | Error message if failed |
| `agent_assigned_sha` | `string` | No | `""` | HEAD SHA when agent was assigned |
| `agent_sub_issues` | `dict` | No | `{}` | Maps agent_name → sub-issue info |
| `original_status` | `string` | No | `null` | Preserved transition target |
| `target_status` | `string` | No | `null` | Next status to transition to |
| **`execution_mode`** | `string` | No | `"sequential"` | **NEW** — Stage execution mode |
| **`parallel_agent_statuses`** | `dict[str, str]` | No | `{}` | **NEW** — Per-agent status for parallel stages. Keys: agent slug, Values: `"pending"` \| `"running"` \| `"completed"` \| `"failed"` |
| **`failed_agents`** | `string[]` | No | `[]` | **NEW** — Agent slugs that failed in a parallel stage |

### Parallel Execution State Machine

```text
Stage enters execution:
  if execution_mode == "sequential":
    → existing behavior (current_agent_index increments)
  if execution_mode == "parallel":
    → all agents set to "pending" in parallel_agent_statuses
    → all agents dispatched simultaneously → status becomes "running"
    → as each completes → status becomes "completed" or "failed"
    → when ALL are "completed" → stage complete, advance pipeline
    → when ANY is "failed" and ALL are done → stage failed, halt pipeline
```

---

## Relationship Diagram

```text
┌──────────────────────────────────┐
│          PipelineConfig          │
│ ─────────────────────────────    │
│ id, name, description, blocking  │
│ project_id, is_preset, preset_id │
│ stages: PipelineStage[]          │
└──────────┬───────────────────────┘
           │ 1..*
           ▼
┌──────────────────────────────────┐
│          PipelineStage           │
│ ─────────────────────────────    │
│ id, name, order                  │
│ execution_mode: seq | parallel   │  ◄── NEW FIELD
│ agents: PipelineAgentNode[]      │
└──────────┬───────────────────────┘
           │ 0..*
           ▼
┌──────────────────────────────────┐
│       PipelineAgentNode          │
│ ─────────────────────────────    │
│ id, agent_slug                   │
│ agent_display_name               │
│ model_id, model_name             │
│ tool_ids[], tool_count, config{} │
└──────────────────────────────────┘
```

---

## Storage Notes

- **No SQL migration needed**: The `stages` column is `TEXT NOT NULL DEFAULT '[]'` storing JSON. Adding `execution_mode` to the Pydantic model with a default value means existing JSON deserializes correctly.
- **Serialization**: When saving, `execution_mode` is included in the JSON. When loading old records, the field defaults to `"sequential"`.
- **Index impact**: None — no new columns or indexes required at the SQL level.
