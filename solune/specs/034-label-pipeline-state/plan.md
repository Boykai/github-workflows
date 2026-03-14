# Implementation Plan: GitHub Label-Based Agent Pipeline State Tracking

**Branch**: `034-label-pipeline-state` | **Date**: 2026-03-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/034-label-pipeline-state/spec.md`

## Summary

Refactor Solune's Agent Pipeline to use GitHub issue labels as durable, instantly-queryable pipeline state markers. Labels on parent issues (`pipeline:<config>`, `agent:<slug>`) and sub-issues (`active`) provide zero-additional-API-call state detection from the already-fetched GraphQL board query — eliminating the most expensive reconstruction and recovery paths.

The current system reconstructs pipeline state by parsing Markdown tracking tables embedded in issue bodies, requiring multiple GitHub API calls per stalled issue (15–25 calls). This feature introduces a fast-path layer: when `pipeline:<config>` and `agent:<slug>` labels are present on an issue, the system builds a valid `PipelineState` directly from labels and the known pipeline configuration — with zero additional API calls beyond the board query that already fetches `labels(first: 20)`.

Labels supplement but do not replace the tracking table. The table remains as the detailed audit trail; labels become the fast-path primary signal. Issues created before this feature (lacking pipeline labels) gracefully fall through to the existing reconstruction chain with no behavioral change.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript (frontend)
**Primary Dependencies**: FastAPI ≥0.135.0, Pydantic ≥2.12.0, githubkit ≥0.14.6, httpx ≥0.28.0 (backend); React, TanStack Query (frontend)
**Storage**: aiosqlite (pipeline configs, agent tracking); GitHub Issues API (labels as state markers)
**Testing**: pytest ≥9.0.0 with pytest-asyncio (backend); Vitest with happy-dom (frontend)
**Target Platform**: Linux server (Docker), modern web browsers
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Pipeline state recovery in 3–5 API calls per issue (down from 15–25); zero additional API calls for fast-path reconstruction from labels
**Constraints**: Label budget ≤10 per parent issue (GitHub limit: 100); label operations must be idempotent and non-blocking; label failures must not block pipeline progression
**Scale/Scope**: Affects 8 backend files (2 new), 2 frontend components; ~15 functions modified/added; 5 implementation phases with clear dependency ordering

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Feature has comprehensive spec.md with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, clear scope boundaries, and 17 functional requirements (FR-001 through FR-017). |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates. Plan, research, data-model, contracts, and quickstart generated from `.specify/templates/`. |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Planning phase executed by `speckit.plan` agent with clear inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). |
| **IV. Test Optionality** | ✅ PASS | Spec explicitly lists unit tests for label utilities, write path, fast-path reconstruction, and validation (Verification items 1–4). Tests are required by spec, not presumed. |
| **V. Simplicity and DRY** | ✅ PASS | Labels reuse existing `update_issue_state()` API (no new GitHub integration). Fast-path is a thin layer before existing reconstruction chain. No premature abstraction — label utilities are pure functions in constants.py. |

**Gate Result**: ALL PASS — proceed to Phase 0 research.

### Post-Design Re-Evaluation (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to FR-001–FR-017 and SC-001–SC-008. Research findings (R-001–R-008) resolve each specification unknown. |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, quickstart.md, and contracts/ all follow canonical templates from `.specify/templates/`. |
| **III. Agent-Orchestrated** | ✅ PASS | `speckit.plan` produces plan.md + Phase 0/1 artifacts. Handoff to `speckit.tasks` for Phase 2 (tasks.md). |
| **IV. Test Optionality** | ✅ PASS | 4 test files specified in Project Structure, corresponding to spec Verification items 1–4. Tests are spec-mandated. |
| **V. Simplicity and DRY** | ✅ PASS | No new GitHub API integration — reuses `update_issue_state()`. Label utilities are 4 pure functions (~20 lines each). One new file (`state_validation.py`). No premature abstraction. |

**Post-Design Gate Result**: ALL PASS — design is constitution-compliant.

## Project Structure

### Documentation (this feature)

```text
specs/034-label-pipeline-state/
├── plan.md              # This file
├── research.md          # Phase 0 output — unknowns resolution
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — developer guide
├── contracts/           # Phase 1 output — API contracts
│   ├── label-utilities.md
│   ├── label-write-path.md
│   ├── label-fast-path.md
│   └── label-validation.md
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── constants.py                              # Label constants + parsing/builder utilities
│   ├── models/
│   │   ├── task.py                               # Add labels field to Task model
│   │   └── board.py                              # Label model (existing, no changes)
│   ├── services/
│   │   ├── workflow_orchestrator/
│   │   │   ├── orchestrator.py                   # Label writes at issue creation + agent assignment
│   │   │   └── models.py                         # PipelineState (existing, no changes)
│   │   ├── copilot_polling/
│   │   │   ├── pipeline.py                       # Fast-path layer + completion label cleanup
│   │   │   ├── recovery.py                       # Stalled label + simplified reconciliation
│   │   │   ├── polling_loop.py                   # Pass labels through polling steps
│   │   │   ├── helpers.py                        # is_sub_issue() (existing, no changes)
│   │   │   └── state_validation.py               # NEW: consolidated label vs tracking table validation
│   │   ├── github_projects/
│   │   │   ├── issues.py                         # update_issue_state() (existing, no changes)
│   │   │   ├── board.py                          # Label parsing (existing, no changes)
│   │   │   ├── graphql.py                        # GET_PROJECT_ITEMS_QUERY extended with labels(first: 20)
│   │   │   └── projects.py                       # Pass labels from GraphQL response to Task
│   │   └── copilot_polling/pipeline.py           # _self_heal_tracking_table() simplified with pipeline: label
│   └── api/
│       └── projects.py                           # Expose labels in task API responses
└── tests/
    └── unit/
        ├── test_label_constants.py               # NEW: label parsing/builder utilities
        ├── test_label_write_path.py              # NEW: label application at transitions
        ├── test_label_fast_path.py               # NEW: fast-path reconstruction from labels
        └── test_label_validation.py              # NEW: label vs tracking table cross-check

frontend/
├── src/
│   ├── components/
│   │   └── board/
│   │       ├── BoardToolbar.tsx                  # Pipeline config filter
│   │       └── IssueCard.tsx                     # Agent badge, pipeline tag, stalled indicator
│   └── services/
│       └── api.ts                                # Updated response types with labels
└── tests/
    └── (frontend label rendering tests)
```

**Structure Decision**: Web application structure (backend + frontend) — matches existing repository layout. All backend changes extend existing files in `backend/src/`. One new file: `state_validation.py` for consolidated label/tracking-table cross-checking. Four new test files for label-specific functionality.

## Complexity Tracking

> No constitutional violations detected. All changes use existing patterns and infrastructure.
