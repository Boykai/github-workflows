# Implementation Plan: Pagination & Infinite Scroll for All List Views

**Branch**: `053-pagination-infinite-scroll` | **Date**: 2026-03-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/053-pagination-infinite-scroll/spec.md`

## Summary

Add cursor-based pagination to all backend list endpoints and migrate all frontend list views from
`useQuery` (full-list fetch) to `useInfiniteQuery` (infinite scroll). Currently, every list view
(board columns, agents, tools, chores, apps, saved pipelines) fetches and renders the entire data
set at once — no `useInfiniteQuery`, no load-more, no page cursors anywhere. This degrades
performance and overwhelms users on large projects.

The approach introduces a shared `PaginatedResponse[T]` envelope on the backend (FastAPI/Pydantic),
a reusable `useInfiniteList` hook on the frontend (TanStack React Query v5), and an
`InfiniteScrollContainer` component that detects scroll position via `IntersectionObserver` and
triggers the next page fetch. Each list view is migrated independently, starting with the
highest-impact P1 views (project board columns, agents catalog) and proceeding to P2/P3 views.

## Technical Context

**Language/Version**: Python 3.12+/3.13 (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI 0.135+, React 19, Pydantic 2.12+, Vite 8, TanStack Query v5, Tailwind CSS 4, @dnd-kit/core (board drag-and-drop)
**Storage**: SQLite via aiosqlite (existing — no schema changes required)
**Testing**: pytest + pytest-asyncio (backend), Vitest + @testing-library/react (frontend)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (backend + frontend monorepo under `solune/`)
**Performance Goals**: Initial page load < 2s for 200+ items; per-page fetch < 1s; memory ≤ 150% of baseline at 500 items
**Constraints**: No breaking changes to existing API consumers; infinite scroll preferred over numbered pagination; virtual scrolling deferred to follow-up
**Scale/Scope**: 6 list views to paginate (board columns, agents, tools, chores, apps, saved pipelines); default page size 20–25 items

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development ✅ PASS

- ✅ Feature work began with explicit specification (`spec.md`)
- ✅ 6 prioritized user stories (P1–P3) with independent testing criteria
- ✅ Given-When-Then acceptance scenarios for each story
- ✅ Clear scope boundaries (virtual scrolling explicitly deferred; server-side filtering out of scope unless pagination makes it necessary)
- ✅ 6 edge cases identified and documented

### Principle II: Template-Driven Workflow ✅ PASS

- ✅ All artifacts follow canonical templates from `.specify/templates/`
- ✅ Plan, research, data-model, contracts, quickstart generated per template structure
- ✅ No custom sections added without justification

### Principle III: Agent-Orchestrated Execution ✅ PASS

- ✅ Plan phase produces well-defined outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md)
- ✅ Explicit handoff to subsequent phases (tasks generation, implementation)
- ✅ Single-responsibility: this plan phase does not implement code changes

### Principle IV: Test Optionality with Clarity ✅ PASS

- ✅ Tests are NOT the primary deliverable — pagination is the feature
- ✅ Spec does not mandate specific test types; tests will follow standard project patterns
- ✅ Constitution check does not mandate additional testing beyond existing project thresholds

### Principle V: Simplicity and DRY ✅ PASS

- ✅ Single `PaginatedResponse[T]` envelope reused across all backend endpoints — avoids per-endpoint response shapes
- ✅ Single `useInfiniteList` hook wraps `useInfiniteQuery` with shared defaults — avoids duplicating pagination logic in each page
- ✅ Single `InfiniteScrollContainer` component wraps `IntersectionObserver` — avoids scroll detection logic in every list view
- ✅ No new abstractions beyond what pagination requires; no Repository pattern, no virtual scrolling, no server-side filtering
- ✅ Uses existing TanStack Query infrastructure (`useInfiniteQuery` is built-in, not a new dependency)

## Project Structure

### Documentation (this feature)

```text
specs/053-pagination-infinite-scroll/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — research decisions
├── data-model.md        # Phase 1 output — paginated response entities
├── quickstart.md        # Phase 1 output — implementation guide
├── contracts/           # Phase 1 output — API contracts
│   ├── pagination-api.md        # Paginated endpoint contracts
│   └── verification-commands.md # Verification command reference
├── checklists/
│   └── requirements.md          # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/                        # FastAPI route handlers (modify for pagination)
│   │   │   ├── agents.py               # Add limit/cursor params to list endpoint
│   │   │   ├── tools.py                # Add limit/cursor params to list endpoint
│   │   │   ├── chores.py               # Add limit/cursor params to list endpoint
│   │   │   ├── apps.py                 # Add limit/cursor params to list endpoint
│   │   │   ├── board.py                # Add per-column pagination to board data
│   │   │   └── pipelines.py            # Add limit/cursor params to list endpoint
│   │   ├── models/                     # Pydantic models (add PaginatedResponse)
│   │   │   └── pagination.py           # NEW: PaginatedResponse[T] generic model
│   │   └── services/                   # Business logic (add pagination helpers)
│   │       └── pagination.py           # NEW: apply_pagination() utility
│   └── tests/
│       └── unit/
│           └── test_pagination.py      # NEW: Pagination utility tests
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   └── InfiniteScrollContainer.tsx  # NEW: Reusable scroll container
│   │   │   └── board/
│   │   │       └── BoardColumn.tsx              # Modify for paginated column items
│   │   ├── hooks/
│   │   │   ├── useInfiniteList.ts               # NEW: Shared infinite query hook
│   │   │   ├── useAgents.ts                     # Migrate to useInfiniteQuery
│   │   │   ├── useTools.ts                      # Migrate to useInfiniteQuery
│   │   │   ├── useChores.ts                     # Migrate to useInfiniteQuery
│   │   │   ├── useApps.ts                       # Migrate to useInfiniteQuery
│   │   │   └── useProjectBoard.ts               # Add per-column pagination
│   │   ├── pages/
│   │   │   ├── AgentsPage.tsx                   # Integrate InfiniteScrollContainer
│   │   │   ├── ToolsPage.tsx                    # Integrate InfiniteScrollContainer
│   │   │   ├── ChoresPage.tsx                   # Integrate InfiniteScrollContainer
│   │   │   └── AppsPage.tsx                     # Integrate InfiniteScrollContainer
│   │   ├── services/
│   │   │   └── api.ts                           # Add paginated fetch helpers
│   │   └── types/
│   │       └── index.ts                         # Add PaginatedResponse type
│   └── tests/
│       └── (test files following existing patterns)
```

**Structure Decision**: Web application structure (backend + frontend monorepo under `solune/`).
The feature modifies existing files and adds a small number of new shared utilities. No new
top-level directories or projects are created.

## Phases

### Phase A: Backend Pagination Foundation (P1 — Shared Infrastructure)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 1 | Create `PaginatedResponse[T]` Pydantic model with `items`, `next_cursor`, `has_more`, `total_count` fields | — | `src/models/pagination.py` |
| 2 | Create `apply_pagination()` helper that accepts a list, cursor, and limit, returns a `PaginatedResponse` | Step 1 | `src/services/pagination.py` |
| 3 | Add unit tests for pagination utility (empty list, exact page, partial page, cursor navigation, invalid cursor) | Steps 1–2 | `tests/unit/test_pagination.py` |

**Parallelism**: Steps 1 and 2 are sequential (model before helper). Step 3 can begin once Step 2 is complete.

### Phase B: Backend Endpoint Migration (P1 — Agents + Board, then P2/P3)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 4 | Add `limit` and `cursor` query params to agents list endpoint; return `PaginatedResponse[Agent]` | Phase A | `src/api/agents.py` |
| 5 | Add per-column pagination to board data endpoint (accept per-column limit/cursor) | Phase A | `src/api/board.py` |
| 6 | Add `limit` and `cursor` query params to tools list endpoint | Phase A | `src/api/tools.py` |
| 7 | Add `limit` and `cursor` query params to chores list endpoint | Phase A | `src/api/chores.py` |
| 8 | Add `limit` and `cursor` query params to apps list endpoint | Phase A | `src/api/apps.py` |
| 9 | Add `limit` and `cursor` query params to pipelines list endpoint | Phase A | `src/api/pipelines.py` |

**Parallelism**: Steps 4–9 are all independent once Phase A is complete. P1 items (Steps 4–5) should be implemented first.

**Backward compatibility**: All new params default to returning the full list when omitted (limit defaults to `None`, cursor defaults to `None`). Existing callers are unaffected.

### Phase C: Frontend Shared Infrastructure (P1)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 10 | Add `PaginatedResponse<T>` TypeScript type to `types/index.ts` | — | `src/types/index.ts` |
| 11 | Create `useInfiniteList` hook wrapping `useInfiniteQuery` with shared defaults (page size, getNextPageParam, error handling) | Step 10 | `src/hooks/useInfiniteList.ts` |
| 12 | Create `InfiniteScrollContainer` component using `IntersectionObserver` to trigger `fetchNextPage` when sentinel element enters viewport | Step 11 | `src/components/common/InfiniteScrollContainer.tsx` |
| 13 | Add paginated fetch helpers to `api.ts` service (accept `limit` and `cursor` params, parse `PaginatedResponse`) | Step 10 | `src/services/api.ts` |

**Parallelism**: Steps 10 is first. Steps 11, 12, 13 can proceed in parallel once types are defined.

### Phase D: Frontend Page Migration (P1 first, then P2/P3)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 14 | Migrate `useAgentsList` to `useInfiniteQuery`; update `AgentsPage` with `InfiniteScrollContainer` | Phase C | `src/hooks/useAgents.ts`, `src/pages/AgentsPage.tsx` |
| 15 | Add per-column infinite scroll to `BoardColumn`; update `useProjectBoard` for paginated board data | Phase C | `src/components/board/BoardColumn.tsx`, `src/hooks/useProjectBoard.ts` |
| 16 | Migrate `useToolsList` to `useInfiniteQuery`; update `ToolsPage` with `InfiniteScrollContainer` | Phase C | `src/hooks/useTools.ts`, `src/pages/ToolsPage.tsx` |
| 17 | Migrate `useChoresList` to `useInfiniteQuery`; update `ChoresPage` with `InfiniteScrollContainer` | Phase C | `src/hooks/useChores.ts`, `src/pages/ChoresPage.tsx` |
| 18 | Migrate `useApps` to `useInfiniteQuery`; update `AppsPage` with `InfiniteScrollContainer` | Phase C | `src/hooks/useApps.ts`, `src/pages/AppsPage.tsx` |
| 19 | Add pagination to saved pipelines list on projects page | Phase C | `src/hooks/usePipelineConfig.ts`, relevant page component |

**Parallelism**: Steps 14–19 are all independent once Phase C is complete. P1 items (Steps 14–15) should be implemented first.

### Phase E: Edge Cases and Polish (All priorities)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 20 | Add debounce/dedup to rapid scroll triggers (prevent duplicate page requests) | Phase D | `InfiniteScrollContainer.tsx` |
| 21 | Add retry UI for failed page loads (error state with retry button, preserving loaded data) | Phase D | `InfiniteScrollContainer.tsx` |
| 22 | Handle filter/sort reset (reset to first page when filter or sort changes) | Phase D | `useInfiniteList.ts`, page components |
| 23 | Handle concurrent mutations (item create/delete while viewing paginated list) | Phase D | Hook files, query invalidation |
| 24 | Verify drag-and-drop on paginated board columns works correctly | Step 15 | `BoardColumn.tsx`, E2E tests |

**Parallelism**: Steps 20–23 can proceed in parallel. Step 24 depends on Step 15.

### Phase F: Verification (All priorities)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 25 | Verify initial load < 2s for 200+ item lists | Phases D–E | Performance measurement |
| 26 | Verify per-page fetch < 1s | Phases D–E | Performance measurement |
| 27 | Verify zero duplicate/skipped items across full list traversal | Phases D–E | Integration test |
| 28 | Verify existing lint, type-check, and test suites pass | Phases D–E | CI verification |

## Complexity Tracking

> No constitution violations detected. No entries required.
