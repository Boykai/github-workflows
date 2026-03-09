# Implementation Plan: Performance Review

**Branch**: `032-performance-review` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/032-performance-review/spec.md`

## Summary

Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. The plan captures baselines first, then addresses the highest-value issues: backend GitHub API churn during idle board viewing and polling, and frontend board responsiveness caused by broad query invalidation, full-list rerenders, and hot event listeners. Broader architectural refactors (virtualization, service decomposition) are deferred unless the first pass fails to meet targets.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.8 (frontend)
**Primary Dependencies**: FastAPI 0.109+, TanStack React Query 5.17, React 18.3, native WebSocket (asyncio), Vitest 4.0+
**Storage**: SQLite (aiosqlite) for persistence, in-memory `InMemoryCache` with TTL for API response caching
**Testing**: pytest 7.4+ / pytest-asyncio 0.23+ (backend), Vitest 4.0+ with React Testing Library (frontend)
**Target Platform**: Linux server (Docker), modern browser (React 18.3 SPA)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: ≥50% reduction in idle API calls, ≤1s perceived latency for single-card real-time updates, ≥80% reduction in sub-issue API calls via caching, ≥30 fps for drag interactions, ≤3 component re-renders for a single-card update on a 100-card board
**Constraints**: Must not break manual refresh (cache bypass), must not degrade board initial render time by more than 10%, must not introduce new dependencies or virtualization in the first pass
**Scale/Scope**: Projects with up to ~200 items across 3–7 columns, 20+ issues with sub-issues, 2+ repositories

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | Spec completed with 7 prioritized user stories (P1–P3), 20+ acceptance scenarios, 10 measurable success criteria, and explicit scope boundaries |
| II. Template-Driven | ✅ PASS | Using canonical plan template. All artifacts follow standard structure |
| III. Agent-Orchestrated | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md |
| IV. Test Optionality | ✅ PASS | Spec explicitly requires regression test coverage (FR-014, User Story 7). Existing tests serve as guardrails; extension limited to changed behavior |
| V. Simplicity and DRY | ✅ PASS | All changes are targeted edits to existing files. No new modules, no new abstractions. Reuses existing InMemoryCache, existing React.memo patterns, existing refresh infrastructure. Defers virtualization and service decomposition to second wave |

**Gate Result**: PASS — no violations, proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/032-performance-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── internal-contracts.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── board.py                  # FR-003/004/006/008: Board cache, manual refresh, sub-issue invalidation
│   │   ├── projects.py               # FR-003/005/012: WebSocket change detection, refresh semantics
│   │   └── workflow.py               # FR-010: Repository resolution dedup (uses utils.resolve_repository)
│   ├── services/
│   │   ├── cache.py                  # FR-007/008: InMemoryCache, TTL management, cache key helpers
│   │   ├── copilot_polling/
│   │   │   └── polling_loop.py       # FR-004/015: Rate-limit-aware polling, adaptive backoff
│   │   └── github_projects/
│   │       └── service.py            # FR-007/008: Sub-issue caching in get_sub_issues()
│   ├── utils.py                      # Shared repository resolution, BoundedSet/BoundedDict
│   └── constants.py                  # Cache prefix constants
└── tests/
    └── unit/
        ├── test_cache.py             # FR-014: Cache TTL and stale fallback tests (14 tests)
        ├── test_api_board.py          # FR-014: Board cache and endpoint tests (13 tests)
        └── test_copilot_polling.py    # FR-014: Polling behavior and rate-limit tests (227 tests)

frontend/
├── src/
│   ├── hooks/
│   │   ├── useRealTimeSync.ts        # FR-003/005/012/015: WebSocket, fallback polling, query invalidation
│   │   ├── useBoardRefresh.ts        # FR-006/013/015: Manual/auto refresh, deduplication, visibility API
│   │   └── useProjectBoard.ts        # FR-009: Board data query ownership, staleTime config
│   ├── components/
│   │   └── board/
│   │       ├── BoardColumn.tsx       # FR-009: Column rendering, React.memo, card list
│   │       ├── IssueCard.tsx         # FR-009: Card rendering, React.memo, prop stability
│   │       └── AddAgentPopover.tsx   # FR-011: Portal-based popover, positioning listeners
│   ├── pages/
│   │   └── ProjectsPage.tsx          # FR-010: Derived-data computation, sorting, hook orchestration
│   └── components/
│       └── chat/
│           └── ChatPopup.tsx         # FR-011: Drag resize, RAF throttling, event listeners
└── src/
    └── hooks/
        ├── useRealTimeSync.test.tsx   # FR-014: WebSocket fallback and invalidation tests
        └── useBoardRefresh.test.tsx   # FR-014: Refresh timer and deduplication tests
```

**Structure Decision**: Web application (backend + frontend). All changes are edits to existing files — no new modules, components, or dependencies. This follows the Simplicity principle (Constitution V).

## Complexity Tracking

> No violations found. No complexity justifications needed.

All optimization changes are minimal, targeted edits:
- Backend: Verify existing Spec 022 implementations, tighten remaining gaps in change detection and polling
- Frontend: Stabilize derived data with `useMemo`, ensure callback stability with `useCallback`, verify React.memo effectiveness, add throttling to unthrottled event listeners
- No new abstractions, no new dependencies, no architectural changes

## Constitution Check — Post-Design Re-evaluation

*Re-evaluated after Phase 1 design artifacts (research.md, data-model.md, contracts/, quickstart.md) are complete.*

| Principle | Status | Post-Design Notes |
|-----------|--------|-------------------|
| I. Specification-First | ✅ PASS | All design artifacts trace back to spec requirements (FR-001–FR-015, SC-001–SC-010). No scope creep beyond spec boundaries |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates. plan.md, research.md, data-model.md, contracts/internal-contracts.md, and quickstart.md match the established structure from prior specs (e.g., 022-api-rate-limit-protection) |
| III. Agent-Orchestrated | ✅ PASS | Plan phase produced all required outputs. Ready for handoff to `/speckit.tasks` for Phase 2 task generation |
| IV. Test Optionality | ✅ PASS | Spec explicitly mandates regression coverage (FR-014, User Story 7). Test extension strategy documented in research.md (R8). Tests extend existing suites rather than creating new infrastructure |
| V. Simplicity and DRY | ✅ PASS | Research confirmed Spec 022 is fully implemented — no rework needed. All remaining changes are targeted edits: `useMemo`/`useCallback` in ProjectsPage, RAF gating in AddAgentPopover. No new modules, no new dependencies, no architectural changes. Virtualization and service decomposition explicitly deferred |

**Post-Design Gate Result**: PASS — no violations introduced during design phase. Ready for Phase 2 (`/speckit.tasks`).
