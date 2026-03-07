# Implementation Plan: Pipeline Page — MCP Tool Selection, Model Override, Flow Graph Cards, Preset Configs & Agent Stamp Isolation

**Branch**: `028-pipeline-mcp-config` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/028-pipeline-mcp-config/spec.md`

## Summary

Extend the existing pipeline builder (`AgentsPipelinePage`) and its backend (`pipeline_configs` table, `PipelineService`) with five capability tiers: (1) per-agent MCP tool selection via a lightweight flyout that reuses the existing `ToolSelectorModal` component and persists tool IDs inside each `PipelineAgentNode`, with strict agent stamp isolation so the source agent's global config is never mutated; (2) a pipeline-level model override dropdown (including "Auto") at the top of the builder that batch-updates all agents within the pipeline session; (3) always-enabled Save with inline validation (red borders + helper text on missing required fields like pipeline name); (4) enriched Saved Workflows and Recent Activity cards showing stages, per-agent models, tool counts, and a compact inline flow graph (custom SVG renderer); (5) two preset pipeline configurations ("Spec Kit" and "GitHub Copilot") seeded as system presets with visual differentiation, plus project-level pipeline assignment that auto-injects pipeline metadata on new GitHub Issues. The implementation extends existing `PipelineAgentNode` with a `tool_ids` field and optional `tool_count`, adds an `is_preset` + `preset_id` flag to `pipeline_configs`, introduces a `project_pipeline_assignment` column in `project_settings`, and adds ~6 new/modified frontend components. All changes build on the established patterns from specs 026-pipeline-crud and 027-mcp-tools-page.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, react-router-dom v7, TanStack Query v5.90, @dnd-kit (core + sortable), Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — extending `pipeline_configs` table with preset flags and `PipelineAgentNode` with `tool_ids`; adding `assigned_pipeline_id` column to `project_settings`
**Testing**: Vitest 4 + Testing Library (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers, 1024px minimum viewport width; Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: MCP tool selector loads within 2s (SC-009); pipeline creation under 5 minutes (SC-001); CRUD operations persist across page reloads; flow graph renders within card layout without performance degradation
**Constraints**: No new UI libraries beyond what is installed; must not break existing pipeline CRUD, agent management, or MCP tool management; agent stamp isolation is non-negotiable (FR-006); under 100 saved workflows per project
**Scale/Scope**: ~6 new/modified frontend components, ~2 modified hooks, 1 new migration, 2 modified backend services, 2 modified API routers, 1 new preset seed config

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 13 functional requirements (FR-001–FR-013), 10 success criteria, 7 edge cases, 6 key entities, 6 assumptions |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Extends existing pipeline CRUD (026) and MCP tool system (027); reuses `ToolSelectorModal`, `usePipelineConfig`, `useTools`; no new UI libraries; flow graph uses simple custom SVG (no React Flow dependency — YAGNI for read-only mini graphs) |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-013) and success criteria (SC-001–SC-010) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure from prior specs |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 task decomposition |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing tests unaffected by additive schema changes (new columns with defaults, new table rows) |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing `ToolSelectorModal` for MCP tool selection (no new modal). Extends `PipelineAgentNode` with `tool_ids` rather than creating a new junction table. Custom SVG flow graph avoids heavy dependency. Preset configs seeded from static JSON — no new migration framework. Pipeline-level model override is a thin wrapper around existing per-agent `ModelSelector`. Agent stamp isolation achieved by never writing back to `agent_configs` from pipeline save path. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/028-pipeline-mcp-config/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R10)
├── data-model.md        # Phase 1: Entity extensions, types, schema changes
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── api.md           # Phase 1: REST API endpoint contracts (new + modified)
│   └── components.md    # Phase 1: Component interface contracts (new + modified)
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── pipelines.py                 # MODIFIED: Add preset seeding endpoint, pipeline assignment
│   │   └── tools.py                     # UNCHANGED: Existing tool CRUD (reused as-is)
│   ├── models/
│   │   └── pipeline.py                  # MODIFIED: Extend PipelineAgentNode with tool_ids; add preset fields
│   ├── services/
│   │   ├── pipelines/
│   │   │   └── service.py               # MODIFIED: Add preset seeding, assignment logic, tool count
│   │   └── github_projects/
│   │       └── service.py               # MODIFIED: Inject pipeline metadata on issue creation
│   └── migrations/
│       └── 015_pipeline_mcp_presets.sql  # NEW: Add preset columns + project pipeline assignment
└── tests/
    └── unit/                            # Existing tests — no changes expected

frontend/
├── src/
│   ├── pages/
│   │   └── AgentsPipelinePage.tsx        # MODIFIED: Add pipeline-level model dropdown, validation states
│   ├── components/
│   │   ├── pipeline/
│   │   │   ├── PipelineBoard.tsx         # MODIFIED: Add tool selection trigger per agent, model override
│   │   │   ├── AgentNode.tsx             # MODIFIED: Show tool count badge, model display
│   │   │   ├── StageCard.tsx             # MODIFIED: Wire tool selector flyout per agent
│   │   │   ├── SavedWorkflowsList.tsx    # MODIFIED: Enhanced cards with agent details + flow graph
│   │   │   ├── PipelineToolbar.tsx       # MODIFIED: Always-enabled Save with validation
│   │   │   ├── PipelineFlowGraph.tsx     # NEW: Compact SVG flow graph component
│   │   │   ├── PipelineModelDropdown.tsx # NEW: Pipeline-level model override dropdown
│   │   │   └── PresetBadge.tsx           # NEW: Visual badge for preset pipelines
│   │   └── tools/
│   │       └── ToolSelectorModal.tsx     # MODIFIED: Accept pipeline context for scoped selection
│   ├── hooks/
│   │   ├── usePipelineConfig.ts          # MODIFIED: Add tool_ids management, validation, preset loading
│   │   └── useTools.ts                   # UNCHANGED: Existing tool list fetching (reused as-is)
│   ├── services/
│   │   └── api.ts                        # MODIFIED: Add preset seeding + pipeline assignment endpoints
│   ├── types/
│   │   └── index.ts                      # MODIFIED: Extend PipelineAgentNode, add preset types
│   └── data/
│       └── preset-pipelines.ts           # NEW: Static preset pipeline definitions (Spec Kit, GitHub Copilot)
```

