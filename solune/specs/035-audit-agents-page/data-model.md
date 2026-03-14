# Data Model: Audit & Polish the Agents Page

**Feature Branch**: `035-audit-agents-page`
**Date**: 2026-03-11

## Overview

This document describes the key entities rendered on the Agents page and their relationships. Since this is an audit-and-polish feature (no new entities), the data model captures the **existing** entities that components interact with, their validation rules, and state transitions. This serves as a reference for auditing component correctness.

## Entity Diagram

```text
┌─────────────────────────┐
│      AgentsPage         │
│  (selectedProject,      │
│   boardData, agentConfig│
│   pipelineList,         │
│   pipelineAssignment)   │
└─────┬──────────┬────────┘
      │          │
      │          │ composes
      ▼          ▼
┌────────────┐  ┌───────────────────┐
│ AgentsPanel│  │  Column            │
│ (Agent     │  │  Assignments       │
│  Catalog)  │  │  (Orbital Map)     │
└──────┬─────┘  └────────┬──────────┘
       │                 │
  ┌────┴────┐       ┌───┴─────────────┐
  ▼         ▼       ▼                 ▼
┌─────────┐ ┌────────────┐  ┌──────────────┐  ┌──────────────────┐
│AgentCard│ │AgentInline │  │AgentConfigRow│  │AgentPreset       │
│         │ │Editor      │  │  (DnD host)  │  │Selector          │
└────┬────┘ └────────────┘  └──────┬───────┘  └──────────────────┘
     │                             │
     ▼                        ┌────┴─────────┐
┌──────────────┐              ▼              ▼
│AddAgentModal │        ┌──────────┐   ┌──────────┐
│IconPicker    │        │AgentCol  │   │AgentSave │
│BulkUpdate    │        │umnCell   │   │Bar       │
└──────────────┘        └────┬─────┘   └──────────┘
                             │
                             ▼
                       ┌──────────┐
                       │AgentTile │
                       └──────────┘
```

## Entities

### AgentConfig

The primary entity representing an AI agent in the catalog.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique agent identifier |
| `name` | string | ✅ | Display name (1–100 characters) |
| `slug` | string | ✅ | URL-safe identifier derived from name |
| `description` | string | ❌ | Optional agent description |
| `systemPrompt` | string | ❌ | System prompt text (0–30,000 characters) |
| `model` | string | ❌ | AI model identifier |
| `tools` | string[] | ✅ | Array of tool IDs (may be empty) |
| `status` | `'active' \| 'pending_creation' \| 'pending_deletion'` | ✅ | Current lifecycle status |
| `source` | `'builtin' \| 'repository' \| 'shared' \| 'local'` | ✅ | Origin of the agent definition |
| `iconName` | string | ❌ | Celestial icon name override (e.g., `'eclipse'`, `'crescent'`) |
| `avatarUrl` | string | ❌ | Custom avatar image URL |
| `usageCount` | number | ❌ | Number of times used in pipeline runs |
| `createdAt` | string (ISO 8601) | ❌ | Creation timestamp |

**Validation Rules**:

- `name` must be 1–100 non-empty characters
- `systemPrompt` must not exceed 30,000 characters
- `status` must be one of the three allowed values
- `tools` defaults to empty array
- `slug` is auto-generated from name if not provided

**UI Rendering Notes**:

- Rendered as `AgentCard.tsx` in the catalog grid
- Status badge colors: Active → `solar-chip-success`, Pending Creation → `solar-chip-violet`, Pending Deletion → `solar-chip-danger`
- Source badge colors: builtin → `solar-chip-neutral`, repository → `solar-chip-success`, shared → `solar-chip-violet`, local → `solar-chip`
- Icon falls back to `ThemedAgentIcon` (slug-based) → first letter of name
- Spotlight (featured) cards use `variant="spotlight"` with gradient overlay

**State Transitions**:

```text
[none] → pending_creation (after create mutation, awaiting PR merge)
pending_creation → active (after PR merged)
active → pending_deletion (after delete mutation, awaiting PR merge)
pending_deletion → [removed] (after PR merged)
```

---

### AgentAssignment

