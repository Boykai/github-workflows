# Data Model: Project Board — Parent Issue Hierarchy, Sub-Issue Display, Agent Pipeline Fixes & Functional Filters

**Feature**: 029-board-hierarchy-filters  
**Date**: 2026-03-07

## Existing Entities (Modified)

### BoardItem (Backend — `backend/src/models/board.py` lines 112-139)

```python
class BoardItem(BaseModel):
    item_id: str
    content_id: str | None = None
    content_type: ContentType
    title: str
    number: int | None = None
    repository: Repository | None = None
    url: str | None = None
    body: str | None = None
    status: str
    status_option_id: str
    assignees: list[Assignee] = []
    priority: CustomFieldValue | None = None
    size: CustomFieldValue | None = None
    estimate: float | None = None
    linked_prs: list[LinkedPR] = []
    sub_issues: list[SubIssue] = []
    labels: list[Label] = []           # NEW — GitHub issue labels (FR-004, FR-009)
    created_at: str | None = None      # NEW — ISO 8601 timestamp for sort (FR-010)
    updated_at: str | None = None      # NEW — ISO 8601 timestamp for sort (FR-010)
    milestone: str | None = None       # NEW — Milestone name for filter/group (FR-009, FR-011)
```

### BoardItem (Frontend — `frontend/src/types/index.ts` lines 666-683)

```typescript
export interface BoardItem {
  item_id: string;
  content_id?: string;
  content_type: ContentType;
  title: string;
  number?: number;
  repository?: BoardRepository;
  url?: string;
  body?: string;
  status: string;
  status_option_id: string;
  assignees: BoardAssignee[];
  priority?: BoardCustomFieldValue;
  size?: BoardCustomFieldValue;
  estimate?: number;
  linked_prs: LinkedPR[];
  sub_issues: SubIssue[];
  labels: BoardLabel[];                // NEW — GitHub issue labels
  created_at?: string;                 // NEW — ISO 8601 timestamp
  updated_at?: string;                 // NEW — ISO 8601 timestamp
  milestone?: string;                  // NEW — Milestone name
}
```

### SubIssue (Backend — `backend/src/models/board.py` lines 95-110)

No changes required. The `assigned_agent` field already carries the agent slug. Model name is resolved on the frontend via the `AvailableAgent` lookup.

### SubIssue (Frontend — `frontend/src/types/index.ts` lines 655-664)

No changes to the interface. Model name resolution happens at render time by looking up `assigned_agent` in the `AvailableAgent[]` array.

## New Types

### Label (Backend — `backend/src/models/board.py`)

```python
class Label(BaseModel):
    """A GitHub issue label with color information."""
    id: str                            # GraphQL node ID
    name: str                          # Label display name (e.g., "enhancement")
    color: str                         # Hex color without '#' prefix (e.g., "0075ca")
```

### BoardLabel (Frontend — `frontend/src/types/index.ts`)

```typescript
export interface BoardLabel {
  id: string;                          // GraphQL node ID
  name: string;                        // Label display name
  color: string;                       // Hex color without '#' prefix
}
```

### BoardFilterState (Frontend — `frontend/src/hooks/useBoardControls.ts`)

```typescript
export interface BoardFilterState {
  labels: string[];                    // Filter by label names
  assignees: string[];                 // Filter by assignee logins
  milestones: string[];                // Filter by milestone names
}
```

### BoardSortState (Frontend — `frontend/src/hooks/useBoardControls.ts`)

```typescript
export interface BoardSortState {
  field: 'created' | 'updated' | 'priority' | 'title' | null;
  direction: 'asc' | 'desc';
}
```

### BoardGroupState (Frontend — `frontend/src/hooks/useBoardControls.ts`)

```typescript
export interface BoardGroupState {
  field: 'label' | 'assignee' | 'milestone' | null;
}
```

### BoardControlsState (Frontend — `frontend/src/hooks/useBoardControls.ts`)

```typescript
export interface BoardControlsState {
  filters: BoardFilterState;
  sort: BoardSortState;
  group: BoardGroupState;
}
```

