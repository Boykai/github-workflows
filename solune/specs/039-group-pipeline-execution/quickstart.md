# Quickstart: Group-Aware Pipeline Execution & Tracking Table

**Feature Branch**: `039-group-pipeline-execution`
**Date**: 2026-03-13

## Prerequisites

- Python ≥3.12 (backend only — no frontend changes)
- Git

## Setup

```bash
# Clone and checkout feature branch
git checkout 039-group-pipeline-execution

# Backend setup
cd backend
pip install -e ".[dev]"
```

## Running Locally

```bash
# Terminal 1 — Backend
cd backend
python -m uvicorn src.main:app --reload --port 8000

# Terminal 2 — Frontend (no changes needed, but required for testing)
cd frontend
npm run dev
```

## Running Tests

```bash
# Targeted tests for this feature
cd backend
python -m pytest tests/unit/test_agent_tracking.py -v
python -m pytest tests/unit/test_workflow_orchestrator.py -v -k "pipeline_state or group"
python -m pytest tests/unit/test_copilot_polling.py -v -k "advance_pipeline or reconstruct"

# Full backend test suite
cd backend
python -m pytest tests/unit/ -v
```

## Key Files to Understand

### Data Model Changes

| File | What It Does |
|------|-------------|
| `backend/src/models/workflow.py` | **UPDATED** — `ExecutionGroupMapping` model (NEW); `WorkflowConfiguration.group_mappings` field (NEW) |
| `backend/src/services/workflow_orchestrator/models.py` | **UPDATED** — `PipelineGroupInfo` dataclass (NEW); `PipelineState` gains `groups`, `current_group_index`, `current_agent_index_in_group` fields |
| `backend/src/models/pipeline.py` | Existing `ExecutionGroup` and `PipelineStage` — **UNCHANGED** (group structure already exists here) |

### Conversion Layer

| File | What It Does |
|------|-------------|
| `backend/src/services/workflow_orchestrator/config.py` | **UPDATED** — `load_pipeline_as_agent_mappings()` now iterates `stage.groups` and builds `group_mappings`; `PipelineResolutionResult` gains `group_mappings` field |
| `backend/src/api/pipelines.py` | **UPDATED** — `_prepare_workflow_config()` unpacks 4-tuple and sets `config.group_mappings` |

### Tracking Table

| File | What It Does |
|------|-------------|
| `backend/src/services/agent_tracking.py` | **UPDATED** — `AgentStep` gains group fields; `build_agent_pipeline_steps()` accepts `group_mappings`; `render_tracking_markdown()` auto-detects 6-column format; `parse_tracking_from_body()` adds 6-column regex |

### Execution Engine

| File | What It Does |
|------|-------------|
| `backend/src/services/workflow_orchestrator/orchestrator.py` | **UPDATED** — `execute_full_workflow()` initializes `PipelineState.groups`; `assign_agent_for_status()` handles parallel group assignment |
| `backend/src/services/copilot_polling/pipeline.py` | **UPDATED** — `_advance_pipeline()` handles group-aware advancement; `_reconstruct_pipeline_state()` rebuilds groups from tracking table; polling checks handle parallel groups |

## Architecture Overview

```
Pipeline Config (Database)
    │
    │  PipelineStage.groups → ExecutionGroup[]
    │
    ▼
load_pipeline_as_agent_mappings()   ← KEY CHANGE: now preserves groups
    │
    ├── agent_mappings (flat, for backward-compat consumers)
    └── group_mappings (structured, for group-aware execution)
    │
    ▼
WorkflowConfiguration
    │
    ├── agent_mappings[status] → flat agent list
    └── group_mappings[status] → ordered ExecutionGroupMapping[]
    │
    ▼
build_agent_pipeline_steps() → AgentStep[] (with group_label)
    │
    ▼
render_tracking_markdown() → Issue body (6-column table)
    │
    ▼
Polling loop reads issue → parse_tracking_from_body()
    │
    ▼
_reconstruct_pipeline_state() → PipelineState (with groups)
    │
    ▼
_advance_pipeline()
    ├── Sequential group: assign next agent in group
    ├── Parallel group: check all agents done
    └── Group complete: advance to next group or next status
```

## Testing Scenarios

### Sequential Group Execution
1. Create a pipeline with one stage, one group in "sequential" mode, agents A → B → C
2. Launch an issue with this pipeline
3. Verify: Agent A assigned first; on completion, B assigned; then C
4. Verify: Tracking table shows "G1 (series)" in Group column

### Parallel Group Execution
1. Create a pipeline with one stage, one group in "parallel" mode, agents X, Y, Z
2. Launch an issue with this pipeline
3. Verify: All three agents assigned within seconds (2s stagger)
4. Verify: Stage does not advance until all three post "Done!"

### Mixed Groups
1. Create a pipeline with one stage, Group 1 (sequential: A, B), Group 2 (parallel: C, D, E)
2. Launch an issue
3. Verify: A runs, then B; after B completes, C/D/E all start
4. Verify: Tracking table shows G1 (series) for A/B, G2 (parallel) for C/D/E

### Backward Compatibility
1. Use an existing pipeline with no groups defined
2. Launch an issue
3. Verify: Agents run sequentially as before
4. Verify: Tracking table uses 5-column format (no Group column)

## Linting

```bash
# Backend
cd backend
python -m ruff check src/
python -m ruff format --check src/
```
