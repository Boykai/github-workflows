# Implementation Plan: Activity Log / Audit Trail

**Branch**: `054-activity-audit-trail` | **Date**: 2026-03-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/054-activity-audit-trail/spec.md`

## Summary

Add a unified activity events system to Solune: a single `activity_events` table in the SQLite backend that captures all significant user and system actions (pipeline runs, chore triggers, CRUD operations, webhook events, cleanup operations), a paginated REST API to query them, and a full-featured Activity page with filtering and infinite scroll in the React frontend. Wire the existing placeholder notification bell to surface high-signal events. Add entity-scoped history panels and a pipeline run history view.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI + Pydantic (backend API/models), aiosqlite (async SQLite), React 18 + TanStack Query v5 (frontend state), React Router v6 (routing), Lucide React (icons), Tailwind CSS (styling)
**Storage**: SQLite via aiosqlite — direct SQL queries, no ORM. Pydantic models for serialization. Numbered SQL migration files (current highest: 031).
**Testing**: Backend: ruff (lint) + pyright (type-check) + pytest. Frontend: vitest + happy-dom + @testing-library/react + ESLint + tsc.
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: Web — backend at `solune/backend/`, frontend at `solune/frontend/`
**Performance Goals**: Activity feed query <100ms for 10K rows (indexed), initial page load <2s, subsequent pages <1s, logging overhead <50ms per operation
**Constraints**: Fire-and-forget logging (never block primary operations), cursor-based pagination (no offset), 30s stale time for polling, localStorage for read tracking
**Scale/Scope**: Single-project scoped feeds, expected 10K–100K events per project over months, no retention policy in v1

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

The feature specification (`spec.md`) includes 6 prioritized user stories (P1–P3) with independent testing criteria, 27 functional requirements with Given-When-Then acceptance scenarios, clear scope boundaries, and explicit out-of-scope declarations. Requirements checklist validates all items.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates. This plan uses `plan-template.md`. Research, data model, contracts, and quickstart will be generated per template conventions.

### III. Agent-Orchestrated Execution — ✅ PASS

This plan is produced by the `speckit.plan` agent with clear inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). The subsequent `speckit.tasks` agent will consume this plan.

### IV. Test Optionality with Clarity — ✅ PASS

The spec does not mandate TDD. Tests are optional. The backend already has ruff/pyright checks; frontend has ESLint/tsc/vitest. Existing test suites should pass after implementation (regression check). New tests are recommended but not required.

### V. Simplicity and DRY — ✅ PASS

- **Single table** (`activity_events`) over per-entity history tables — simpler queries, no JOINs for feed.
- **Reuse existing infrastructure**: `PaginatedResponse[T]` model, `apply_pagination()` service (or SQL-level cursor pagination), `useInfiniteList` hook, `InfiniteScrollContainer` component.
- **Fire-and-forget** pattern avoids complex transaction coordination.
- **No new abstractions**: activity logger is a thin service function, not a framework.
- No complexity violations identified.

## Project Structure

### Documentation (this feature)

```text
specs/054-activity-audit-trail/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── activity-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── __init__.py          # Register activity router
│   │   │   ├── activity.py          # NEW — GET /activity feed + entity history
│   │   │   ├── pipelines.py         # ADD log_event() calls
│   │   │   ├── chores.py            # ADD log_event() calls
│   │   │   ├── agents.py            # ADD log_event() calls
│   │   │   ├── apps.py              # ADD log_event() calls
│   │   │   ├── tools.py             # ADD log_event() calls
│   │   │   ├── webhooks.py          # ADD log_event() calls
│   │   │   └── cleanup.py           # ADD log_event() calls
│   │   ├── models/
│   │   │   └── activity.py          # NEW — ActivityEvent, ActivityEventCreate
│   │   ├── services/
│   │   │   ├── activity_logger.py   # NEW — log_event() fire-and-forget service
│   │   │   └── workflow_orchestrator/
│   │   │       └── orchestrator.py  # ADD log_event() for transitions
│   │   ├── migrations/
│   │   │   └── 032_activity_events.sql  # NEW — activity_events table + indexes
│   │   └── main.py                  # Activity router registered via api/__init__.py
│   └── tests/
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── activity/             # NEW — ActivityRow, ActivityDetail, FilterChips
    │   ├── hooks/
    │   │   ├── useActivityFeed.ts    # NEW — useInfiniteList wrapper for activity
    │   │   └── useNotifications.ts   # MODIFY — wire to real activity data
    │   ├── layout/
    │   │   └── Sidebar.tsx           # ADD "Activity" nav link (via NAV_ROUTES)
    │   ├── pages/
    │   │   └── ActivityPage.tsx      # NEW — full activity timeline page
    │   ├── services/
    │   │   └── api.ts                # ADD activityApi + pipelinesApi.listRuns/getRun
    │   ├── types/
    │   │   └── index.ts              # ADD ActivityEvent type
    │   ├── constants.ts              # ADD Activity nav route to NAV_ROUTES
    │   └── App.tsx                   # ADD /activity route
    └── tests/
```

**Structure Decision**: Web application (Option 2) — existing `solune/backend/` and `solune/frontend/` structure. All new files follow established patterns. No new top-level directories needed.

## Complexity Tracking

> No violations identified. All design choices favor simplicity and DRY:

| Decision | Rationale | Alternative Rejected |
|----------|-----------|---------------------|
| Single `activity_events` table | Unified feed query without JOINs, single migration | Per-entity tables: more migrations, complex feed query |
| Cursor-based pagination (timestamp) | Consistent with existing `PaginatedResponse[T]` pattern | Offset-based: skips/duplicates on concurrent inserts |
| Fire-and-forget logging | Logging failures never block user operations | Transactional logging: adds latency, couples to primary operation |
| SQL-level pagination for activity | Activity data lives in DB, not in-memory | In-memory `apply_pagination()`: requires loading all rows |
| Reuse `useInfiniteList` hook | Existing pattern for cursor-based pagination | Custom hook: duplicates proven logic |
| localStorage for read tracking | Consistent with existing notification pattern | Server-side read tracking: new table, API, complexity |
