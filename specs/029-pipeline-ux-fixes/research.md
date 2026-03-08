# Research: Pipeline Page — Fix Model List, Tools Z-Index, Tile Dragging, Agent Clone, and Remove Add Stage

**Feature**: 029-pipeline-ux-fixes | **Date**: 2026-03-07

## R1: Dynamic Model List — Data Source Strategy

**Task**: Determine how to replace the static model list in the pipeline page with dynamically fetched per-user GitHub models, given the existing `modelsApi.list()` and `pipelinesApi.listModels()` code paths.

**Decision**: Replace the `usePipelineModels()` hook in `AgentsPipelinePage.tsx` (which calls `pipelinesApi.listModels()` → backend static list) with the existing `useModels()` hook (which calls `modelsApi.list()` → `settingsApi.fetchModels('copilot')` → `GET /settings/models/copilot` → GitHub Models API with user auth token). Remove the now-dead `pipelinesApi.listModels()` frontend method and the backend `GET /pipelines/models/available` endpoint that returned the static list.

**Rationale**: The codebase already has two model-fetching paths:

1. **`pipelinesApi.listModels()`** — Calls `GET /api/v1/pipelines/models/available` → `PipelineService.list_models()` → returns a hardcoded `_AVAILABLE_MODELS` list of 6 models (GPT-4o, GPT-4o Mini, Claude Sonnet 4, Claude 3.5 Haiku, Gemini 2.5 Pro, Gemini 2.5 Flash). This is the **bug** — this list doesn't reflect per-user model availability.

2. **`modelsApi.list()`** — Calls `settingsApi.fetchModels('copilot')` → `GET /api/v1/settings/models/copilot` → `ModelFetcherService.get_models('copilot', token=user_token)` → GitHub Models API. This returns the actual models available to the authenticated user's account. It already has caching (`staleTime: Infinity`), refresh support, and error handling via TanStack Query.

The `useModels()` hook wraps path #2 and is already used by `ModelSelector.tsx` (the per-agent model picker in the pipeline). The `usePipelineModels()` hook wraps path #1 and is used only by `AgentsPipelinePage.tsx` to pass `availableModels` to `PipelineBoard` → `PipelineModelDropdown`. By switching `AgentsPipelinePage` to use `useModels()`, both the pipeline-level dropdown and the per-agent selector will share the same data source — the user's actual GitHub models.

**Alternatives Considered**:
- **Modify the backend static list to match GitHub models**: Rejected — the static list would need to be updated whenever GitHub adds models, and it still wouldn't reflect per-user availability (different plans have different model access).
- **Create a new backend endpoint that proxies to GitHub**: Rejected — the existing `GET /settings/models/copilot` endpoint already does this. Creating another one violates DRY.
- **Keep `usePipelineModels` but change its data source**: Rejected — adds unnecessary indirection. `useModels()` already provides the exact interface (`models: AIModel[]`, `isLoading`, `error`).

---

## R2: Tools Module Z-Index — Stacking Context Analysis

**Task**: Investigate why the `ToolSelectorModal` is hidden behind other pipeline elements and determine the correct fix.

**Decision**: The `ToolSelectorModal` already renders as a `fixed inset-0 z-50` overlay (line 75 of `ToolSelectorModal.tsx`). However, it is **not portaled** to `document.body` — it renders inline within the `StageCard` component tree. The `StageCard` is inside a `DndContext` which may establish a stacking context via transforms (`CSS.Transform.toString(transform)` on line 54). The fix is twofold:

1. **Increase z-index** from `z-50` to `z-[9999]` on the ToolSelectorModal backdrop.
2. **Portal the modal** to `document.body` using `createPortal()` (already imported in `StageCard.tsx` for the agent picker). This escapes any parent stacking contexts created by the DnD transform or parent `overflow:hidden`.

**Rationale**: CSS stacking contexts are created by elements with `transform`, `opacity`, `will-change`, or explicit `z-index`. The `StageCard` applies `transform` from `useSortable` (line 54: `CSS.Transform.toString(transform)`), which creates a new stacking context. Any `z-index` on children (including `fixed` positioned children) is resolved within that stacking context, not the document root. Portaling to `document.body` escapes this entirely. The `ModelSelector` popover already uses `createPortal(... , document.body)` (line 236 of `ModelSelector.tsx`) and the `StageCard` agent picker also uses `createPortal` (line 209) — this is an established pattern.

**Alternatives Considered**:
- **Just increase z-index**: Rejected alone — z-index within a stacking context only competes with siblings in the same context. The DnD transform on `StageCard` creates a stacking context that caps the effective z-index of its children.
- **Remove transform from StageCard**: Rejected — the transform is essential for DnD visual feedback.
- **Render ToolSelectorModal at the page level**: Considered but more invasive — would require lifting state to `PipelineBoard` or `AgentsPipelinePage`. Portaling from `StageCard` is the minimal change.

---

## R3: Stage Drag-and-Drop Disabling — @dnd-kit Strategy

**Task**: Determine how to lock Status tiles (stages) in place while keeping Agent tiles draggable, using @dnd-kit.

**Decision**: Disable stage drag-and-drop entirely by passing `disabled: true` to `useSortable()` in `StageCard.tsx` and removing the drag handle UI (the `GripVertical` button). The `DndContext` and `SortableContext` in `PipelineBoard.tsx` can be simplified or retained as a no-op wrapper. Additionally, remove the `onStagesChange` / `reorderStages` prop usage since stages should no longer be reorderable.

