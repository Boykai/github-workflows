# Research: Align Agent Pipeline Columns with Project Board Status & Enable Drag/Drop

**Feature**: `023-pipeline-dragdrop` | **Date**: 2026-03-06

## Research Task 1: Column Alignment Between Agent Pipeline and Project Board

### Decision
The Agent Pipeline columns are **already structurally aligned** with the Project Board Status columns. Both views consume the same data source: `boardData.columns` fetched from the backend's `GET /board/projects/{project_id}` endpoint.

### Rationale
- `AgentConfigRow` receives `columns={boardData.columns}` (from `ProjectBoardPage.tsx`)
- Each column maps to a `StatusOption` with `option_id`, `name`, and `color` from the GitHub Projects V2 status field
- The column order is determined by the GitHub Projects V2 API response (`status_field.options` array order)
- Both the `ProjectBoard` and `AgentConfigRow` iterate over the same `columns` array, ensuring identical naming and ordering

### Alternatives Considered
- Separate column configuration for Agent Pipeline: Rejected — would introduce drift and require synchronization logic
- Hard-coded column names: Rejected — the current dynamic approach automatically reflects Project Board changes

### Outstanding Concern
- When the Project Board adds/removes columns while `agent_mappings` reference old column names, orphaned mappings can occur. The `useAgentConfig` hook already handles case-insensitive key matching but does not clean up mappings for deleted columns. This is an edge case noted in the spec (EC-6) and should be addressed with a mapping cleanup step during config load.

---

## Research Task 2: @dnd-kit Cross-Column Drag-and-Drop Patterns

### Decision
Use `@dnd-kit/core` with multiple `useDroppable` zones (one per column) wrapped in a single `DndContext` at the `AgentConfigRow` level, combined with `@dnd-kit/sortable` for within-column ordering.

### Rationale
The current implementation has a **per-column** `DndContext` in `AgentColumnCell.tsx` with `restrictToVerticalAxis` modifier. This architecture prevents cross-column dragging because each `DndContext` is isolated. The standard @dnd-kit pattern for multi-container drag-and-drop is:

1. **Single DndContext** wrapping all containers (columns)
2. **Multiple `SortableContext`** instances (one per column) with `useDroppable` on each column
3. **DragOverlay** for the visual preview of the dragged item
4. **Custom collision detection** or `closestCenter`/`rectIntersection` to determine the target column
5. **`onDragStart`**: Record source column and index
6. **`onDragOver`**: Move item between containers as cursor crosses column boundaries (live preview)
7. **`onDragEnd`**: Finalize position, update state

### Key Implementation Details
- **Remove `restrictToVerticalAxis` modifier**: This currently locks drag to vertical only; removing it enables horizontal movement
- **Replace per-column DndContext**: Move the single DndContext up to `AgentConfigRow`
- **Use `DragOverlay`**: Renders a floating copy of the dragged tile outside the DOM flow, preventing layout shifts
- **Collision detection**: `closestCenter` works well for column-based layouts; alternatively `pointerWithin` for pointer-position-based detection
- **Container identification**: Each `SortableContext` gets a unique ID (the status column name), and `useDroppable` on each column container registers it as a valid drop target

### @dnd-kit Version Compatibility
- `@dnd-kit/core` ^6.3.1 — supports `DragOverlay`, `useDroppable`, multiple `SortableContext`
- `@dnd-kit/sortable` ^10.0.0 — supports `sortableKeyboardCoordinates`, `verticalListSortingStrategy`
- No new packages needed; all cross-column functionality is available in the installed versions

### Alternatives Considered
- `react-beautiful-dnd`: Rejected — in maintenance mode (Atlassian), @dnd-kit already installed
- `react-dnd` (react-dnd/react-dnd): Rejected — more complex API, @dnd-kit already in use
- Custom HTML5 drag-and-drop: Rejected — poor mobile/touch support, accessibility concerns

---

## Research Task 3: State Management for Cross-Column Moves

### Decision
Extend the existing `useAgentConfig` hook with a `moveAgentToColumn(sourceStatus, targetStatus, agentId, targetIndex?)` method that operates on `localMappings`.

### Rationale
The current `useAgentConfig` hook manages `localMappings: Record<string, AgentAssignment[]>` with methods for add, remove, and reorder. The dirty-state tracking (`isDirty`) and save/discard workflow already handle the persistence path (`PUT /workflow/config`). Adding a cross-column move is a natural extension:

