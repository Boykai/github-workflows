# Implementation Plan: Performance Review

**Branch**: `032-performance-review` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/032-performance-review/spec.md`

## Summary

Balanced first-pass performance optimization across backend and frontend. The approach captures quantitative baselines first, then targets the highest-value fixes: backend GitHub API churn around board refreshes and idle polling, and frontend board responsiveness caused by broad query invalidation, full-list rerenders, and hot event listeners. The implementation uses existing cache infrastructure (InMemoryCache with TTL), TanStack React Query invalidation strategies, React.memo patterns already present in board components, and requestAnimationFrame gating already used in ChatPopup. Broader architectural refactors (virtualization, service decomposition) are deferred to a follow-on phase unless first-pass measurements prove them necessary.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript ~5.9 (frontend)
**Primary Dependencies**: FastAPI 0.135+, TanStack React Query 5.90+, React 19.2, Vite 7.3, githubkit 0.14+
**Storage**: In-memory cache with TTL (backend `InMemoryCache`), aiosqlite for durable settings; TanStack Query cache (frontend)
**Testing**: pytest 9+ / pytest-asyncio (backend), Vitest 4+ / Testing Library / Playwright (frontend)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: <100 idle API calls/hour (down from ~1,000+), <5 API calls per warm-cache board refresh (down from 23+), <100ms board interaction response, smooth 60fps scrolling on 50+ card boards
**Constraints**: No new dependencies in first pass, no virtualization unless measurements require it, all existing tests must continue passing
**Scale/Scope**: Boards with 5+ columns and 50+ cards; shared rate-limit token across users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 6 prioritized user stories, Given-When-Then scenarios, edge cases, and measurable success criteria |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md; tasks.md deferred to /speckit.tasks |
| **IV. Test Optionality** | ✅ PASS | Spec explicitly requires test coverage (FR-015, FR-016); existing test suites serve as regression guardrails with targeted extensions |
| **V. Simplicity and DRY** | ✅ PASS | First pass scoped to low-risk optimizations using existing patterns (React.memo, useMemo, RAF gating, cache TTL). No premature abstraction. Complexity (virtualization, decomposition) explicitly deferred |

**Gate Result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/032-performance-review/
├── plan.md              # This file
├── research.md          # Phase 0: technical research and decisions
├── data-model.md        # Phase 1: entity model for performance domain
├── quickstart.md        # Phase 1: quick reference for implementers
├── contracts/           # Phase 1: interface contracts
│   ├── cache-contract.md
│   └── refresh-contract.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (already exists)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── board.py             # Board data endpoint, cache behavior, manual refresh
│   │   ├── projects.py          # Projects/tasks endpoints, WebSocket subscription
│   │   └── workflow.py          # Workflow endpoint (duplicate repo resolution target)
│   ├── services/
│   │   ├── cache.py             # InMemoryCache, TTL helpers, cache key functions
│   │   ├── copilot_polling/
│   │   │   └── polling_loop.py  # 5-step polling loop, adaptive backoff, rate-limit aware
│   │   └── github_projects/
│   │       └── service.py       # Board/project fetching, sub-issue caching, reconciliation
│   └── utils.py                 # Shared resolve_repository() 3-step fallback
└── tests/unit/
    ├── test_cache.py            # Cache TTL, expiration, clear_expired coverage
    ├── test_api_board.py        # Board endpoint behavior, cache bypass, rate-limit errors
    └── test_copilot_polling.py  # Polling loop, rate-limit aware logic, activity detection

frontend/
├── src/
│   ├── hooks/
│   │   ├── useRealTimeSync.ts       # WebSocket + polling fallback, message-driven invalidation
│   │   ├── useBoardRefresh.ts       # Manual/auto refresh, Page Visibility API, deduplication
│   │   ├── useProjectBoard.ts       # Board data query, project selection
│   │   ├── useRealTimeSync.test.tsx  # WebSocket/polling test coverage
│   │   └── useBoardRefresh.test.tsx  # Refresh timer, dedup, visibility API tests
│   ├── components/
│   │   ├── board/
│   │   │   ├── BoardColumn.tsx      # React.memo column rendering
│   │   │   ├── IssueCard.tsx        # React.memo card with collapsible sub-issues
│   │   │   └── AddAgentPopover.tsx  # Portal positioning with scroll/resize listeners
│   │   └── chat/
│   │       └── ChatPopup.tsx        # RAF-gated drag resize
│   └── pages/
│       └── ProjectsPage.tsx         # Board page with useMemo derived state
└── e2e/                             # Playwright E2E tests
```

**Structure Decision**: Existing web application layout (backend/ + frontend/) is used. No structural changes needed — all optimizations apply within existing file boundaries.

## Post-Design Constitution Re-Check

*Re-evaluation after Phase 1 design artifacts (data-model.md, contracts/, quickstart.md) are complete.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec.md requirements (FR-001 through FR-016, SC-001 through SC-008) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow canonical structure |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0 (research) and Phase 1 (design) complete; tasks.md deferred to /speckit.tasks as expected |
| **IV. Test Optionality** | ✅ PASS | Test extensions defined in research.md Area 6; targeted additions to existing suites, no new test infrastructure |
| **V. Simplicity and DRY** | ✅ PASS | No new abstractions introduced. Contracts reference existing patterns (React.memo, useMemo, RAF, InMemoryCache). No unnecessary complexity |

**Gate Result**: ALL PASS — design phase complete, ready for /speckit.tasks.

## Complexity Tracking

> No Constitution Check violations requiring justification. All optimizations use existing patterns and infrastructure.