**Rationale**: In @dnd-kit/sortable v10, the `useSortable` hook accepts a `disabled` option (boolean or `{ draggable: boolean, droppable: boolean }`) that prevents the element from being dragged or acting as a drop target. Setting `disabled: true` on all stage cards:
- Prevents drag initiation on stages
- Removes the grab cursor affordance
- Keeps the layout intact (unlike removing from `SortableContext`)

The spec says "Status tiles must not be moveable" and "the Agent tiles should be moveable." In the current architecture, "Status tiles" are the `StageCard` components (representing pipeline stages like "Triage", "In Progress"), and "Agent tiles" are the `AgentNode` components within each stage. Currently, only stages are sortable via DnD — agent nodes within stages are not draggable (they're static list items). The spec's request to make "Agent tiles moveable" within the current iteration means keeping them editable (add/remove/clone) rather than drag-sortable, since no agent-level DnD currently exists.

**Alternatives Considered**:
- **`canDrag` guard**: Not available in @dnd-kit — that's a `react-dnd` concept.
- **Remove `DndContext` entirely**: Viable and simpler — since all stages are now non-draggable, the DnD wrapper serves no purpose. However, removing it is a larger refactor that changes the component tree. The `disabled` approach is more surgical and preserves the infrastructure if agent-level DnD is added later.
- **Conditional `disabled` per tile type**: Not needed — all stage cards should be locked. If future requirements need selectively draggable stages, the `disabled` prop can be parameterized.

---

## R4: Agent Clone — Deep Copy Strategy

**Task**: Determine how to implement agent cloning with full independence (deep copy) and unique identification.

**Decision**: Add a "Clone" button to `AgentNode.tsx` that calls a new `onClone` callback prop. The parent `StageCard` handles the clone logic:

1. `structuredClone(agentNode)` — creates a deep copy of the `PipelineAgentNode` object (handles nested `tool_ids` array, `config` object, etc.)
2. Assign a new `id` via `crypto.randomUUID()`
3. Append the cloned agent to the same stage's `agents` array via the existing `onUpdateAgent` mechanism (or a new `onCloneAgent` callback that adds to the stage)

The `usePipelineConfig` hook needs a new `cloneAgentInStage(stageId: string, agentNodeId: string)` action that:
1. Finds the target agent node in the specified stage
2. Deep clones it with a new UUID
3. Appends to the stage's agents array
4. Triggers dirty state

**Rationale**: `structuredClone` is a built-in browser API (available in all modern browsers) that handles:
- Nested objects and arrays (e.g., `tool_ids: string[]`, `config: Record<string, unknown>`)
- Primitive values, dates, maps, sets
- Circular references (unlikely here but handled)

It avoids the pitfalls of `JSON.parse(JSON.stringify())` (loses `undefined`, `Date` objects, functions) and doesn't require an external dependency like `lodash.cloneDeep`. The `PipelineAgentNode` type contains only JSON-serializable fields (strings, numbers, arrays of strings, plain objects), so `structuredClone` is ideal.

**Alternatives Considered**:
- **`JSON.parse(JSON.stringify())`**: Rejected — while it would work for the current data shape, it's fragile against future type additions and has known edge cases.
- **`lodash.cloneDeep`**: Rejected — adds a dependency for something the platform provides natively.
- **Spread operator**: Rejected — only shallow copies; `tool_ids` array and `config` object would be shared references.
- **Manual field-by-field copy**: Rejected — verbose, error-prone, requires updates when fields are added.

---

## R5: Add Stage Removal — Impact Analysis

**Task**: Verify that removing the "Add Stage" button has no dependent features or side effects.

**Decision**: Remove both "Add Stage" buttons from `PipelineBoard.tsx` (lines 165-172 for empty state, lines 253-260 for normal state) and the `onAddStage` prop. Also remove the `addStage` method from `usePipelineConfig.ts` if no other callers exist, and remove the `onAddStage` prop from `AgentsPipelinePage.tsx`.

**Rationale**: The "Add Stage" button was part of the original pipeline CRUD implementation (spec 026). The current architecture initializes pipeline stages from the project's board columns when `newPipeline()` is called (see `AgentsPipelinePage.tsx` line 108: `const initialStageNames = columns.map((column) => column.status.name)`). This means stages are derived from the project board and should not be manually added during pipeline creation. The "Add Stage" button created a potential inconsistency where pipeline stages could diverge from board columns.

Code analysis confirms:
- `onAddStage` is only called from `PipelineBoard.tsx` (2 occurrences)
- `pipelineConfig.addStage()` is only referenced in `AgentsPipelinePage.tsx` line 220 (`onAddStage={() => pipelineConfig.addStage()}`)
- No other components or hooks reference `addStage`
- The `addStage` method in `usePipelineConfig.ts` can be safely removed (or retained as dead code for potential future use — recommend removal per YAGNI)

**Alternatives Considered**:
- **Hide the button behind a feature flag**: Rejected — the spec explicitly says "remove" and there's no indication this feature will return.
- **Keep `addStage` in the hook but remove UI**: Acceptable minimalist approach — retains the capability in the state management layer. Recommended if future specs might re-enable it. However, per Constitution Principle V (YAGNI), full removal is preferred.
- **Replace with a disabled button showing explanation**: Rejected — adds complexity for a feature that shouldn't exist in the UI at all.
