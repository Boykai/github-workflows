# Implementation Plan: Performance Review

**Branch**: `056-performance-review` | **Date**: 2026-03-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/056-performance-review/spec.md`

## Summary

Deliver a balanced first pass of measurable, low-risk performance improvements across backend and frontend. The work starts by capturing baselines and instrumentation, then targets the highest-value issues already surfaced in the codebase: backend GitHub API churn around board refreshes and polling (WebSocket subscription refresh logic, sub-issue cache reuse, polling-triggered board refreshes), and frontend board responsiveness issues (broad query invalidation on lightweight updates, full-list rerenders without stable props, and hot event listeners on drag/popover positioning). Deeper architectural refactors (virtualization, service decomposition) are deferred unless first-pass metrics prove them necessary.

The technical approach proceeds in four phases:
1. **Baseline & Guardrails** — Capture before metrics, confirm current state against existing rate-limit protections.
2. **Backend API Consumption Fixes** — Eliminate redundant upstream API calls during idle viewing, harden sub-issue cache reuse, prevent polling-triggered full board refreshes.
3. **Frontend Refresh-Path & Render Fixes** — Decouple lightweight task updates from full board queries, stabilize props and memoize heavy components, throttle hot event listeners.
4. **Verification & Regression Coverage** — Prove improvements with before/after comparisons, extend automated test coverage.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, Starlette WebSockets, httpx (backend); React 18, TanStack Query v5, Radix UI, dnd-kit (frontend)
**Storage**: SQLite (backend persistence), In-memory cache with TTL (runtime caching)
**Testing**: pytest (backend unit/integration), Vitest (frontend unit), Ruff + Pyright (backend lint/type), ESLint + tsc (frontend lint/type)
**Target Platform**: Linux server (backend), Modern browsers (frontend SPA)
**Project Type**: Web application (backend + frontend monorepo under `solune/`)
**Performance Goals**: ≥50% reduction in idle upstream API calls (SC-001); measurable reduction in board rerenders (SC-005); polling fallback never triggers full board refresh when data unchanged (SC-003)
**Constraints**: No new runtime dependencies in first pass; no board virtualization unless baseline proves necessary; changes must not regress existing test suites
**Scale/Scope**: Boards with 5+ columns and 50+ tasks as representative workload; single-user performance focus (no multi-tenant scaling changes)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md includes 6 prioritized user stories with Given-When-Then acceptance scenarios, clear scope boundaries, and out-of-scope declarations |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md; hands off to tasks phase |
| **IV. Test Optionality** | ✅ PASS | Tests are explicitly requested in the spec (User Story 5, FR-014). Test tasks will follow implementation tasks per spec sequencing (verification depends on optimization phases completing first) |
| **V. Simplicity and DRY** | ✅ PASS | First pass intentionally avoids premature abstraction (no virtualization, no service decomposition). Consolidates duplicate repository resolution. No new dependencies |

**Post-Phase 1 Re-check**: All gates remain PASS. Design artifacts add no unnecessary complexity — data-model captures existing cache/refresh structures being optimized, contracts define the refresh policy interface between backend and frontend, no new entities or services introduced.

## Project Structure

### Documentation (this feature)

```text
specs/056-performance-review/
├── plan.md              # This file
├── research.md          # Phase 0: research findings
├── data-model.md        # Phase 1: cache and refresh data structures
├── quickstart.md        # Phase 1: developer quickstart
├── contracts/           # Phase 1: refresh policy contracts
│   └── refresh-policy.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
solune/backend/
├── src/
│   ├── api/
│   │   ├── board.py             # Board cache, manual refresh, sub-issue invalidation
│   │   ├── projects.py          # WebSocket subscription, change detection, task endpoints
│   │   └── workflow.py          # Duplicate repository resolution path (consolidation target)
│   ├── services/
│   │   ├── cache.py             # InMemoryCache, TTL, data hash, cached_fetch
│   │   ├── copilot_polling/
│   │   │   └── polling_loop.py  # Polling hot path, rate-limit-aware scheduling
│   │   └── github_projects/
│   │       └── service.py       # GraphQL/REST client, cycle cache, inflight coalescing
│   └── utils.py                 # Repository resolution, BoundedDict/BoundedSet
└── tests/
    └── unit/
        ├── test_cache.py            # Cache TTL, stale fallback, hash change detection
        ├── test_api_board.py        # Board endpoint, cache behavior, sub-issue cache
        └── test_copilot_polling.py  # Polling orchestration, rate-limit behavior

solune/frontend/
├── src/
│   ├── hooks/
│   │   ├── useRealTimeSync.ts       # WebSocket + polling fallback, query invalidation
│   │   ├── useBoardRefresh.ts       # Manual/auto-refresh, debounce, page visibility
│   │   └── useProjectBoard.ts       # Board query ownership, project selection
│   ├── components/
│   │   ├── board/
│   │   │   ├── BoardColumn.tsx      # Column rendering (React.memo, infinite scroll)
│   │   │   ├── IssueCard.tsx        # Card rendering (React.memo, draggable)
│   │   │   └── AddAgentPopover.tsx  # Agent selection popover (Radix positioning)
│   │   └── chat/
│   │       └── ChatPopup.tsx        # Resizable chat (RAF-gated drag listeners)
│   └── pages/
│       └── ProjectsPage.tsx         # Board page, heroStats, derived state
└── src/hooks/
    ├── useRealTimeSync.test.tsx      # WebSocket/polling invalidation tests
    └── useBoardRefresh.test.tsx      # Refresh timer/deduplication tests
```

**Structure Decision**: Existing web application structure (backend + frontend under `solune/`). This feature modifies existing files only — no new modules or services are introduced, consistent with the low-risk first-pass approach.

## Complexity Tracking

No constitution violations requiring justification. All changes follow YAGNI principles:
- Optimizations target existing code paths rather than introducing new abstractions
- No new dependencies added
- Deferred work (virtualization, service decomposition) explicitly excluded unless metrics justify it
