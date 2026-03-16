# Data Model: Agents Page Audit

**Feature**: 043-agents-page-audit | **Date**: 2026-03-16

## Overview

The Agents page manages two primary domains: the **Agent Catalog** (CRUD operations on agent configurations) and the **Column Assignment Map** (assigning agents to board columns). This document captures the entity model, relationships, state transitions, and data flow as they exist today and will remain after the audit (no schema changes).

## Entities

### AgentConfig (Catalog Agent)

The primary entity representing a configured AI agent in the system.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | ✅ | Unique identifier (UUID) |
| name | string | ✅ | Display name |
| slug | string | ✅ | URL-safe identifier, unique per project |
| description | string \| null | ❌ | Agent description text |
| system_prompt | string \| null | ❌ | System prompt configuration |
| model_id | string \| null | ❌ | Assigned AI model identifier |
| model_name | string \| null | ❌ | Display name of the assigned model |
| status | AgentStatus | ✅ | Current lifecycle status |
| source | AgentSource | ✅ | Where the agent config originates |
| icon_name | string \| null | ❌ | Celestial icon identifier |
| avatar_url | string \| null | ❌ | Custom avatar image URL |
| tools | AgentTool[] | ✅ | Assigned tools (may be empty array) |
| github_issue_number | number \| null | ❌ | Linked GitHub issue |
| created_at | string | ✅ | ISO 8601 timestamp |
| updated_at | string | ✅ | ISO 8601 timestamp |

**Validation Rules**:
- `name`: Required, non-empty string
- `slug`: Required, auto-generated from name, unique per project
- `status`: Must be one of `'active' | 'pending_pr' | 'pending_deletion'`
- `source`: Must be one of `'local' | 'repo' | 'both'`
- `tools`: Array of AgentTool objects (validated on backend)

### AgentAssignment (Column Assignment)

An instance of an agent assigned to a board column.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | ✅ | Unique instance ID (UUID) |
| slug | string | ✅ | Reference to AgentConfig.slug |
| display_name | string \| null | ❌ | Override display name |
| config | Record<string, unknown> \| null | ❌ | Instance-specific configuration |

**Validation Rules**:
- `id`: UUID format, unique per column
- `slug`: Must reference an existing agent slug
- Same agent slug can appear in multiple columns

### AvailableAgent (Registry Agent)

An agent template from the workflow API registry.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| slug | string | ✅ | Unique identifier |
| display_name | string | ✅ | Human-readable name |
| description | string \| null | ❌ | Agent description |
| avatar_url | string \| null | ❌ | Default avatar URL |
| icon_name | string \| null | ❌ | Default icon identifier |
| default_model_id | string \| null | ❌ | Default model |
| default_model_name | string \| null | ❌ | Default model display name |
| tools_count | number \| null | ❌ | Number of available tools |
| source | AgentSource | ✅ | `'builtin' | 'repository'` |

### AgentTool

A tool capability assignable to an agent.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| tool_id | string | ✅ | Unique tool identifier |
| name | string | ✅ | Display name |
| description | string \| null | ❌ | Tool description |

### BoardColumn

A project board column (status) to which agents are assigned.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | string | ✅ | Column name (case-insensitive matching) |
| items | BoardItem[] | ✅ | Items in this column |
| item_count | number | ✅ | Count of items |

### AgentPreset

A predefined agent-to-column mapping configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | ✅ | Preset identifier |
| label | string | ✅ | Display name |
| description | string | ✅ | Preset description |
| mappings | Record<string, AgentAssignment[]> | ✅ | Column → agents mapping |

## Relationships

```text
AgentConfig (Catalog)
  ├── 1:N → AgentTool (tools array)
  ├── 1:N → AgentAssignment (same slug in multiple columns)
  └── 1:1 → AvailableAgent (slug match for registry data)

BoardColumn
  └── 1:N → AgentAssignment (via localMappings in useAgentConfig)

AgentPreset
  └── 1:N → AgentAssignment (preset defines column mappings)

AgentsPage
  ├── uses → AgentConfig[] (via useAgents → agentsApi.list)
  ├── uses → AgentConfig[] (via useAgents → agentsApi.pending)
  ├── uses → BoardColumn[] (via useProjectBoard)
  ├── uses → AgentAssignment[] (via useAgentConfig → localMappings)
  └── uses → PipelineConfig[] (via pipelinesApi.list for usage counts)
```

## State Transitions

### Agent Lifecycle

```text
[Created] → active
  ├── (update) → active (stays active after edit)
  ├── (delete initiated) → pending_deletion
  │     ├── (deletion confirmed) → [Deleted]
  │     └── (clear pending) → active
  └── (PR created) → pending_pr
        ├── (PR merged) → active
        └── (PR closed / clear) → active
```

### Column Assignment State

```text
[Server State] ← useAgentConfig.reset()
  │
  ├── addAgent(column, agent) → [Dirty]
  ├── removeAgent(column, instanceId) → [Dirty]
  ├── reorderAgents(column, oldIndex, newIndex) → [Dirty]
  ├── moveAgentToColumn(sourceCol, targetCol, instanceId) → [Dirty]
  └── applyPreset(preset) → [Dirty]
        │
        [Dirty] → isDirty = true, AgentSaveBar visible
          ├── save() → [Saving] → [Server State] (on success)
          └── discard() → [Server State] (reset to server snapshot)
```

### Inline Editor State

```text
[View Mode] → (click edit) → [Edit Mode]
  │
  [Edit Mode]
  ├── (modify fields) → [Dirty Edit Mode]
  │     ├── (save) → [Saving] → [View Mode] (on success)
  │     ├── (cancel) → [View Mode] (discard changes)
  │     └── (navigate away while dirty) → [Confirm Discard Dialog]
  └── (cancel) → [View Mode]
```

## Data Flow

### Page Load Sequence

```text
1. AgentsPage mounts
2. useAuth() → authenticated user context
3. useProjects() → active project ID
4. If no project selected → render ProjectSelectionEmptyState (STOP)
5. Parallel fetches:
   a. useAgents → agentKeys.list(projectId) → agentsApi.list()
   b. useAgents → agentKeys.pending(projectId) → agentsApi.pending()
   c. useProjectBoard → board columns
   d. useAgentConfig → workflow config → localMappings
   e. useQuery → pipelinesApi.list() → pipeline usage counts
6. Each section renders independently based on its query state
7. Page fully interactive when all queries resolve
```

### Mutation Flow (Create/Update/Delete)

```text
1. User initiates action (form submit, delete click)
2. If destructive → ConfirmationDialog → user confirms
3. useMutation fires → API call
4. On success:
   a. Toast notification displayed
   b. invalidateQueries([agentKeys.all]) → refetch lists
   c. UI updates from fresh cache
5. On error:
   a. isRateLimitApiError(error) → rate limit message
   b. Otherwise → "Could not [action]. [Reason]. [Suggestion]."
   c. Toast notification with error
```

## Query Key Registry

| Key | Pattern | Usage |
|-----|---------|-------|
| `agentKeys.all` | `['agents']` | Invalidation root for all agent queries |
| `agentKeys.list(id)` | `['agents', 'list', projectId]` | Agent catalog list |
| `agentKeys.pending(id)` | `['agents', 'pending', projectId]` | Pending agents list |
| Pipeline list | `['pipelines', 'list', projectId]` | Pipeline configs for usage counts |
| Pipeline assignments | `['pipelines', 'assignment', projectId]` | Pipeline assignment data |
| Workflow config | `['workflow', projectId]` | Agent column assignments |
