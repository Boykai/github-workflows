# Implementation Plan: Pipeline Page — CRUD for Agent Pipeline Configurations with Model Selection and Saved Workflow Management

**Branch**: `026-pipeline-crud` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/026-pipeline-crud/spec.md`

## Summary

Add full CRUD operations for Agent Pipeline configurations on the existing pipeline page (`/pipeline`). Users can create named pipelines with ordered stages, assign agents to each stage with per-agent model selection via a context-aware model picker, and persist configurations to a new `pipeline_configs` SQLite table via REST endpoints (`GET/POST/PUT/DELETE /api/v1/pipelines/:id`). Saved workflows are displayed at the bottom of the page as cards; clicking one loads the full configuration into the board in edit mode. The frontend extends the existing `AgentsPipelinePage` with new components (`PipelineBoard`, `StageCard`, `AgentNode`, `ModelSelector`, `SavedWorkflowsList`, `PipelineToolbar`) and a `usePipelineConfig` hook built on TanStack Query, following the established modal + card + hook patterns. Unsaved changes protection, drag-and-drop stage reordering (via existing `@dnd-kit`), and contextual toolbar states round out the UX.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, react-router-dom v7, TanStack Query v5.90, @dnd-kit (core + sortable), Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — new `pipeline_configs` table for saved pipeline configurations
**Testing**: Vitest 4 + Testing Library (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers, 1024px minimum viewport width; Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Board load < 2s (SC-002); CRUD operations complete and persist across page reloads (SC-003); model picker selection < 15s (SC-006)
**Constraints**: No new UI libraries beyond what is installed; must not break existing pipeline drag-and-drop or workflow automation; under 100 saved workflows per project for initial release
**Scale/Scope**: ~8 new/modified frontend components, ~2 new hooks, 1 new backend service, 1 new migration, 4 new REST endpoints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 22 functional requirements, 10 success criteria, edge cases |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Extends existing patterns (hook + card + modal CRUD); reuses @dnd-kit, TanStack Query; new `pipeline_configs` table follows established migration pattern |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-022) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing tests unaffected |
| **V. Simplicity/DRY** | ✅ PASS | Reuses `AvailableAgent` discovery, existing drag-and-drop infrastructure, established API patterns. New `ModelSelector` component is reusable. No unnecessary abstractions. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/026-pipeline-crud/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R8)
├── data-model.md        # Phase 1: Entity definitions, types, state machines
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── api.md           # Phase 1: REST API endpoint contracts
│   └── components.md    # Phase 1: Component interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── pipelines.py                 # NEW: CRUD endpoints for pipeline configs
│   ├── models/
│   │   └── pipeline.py                  # NEW: Pydantic models (PipelineConfig, Stage, etc.)
│   ├── services/
│   │   └── pipelines/
│   │       ├── __init__.py              # NEW: Re-exports
│   │       └── service.py               # NEW: PipelineService (CRUD + validation)
│   └── migrations/
│       └── 013_pipeline_configs.sql     # NEW: pipeline_configs table
├── tests/
│   └── unit/                            # Existing tests — no changes expected

frontend/
├── src/
│   ├── pages/
│   │   └── AgentsPipelinePage.tsx        # MODIFIED: Integrate PipelineBoard + SavedWorkflowsList
│   ├── components/
│   │   └── pipeline/                    # NEW directory
│   │       ├── PipelineBoard.tsx        # NEW: Main board canvas (stages + agents)
│   │       ├── PipelineToolbar.tsx      # NEW: Create/Save/Delete/Discard actions
│   │       ├── StageCard.tsx            # NEW: Stage container with agents
│   │       ├── AgentNode.tsx            # NEW: Agent card within a stage
│   │       ├── ModelSelector.tsx        # NEW: Reusable model picker popover
│   │       ├── SavedWorkflowsList.tsx   # NEW: List of saved pipeline configs
│   │       └── UnsavedChangesDialog.tsx # NEW: Confirmation dialog
│   ├── hooks/
│   │   ├── usePipelineConfig.ts         # NEW: Pipeline CRUD state management
│   │   └── useModels.ts                 # NEW: Model list fetching + caching
│   ├── services/
│   │   └── api.ts                       # MODIFIED: Add pipeline API client methods
│   └── types/
│       └── index.ts                     # MODIFIED: Add pipeline-related types
```

**Structure Decision**: Web application (frontend/ + backend/). The repo already has `frontend/` and `backend/` directories. A new `frontend/src/components/pipeline/` directory is added for pipeline CRUD components, following the existing pattern of domain-scoped component directories (`agents/`, `board/`, `chores/`). A new `backend/src/services/pipelines/` service directory follows the pattern of `agents/` and `chores/` services. The existing `AgentsPipelinePage.tsx` is modified to compose the new components.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| New `pipeline_configs` table | Pipeline configs are distinct from `workflow_config` in `project_settings`; separate table enables per-pipeline CRUD, list queries, and independent lifecycle | Storing as JSON array in `project_settings.workflow_config` (rejected: mixing concerns, no individual record IDs, harder to query/paginate) |
| Reuse `AvailableAgent` for agent assignment | Agents in pipeline stages reference the same agents from the existing discovery system | Creating separate agent entities for pipelines (rejected: duplication, YAGNI) |
| Model metadata as static config + API | Model list served from a backend config/endpoint, cached on frontend | Hardcoded model list in frontend (rejected: harder to maintain, no single source of truth) |
