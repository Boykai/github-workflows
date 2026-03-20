# Implementation Plan: Pipeline Queue Mode Toggle

**Branch**: `053-pipeline-queue-mode` | **Date**: 2026-03-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/053-pipeline-queue-mode/spec.md`

## Summary

Add a per-project **"Queue Mode"** toggle to the Project Board toolbar that enforces sequential pipeline execution — only one parent issue's agent pipeline runs at a time. When ON, newly launched pipelines create the issue and sub-issues on the board but **hold in Backlog without assigning any agent**. When the active pipeline's parent issue reaches "In Review" or "Done/Closed" (whichever comes first), the next queued issue's pipeline automatically starts.

**Decisions**:
- Launch with queue active: issue is created on board, held in Backlog with no agent assigned
- Slot release trigger: "In Review" OR "Done/Closed" — whichever comes first
- Scope: per-project toggle, persisted in the existing `project_settings` table

## Technical Context

**Language/Version**: Python ≥3.12 (backend, pyright targets 3.13), TypeScript ~5.9.0 (frontend)
**Primary Dependencies**: FastAPI ≥0.135 (backend), React 19.2 (frontend), Pydantic ≥2.12 (backend), Vite 8 (frontend), TanStack Query v5.91 (frontend), Tailwind CSS 4.2 (frontend)
**Storage**: SQLite via aiosqlite ≥0.22 (existing `project_settings` table — add column)
**Testing**: pytest ≥9.0 + pytest-asyncio ≥1.3 (backend), Vitest ≥4.0.18 + @testing-library/react 16.3 (frontend)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (backend + frontend monorepo under `solune/`)
**Performance Goals**: Toggle responds in <2 seconds; dequeue triggers within 30 seconds of pipeline completion
**Constraints**: Queue mode defaults to OFF; toggling OFF does not affect existing queued pipelines; no timeout-based queue release in initial release
**Scale/Scope**: Per-project setting; FIFO ordering by launch timestamp; O(n) scan of L1 cache for active pipeline count

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development ✅ PASS

- ✅ Feature began with spec.md containing 5 prioritized user stories (P1–P2)
- ✅ Given-When-Then acceptance scenarios for all 5 stories
- ✅ Clear scope boundaries (timeout-based release explicitly out of scope)
- ✅ Independent testing criteria for each story

### Principle II: Template-Driven Workflow ✅ PASS

- ✅ All artifacts follow canonical templates from `.specify/templates/`
- ✅ Plan follows plan-template.md structure
- ✅ No unjustified custom sections

### Principle III: Agent-Orchestrated Execution ✅ PASS

- ✅ Clear phase ordering: specify → plan → tasks → implement
- ✅ Single-responsibility phases with explicit handoffs
- ✅ Tasks will be organized by user story for parallel implementation

### Principle IV: Test Optionality with Clarity ✅ PASS

- ✅ Tests are explicitly requested in the parent issue (Phase 4 has 3 test tasks)
- ✅ Unit tests, integration tests, and frontend tests are specified
- ✅ Test tasks are grouped in a dedicated phase after implementation

### Principle V: Simplicity and DRY ✅ PASS

- ✅ Extends existing `project_settings` table — no new tables
- ✅ Extends existing `PipelineState` dataclass — no new data structures
- ✅ Uses existing `BoundedDict` cache pattern
- ✅ Uses existing `ToolbarButton` pattern for frontend toggle
- ✅ No premature abstraction — direct implementation in existing files

## Project Structure

### Documentation (this feature)

```text
specs/053-pipeline-queue-mode/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification (/speckit.specify output)
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Task list (/speckit.tasks command output)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── pipelines.py          # Queue gate in execute_pipeline_launch()
│   │   │   └── settings.py           # PUT handler for queue_mode
│   │   ├── migrations/
│   │   │   └── 031_queue_mode.sql    # New migration — queue_mode column
│   │   ├── models/
│   │   │   └── settings.py           # ProjectBoardConfig + ProjectSettingsUpdate
│   │   └── services/
│   │       ├── copilot_polling/
│   │       │   └── pipeline.py       # Dequeue trigger after pipeline completion
│   │       ├── pipeline_state_store.py  # count_active_pipelines_for_project()
│   │       ├── settings_store.py     # is_queue_mode_enabled() + column allowlist
│   │       └── workflow_orchestrator/
│   │           └── models.py         # PipelineState.queued field
│   └── tests/
│       ├── unit/
│       │   └── test_queue_mode.py    # New unit tests
│       └── integration/
│           └── test_queue_mode.py    # New integration test
└── frontend/
    └── src/
        ├── components/
        │   └── board/
        │       └── IssueCard.tsx      # "Queued" badge
        ├── pages/
        │   └── ProjectsPage.tsx       # Queue Mode toggle in toolbar
        └── types/
            └── index.ts              # Type updates for queue_mode
