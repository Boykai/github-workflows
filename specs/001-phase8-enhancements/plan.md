# Implementation Plan: Phase 8 Feature Enhancements — Polling, UX, Board Projection, Concurrency, Collision Fix, Undo/Redo

**Branch**: `001-phase8-enhancements` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-phase8-enhancements/spec.md`

## Summary

Implement six cross-cutting enhancements to the Solune platform: (1) adaptive polling that adjusts frequency based on board activity and applies exponential backoff on failures, (2) concurrent pipeline execution with fault isolation while respecting queue-mode serialization, (3) lazy-loaded board projection for large boards with client-side caching, (4) a pipeline config filter dropdown in BoardToolbar for client-side filtering, (5) label-driven state recovery to reconstruct pipeline state from GitHub labels after restarts, (6) MCP collision detection and resolution with last-write-wins + user-priority semantics, and (7) session-scoped undo/redo for destructive board actions with a configurable time window.

The backend changes center on extending the existing `copilot_polling` service with adaptive interval logic, enabling concurrent pipeline dispatch in `workflow_orchestrator`, adding label-based state reconstruction in `recovery.py`, and introducing collision detection in `mcp_store.py`. The frontend changes add an adaptive polling hook wrapping TanStack Query's `refetchInterval`, a virtualized/lazy-loaded board via intersection observers, a pipeline filter dropdown in `BoardToolbar.tsx`, and a React context-based undo/redo stack.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.x + React 19 (frontend)  
**Primary Dependencies**: FastAPI ≥0.135, TanStack Query ≥5.91, Radix UI, @dnd-kit, Vite 8, aiosqlite, githubkit ≥0.14.6  
**Storage**: SQLite (async via aiosqlite) with BoundedDict L1 in-memory cache  
**Testing**: pytest + pytest-asyncio (backend, 75% coverage), Vitest + happy-dom (frontend, 50/44/41/50 thresholds), Playwright (E2E)  
**Target Platform**: Linux server (Docker), modern browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web application (backend + frontend monorepo under `solune/`)  
**Performance Goals**: Board initial render ≤2s for 500 items, scroll batch load ≤500ms, poll updates visible within 5s during active periods, 50% polling resource reduction during idle  
**Constraints**: Backward-compatible with queue-mode serialization, no breaking API changes, undo window default 30s configurable  
**Scale/Scope**: Boards with up to 500+ items, 3+ concurrent independent pipelines per project

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md contains 7 prioritized user stories (P1–P3) with Given-When-Then acceptance scenarios, clear scope boundaries, and independent test criteria |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Plan phase generates well-defined artifacts (research.md, data-model.md, contracts/, quickstart.md) as inputs for subsequent task/implement phases |
| **IV. Test Optionality** | ✅ PASS | Spec does not mandate TDD. Tests are optional unless implementation phase decides otherwise. Existing test infrastructure (pytest, Vitest) is available |
| **V. Simplicity & DRY** | ✅ PASS | Design extends existing services (copilot_polling, workflow_orchestrator, pipeline_state_store) rather than introducing new architectural layers. No premature abstraction |
| **Branch/Dir Naming** | ✅ PASS | `001-phase8-enhancements` follows `###-short-name` convention |
| **Phase-Based Execution** | ✅ PASS | Specify phase complete (spec.md exists). Plan phase in progress. Tasks phase deferred to `/speckit.tasks` |
| **Independent Stories** | ✅ PASS | All 7 user stories are independently implementable and testable per spec |

