# Implementation Plan: Performance Review

**Branch**: `001-performance-review` | **Date**: 2026-03-26 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-performance-review/spec.md`

## Summary

Balanced first-pass performance optimization across backend and frontend. The plan starts with mandatory baseline measurement, then targets the highest-value issues already identified in the codebase: backend GitHub API churn around board refreshes/polling, and frontend board responsiveness problems caused by broad query invalidation, full-list rerenders, and hot interaction handlers. Research confirmed that the existing codebase already has strong foundations (300s cache TTL, data-hash change detection, WebSocket with polling fallback, adaptive polling) — the work focuses on proving current behavior with measurements and tightening only the remaining gaps rather than introducing new architecture. Board virtualization, major service decomposition, and new dependencies are explicitly deferred unless first-pass measurements prove them necessary.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript/React 19 (frontend)  
**Primary Dependencies**: FastAPI ≥0.135, TanStack React Query 5.91, dnd-kit, Radix UI, websockets ≥16.0  
**Storage**: SQLite via aiosqlite (sessions, settings, done-items fallback)  
**Testing**: pytest ≥9.0 + pytest-asyncio (backend), Vitest 4.0 + @testing-library/react (frontend)  
**Target Platform**: Linux server (backend), modern browsers (frontend)  
**Project Type**: Web application (backend + frontend monorepo under `solune/`)  
**Performance Goals**: ≥50% reduction in idle board API calls over 5 min; sub-second UI feedback for common board interactions; zero unnecessary full-board refetches on lightweight task updates  
**Constraints**: No new external dependencies; no board virtualization or major service decomposition in first pass; 75% backend test coverage minimum  
**Scale/Scope**: Representative board: 5+ columns, 20+ cards. Extreme boards (100+ columns, 500+ cards) deferred to optional second-wave.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md complete with prioritized user stories (P1–P4), Given-When-Then acceptance scenarios, clear scope boundaries, and out-of-scope declarations |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan produced by `speckit.plan` agent; hands off to `speckit.tasks` for Phase 2 |
| IV. Test Optionality with Clarity | ✅ PASS | Tests explicitly required by spec (FR-015, FR-016); extends existing test files rather than creating new framework |
| V. Simplicity and DRY | ✅ PASS | First pass targets low-risk optimizations (memoization, throttling, cache tightening). No premature abstraction. Virtualization/decomposition deferred unless measurements justify them |

**Gate Result**: ALL PASS — proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/001-performance-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── refresh-policy.md
│   └── cache-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── board.py          # Board data cache, manual refresh, sub-issue invalidation
│   │   │   ├── projects.py       # WebSocket subscription, change detection, refresh semantics
│   │   │   └── workflow.py       # Workflow endpoints (uses shared resolve_repository)
│   │   ├── services/
│   │   │   ├── cache.py          # InMemoryCache, TTLs, hash-based change detection
│   │   │   ├── copilot_polling/
│   │   │   │   └── polling_loop.py  # Polling hot path, rate-limit-aware step skipping
│   │   │   └── github_projects/
│   │   │       └── service.py    # Board/project fetching, sub-issue caching
│   │   └── utils.py              # BoundedDict/Set, resolve_repository (single source)
│   └── tests/
│       └── unit/
│           ├── test_cache.py          # Cache TTL, stale fallback, hash comparison
│           ├── test_api_board.py      # Board cache, endpoint behavior
│           └── test_copilot_polling.py # Polling behavior, rate-limit logic
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   ├── useRealTimeSync.ts       # WebSocket/polling fallback, query invalidation
│   │   │   ├── useBoardRefresh.ts       # Auto-refresh timer, manual refresh, deduplication
│   │   │   ├── useProjectBoard.ts       # Board query, adaptive polling, change detection
│   │   │   ├── useRealTimeSync.test.tsx  # WebSocket/fallback coverage
│   │   │   └── useBoardRefresh.test.tsx  # Refresh timer/dedup coverage
│   │   ├── components/
│   │   │   ├── board/
│   │   │   │   ├── BoardColumn.tsx       # Column rendering, drag-drop target
│   │   │   │   ├── IssueCard.tsx         # Card rendering, sub-issue expansion
│   │   │   │   └── AddAgentPopover.tsx   # Agent popover interactions
│   │   │   └── chat/
│   │   │       └── ChatPopup.tsx         # Drag listener, resize handling
│   │   └── pages/
│   │       └── ProjectsPage.tsx          # Board orchestrator, derived state
│   └── tests/
```

**Structure Decision**: Existing web application monorepo under `solune/` with separate `backend/` and `frontend/` directories. All changes target existing files — no new directories or structural changes required.

## Constitution Check — Post-Design Re-Evaluation

*Re-evaluated after Phase 1 design artifacts (research.md, data-model.md, contracts/, quickstart.md) are complete.*

| Principle | Status | Post-Design Notes |
|-----------|--------|-------------------|
| I. Specification-First Development | ✅ PASS | Design artifacts trace directly to spec requirements (FR-001–FR-017, SC-001–SC-008). All research findings reference spec requirement IDs. |
| II. Template-Driven Workflow | ✅ PASS | All Phase 0 and Phase 1 outputs follow canonical structure. Contracts use consistent table-based format. |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan hands off to `speckit.tasks` for Phase 2 task generation. Clear inputs (this plan + contracts) and outputs (tasks.md) defined. |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are explicitly required by FR-015 and FR-016. Test scope is defined: extend existing test files (test_cache.py, test_api_board.py, useRealTimeSync.test.tsx, useBoardRefresh.test.tsx). No new test framework. |
| V. Simplicity and DRY | ✅ PASS | Research confirmed no repository resolution duplication (R-006). All optimizations use existing patterns (React.memo, useMemo, throttle) — no new abstractions. Contracts codify existing behavior rather than inventing new patterns. |

**Post-Design Gate Result**: ALL PASS — ready for `speckit.tasks` (Phase 2).

## Complexity Tracking

> No constitution violations detected. No complexity justifications required.
