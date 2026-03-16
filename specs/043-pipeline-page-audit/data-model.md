# Data Model: Pipeline Page Audit

**Feature**: `043-pipeline-page-audit` | **Date**: 2026-03-16

## Entity Diagram

```text
┌─────────────────────┐
│   PipelineConfig    │
│─────────────────────│
│  id                 │
│  project_id         │
│  name               │
│  description        │
│  stages[]           │───────┐
│  is_preset          │       │
│  preset_id          │       │
│  created_at         │       │
│  updated_at         │       │
└─────────────────────┘       │
                              │ 1:N
                    ┌─────────▼───────────┐
                    │   PipelineStage     │
                    │─────────────────────│
                    │  id                 │
                    │  name               │
                    │  order              │
                    │  groups[]           │───────┐
                    │  agents[] (legacy)  │       │
                    │  execution_mode?    │       │
                    │    (legacy)         │       │
                    └─────────────────────┘       │
                                                  │ 1:N
                                        ┌─────────▼───────────┐
                                        │  ExecutionGroup     │
                                        │─────────────────────│
                                        │  id                 │
                                        │  order              │
                                        │  execution_mode     │
                                        │  agents[]           │───────┐
                                        └─────────────────────┘       │
                                                                      │ 1:N
                                                            ┌─────────▼───────────┐
                                                            │  PipelineAgentNode  │
                                                            │─────────────────────│
                                                            │  id                 │
                                                            │  agent_slug         │
                                                            │  agent_display_name │
                                                            │  model_id           │
                                                            │  model_name         │
                                                            │  tool_ids[]         │
                                                            │  tool_count         │
                                                            │  config             │
                                                            └─────────────────────┘

┌───────────────────────────┐       ┌──────────────────────────────┐
│ ProjectPipelineAssignment │       │   PipelineConfigSummary      │
│───────────────────────────│       │──────────────────────────────│
│  project_id               │       │  id                          │
│  pipeline_id              │       │  name                        │
└───────────────────────────┘       │  description                 │
                                    │  stage_count                 │
                                    │  agent_count                 │
                                    │  total_tool_count            │
                                    │  is_preset                   │
                                    │  preset_id                   │
                                    │  stages[]                    │
                                    │  updated_at                  │
                                    └──────────────────────────────┘
```

## Entity Definitions

### PipelineConfig

The core entity representing a user-configured pipeline within a project.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique pipeline identifier (UUID) |
| `project_id` | `string` | Yes | Parent project identifier |
| `name` | `string` | Yes | User-visible pipeline name (must be unique within project) |
| `description` | `string` | Yes | User-visible description (may be empty string) |
| `stages` | `PipelineStage[]` | Yes | Ordered list of pipeline stages |
| `is_preset` | `boolean` | Yes | Whether this is a system-provided preset pipeline |
| `preset_id` | `string` | Yes | Identifier for the preset template (empty if not preset) |
| `created_at` | `string` (ISO 8601) | Yes | Creation timestamp |
| `updated_at` | `string` (ISO 8601) | Yes | Last modification timestamp |

**Validation Rules**:
- `name` must be non-empty after trimming whitespace
- `name` must be unique within the same `project_id` (HTTP 409 on conflict)
- `stages` can be an empty array (valid for draft pipelines)

### PipelineStage

A step within a pipeline containing one or more execution groups.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique stage identifier (UUID) |
| `name` | `string` | Yes | User-visible stage name |
| `order` | `number` | Yes | Display/execution order (0-indexed) |
| `groups` | `ExecutionGroup[]` | No | Ordered execution groups within this stage |
| `agents` | `PipelineAgentNode[]` | Yes | **Legacy**: flat list of agents (kept in sync with group agents) |
| `execution_mode` | `'sequential' \| 'parallel'` | No | **Legacy**: stage-level execution mode |

**Validation Rules**:
- `groups` defaults to a single default group if absent (handled by `ensureDefaultGroups()` migration)
- Legacy `agents[]` is always kept in sync with `groups[].agents[]` via `syncLegacyAgents()`

**UI Rendering Notes**:
- Stage cards display in `order` sequence
- Stage name supports inline editing with validation
- Empty stages show a placeholder with "Add agent" call-to-action

### ExecutionGroup

A collection of agents within a stage that execute together with a shared mode.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique group identifier (UUID) |
| `order` | `number` | Yes | Execution/display order within stage |
| `execution_mode` | `'sequential' \| 'parallel'` | Yes | How agents in this group are orchestrated |
| `agents` | `PipelineAgentNode[]` | Yes | Ordered list of agents in this group |

**Validation Rules**:
- A group cannot be removed if it contains agents
- At least one group must exist per stage (enforced by `ensureDefaultGroups()`)

**UI Rendering Notes**:
- Groups with `parallel` mode show a visual parallel indicator
- Execution mode toggle: `role="switch"` with `aria-checked` for accessibility

### PipelineAgentNode

