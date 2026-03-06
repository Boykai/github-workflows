# Component Contracts: Agent Pipeline Drag-and-Drop

**Feature**: `023-pipeline-dragdrop` | **Date**: 2026-03-06

## Overview

This document defines the updated component interfaces (props, callbacks, hooks) for the Agent Pipeline drag-and-drop feature. No new REST/GraphQL API endpoints are required — all changes are frontend-only, using the existing `PUT /workflow/config` persistence path.

---

## Modified Components

### AgentConfigRow (modified)

**File**: `frontend/src/components/board/AgentConfigRow.tsx`

**Change Summary**: Wraps all columns in a single `DndContext` to enable cross-column drag-and-drop. Manages drag state (active item, source column) and renders `DragOverlay`.

```typescript
interface AgentConfigRowProps {
  columns: BoardColumn[];                          // unchanged
  agentConfig: ReturnType<typeof useAgentConfig>;  // unchanged (hook adds moveAgentToColumn)
  availableAgents?: AvailableAgent[];              // unchanged
  renderPresetSelector: React.ReactNode;           // unchanged
  renderAddButton: (status: string) => React.ReactNode; // unchanged
}
```

**New Internal State**:
```typescript
const [activeId, setActiveId] = useState<string | null>(null);
const [activeAgent, setActiveAgent] = useState<AgentAssignment | null>(null);
```

**New Event Handlers**:
```typescript
// Called when drag starts — records the dragged agent
handleDragStart(event: DragStartEvent): void

// Called when dragged item crosses column boundary — live preview
handleDragOver(event: DragOverEvent): void

// Called when drag completes — finalizes move (same or cross-column)
handleDragEnd(event: DragEndEvent): void

// Called when drag is cancelled — revert any preview changes
handleDragCancel(): void
```

**New Rendered Elements**:
- `<DndContext>` wrapping the columns flex container
- `<DragOverlay>` rendering `<AgentTile>` preview of the active dragged item

---

### AgentColumnCell (modified)

**File**: `frontend/src/components/board/AgentColumnCell.tsx`

**Change Summary**: Remove internal `DndContext` (moved to parent). Become a droppable container via `useDroppable`. Keep `SortableContext` for within-column ordering.

```typescript
interface AgentColumnCellProps {
  status: string;                                   // unchanged
  agents: AgentAssignment[];                        // unchanged
  isModified: boolean;                              // unchanged
  onRemoveAgent: (status: string, agentId: string) => void; // unchanged
  onReorderAgents: (status: string, newOrder: AgentAssignment[]) => void; // unchanged
  renderAddButton: React.ReactNode;                 // unchanged
  availableAgents?: AvailableAgent[];               // unchanged
  isDropTarget?: boolean;                           // NEW: highlight when dragged item is over this column
}
```

**New Behavior**:
- Calls `useDroppable({ id: status })` to register as a drop target
- Applies visual highlight when `isOver` is true or `isDropTarget` prop is true
- No longer creates its own `DndContext` or sensors (handled by parent)

---

### AgentTile (no interface changes)

**File**: `frontend/src/components/board/AgentTile.tsx`

**Change Summary**: No prop changes. The existing `sortableProps` interface supports all needed drag behavior. Styling updates for drag-in-progress state.

```typescript
interface AgentTileProps {
  agent: AgentAssignment;                           // unchanged
  onRemove: (id: string) => void;                  // unchanged
  sortableProps?: {                                  // unchanged
    attributes: Record<string, unknown>;
    listeners: Record<string, unknown>;
    setNodeRef: (el: HTMLElement | null) => void;
    style: React.CSSProperties;
    isDragging: boolean;
  };
  availableAgents?: AvailableAgent[];               // unchanged
  isWarning?: boolean;                              // unchanged
}
```

**Styling Changes**:
- When `sortableProps.isDragging` is true: apply `opacity-30` to create ghost effect at original position

---

### AgentDragOverlay (new)

**File**: `frontend/src/components/board/AgentDragOverlay.tsx`

**Purpose**: Render a floating preview of the dragged agent tile inside `DragOverlay`.

```typescript
interface AgentDragOverlayProps {
  agent: AgentAssignment;
  availableAgents?: AvailableAgent[];
}
```

**Behavior**:
- Renders a styled copy of `AgentTile` (without remove button, without sortable props)
- Semi-transparent (`opacity-80`) with shadow for visual distinction
- Follows cursor position (handled by @dnd-kit's DragOverlay)

---

## Modified Hook

### useAgentConfig (modified)

**File**: `frontend/src/hooks/useAgentConfig.ts`

**New Return Value**:
```typescript
interface UseAgentConfigReturn {
  // ... existing fields unchanged ...
  moveAgentToColumn: (
    sourceStatus: string,
    targetStatus: string,
    agentId: string,
    targetIndex?: number
  ) => void;
}
```

**`moveAgentToColumn` Contract**:
- **Preconditions**: `sourceStatus` and `agentId` must identify an existing agent in `localMappings`
- **Postconditions**: Agent removed from source, inserted at `targetIndex` in target (or appended)
- **Side Effects**: Updates `localMappings` state → triggers `isDirty` recomputation
- **Error Handling**: No-op if agent not found in source column

---

## Sensor Configuration

Sensors are configured at the `AgentConfigRow` level (single DndContext):

```typescript
const sensors = useSensors(
  useSensor(PointerSensor, {
    activationConstraint: { distance: 5 },
  }),
  useSensor(TouchSensor, {
    activationConstraint: { delay: 250, tolerance: 5 },
  }),
  useSensor(KeyboardSensor, {
    coordinateGetter: sortableKeyboardCoordinates,
  })
);
```

---

## Collision Detection Strategy

```typescript
collisionDetection: closestCenter
```

- `closestCenter` provides good results for column-based layouts
- Fallback to `pointerWithin` if user testing reveals issues with column boundary detection

---

## Accessibility Contract

| Element | ARIA Attribute | Value |
|---------|---------------|-------|
| Column container | `role` | `"group"` |
| Column container | `aria-label` | `"{status} column, {count} agents"` |
| Agent tile (draggable) | `role` | `"listitem"` |
| Agent tile (draggable) | `aria-roledescription` | `"sortable agent"` |
| Agent tile (dragging) | `aria-grabbed` | `"true"` |
| Drag instructions | `aria-describedby` | Instructions for keyboard users |

**Keyboard Controls** (when item is focused):
- `Space` / `Enter`: Activate drag mode
- `Arrow Up/Down`: Move within column
- `Arrow Left/Right`: Move to adjacent column (custom handler)
- `Escape`: Cancel drag, return to original position
