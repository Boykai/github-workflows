# Data Model: Project Page — Agent Pipeline UX Overhaul

**Feature Branch**: `028-project-page-ux`
**Date**: 2026-03-07

> This feature is primarily frontend. Backend changes are limited to board data filtering. This document describes type modifications, new types, and entity changes needed for the overhaul.

## Existing Entities (Modified)

### AgentAssignment (Frontend — No Schema Change)

**File**: `frontend/src/types/index.ts` (lines 240-245)

Current type is unchanged. Model/tool metadata is derived from `AvailableAgent` lookup, not stored on the assignment.

```typescript
export interface AgentAssignment {
  id: string;
  slug: string;
  display_name?: string | null;
  config?: Record<string, unknown> | null;
}
```

### AvailableAgent (Frontend — Extended)

**File**: `frontend/src/types/index.ts` (lines 247-254)

Extended with model and tool metadata for agent tile display.

```typescript
export interface AvailableAgent {
  slug: string;
  display_name: string;
  description?: string | null;
  avatar_url?: string | null;
  source: AgentSource;
  default_model_name?: string | null;  // NEW: e.g., "GPT-4o", "Claude Sonnet"
  tools_count?: number | null;          // NEW: Derived from tools array length
}
```

### Agent (Backend — No Schema Change)

**File**: `backend/src/models/agents.py` (lines 22-39)

Already contains the fields needed — no migration required:

```python
class Agent(BaseModel):
    # ... existing fields ...
    default_model_name: str = ""    # Already exists
    tools: list[str] = Field(default_factory=list)  # Already exists — len() gives count
```

### BoardColumn (Backend Response — Modified Behavior)

**File**: `backend/src/services/github_projects/service.py` (lines 920-970)

Behavior change: When building columns with "Done"/"Closed" status, filter out items that are sub-issues of any parent item.

```python
# Pseudocode for filtering
done_column_items = [
    item for item in column_items
    if item.item_id not in all_sub_issue_ids
]
```

### BoardItem (Frontend — No Type Change)

**File**: `frontend/src/types/index.ts`

The `BoardItem.body` field (already `string | null`) is now rendered as Markdown instead of plain text. No type change needed.

## New Types (Frontend Only)

### FormatAgentNameInput

Not a formal type — the utility function signature:

```typescript
function formatAgentName(slug: string, displayName?: string | null): string
```

**Rules**:
| Input | Output |
|-------|--------|
| `("linter")` | `"Linter"` |
| `("speckit.tasks")` | `"Spec Kit - Tasks"` |
| `("speckit.implement")` | `"Spec Kit - Implement"` |
| `("agent.v2.runner")` | `"Agent - V2 - Runner"` |
| `("speckit..tasks")` | `"Spec Kit - Tasks"` |
| `("LINTER")` | `"Linter"` |
| `("linter", "My Custom Linter")` | `"My Custom Linter"` |
| `("")` | `""` |

### PipelineConfigOption

Represents a saved pipeline configuration in the selector dropdown.

```typescript
interface PipelineConfigOption {
  id: string;                        // Pipeline config ID
  name: string;                      // Display name (e.g., "Default Pipeline")
  stages: PipelineStage[];           // Stage definitions with agents
  isBuiltIn: boolean;                // true for hardcoded presets, false for saved configs
}
```

### AgentTileMetadata

Display metadata resolved from AvailableAgent lookup.

```typescript
interface AgentTileMetadata {
  formattedName: string;             // Output of formatAgentName()
  modelName?: string | null;         // e.g., "GPT-4o"
  toolsCount?: number | null;        // e.g., 5
}
```

## Existing Types Used As-Is

| Entity | Key Fields | Used By |
|--------|-----------|---------|
| `BoardItem` | item_id, title, body?, status, sub_issues | IssueCard, IssueDetailModal |
| `BoardColumn` | status, items, item_count | BoardColumn, ProjectBoard |
| `BoardDataResponse` | columns, rate_limit | ProjectBoard, useProjectBoard |
| `PipelineConfig` | id, name, stages | AgentPresetSelector (new usage) |
| `PipelineStage` | id, name, order, agents | Pipeline config mapping |
| `PipelineAgentNode` | agent_slug, model_id, model_name | Agent metadata source |
| `SubIssue` | id, number, title, state | Done column filtering |
| `WorkflowConfiguration` | agent_mappings | useAgentConfig |

## State Changes

### Pipeline Config Selection Persistence

**Storage**: `localStorage` key `pipeline-config:{project_id}`
**Value**: Pipeline config ID (string) or `null` for custom/no selection
**Read**: On `AgentPresetSelector` mount — restore last selected config
**Write**: On config selection change — persist immediately
**Clear**: On project switch — read new project's stored config

### Sub-Issue ID Collection (Backend)

**Lifecycle**: Computed during board data assembly
**Scope**: Per-request, not cached
**Data**: `Set[str]` of all `item_id` values that appear as sub-issues of any parent item
**Usage**: Filter Done/Closed column items against this set

## Relationships

```
ProjectsPage
├── AgentConfigRow (pipeline section)
│   ├── AgentPresetSelector
│   │   ├── Built-in Presets (Custom, GitHub Copilot, Spec Kit)
│   │   └── Saved Configs (from /api/pipelines/{project_id})
│   ├── AgentColumnCell (per status column)
│   │   └── SortableAgentTile
│   │       ├── formatAgentName(slug, display_name) → formatted name
│   │       └── AvailableAgent lookup → model_name, tools_count
│   └── DragOverlay → AgentDragOverlay
├── ProjectBoard (kanban section)
│   ├── BoardColumn (per status, shared grid)
│   │   └── IssueCard
│   └── (No "Add column" button)
└── IssueDetailModal
    └── ReactMarkdown + remarkGfm → rendered body
```

## Component Prop Changes

### AgentTile (Modified Props)

```typescript
interface AgentTileProps {
  agent: AgentAssignment;
  availableAgents: AvailableAgent[];  // For metadata lookup
  // ... existing sortable props
}
// Now displays: formatAgentName(agent.slug, agent.display_name)
// Now displays: model name and tool count from AvailableAgent lookup
```

### IssueDetailModal (No Prop Changes)

The `item.body` rendering changes from plain text to `<ReactMarkdown remarkPlugins={[remarkGfm]}>{item.body}</ReactMarkdown>`. No prop interface changes.

### ProjectBoard (Modified Props/Behavior)

```typescript
interface ProjectBoardProps {
  boardData: BoardDataResponse;
  onItemClick: (item: BoardItem) => void;
  // "Add column" button removed from render
  // Layout changes from flex w-[320px] to shared grid
}
```
