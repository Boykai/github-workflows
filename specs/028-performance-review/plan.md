# Implementation Plan: Performance Review — Balanced First Pass

**Branch**: `028-performance-review` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/028-performance-review/spec.md`

## Summary

Deliver a balanced, measurement-driven first pass of performance optimizations across backend and frontend. Backend work targets remaining GitHub API churn around board refreshes and polling — verifying Spec 022 completion, tightening WebSocket change-detection refresh semantics, warming sub-issue caches, and eliminating fallback-polling-triggered board refreshes. Frontend work targets board responsiveness — decoupling lightweight task updates from the expensive board query, stabilizing callback props for memoized components (BoardColumn, IssueCard), memoizing remaining derived state in ProjectsPage, and debouncing hot event listeners in AddAgentPopover. All changes are gated on baseline measurements captured before any optimization code lands, and validated with before/after comparisons using a repeatable measurement protocol.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.9 (frontend), Node 22 (build)
**Primary Dependencies**: FastAPI, githubkit, pydantic 2.x, aiosqlite, React 19.2, TanStack Query, Vite 7.3
**Storage**: SQLite with WAL mode (aiosqlite) — sessions, settings; in-memory cache (`backend/src/services/cache.py`)
**Testing**: pytest + pytest-asyncio (backend), Vitest (frontend)
**Target Platform**: Docker Compose (Linux containers), nginx reverse proxy
**Project Type**: Web application (FastAPI backend + React frontend)
**Performance Goals**: ≤2 idle API calls/5 min, <2s perceived single-card update, ≥30 fps board drag, ≤3 component re-renders per single-card change, ≥80% sub-issue cache hit rate on automatic refresh
**Constraints**: Zero feature regressions; no new frontend dependencies; no virtualization or major service decomposition in first pass; all improvements proven with before/after baselines
**Scale/Scope**: ~10 backend files modified, ~8 frontend files modified; target board size 50–200 cards across 3–7 columns

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — PASS

Feature work began with explicit specification (`spec.md`) containing 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios for each, clear scope boundaries (board virtualization, major refactors, new dependencies out of scope), edge case analysis, and 10 measurable success criteria.

### II. Template-Driven Workflow — PASS

All artifacts follow canonical templates: `spec.md` from spec-template, `plan.md` from plan-template. No custom sections added without justification.

### III. Agent-Orchestrated Execution — PASS

Workflow follows the specify → plan → tasks → implement sequence. Each phase produces specific outputs and hands off to the next agent. The plan phase generates `research.md`, `data-model.md`, `contracts/`, and `quickstart.md` before proceeding.

### IV. Test Optionality with Clarity — PASS

The spec mandates baseline measurement (FR-001) and regression coverage (FR-015) as functional requirements. New unit tests are added only for areas directly modified by optimization changes (cache behavior, refresh hooks, component memoization). Existing test suites serve as regression gates. Tests are mandatory where the spec explicitly requires them, optional otherwise.

### V. Simplicity and DRY — PASS

Changes are strictly scoped to performance remediation. No new abstractions beyond what existing patterns support. Memoization uses standard `React.memo`/`useMemo`/`useCallback`. Backend changes use the existing cache service infrastructure. No new dependencies introduced. YAGNI is respected by deferring virtualization and service decomposition to a potential Phase 4.

**GATE RESULT: ALL PASS — proceed to Phase 0.**

### Post-Phase 1 Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All 16 FRs traced to design artifacts |
| II. Template-Driven | ✅ PASS | All plan artifacts follow templates |
| III. Agent-Orchestrated | ✅ PASS | Plan → tasks → implement pipeline maintained |
| IV. Test Optionality | ✅ PASS | Regression tests required by spec; new tests only for modified areas |
| V. Simplicity/DRY | ✅ PASS | No new dependencies; no new abstractions; standard React/Python patterns only |

## Project Structure

### Documentation (this feature)

```text
specs/028-performance-review/
├── plan.md              # This file
├── spec.md              # Feature specification (complete)
├── research.md          # Phase 0: Performance research and Spec 022 audit
├── data-model.md        # Phase 1: Cache, refresh, and baseline entity definitions
├── quickstart.md        # Phase 1: Verification commands and measurement protocol
├── contracts/           # Phase 1: Refresh and caching contracts
│   ├── refresh-contract.md
│   └── cache-contract.md
├── checklists/
│   └── requirements.md  # Quality checklist (complete)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── board.py             # FR-007,008,009: Sub-issue cache, manual refresh bypass
│   │   └── projects.py          # FR-003,013: WebSocket change detection, reconnection guard
│   ├── services/
│   │   ├── cache.py             # FR-008,009: Sub-issue cache TTL, bounded cache
│   │   ├── copilot_polling/
│   │   │   └── polling_loop.py  # FR-004: Polling-triggered refresh guard
│   │   └── github_projects/
│   │       └── service.py       # FR-008: Sub-issue caching in fetch path
│   └── utils.py                 # Shared repository resolution (no changes expected)
└── tests/
    └── unit/
        ├── test_cache.py            # FR-015: Cache TTL regression tests
        ├── test_api_board.py        # FR-015: Board cache regression tests
        └── test_copilot_polling.py  # FR-015: Polling regression tests

frontend/
├── src/
│   ├── hooks/
│   │   ├── useRealTimeSync.ts       # FR-005,013: Decouple task updates from board query
│   │   ├── useBoardRefresh.ts       # FR-006,014: Manual refresh priority, dedup
│   │   └── useProjectBoard.ts       # FR-005: Board query invalidation strategy
│   ├── components/
│   │   ├── board/
│   │   │   ├── BoardColumn.tsx      # FR-010: Already React.memo; stabilize function props
│   │   │   └── IssueCard.tsx        # FR-010: Already React.memo; stabilize function props
│   │   ├── chat/
│   │   │   └── ChatPopup.tsx        # FR-012: Already RAF-gated drag (verified)
│   │   └── agents/
│   │       └── AddAgentPopover.tsx   # FR-012: Debounce scroll/resize position listeners
│   └── pages/
│       └── ProjectsPage.tsx         # FR-011: useMemo for remaining inline derivations, useCallback for handlers
└── tests/
    └── hooks/
        ├── useRealTimeSync.test.tsx  # FR-015: Refresh invalidation regression tests
        └── useBoardRefresh.test.tsx  # FR-015: Refresh timer regression tests
```

**Structure Decision**: Existing web application layout (backend/ + frontend/). No new directories or files beyond contracts/. All changes are in-place modifications to existing files using standard patterns already present in the codebase.

## Complexity Tracking

> No constitution violations. No complexity justification needed.
>
> All optimizations use standard patterns: `React.memo`/`useMemo`/`useCallback` for frontend memoization, existing in-memory cache service for backend caching, and standard hash-based change detection already present in the WebSocket subscription flow. No new abstractions or dependencies are introduced.
>
> **Notable current-state findings that reduce scope:**
> - `BoardColumn` and `IssueCard` are already wrapped in `React.memo()` — work shifts to stabilizing parent-supplied function props.
> - `ChatPopup` drag listeners already use `requestAnimationFrame` gating — no further throttling needed.
> - `useRealTimeSync` already decouples task invalidation from board data invalidation — verify and extend (reconnection debounce already present at 2s window).
> - `useBoardRefresh` already uses `useCallback` for timer functions — verify manual refresh cancellation.
> - `ProjectsPage` already memoizes `blockingIssueNumbers` and `assignedStageMap` — remaining work is stabilizing event handlers and a few inline derivations.
