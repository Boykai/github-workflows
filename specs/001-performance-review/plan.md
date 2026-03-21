# Implementation Plan: Performance Review

**Branch**: `001-performance-review` | **Date**: 2026-03-21 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-performance-review/spec.md`

## Summary

Deliver a balanced first pass of measurable, low-risk performance gains across backend and frontend. The approach is measurement-first: capture baselines, then fix the highest-value issues already surfaced by the codebase — backend GitHub API churn around board refreshes and polling, and frontend board responsiveness issues caused by broad query invalidation, full-list rerenders, and hot event listeners. Research confirms the core cache and change-detection mechanisms are already implemented; this work focuses on verifying correctness, closing coverage gaps, and adding targeted render optimizations. Broader architectural refactors (virtualization, service decomposition) are explicitly deferred unless first-pass metrics fail to meet targets.

## Technical Context

**Language/Version**: Python ≥ 3.12 (backend, tooling targets 3.13) / TypeScript (frontend, React 19)  
**Primary Dependencies**: FastAPI, githubkit, websockets (backend) / React 19.2.0, TanStack Query 5.91.0, @dnd-kit 6.3.1 (frontend)  
**Storage**: In-memory cache (InMemoryCache singleton), aiosqlite for sessions/settings  
**Testing**: pytest + pytest-asyncio (backend, 3365 tests) / Vitest + @testing-library/react (frontend, 1219 tests)  
**Target Platform**: Linux server (backend) / Web browser (frontend)  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: ≥ 50% idle API reduction (SC-001), ≥ 20% board render improvement (SC-002), ≥ 30% event callback reduction (SC-009), no interaction degradation (SC-008)  
**Constraints**: No new dependencies, no virtualization in first pass, no service decomposition in first pass  
**Scale/Scope**: Boards with 50+ cards across 5+ columns; shared GitHub API quota across users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development — ✅ PASS

- Feature has a complete `spec.md` with 6 prioritized user stories (P1–P3).
- Each story has Given-When-Then acceptance scenarios and independent testing criteria.
- Clear scope boundaries: first-pass optimizations only, virtualization/decomposition deferred.
- Passed quality checklist in `checklists/requirements.md`.

### Principle II: Template-Driven Workflow — ✅ PASS

- Plan follows `plan-template.md` structure.
- Research, data model, contracts, and quickstart follow expected artifact patterns.
- No custom sections added without justification.

### Principle III: Agent-Orchestrated Execution — ✅ PASS

- `speckit.specify` completed spec.md → `speckit.plan` generates plan artifacts → `speckit.tasks` will decompose into tasks.
- Clear handoff: plan artifacts are inputs for task generation.
- Single-responsibility maintained.

### Principle IV: Test Optionality with Clarity — ✅ PASS

- Tests ARE required for this feature (explicitly mandated in spec FR-019 through FR-021 and User Story 6).
- Regression tests guard against reintroduction of performance problems.
- New tests must cover changed behaviors: change-detection suppression, refresh path decoupling, event listener throttling.

### Principle V: Simplicity and DRY — ✅ PASS

- No new abstractions introduced; optimizations target existing code paths.
- No new dependencies added.
- Complexity is low: memoization, throttling, and test additions are standard patterns.
- No violations to justify in Complexity Tracking.

### Post-Design Re-Check — ✅ PASS

- Data model describes existing entities, no new models introduced.
- Contracts document existing endpoint behavior after optimization.
- Research confirmed all mechanisms are already implemented; work is verification and gap-filling.
- No principle violations introduced by the design.

## Project Structure

### Documentation (this feature)

```text
specs/001-performance-review/
├── plan.md              # This file
├── research.md          # Phase 0 output — research findings
├── data-model.md        # Phase 1 output — entity descriptions
├── quickstart.md        # Phase 1 output — setup and verification guide
├── contracts/
│   └── refresh-policy.md  # Phase 1 output — refresh and cache contracts
├── checklists/
│   └── requirements.md  # Pre-existing quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── board.py           # Board cache, manual refresh, sub-issue invalidation
│   │   │   ├── projects.py        # WebSocket subscription, change detection
│   │   │   └── workflow.py        # Repository resolution consumer
│   │   ├── services/
│   │   │   ├── cache.py           # InMemoryCache, TTLs, hash computation
│   │   │   ├── copilot_polling/
│   │   │   │   └── polling_loop.py  # Polling hot path, rate-limit gating
│   │   │   └── github_projects/
│   │   │       ├── service.py     # GitHubProjectsService, rate-limit extraction
│   │   │       └── issues.py      # Sub-issue fetching and caching
│   │   └── utils.py               # Shared repository resolution
│   └── tests/
│       └── unit/
│           ├── test_cache.py           # Cache TTL, hash, stale fallback
│           ├── test_api_board.py       # Board endpoint, cache bypass
│           └── test_copilot_polling.py # Polling thresholds, sub-issue filtering
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   ├── useRealTimeSync.ts       # WebSocket + fallback polling
│   │   │   ├── useRealTimeSync.test.tsx # WS lifecycle, message handling
│   │   │   ├── useBoardRefresh.ts       # Auto/manual refresh orchestration
│   │   │   ├── useBoardRefresh.test.tsx # Timer, dedup, visibility
│   │   │   └── useProjectBoard.ts       # Board query ownership
│   │   ├── components/
│   │   │   ├── board/
│   │   │   │   ├── BoardColumn.tsx   # Column rendering (memo'd)
│   │   │   │   └── IssueCard.tsx     # Card rendering (memo'd)
│   │   │   ├── chat/
│   │   │   │   └── ChatPopup.tsx     # Drag resize (RAF-gated)
│   │   │   └── agents/
│   │   │       └── AddAgentPopover.tsx # Positioning (Radix-managed)
│   │   └── pages/
│   │       └── ProjectsPage.tsx      # Derived state, board orchestration
│   └── package.json
```

**Structure Decision**: Web application structure with separate `backend/` and `frontend/` under `solune/`. Both already exist with well-established patterns. No structural changes needed for this feature.

## Implementation Phases

### Phase 1 — Baseline and Guardrails (Blocks All Other Phases)

**Goal**: Capture current performance baselines before changing behavior.

**Tasks**:

1. **Backend baseline measurement** (FR-001)
   - Instrument idle API activity for an open board over a 10-minute observation window.
   - Document: outbound GitHub API request count, board endpoint response time, WebSocket refresh message frequency.
   - Record baseline in a measurement log within the PR description or a dedicated baseline document.

2. **Frontend baseline measurement** (FR-002)
   - Profile board load with 50+ cards across 5+ columns.
   - Document: initial render time, re-render counts for BoardColumn/IssueCard, network activity during idle.
   - Capture event listener callback frequency during a standard drag interaction.

3. **Confirm backend state against spec requirements** (parallel with step 2)
   - Verify WebSocket change detection via content hash is active in `projects.py` `send_tasks()`.
   - Verify board cache TTL (300s) alignment with frontend auto-refresh (5 minutes).
   - Verify sub-issue cache invalidation on manual refresh in `board.py`.
   - Verify sub-issue cache preservation during auto-refresh.
   - Document any gaps as implementation targets for Phase 2.

4. **Define before/after checklist** using existing test suites
   - Run `test_cache.py`, `test_api_board.py`, `test_copilot_polling.py` — record pass/fail state.
   - Run `useRealTimeSync.test.tsx`, `useBoardRefresh.test.tsx` — record pass/fail state.
   - This becomes the regression baseline (SC-006).

**Exit Criteria**: Baseline measurements documented; all existing tests passing; backend state confirmed.

### Phase 2 — Backend API Consumption Fixes

**Goal**: Reduce unnecessary GitHub API calls during idle board viewing and polling.

**Depends on**: Phase 1 baselines.

**Tasks**:

5. **Verify WebSocket refresh suppression** (FR-004, FR-005)
   - Confirm `send_tasks()` in `projects.py` suppresses refresh messages when task hash is unchanged.
   - Add test coverage for hash-based suppression (currently untested path).
   - Validate stale-revalidation counter behavior (10-cycle forced fetch with hash comparison).

6. **Verify sub-issue cache behavior** (FR-007, FR-008)
   - Confirm auto-refresh path reuses warm sub-issue caches (600s TTL).
   - Confirm manual refresh path clears sub-issue caches before re-fetching.
   - Add test verifying sub-issue cache preservation during auto-refresh.

7. **Verify fallback polling behavior** (FR-006)
   - Confirm polling loop does not trigger board data endpoint refreshes.
   - Confirm polling loop uses rate-limit-aware gating (3 thresholds).
   - Verify sub-issue filtering removes child issues before pipeline processing.

8. **Validate idle board API activity** (SC-001)
   - Re-measure idle API activity after verification/fixes.
   - Compare against Phase 1 baseline.
   - Target: ≥ 50% reduction in outbound GitHub API requests over 10-minute idle window.

### Phase 2 — Frontend Refresh-Path Fixes (Parallel with Backend)

**Goal**: Ensure lightweight task updates stay decoupled from expensive board data queries.

**Depends on**: Phase 1 baseline; can run in parallel with backend Phase 2.

**Tasks**:

9. **Verify refresh path decoupling** (FR-011, FR-012, FR-013)
   - Confirm `useRealTimeSync` only invalidates `['projects', pid, 'tasks']`, never `['board', 'data', pid]`.
   - Confirm fallback polling follows the same invalidation policy as WebSocket.
   - Confirm auto-refresh timer only invalidates `['board', 'data', pid]`.
   - Add test verifying board query is NOT invalidated on WebSocket task messages.

10. **Verify manual refresh priority** (FR-014)
    - Confirm `useBoardRefresh.refresh()` cancels in-flight auto-refresh and pending debounced reloads.
    - Confirm manual refresh result is written directly to query cache via `setQueryData`.
    - Add test for manual refresh during concurrent auto-refresh.

11. **Verify WebSocket/polling interaction** (Edge case: unstable WebSocket)
    - Confirm `initial_data` debounce prevents cascade invalidations on reconnect.
    - Confirm transition from connected → polling → connected doesn't multiply refresh requests.
    - Add test for reconnection debounce behavior.

### Phase 3 — Frontend Render Optimization

**Goal**: Reduce rendering costs in board and chat surfaces.

**Depends on**: Phase 2 completion (refresh paths confirmed correct).

**Tasks**:

12. **Verify and extend component memoization** (FR-015, FR-016)
    - Confirm `BoardColumn` and `IssueCard` `memo()` wrappers are effective.
    - Profile: when a single card updates via WebSocket, verify only that card re-renders (SC-003).
    - If other cards/columns re-render unnecessarily, stabilize props with `useMemo`/`useCallback`.

13. **Verify derived data memoization** (FR-018)
    - Confirm `ProjectsPage` `useMemo` blocks cover all expensive computations.
    - Verify `useBoardControls` transformation output is memoized.
    - Profile render cycle to confirm memoization prevents redundant work.

14. **Throttle hot event listeners** (FR-017, SC-009)
    - `ChatPopup` resize: already uses `requestAnimationFrame` gating — verify effectiveness.
    - `AddAgentPopover` positioning: uses Radix UI automatic positioning — verify no custom listeners needed.
    - If drag event listeners in board interactions fire excessively, add `requestAnimationFrame` or `throttle()` gating.
    - Measure callback frequency before and after — target ≥ 30% reduction.

### Phase 3 — Verification and Regression Coverage (Parallel)

**Goal**: Extend test coverage around changed behaviors and validate improvements.

**Depends on**: Phases 2 and 3 implementation.

**Tasks**:

15. **Backend regression tests** (FR-019, FR-021, SC-007)
    - Extend `test_cache.py`: add test for `refresh_ttl()` preserving hash when data unchanged.
    - Extend `test_api_board.py`: add test for sub-issue cache preservation during auto-refresh.
    - Extend `test_copilot_polling.py`: add test for sub-issue filtering correctness.
    - Run full backend test suite — all 3365+ tests must pass.

16. **Frontend regression tests** (FR-020, FR-021, SC-007)
    - Extend `useRealTimeSync.test.tsx`: add test verifying board query NOT invalidated on task messages.
    - Extend `useBoardRefresh.test.tsx`: add test for manual refresh cancelling auto-refresh.
    - Run full frontend test suite — all 1219+ tests must pass.

17. **Final validation** (SC-001 through SC-009)
    - Re-run backend idle API measurement — compare against baseline.
    - Re-run frontend render profile — compare against baseline.
    - Manual end-to-end check: WebSocket updates, fallback polling, manual refresh, board interactions.
    - Document before/after results.

### Phase 4 — Optional Second-Wave Work (Out of Scope)

**Explicitly deferred** unless Phase 3 validation shows targets are missed.

**Potential items** (for follow-on plan only):
- Board virtualization with `@tanstack/virtual` for large boards (>100 cards).
- Service decomposition of `GitHubProjectsService` mixin architecture.
- Bounded cache policies with eviction callbacks for memory management.
- Request budget instrumentation for per-request API cost tracking.
- Render timing instrumentation for per-component performance monitoring.

**Trigger**: Only planned if SC-001 (≥ 50% idle API reduction) or SC-002 (≥ 20% render improvement) fails after all Phase 2–3 work is complete.

## Complexity Tracking

> No constitution violations identified. All changes use standard patterns (memoization, throttling, test extensions) without introducing new abstractions, dependencies, or architectural changes.
