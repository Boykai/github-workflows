# Implementation Plan: Performance Review

**Branch**: `037-performance-review` | **Date**: 2026-03-12 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/037-performance-review/spec.md`

## Summary

Deliver a balanced first-pass performance optimization across backend and frontend, targeting measurable reductions in idle API activity, sub-issue cache waste, unnecessary board refreshes, and frontend rerender volume. All changes are preceded by baseline measurement and validated against specific success criteria. Heavy architectural changes (virtualization, service decomposition, new dependencies) are explicitly deferred unless first-pass metrics prove them necessary. Research confirms that Spec 022 cache and refresh behaviors are substantially implemented; remaining work targets gaps in sub-issue cache reuse, fallback polling change detection, callback prop stability, and regression test coverage.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.9 / React 19.2 (frontend)  
**Primary Dependencies**: FastAPI, aiosqlite, githubkit, httpx, websockets (backend); TanStack React Query v5.90, @dnd-kit v6.3, Vite 7.3 (frontend)  
**Storage**: SQLite via aiosqlite (session/settings); InMemoryCache for board/sub-issue/project data  
**Testing**: pytest + pytest-asyncio (backend, 1736+ tests); Vitest + Testing Library (frontend, 644+ tests)  
**Target Platform**: Web application — Docker (Nginx 1.27-alpine frontend, Python backend), SPA with WebSocket + polling fallback  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: ≥50% reduction in idle API calls (5 min window); ≥30% fewer outbound calls with warm sub-issue caches; single-task update <2s without full board reload; zero unnecessary full refreshes during fallback polling  
**Constraints**: No new external dependencies; no board virtualization; no major service decomposition in first pass; all existing tests must continue to pass  
**Scale/Scope**: Boards with 50–100 tasks across 4–8 columns (representative production usage); optimization targets this range with graceful degradation for larger boards

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅
Feature spec (`spec.md`) includes 6 prioritized user stories (P1–P3) with independent testing criteria and Given-When-Then acceptance scenarios. Scope boundaries and out-of-scope declarations are explicit.

### II. Template-Driven Workflow ✅
All artifacts follow canonical templates: `plan.md` (this file), `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`. No custom sections added without justification.

### III. Agent-Orchestrated Execution ✅
Plan phase produces well-defined outputs (research, data model, contracts, quickstart) that feed into the tasks phase. Each phase has clear inputs and outputs.

### IV. Test Optionality with Clarity ✅
Tests are included because:
- Spec explicitly requires regression coverage (User Story 5, FR-011)
- Extending existing test suites (not creating new infrastructure)
- Test assertions validate the specific optimizations being delivered

### V. Simplicity and DRY ✅
All proposed changes are low-risk optimizations within existing code structure. No new abstractions, no new dependencies, no service decomposition. Changes reuse existing cache infrastructure, hash computation, and React memoization patterns already in the codebase. YAGNI is respected by deferring virtualization and heavier changes.

**Gate Result**: PASS — all constitution principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/037-performance-review/
├── plan.md              # This file
├── research.md          # Phase 0 output — resolved unknowns and best practices
├── data-model.md        # Phase 1 output — entity definitions and state machines
├── quickstart.md        # Phase 1 output — developer onboarding guide
├── contracts/           # Phase 1 output — behavioral contracts
│   ├── refresh-policy.md    # Board data refresh rules
│   ├── cache-behavior.md    # Backend caching contracts
│   └── render-behavior.md   # Frontend rendering rules
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── board.py           # Board data endpoint — sub-issue cache reuse
│   │   ├── projects.py        # WebSocket subscription — change detection
│   │   └── workflow.py        # Duplicate repo resolution (review only)
│   ├── services/
│   │   ├── cache.py           # Cache infrastructure — TTL alignment
│   │   ├── copilot_polling/
│   │   │   └── polling_loop.py  # Polling hot path — idle behavior
│   │   └── github_projects/
│   │       └── service.py     # GitHub API client — inflight coalescing
│   └── utils.py               # Shared utilities
└── tests/
    └── unit/
        ├── test_cache.py          # Cache behavior regression
        ├── test_api_board.py      # Board endpoint regression
        └── test_copilot_polling.py  # Polling behavior regression

frontend/
├── src/
│   ├── hooks/
│   │   ├── useRealTimeSync.ts      # WebSocket + polling — change detection
│   │   ├── useBoardRefresh.ts      # Refresh orchestration — debounce
│   │   ├── useProjectBoard.ts      # Board query — stale times
│   │   ├── useRealTimeSync.test.tsx  # Sync hook tests
│   │   └── useBoardRefresh.test.tsx  # Refresh hook tests
│   ├── components/
│   │   ├── board/
│   │   │   ├── BoardColumn.tsx    # Column rendering — memo verification
│   │   │   └── IssueCard.tsx      # Card rendering — memo verification
│   │   ├── chat/
│   │   │   └── ChatPopup.tsx      # Drag listener — already optimized
│   │   └── agents/
│   │       └── AddAgentPopover.tsx  # Positioning — already optimized
│   └── pages/
│       └── ProjectsPage.tsx       # Board page — callback stability
└── tests/
```

**Structure Decision**: Existing web application structure (backend + frontend) is used as-is. No new directories or modules are introduced. All changes are within existing files.

## Complexity Tracking

> No constitution violations detected. This section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
