# Data Model: Phase 3 — Testing

**Feature**: `001-phase-3-testing` | **Date**: 2026-03-22 | **Plan**: [plan.md](./plan.md)

## Overview

Phase 3 is a test infrastructure feature — it does not introduce new data models, entities, or schema changes. All work extends existing test suites, adjusts configuration thresholds, and adds new test files. This document captures the key data structures and state models that tests interact with.

## Existing Entities Under Test

### PipelineState

**Location**: `solune/backend/src/services/workflow_orchestrator/models.py`

| Field | Type | Description | Test Relevance |
|-------|------|-------------|----------------|
| `issue_number` | `int` | GitHub issue number | Used as pipeline identifier in all tests |
| `project_id` | `str` | GitHub project ID (e.g., `PVT_xxx`) | Used for queue scoping (active pipelines per project) |
| `status` | `str` | Pipeline status | Transitions: idle → running → completed; Backlog → Ready → In Progress → In Review |
| `agents` | `list[str]` | Agent names for execution | Sequential execution order |
| `current_agent_index` | `int` | Index of currently executing agent | Tracks sequential progress |
| `completed_agents` | `list[str]` | Agents that finished execution | Agent completion tracking |
| `started_at` | `datetime \| None` | Pipeline start timestamp | FIFO ordering key for queue tests |
| `queued` | `bool` | Whether pipeline is in queue | Queue gate logic — True = waiting, False = active |
| `execution_mode` | `str` | `"sequential"` or `"parallel"` | State machine preconditions |
| `error` | `str \| None` | Error message if failed | Error path coverage |
| `agent_assigned_sha` | `str` | SHA of agent assignment | Agent trigger deduplication |
| `original_status` | `str \| None` | Status before transition | Status transition tracking |
| `target_status` | `str \| None` | Target status for transition | Status transition tracking |

### PipelineGroupInfo

**Location**: `solune/backend/src/services/workflow_orchestrator/models.py`

Used by the state machine for grouping pipeline metadata.

### Agent Trigger Inflight State

**Location**: `solune/backend/src/services/pipeline_state_store.py` (L1 cache)

| Cache | Type | Description | Test Relevance |
|-------|------|-------------|----------------|
| `_pipeline_states` | `dict[int, PipelineState]` | Pipeline state by issue number | Queue function queries scan this cache |
| `_agent_trigger_inflight` | `dict[str, float]` | Inflight triggers by key → timestamp | `should_skip_agent_trigger()` grace period and stale reclaim |

### Coverage Thresholds (Configuration)

**Frontend** (`vitest.config.ts`):

| Phase | Statements | Branches | Functions | Lines |
|-------|-----------|----------|-----------|-------|
| Current | 50 | 44 | 41 | 50 |
| Phase 1 Target | 65 | 55 | 55 | 65 |
| Phase 2 Target | 75 | 65 | 65 | 75 |

**Backend** (`pyproject.toml`):

| File | Current Floor | Target Floor |
|------|--------------|--------------|
| Overall | 75% | 75% (unchanged) |
| board.py | N/A (per-file) | ≥80% |
| pipelines.py | N/A (per-file) | ≥80% |
| pipeline.py | N/A (per-file) | ≥85% |
| agent_creator.py | N/A (per-file) | ≥70% |

### Mutation Thresholds (Configuration)

| Tool | Config File | Field | Current | Target |
|------|------------|-------|---------|--------|
| Stryker | `stryker.config.mjs` | `thresholds.break` | `null` | `50` |
| mutmut | `mutation-testing.yml` | aggregation step | N/A | kill ratio ≥ 60% |

## State Transitions

### Pipeline Lifecycle (Full-Workflow Integration Test)

```text
[Issue Created] → Backlog → Ready → In Progress → In Review → [Completed]
                                                                    │
                                                              [PR Merged]
                                                                    │
                                                              [Cleanup] → [Dequeue Next]
```

### Queue State Machine (Property Tests)

```text
                    ┌─────────────────────────────────┐
                    │                                 │
                    ▼                                 │
[New Pipeline] ─→ active (running)                   │
                    │         │                       │
                    │    [active exists]               │
                    │         │                       │
                    │         ▼                       │
                    │    queued (FIFO)                 │
                    │         │                       │
                    │    [active completes]            │
                    │         │                       │
                    │         ▼                       │
                    │    dequeue → active ─────────────┘
                    │
                    │    [cancel]
                    │         │
                    │         ▼
                    │    cancelled
                    │
              [completes]
                    │
                    ▼
              completed
```

**Queue Invariants** (enforced by property tests):
1. FIFO order: queued pipelines sorted by `started_at` ascending
2. No agent on queued: `queued=True` → no agent assigned
3. Single active: at most 1 non-queued pipeline per `project_id`
4. Grace period: `should_skip_agent_trigger()` returns `True` within grace window
5. Stale reclaim: `should_skip_agent_trigger()` returns `False` after 120 seconds

## Validation Rules

No new validation rules are introduced. All existing validation (Pydantic model validators, coverage threshold checks, mutation score thresholds) is preserved. The feature adjusts numeric thresholds in configuration files.
