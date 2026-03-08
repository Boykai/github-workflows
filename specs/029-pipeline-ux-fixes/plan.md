# Implementation Plan: Pipeline Page — Fix Model List, Tools Z-Index, Tile Dragging, Agent Clone, and Remove Add Stage

**Branch**: `029-pipeline-ux-fixes` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/029-pipeline-ux-fixes/spec.md`

## Summary

Five targeted fixes to the Pipeline Creation page: (1) Replace the static model list in `PipelineService.list_models()` (backend) and `usePipelineModels` (frontend) with dynamic model fetching from the authenticated user's GitHub account via the existing `modelsApi.list()` / `settingsApi.fetchModels('copilot')` path, which calls the GitHub Models endpoint with the user's auth token — the pipeline-level `PipelineModelDropdown` and per-agent `ModelSelector` already consume `AIModel[]` so the change is at the data source only; (2) fix the CSS stacking context of `ToolSelectorModal` which already renders as a `z-50` fixed overlay but may be clipped by parent `overflow:hidden` or competing stacking contexts — ensure the modal is portaled to `document.body` at `z-[9999]` and not constrained by parent overflow; (3) disable drag-and-drop on `StageCard` (status tiles) by setting `useSortable({ id, disabled: true })` and removing the drag handle, while preserving sortable Agent tiles within each stage; (4) add a "Clone" button to `AgentNode` that deep-copies the agent's configuration (model, tools, parameters) with a new UUID and inserts it into the stage; (5) remove the "Add Stage" button and its `onAddStage` prop from `PipelineBoard`. All changes are frontend-only (5 modified components, 1 modified hook, 1 modified API endpoint) with one backend change (replace static model list with delegation to the existing dynamic model fetcher).

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, react-router-dom v7, TanStack Query v5.90, @dnd-kit (core@6.3 + sortable@10.0), Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — no schema changes needed
**Testing**: Vitest 4 + Testing Library (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers, 1024px minimum viewport width; Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Model list loads within 2s; all UI interactions (clone, drag) respond within 100ms
**Constraints**: No new UI libraries; must not break existing pipeline CRUD, agent management, or MCP tool management; no database schema changes
**Scale/Scope**: ~5 modified frontend components, 1 modified frontend hook, 1 modified backend endpoint, 0 new files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 5 prioritized user stories (P1–P2), Given-When-Then acceptance scenarios, 12 functional requirements (FR-001–FR-012), 10 success criteria, 8 edge cases, 4 key entities, 7 assumptions |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing `modelsApi.list()` for dynamic model fetching instead of new endpoint; extends `@dnd-kit` `disabled` prop instead of new DnD system; `ToolSelectorModal` z-index fix is CSS-only; agent clone uses `structuredClone` + `crypto.randomUUID()` — no new abstractions |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-012) and success criteria (SC-001–SC-010) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure from prior specs |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 task decomposition |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing tests unaffected by changes |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing `modelsApi` (from `useModels` hook) instead of `pipelinesApi.listModels()` — eliminates the static backend list entirely. `ToolSelectorModal` fix is a 2-line CSS change. Stage drag disable is a single prop. Clone is ~15 lines of logic. "Add Stage" removal is pure deletion. No new components, no new abstractions. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/029-pipeline-ux-fixes/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R5)
├── data-model.md        # Phase 1: State changes and type modifications
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── api.md           # Phase 1: API endpoint contract changes
│   └── components.md    # Phase 1: Component interface contract changes
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── pipelines.py                 # MODIFIED: Replace static list_models with dynamic fetch
│   ├── services/
│   │   └── pipelines/
│   │       └── service.py               # MODIFIED: Remove static _AVAILABLE_MODELS list, delegate to model fetcher
│   └── api/
│       └── settings.py                  # UNCHANGED: Existing dynamic model fetching (reused as-is)

frontend/
├── src/
│   ├── pages/
│   │   └── AgentsPipelinePage.tsx        # MODIFIED: Replace usePipelineModels with useModels hook
│   ├── components/
│   │   ├── pipeline/
│   │   │   ├── PipelineBoard.tsx         # MODIFIED: Remove Add Stage button and onAddStage prop; disable stage DnD
│   │   │   ├── StageCard.tsx             # MODIFIED: Remove drag handle, disable useSortable, add locked visual
│   │   │   └── AgentNode.tsx             # MODIFIED: Add Clone button with deep copy logic
│   │   └── tools/
│   │       └── ToolSelectorModal.tsx     # MODIFIED: Increase z-index to z-[9999]
│   ├── hooks/
│   │   ├── useModels.ts                 # UNCHANGED: Existing dynamic model fetching (reused as-is)
│   │   └── usePipelineConfig.ts         # MODIFIED: Remove addStage action; add cloneAgent action
│   └── services/
│       └── api.ts                        # MODIFIED: Remove pipelinesApi.listModels (dead code)
```

**Structure Decision**: Web application (frontend/ + backend/). All changes modify existing files — no new files are created. The primary changes are in the frontend pipeline components directory (`frontend/src/components/pipeline/`) with a minor backend change to delegate model listing from a static list to the existing dynamic model fetcher service. The `modelsApi` (used by `useModels` hook) already fetches from GitHub via `settingsApi.fetchModels('copilot')` — the pipeline page simply switches to this data source.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Reuse `useModels()` hook for pipeline model list | The `useModels` hook already fetches per-user GitHub models via `settingsApi.fetchModels('copilot')` with caching, refresh, and error handling. The `usePipelineModels` hook fetched from a static backend list — simply replacing the data source avoids duplication. | New dedicated pipeline models API endpoint (rejected: duplicates existing dynamic model fetching infrastructure; the static list was the bug) |
| Disable stage DnD via `useSortable({ disabled })` | @dnd-kit/sortable@10 supports a `disabled` prop on `useSortable`. Setting `disabled: true` on all `StageCard` instances prevents drag without removing the component from the `SortableContext` (which is needed for layout). | Remove `DndContext` entirely (rejected: would require significant refactoring and may break future drag requirements); `canDrag` guard (rejected: not available in @dnd-kit — that's a react-dnd concept) |
| `structuredClone` for agent deep copy | Built-in browser API (supported in all target browsers) that handles nested objects, arrays, and primitive values. Avoids JSON.parse(JSON.stringify()) which doesn't handle undefined values or Date objects. | `lodash.cloneDeep` (rejected: unnecessary dependency); JSON round-trip (rejected: loses undefined values and is slower for complex objects) |
