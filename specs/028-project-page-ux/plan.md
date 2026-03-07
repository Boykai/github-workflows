# Implementation Plan: Project Page — Agent Pipeline UX Overhaul, Drag/Drop Fixes, Issue Rendering & Layout Improvements

**Branch**: `028-project-page-ux` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/028-project-page-ux/spec.md`

## Summary

Overhaul the project page's Agent Pipeline and kanban board to achieve production-quality UX: fix drag/drop teleportation and interaction bugs by correcting @dnd-kit offset handling, restyle the agent pipeline to match the subtle Pipeline Stages design, display agent metadata (model/tools) and auto-format names, add a saved pipeline configuration selector that persists to new issues, render issue descriptions as Markdown, filter sub-issues from the Done column, remove the Add Column button, and unify the layout alignment between pipeline and kanban using a shared grid.

## Technical Context

**Language/Version**: TypeScript 5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, @dnd-kit/core 6.3.1, @dnd-kit/sortable 10.0.0, TanStack Query 5.90, FastAPI, Tailwind CSS 4, react-markdown (new), remark-gfm (new)
**Storage**: SQLite with WAL mode (aiosqlite) — agent_configs, pipeline_configs tables
**Testing**: Vitest (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Docker Compose (Linux containers), nginx reverse proxy
**Project Type**: Web application (FastAPI backend + React frontend)
**Performance Goals**: ≥30 fps drag interaction, <500ms pipeline config switch, <200ms Markdown render for typical issue bodies
**Constraints**: No new drag/drop library (fix existing @dnd-kit usage); Markdown library must be lightweight and safe (XSS-free); no backend schema changes required
**Scale/Scope**: ~12 frontend files modified/created, ~3 backend files modified; board size 10–200 cards across 3–7 columns

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — PASS

Feature work began with explicit specification (spec.md) containing 7 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios for each story, clear scope boundaries, edge case analysis for name formatting and drag/drop, and 11 measurable success criteria.

### II. Template-Driven Workflow — PASS

All artifacts follow canonical templates: spec.md from spec-template, plan.md from plan-template. No custom sections added without justification.

### III. Agent-Orchestrated Execution — PASS

Workflow follows the specify → plan → tasks → implement sequence. Each phase produces specific outputs and hands off to the next agent. The plan phase generates research.md, data-model.md, contracts/, and quickstart.md before proceeding.

### IV. Test Optionality with Clarity — PASS

The spec does not mandate specific test types. Tests are included only for the `formatAgentName` utility function (pure function with defined edge cases) and for the sub-issue filtering logic (critical data correctness requirement). Existing test suites serve as regression gates. Frontend visual changes are validated manually against reference screenshots.

### V. Simplicity and DRY — PASS

Changes use existing patterns: @dnd-kit is already in the dependency tree (fix configuration, not replace library); Tailwind CSS classes match existing Pipeline Stages reference; `formatAgentName` is a single pure utility function. Two new dependencies (react-markdown, remark-gfm) are the standard minimal stack for safe Markdown rendering in React. No new abstractions or architecture changes.

**GATE RESULT: ALL PASS — proceed to Phase 0.**

### Post-Phase 1 Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All 13 FRs traced to design artifacts and contracts |
| II. Template-Driven | ✅ PASS | All plan artifacts follow templates |
| III. Agent-Orchestrated | ✅ PASS | Plan → tasks → implement pipeline maintained |
| IV. Test Optionality | ✅ PASS | Unit tests for formatAgentName utility and sub-issue filter; manual validation for visual/DnD changes |
| V. Simplicity/DRY | ✅ PASS | Two new dependencies (react-markdown, remark-gfm) justified; no new abstractions; fix existing DnD configuration rather than replacing library |

## Project Structure

### Documentation (this feature)

```text
specs/028-project-page-ux/
├── plan.md              # This file
├── spec.md              # Feature specification (complete)
├── research.md          # Phase 0: Technical research and decisions
├── data-model.md        # Phase 1: Entity and type definitions
├── quickstart.md        # Phase 1: Verification commands
├── contracts/           # Phase 1: Component and API contracts
│   ├── components.md    # Frontend component contracts
│   └── api.md           # Backend API contract changes
├── checklists/
│   └── requirements.md  # Quality checklist (complete)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── utils/
│   │   └── formatAgentName.ts           # FR-003,004: Pure utility for agent name formatting
│   ├── components/
│   │   └── board/
│   │       ├── AgentConfigRow.tsx        # FR-001,010,011,012,013: DnD fixes, restyling, layout alignment
│   │       ├── AgentColumnCell.tsx       # FR-011,012: DnD offset fix, drop target indicator
│   │       ├── AgentTile.tsx             # FR-002,003: Model/tool metadata, formatted names
│   │       ├── AgentDragOverlay.tsx      # FR-003: Formatted name in drag overlay
│   │       ├── AgentPresetSelector.tsx   # FR-005: Pipeline config selector (extend with saved configs)
│   │       ├── ProjectBoard.tsx          # FR-009,010: Remove Add Column, shared grid layout
│   │       ├── BoardColumn.tsx           # FR-010: Flex width for shared grid alignment
│   │       └── IssueDetailModal.tsx      # FR-008: Markdown rendering for issue descriptions
│   ├── hooks/
│   │   └── useAgentConfig.ts            # FR-005,006: Pipeline config selection persistence
│   └── pages/
│       └── ProjectsPage.tsx             # FR-001,010: Unified layout container for pipeline + board
└── tests/
    └── utils/
        └── formatAgentName.test.ts      # FR-003,004: Unit tests for name formatting

backend/
├── src/
│   ├── api/
│   │   └── board.py                     # FR-007: Sub-issue filtering for Done column
│   └── services/
│       └── github_projects/
│           └── service.py               # FR-007: Filter sub-issues from Done columns
└── tests/
    └── unit/
        └── test_board_filter.py         # FR-007: Sub-issue filter tests (if warranted)
```

**Structure Decision**: Existing web application layout (backend/ + frontend/). One new utility file (`formatAgentName.ts`) and its test. All other changes are in-place modifications to existing files. Two new npm dependencies (react-markdown, remark-gfm) for Markdown rendering.

## Complexity Tracking

> No constitution violations. No complexity justification needed.
>
> All changes use standard patterns: @dnd-kit offset correction follows library documentation; Tailwind restyling references existing Pipeline Stages component; react-markdown is the standard React Markdown renderer; `formatAgentName` is a single pure function; sub-issue filtering is a straightforward array filter. No new abstractions or architecture changes are introduced.
