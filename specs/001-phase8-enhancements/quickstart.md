# Quickstart: Phase 8 Feature Enhancements

**Feature**: `001-phase8-enhancements` | **Date**: 2026-03-22

## Overview

This guide provides a rapid onboarding path for implementing the Phase 8 Feature Enhancements. It covers the key implementation touchpoints, dependency order, and verification steps for each user story.

## Prerequisites

- Python 3.12+ with `pip` (backend)
- Node.js 20+ with `npm` (frontend)
- SQLite3 (included with Python)
- GitHub Personal Access Token (for API integration testing)
- Docker (optional, for full-stack local development)

## Quick Setup

```bash
# Clone and navigate
cd solune

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest --co -q  # Verify test collection

# Frontend setup
cd ../frontend
npm install
npm run build  # Verify build
npm run test -- --run  # Verify tests
```

## Implementation Order

Stories should be implemented in dependency order. Stories within the same tier can be parallelized.

```text
Tier 1 (Foundation — no dependencies):
  US-1: Adaptive Polling         ← Backend polling_loop.py + Frontend useAdaptivePolling
  US-4: Pipeline Config Filter   ← Frontend only (BoardToolbar.tsx + useBoardControls.ts)

Tier 2 (Depends on Tier 1 polling):
  US-2: Concurrent Pipelines     ← Backend orchestrator.py + pipeline_state_store.py
  US-3: Board Projection         ← Frontend ProjectBoard.tsx + useBoardProjection hook
  US-5: Label-Driven Recovery    ← Backend recovery.py + label_manager.py

Tier 3 (Depends on US-2 concurrency):
  US-6: MCP Collision Resolution ← Backend mcp_store.py + collision_resolver.py
  US-7: Undo/Redo                ← Frontend UndoRedoContext + Backend soft-delete
```

## Per-Story Implementation Guide

### US-1: Adaptive Polling

**Files to modify**:
- `solune/backend/src/services/copilot_polling/state.py` — Add adaptive interval constants
- `solune/backend/src/services/copilot_polling/polling_loop.py` — Add activity tracking to poll tick
- `solune/frontend/src/hooks/useAdaptivePolling.ts` — New hook (create)
- `solune/frontend/src/hooks/useProjectBoard.ts` — Integrate adaptive refetchInterval

**Key pattern**:
```typescript
// Frontend: useAdaptivePolling.ts
const getRefetchInterval = useCallback(() => {
  if (!isTabVisible) return false; // Pause when tab hidden
  return currentInterval;
}, [isTabVisible, currentInterval]);
```

**Verify**: Open board → observe network tab → polling interval should adapt to activity.

---

### US-2: Concurrent Pipeline Execution

**Files to modify**:
- `solune/backend/src/services/workflow_orchestrator/orchestrator.py` — Add concurrent dispatch
- `solune/backend/src/services/pipeline_state_store.py` — Add `concurrent_group_id` field
- `solune/backend/src/services/copilot_polling/pipeline.py` — Dispatch via task_registry

**Key pattern**:
```python
# Backend: Use task_registry for concurrent dispatch
from src.services.task_registry import task_registry

async def dispatch_concurrent(configs, context, group_id):
    tasks = []
    for config in configs:
        task = task_registry.create_task(
            execute_pipeline(config, context, group_id)
        )
        tasks.append(task)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Handle results with fault isolation
```

**Verify**: Trigger 2 independent pipelines → both should start concurrently (check logs).

---

### US-3: Board Projection (Lazy Loading)

**Files to modify**:
- `solune/frontend/src/hooks/useBoardProjection.ts` — New hook (create)
- `solune/frontend/src/components/board/ProjectBoard.tsx` — Integrate projection
- `solune/frontend/src/components/board/BoardColumn.tsx` — Add intersection observer ref

**Key pattern**:
```typescript
// Frontend: Intersection Observer for lazy column rendering
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        expandRenderedRange(columnId);
      }
    });
  },
  { threshold: 0.1 }
);
```

**Verify**: Load board with 500+ items → initial render should show only visible items (check DOM node count).

---

### US-4: Pipeline Config Filter

