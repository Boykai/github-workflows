# Implementation Plan: Add 'Human' Agent Type to Agent Pipeline

**Branch**: `014-human-agent-pipeline` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-human-agent-pipeline/spec.md`

## Summary

Add a 'Human' agent type to the Agent Pipeline that enables manual human tasks within automated workflows. When a pipeline containing a Human step is triggered, the system creates a GitHub Sub Issue assigned to the parent issue creator. The pipeline blocks on the Human step until either the Sub Issue is closed or the assigned user comments exactly 'Done!' on the parent issue. The implementation reuses existing sub-issue creation, agent tracking, and completion detection infrastructure, extending constants, the orchestrator, the polling pipeline, and the frontend agent UI. See [research.md](./research.md) for decision rationale.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript/React (frontend)
**Primary Dependencies**: FastAPI, aiosqlite, Pydantic v2 (backend); React 18, Vite, TanStack Query, @dnd-kit, shadcn/ui tokens (frontend)
**Storage**: SQLite (WAL mode) via aiosqlite — no new tables required (reuses existing pipeline state and sub-issue tracking)
**Testing**: pytest (backend), Vitest + React Testing Library (frontend)
**Target Platform**: Linux server (Docker), modern browsers
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Pipeline resumes within 30 seconds of a completion signal (SC-003); Human step addition under 10 seconds (SC-001)
**Constraints**: Idempotent completion handling (both signals must advance pipeline only once); exact 'Done!' string match; only assigned user's comments accepted
**Scale/Scope**: 1 new builtin agent constant, modifications to orchestrator + pipeline + helpers + frontend agent UI; no new DB tables or migrations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check (Phase 0 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with 4 prioritized user stories (P1×3, P2×1), Given-When-Then scenarios, edge cases, and 12 functional requirements |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` agent produces plan.md and Phase 0/1 artifacts |
| IV. Test Optionality | ✅ PASS | Tests not explicitly mandated in spec; will follow existing test patterns where present |
| V. Simplicity and DRY | ✅ PASS | Reuses existing sub-issue creation, agent tracking, and completion detection. No new DB tables, no new frameworks, no new abstractions. Human step is a thin extension of the existing agent step pattern. |

### Post-Design Check (Phase 1 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All FR items (FR-001 through FR-012) have corresponding design in data-model.md and contracts/ |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all generated |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan ready for handoff to `speckit.tasks` |
| IV. Test Optionality | ✅ PASS | No test mandate; tests optional per constitution |
| V. Simplicity and DRY | ✅ PASS | Reuses `create_all_sub_issues`, `check_last_comment_for_done`, `_advance_pipeline`, `AddAgentPopover`, existing `AgentAssignment` model. No new abstractions or patterns introduced. |

## Project Structure

### Documentation (this feature)

```text
specs/014-human-agent-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0: Technical decisions and rationale
├── data-model.md        # Phase 1: Entity definitions and type changes
├── quickstart.md        # Phase 1: Development setup and implementation guide
├── contracts/
│   └── human-agent-events.md  # Phase 1: Event contract (completion signals)
├── checklists/
│   └── requirements.md  # Requirements checklist
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── constants.py                              # Add HUMAN agent to builtin agents, DEFAULT_AGENT_MAPPINGS, AGENT_DISPLAY_NAMES
│   ├── models/
│   │   └── agent.py                              # No changes needed (AgentAssignment already generic)
│   ├── services/
│   │   ├── agent_tracking.py                     # Extend check_last_comment_for_done for human completion
│   │   ├── workflow_orchestrator/
│   │   │   ├── orchestrator.py                   # Modify create_all_sub_issues to assign Human sub-issues to issue creator
│   │   │   └── models.py                         # No changes needed (PipelineState already generic)
│   │   ├── copilot_polling/
│   │   │   ├── pipeline.py                       # Modify _advance_pipeline and agent assignment to handle Human steps
│   │   │   └── helpers.py                        # Extend completion checking for Human agent
│   │   └── github_projects/
│   │       └── service.py                        # No changes needed (assign_issue already exists)
│   └── api/
│       └── workflow.py                           # No changes needed (list_agents already returns builtin agents)
└── tests/
    └── unit/                                     # Optional: tests for human agent behavior

frontend/
├── src/
│   ├── components/
│   │   └── board/
│   │       ├── AddAgentPopover.tsx                # No changes needed (already renders any agent from list)
│   │       └── AgentTile.tsx                      # Add visual distinction for Human agent (person icon, label)
│   └── services/
│       └── api.ts                                 # No changes needed (already fetches agents generically)
└── tests/                                         # Optional: Vitest tests
```

**Structure Decision**: Web application structure (Option 2). The repository already uses `backend/` and `frontend/` top-level directories. The Human agent type is integrated as an extension of existing patterns — no new directories or files are required beyond modifying existing ones. The key insight is that the existing `AgentAssignment`, `PipelineState`, and sub-issue infrastructure are generic enough that the Human agent needs only constants, conditional logic branches, and a frontend icon distinction.

## Complexity Tracking

> No constitution violations detected. All design decisions follow existing patterns.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
