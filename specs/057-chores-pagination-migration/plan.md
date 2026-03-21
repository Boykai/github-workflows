# Implementation Plan: ChoresPanel Pagination Migration

**Branch**: `057-chores-pagination-migration` | **Date**: 2026-03-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/057-chores-pagination-migration/spec.md`

## Summary

Migrate ChoresPanel from client-side filtering/sorting with full data fetch to server-side filtering/sorting with cursor-based infinite scroll pagination. ChoresPanel is the only remaining unpaginated list — Agents, Tools, Apps, Activity, and Board panels already use `useInfiniteList` + `InfiniteScrollContainer`. The existing pagination infrastructure (`apply_pagination`, `useInfiniteList`, `InfiniteScrollContainer`, `ChoresGrid` pagination props) is fully built; the work is wiring ChoresPanel to use it and adding server-side filter/sort query parameters to the backend endpoint.

The key complication is that ChoresPanel currently does client-side filtering (search, status, schedule type) and sorting. Switching to paginated data requires moving all filters and sorting server-side — client-side filtering on paginated data would only filter loaded pages, missing items on later pages.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI + aiosqlite (backend), React 18 + TanStack Query v5 + Vite (frontend)
**Storage**: SQLite via aiosqlite
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: web (backend + frontend monorepo under `solune/`)
**Performance Goals**: Initial chore load <2s, page transitions <1s, no perceptible delay on filter change
**Constraints**: Maintain behavioral parity with existing paginated panels (Agents, Tools, Apps, Activity, Board); default page size of 25
**Scale/Scope**: Single panel migration affecting 6 files across backend and frontend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS
- Feature spec (`spec.md`) includes 5 prioritized user stories (P1–P3) with Given-When-Then acceptance scenarios
- Each story has independent testing criteria
- Edge cases identified (rapid scrolling, zero results, fast typing, server errors, concurrent mutations, combined filters)

### II. Template-Driven Workflow — ✅ PASS
- Spec follows canonical spec-template.md
- This plan follows plan-template.md
- All artifacts will be generated in the standard `specs/057-chores-pagination-migration/` directory

### III. Agent-Orchestrated Execution — ✅ PASS
- `speckit.specify` produced the spec → `speckit.plan` produces this plan → `speckit.tasks` will produce tasks.md
- Clear single-responsibility handoffs between phases

### IV. Test Optionality with Clarity — ✅ PASS
- Tests are explicitly requested in the feature spec: pytest tests for backend filter combos + cursor behavior, Vitest tests for frontend hook with filter params in query key
- Tests will follow Red-Green-Refactor ordering in tasks phase

### V. Simplicity and DRY — ✅ PASS
- No new abstractions introduced — reuses existing `apply_pagination`, `useInfiniteList`, `InfiniteScrollContainer`
- Server-side filtering uses standard SQL WHERE clauses added to existing query
- Frontend changes swap one hook call for another and remove client-side logic (net code reduction)
- No premature abstraction — filter params are passed directly, not through a generic filter framework

### Post-Design Re-check — ✅ PASS
- All five principles remain satisfied after Phase 1 design
- No complexity violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/057-chores-pagination-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output — technical decisions and rationale
├── data-model.md        # Phase 1 output — entity definitions and relationships
├── quickstart.md        # Phase 1 output — implementation guide
├── contracts/           # Phase 1 output — API contracts
│   └── chores-list-paginated.yaml   # OpenAPI contract for filtered paginated endpoint
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   └── chores.py              # Add filter/sort query params to GET /{project_id}
│   │   ├── models/
│   │   │   └── chores.py              # Existing Chore model (no changes needed)
│   │   └── services/
│   │       ├── chores/
│   │       │   └── service.py         # Existing list_chores (no changes needed — filtering in API layer)
│   │       └── pagination.py          # Existing apply_pagination (no changes needed)
│   └── tests/
│       └── unit/
│           └── api/
│               └── test_chores.py     # Add tests for filter param combos + cursor behavior
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── chores/
│   │   │       ├── ChoresPanel.tsx    # Swap to useChoresListPaginated, remove client-side filter useMemo
│   │   │       ├── ChoresGrid.tsx     # No changes (already supports pagination props)
│   │   │       └── ChoresToolbar.tsx  # No changes (filter UI stays the same)
│   │   ├── hooks/
│   │   │   ├── useChores.ts           # Update useChoresListPaginated to accept filter params
│   │   │   └── useInfiniteList.ts     # No changes (generic hook)
│   │   └── services/
│   │       └── api.ts                 # Update choresApi.listPaginated to accept filter params
│   └── tests/
│       └── hooks/
│           └── useChores.test.ts      # Update tests for filter params in query key
```

**Structure Decision**: Web application layout (`solune/backend/` + `solune/frontend/`). All changes are modifications to existing files — no new source files created. The migration touches 4 source files (backend `chores.py` API, frontend `api.ts`, `useChores.ts`, `ChoresPanel.tsx`) and 2 test files.

## Complexity Tracking

> No constitution violations — no entries needed.

_No complexity violations. The implementation reuses 100% of existing infrastructure (`apply_pagination`, `useInfiniteList`, `InfiniteScrollContainer`, `ChoresGrid` pagination props). The only new code is SQL WHERE clauses for filtering and query parameter forwarding through the existing hook/API chain._
