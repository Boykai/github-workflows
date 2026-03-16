# Data Model: Pipeline Page Audit

**Feature Branch**: `043-pipeline-page-audit`
**Date**: 2026-03-16

## Overview

This document describes the key entities rendered on the Pipeline page and their relationships. Since this is an audit-and-polish feature (no new entities), the data model captures the **existing** entities that components interact with, their validation rules, and state transitions. This serves as a reference for auditing component correctness.

## Entity Diagram

```text
┌───────────────────────────────────┐
│       AgentsPipelinePage          │
│  (selectedProject, boardState,    │
│   pipeline, pipelines,            │
│   assignedPipelineId, isDirty,    │
│   modelOverride, validationErrors)│
└──────┬─────────┬─────────┬───────┘
       │         │         │
       │         │         │ composes
       ▼         ▼         ▼
┌────────────┐ ┌──────────────────┐ ┌──────────────────┐
│Pipeline    │ │PipelineBoard     │ │SavedWorkflows    │
│Toolbar     │ │ (stage grid)     │ │List              │
└──────┬─────┘ └────────┬─────────┘ └────────┬─────────┘
       │                │                     │
       ▼                ▼                     ▼
┌──────────────┐  ┌───────────┐        ┌───────────────┐
│UnsavedChanges│  │StageCard  │ [1..N] │PipelineConfig │
│Dialog        │  │           │        │Summary cards  │
└──────────────┘  └─────┬─────┘        └───────────────┘
                        │
                   ┌────┴──────────┐
                   ▼               ▼
             ┌───────────────┐  ┌──────────────────┐
             │ExecutionGroup │  │PipelineFlow      │
             │Card       [1.N│  │Graph             │
             └──────┬────────┘  └──────────────────┘
                    │
                    ▼
              ┌───────────┐
              │AgentNode  │ [1..N]
              │           │
              └─────┬─────┘
                    │
                    ▼
              ┌───────────┐
              │Model      │
              │Selector   │
              └───────────┘

Side panels:
┌──────────────────┐  ┌──────────────────┐
│PipelineAnalytics │  │PipelineModel     │
│ (usage stats)    │  │Dropdown          │
└──────────────────┘  │ (global override)│
                      └──────────────────┘
```

## Entities

### PipelineConfig

The primary entity representing a user-configured pipeline with ordered stages and agent assignments.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique pipeline identifier |
| `project_id` | string | ✅ | Owning project identifier |
| `name` | string | ✅ | Display name (1–100 characters) |
| `description` | string | ❌ | Optional pipeline description |
| `stages` | PipelineStage[] | ✅ | Ordered list of pipeline stages |
| `is_preset` | boolean | ✅ | Whether this is a system-provided preset |
| `preset_id` | string | ❌ | Identifier linking to preset definition |
| `created_at` | string (ISO 8601) | ✅ | Creation timestamp |
| `updated_at` | string (ISO 8601) | ✅ | Last update timestamp |

**Validation Rules**:

- `name` must be 1–100 non-empty characters
- `name` must be unique within the project scope (server-enforced)
- `stages` defaults to empty array for new pipelines
- `is_preset` is read-only from the client perspective

**UI Rendering Notes**:

- Rendered as the primary editing surface in `PipelineBoard.tsx`
- Pipeline name displayed in an inline-editable input with validation error display
- Preset pipelines shown with `PresetBadge.tsx` indicator
- Timestamps formatted with `formatTimeAgo` (relative for recent, absolute for older)
- Long names truncated with `text-ellipsis` and full name in Tooltip

**State Transitions**:

```text
[none] → creating (user clicks "Create Pipeline")
creating → editing (user saves new pipeline)
editing → editing (user modifies and saves)
editing → [deleted] (user confirms delete)
```

---

### PipelineConfigSummary

A lightweight representation of a pipeline used in list views.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique pipeline identifier |
| `name` | string | ✅ | Display name |
| `description` | string | ❌ | Optional description |
| `stage_count` | number | ✅ | Number of stages |
| `agent_count` | number | ✅ | Total agents across all stages |
| `total_tool_count` | number | ✅ | Total tools across all agents |
| `is_preset` | boolean | ✅ | Whether this is a preset |
| `preset_id` | string | ❌ | Preset identifier |
| `stages` | PipelineStage[] | ✅ | Stage details (for preview) |
| `updated_at` | string (ISO 8601) | ✅ | Last update timestamp |

