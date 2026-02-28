# Implementation Plan: Add Manual Refresh Button & Auto-Refresh to Project Board with GitHub API Rate Limit Optimization

**Branch**: `014-board-refresh-ratelimit` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-board-refresh-ratelimit/spec.md`

## Summary

Add a manual refresh button with tooltip and a 5-minute auto-refresh timer to the project board, integrated with the existing `useRealTimeSync` WebSocket/polling infrastructure. Implement a centralized GitHub API client layer with ETag-based conditional requests, response caching with TTL, request deduplication, and rate-limit-aware error handling. The auto-refresh pauses when the browser tab is hidden (Page Visibility API) and resumes with an immediate refresh when the tab regains focus. Rate limit errors display a non-intrusive warning with reset time countdown.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.4 / Node 20 (frontend)
**Primary Dependencies**: FastAPI, React 18, Vite 5, TanStack Query v5, httpx (backend HTTP client)
**Storage**: In-memory cache (`backend/src/services/cache.py` — `InMemoryCache` with TTL)
**Testing**: pytest 7.4+ / pytest-asyncio (backend), Vitest 4.0+ / @testing-library/react (frontend)
**Target Platform**: Linux server (backend), Modern browsers (frontend)
**Project Type**: web (backend + frontend)
**Performance Goals**: Manual refresh completes within 5 seconds under normal network conditions; auto-refresh every 5 minutes; rapid clicks (5 within 1 second) result in at most 1 API call
**Constraints**: Must not exhaust GitHub API rate limit (5,000 req/hr authenticated) during an 8-hour workday; conditional requests (304 Not Modified) should not count against rate limit; no new external dependencies
**Scale/Scope**: Single project board per browser tab; 2 backend board endpoints (`/board/projects`, `/board/projects/{id}`); 1 GraphQL query per board refresh cycle; existing WebSocket + polling fallback in `useRealTimeSync`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md exists with 4 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, edge cases, and scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase follows single-responsibility agent model with well-defined inputs and outputs |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are not explicitly mandated in the spec; implementation may add tests where the existing test infrastructure supports it, but they are not required |
| V. Simplicity and DRY | ✅ PASS | Design reuses existing infrastructure (TanStack Query, `useRealTimeSync`, `InMemoryCache`, `_request_with_retry`); new components are minimal extensions of existing patterns |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/014-board-refresh-ratelimit/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Entity model for refresh/cache/rate-limit state
├── quickstart.md        # Phase 1: Developer quickstart
├── contracts/           # Phase 1: API contracts
│   └── board-refresh-api.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT this phase)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── board.py             # MODIFIED: Add rate limit headers to responses
│   ├── services/
│   │   ├── cache.py             # MODIFIED: Add ETag support to InMemoryCache
│   │   └── github_projects/
│   │       ├── service.py       # MODIFIED: Return rate limit headers from _graphql/_request_with_retry
│   │       └── graphql.py       # Existing GraphQL queries (unchanged)
│   └── models/
│       └── board.py             # MODIFIED: Add rate_limit fields to BoardDataResponse
└── tests/
    └── unit/
        └── test_api_board.py    # Existing tests (may be extended)

frontend/
├── src/
│   ├── components/
│   │   └── board/
│   │       └── RefreshButton.tsx     # NEW: Manual refresh button with tooltip
│   ├── hooks/
│   │   ├── useProjectBoard.ts        # MODIFIED: Add manual refresh + auto-refresh timer
│   │   ├── useRealTimeSync.ts        # MODIFIED: Integrate with refresh timer, add Page Visibility
│   │   └── useBoardRefresh.ts        # NEW: Centralized refresh orchestration hook
│   ├── pages/
│   │   └── ProjectBoardPage.tsx      # MODIFIED: Add RefreshButton, rate limit warning UI
│   ├── services/
│   │   └── api.ts                    # MODIFIED: Add rate limit header parsing to boardApi
│   ├── constants.ts                  # MODIFIED: Add AUTO_REFRESH_INTERVAL_MS constant
│   └── types/
│       └── index.ts                  # MODIFIED: Add RateLimitInfo type
└── tests/                            # Existing test infrastructure
```

**Structure Decision**: Web application (backend + frontend). All changes extend the existing `backend/src/api/board.py`, `backend/src/services/`, `frontend/src/hooks/`, `frontend/src/components/board/`, and `frontend/src/pages/ProjectBoardPage.tsx` modules. One new component (`RefreshButton.tsx`) and one new hook (`useBoardRefresh.ts`) are introduced to encapsulate refresh logic without modifying unrelated code.

## Complexity Tracking

> No constitution violations to justify. All principles are satisfied. The design reuses existing infrastructure (TanStack Query for caching/deduplication, `useRealTimeSync` for WebSocket/polling, `InMemoryCache` for server-side caching, `_request_with_retry` for backoff) and introduces minimal new abstractions.

## Constitution Re-Check (Post Phase 1 Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All design artifacts trace back to spec.md requirements (FR-001 through FR-016) |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow canonical structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produced well-defined outputs for handoff to tasks phase |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not mandated; existing test files may be extended but no new test infrastructure required |
| V. Simplicity and DRY | ✅ PASS | Design favors extending existing hooks/services over new abstractions; `useBoardRefresh` consolidates refresh logic that would otherwise be scattered across multiple components; ETag caching reuses existing `InMemoryCache` |

**Post-Design Gate Result**: ✅ ALL PASS — ready for Phase 2 (tasks generation via `/speckit.tasks`).