### BoardGroup (Frontend — render helper)

```typescript
export interface BoardGroup {
  name: string;                        // Group header (e.g., "Boykai", "Sprint 1")
  items: BoardItem[];                  // Items in this group
}
```

## State Management

### localStorage Keys

| Key Pattern | Value Type | Lifecycle | Scope |
|------------|------------|-----------|-------|
| `board-controls-{projectId}` | `BoardControlsState` (JSON) | Persists across refreshes; cleared when project changes | Per-project |
| `agent-preset-{projectId}` | `string` (preset/pipeline ID) | Already exists (AgentPresetSelector line 166) | Per-project |

### Component State

| Component | State | Type | Default |
|-----------|-------|------|---------|
| `IssueCard` | `isExpanded` | `boolean` | `false` (collapsed by default, FR-002) |
| `BoardToolbar` | `activePanel` | `'filter' \| 'sort' \| 'group' \| null` | `null` (no panel open) |
| `AgentPresetSelector` | `activePipelineName` | `string \| null` | `null` (shows "Custom") |

## Relationships

```text
ProjectsPage
├── BoardToolbar (NEW)
│   ├── FilterPanel — reads/writes BoardFilterState
│   ├── SortPanel — reads/writes BoardSortState
│   └── GroupByPanel — reads/writes BoardGroupState
├── AgentConfigRow
│   ├── AgentPresetSelector — dynamic "Custom"/pipeline name label
│   └── AgentColumnCell → AgentTile — fixed model name / tool count display
├── ProjectBoard
│   └── BoardColumn (overflow-y-auto constrained height)
│       └── IssueCard
│           ├── LabelChips — renders BoardLabel[] as colored pills
│           └── CollapsibleSubIssues — toggle, sub-issue tiles with agent/model
└── useBoardControls (hook)
    ├── Manages: BoardControlsState
    ├── Reads: BoardDataResponse (raw)
    ├── Outputs: transformed BoardDataResponse (filtered/sorted/grouped)
    └── Persists: localStorage per project
```

## GraphQL Query Changes

### BOARD_GET_PROJECT_ITEMS_QUERY — Extended Issue Fragment

```graphql
... on Issue {
  id
  number
  title
  body
  url
  createdAt                              # NEW — for sort by created date
  updatedAt                              # NEW — for sort by updated date
  milestone {                            # NEW — for filter/group by milestone
    title
  }
  labels(first: 20) {                   # NEW — for label display and filter
    nodes {
      id
      name
      color
    }
  }
  assignees(first: 10) {
    nodes {
      login
      avatarUrl
    }
  }
  repository {
    owner { login }
    name
  }
  timelineItems(itemTypes: [CONNECTED_EVENT, CROSS_REFERENCED_EVENT], first: 50) {
    # ... existing PR linking logic unchanged
  }
}
```

## Data Flow Summary

```text
GitHub GraphQL API
  │
  ├─ labels(first:20) { nodes { id, name, color } }
  ├─ createdAt, updatedAt
  └─ milestone { title }
  │
  ▼
Backend Service (service.py)
  │
  ├─ Parse labels → Label[] on BoardItem
  ├─ Parse createdAt/updatedAt → strings on BoardItem
  ├─ Parse milestone.title → string on BoardItem
  └─ Filter ALL sub-issue IDs from ALL columns (not just Done)
  │
  ▼
Frontend API Response (BoardDataResponse)
  │
  ├─ BoardItem now includes: labels, created_at, updated_at, milestone
  └─ Only parent issues appear as top-level items
  │
  ▼
useBoardControls Hook
  │
  ├─ Apply filters: labels, assignees, milestones
  ├─ Apply sort: created, updated, priority, title
  ├─ Apply group: label, assignee, milestone
  └─ Persist state to localStorage
  │
  ▼
ProjectBoard → BoardColumn → IssueCard
  │
  ├─ IssueCard: label chips, collapsible sub-issues
  ├─ Sub-issue tiles: agent name + model name (from AvailableAgent lookup)
  └─ BoardColumn: constrained height, overflow-y-auto
```
