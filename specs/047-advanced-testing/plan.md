# Implementation Plan: Advanced Testing for Deep Unknown Bugs

**Branch**: `047-advanced-testing` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/047-advanced-testing/spec.md`

## Summary

Add advanced testing infrastructure to surface deep, unknown bugs across 7 disciplines: concurrency race-condition detection, fault injection for background loops and external services, stateful property-based pipeline verification, runtime type validation (Zod schemas for frontend API responses, Pydantic models for backend webhooks), fuzz testing on parsing boundaries, thin-mock integration tests with real internal wiring, and flaky test detection in CI.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript ~5.9 (frontend)
**Primary Dependencies**: FastAPI, Pydantic 2, aiosqlite, httpx, hypothesis (backend); React 19, Vite 7, Vitest 4, Zod 4 (frontend)
**Storage**: SQLite via aiosqlite with SQL migration files (023–027), `BoundedDict`/`BoundedSet` L1 in-memory caches
**Testing**: pytest + pytest-asyncio + hypothesis + pytest-cov (backend); Vitest + @fast-check/vitest (frontend); Playwright (E2E)
**Target Platform**: Linux containers (Docker Compose: backend:8000, frontend:5173→8080, signal-api)
**Project Type**: Web (monorepo: `solune/backend/` + `solune/frontend/`)
**Performance Goals**: All new tests complete within 60s added CI time
**Constraints**: No production runtime overhead from validation (dev/test mode only for frontend Zod); flaky detection runs as scheduled CI job only
**Scale/Scope**: ~7,400 LOC across 11 target files; ~2,100 existing backend tests, ~850 frontend tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Specification-First | ✅ PASS | `spec.md` complete with 7 prioritized user stories, acceptance scenarios, edge cases |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Plan produced by `/speckit.plan`, tasks by `/speckit.tasks` |
| IV. Test Optionality | ✅ PASS | Tests are the explicit feature deliverable here — not incidental overhead |
| V. Simplicity & DRY | ✅ PASS | Each testing discipline targets a specific architectural risk; no speculative frameworks. Complexity justified by the feature being testing infrastructure itself |

**Gate result: PASS — proceed to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/047-advanced-testing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── webhook-payloads.md
│   └── api-response-schemas.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (from /speckit.tasks)
```

### Source Code (repository root)

```text
solune/backend/
├── src/
│   ├── api/webhooks.py            # Add Pydantic webhook payload models
│   ├── services/
│   │   ├── copilot_polling/state.py   # Concurrency test target
│   │   ├── pipeline_state_store.py    # Stateful cache test target
│   │   ├── signal_bridge.py           # Fault injection test target
│   │   ├── workflow_orchestrator/     # Transaction safety test target
│   │   ├── github_projects/service.py # _with_fallback fault injection target
│   │   └── agent_tracking.py          # Markdown fuzz test target
│   └── main.py                        # Background loop test targets
└── tests/
    ├── concurrency/                   # NEW: race condition & interleaving tests
    ├── chaos/                         # NEW: fault injection tests
    ├── property/
    │   ├── test_pipeline_state_machine.py  # NEW: stateful pipeline model
    │   └── test_bounded_cache_stateful.py  # NEW: stateful cache model
    ├── integration/
    │   ├── conftest.py                # NEW: thin-mock fixture
    │   ├── test_migrations.py         # NEW: migration regression
    │   └── test_thin_mock_flows.py    # NEW: real-wiring integration
    └── fuzz/                          # NEW: webhook, markdown, JSON fuzz

solune/frontend/
├── src/
│   ├── services/
│   │   ├── schemas/                   # NEW: Zod response validation schemas
│   │   │   ├── validate.ts
│   │   │   ├── projects.ts
│   │   │   ├── board.ts
│   │   │   ├── chat.ts
│   │   │   ├── pipeline.ts
│   │   │   └── settings.ts
│   │   └── api.ts                     # Hook Zod validation in dev mode
│   └── hooks/
│       ├── usePipelineReducer.ts      # Harden JSON.parse
│       └── useRealTimeSync.ts         # Harden JSON.parse
└── src/__tests__/
    └── fuzz/                          # NEW: frontend fuzz tests
        └── jsonParse.test.ts

.github/workflows/
├── ci.yml                             # Add --durations=20 to pytest
└── flaky-detection.yml                # NEW: scheduled flaky detection job
```

**Structure Decision**: Web monorepo. New test directories (`concurrency/`, `chaos/`, `fuzz/`) are added as siblings to existing `unit/`, `integration/`, `property/` under `solune/backend/tests/`. Frontend schemas go into `solune/frontend/src/services/schemas/`. CI gets a new workflow file for flaky detection.

## Complexity Tracking

> No constitution violations. Complexity is inherent to the feature scope (testing infrastructure). Each phase is independently deliverable per Constitution Principle I (user story independence).

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No complexity violations | — |