**Structure Decision**: Web application (frontend/ + backend/). Extends the existing pipeline components directory (`frontend/src/components/pipeline/`) and backend pipeline service (`backend/src/services/pipelines/`). New components (`PipelineFlowGraph`, `PipelineModelDropdown`, `PresetBadge`) are added to the existing `pipeline/` directory. No new top-level directories needed. Preset definitions are stored as a static TypeScript module in `frontend/src/data/` and as a JSON seed in the backend migration, following the simplest possible approach per Constitution Principle V.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Embed `tool_ids` in `PipelineAgentNode` JSON | Tool selections are pipeline-scoped and always loaded/saved as part of the pipeline document; a separate junction table is unnecessary overhead | Separate `pipeline_agent_tools` junction table (rejected: requires JOINs for every pipeline load, overengineered for document-oriented pipeline storage) |
| Custom SVG flow graph (no React Flow) | Flow graphs on cards are read-only, small (~200px wide), and structurally simple (linear stage progression); React Flow adds 150KB+ for features we don't need | React Flow in read-only mode (rejected: heavy dependency for a simple read-only visualization); D3.js (rejected: even heavier, overkill for node-edge diagrams) |
| Static preset definitions (no admin UI) | "Spec Kit" and "GitHub Copilot" presets are system-seeded with known configurations; an admin interface for managing presets is YAGNI | Backend admin API for preset CRUD (rejected: premature abstraction, only 2 presets needed) |
| Pipeline-level model stored in session only | The pipeline-level model dropdown is a convenience that batch-updates agents; no separate `pipeline_model` column needed since each agent stores its own model | Dedicated `pipeline_model` column (rejected: redundant — the individual agent model fields already capture the state after batch update) |
