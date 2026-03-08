# Component Contracts: Project Board — Parent Issue Hierarchy, Sub-Issue Display, Agent Pipeline Fixes & Functional Filters

**Feature**: 029-board-hierarchy-filters  
**Date**: 2026-03-07

## C1: IssueCard — Collapsible Sub-Issues & Label Chips

**File**: `frontend/src/components/board/IssueCard.tsx`

### Visual Contract

```
┌─────────────────────────────────────────┐
│ ● P1  L  8pts                    #42    │  ← Priority, Size, Estimate, Number
│ Implement login flow                     │  ← Title
│ Description snippet...                   │  ← Body (80-char truncation)
│                                          │
│ [enhancement] [p1] [javascript]          │  ← NEW: Label chips (FR-004)
│                                          │
│ 👤 Boykai                                │  ← Assignees
│ 🔗 1 PR                                 │  ← Linked PRs
│                                          │
│ ▶ 3 sub-issues                           │  ← NEW: Collapsible toggle (FR-002)
│ ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐  │  (only when expanded ▼)
│ │ ○ Login form component              │  │
│ │   Agent: speckit.implement          │  │  ← FR-003
│ │   Model: Claude 3.5 Sonnet          │  │  ← FR-003 (resolved via AvailableAgent)
│ │ ✓ API endpoint setup                │  │
│ │   Agent: speckit.implement          │  │
│ │   Model: Claude 3.5 Sonnet          │  │
│ │ ○ Test coverage                     │  │
│ │   Agent: Unassigned                 │  │  ← No agent → "Unassigned"
│ │   Model: —                          │  │  ← No model → dash or omit
│ └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘  │
└─────────────────────────────────────────┘
```

### Behavior Specification

| Behavior | Rule |
|----------|------|
| Default state | Sub-issue section collapsed; only toggle row visible |
| Toggle click | Toggles `isExpanded` local state; shows/hides sub-issue list |
| Zero sub-issues | Toggle row hidden entirely (no "0 sub-issues" badge) |
| Sub-issue count | Badge text: `"{count} sub-issue{count !== 1 ? 's' : ''}"` |
| Chevron direction | `▶` (right) when collapsed; `▼` (down) when expanded |
| Agent display | `assigned_agent` slug formatted via `formatAgentName` (remove `speckit.` prefix) |
| Model display | Resolved from `availableAgents.find(a => a.slug === subIssue.assigned_agent)?.default_model_name` |
| No agent | Display "Unassigned" for agent; omit model line |
| Label chips | Rendered below description, before assignees; max-width with text truncation + hover tooltip for long names |
| Label colors | Background: `#{label.color}`; text: computed contrast (white/black) based on luminance |
| Many labels (>5) | Wrap to next line; no truncation of chip count |
| No labels | Label section hidden (no empty row) |
| Large sub-issue list (50+) | Sub-issue panel gets `max-h-60 overflow-y-auto` for internal scrolling |

### Props Changes

```typescript
interface IssueCardProps {
  item: BoardItem;
  onClick: (item: BoardItem) => void;
  availableAgents?: AvailableAgent[];    // NEW: passed for sub-issue model resolution
}
```

## C2: BoardColumn — Constrained Height Scrolling

**File**: `frontend/src/components/board/BoardColumn.tsx`

### Layout Contract

```
┌──────────────────────────┐
│ ● In Progress  (5)  32pts│  ← Header (fixed, non-scrolling)
│ Description text...      │  ← Optional description
├──────────────────────────┤
│ ┌──────────────────────┐ │
│ │ Card 1               │ │  ← Scrollable area
│ └──────────────────────┘ │     overflow-y: auto
│ ┌──────────────────────┐ │     max-height: calc(100vh - header)
│ │ Card 2               │ │
│ └──────────────────────┘ │
│ ┌──────────────────────┐ │
│ │ Card 3               │ │
│ └──────────────────────┘ │
│         ↕ scroll         │
└──────────────────────────┘
```

### Styling Changes

```
Column container: flex flex-col h-full
Header: flex-shrink-0
Card list: flex-1 overflow-y-auto
```

