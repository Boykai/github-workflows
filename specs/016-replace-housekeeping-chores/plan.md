# Implementation Plan: Replace Housekeeping with Chores

**Branch**: `016-replace-housekeeping-chores` | **Date**: 2026-03-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-replace-housekeeping-chores/spec.md`

## Summary

Replace the existing Housekeeping feature with a new Chores feature. Chores are recurring maintenance tasks backed by GitHub Issue Templates (`.md` with YAML front matter). They trigger on a time interval (days) or after N new parent issues are created (excluding chore-generated and sub-issues). When triggered, a chore creates a GitHub Parent Issue from its template and executes the agent pipeline to create sub-issues assigned to configured agents. The chore creation flow supports both rich input (direct template content) and sparse input (interactive chat agent conversation). Template files are committed to the repo via branch+PR workflow.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.4 (frontend)
**Primary Dependencies**: FastAPI 0.109+, Pydantic v2, httpx 0.26+, aiosqlite 0.20+ (backend); React 18, Vite 5, TailwindCSS 3.4, @tanstack/react-query 5, socket.io-client 4.7 (frontend)
**Storage**: SQLite via aiosqlite, raw SQL (no ORM), Pydantic models, custom numbered SQL migrations
**Testing**: pytest + pytest-asyncio with in-memory SQLite (backend); Vitest + happy-dom + Testing Library (frontend); Playwright (e2e)
**Target Platform**: Docker (Linux containers), docker-compose orchestration
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Chore trigger evaluation within 5 minutes of schedule condition being met; chore creation completes within 30 seconds
**Constraints**: No new dependencies unless absolutely necessary; follow existing raw SQL + Pydantic patterns (no ORM); all GitHub API calls via existing httpx GraphQL/REST client
**Scale/Scope**: Single-user app managing GitHub Projects; dozens of chores per project

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS
Feature spec exists at `specs/016-replace-housekeeping-chores/spec.md` with 8 prioritized user stories (P1-P3), Given-When-Then acceptance scenarios, clear scope boundaries, functional requirements, and success criteria.

### II. Template-Driven Workflow — ✅ PASS
Plan follows the canonical `plan-template.md`. Spec follows `spec-template.md`. All artifacts in standard directory structure.

### III. Agent-Orchestrated Execution — ✅ PASS
Following speckit agent workflow: specify → plan → tasks → implement. Each phase produces defined outputs with explicit transitions.

### IV. Test Optionality with Clarity — ✅ PASS
Tests are explicitly requested in the spec (FR: "Write backend unit tests (pytest)... Write frontend unit tests (vitest)..."). Tests will follow phase ordering.

### V. Simplicity and DRY — ✅ PASS
Chores replaces Housekeeping 1:1 — same domain concept modernized. Uses existing patterns: raw SQL + Pydantic models, httpx GitHub client, existing chat agent infrastructure, existing workflow orchestrator. No new abstractions introduced. Migration drops old tables and creates new ones in a single numbered SQL file.

**Gate Result: ALL PASS — proceed to Phase 0**

## Project Structure

### Documentation (this feature)

```text
specs/016-replace-housekeeping-chores/
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
│   │   └── chores.py               # NEW: Pydantic models (replaces housekeeping.py)
│   ├── services/
│   │   └── chores/                  # NEW: Chore service package (replaces housekeeping/)
│   │       ├── __init__.py
│   │       ├── service.py           # Core CRUD + trigger logic
│   │       ├── scheduler.py         # Time-based schedule evaluation
│   │       ├── counter.py           # Count-based trigger evaluation
│   │       └── template_builder.py  # GitHub Issue Template generation + PR workflow
│   ├── api/
│   │   └── chores.py               # NEW: REST endpoints (replaces housekeeping.py)
│   └── migrations/
│       └── 010_chores.sql           # NEW: Drop housekeeping tables, create chores tables
└── tests/
    └── unit/
        ├── test_chores_service.py   # NEW
        ├── test_chores_api.py       # NEW
        ├── test_chores_scheduler.py # NEW
        └── test_chores_counter.py   # NEW

frontend/
├── src/
│   ├── components/
│   │   └── chores/                  # NEW: Chores panel components (replaces housekeeping/)
│   │       ├── ChoresPanel.tsx      # Main panel container
│   │       ├── ChoreCard.tsx        # Individual chore display
│   │       ├── AddChoreModal.tsx    # Creation pop-up with text input
│   │       ├── ChoreScheduleConfig.tsx  # Schedule type/value inline editor
│   │       └── ChoreChatFlow.tsx    # Chat agent interaction for sparse input
│   ├── hooks/
│   │   └── useChores.ts            # NEW: React Query hooks (replaces useHousekeeping.ts)
│   └── pages/
│       └── ProjectBoardPage.tsx     # MODIFIED: Add ChoresPanel to right side
└── src/
    └── components/
        └── chores/
            └── __tests__/
                ├── ChoresPanel.test.tsx
                ├── AddChoreModal.test.tsx
                └── ChoreScheduleConfig.test.tsx
```

**Structure Decision**: Web application layout matching existing `backend/` + `frontend/` structure. New code mirrors existing patterns: Pydantic models in `models/`, service package in `services/`, API router in `api/`, React components in `components/`, hooks in `hooks/`. Files to delete: `backend/src/models/housekeeping.py`, `backend/src/api/housekeeping.py`, `backend/src/services/housekeeping/` (entire directory), `frontend/src/components/housekeeping/` (entire directory), `frontend/src/hooks/useHousekeeping.ts`.

## Complexity Tracking

> No constitution violations — no entries needed.