1. Remove the agent from `localMappings[sourceStatus]`
2. Insert the agent into `localMappings[targetStatus]` at the specified index
3. The existing `isDirty` detection triggers `AgentSaveBar` visibility
4. The user clicks "Save" to persist via `PUT /workflow/config`

This maintains the existing UX pattern: changes are local until explicitly saved (or discarded).

### Alternatives Considered
- Auto-save on each drag: Rejected — breaks the existing batch-save UX pattern and would require new API endpoints for individual moves
- Separate state for drag operations: Rejected — duplicates state management; the existing `localMappings` is the correct place

---

## Research Task 4: Visual Feedback During Drag Operations

### Decision
Use @dnd-kit's built-in `DragOverlay` component for the floating preview, CSS classes for drop zone highlighting, and insertion line indicators via conditional rendering.

### Rationale
@dnd-kit provides:
- **`DragOverlay`**: Renders a portal-based floating element that follows the cursor; avoids layout shifts
- **`useSortable` → `isDragging`**: Boolean flag on the source item, used to apply a "ghost" style (opacity: 0.3)
- **`useDroppable` → `isOver`**: Boolean flag on drop targets, used to highlight valid drop zones
- **Active drag data**: Available via `useDndMonitor` or the `onDragOver` callback for custom indicators

### Visual Feedback Plan
| State | Visual Treatment |
|-------|-----------------|
| Drag start | Source card gets `opacity-30` ghost; `DragOverlay` shows semi-transparent copy following cursor |
| Over valid column | Column border changes to `border-primary` with `bg-primary/10` background |
| Over specific position | Insertion line (2px `bg-primary` divider) appears between cards |
| Over invalid area | No indicator; cursor stays default |
| Drop complete | Card animates to new position via @dnd-kit's built-in `transform` transitions |
| Drop cancelled | Card animates back to original position |

### Alternatives Considered
- Custom overlay rendering without DragOverlay: Rejected — requires manual portal management and positioning
- HTML5 drag image: Rejected — limited styling control, no animation support

---

## Research Task 5: Keyboard and Touch Accessibility

### Decision
Use @dnd-kit's built-in keyboard sensor with `sortableKeyboardCoordinates` for keyboard navigation, and the existing `PointerSensor` for touch support (already handles both mouse and touch events).

### Rationale
- **Keyboard**: @dnd-kit's `KeyboardSensor` with `sortableKeyboardCoordinates` already supports arrow-key movement within a `SortableContext`. For cross-column movement, a custom `coordinateGetter` or keyboard shortcut handler is needed to move focus between columns.
- **Touch**: @dnd-kit's `PointerSensor` handles touch events natively. The `activationConstraint: { distance: 5 }` prevents accidental drags from taps. Touch long-press support can be added via `TouchSensor` with `activationConstraint: { delay: 250, tolerance: 5 }`.

### Implementation Plan
1. Add `TouchSensor` alongside existing `PointerSensor` and `KeyboardSensor`
2. For keyboard cross-column movement: implement custom key handlers (Left/Right arrow when in "movable" mode) that call `moveAgentToColumn`
3. Add ARIA attributes: `role="listbox"` on columns, `role="option"` on tiles, `aria-grabbed`, `aria-dropeffect`

### Alternatives Considered
- Custom keyboard handler from scratch: Rejected — @dnd-kit provides the building blocks
- Separate touch library: Rejected — @dnd-kit handles touch via PointerSensor/TouchSensor

---

## Research Task 6: Error Handling and Rollback

### Decision
Leverage the existing `useAgentConfig` dirty-state and discard workflow for rollback on failed saves. For visual rollback during drag, @dnd-kit's animation handles returning items to their pre-drag positions automatically when `onDragCancel` fires.

### Rationale
- **Drag cancellation** (drop outside valid zone): @dnd-kit automatically animates the item back to its original position
- **Save failure** (`PUT /workflow/config` returns error): The `save()` function in `useAgentConfig` already shows a toast notification on failure; the `localMappings` remain in the modified state, and the user can either retry or discard
- **Concurrent edits**: Out of scope for initial implementation. The existing workflow config save is a full-object PUT, so last-write-wins semantics apply. WebSocket-based live sync could be added later.

### Alternatives Considered
- Per-drag API calls with automatic rollback: Rejected — complex, breaks existing batch-save pattern
- Server-side optimistic locking: Rejected — over-engineering for current scale
