# Component Contracts: Project Page UX Overhaul

**Feature Branch**: `028-project-page-ux`
**Date**: 2026-03-07

## C1: formatAgentName Utility

**File**: `frontend/src/utils/formatAgentName.ts`
**Type**: Pure function (no side effects, no dependencies)

### Contract

```typescript
/**
 * Format an agent identifier for display.
 *
 * Priority: displayName (if provided) > slug formatting.
 * Slug rules:
 *   1. Split on "."
 *   2. Filter empty segments
 *   3. Title-case each segment (first char upper, rest lower)
 *   4. Special compound: "speckit" → "Spec Kit"
 *   5. Join segments with " - "
 *
 * @param slug - Agent identifier (e.g., "speckit.tasks", "linter")
 * @param displayName - Optional explicit display name (takes precedence)
 * @returns Formatted display string
 */
export function formatAgentName(slug: string, displayName?: string | null): string;
```

### Examples

| slug | displayName | Result |
|------|-------------|--------|
| `"linter"` | `undefined` | `"Linter"` |
| `"speckit.tasks"` | `undefined` | `"Spec Kit - Tasks"` |
| `"speckit.implement"` | `undefined` | `"Spec Kit - Implement"` |
| `"agent.v2.runner"` | `undefined` | `"Agent - V2 - Runner"` |
| `"speckit..tasks"` | `undefined` | `"Spec Kit - Tasks"` |
| `""` | `undefined` | `""` |
| `"linter"` | `"My Custom Linter"` | `"My Custom Linter"` |
| `"LINTER"` | `undefined` | `"Linter"` |
| `"speckit.analyze"` | `""` | `"Spec Kit - Analyze"` |

---

## C2: AgentTile Component

**File**: `frontend/src/components/board/AgentTile.tsx`
**Type**: React component (presentational)

### Visual Contract

```
┌──────────────────────────┐
│  Spec Kit - Tasks        │  ← formatAgentName(slug, display_name)
│  GPT-4o · 3 tools        │  ← model_name + tools_count from AvailableAgent
└──────────────────────────┘
```

### Behavior

- Display formatted agent name using `formatAgentName(agent.slug, agent.display_name)`
- Look up matching `AvailableAgent` by `slug` from `availableAgents` prop
- If model name found: display as secondary text (e.g., "GPT-4o")
- If tools count > 0: display as "N tools" (e.g., "3 tools")
- If both present: join with " · " separator
- If neither present: omit secondary metadata line entirely
- Styling matches Pipeline Stages tile: `border border-border/60 rounded-[1.2rem]`

---

## C3: AgentConfigRow Layout

**File**: `frontend/src/components/board/AgentConfigRow.tsx`
**Type**: React component (container with DnD)

### Layout Contract

```
┌─────────────────────────────────────────────────────────────────┐
│  Agent Pipeline   [Preset Selector ▼]          [+ Add Agent]   │
├──────────┬──────────┬──────────┬──────────┬────────────────────┤
│ Backlog  │ To Do    │ In Prog  │ Review   │ Done               │
│ [tile]   │ [tile]   │ [tile]   │ [tile]   │                    │
│          │ [tile]   │          │          │                    │
└──────────┴──────────┴──────────┴──────────┴────────────────────┘
```

### Styling Contract

- Container: `celestial-panel rounded-[1.2rem] border border-border/60`
- Grid: `grid gap-3` with `gridTemplateColumns: repeat(N, minmax(14rem, 1fr))`
- Column cells: `border border-border/60 rounded-[1.2rem] p-2`
- Matches `PipelineBoard.tsx` visual weight

### DnD Contract

- Sensors: PointerSensor (distance: 5), TouchSensor (delay: 250, tolerance: 5), KeyboardSensor
- Collision detection: `closestCenter`
- DragOverlay: Anchored to cursor grab point (no teleport)
- Drop targets: Visual highlight (`border-primary/40 bg-primary/5`) during drag-over
- Cross-column moves: `moveAgentToColumn()` with live preview
- Same-column reorder: `reorderAgents()` via `arrayMove`

