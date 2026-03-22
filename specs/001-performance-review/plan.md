# Implementation Plan: Performance Review

**Branch**: `001-performance-review` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-performance-review/spec.md`

## Summary

Perform a balanced first pass of measurable, low-risk performance optimizations across the Solune backend and frontend. The approach is phased: first capture performance baselines and verify existing rate-limit protections (Spec 022), then fix the highest-value issues — backend GitHub API churn around board refreshes/polling and frontend board responsiveness caused by broad query invalidation, full-list rerenders, and hot event listeners. Broader architectural refactors (virtualization, service decomposition) are explicitly deferred unless first-pass metrics prove them necessary.

The implementation targets three categories: (1) backend idle API call elimination via WebSocket change detection, sub-issue cache reuse, and polling guard rails; (2) frontend refresh-path cleanup so lightweight task updates stay decoupled from expensive board data queries; (3) low-risk frontend render optimization via derived-data memoization, prop stabilization, and event listener throttling. All changes require before/after baseline measurements and regression test coverage.

## Technical Context

**Language/Version**: Python ≥3.12 (target 3.13) backend; TypeScript ~5.9 frontend  
**Primary Dependencies**: FastAPI 0.135+, TanStack React Query 5.91+, React 19.2+, Vite 8.0+, @dnd-kit 6.3+  
**Storage**: SQLite (aiosqlite) for durable state; in-memory TTL cache (`InMemoryCache`) for hot data  
**Testing**: pytest 9.0+ / Vitest 4.0+ / Playwright 1.58+; ruff 0.15+ / pyright 1.1.408+ / ESLint 10+  
**Target Platform**: Linux server (backend); ES2022 modern browsers (frontend)  
**Project Type**: Web application (backend + frontend monorepo under `solune/`)  
**Performance Goals**: Zero unnecessary idle API calls over 5 min; cached board response <500ms; board interactions >30 FPS on 50+ card boards; ≥30% reduction in component re-renders per task update; ≥50% reduction in idle GitHub API calls  
**Constraints**: No new dependencies in first pass; no virtualization unless baselines prove need; preserve existing 300s board cache TTL and 30s WebSocket check interval  
**Scale/Scope**: Typical board: 50+ cards across 5+ columns; single active project per user session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

The feature spec (`spec.md`) includes six prioritized user stories (P1–P3) with independent testing criteria and Given-When-Then acceptance scenarios. Scope boundaries and out-of-scope declarations are explicit.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates from `.specify/templates/`. This plan follows `plan-template.md`. Research, data-model, contracts, and quickstart artifacts will be generated per the template structure.

### III. Agent-Orchestrated Execution — ✅ PASS

This plan is produced by the `speckit.plan` agent. Subsequent phases (`speckit.tasks`, `speckit.implement`) will receive well-defined inputs from this plan's outputs.

### IV. Test Optionality with Clarity — ✅ PASS

The specification explicitly mandates regression test extension (User Story 5, FR-012, FR-013, SC-010). Tests are required because the feature modifies performance-critical code paths where regressions must be caught. Tests follow existing patterns in `test_cache.py`, `test_api_board.py`, `useRealTimeSync.test.tsx`, and `useBoardRefresh.test.tsx`.

### V. Simplicity and DRY — ✅ PASS

The plan explicitly avoids premature abstraction (no virtualization, no service decomposition, no new dependencies). Changes are targeted at existing code paths. Complexity is kept low: memoization of existing computations, throttling of existing listeners, and cache reuse of existing cache infrastructure.

**Gate Result**: All five constitution principles pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-performance-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── refresh-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── board.py              # Board cache, manual refresh, sub-issue invalidation
│   │   │   ├── projects.py           # WebSocket subscription, change detection, tasks endpoint
│   │   │   └── workflow.py           # Repository resolution (verify DRY with utils.py)
│   │   ├── services/
│   │   │   ├── cache.py              # InMemoryCache, cached_fetch, compute_data_hash
│   │   │   ├── github_projects/
│   │   │   │   └── service.py        # Board/project fetching, sub-issue caching, rate limit tracking
│   │   │   └── copilot_polling/
│   │   │       └── polling_loop.py   # Polling hot path, rate limit budget checking
│   │   └── utils.py                  # Shared repository resolution, BoundedSet/Dict
│   └── tests/
│       └── unit/
│           ├── test_cache.py         # Cache TTL, stale fallback, hash comparison tests
│           ├── test_api_board.py      # Board cache, manual refresh, sub-issue tests
│           └── test_copilot_polling.py # Polling behavior, rate limit tests
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   ├── useRealTimeSync.ts    # WebSocket/polling, query invalidation, debounce
│   │   │   ├── useBoardRefresh.ts    # Auto-refresh, manual refresh, page visibility
│   │   │   ├── useProjectBoard.ts    # Board query keys, stale times, invalidation
│   │   │   ├── useRealTimeSync.test.tsx
│   │   │   └── useBoardRefresh.test.tsx
│   │   ├── components/
│   │   │   ├── board/
│   │   │   │   ├── BoardColumn.tsx   # Memoized column, card rendering, drop zone
│   │   │   │   └── IssueCard.tsx     # Memoized card, draggable, sub-issues
│   │   │   ├── chat/
│   │   │   │   └── ChatPopup.tsx     # Resize listeners, RAF-gated mousemove
│   │   │   └── agents/
│   │   │       └── AddAgentModal.tsx # Modal-based (not popover), no hot listeners
│   │   └── pages/
│   │       └── ProjectsPage.tsx      # Derived data (heroStats, rateLimitState, syncStatus)
│   └── tests/
```

**Structure Decision**: Web application layout. The repository already uses the `solune/backend/` and `solune/frontend/` structure. This feature modifies existing files in both; no new directories are needed.

## Complexity Tracking

> No constitution violations detected. No complexity justifications required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
