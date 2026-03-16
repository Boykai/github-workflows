# Data Model: Agents Page Audit

**Feature Branch**: `043-agents-page-audit`
**Date**: 2026-03-16

## Overview

This document describes the key entities rendered on the Agents page and their relationships. Since this is an audit-and-polish feature (no new entities), the data model captures the **existing** entities that components interact with, their validation rules, and state transitions. This serves as a reference for auditing component correctness and ensuring type safety.

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
| `iconName` | string \| null | ❌ | Celestial icon name override (e.g., `'eclipse'`, `'crescent'`) |
| `avatarUrl` | string \| null | ❌ | Custom avatar image URL |
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

### AgentCreate

Payload for creating a new agent.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Display name |
| `description` | string | ❌ | Optional description |
| `systemPrompt` | string | ❌ | System prompt text |
| `model` | string | ❌ | AI model identifier |
| `tools` | string[] | ❌ | Array of tool IDs |
| `iconName` | string | ❌ | Celestial icon name |

**Validation Rules**:

- `name` is required, 1–100 characters
- All other fields are optional with sensible defaults

---

### AgentUpdate

Payload for updating an existing agent.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ❌ | Updated display name |
| `description` | string | ❌ | Updated description |
| `systemPrompt` | string | ❌ | Updated system prompt |
| `model` | string | ❌ | Updated AI model identifier |
| `tools` | string[] | ❌ | Updated tool IDs |
| `iconName` | string | ❌ | Updated Celestial icon name |

**Validation Rules**:

- All fields optional (partial update)
- Same constraints as AgentCreate for provided fields

---

### AgentAssignment

An agent assigned to a board column in the Orbital Map.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agentInstanceId` | string (UUID) | ✅ | Unique instance ID (one agent can appear in multiple columns) |
| `slug` | string | ✅ | Reference to the agent's slug |
| `model` | string \| null | ❌ | Model override for this specific assignment |
| `pipelineModel` | string \| null | ❌ | Model assigned via pipeline configuration |

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

### AvailableAgent

A registered agent template from the workflow API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `slug` | string | ✅ | Agent slug identifier |
| `displayName` | string | ✅ | Human-readable name |
| `model` | string \| null | ❌ | Default model assignment |
| `source` | `'builtin' \| 'repository'` | ✅ | Agent source classification |

**UI Rendering Notes**:

- Listed in `AddAgentPopover.tsx` for column assignment
- Source badge differentiates builtin vs. repository agents
- Used to resolve agent display info in `AgentTile` and `AgentConfigRow`

---

### AgentTool

A tool capability that can be assigned to an agent.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `toolId` | string | ✅ | Unique tool identifier |
| `displayName` | string | ✅ | Human-readable tool name |
| `description` | string | ❌ | Tool description |

**UI Rendering Notes**:

- Managed via `ToolsEditor.tsx` component
- Ordered list with drag reorder, add, and remove operations
- Displayed as chips/badges in `AgentCard` metadata

---

### BoardColumn

A project board column (status) to which agents are assigned.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Column display name |
| `agents` | AgentAssignment[] | ✅ | Agents assigned to this column |

**Validation Rules**:

- Column names are case-insensitive for matching
- Column order is determined by the board configuration

**UI Rendering Notes**:

- Rendered as `AgentColumnCell.tsx` in the Orbital Map grid
- Each column is a droppable zone for agent tiles
- Empty columns show an "Add agent" action

---

### PipelineConfiguration

Pipeline stage definitions that reference agents. Used for usage counts and config counts.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Pipeline configuration ID |
| `name` | string | ✅ | Pipeline name |
| `stages` | PipelineStage[] | ✅ | Pipeline stages with agent references |

**UI Rendering Notes**:

- Not directly rendered on the Agents page
- Used to compute `agentUsageCounts` and `pipelineConfigCounts` passed to `AgentsPanel`
- Pipeline config count displayed as badge on `AgentCard`

## Relationships

```text
AgentConfig 1──* AgentAssignment (via slug)
AgentConfig 1──* AgentTool (via tools array)
BoardColumn 1──* AgentAssignment (via agents array)
AvailableAgent 1──1 AgentConfig (lookup by slug)
PipelineConfiguration *──* AgentConfig (via stage agent references)
```

## Edge Cases

1. **Empty agents list + populated board**: Board columns render with zero agent tiles; empty state shows in catalog panel only
2. **Agent with no icon**: Falls back to `ThemedAgentIcon` slug-based generation, then first letter avatar
3. **Agent with null optional fields**: `description`, `systemPrompt`, `model`, `iconName`, `avatarUrl` may all be null — UI uses graceful defaults
4. **Orphaned assignment**: `AgentAssignment.slug` doesn't match any `AvailableAgent` — shows warning state on tile
5. **Rate limit on mutation**: Detected via `isRateLimitApiError()` — specific error message with retry guidance
6. **Very long agent name (>200 chars)**: Truncated with `text-ellipsis`, full name in Tooltip
