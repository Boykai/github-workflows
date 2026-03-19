# Contract: Kanban Board Drag-and-Drop (Phase 3)

**Feature**: 050-frontend-ux-improvements  
**Requirements**: FR-011 through FR-017  
**Dependencies**: `@dnd-kit/core` ^6.3.1 (existing), `@dnd-kit/sortable` ^10.0.0 (existing), `@dnd-kit/modifiers` ^9.0.0 (existing)

## Component Contracts

### `ProjectBoard.tsx` Modification

**Location**: `solune/frontend/src/components/board/ProjectBoard.tsx`  
**Action**: Wrap the board grid with DndContext and DragOverlay.

```tsx
import { DndContext, DragOverlay, closestCorners, PointerSensor, KeyboardSensor, useSensor, useSensors } from '@dnd-kit/core';
import { useBoardDnd } from '@/hooks/useBoardDnd';
import { IssueDragOverlay } from './IssueDragOverlay';

// Inside ProjectBoard component:
const { activeCard, handlers } = useBoardDnd(boardData, onStatusUpdate);

const sensors = useSensors(
  useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  useSensor(KeyboardSensor)
);

return (
  <DndContext
    sensors={sensors}
    collisionDetection={closestCorners}
    onDragStart={handlers.onDragStart}
    onDragOver={handlers.onDragOver}
    onDragEnd={handlers.onDragEnd}
    onDragCancel={handlers.onDragCancel}
  >
    <div className="grid gap-5 ..." style={{ gridTemplateColumns: ... }}>
      {columns.map(column => (
        <BoardColumn key={column.status} column={column} ... />
      ))}
    </div>
    <DragOverlay>
      {activeCard ? <IssueDragOverlay item={activeCard} /> : null}
    </DragOverlay>
  </DndContext>
);
```

### `BoardColumn.tsx` Modification

**Location**: `solune/frontend/src/components/board/BoardColumn.tsx`  
**Action**: Make each column a drop target using `useDroppable`.

```tsx
import { useDroppable } from '@dnd-kit/core';

// Inside BoardColumn:
const { setNodeRef, isOver } = useDroppable({
  id: `column-${column.status}`,
  data: { status: column.status },
});

// Apply highlight when dragging over:
<div
  ref={setNodeRef}
  className={cn(
    'project-board-column pipeline-column-surface ...',
    isOver && 'ring-2 ring-primary/50 bg-primary/5'  // FR-015: target column highlighting
  )}
>
```

### `IssueCard.tsx` Modification

**Location**: `solune/frontend/src/components/board/IssueCard.tsx`  
**Action**: Make each card draggable using `useDraggable`.

```tsx
import { useDraggable } from '@dnd-kit/core';

// Inside IssueCard:
const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
  id: item.id,
  data: { item, status: column.status },
});

// Apply dimming when dragging:
<div
  ref={setNodeRef}
  {...attributes}
  {...listeners}
  className={cn(
    'cursor-grab active:cursor-grabbing ...',
    isDragging && 'opacity-30'  // FR-015: source card dims
  )}
>
```

### `IssueDragOverlay.tsx` (NEW)

**Location**: `solune/frontend/src/components/board/IssueDragOverlay.tsx`  
**Pattern**: Follow `AgentDragOverlay.tsx` structure.

```tsx
interface IssueDragOverlayProps {
  item: BoardItem;
}

// Renders a simplified card preview:
// - Title (truncated)
// - Status badge
// - Label pills (max 3)
// - Assignee avatars
// Styling: shadow-lg opacity-80 cursor-grabbing border-primary/50 bg-card
```

### `useBoardDnd.ts` (NEW Hook)

**Location**: `solune/frontend/src/hooks/useBoardDnd.ts`

```tsx
interface UseBoardDndReturn {
  activeCard: BoardItem | null;
  handlers: BoardDndHandlers;
}

function useBoardDnd(
  boardData: BoardDataResponse,
  onStatusUpdate: (itemId: string, fromStatus: string, toStatus: string) => void
): UseBoardDndReturn;
```

**Behavior**:
1. `onDragStart`: Set `activeCard` and `sourceColumn` from drag event data.
2. `onDragOver`: Set `overColumn` for visual feedback.
3. `onDragEnd`: 
   - If `fromColumn === toColumn` → no-op (FR-016).
   - Else → call `onStatusUpdate` for optimistic update + API call.
4. `onDragCancel`: Reset all DnD state.

### API Integration

**Location**: `solune/frontend/src/services/api.ts`  
**New function**:

```tsx
updateBoardItemStatus(
  projectId: string,
  itemId: string,
  status: string
): Promise<void> {
  return request(`/projects/${projectId}/board/items/${itemId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}
```

**Optimistic Update Pattern** (TanStack Query):

```tsx
const mutation = useMutation({
  mutationFn: ({ itemId, status }) => api.updateBoardItemStatus(projectId, itemId, status),
  onMutate: async ({ itemId, fromStatus, toStatus }) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: boardKeys.data(projectId) });
    // Snapshot previous value
    const previous = queryClient.getQueryData(boardKeys.data(projectId));
    // Optimistically move card between columns
    queryClient.setQueryData(boardKeys.data(projectId), (old) => moveCard(old, itemId, fromStatus, toStatus));
    return { previous };
  },
  onError: (err, vars, context) => {
    // FR-014: Roll back on error
    queryClient.setQueryData(boardKeys.data(projectId), context?.previous);
    toast.error('Failed to move issue');
  },
  onSuccess: () => {
    toast.success('Issue moved');
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: boardKeys.data(projectId) });
  },
});
```

## Accessibility

- FR-017: `KeyboardSensor` from `@dnd-kit/core` enables keyboard-based drag-and-drop.
  - Enter/Space: Activate drag mode on focused card.
  - Arrow keys: Move between columns.
  - Enter: Drop card in current position.
  - Escape: Cancel drag.
- ARIA announcements: `@dnd-kit` provides built-in `aria-describedby` instructions and live region updates during drag.
