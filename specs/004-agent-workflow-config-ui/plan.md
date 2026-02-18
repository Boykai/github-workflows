# Implementation Plan: Custom Agent Workflow Configuration UI

**Branch**: `004-agent-workflow-config-ui` | **Date**: 2026-02-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-agent-workflow-config-ui/spec.md`

## Summary

Add an interactive agent configuration UI to the Project Board page — a collapsible row above the issue columns where users can assign, reorder (via `@dnd-kit` drag-and-drop), and remove agents per status column. Includes a local-first save/discard workflow with visual diff indicators, a backend endpoint for discovering available Custom GitHub Agents from the selected repository, three built-in preset configurations (Custom, GitHub Copilot, Spec Kit), and pass-through support for statuses with no agents. The `agent_mappings` data model is migrated from `dict[str, list[str]]` to `dict[str, list[AgentAssignment]]` with UUID-based instance identity and per-assignment extensibility.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript ~5.4 (frontend)
**Primary Dependencies**: FastAPI ≥0.109, Pydantic ≥2.5, httpx ≥0.26 (backend); React 18.3, @tanstack/react-query ^5.17, `@dnd-kit/core` + `@dnd-kit/sortable` (new, frontend)
**Storage**: In-memory dict (`_workflow_configs` in `workflow_orchestrator.py`); no database
**Testing**: pytest + pytest-asyncio (backend); vitest + @testing-library/react (frontend); Playwright (E2E)
**Target Platform**: Linux server (Docker Compose), web browser
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Agent row render <2s; save round-trip <2s p95; drag animation <300ms
**Constraints**: No new database; backward-compatible API; accessible drag-and-drop (keyboard)
**Scale/Scope**: Single-user at a time per session; 5-15 status columns; ≤10 agents per column (soft limit)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md complete with 9 prioritized user stories, clarifications, acceptance scenarios |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | specify → plan → tasks → implement phase sequence followed |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; test tasks omitted per Test Optionality principle. Test file paths below are optional guidance for implementers |
| V. Simplicity/DRY | ✅ PASS | Extends existing `WorkflowConfiguration` model; reuses existing API patterns; `@dnd-kit` is purpose-built (no over-engineering). UUID instance IDs are the simplest solution for duplicate agent identity. |

## Project Structure

### Documentation (this feature)

```text
specs/004-agent-workflow-config-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── chat.py              # AgentAssignment model, updated WorkflowConfiguration
│   ├── services/
│   │   ├── github_projects.py   # New: list_available_agents() method
│   │   └── workflow_orchestrator.py  # Updated: pass-through logic for empty statuses
│   └── api/
│       └── workflow.py          # New: GET /agents endpoint
└── tests/
    └── unit/
        ├── test_workflow_agents.py   # Tests for agents endpoint
        └── test_agent_mappings.py    # Tests for AgentAssignment serialization

frontend/
├── src/
│   ├── components/
│   │   └── board/
│   │       ├── AgentConfigRow.tsx      # Collapsible row container
│   │       ├── AgentColumnCell.tsx      # Per-column agent stack + dnd-kit sortable
│   │       ├── AgentTile.tsx            # Card-style tile with expand, remove
│   │       ├── AddAgentPopover.tsx      # Dropdown popover for adding agents
│   │       ├── AgentPresetSelector.tsx  # Preset buttons + confirmation dialog
│   │       └── AgentSaveBar.tsx         # Floating save/discard bar
│   ├── hooks/
│   │   └── useAgentConfig.ts    # Local agent state, dirty tracking, save/discard
│   ├── types/
│   │   └── index.ts             # AgentAssignment type, updated WorkflowConfiguration
│   └── pages/
│       └── ProjectBoardPage.tsx # Integration: passes boardData to AgentConfigRow
└── tests/
    └── unit/
        └── useAgentConfig.test.ts  # Hook unit tests
```

**Structure Decision**: Web application structure (Option 2) — matches existing `backend/` + `frontend/` layout. New components live under `frontend/src/components/board/` alongside existing board components. New hook in `frontend/src/hooks/`. Backend changes are minimal — one new endpoint and model updates in existing files.

## Complexity Tracking

> No constitution violations identified. No complexity justifications needed.

## Constitution Re-Check (Post-Design)

*Re-evaluated after Phase 1 design artifacts were generated.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md was completed and clarified before any design artifacts were created |
| II. Template-Driven | ✅ PASS | plan.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md all follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Phase sequence respected: specify → clarify → plan (current). Tasks and implementation deferred to later phases |
| IV. Test Optionality | ✅ PASS | No tests mandated. Test file locations documented in project structure for implementer convenience |
| V. Simplicity/DRY | ✅ PASS | (a) `BeforeValidator` reuses existing Pydantic v2 patterns — no custom framework. (b) `get_agent_slugs()` helper minimizes downstream migration diff. (c) One `DndContext` per column (simplest isolation). (d) No new database — stays in-memory. (e) `DEFAULT_AGENT_MAPPINGS` unchanged — auto-promoted at runtime. (f) New dependency `@dnd-kit` is purpose-built for the exact drag-and-drop requirement |

**Result**: All gates pass. No complexity justifications needed. Ready for Phase 2 (`/speckit.tasks`).