**UI Rendering Notes**:

- Rendered as cards in `SavedWorkflowsList.tsx`
- Cards display name, stage count, agent count, and updated timestamp
- Active (assigned) pipeline highlighted with distinct styling
- Cards are interactive (`role="button"`) for loading into the editor
- Action buttons: Copy, Assign/Unassign

---

### PipelineStage

A step within a pipeline containing one or more execution groups of agents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique stage identifier |
| `name` | string | ✅ | Display name (editable inline) |
| `order` | number | ✅ | Position in the pipeline (0-indexed) |
| `groups` | ExecutionGroup[] | ❌ | Execution groups (modern format) |
| `agents` | PipelineAgentNode[] | ✅ | Legacy flat agent list (backward compatibility) |
| `execution_mode` | `'sequential' \| 'parallel'` | ❌ | Legacy stage-level mode (backward compatibility) |

**Validation Rules**:

- `name` must be non-empty
- `order` is automatically managed during reorder operations
- `groups` takes precedence over `agents` when present (migration path)
- Legacy `agents` array maintained for backward compatibility with existing data

**UI Rendering Notes**:

- Rendered as `StageCard.tsx` in the horizontal board layout
- Stage name editable inline with Enter to confirm, Escape to cancel
- Lock icon (`role="img" aria-label="Stage position is locked"`) for position indication
- Agent picker button to add agents to the stage
- Remove stage button with `aria-label="Remove stage"`

---

### ExecutionGroup

A collection of agents within a stage that execute together with a specified mode.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique group identifier |
| `order` | number | ✅ | Position within the stage |
| `execution_mode` | `'sequential' \| 'parallel'` | ✅ | How agents in this group are orchestrated |
| `agents` | PipelineAgentNode[] | ✅ | Agents in this group |

**Validation Rules**:

- At least one agent required per group (empty groups can exist during editing)
- `execution_mode` defaults to `'sequential'`
- `order` is managed automatically during reorder

**UI Rendering Notes**:

- Rendered as `ExecutionGroupCard.tsx` within `StageCard.tsx`
- Mode toggle button with `aria-label` describing the switch action
- Remove group button with `aria-label="Remove group"`
- Visual distinction between sequential (arrow indicators) and parallel (side-by-side) modes
- `ParallelStageGroup.tsx` wrapper for parallel layout

---

### PipelineAgentNode

An individual agent assignment within an execution group.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique node identifier |
| `agent_slug` | string | ✅ | Reference to the agent by slug |
| `agent_display_name` | string | ✅ | Human-readable agent name |
| `model_id` | string | ✅ | Selected model identifier |
| `model_name` | string | ✅ | Human-readable model name |
| `tool_ids` | string[] | ✅ | Selected tool identifiers |
| `tool_count` | number | ✅ | Number of selected tools |
| `config` | Record<string, unknown> | ❌ | Additional agent configuration |

**Validation Rules**:

- `agent_slug` must match an existing agent's slug
- `model_id` must be a valid model identifier
- `tool_ids` defaults to empty array

**UI Rendering Notes**:

- Rendered as `AgentNode.tsx` within `ExecutionGroupCard.tsx`
- Displays agent name, model, tool count
- Action buttons: Select tools (`aria-label="Select tools"`), Clone (`aria-label="Clone agent"`), Remove (`aria-label="Remove agent"`)
- Model selection via `ModelSelector.tsx` dropdown
- Missing agent (slug not found) should display a graceful fallback indicator

---

### ProjectPipelineAssignment

A project-level setting designating the active/default pipeline.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | string | ✅ | Project identifier |
| `pipeline_id` | string | ✅ | Assigned pipeline identifier |

**UI Rendering Notes**:

- The assigned pipeline is highlighted in `SavedWorkflowsList.tsx`
- "Assign" / "Unassign" action on saved workflow cards
- Affects which pipeline is used for project execution

---

### PipelineModelOverride

