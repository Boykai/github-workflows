# Implementation Plan: Housekeeping Issue Templates with Configurable Triggers

**Branch**: `014-housekeeping-triggers` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-housekeeping-triggers/spec.md`

## Summary

Add a recurring housekeeping task system that automatically creates predefined GitHub Issues with sub issues based on configurable triggers. Each housekeeping task references a stored issue template and fires via either a time-based schedule (cron) or a count-based threshold (N parent issues created since last trigger). The system ships with three built-in starter templates (Security and Privacy Review, Test Coverage Refresh, Bug Bash) that default to the Spec Kit agent pipeline for sub-issue generation. The backend persists task definitions and trigger state in SQLite, exposes CRUD + trigger APIs via FastAPI, and integrates with GitHub Actions scheduled workflows for time-based triggers and the existing webhook pipeline for count-based triggers. The frontend provides React UI for task management, template library, manual "Run Now", and trigger history.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.4 / Node 20 (frontend)
**Primary Dependencies**: FastAPI, Pydantic 2.5+, aiosqlite 0.20+ (backend); React 18, Vite 5, TanStack Query v5, Shadcn/ui (frontend)
**Storage**: SQLite (aiosqlite, WAL mode) — extends existing `settings.db` with new tables for housekeeping tasks, templates, and trigger history
**Testing**: pytest 7.4+ / pytest-asyncio (backend), Vitest 4.0+ / @testing-library/react (frontend)
**Target Platform**: Linux server (backend), Modern browsers (frontend)
**Project Type**: web (backend + frontend)
**Performance Goals**: Time-based triggers fire within 5 minutes of schedule; count-based triggers evaluate within 1 minute of threshold issue creation; manual "Run Now" completes within 30 seconds; API responses under 3 seconds
**Constraints**: No new external dependencies beyond what is already in the project; idempotency guards with minimum cooldown window to prevent double-triggers; must integrate with existing GitHub Actions cron scheduler and webhook pipeline
**Scale/Scope**: Tens of housekeeping tasks per project; hundreds of trigger history entries per task; three built-in seed templates; single-project scope (not multi-tenant)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md exists with 7 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, clear scope boundaries, and edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase follows single-responsibility agent model; outputs are well-defined markdown documents for handoff |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are not explicitly mandated in the spec; will be included only if required during task generation phase |
| V. Simplicity and DRY | ✅ PASS | Design reuses existing SQLite storage, webhook pipeline, and workflow orchestrator patterns; no premature abstractions; built-in templates are simple seed data |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/014-housekeeping-triggers/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Developer quickstart
├── contracts/           # Phase 1: API contracts
│   └── housekeeping-api.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT this phase)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── housekeeping.py      # Pydantic models for housekeeping tasks, templates, trigger events
│   ├── services/
│   │   └── housekeeping/        # Housekeeping service package
│   │       ├── __init__.py
│   │       ├── service.py       # HousekeepingService — CRUD, trigger evaluation, execution
│   │       ├── scheduler.py     # Time-based trigger scheduler (integrates with GitHub Actions cron)
│   │       ├── counter.py       # Count-based trigger evaluator (hooks into issue creation events)
│   │       └── seed.py          # Built-in seed templates (Security Review, Test Coverage, Bug Bash)
│   ├── api/
│   │   └── housekeeping.py      # FastAPI router for housekeeping endpoints
│   └── migrations/
│       └── 006_housekeeping.sql # New tables: housekeeping_tasks, issue_templates, trigger_history
└── tests/
    └── unit/
        └── test_housekeeping.py # Unit tests for housekeeping service

frontend/
├── src/
│   ├── components/
│   │   └── housekeeping/        # Housekeeping UI components
│   │       ├── HousekeepingTaskList.tsx
│   │       ├── HousekeepingTaskForm.tsx
│   │       ├── TemplateLibrary.tsx
│   │       ├── TriggerHistoryLog.tsx
│   │       └── RunNowButton.tsx
│   ├── hooks/
│   │   └── useHousekeeping.ts   # Custom hook for housekeeping API calls
│   └── services/
│       └── api.ts               # Extended with housekeeping API endpoints
└── tests/

.github/
└── workflows/
    └── housekeeping-cron.yml    # GitHub Actions workflow for time-based housekeeping triggers
```

**Structure Decision**: Web application (backend + frontend) — the repository already uses a `backend/` + `frontend/` split. New housekeeping functionality is added as a new service package in the backend and a new component directory in the frontend, following the existing modular patterns (e.g., `workflow_orchestrator/`, `copilot_polling/`).

## Complexity Tracking

> No constitution violations to justify. All principles are satisfied.

## Constitution Re-Check (Post Phase 1 Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All design artifacts (data-model.md, contracts/, quickstart.md) trace back to spec.md requirements |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow canonical structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produced well-defined outputs for handoff to tasks phase |
| IV. Test Optionality with Clarity | ✅ PASS | No tests mandated; test infrastructure notes included in quickstart for when tests are needed |
| V. Simplicity and DRY | ✅ PASS | Design reuses existing patterns (SQLite migrations, service modules, FastAPI routers, React hooks); no unnecessary abstractions; seed templates are simple JSON/YAML data |

**Post-Design Gate Result**: ✅ ALL PASS — ready for Phase 2 (tasks generation via `/speckit.tasks`).
