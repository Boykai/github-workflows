# Data Model: Pipeline Page — Fix Model List, Tools Z-Index, Tile Dragging, Agent Clone, and Remove Add Stage

**Feature**: 029-pipeline-ux-fixes | **Date**: 2026-03-07

## Overview

This feature requires **no schema changes** and **no new entities**. All changes operate on existing data structures. The modifications are:

1. **Data source change**: Pipeline model list switches from static backend list to dynamic per-user GitHub models (same `AIModel` type)
2. **State management change**: Add `cloneAgentInStage` action; remove `addStage` action from `usePipelineConfig` hook
3. **Component prop changes**: New `onClone` prop on `AgentNode`; remove `onAddStage` from `PipelineBoard`; add `disabled` to stage sortable

## Existing Entities (Unchanged Schema)

### PipelineAgentNode (NO CHANGES)

The agent node type is already sufficient for cloning. `structuredClone` produces a complete copy.

```typescript
interface PipelineAgentNode {
  id: string;                    // UUID — replaced with new UUID on clone
  agent_slug: string;            // Copied as-is
  agent_display_name: string;    // Copied as-is
  model_id: string;              // Copied as-is (deep copy independent)
  model_name: string;            // Copied as-is
  tool_ids: string[];            // Copied as new array (deep copy independent)
  tool_count: number;            // Copied as-is
  config: Record<string, unknown>; // Deep copied (nested objects independent)
}
```

**Clone behavior**: `structuredClone(agentNode)` creates a fully independent copy. The clone's `id` is replaced with `crypto.randomUUID()`. All array and object fields (`tool_ids`, `config`) are new instances — mutations to the clone do not affect the original.

### PipelineStage (NO CHANGES)

```typescript
interface PipelineStage {
  id: string;
  name: string;
  order: number;
  agents: PipelineAgentNode[];  // Clone target: new agent appended here
}
```

### AIModel (NO CHANGES — different source)

```typescript
interface AIModel {
  id: string;                           // e.g., "gpt-4o", "claude-sonnet-4"
  name: string;                         // e.g., "GPT-4o", "Claude Sonnet 4"
  provider: string;                     // e.g., "OpenAI", "Anthropic", "Google"
  context_window_size?: number;         // e.g., 128000, 200000, 1000000
  cost_tier?: 'economy' | 'standard' | 'premium';
  capability_category?: string;         // e.g., "general", "coding"
}
```

**Data source change**: Currently the pipeline page fetches models from `GET /api/v1/pipelines/models/available` which returns a hardcoded list of 6 models. After this fix, it will use the existing `modelsApi.list()` path which fetches from `GET /api/v1/settings/models/copilot` — this calls the GitHub Models API with the user's auth token and returns only models available to that user's account.

**Note**: The `modelsApi.list()` currently maps response models to `{ id, name, provider }` only (line 909-913 of `api.ts`), dropping `context_window_size` and `cost_tier`. The `PipelineModelDropdown` groups by `provider` and does not use `context_window_size` or `cost_tier`. The per-agent `ModelSelector` uses `useModels()` which returns full model data. After this change, both dropdowns will use `useModels()` data, so full metadata will be available everywhere.

## State Management Changes

### UsePipelineConfigReturn (MODIFIED)

```typescript
interface UsePipelineConfigReturn {
  // ... existing fields unchanged ...

  // REMOVED
  // addStage: (name?: string) => void;  // FR-012: Remove Add Stage

  // ADDED
  cloneAgentInStage: (stageId: string, agentNodeId: string) => void;  // FR-009, FR-010
}
```

### New Action: `cloneAgentInStage`

```typescript
const cloneAgentInStage = useCallback((stageId: string, agentNodeId: string) => {
  setPipeline((prev) => {
    if (!prev) return null;
    const stage = prev.stages.find((s) => s.id === stageId);
    if (!stage) return prev;
    const sourceAgent = stage.agents.find((a) => a.id === agentNodeId);
    if (!sourceAgent) return prev;

    const clonedAgent: PipelineAgentNode = {
      ...structuredClone(sourceAgent),
      id: crypto.randomUUID(),
    };

    return {
      ...prev,
      stages: prev.stages.map((s) =>
        s.id === stageId
          ? { ...s, agents: [...s.agents, clonedAgent] }
          : s,
      ),
    };
  });
}, []);
```

**Behavior**:
- Finds the source agent by `stageId` + `agentNodeId`
- Deep copies all fields via `structuredClone` (model, tools, config)
- Assigns a new UUID via `crypto.randomUUID()`
- Appends the clone after the last agent in the same stage
- Triggers dirty state detection (existing `isDirty` mechanism via snapshot comparison)

### Removed Action: `addStage`

The `addStage` callback and its usage in the return object are removed. The `buildStage` helper function can be retained (it's also used by `newPipeline`).

## Component Prop Changes

### PipelineBoardProps (MODIFIED)

```typescript
interface PipelineBoardProps {
  // REMOVED
  // onAddStage: () => void;

  // ADDED
  onCloneAgent: (stageId: string, agentNodeId: string) => void;

  // ... all other props unchanged ...
}
```

### StageCardProps (MODIFIED)

```typescript
interface StageCardProps {
  // ADDED
  onCloneAgent: (agentNodeId: string) => void;

  // ... all other props unchanged ...
}
```

### AgentNodeProps (MODIFIED)

```typescript
interface AgentNodeProps {
  // ADDED
  onClone: () => void;

  // ... all other props unchanged ...
}
```

## Backend Changes

### PipelineService.list_models (MODIFIED → REMOVED)

The `list_models()` static method and `_AVAILABLE_MODELS` constant are removed from `backend/src/services/pipelines/service.py`. The `GET /pipelines/models/available` endpoint in `backend/src/api/pipelines.py` is redirected to use the existing `ModelFetcherService` via `GET /settings/models/copilot`, or the endpoint is removed entirely since the frontend will no longer call it.

**Recommended approach**: Remove the endpoint since no frontend code will call it after the change. This avoids maintaining dead code.

## Validation Rules

No new validation rules. Existing validation in `usePipelineConfig` (pipeline name required, stages non-empty) is unchanged. The clone operation inherits all validation state from the source agent — if the source was valid, the clone is valid.

## Migration

No database migration required. All changes are in application code (frontend components, hooks, and one backend endpoint).
