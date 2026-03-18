# Implementation Plan: Performance Review

**Branch**: `051-performance-review` | **Date**: 2026-03-18 | **Spec**: [`specs/051-performance-review/spec.md`](spec.md)
**Input**: Feature specification from `specs/051-performance-review/spec.md`

## Summary

Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. The plan captures baselines, then fixes the highest-value issues already surfaced by the codebase: backend GitHub API churn around board refreshes and polling (WebSocket change detection, sub-issue cache reuse, polling guard rails), and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Broader architectural refactors like virtualization and large service decomposition are deferred unless the first pass fails to meet targets.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.9.0 + React 19.2.0 (frontend)
**Primary Dependencies**: FastAPI ≥0.135.0, githubkit ≥0.14.6, TanStack React Query ^5.90.0, @dnd-kit (drag-and-drop), Radix UI (popovers)
**Storage**: SQLite via aiosqlite (persistent settings, completed tasks); in-memory `InMemoryCache` (board data, sub-issues, rate limits)
**Testing**: pytest + pytest-asyncio + pytest-cov (backend), Vitest + React Testing Library + Playwright (frontend)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: ≤2 external API calls/min idle, 30% faster board TTI with warm cache, ≥30 fps board interactions, real-time task updates within 3 seconds
**Constraints**: No new external dependencies in first pass, no architectural rewrites, maintain all existing test coverage, respect GitHub API rate limits
**Scale/Scope**: ~18 API endpoints, ~30+ service modules, representative board size 50–100 tasks across 4–6 columns

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

The feature specification (`specs/051-performance-review/spec.md`) contains 6 prioritized user stories (P1–P3) with independent testing criteria and Given-When-Then acceptance scenarios. Scope boundaries and out-of-scope declarations are explicit.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates from `.specify/templates/`. This plan follows `plan-template.md`. Research, data model, contracts, and quickstart documents are generated per the template structure.

### III. Agent-Orchestrated Execution — ✅ PASS

This plan is produced by the `speckit.plan` agent with clear inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to `speckit.tasks` for task generation is explicit.

### IV. Test Optionality with Clarity — ✅ PASS

Tests are explicitly requested in the spec (FR-017, FR-018, FR-019) for backend cache behavior, change detection, fallback polling safety, frontend real-time sync, board refresh hooks, and query invalidation. Test tasks are scoped to verification of changed behavior only, not broad coverage expansion.

### V. Simplicity and DRY — ✅ PASS

The plan favors extending existing infrastructure (InMemoryCache, useBoardRefresh, useRealTimeSync) over introducing new abstractions. Optimizations target specific hot paths with minimal surface area. The only patterns introduced are `React.memo` wrappers and `useMemo`/`useCallback` stabilization on existing components — standard React patterns, not new abstractions.

### Post-Design Re-evaluation — ✅ PASS

After Phase 1 design, all principles remain satisfied. The data model introduces only essential entities (Performance Baseline, Refresh Policy). No unnecessary abstractions or complexity is added. All changes are to existing files and patterns.

## Project Structure

### Documentation (this feature)

```text
specs/051-performance-review/
├── plan.md              # This file (speckit.plan output)
├── research.md          # Phase 0 output (speckit.plan)
├── data-model.md        # Phase 1 output (speckit.plan)
├── quickstart.md        # Phase 1 output (speckit.plan)
├── contracts/           # Phase 1 output (speckit.plan)
│   ├── refresh-policy.md
│   └── baseline-metrics.md
└── tasks.md             # Phase 2 output (speckit.tasks — NOT created by speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── board.py           # Board cache behavior, manual refresh, sub-issue invalidation
│   │   │   ├── projects.py        # WebSocket subscription, change detection, SSE fallback
│   │   │   └── workflow.py        # Duplicate repo-resolution path (consolidation target)
│   │   ├── services/
│   │   │   ├── cache.py           # InMemoryCache, TTLs, cache keys, compute_data_hash
│   │   │   ├── github_projects/
│   │   │   │   └── service.py     # Board/project fetching, request coalescing, cycle cache
│   │   │   └── copilot_polling/
│   │   │       └── polling_loop.py # Polling hot path, rate-limit aware scheduling
│   │   └── utils.py               # Shared repo resolution, BoundedSet/Dict
│   └── tests/
│       └── unit/
│           ├── test_cache.py           # Cache TTL and stale fallback coverage
│           ├── test_api_board.py       # Board endpoint behavior
│           └── test_copilot_polling.py # Polling behavior and rate-limit logic
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   ├── useRealTimeSync.ts       # WebSocket/polling fallback, query invalidation
│   │   │   ├── useBoardRefresh.ts       # Manual/auto refresh, debounce, page visibility
│   │   │   ├── useProjectBoard.ts       # Board query ownership, staleness config
│   │   │   ├── useRealTimeSync.test.tsx  # WebSocket/polling test coverage
│   │   │   └── useBoardRefresh.test.tsx  # Refresh timer/deduplication tests
│   │   ├── components/
│   │   │   └── board/
│   │   │       ├── BoardColumn.tsx  # Column rendering (memoization target)
│   │   │       └── IssueCard.tsx    # Card rendering (memoization target)
│   │   ├── pages/
│   │   │   └── ProjectsPage.tsx     # Board page, derived-data stabilization target
│   │   └── components/
│   │       └── chat/
│   │           └── ChatPopup.tsx    # Drag listener throttling target
│   └── e2e/                         # Playwright E2E specs
```

**Structure Decision**: Web application structure (backend + frontend). All changes are to existing files within `solune/backend/` and `solune/frontend/`. No new directories or modules are created. The paths referenced in the issue description correctly map to `solune/backend/` and `solune/frontend/` (not `apps/solune/`).

## Complexity Tracking

> No constitution violations detected. No complexity justification required.