An agent assigned to a board column in the Orbital Map.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agentInstanceId` | string (UUID) | ✅ | Unique instance ID (one agent can appear in multiple columns) |
| `slug` | string | ✅ | Reference to the agent's slug |
| `model` | string | ❌ | Model override for this specific assignment |
| `pipelineModel` | string | ❌ | Model assigned via pipeline configuration |

**Validation Rules**:

- `agentInstanceId` must be a UUID (generated client-side)
- `slug` must match an existing agent's slug
- An agent can appear multiple times in the same column (clone operation)

**UI Rendering Notes**:

- Rendered as `AgentTile.tsx` within `AgentColumnCell.tsx`
- Drag-and-drop enabled via @dnd-kit (`useSortable`)
- Compact variant used in pipeline view; default variant in full assignments view
- Warning state shown when agent slug doesn't match any available agent

---

### BoardColumn

A status column in the project board.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | ✅ | Column status name (e.g., "Backlog", "In Progress", "Done") |
| `items` | BoardItem[] | ✅ | Items in this column |
| `item_count` | number | ✅ | Total items |

**UI Rendering Notes**:

- Used as headers in `AgentConfigRow.tsx` grid
- Each column maps to an `AgentColumnCell.tsx` with droppable zone
- Soft limit warning at 10+ agents per column

---

### AvailableAgent

An agent available for assignment to columns (from the server-side agent registry).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `slug` | string | ✅ | Agent identifier |
| `name` | string | ✅ | Display name |
| `description` | string | ❌ | Agent description |
| `model` | string | ❌ | Default model |
| `source` | string | ❌ | Agent source origin |

**UI Rendering Notes**:

- Rendered in `AddAgentPopover.tsx` dropdown
- Duplicate detection: agents already assigned to the target column are shown with reduced opacity
- Source badges displayed with color-coded chips

---

### PipelinePreset

A predefined agent-to-column mapping configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Preset identifier (`'custom'`, `'copilot'`, `'speckit'`) |
| `label` | string | ✅ | Display name |
| `mappings` | Record<string, AgentAssignment[]> | ✅ | Column → agents mapping |

**Built-in Presets**:

- **Clear** (`custom`): Empty mappings — removes all assignments
- **GitHub Copilot** (`copilot`): Single Copilot agent in "In Progress"
- **Spec Kit** (`speckit`): Full pipeline with speckit agents across Backlog, Ready, In Progress, Review

**UI Rendering Notes**:

- Rendered as toggle buttons in `AgentPresetSelector.tsx`
- Active preset highlighted with `solar-chip-soft` class
- Saved pipelines loaded from server via `pipelines/list` query

---

### CelestialIconName

An icon from the project's custom icon set.

| Field | Type | Description |
|-------|------|-------------|
| Name | string enum | One of ~40 celestial icon names (e.g., `'eclipse'`, `'crescent'`, `'moon-phase'`, `'constellation'`, `'nebula'`, `'comet'`, `'orbit'`, `'solar-flare'`, etc.) |

**UI Rendering Notes**:

- Selected via `AgentIconCatalog.tsx` grid
- Rendered by `ThemedAgentIcon.tsx` using slug-to-icon mapping
- Automatic selection: `getThemedAgentIconName(slug)` provides default based on agent slug
- Explicit override stored as `AgentConfig.iconName`

---

## State Interactions

### Dirty State Tracking

The Agents page manages two independent dirty-state concerns:

1. **Inline Editor Dirty State**: Tracked via `AgentInlineEditor` snapshot comparison → reported to `AgentsPanel` via `onDirtyChange` callback → blocks navigation via `useUnsavedChanges`
2. **Column Assignment Dirty State**: Tracked via `useAgentConfig` hook → displayed in `AgentSaveBar` → persisted via save API on user action

### Data Flow

```text
AgentsPage
├── useProjects() → selectedProject
├── useProjectBoard(projectId) → boardData (columns)
├── useAgentConfig(projectId) → agentConfig (mappings, isDirty, save/discard)
├── useQuery('pipelines/list') → pipelineList
├── useQuery('pipelines/assignment') → pipelineAssignment
│
├── AgentsPanel
│   ├── useAgentsList(projectId) → agents
│   ├── usePendingAgentsList(projectId) → pendingAgents
│   ├── useModels() → models (for BulkModelUpdateDialog)
│   │
│   ├── AgentCard
│   │   ├── useDeleteAgent(projectId) → delete mutation
│   │   ├── useUpdateAgent(projectId) → icon update mutation
│   │   └── useConfirmation() → delete confirmation
│   │
│   ├── AgentInlineEditor
│   │   └── useUpdateAgent(projectId) → save mutation
│   │
│   └── AddAgentModal
│       ├── useCreateAgent(projectId) → create mutation
│       ├── useUpdateAgent(projectId) → edit mutation
│       └── useToolsList(projectId) → available tools
│
└── Column Assignments (Orbital Map)
    └── AgentConfigRow
        ├── DndContext (drag-and-drop orchestration)
        ├── AgentPresetSelector
        │   └── useQuery('pipelines/list') → saved pipelines
        ├── AgentColumnCell[] (per board column)
        │   ├── useDroppable() → drop zone
        │   └── AgentTile[] (per assigned agent)
        │       └── useSortable() → drag handle
        ├── AddAgentPopover (per column)
        │   └── useAvailableAgents() → agent dropdown
        └── AgentSaveBar (when isDirty)
```
