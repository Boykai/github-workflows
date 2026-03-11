# Implementation Plan: Performance Review

**Branch**: `034-performance-review` | **Date**: 2026-03-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/034-performance-review/spec.md`

## Summary

Deliver a balanced first-pass performance improvement across backend and frontend. The approach starts with baseline measurement and instrumentation, then fixes the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Research confirms Spec 022 is mostly implemented; remaining work targets residual gaps and measurable low-risk optimizations. Architectural changes (virtualization, service decomposition) are explicitly deferred unless first-pass measurements prove they are necessary.

## Technical Context

**Language/Version**: Python ≥ 3.12 (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI ≥ 0.135.0, githubkit ≥ 0.14.6, websockets ≥ 16.0 (backend); React 19.2.0, TanStack React Query 5.90.0, @dnd-kit (frontend)
**Storage**: aiosqlite ≥ 0.22.0 (async SQLite); in-memory TTL cache (backend `services/cache.py`)
**Testing**: pytest + pytest-asyncio + pyright + ruff (backend); vitest 4.0.18 + playwright 1.58.2 + ESLint (frontend)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: ≥ 50% reduction in idle API calls (SC-001); ≥ 30% fewer GitHub API calls on warm-cache refresh (SC-002); lightweight task updates reflected in < 2 s without full board reload (SC-003); zero full board refreshes from idle fallback polling over 5 min (SC-004); responsive board interactions on boards with 100+ cards (SC-005)
**Constraints**: No new runtime dependencies; no architectural rewrites in first pass; backward-compatible behavior for manual refresh and real-time updates
**Scale/Scope**: Boards with 50–100 tasks across 4–6 columns (typical); up to 100+ cards for stress testing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | `spec.md` includes prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, scope boundaries, and out-of-scope declarations. |
| II | Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/`. No custom sections added. |
| III | Agent-Orchestrated Execution | ✅ PASS | This plan is produced by `speckit.plan` with clear inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). |
| IV | Test Optionality with Clarity | ✅ PASS | Tests are explicitly mandated by the spec (FR-013, FR-014, User Story 5). Backend and frontend regression coverage is in scope. |
| V | Simplicity and DRY | ✅ PASS | First pass is intentionally low-risk: memoization, cache reuse, listener throttling. No premature abstraction. Architectural changes deferred unless metrics justify. |

**Gate result**: All principles satisfied. Proceeding to Phase 0.

### Post-Phase-1 Re-check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | Design artifacts (data-model, contracts, quickstart) trace back to spec requirements. |
| II | Template-Driven Workflow | ✅ PASS | All generated artifacts follow template structure. |
| III | Agent-Orchestrated Execution | ✅ PASS | Phase 1 outputs are well-defined inputs for `speckit.tasks`. |
| IV | Test Optionality with Clarity | ✅ PASS | Spec explicitly mandates tests; regression coverage included in data model and contracts. |
| V | Simplicity and DRY | ✅ PASS | No unnecessary abstractions introduced. Optimization targets are specific and measurable. |

## Project Structure

### Documentation (this feature)

```text
specs/034-performance-review/
├── plan.md              # This file
├── research.md          # Phase 0: unknowns resolution and technology research
├── data-model.md        # Phase 1: entities, state transitions, validation rules
├── quickstart.md        # Phase 1: implementation quickstart guide
├── contracts/
│   ├── backend-cache.md        # Cache behavior contracts
│   ├── refresh-policy.md       # Unified refresh policy contract
│   └── board-endpoints.md      # Board endpoint performance contracts
├── checklists/
│   └── requirements.md         # Spec quality checklist (pre-existing)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── board.py             # Board endpoint: cache TTL 300s, stale fallback, sub-issue invalidation
│   │   ├── projects.py          # WebSocket subscription: 30s refresh, SHA256 change detection
│   │   └── workflow.py          # Duplicate repo resolution (DRY target)
│   ├── services/
│   │   ├── cache.py             # TTL cache: 300s primary, 3600s metadata, BoundedSet/BoundedDict
│   │   ├── github_projects/
│   │   │   └── service.py       # Board/project fetching, GraphQL coalescing, cycle cache
│   │   └── copilot_polling/
│   │       └── polling_loop.py  # Rate-limit-aware polling: pause/skip/stale thresholds
│   └── utils.py                 # Canonical repo resolution, cached_fetch, BoundedCollections
└── tests/unit/
    ├── test_cache.py            # Cache TTL, expiry, stale fallback tests
    ├── test_api_board.py        # Board cache behavior, refresh bypass, sub-issue invalidation tests
    └── test_copilot_polling.py  # Polling rate-limit awareness tests

frontend/
├── src/
│   ├── hooks/
│   │   ├── useRealTimeSync.ts       # WebSocket + fallback polling, task-only invalidation
│   │   ├── useBoardRefresh.ts       # Auto-refresh (5 min), manual refresh coordination
│   │   └── useProjectBoard.ts       # Board query: staleTime 60s, projects staleTime 15 min
│   ├── components/
│   │   └── board/
│   │       ├── BoardColumn.tsx      # memo()-wrapped, grouping support
│   │       └── IssueCard.tsx        # memo()-wrapped, avatar validation
│   ├── pages/
│   │   └── ProjectsPage.tsx         # Derived state (useMemo), unmemoized grid style (optimization target)
│   └── components/
│       └── chat/
│           └── ChatPopup.tsx        # Drag listeners gated to rAF (already optimized)
└── src/hooks/
    ├── useRealTimeSync.test.tsx     # WebSocket, fallback polling, query invalidation tests
    └── useBoardRefresh.test.tsx     # Manual refresh dedup, auto-refresh timer, visibility tests
```

**Structure Decision**: Web application with separate `backend/` and `frontend/` directories. All changes target existing files and test files — no new modules or directories needed except the `contracts/` subdirectory under the spec.

## Complexity Tracking

> No constitution violations detected. No complexity justifications required.