```

## Architecture

### Phase 1: Backend Data Model

The queue mode setting is stored as an `INTEGER NOT NULL DEFAULT 0` column in the existing `project_settings` table. This leverages the existing settings infrastructure — column allowlist, upsert SQL, PUT handler — requiring only additive changes.

### Phase 2: Backend Queue Logic

The queue gate is inserted in `execute_pipeline_launch()` between `set_pipeline_state` (L350) and `assign_agent_for_status` (L363). When queue mode is ON and another pipeline is active:
1. Pipeline state is created with `queued=True`
2. Agent assignment and polling start are skipped
3. Response message indicates "Pipeline queued"

Dequeue is triggered in two places:
1. `_transition_after_pipeline_complete()` after `remove_pipeline_state()` (L1928) — handles "Done/Closed" path
2. `check_in_review_issues()` — handles "In Review" path

Both paths find the oldest queued pipeline by `started_at` (FIFO) and call `assign_agent_for_status()` on it.

### Phase 3: Frontend Toggle

The toggle follows the existing `ToolbarButton` pattern in `ProjectsPage.tsx` (around L201). It uses the `ListOrdered` icon from lucide-react and the `useProjectSettings` hook for state management. The "Queued" badge on `IssueCard.tsx` uses a clock/queue icon.

### Phase 4: Tests

Unit tests verify the gate logic, FIFO ordering, and backward compatibility. Integration tests verify the full lifecycle (launch → queue → complete → dequeue). Frontend tests verify toggle rendering, settings persistence, and badge visibility.

## Relevant Files

| Layer | File | Change |
|-------|------|--------|
| Migration | `solune/backend/src/migrations/031_queue_mode.sql` | **new** — `queue_mode INTEGER NOT NULL DEFAULT 0` |
| Model | `solune/backend/src/models/settings.py` | add `queue_mode` to `ProjectBoardConfig` + `ProjectSettingsUpdate` |
| Store | `solune/backend/src/services/settings_store.py` | column allowlist, upsert SQL, `is_queue_mode_enabled()` helper |
| API | `solune/backend/src/api/settings.py` | persist `queue_mode` in PUT handler |
| State | `solune/backend/src/services/pipeline_state_store.py` | `count_active_pipelines_for_project()` |
| Launch | `solune/backend/src/api/pipelines.py` | queue gate before `assign_agent_for_status()` at L363 |
| Polling | `solune/backend/src/services/copilot_polling/pipeline.py` | dequeue trigger after `remove_pipeline_state()` + on In Review/Done |
| Orchestrator | `solune/backend/src/services/workflow_orchestrator/models.py` | `queued: bool = False` on `PipelineState` |
| Types | `solune/frontend/src/types/index.ts` | `queue_mode` in 4 interfaces |
| Page | `solune/frontend/src/pages/ProjectsPage.tsx` | Queue Mode toggle in toolbar |
| Card | `solune/frontend/src/components/board/IssueCard.tsx` | "Queued" badge |
| Tests | `solune/backend/tests/unit/test_queue_mode.py` | **new** unit tests |
| Tests | `solune/backend/tests/integration/test_queue_mode.py` | **new** integration test |

## Verification

1. `cd solune/backend && pytest tests/unit/test_queue_mode.py -v`
2. `cd solune/backend && pytest --cov=src --cov-report=term-missing` — coverage does not regress
3. `cd solune/frontend && npm test` — frontend tests pass
4. Manual: toggle ON → launch 2 issues → second held in Backlog (no agent) → complete first → second auto-starts
5. Manual: toggle OFF → both launch immediately (existing behavior preserved)