---

## C4: IssueDetailModal Markdown Rendering

**File**: `frontend/src/components/board/IssueDetailModal.tsx`
**Type**: React component (modal)

### Rendering Contract

```typescript
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// In the description section:
{item.body && (
  <div className="mb-6">
    <h3 className="text-sm font-semibold mb-2">Description</h3>
    <div className="prose prose-sm dark:prose-invert max-w-none overflow-y-auto max-h-[50vh]
                    bg-muted/30 p-4 rounded-md border border-border">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {item.body}
      </ReactMarkdown>
    </div>
  </div>
)}
```

### Supported Markdown Elements

| Element | Rendered As |
|---------|-------------|
| `# Heading` | `<h1>` with appropriate size/weight |
| `## Heading` | `<h2>` with appropriate size/weight |
| `` `code` `` | `<code>` with monospace font and subtle background |
| ` ```lang ``` ` | `<pre><code>` with monospace font, distinct background |
| `- item` | `<ul><li>` with bullet markers |
| `1. item` | `<ol><li>` with numbered markers |
| `**bold**` | `<strong>` with bold weight |
| `*italic*` | `<em>` with italic style |
| `[text](url)` | `<a>` with link styling |
| `~~strike~~` | `<del>` with strikethrough |
| `| table |` | `<table>` with bordered cells (GFM) |

### Overflow Handling

- Content constrained to `max-h-[50vh]` with `overflow-y-auto`
- Prevents layout breakage for long issue descriptions

---

## C5: ProjectBoard Layout

**File**: `frontend/src/components/board/ProjectBoard.tsx`
**Type**: React component (container)

### Layout Contract (Before → After)

**Before**:
```
[flex container, gap-6]
  [BoardColumn w-[320px]] [BoardColumn w-[320px]] ... [+ Add column w-[320px]]
```

**After**:
```
[grid container, gap-4]
  grid-template-columns: repeat(N, minmax(14rem, 1fr))
  [BoardColumn] [BoardColumn] ... [BoardColumn]
  (No "Add column" button)
```

### Behavior

- `+ Add column` button: **REMOVED**
- Column widths: Dynamic `minmax(14rem, 1fr)` instead of fixed `w-[320px]`
- Grid template matches `AgentConfigRow` grid for vertical alignment
- `overflow-x-auto` preserved for narrow viewports

---

## C6: AgentPresetSelector Enhancement

**File**: `frontend/src/components/board/AgentPresetSelector.tsx`
**Type**: React component (dropdown/popover)

### Data Sources

1. **Built-in Presets** (existing): Custom, GitHub Copilot, Spec Kit
2. **Saved Configurations** (new): Fetched from `GET /api/pipelines/{project_id}`

### Selection Persistence

- On select: Store config ID in `localStorage` key `pipeline-config:{project_id}`
- On mount: Read stored config ID and restore selection
- On project change: Read new project's stored config

### Mapping Contract

```typescript
// Convert PipelineConfig stages to AgentAssignment mappings
function pipelineConfigToMappings(
  config: PipelineConfig,
  columnNames: string[]
): Record<string, AgentAssignment[]> {
  // For each stage, map stage.name → column name (case-insensitive)
  // For each agent in stage, create AgentAssignment { id: uuid, slug, display_name }
}
```

---

## C7: Drop Target Visual Indicator

**File**: `frontend/src/components/board/AgentColumnCell.tsx`
**Type**: React component (droppable zone)

### Visual Contract

| State | Border | Background |
|-------|--------|------------|
| Default | `border-border/60` | `transparent` |
| Drag hover (valid) | `border-primary/40` | `bg-primary/5` |
| Drag hover (invalid) | `border-destructive/40` | `bg-destructive/5` |
| Active drop | `border-primary/60` | `bg-primary/10` |

### Transition

- `transition-colors duration-150` for smooth state changes
- Indicator shown only when a drag operation is active (not on hover without drag)
