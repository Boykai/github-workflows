# Quickstart: Agent Pipeline Drag-and-Drop Implementation

**Feature**: `023-pipeline-dragdrop` | **Date**: 2026-03-06

## Prerequisites

- Node.js 18+ with npm
- Repository cloned and dependencies installed (`cd frontend && npm install`)
- Backend running (`cd backend && python -m uvicorn src.main:app`)
- A GitHub Project V2 with status columns configured

## Architecture Overview

```text
AgentConfigRow (DndContext — single context for all columns)
├── AgentColumnCell (useDroppable + SortableContext per column)
│   ├── SortableAgentTile (useSortable per tile)
│   └── SortableAgentTile
├── AgentColumnCell
│   └── SortableAgentTile
└── DragOverlay (floating preview of dragged tile)
```

## Implementation Order

### Step 1: Add `moveAgentToColumn` to useAgentConfig

**File**: `frontend/src/hooks/useAgentConfig.ts`

Add a new method alongside existing `addAgent`, `removeAgent`, `reorderAgents`:

```typescript
const moveAgentToColumn = useCallback(
  (sourceStatus: string, targetStatus: string, agentId: string, targetIndex?: number) => {
    setLocalMappings((prev) => {
      const sourceKey = findKey(prev, sourceStatus);
      const targetKey = findKey(prev, targetStatus) ?? targetStatus;
      if (!sourceKey) return prev;

      const sourceAgents = [...(prev[sourceKey] ?? [])];
      const agentIndex = sourceAgents.findIndex((a) => a.id === agentId);
      if (agentIndex === -1) return prev;

      const [agent] = sourceAgents.splice(agentIndex, 1);
      const targetAgents = sourceKey === targetKey ? sourceAgents : [...(prev[targetKey] ?? [])];
      const insertAt = targetIndex ?? targetAgents.length;
      targetAgents.splice(insertAt, 0, agent);

      return {
        ...prev,
        [sourceKey]: sourceAgents,
        ...(sourceKey !== targetKey ? { [targetKey]: targetAgents } : {}),
      };
    });
  },
  []
);
```

### Step 2: Lift DndContext to AgentConfigRow

**File**: `frontend/src/components/board/AgentConfigRow.tsx`

Replace the current column iteration with a `DndContext` wrapper:

```tsx
import { DndContext, DragOverlay, closestCenter, PointerSensor, TouchSensor, KeyboardSensor,
         useSensors, useSensor, type DragStartEvent, type DragEndEvent, type DragOverEvent } from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';

// Inside component:
const [activeAgent, setActiveAgent] = useState<AgentAssignment | null>(null);

const sensors = useSensors(
  useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  useSensor(TouchSensor, { activationConstraint: { delay: 250, tolerance: 5 } }),
  useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
);

// Wrap columns in DndContext:
<DndContext sensors={sensors} collisionDetection={closestCenter}
  onDragStart={handleDragStart} onDragOver={handleDragOver}
  onDragEnd={handleDragEnd} onDragCancel={handleDragCancel}>
  <div className="flex gap-4 overflow-x-auto pb-2">
    {columns.map((col) => (
      <AgentColumnCell key={col.status.option_id} ... />
    ))}
  </div>
  <DragOverlay>
    {activeAgent ? <AgentTile agent={activeAgent} onRemove={() => {}} /> : null}
  </DragOverlay>
</DndContext>
```

### Step 3: Convert AgentColumnCell to Droppable Container

**File**: `frontend/src/components/board/AgentColumnCell.tsx`

Remove the internal `DndContext` and add `useDroppable`:

```tsx
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';

export function AgentColumnCell({ status, agents, ... }: AgentColumnCellProps) {
  const { setNodeRef, isOver } = useDroppable({ id: status });

  return (
    <div ref={setNodeRef}
         className={`... ${isOver ? 'border-primary bg-primary/10' : 'border-border/50'}`}>
      <SortableContext items={agents.map((a) => a.id)} strategy={verticalListSortingStrategy}>
        {/* ... existing tile rendering ... */}
      </SortableContext>
    </div>
  );
}
```

### Step 4: Handle Cross-Column Drag Events

**File**: `frontend/src/components/board/AgentConfigRow.tsx`

Implement the drag event handlers:

```typescript
function findColumnForAgent(agentId: string): string | undefined {
  for (const [status, agents] of Object.entries(localMappings)) {
    if (agents.some((a) => a.id === agentId)) return status;
  }
  return undefined;
}

function handleDragStart(event: DragStartEvent) {
  const agent = /* find agent by event.active.id */;
  setActiveAgent(agent ?? null);
}

function handleDragOver(event: DragOverEvent) {
  const { active, over } = event;
  if (!over) return;
  const sourceCol = findColumnForAgent(active.id as string);
  const targetCol = /* determine from over.id or over.data */;
  if (sourceCol && targetCol && sourceCol !== targetCol) {
    moveAgentToColumn(sourceCol, targetCol, active.id as string);
  }
}

function handleDragEnd(event: DragEndEvent) {
  const { active, over } = event;
  setActiveAgent(null);
  if (!over) return;
  // Handle within-column reorder (same as existing behavior)
  // Cross-column moves already handled in onDragOver
}

function handleDragCancel() {
  setActiveAgent(null);
  // localMappings auto-reverts if onDragOver made preview changes
  // Consider: store snapshot on dragStart and restore on cancel
}
```

### Step 5: Add Visual Feedback

Apply these Tailwind classes during drag:

| State | Element | Classes |
|-------|---------|---------|
| Dragging (source) | Original tile position | `opacity-30 border-dashed` |
| Over valid column | Column container | `border-primary bg-primary/10 ring-2 ring-primary/30` |
| Drag overlay | Floating preview | `shadow-lg opacity-90 rotate-2` |
| Drop complete | Target position | Smooth transition via @dnd-kit transforms |

## Testing Verification

After implementation, verify:

1. **Column alignment**: Open Project Board and Agent Pipeline side by side — columns should match
2. **Vertical reorder**: Drag agent tile up/down within same column — order changes
3. **Cross-column move**: Drag agent tile from one column to another — agent appears in new column
4. **Visual feedback**: During drag, source shows ghost, target column highlights
5. **Save/discard**: After any drag, AgentSaveBar appears; Save persists, Discard reverts
6. **Keyboard**: Focus tile → Space → Arrow keys → Space to drop
7. **Touch**: Long-press tile → drag to new position → release
8. **Cancel**: Drag to empty area → tile returns to original position

## Files Modified

| File | Change Type | Description |
|------|------------|-------------|
| `frontend/src/hooks/useAgentConfig.ts` | Modified | Add `moveAgentToColumn` method |
| `frontend/src/components/board/AgentConfigRow.tsx` | Modified | Lift DndContext, add DragOverlay, cross-column handlers |
| `frontend/src/components/board/AgentColumnCell.tsx` | Modified | Remove internal DndContext, add useDroppable |
| `frontend/src/components/board/AgentDragOverlay.tsx` | New | Optional: dedicated overlay component |
| `frontend/src/components/board/AgentTile.tsx` | Minor | Add ghost styling when isDragging |
