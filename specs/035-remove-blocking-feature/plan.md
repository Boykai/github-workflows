# Implementation Plan: Remove Blocking Feature Entirely from Application

**Branch**: `035-remove-blocking-feature` | **Date**: 2026-03-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/035-remove-blocking-feature/spec.md`

## Summary

Remove the entire Blocking feature from the Solune application — including the blocking queue system, `#block` chat detection, blocking labels, blocking-related database schema, and all integration points across backend services, API endpoints, and frontend test mocks. The blocking feature is partially implemented: database migrations (017, 018) and integration call sites exist throughout the codebase, but core implementation files (`blocking_queue` service, `BlockingQueueEntry`/`BlockingQueueStatus` models, `with_blocking_label()` constant, and `is_blocking` model fields) were never created. Removal requires surgically excising all references to the planned feature — imports, try/except guarded calls, migration files, test fixtures, and configuration columns — so the application builds and runs cleanly with zero blocking residue.

Technical approach: Ordered removal starting from leaf references (tests, frontend mocks), then integration call sites (API chat, workflow orchestrator, copilot polling, chores service, signal chat), then database migrations, finishing with a comprehensive grep audit to confirm zero residual references.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript (frontend)
**Primary Dependencies**: FastAPI ≥0.135.0, Pydantic ≥2.12.0, githubkit ≥0.14.6, httpx ≥0.28.0 (backend); React 19, TanStack Query, Vitest (frontend)
**Storage**: aiosqlite (blocking_queue table, blocking columns on pipeline_configs/chores/project_settings)
**Testing**: pytest ≥9.0.0 with pytest-asyncio (backend); Vitest with happy-dom (frontend)
**Target Platform**: Linux server (Docker), modern web browsers
**Project Type**: Web application (backend + frontend)
**Performance Goals**: N/A — removal only, no new performance targets
**Constraints**: Zero build errors, zero test failures, zero runtime import errors after removal; no data loss for non-blocking data; existing features must remain fully functional
**Scale/Scope**: ~20 files modified (13 backend, 4 backend tests, 3 frontend tests); 2 migration files to create (rollback); 0 new features added

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Feature has comprehensive spec.md with 4 prioritized user stories (P1–P2), Given-When-Then acceptance scenarios, 15 functional requirements (FR-001 through FR-015), clear scope boundaries, edge cases, and 6 success criteria (SC-001 through SC-006). |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/`. Plan, research, data-model, contracts, and quickstart generated per template structure. |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Planning phase executed by `speckit.plan` agent with clear inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to `speckit.tasks` for Phase 2. |
| **IV. Test Optionality** | ✅ PASS | This is a removal feature — no new tests required. Existing tests that reference blocking will be updated or removed. Spec requires all existing tests pass after removal (FR-014). |
| **V. Simplicity and DRY** | ✅ PASS | Pure removal — no new abstractions, no new code. Simplifies the codebase by removing a partially-implemented feature. This is the simplest possible approach. |

**Gate Result**: ALL PASS — proceed to Phase 0 research.

### Post-Design Re-Evaluation (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All removal targets trace back to FR-001–FR-015 and SC-001–SC-006. Research findings (R-001–R-005) resolve each audit finding. |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, quickstart.md, and contracts/ all follow canonical templates. |
| **III. Agent-Orchestrated** | ✅ PASS | `speckit.plan` produces plan.md + Phase 0/1 artifacts. Handoff to `speckit.tasks` for Phase 2 (tasks.md). |
| **IV. Test Optionality** | ✅ PASS | No new tests. Existing blocking tests removed; existing non-blocking tests verified passing. |
| **V. Simplicity and DRY** | ✅ PASS | Pure deletion. No new code, no new abstractions, no premature complexity. |

**Post-Design Gate Result**: ALL PASS — design is constitution-compliant.

## Project Structure

### Documentation (this feature)

```text
specs/035-remove-blocking-feature/
├── plan.md              # This file
├── research.md          # Phase 0 output — codebase audit and unknowns resolution
├── data-model.md        # Phase 1 output — entities being removed
├── quickstart.md        # Phase 1 output — developer guide for the removal
├── contracts/           # Phase 1 output — API surface changes
│   ├── blocking-queue-removal.md
│   └── model-field-removal.md
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── migrations/
│   │   ├── 017_blocking_queue.sql                  # REMOVE: blocking_queue table + blocking columns
│   │   ├── 018_pipeline_blocking_override.sql      # REMOVE: pipeline_blocking_override column
│   │   └── 019_remove_blocking.sql                 # NEW: rollback migration dropping blocking artifacts
│   ├── constants.py                                # CLEAN: remove with_blocking_label() if present
│   ├── models/
│   │   └── recommendation.py                       # CLEAN: remove is_blocking field references (not yet added)
│   ├── services/
│   │   ├── chores/
│   │   │   └── service.py                          # CLEAN: remove blocking flag resolution + enqueue logic
│   │   ├── copilot_polling/
│   │   │   ├── pipeline.py                         # CLEAN: remove mark_completed/mark_in_review calls + _activate_queued_issue
│   │   │   ├── recovery.py                         # CLEAN: remove BlockingQueueStatus import + queue guard
│   │   │   └── polling_loop.py                     # CLEAN: remove _step_sweep_blocking_queue + Step 4c registration
│   │   ├── signal_chat.py                          # CLEAN: remove with_blocking_label imports + calls
│   │   └── workflow_orchestrator/
│   │       └── orchestrator.py                     # CLEAN: remove blocking_queue import + enqueue + base_ref override
│   └── api/
│       ├── chat.py                                 # CLEAN: remove blocking_queue enqueue + proposal_is_blocking
│       └── workflow.py                             # CLEAN: remove is_blocking= parameter
└── tests/unit/
    ├── test_chat_block.py                          # REMOVE: entire file (tests #block detection)
    ├── test_api_board.py                           # CLEAN: remove TestSkipBlockingIssue + TestDeleteBlockingIssue classes
    ├── test_copilot_polling.py                     # CLEAN: remove blocking queue mock references
    └── test_api_pipelines.py                       # CLEAN: remove blocking mock references

frontend/
├── src/
│   └── components/
│       ├── board/
│       │   └── ProjectIssueLaunchPanel.test.tsx    # CLEAN: remove blocking: false from mock data
│       └── pipeline/
│           └── SavedWorkflowsList.test.tsx         # CLEAN: remove blocking: false from mock data
└── src/pages/
    └── ProjectsPage.test.tsx                       # CLEAN: remove blocking_override mock references
```

**Structure Decision**: Web application structure (backend + frontend) — matches existing repository layout. This is a pure removal feature: no new source files are created (only a rollback migration). All changes are deletions or edits to existing files to excise blocking references.

## Complexity Tracking

> No constitutional violations detected. All changes are pure deletions of a partially-implemented feature using existing patterns and infrastructure.