The key change is ensuring the column has a constrained height from its parent (`ProjectBoard` flex container) so `overflow-y-auto` activates when content overflows.

## C3: AgentTile — Model Name & Tool Count Fix

**File**: `frontend/src/components/board/AgentTile.tsx`

### Current Bug (lines 33, 38-41)

```typescript
// Current — case-sensitive slug match may fail
const metadata = availableAgents?.find((a) => a.slug === agent.slug);
```

### Fix

```typescript
// Fixed — normalize slug comparison for case-insensitive matching
const metadata = availableAgents?.find(
  (a) => a.slug.toLowerCase() === agent.slug.toLowerCase()
);
```

### Visual Contract

```
┌────────────────────────────────────┐
│ ⠿  [A]  speckit.implement         │  ← Drag handle, Avatar, Agent name
│         Claude 3.5 Sonnet · 5 tools│  ← Model name · Tool count (metaLine)
│                                  ✕ │  ← Remove button
└────────────────────────────────────┘
```

### Behavior

| Field | Source | Fallback |
|-------|--------|----------|
| Model name | `metadata?.default_model_name` | Omit from metaLine |
| Tool count | `metadata?.tools_count` | Omit from metaLine |
| Meta separator | `" · "` between model and tools | Single value if only one present |
| Warning badge (⚠) | Shown when `!metadata` | Indicates agent not in available list |

## C4: AgentPresetSelector — Dynamic Pipeline Name

**File**: `frontend/src/components/board/AgentPresetSelector.tsx`

### Current Behavior

The header label always shows the preset label (e.g., "Custom", "GitHub Copilot", "Spec Kit") regardless of whether a saved pipeline configuration is selected.

### New Behavior

```
State A: No saved pipeline active
  → Header shows "Custom" (or matched preset name)

State B: Saved pipeline "Frontend Review Pipeline" selected
  → Header shows "Frontend Review Pipeline"

State C: Saved pipeline active, user makes manual changes (isDirty)
  → Header shows "Custom" (diverged from saved config)

State D: Saved pipeline active, page refresh
  → On load, resolve pipeline ID from localStorage → show pipeline name
```

### Implementation

```typescript
// In AgentPresetSelector, after resolving active preset/pipeline:
const activePipelineName = useMemo(() => {
  if (selectedPipelineId && savedPipelines) {
    const pipeline = savedPipelines.find(p => p.id === selectedPipelineId);
    if (pipeline && !isDirty) return pipeline.name;
  }
  return null; // falls back to preset label (e.g., "Custom")
}, [selectedPipelineId, savedPipelines, isDirty]);
```

The header label uses `activePipelineName ?? matchedPreset.label`.

## C5: BoardToolbar — Filter/Sort/GroupBy Controls

**File**: `frontend/src/components/board/BoardToolbar.tsx` (NEW)

### Visual Contract

```
┌─────────────────────────────────────────────────────────┐
│ [🔽 Filter ●]  [↕ Sort ●]  [⊞ Group By]               │  ← Toolbar
└─────────────────────────────────────────────────────────┘
       │               │
       ▼               ▼
┌─────────────┐  ┌──────────────┐
│ Filter Panel│  │  Sort Panel  │  ← Dropdown panels (one at a time)
│             │  │              │
│ Labels:     │  │ ○ Created ↑↓│
│ ☑ enhance.. │  │ ○ Updated ↑↓│
│ ☑ p1        │  │ ● Priority↑↓│
│ ☐ bug       │  │ ○ Title  ↑↓│
│             │  │              │
│ Assignees:  │  │ [Clear Sort] │
│ ☑ Boykai    │  └──────────────┘
│ ☐ Other     │
│             │
│ Milestones: │
│ ☑ Sprint 5  │
│             │
│ [Clear All] │
└─────────────┘
```

### Props

```typescript
interface BoardToolbarProps {
  controls: BoardControlsState;
  onControlsChange: (controls: BoardControlsState) => void;
  availableLabels: string[];           // Derived from all board items
  availableAssignees: string[];        // Derived from all board items
  availableMilestones: string[];       // Derived from all board items
}
```

### Active State Indicators (FR-013)

