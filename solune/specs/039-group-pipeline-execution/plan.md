# Implementation Plan: Group-Aware Pipeline Execution & Tracking Table

**Branch**: `039-group-pipeline-execution` | **Date**: 2026-03-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/039-group-pipeline-execution/spec.md`

## Summary

The frontend Pipeline page already supports `ExecutionGroup` with series/parallel toggles, and the backend data model stores per-group execution modes. However, all group information is lost during the conversion from `PipelineConfig` → `WorkflowConfiguration` → `PipelineState` because `load_pipeline_as_agent_mappings()` iterates the deprecated flat `stage.agents` field instead of `stage.groups`. This plan adds a `group_mappings` field to `WorkflowConfiguration`, threads group information through the orchestration and tracking layers, implements group-aware execution (sequential groups run agents one-by-one; parallel groups run all agents simultaneously with 2s stagger; groups execute in configured order within a stage), and extends the GitHub Issue tracking table with a "Group" column — all with backward-compatible fallback for legacy pipelines. No frontend changes are needed. See [research.md](./research.md) for technology decisions.

## Technical Context

**Language/Version**: Python ≥3.12 (backend only — no frontend changes required)
**Primary Dependencies**: FastAPI ≥0.135, Pydantic v2, aiosqlite, asyncio
**Storage**: SQLite via aiosqlite with JSON-serialized pipeline stages (existing pattern); `WorkflowConfiguration` persisted per-project; `PipelineState` is in-memory only (reconstructed from issue tracking table)
**Testing**: pytest (~1736 backend tests); relevant test files: `test_agent_tracking.py` (522 lines), `test_workflow_orchestrator.py` (3610 lines), `test_copilot_polling.py` (9744 lines)
**Target Platform**: Linux server (backend service)
**Project Type**: Web application (backend changes only for this feature)
**Performance Goals**: Parallel group agents assigned within 2s × N stagger window; no regression to sequential pipeline latency
**Constraints**: Full backward compatibility with existing pipelines; no data migration required; tracking table must parse 3 formats (6-col, 5-col, 4-col)
**Scale/Scope**: Up to 10 stages × 5 groups × 10 agents per pipeline; typical 2–5 agents per parallel group

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md contains 6 prioritized user stories (P1–P3) with Given-When-Then acceptance scenarios, edge cases, and 14 functional requirements |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan produced by `speckit.plan` agent; tasks will be produced by `speckit.tasks` agent |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are included — updating existing test files (`test_agent_tracking.py`, `test_workflow_orchestrator.py`, `test_copilot_polling.py`) to cover new group-aware behavior and backward compatibility |
| V. Simplicity and DRY | ✅ PASS | Extends existing models (`WorkflowConfiguration`, `PipelineState`, `AgentStep`) with optional fields rather than creating parallel structures; uses "if groups exist, use group logic; else flat fallback" guard pattern throughout |

**Post-Phase 1 Re-check**: ✅ PASS — Two new models added (`ExecutionGroupMapping`, `PipelineGroupInfo`), both are minimal dataclasses/Pydantic models with no unnecessary abstraction. The `ExecutionGroupMapping` mirrors the existing `ExecutionGroup` from `pipeline.py` but at the workflow layer — this separation maintains the existing architectural boundary between pipeline config and workflow execution. No complexity violations.

## Project Structure

### Documentation (this feature)

```text
specs/039-group-pipeline-execution/
├── plan.md                          # This file
├── research.md                      # Phase 0 output — technology decisions
├── data-model.md                    # Phase 1 output — entity definitions & relationships
├── quickstart.md                    # Phase 1 output — developer onboarding guide
├── contracts/                       # Phase 1 output — internal interface changes
│   └── internal-interfaces.md       # Changed internal service interfaces
└── tasks.md                         # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── workflow.py              # Add ExecutionGroupMapping; add group_mappings to WorkflowConfiguration
│   ├── services/
│   │   ├── agent_tracking.py        # Add group fields to AgentStep; update build/render/parse for 6-col table
│   │   ├── workflow_orchestrator/
│   │   │   ├── models.py            # Add PipelineGroupInfo; update PipelineState with group fields
│   │   │   ├── config.py            # Update load_pipeline_as_agent_mappings() to build group_mappings
│   │   │   └── orchestrator.py      # Update execute_full_workflow() and assign_agent_for_status()
│   │   └── copilot_polling/
│   │       ├── pipeline.py          # Update _advance_pipeline(), _reconstruct_pipeline_state(), polling checks
│   │       └── helpers.py           # Update tracking helpers (pass-through group info)
│   └── api/
│       └── pipelines.py             # Update _prepare_workflow_config() to accept 4-tuple
└── tests/
    └── unit/
        ├── test_agent_tracking.py   # Add 6-col format tests + backward compat parsing
        ├── test_workflow_orchestrator.py  # Add PipelineState group property tests
        └── test_copilot_polling.py  # Update _advance_pipeline and reconstruct tests
```

**Structure Decision**: Web application (backend only). All changes are confined to `backend/` directory. No frontend changes — the UI already supports ExecutionGroups. Eight existing backend files are modified; two new models are added to existing files. Test updates extend three existing test files.

## Complexity Tracking

> No Constitution Check violations. Table included for completeness.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | — | — |
