# Research: Reinvent Agent Pipeline Creation UX

**Feature Branch**: `037-pipeline-builder-ux`
**Date**: 2026-03-12
**Input**: [spec.md](./spec.md), [plan.md](./plan.md)

## 1. Cross-Column Drag-and-Drop with @dnd-kit

### Decision
Lift the `DndContext` from `StageCard` to `PipelineBoard` to enable cross-stage agent movement. Use a single board-level `DndContext` with multiple `SortableContext` providers (one per `ExecutionGroup`).

### Rationale
The current implementation places a `DndContext` inside each `StageCard`, which scopes drag-and-drop to within a single stage. Lifting the context to `PipelineBoard` is the standard @dnd-kit pattern for cross-container sortable lists. This approach:

- Requires no additional libraries (stays within @dnd-kit/core + @dnd-kit/sortable)
- Enables a single `onDragEnd` handler to detect source/target containers and perform cross-group moves
- Supports `DragOverlay` for smooth visual feedback during cross-column drags
- Maintains keyboard accessibility through @dnd-kit's built-in `KeyboardSensor`

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Multiple DndContexts with shared state | @dnd-kit does not support drag events across separate DndContexts; workarounds are fragile |
| react-beautiful-dnd | Deprecated and unmaintained; incompatible with React 19 concurrent mode |
| Custom HTML5 drag-and-drop | Poor keyboard accessibility; inconsistent cross-browser behavior; significantly more code |
| Keep DnD within-stage only, add move-to-stage dropdown | Violates FR-005 (single-gesture cross-column move) and degrades UX vs. drag-and-drop |

### Implementation Pattern

```tsx
// PipelineBoard.tsx — board-level DndContext
<DndContext
  sensors={sensors}
  collisionDetection={closestCenter}
  onDragStart={handleDragStart}
  onDragOver={handleDragOver}
  onDragEnd={handleDragEnd}
  onDragCancel={handleDragCancel}
>
  {stages.map(stage => (
    <StageCard key={stage.id} stage={stage}>
      {stage.groups.map(group => (
        <SortableContext
          key={group.id}
          items={group.agents.map(a => a.id)}
          strategy={group.execution_mode === 'parallel'
            ? rectSortingStrategy
            : verticalListSortingStrategy}
        >
          <ExecutionGroupCard group={group} />
        </SortableContext>
      ))}
    </StageCard>
  ))}
  <DragOverlay>
    {activeAgent && <AgentNode agentNode={activeAgent} isDragOverlay />}
  </DragOverlay>
</DndContext>
```

The `onDragEnd` handler resolves source and target containers by mapping agent IDs to their containing group/stage. When source ≠ target, the handler removes the agent from the source group and inserts it at the drop index in the target group.

---

## 2. ExecutionGroup Data Model Design

### Decision
Add an `ExecutionGroup` entity as a child of `PipelineStage`. Each group has its own `id`, `execution_mode`, and ordered `agents[]` array. The stage's top-level `agents` and `execution_mode` fields are retained for backward compatibility during migration but are deprecated in the new format.

### Rationale
The spec defines four key entities: Pipeline Config, Stage, Execution Group, and Agent Node. The current model has Stage → Agent Node (flat). The new model inserts Execution Group between Stage and Agent Node:

```
PipelineConfig → Stage[] → ExecutionGroup[] → AgentNode[]
```

This directly maps to the spec's requirements:
- FR-001: Multiple groups per stage
- FR-002: Independent execution mode per group
- FR-011: Persist group structure
- FR-019: Groups execute top-to-bottom within a stage

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Encode groups as metadata on agents (e.g., `group_id` field) | Requires grouping logic at render time; execution order ambiguous; harder to persist group-level properties |
| Replace `PipelineStage` with a new `GroupedStage` type | Breaking change; requires migrating all presets, API consumers, and tests simultaneously |
| Nested stages (stages within stages) | Over-engineered; spec only requires one level of grouping |

### Key Design Details
- `ExecutionGroup.id` uses the same `generateId()` utility as stages and agents
- `ExecutionGroup.order` determines top-to-bottom execution sequence within a stage
- When a stage has zero groups, it implicitly has one empty default group (edge case from spec)
- The `execution_mode` on `PipelineStage` becomes derived from the first group for backward compat display

---

## 3. Backward-Compatible Migration Strategy

### Decision
Implement a pure function `migratePipelineToGroupFormat(config: PipelineConfig): PipelineConfig` that runs at load time in the frontend. The function detects legacy format (no `groups` array on stages) and wraps each stage's flat `agents[]` into a single `ExecutionGroup` with the stage's original `execution_mode`.

### Rationale
- The spec explicitly requires backward compatibility (US-6, FR-012, SC-004)
- Pipelines are persisted as JSON blobs in SQLite; there is no relational schema to migrate
- A frontend-only migration avoids a backend migration script and database downtime
- The migration is idempotent: running it on an already-migrated pipeline is a no-op
- On save, the pipeline is persisted in the new group format, completing the migration

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Backend batch migration script | Adds deployment complexity; requires downtime or careful rollout; frontend still needs migration for in-flight unsaved pipelines |
| Dual-format support forever | Increases code complexity; every feature must handle two formats; technical debt |
| Backend migration on read | Duplicates migration logic in Python; synchronisation risk if frontend and backend migrate differently |

### Migration Algorithm

```typescript
function migratePipelineToGroupFormat(config: PipelineConfig): PipelineConfig {
  return {
    ...config,
    stages: config.stages.map(stage => {
      // Already migrated — has groups array
      if (stage.groups && stage.groups.length > 0) return stage;

      // Legacy format — wrap agents in a single group
      return {
        ...stage,
        groups: [{
          id: generateId(),
          order: 0,
          execution_mode: stage.execution_mode ?? 'sequential',
          agents: stage.agents ?? [],
        }],
        // Keep agents for backward compat but mark as deprecated
        agents: stage.agents ?? [],
      };
    }),
  };
}
```

---

## 4. Per-Group Execution Mode Toggle UX

### Decision
Each `ExecutionGroupCard` renders a toggle button in its header that switches between "series" and "parallel". The toggle uses the existing icon pattern (`GitBranch` for parallel, `ArrowDown` or similar for series) and updates the group's `execution_mode` via the existing state management pattern.

### Rationale
- The spec requires a single-interaction toggle (FR-004)
- The current UI already has an execution mode indicator on stages; moving it to groups is a natural evolution
- Using a button (not a dropdown) minimises interaction cost
- The layout change (vertical list ↔ side-by-side grid) provides immediate visual feedback

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Dropdown select (series / parallel / auto) | Extra "auto" mode not in spec; dropdown requires two clicks vs. one for toggle |
| Context menu | Hidden interaction; violates FR-004's "single interaction" requirement |
| Drag-to-rearrange to imply mode | Ambiguous; users can't tell if rearranging agents or changing mode |

---

## 5. @dnd-kit Collision Detection for Nested Containers

### Decision
Use `closestCenter` collision detection at the board level with custom `onDragOver` logic to handle container switching. When the pointer enters a different `SortableContext`, the `onDragOver` event fires and the handler moves the agent's ID to the new container's items array, providing real-time visual feedback.

### Rationale
@dnd-kit's built-in `closestCenter` works well for flat lists but needs supplementation for nested containers. The `onDragOver` pattern (moving items between containers during hover, not just on drop) is the recommended approach from @dnd-kit documentation for multi-container sortable scenarios.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| `closestCorners` collision | Less intuitive for card-based layouts; `closestCenter` feels more natural for agent cards |
| `rectIntersection` collision | Too sensitive; triggers container switches too eagerly during quick drags |
| Custom collision detection | Unnecessary complexity; standard `closestCenter` + `onDragOver` handles the use case |

---

## 6. State Management for Group Operations

### Decision
Extend the existing `usePipelineBoardMutations` hook with group-level operations: `addGroupToStage`, `removeGroupFromStage`, `reorderGroupsInStage`, `setGroupExecutionMode`, and `moveAgentBetweenGroups`. All mutations follow the existing `setPipeline` callback pattern using functional state updates.

### Rationale
- The existing pattern (`useCallback` + `setPipeline`) is well-established and consistent
- Adding group mutations alongside existing stage/agent mutations keeps the API surface cohesive
- No new state management library is needed (stays with React state + TanStack Query)

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Zustand store for pipeline state | Adds a dependency; the existing `useReducer` + functional updates pattern is sufficient |
| Redux Toolkit | Heavy-weight for this use case; inconsistent with rest of codebase |
| Separate `usePipelineGroupMutations` hook | Fragments the API; callers would need to coordinate two hooks |

---

## 7. Backend Model Extension

### Decision
Add an `ExecutionGroup` Pydantic model to `backend/src/models/pipeline.py`. Update `PipelineStage` to include an optional `groups: list[ExecutionGroup]` field. The backend normalisation function (`_normalize_execution_modes`) is updated to work at the group level. The field is optional to maintain backward compatibility with API consumers that send the old format.

### Rationale
- The backend must validate and persist the group structure (FR-011)
- Making `groups` optional means existing API consumers (including tests) continue working without changes
- The normalization function already handles execution mode consistency; extending it to groups is a natural fit
- No DDL migration needed — pipelines are stored as JSON blobs in SQLite

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Backend-only migration (rewrite JSON on disk) | Risk of data loss if migration has bugs; harder to test |
| Separate database table for groups | Over-normalised for a JSON-blob storage pattern; adds join complexity |
| Accept any shape and validate only in frontend | Violates defense-in-depth; backend should validate what it persists |

---

## 8. Keyboard Accessibility for Cross-Column DnD

### Decision
Use @dnd-kit's built-in `KeyboardSensor` with `sortableKeyboardCoordinates` (already configured in `StageCard`). Extend with a custom keyboard coordinate getter that understands the board's two-dimensional layout (stages as columns, groups as rows within columns) so arrow keys navigate logically across the grid.

### Rationale
- The spec requires full keyboard accessibility (FR-018, SC-005)
- @dnd-kit provides `KeyboardSensor` out of the box; the current code already uses it for within-stage reordering
- A custom coordinate getter maps arrow keys to the board layout: ←/→ for cross-stage, ↑/↓ for within-group
- This approach requires no additional accessibility libraries

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Separate "move agent" modal with keyboard controls | Adds a disruptive interaction; spec requires same gesture for mouse and keyboard |
| Browser-native focus management only | Insufficient for complex drag-and-drop; doesn't support positional reordering |
| react-aria DnD | Different library; would conflict with existing @dnd-kit setup; unnecessary migration |
