# Implementation Plan: Dead Code & Technical Debt Cleanup

**Branch**: `039-dead-code-cleanup` | **Date**: 2026-03-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/039-dead-code-cleanup/spec.md`

## Summary

Systematic codebase cleanup across backend (Python/FastAPI) and frontend (TypeScript/React) to remove dead code, consolidate duplicate patterns, annotate legacy code paths with deprecation timelines, decompose high-complexity functions, and plan future architectural migrations. The work spans 5 phases with 25 steps, using CGC (CodeGraph Context) checkpoints every 5 steps for graph-aware validation. Research confirms the codebase is relatively clean — no high-severity dead code — but has 8 legacy markers in the pipeline module, 5+ TODO items, duplicate utility functions, 20+ inline error handlers that should use the existing `handle_service_error` helper, and 5 functions with cyclomatic complexity >50 requiring decomposition. Singleton removal and in-memory store migration are planned but deferred to separate specifications.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.9 / React 19.2 (frontend)
**Primary Dependencies**: FastAPI, aiosqlite, githubkit, httpx, websockets (backend); TanStack React Query v5.90, @dnd-kit v6.3, Vite 7.3, Vitest 4.0 (frontend)
**Storage**: SQLite via aiosqlite (session/settings); InMemoryCache for board/sub-issue/project data; in-memory dicts for chat messages/proposals/recommendations (MVP, migration 012 tables ready)
**Testing**: pytest + pytest-asyncio (backend); Vitest + Testing Library (frontend); Playwright (E2E)
**Target Platform**: Web application — Docker (Nginx 1.27-alpine frontend, Python backend), SPA with WebSocket + polling fallback
**Project Type**: Web application (frontend + backend)
**Performance Goals**: N/A — this feature targets maintainability, not performance. All 5 complexity targets must be CC < 30 (except `assign_agent_for_status` CC < 25 and `recover_stalled_issues` CC < 20).
**Constraints**: Zero test regressions across backend and frontend; zero type-check errors; no new external dependencies; no behavioral changes to production workflows
**Scale/Scope**: CGC baseline: 465 files, 4653 functions, 803 classes. Cleanup touches ~30 backend files and ~15 frontend files across 5 phases.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅
Feature spec (`spec.md`) includes 5 prioritized user stories (P1–P3) with independent testing criteria and Given-When-Then acceptance scenarios. Scope boundaries are explicit — singleton and in-memory store migrations are deferred to separate specs (Story 5).

### II. Template-Driven Workflow ✅
All artifacts follow canonical templates: `plan.md` (this file), `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`. No custom sections added.

### III. Agent-Orchestrated Execution ✅
Plan phase produces well-defined outputs that feed into the tasks phase. Each phase (cleanup → annotation → DRY → complexity → planning) has clear inputs and outputs with CGC checkpoints for validation.

### IV. Test Optionality with Clarity ✅
Tests are NOT added as new test infrastructure. Existing test suites (pytest, Vitest, Playwright) are run after each phase to verify zero regressions. New tests are only needed if refactored functions change public API contracts (none do — all decompositions keep internal sub-functions private).

### V. Simplicity and DRY ✅
This feature is explicitly about enforcing DRY principles and reducing complexity. All proposed changes simplify the codebase:
- Removing dead code reduces surface area
- Consolidating error handlers reduces duplication (20 inline → 0)
- Decomposing high-CC functions improves readability
- Deprecation annotations prevent future debt accumulation
- No new abstractions beyond `cached_fetch` (a thin wrapper over existing `InMemoryCache`)

**Gate Result**: PASS — all constitution principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/039-dead-code-cleanup/
├── plan.md              # This file
├── research.md          # Phase 0 output — resolved unknowns and best practices
├── data-model.md        # Phase 1 output — entity definitions for cleanup tracking
├── quickstart.md        # Phase 1 output — developer onboarding guide
├── contracts/           # Phase 1 output — behavioral contracts
│   ├── error-handling.md    # Consolidated error handling contract
│   ├── deprecation-policy.md  # Deprecation annotation and lifecycle contract
│   └── complexity-budget.md   # Function complexity targets and decomposition rules
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── chat.py              # Error handling consolidation, temp file lifecycle, in-memory stores
│   │   ├── projects.py          # Error handling, cache pattern extraction
│   │   ├── board.py             # Cache pattern extraction
│   │   ├── webhooks.py          # Error handling consolidation
│   │   ├── signal.py            # Error handling consolidation
│   │   ├── auth.py              # Error handling, backward-compat alias audit
│   │   ├── chores.py            # Error handling consolidation
│   │   └── workflow.py          # require_selected_project adoption
│   ├── services/
│   │   ├── cache.py             # New cached_fetch utility
│   │   ├── agent_tracking.py    # Legacy regex deprecation annotation
│   │   ├── copilot_polling/
│   │   │   ├── agent_output.py  # CC=123 decomposition
│   │   │   ├── pipeline.py      # Legacy path deprecation annotations
│   │   │   └── recovery.py      # CC=72 decomposition
│   │   ├── workflow_orchestrator/
│   │   │   ├── orchestrator.py  # CC=91 decomposition
│   │   │   └── config.py        # agent_pipeline_mappings deprecation audit
│   │   ├── pipelines/
│   │   │   └── service.py       # Legacy format logging
│   │   └── github_projects/
│   │       ├── service.py       # Singleton migration plan (planning only)
│   │       └── agents.py        # Singleton migration plan (planning only)
│   ├── models/
│   │   ├── recommendation.py    # Fix "temporary" docstring
│   │   ├── pipeline.py          # Deprecation timeline for legacy fields
│   │   └── chat.py              # Backward-compat alias audit
│   ├── prompts/
│   │   └── issue_generation.py  # Backward-compat alias audit
│   ├── dependencies.py          # require_selected_project (already exists), singleton plan
│   └── logging_utils.py         # handle_service_error (already exists, reference)
├── tests/                       # Run existing suites for regression verification
└── docs/
    └── configuration.md         # Migration count update

frontend/
├── src/
│   ├── components/
│   │   ├── settings/
│   │   │   ├── DynamicDropdown.tsx   # Remove duplicate formatTimeAgo
│   │   │   ├── GlobalSettings.tsx    # CC=96 decomposition (already partially done)
│   │   │   └── ProjectSettings.tsx   # agent_pipeline_mappings audit
│   │   └── pipeline/
│   │       └── ExecutionGroupCard.tsx # Pipeline migration tracking reference
│   ├── pages/
│   │   └── LoginPage.tsx            # CC=90 decomposition
│   ├── hooks/
│   │   ├── useChatHistory.ts        # clearLegacyStorage audit
│   │   └── useScrollLock.ts         # @internal annotation
│   ├── lib/
│   │   └── pipelineMigration.ts     # Migration tracking adoption rate
│   ├── types/
│   │   └── index.ts                 # Deprecated fields (old_status, agents, execution_mode)
│   └── utils/
│       └── formatTime.ts            # Canonical formatTimeAgo (import target)
└── tests/                           # Run existing suites for regression verification
```

**Structure Decision**: Existing web application structure (backend + frontend) is used as-is. No new directories or modules are introduced. All changes are within existing files, with the exception of `cached_fetch` being added to the existing `backend/src/services/cache.py`.

## Complexity Tracking

> No constitution violations detected. This section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
