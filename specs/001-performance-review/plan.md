# Implementation Plan: Performance Review

**Branch**: `001-performance-review` | **Date**: 2026-03-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-performance-review/spec.md`

## Summary

Deliver a balanced first-pass performance optimization across backend and frontend. The approach starts by capturing measurable baselines, then targets the highest-value issues already identified in the codebase: backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. All changes are low-risk; heavier architectural work (virtualization, service decomposition) is explicitly deferred unless first-pass measurements prove it necessary. The work builds on existing rate-limit protection (Spec 022 patterns already present in caching, change detection, and polling backoff), completing any remaining gaps rather than redoing completed items.

## Technical Context

**Language/Version**: Python ≥ 3.12 (Ruff targets 3.13, Pyright targets 3.13) · TypeScript ~5.9 (strict mode, ES2022 target)
**Primary Dependencies**: FastAPI ≥ 0.135, githubkit ≥ 0.14.6, httpx ≥ 0.28, Pydantic ≥ 2.12 (backend) · React 19.2, TanStack React Query 5.90, Vite, @dnd-kit (frontend)
**Storage**: SQLite via aiosqlite (session/config) · In-memory TTL cache (`InMemoryCache` in `services/cache.py`)
**Testing**: pytest ≥ 9.0 + pytest-asyncio (auto mode) · Vitest + @testing-library/react 16.3 + Playwright 1.58
**Target Platform**: Linux server (backend) · Modern browsers (frontend, ES2022)
**Project Type**: Web application (monorepo: `solune/backend/` + `solune/frontend/`)
**Performance Goals**: ≥ 50% reduction in idle outbound service calls (SC-001) · ≥ 30% fewer calls with warm sub-issue cache (SC-002) · Single-task update reflected in UI < 2 s without full reload (SC-003) · Zero unnecessary full refreshes during fallback polling (SC-004) · Measurable interaction latency improvement on 50+ task boards (SC-005) · Rerenders scoped to affected card + container only (SC-006)
**Constraints**: No new external dependencies · No board virtualization · No major service decomposition · All existing tests must continue to pass (SC-007)
**Scale/Scope**: Representative board: 50–100 tasks across 4–8 columns · Concurrent open board sessions sharing rate-limit budget

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate (Phase 0 entry)

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | `spec.md` exists with 7 prioritized user stories (P1–P3), Given-When-Then scenarios, scope boundaries, and measurable success criteria. |
| II | Template-Driven Workflow | ✅ PASS | Spec follows canonical template; this plan follows `plan-template.md`. |
| III | Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` agent produces plan, research, data-model, contracts, quickstart; hand-off to `speckit.tasks` is explicit. |
| IV | Test Optionality with Clarity | ✅ PASS | Spec FR-014 mandates regression test extension; User Story 6 (P3) covers verification. Tests are required here by spec, not by default. |
| V | Simplicity and DRY | ✅ PASS | First pass is intentionally low-risk. Heavier work deferred. No premature abstraction. Existing patterns reused. |

**Gate Result**: ✅ All principles satisfied. Proceeding to Phase 0.

### Post-Design Gate (re-evaluated after Phase 1)

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | Design artifacts (data-model, contracts) trace back to spec user stories and FRs. |
| II | Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates. |
| III | Agent-Orchestrated Execution | ✅ PASS | Plan output is complete; hand-off to `speckit.tasks` is clear. |
| IV | Test Optionality with Clarity | ✅ PASS | Test tasks explicitly required per FR-014 and SC-008. Red-Green-Refactor not mandated; tests extend existing suites. |
| V | Simplicity and DRY | ✅ PASS | Design reuses existing cache, query, and hook infrastructure. No new abstractions introduced. Complexity tracking section is empty (no violations). |

**Gate Result**: ✅ All principles satisfied post-design.

## Project Structure

### Documentation (this feature)

```text
specs/001-performance-review/
├── plan.md              # This file
├── research.md          # Phase 0: research findings and decisions
├── data-model.md        # Phase 1: key entities and state model
├── quickstart.md        # Phase 1: developer quick-start guide
├── contracts/           # Phase 1: internal API contracts
│   ├── backend-refresh-contract.md
│   └── frontend-refresh-policy.md
├── checklists/
│   └── requirements.md  # Pre-existing spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT this command)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── board.py              # Board cache, manual refresh, sub-issue invalidation
│   │   │   ├── projects.py           # WebSocket subscription, change detection, task endpoints
│   │   │   └── workflow.py           # Duplicate repo resolution (refactor candidate)
│   │   ├── services/
│   │   │   ├── cache.py              # InMemoryCache, TTL, data hashing, cached_fetch
│   │   │   ├── copilot_polling/
│   │   │   │   └── polling_loop.py   # Adaptive backoff, rate-limit-aware polling
│   │   │   └── github_projects/
│   │   │       └── service.py        # GraphQL/REST calls, inflight coalescing, cycle cache
│   │   └── utils.py                  # Repository resolution, BoundedDict/BoundedSet
│   └── tests/unit/
│       ├── test_cache.py             # Cache TTL, data hash, concurrent safety
│       ├── test_api_board.py         # Board cache, refresh bypass, sub-issue invalidation
│       └── test_copilot_polling.py   # Polling loop, rate-limit budget, stale cleanup
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   ├── useRealTimeSync.ts        # WebSocket + polling fallback, selective invalidation
│   │   │   ├── useRealTimeSync.test.tsx   # Fallback, debounce, query scope tests
│   │   │   ├── useBoardRefresh.ts         # 5-min auto-refresh, manual refresh, deduplication
│   │   │   ├── useBoardRefresh.test.tsx   # Timer, dedup, visibility, rate-limit tests
│   │   │   └── useProjectBoard.ts         # TanStack Query owner for board data
│   │   ├── components/
│   │   │   ├── board/
│   │   │   │   ├── BoardColumn.tsx    # Column rendering (already memo'd)
│   │   │   │   └── IssueCard.tsx      # Card rendering (already memo'd)
│   │   │   ├── chat/
│   │   │   │   └── ChatPopup.tsx      # Drag-to-resize (already RAF-throttled)
│   │   │   └── agents/
│   │   │       └── AddAgentPopover.tsx # Portal popover (already RAF-throttled)
│   │   └── pages/
│   │       └── ProjectsPage.tsx       # Board orchestration, derived state, hero stats
│   └── tests/
└── specs/
    └── 001-performance-review/        # This feature's artifacts
```

**Structure Decision**: Web application (Option 2). The existing monorepo structure under `solune/` with `backend/` and `frontend/` directories is used directly. No new directories or packages are created; all changes modify existing files or extend existing test suites.

## Complexity Tracking

> No constitution violations detected. This section is intentionally empty.