**Gate Result**: ✅ ALL GATES PASS — Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-phase8-enhancements/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── polling-api.yaml
│   ├── pipeline-api.yaml
│   ├── board-api.yaml
│   ├── recovery-api.yaml
│   ├── collision-api.yaml
│   └── undo-redo-api.yaml
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── pipelines.py          # Pipeline API (extend for concurrency)
│   │   │   ├── mcp.py                # MCP API (extend for collision resolution)
│   │   │   ├── health.py             # Health/readiness probes
│   │   │   └── board.py              # Board API (extend for projection/lazy load)
│   │   ├── models/
│   │   │   ├── mcp.py                # MCP models (extend for collision events)
│   │   │   └── pipeline.py           # Pipeline models
│   │   └── services/
│   │       ├── copilot_polling/
│   │       │   ├── polling_loop.py    # Polling lifecycle (extend for adaptive intervals)
│   │       │   ├── pipeline.py        # Pipeline execution (extend for concurrency)
│   │       │   ├── recovery.py        # Recovery logic (extend for label-driven state)
│   │       │   ├── label_manager.py   # Label operations (extend for state reconstruction)
│   │       │   ├── state.py           # Polling state constants (extend for adaptive config)
│   │       │   └── state_validation.py
│   │       ├── pipeline_state_store.py  # State store (extend for concurrent pipelines)
│   │       ├── mcp_store.py             # MCP store (extend for collision detection)
│   │       ├── workflow_orchestrator/
│   │       │   ├── orchestrator.py      # Orchestrator (extend for concurrent dispatch)
│   │       │   ├── transitions.py       # State transitions
│   │       │   └── models.py            # Workflow models
│   │       └── task_registry.py         # Fire-and-forget task management
│   └── tests/
│       └── unit/
│           ├── test_api_pipelines.py
│           ├── test_mcp_store.py
│           └── test_api_mcp.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── board/
│   │   │   │   ├── ProjectBoard.tsx       # Main board (extend for lazy loading)
│   │   │   │   ├── BoardToolbar.tsx        # Toolbar (add pipeline filter dropdown)
│   │   │   │   ├── BoardColumn.tsx         # Column (extend for virtualization)
│   │   │   │   ├── IssueCard.tsx           # Issue card
│   │   │   │   ├── ProjectBoardContent.tsx # Content wrapper
│   │   │   │   └── BoardColumnSkeleton.tsx # Loading state
│   │   │   └── common/
│   │   │       └── InfiniteScrollContainer.tsx  # Existing infinite scroll
│   │   ├── hooks/
│   │   │   ├── useProjectBoard.ts         # Board data fetching (extend for adaptive polling)
│   │   │   ├── useBoardControls.ts        # Filter/sort/group (extend for pipeline filter)
│   │   │   ├── useBoardRefresh.ts         # Board refresh (extend for adaptive)
│   │   │   └── useBoardDragDrop.ts        # Drag-drop logic
│   │   ├── services/
│   │   │   ├── api.ts                     # API client
│   │   │   └── schemas/
│   │   │       ├── board.ts               # Board schema types
│   │   │       └── pipeline.ts            # Pipeline schema types
│   │   └── lib/
│   │       └── icons.ts                   # Icon barrel (add new icons here)
│   └── tests/
│       └── (vitest unit tests)
└── docs/
```

**Structure Decision**: Web application structure (Option 2). The existing `solune/backend/` and `solune/frontend/` directories are the primary targets. All changes extend existing modules — no new top-level directories are introduced.

## Constitution Check — Post-Design Re-evaluation

*Re-check after Phase 1 design artifacts are complete.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts (research.md, data-model.md, contracts/, quickstart.md) trace back to spec.md user stories and requirements |
| **II. Template-Driven** | ✅ PASS | plan.md follows plan-template.md structure. All generated artifacts use consistent markdown formatting |
| **III. Agent-Orchestrated** | ✅ PASS | Plan phase outputs are well-defined inputs for the tasks phase. Each contract maps to specific user stories |
| **IV. Test Optionality** | ✅ PASS | No tests mandated. Quickstart includes testing commands but they are informational, not required |
| **V. Simplicity & DRY** | ✅ PASS | All designs extend existing modules (copilot_polling, workflow_orchestrator, pipeline_state_store, mcp_store). No new architectural layers. Frontend changes use existing patterns (TanStack Query, Radix UI, sonner). Only two new service files: `collision_resolver.py` and `UndoRedoContext.tsx` — both are single-responsibility modules with clear interfaces |
| **Independent Stories** | ✅ PASS | Implementation order (quickstart.md) shows 3 tiers with no hidden cross-story dependencies. Each story can be implemented and tested independently |
| **Phase Ordering** | ✅ PASS | Plan phase complete. Tasks phase (next) will consume these artifacts |

**Post-Design Gate Result**: ✅ ALL GATES PASS — Ready for `/speckit.tasks`.

## Complexity Tracking

> No constitution violations detected. All changes extend existing services and follow established patterns.
