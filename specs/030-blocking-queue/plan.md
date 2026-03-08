# Implementation Plan: Blocking Queue — Serial Issue Activation & Branch Ancestry Control

**Branch**: `030-blocking-queue` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/030-blocking-queue/spec.md`

## Summary

Add a per-repository blocking queue that serializes issue activation and controls branch ancestry when blocking issues exist. Blocking is toggled via a `blocking` flag on Chores and Pipelines (pipeline-level flag applies to ALL its issues), or inline via the `#block` magic word in chat messages. A new `blocking_queue` SQLite table tracks issues through states (pending → active → in_review → completed). The core blocking queue service implements batch activation rules: non-blocking issues activate concurrently when no blocking issues exist (preserving current behavior); when any blocking issue is open, serial activation is enforced — blocking issues activate alone, non-blocking issues activate together up to the next blocking entry. All activated issues branch from the oldest open blocking issue's branch (not chained), reverting to `main` when no blocking issues remain. Per-repo locking and SQLite transactions prevent double-activation race conditions. WebSocket notifications broadcast queue state changes, and the polling loop calls `try_activate_next()` on startup for missed-activation recovery. The frontend adds toggle switches to ChoreCard and PipelineBoard, `#block` autocomplete in chat, and visual indicators (🔒 badge, "Pending (blocked)" labels, toast notifications) on the board.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript ~5.9 (frontend)
**Primary Dependencies**: FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12, websockets 16.0 (backend); React 19.2, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend)
**Storage**: SQLite with WAL mode (aiosqlite) — new `blocking_queue` table; ALTER TABLE additions to `pipeline_configs` and `chores`
**Testing**: pytest + pytest-asyncio (backend), Vitest 4 + Testing Library (frontend)
**Target Platform**: Desktop browsers, 1024px minimum viewport; Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Activation cascade completes within 5 seconds of trigger (SC-007); toggle persistence within 2 seconds (SC-004); restart recovery within 30 seconds (SC-008)
**Constraints**: No new external dependencies; must not break existing concurrent non-blocking issue activation; per-repo service-layer lock must not degrade throughput for unrelated repos; under 1000 queue entries per repo
**Scale/Scope**: 4 new backend files, ~10 modified backend files, ~8 modified frontend files; 1 new migration, 1 new service module, 1 new model file, 1 new store file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 7 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 20 functional requirements (FR-001–FR-020), 9 success criteria, 7 edge cases, clear scope boundaries |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Spec explicitly requests unit tests for blocking queue state machine and `#block` parsing; integration tests for chore trigger and pipeline creation; no blanket testing mandate |
| **V. Simplicity/DRY** | ✅ PASS | Extends existing patterns (SQLite migration, Pydantic models, service CRUD, toggle UI); new service follows established chores/pipelines service architecture; no new external dependencies |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-020); data model maps to DB schema in spec |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Tests specified for blocking queue state machine (8-issue scenario), `#block` parsing, chore trigger integration, pipeline creation integration |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing `get_db()` pattern, `connection_manager.broadcast_to_project()` for WebSocket, `_CHORE_UPDATABLE_COLUMNS` pattern for column allowlists, `ai_enhance_enabled` toggle pattern in ChoreCard. No unnecessary abstractions. Blocking queue service is a focused single-responsibility module. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/030-blocking-queue/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R8)
├── data-model.md        # Phase 1: Entity definitions, types, state machines
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── api.md           # Phase 1: REST API endpoint contracts
│   └── components.md    # Phase 1: Component interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── chat.py                          # MODIFIED: #block parsing (Priority 0.5)
│   │   ├── chores.py                        # MODIFIED: pass blocking flag on trigger
│   │   └── pipelines.py                     # MODIFIED: blocking field in CRUD
│   ├── models/
│   │   ├── blocking.py                      # NEW: BlockingQueueEntry, BlockingQueueStatus
│   │   ├── chores.py                        # MODIFIED: add blocking field to Chore, ChoreCreate, ChoreUpdate
│   │   └── pipeline.py                      # MODIFIED: add blocking field to PipelineConfig
│   ├── services/
│   │   ├── blocking_queue.py                # NEW: Core blocking queue state machine
│   │   ├── blocking_queue_store.py          # NEW: SQLite persistence layer
│   │   ├── chores/
│   │   │   └── service.py                   # MODIFIED: read blocking from chore/pipeline, pass to orchestrator
│   │   ├── copilot_polling/
│   │   │   ├── pipeline.py                  # MODIFIED: mark_in_review + activation cascade
│   │   │   └── completion.py                # MODIFIED: mark_completed + activation cascade
│   │   ├── pipelines/
│   │   │   └── service.py                   # MODIFIED: blocking in CRUD, column allowlist
│   │   ├── websocket.py                     # MODIFIED: broadcast blocking_queue_updated event
│   │   └── workflow_orchestrator/
│   │       └── orchestrator.py              # MODIFIED: base_ref resolution + activation gating
│   └── migrations/
│       └── 017_blocking_queue.sql           # NEW: blocking_queue table, ALTER chores + pipeline_configs
└── tests/
    └── unit/
        └── test_blocking_queue.py           # NEW: State machine unit tests (8-issue scenario)

frontend/
├── src/
│   ├── components/
│   │   ├── board/                           # MODIFIED: blocking indicators on issue cards
│   │   ├── chores/
│   │   │   └── ChoreCard.tsx                # MODIFIED: blocking toggle switch
│   │   ├── chat/
│   │   │   └── ChatInterface.tsx            # MODIFIED: #block autocomplete + indicator
│   │   └── pipeline/
│   │       └── SavedWorkflowsList.tsx       # MODIFIED: pipeline blocking toggle
│   ├── hooks/
│   │   ├── useChores.ts                     # MODIFIED: blocking field in types/mutations
│   │   └── usePipelineConfig.ts             # MODIFIED: blocking field in types/mutations
│   └── types/
│       └── index.ts                         # MODIFIED: BlockingQueueEntry type, blocking fields
```

**Structure Decision**: Web application (frontend/ + backend/). The repo already has `frontend/` and `backend/` directories. New backend files (`blocking.py`, `blocking_queue.py`, `blocking_queue_store.py`) follow the existing flat service pattern for focused single-purpose modules (like `cache.py`, `encryption.py`). The migration follows the sequential numbering pattern (`017_blocking_queue.sql`). Frontend changes modify existing components, following the established toggle pattern from `ai_enhance_enabled` on ChoreCard.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Per-repo service-layer lock (asyncio.Lock per repo_key) | Prevents double-activation race conditions without global locking; only contends within the same repo | Global lock (rejected: blocks unrelated repos), DB-only locking (rejected: SQLite doesn't support row-level locks in WAL mode for write contention) |
| Flat branch ancestry (all branch from oldest blocking) | Simpler than chaining branches; avoids merge cascades when intermediate issues complete | Chained branching where each issue branches from the previous (rejected: complex merge dependency chain, harder recovery when middle issues fail) |
| Single `blocking_queue` table (not embedded in existing tables) | Clean separation of concerns; queue state is independent of chore/pipeline lifecycle; enables efficient per-repo queries | Embedding queue status in existing issue tracking (rejected: no dedicated issue table exists; chores table has different lifecycle) |