| Control | Default State | Active State |
|---------|--------------|--------------|
| Filter | No highlight | Colored dot badge; button has accent background |
| Sort | No highlight | Colored dot badge; shows active sort field name |
| Group By | No highlight | Colored dot badge; shows active group field name |

## C6: useBoardControls Hook

**File**: `frontend/src/hooks/useBoardControls.ts` (NEW)

### API Contract

```typescript
function useBoardControls(
  projectId: string | null,
  boardData: BoardDataResponse | null
): {
  // State
  controls: BoardControlsState;
  
  // Setters
  setFilters: (filters: BoardFilterState) => void;
  setSort: (sort: BoardSortState) => void;
  setGroup: (group: BoardGroupState) => void;
  clearAll: () => void;
  
  // Derived data
  transformedData: BoardDataResponse | null;  // Board data with filters/sort/group applied
  hasActiveControls: boolean;                  // True if any non-default control is active
  
  // Available options (derived from raw board data)
  availableLabels: string[];
  availableAssignees: string[];
  availableMilestones: string[];
}
```

### Transform Pipeline (useMemo)

```text
Raw BoardDataResponse
  │
  ├─ 1. Filter: Apply predicate to items in each column
  │     Predicate: item matches ALL active filter criteria (AND logic)
  │     - labels: item.labels.some(l => filters.labels.includes(l.name))
  │     - assignees: item.assignees.some(a => filters.assignees.includes(a.login))
  │     - milestones: filters.milestones.includes(item.milestone)
  │     Empty filter array = no filter for that field
  │
  ├─ 2. Sort: Reorder items within each column
  │     - 'created': compare item.created_at (ISO string sort)
  │     - 'updated': compare item.updated_at (ISO string sort)
  │     - 'priority': compare priority.name using P0<P1<P2<P3 mapping
  │     - 'title': localeCompare
  │     - null: no sort (default order)
  │
  └─ 3. Group: Add group headers within each column
        - 'label': group by first label name (or "No Label")
        - 'assignee': group by first assignee login (or "Unassigned")
        - 'milestone': group by milestone name (or "No Milestone")
        - null: no grouping (default)
```

### localStorage Persistence

```typescript
// On state change:
localStorage.setItem(
  `board-controls-${projectId}`,
  JSON.stringify(controls)
);

// On mount:
const saved = localStorage.getItem(`board-controls-${projectId}`);
if (saved) setControls(JSON.parse(saved));
```

## C7: ProjectBoard — Group-By Layout

**File**: `frontend/src/components/board/ProjectBoard.tsx`

### Default Layout (no grouping)

```
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Backlog │ │In Prog. │ │  Done   │
│         │ │         │ │         │
│ Card A  │ │ Card D  │ │ Card G  │
│ Card B  │ │ Card E  │ │ Card H  │
│ Card C  │ │ Card F  │ │         │
└─────────┘ └─────────┘ └─────────┘
```

### Grouped Layout (e.g., Group By Assignee)

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Backlog    │ │  In Progress │ │     Done     │
│              │ │              │ │              │
│ ── Boykai ── │ │ ── Boykai ── │ │ ── Boykai ── │
│ Card A       │ │ Card D       │ │ Card G       │
│ Card B       │ │              │ │              │
│              │ │ ── Other ──  │ │ ── Other ──  │
│ ── Other ──  │ │ Card E       │ │ Card H       │
│ Card C       │ │ Card F       │ │              │
│              │ │              │ │              │
│ ─ Unassigned │ │              │ │              │
│              │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Group Header Styling

```
Group header: text-xs font-semibold uppercase text-gray-400 tracking-wide
             border-b border-gray-700 pb-1 mb-2 mt-3
             (first group in column: mt-0)
```

### Behavior

| Scenario | Behavior |
|----------|----------|
| No grouping active | Standard card list in each column |
| Grouping active | Cards organized under group headers within each column |
| Empty group | Group header hidden (don't show "Boykai" with zero cards) |
| Item has no value for group field | Placed in "Unassigned" / "No Label" / "No Milestone" group |
| Group + Sort combined | Items sorted within each group |
| Group + Filter combined | Filtered items organized into groups |