Client-side state for pipeline-level model selection.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mode` | `'auto' \| 'specific' \| 'mixed'` | ✅ | Override mode |
| `modelId` | string | ✅ | Selected model identifier (when mode is 'specific') |
| `modelName` | string | ✅ | Human-readable model name |

**UI Rendering Notes**:

- Managed by `usePipelineModelOverride` hook
- Rendered via `PipelineModelDropdown.tsx` in the board header
- `auto`: Each agent uses its configured model
- `specific`: All agents use the selected model
- `mixed`: Some agents overridden, others use defaults

---

### PipelineValidationErrors

Client-side validation state for pipeline editing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ❌ | Pipeline name validation error |
| `stages` | string | ❌ | Stage-level validation error |
| `[key: string]` | string | ❌ | Additional field-level errors |

**UI Rendering Notes**:

- Managed by `usePipelineValidation` hook
- Name error displayed below the pipeline name input with `aria-describedby` association
- Errors cleared on user correction via `clearValidationError`
- Validation triggered on save attempt via `validatePipeline()`

---

### PipelineBoardState

Client-side enum representing the current editing mode.

| Value | Description |
|-------|-------------|
| `'empty'` | No pipeline loaded; show empty state with create CTA |
| `'creating'` | New pipeline being built; not yet saved |
| `'editing'` | Existing pipeline loaded for editing |

---

### PresetPipelineDefinition

A system-provided preset pipeline template.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `presetId` | string | ✅ | Unique preset identifier |
| `name` | string | ✅ | Preset display name |
| `description` | string | ✅ | Preset description |
| `stages` | PipelineStage[] | ✅ | Preset stage configuration |

**UI Rendering Notes**:

- Presets are seeded on page mount via `pipelinesApi.seedPresets()`
- Preset pipelines display `PresetBadge.tsx` indicator
- Presets are not directly editable; user must copy to create a custom variant

---

## State Interactions

### Dirty State Tracking

The Pipeline page manages dirty state through the `usePipelineReducer` hook:

1. **Pipeline editing dirty state**: Tracked by comparing current pipeline state against the last saved snapshot. Any modification (name change, stage add/remove, agent add/remove, model change, tool change) sets `isDirty = true`. Saving or discarding resets to `isDirty = false`.
2. **Navigation guard**: `useBlocker` from react-router-dom blocks navigation when `isDirty === true`. Combined with `useConfirmation` for the `UnsavedChangesDialog`.
3. **Browser close guard**: `beforeunload` event listener activates when `isDirty === true`.

### Data Flow

```text
AgentsPipelinePage
├── useAuth() → authentication state
├── useProjects() → selectedProject
├── useProjectBoard(projectId) → boardData (for project context)
├── useAgentConfig(projectId) → agentConfig (for agent availability)
├── useAvailableAgents(projectId) → agents list for picker
├── useModels() → available AI models
├── usePipelineConfig(projectId) → MAIN PIPELINE STATE
│   ├── usePipelineReducer() → pipeline, isDirty, isSaving, saveError, boardState
│   ├── usePipelineBoardMutations(dispatch) → 20+ mutation functions
│   ├── usePipelineValidation() → validationErrors, validatePipeline, clearValidationError
│   ├── usePipelineModelOverride(pipeline) → modelOverride, setModelOverride
│   ├── useQuery(pipelineKeys.list(projectId)) → pipelines list
│   ├── useQuery(pipelineKeys.assignment(projectId)) → assignedPipelineId
│   └── useMutation → savePipeline, deletePipeline, duplicatePipeline, etc.
├── useConfirmation() → confirmation dialog state
├── useBlocker(isDirty) → navigation blocking
│
├── PipelineToolbar
│   └── Props: pipeline, isDirty, isSaving, isPreset, onSave, onDelete, onDiscard, onCopy, onNew
│
├── PipelineBoard
│   ├── Props: pipeline, boardState, validationErrors, modelOverride, mutations...
│   ├── StageCard[] (one per stage)
│   │   ├── Props: stage, onUpdate, onRemove, onAddAgent, onRemoveAgent...
│   │   ├── ExecutionGroupCard[] (one per group)
│   │   │   ├── Props: group, onUpdateMode, onRemove, onAddAgent...
│   │   │   └── AgentNode[] (one per agent in group)
│   │   │       ├── Props: agent, onUpdate, onRemove, onClone, models
│   │   │       └── ModelSelector
│   │   │           └── Props: modelId, models, onChange
│   │   └── Agent picker (add agents to stage)
│   └── PipelineModelDropdown
│       └── Props: modelOverride, models, onChange
│
├── SavedWorkflowsList
│   └── Props: pipelines, assignedPipelineId, onLoad, onCopy, onAssign
│
├── PipelineAnalytics
│   └── Props: projectId (fetches own data)
│
└── UnsavedChangesDialog
    └── Props: isOpen, onSave, onDiscard, onCancel
```