**Files to modify**:
- `solune/frontend/src/hooks/useBoardControls.ts` — Add `pipelineConfigId` to `BoardFilterState`
- `solune/frontend/src/components/board/BoardToolbar.tsx` — Add pipeline filter dropdown

**Key pattern**:
```typescript
// Frontend: Pipeline filter dropdown in BoardToolbar
<Select value={filterState.pipelineConfigId ?? 'all'} onValueChange={handlePipelineChange}>
  <SelectItem value="all">All Pipelines</SelectItem>
  {pipelineConfigs.map(config => (
    <SelectItem key={config.id} value={config.id}>{config.name}</SelectItem>
  ))}
</Select>
```

**Verify**: Open board with multiple pipelines → use dropdown → items filter correctly.

---

### US-5: Label-Driven State Recovery

**Files to modify**:
- `solune/backend/src/services/copilot_polling/recovery.py` — Add full state reconstruction
- `solune/backend/src/services/copilot_polling/label_manager.py` — Extend for batch parsing
- `solune/backend/src/services/pipeline_state_store.py` — Add `recovered_at` field

**Key pattern**:
```python
# Backend: State reconstruction from labels
async def recover_pipeline_states_from_labels(project_id, access_token, owner, repo):
    items = await list_project_items(project_id, access_token, owner, repo)
    for item in items:
        labels = [l for l in item.labels if l.startswith("solune:pipeline:")]
        parsed = [parse_label(l) for l in labels]
        state = reconstruct_state(parsed)
        if state.confidence != "ambiguous":
            set_pipeline_state(item.number, state.to_pipeline_state())
```

**Verify**: Clear pipeline state DB → restart backend → check logs for recovery report.

---

### US-6: MCP Collision Resolution

**Files to modify**:
- `solune/backend/src/services/collision_resolver.py` — New module (create)
- `solune/backend/src/services/mcp_store.py` — Add version field + collision detection
- `solune/backend/src/models/mcp.py` — Add version + collision response fields
- `solune/backend/src/api/mcp.py` — Add expected_version to update endpoint

**Verify**: Trigger two concurrent MCP updates → check collision event log.

---

### US-7: Undo/Redo

**Files to modify**:
- `solune/frontend/src/context/UndoRedoContext.tsx` — New context (create)
- `solune/frontend/src/hooks/useUndoRedo.ts` — New hook (create)
- `solune/frontend/src/components/board/ProjectBoardContent.tsx` — Wrap with UndoRedoProvider

**Verify**: Archive an item → click Undo toast → item restored → Ctrl+Shift+Z → item archived again.

## Testing Strategy

```bash
# Backend: Run relevant unit tests
cd solune/backend
pytest tests/unit/test_copilot_polling/ -v      # Polling changes
pytest tests/unit/test_api_pipelines.py -v       # Pipeline concurrency
pytest tests/unit/test_mcp_store.py -v           # Collision detection

# Frontend: Run component tests
cd solune/frontend
npm run test -- --run src/hooks/useAdaptivePolling.test.ts
npm run test -- --run src/hooks/useBoardProjection.test.ts
npm run test -- --run src/components/board/BoardToolbar.test.tsx

# Full suite verification
cd solune/backend && pytest --cov=src --cov-fail-under=75
cd solune/frontend && npm run test:coverage
```

## Architecture Decisions Summary

| Decision | Rationale | See |
|----------|-----------|-----|
| Adaptive polling over WebSockets | Lower risk, extends existing infrastructure | [research.md](./research.md) RT-001 |
| task_registry for concurrent dispatch | Codebase convention, no raw asyncio.create_task | [research.md](./research.md) RT-002 |
| Frontend-only virtualization | Full dataset needed for client-side filtering | [research.md](./research.md) RT-003 |
| Client-side pipeline filtering | No backend changes needed, instant response | [research.md](./research.md) RT-004 |
| Labels as state recovery source | Labels are already source of truth in existing recovery.py | [research.md](./research.md) RT-005 |
| Optimistic concurrency control | Simpler than pessimistic locking, fits CRUD pattern | [research.md](./research.md) RT-006 |
| React Context undo stack | Session-scoped, no backend event sourcing needed | [research.md](./research.md) RT-007 |