An individual agent assignment within an execution group.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique node identifier (UUID) |
| `agent_slug` | `string` | Yes | Reference to the agent definition |
| `agent_display_name` | `string` | Yes | Human-readable agent name |
| `model_id` | `string` | Yes | Selected AI model identifier |
| `model_name` | `string` | Yes | Human-readable model name |
| `tool_ids` | `string[]` | Yes | List of enabled tool identifiers |
| `tool_count` | `number` | Yes | Count of enabled tools |
| `config` | `Record<string, unknown>` | Yes | Additional agent configuration |

**UI Rendering Notes**:
- Agent nodes display name, model, and tool count
- Long agent names and model names truncated with ellipsis + tooltip (FR-018)
- Missing/deleted agents should display gracefully with a "missing agent" indicator

### ProjectPipelineAssignment

Designates which pipeline is active/default for a project.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | `string` | Yes | Project identifier |
| `pipeline_id` | `string` | Yes | Active pipeline identifier |

### PipelineConfigSummary

Lightweight pipeline representation used in list views.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Pipeline identifier |
| `name` | `string` | Yes | Pipeline name |
| `description` | `string` | Yes | Pipeline description |
| `stage_count` | `number` | Yes | Number of stages |
| `agent_count` | `number` | Yes | Total agents across all stages |
| `total_tool_count` | `number` | Yes | Total tools across all agents |
| `is_preset` | `boolean` | Yes | Whether this is a preset |
| `preset_id` | `string` | Yes | Preset identifier |
| `stages` | `PipelineStage[]` | Yes | Full stage data (for flow graph preview) |
| `updated_at` | `string` (ISO 8601) | Yes | Last modification timestamp |

### PipelineValidationErrors

Client-side validation error state.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string \| undefined` | No | Name field validation error |
| `stages` | `string \| undefined` | No | Stages validation error |
| `[key: string]` | `string \| undefined` | No | Extensible for additional field errors |

### PipelineModelOverride

Derived state representing model consistency across all agents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mode` | `'auto' \| 'specific' \| 'mixed'` | Yes | Current model override mode |
| `modelId` | `string` | Yes | Selected model ID (meaningful when mode is 'specific') |
| `modelName` | `string` | Yes | Selected model display name |

## State Transitions

### Page-Level States

```text
┌──────────────────┐
│  No Project      │ ─── user selects project ──→ ┌───────────┐
│  Selected        │                               │  Loading   │
│ (empty state)    │                               │  Pipeline  │
└──────────────────┘                               │  Data      │
                                                   └─────┬─────┘
                                                         │
                                    ┌────────────────────┼────────────────────┐
                                    │                    │                    │
                                    ▼                    ▼                    ▼
                             ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
                             │  Empty      │   │  Populated   │   │  Error       │
                             │  Pipeline   │   │  Pipeline    │   │  State       │
                             │  Board      │   │  Board       │   │  (retry)     │
                             └─────────────┘   └──────────────┘   └──────────────┘
```

### Pipeline Board States

```text
                    ┌─────────┐
                    │  empty  │ ← initial state / after delete
                    └────┬────┘
                         │
            ┌────────────┼────────────┐
            │ new        │ load       │
            ▼            │            ▼
     ┌──────────┐       │     ┌──────────┐
     │ creating │       │     │ editing  │
     └────┬─────┘       │     └────┬─────┘
          │             │          │
          │ save success│          │ save success / discard
          └──────┬──────┘          └──────┬──────┘
                 │                        │
                 ▼                        ▼
          ┌──────────┐            ┌──────────┐
          │ editing  │            │  empty   │ (if discarding new)
          └──────────┘            └──────────┘
```

### Unsaved Changes Dialog States

```text
     ┌──────────┐
     │  Hidden  │ ← default
     └────┬─────┘
          │ user triggers navigation/load/new while dirty
          ▼
     ┌──────────────────┐
     │  Visible         │
     │  (3 options)     │
     └──┬───┬───┬───────┘
        │   │   │
        │   │   └── Cancel → dialog closes, no action
        │   │
        │   └── Discard → revert state, continue pending action
        │
        └── Save → save pipeline
                   │
            ┌──────┼──────┐
            │             │
            ▼             ▼
      Save Success   Save Failure
      → continue     → show error
        pending        in dialog,
        action         stay open
```

### Save Operation States

```text
     ┌──────────┐
     │  Idle    │
     └────┬─────┘
          │ user clicks Save
          ▼
     ┌──────────┐
     │ Validating│
     └────┬──────┘
          │
     ┌────┼────────────┐
     │                 │
     ▼                 ▼
  Valid            Invalid
  → API call       → show validation
     │               errors inline
     ▼
  ┌───────┐
  │Saving │ (isSaving=true, button disabled)
  └───┬───┘
      │
  ┌───┼──────────┐
  │              │
  ▼              ▼
Success       Failure
→ toast       → user-friendly
→ update        error message
  snapshot    → save button
→ isDirty       re-enabled
  = false
```
