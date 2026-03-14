# API Contract: Group-Aware Pipeline Execution — Internal Layer Changes

**Feature Branch**: `039-group-pipeline-execution`
**Date**: 2026-03-13
**Input**: [data-model.md](../data-model.md), [spec.md](../spec.md)

## Overview

This feature introduces **no new REST API endpoints** and **no external API changes**. All modifications are internal to the backend service layer. The pipeline CRUD API (`/api/v1/pipelines/{projectId}`) already accepts group-based `PipelineStage` payloads (delivered by feature 037-pipeline-builder-ux). This contract documents the **internal interface changes** between backend services that enable group-aware execution.

## Changed Internal Interfaces

### 1. `load_pipeline_as_agent_mappings()` — Return Type Change

**File**: `backend/src/services/workflow_orchestrator/config.py`

**Before**:
```python
async def load_pipeline_as_agent_mappings(
    project_id: str,
    pipeline_id: str,
) -> tuple[dict[str, list[AgentAssignment]], str, dict[str, str]] | None:
    """Returns: (agent_mappings, pipeline_name, stage_execution_modes)"""
```

**After**:
```python
async def load_pipeline_as_agent_mappings(
    project_id: str,
    pipeline_id: str,
) -> tuple[
    dict[str, list[AgentAssignment]],
    str,
    dict[str, str],
    dict[str, list[ExecutionGroupMapping]],
] | None:
    """Returns: (agent_mappings, pipeline_name, stage_execution_modes, group_mappings)"""
```

**Change**: Returns a 4-tuple instead of a 3-tuple. The fourth element is `group_mappings: dict[str, list[ExecutionGroupMapping]]` — status name to ordered list of execution groups. Empty `{}` when the pipeline has no groups.

**Callers to update**:
- `_prepare_workflow_config()` in `backend/src/api/pipelines.py`
- `resolve_project_pipeline_mappings()` in `backend/src/services/workflow_orchestrator/config.py`

---

### 2. `PipelineResolutionResult` — New Field

**File**: `backend/src/services/workflow_orchestrator/config.py`

**Before**:
```python
@dataclass
class PipelineResolutionResult:
    agent_mappings: dict[str, list[AgentAssignment]] = field(default_factory=dict)
    source: str = "default"
    pipeline_name: str | None = None
    pipeline_id: str | None = None
    stage_execution_modes: dict[str, str] = field(default_factory=dict)
```

**After**:
```python
@dataclass
class PipelineResolutionResult:
    agent_mappings: dict[str, list[AgentAssignment]] = field(default_factory=dict)
    source: str = "default"
    pipeline_name: str | None = None
    pipeline_id: str | None = None
    stage_execution_modes: dict[str, str] = field(default_factory=dict)
    group_mappings: dict[str, list[ExecutionGroupMapping]] = field(default_factory=dict)
```

**Change**: New `group_mappings` field with default `{}`.

---

### 3. `WorkflowConfiguration` — New Field

**File**: `backend/src/models/workflow.py`

**Added field**:
```python
group_mappings: dict[str, list[ExecutionGroupMapping]] = Field(
    default_factory=dict,
    description="Status name → ordered list of execution groups. Empty for legacy pipelines."
)
```

**Backward compatibility**: Default `{}` — all existing serialized configs deserialize without error.

---

### 4. `build_agent_pipeline_steps()` — New Parameter

**File**: `backend/src/services/agent_tracking.py`

**Before**:
```python
def build_agent_pipeline_steps(
    agent_mappings: dict[str, list[AgentAssignment]],
    status_order: list[str],
) -> list[AgentStep]:
```

**After**:
```python
def build_agent_pipeline_steps(
    agent_mappings: dict[str, list[AgentAssignment]],
    status_order: list[str],
    group_mappings: dict[str, list[ExecutionGroupMapping]] | None = None,
) -> list[AgentStep]:
```

**Change**: Optional `group_mappings` parameter. When provided and non-empty for a given status, the function iterates groups instead of the flat agent list for that status, setting `group_label`, `group_order`, and `group_execution_mode` on each `AgentStep`.

**Callers to update**:
- `append_tracking_to_body()` — must accept and forward `group_mappings`

---

### 5. `append_tracking_to_body()` — New Parameter

**File**: `backend/src/services/agent_tracking.py`

**Before**:
```python
def append_tracking_to_body(
    body: str,
    agent_mappings: dict[str, list[AgentAssignment]],
    status_order: list[str],
) -> str:
```

**After**:
```python
def append_tracking_to_body(
    body: str,
    agent_mappings: dict[str, list[AgentAssignment]],
    status_order: list[str],
    group_mappings: dict[str, list[ExecutionGroupMapping]] | None = None,
) -> str:
```

**Change**: Optional `group_mappings` parameter forwarded to `build_agent_pipeline_steps()`.

---

### 6. `render_tracking_markdown()` — Auto-Detect Format

**File**: `backend/src/services/agent_tracking.py`

**No signature change**. The function inspects `steps` to check if any `AgentStep` has a non-empty `group_label`. If so, renders the 6-column table; otherwise renders the existing 5-column table.

**6-column format**:
```markdown
| # | Status | Group | Agent | Model | State |
|---|--------|-------|-------|-------|-------|
| 1 | Ready | G1 (series) | `speckit.plan` | claude-sonnet | ⏳ Pending |
```

---

### 7. `parse_tracking_from_body()` — Multi-Format Parser

**File**: `backend/src/services/agent_tracking.py`

**No signature change**. Returns `list[AgentStep] | None`.

**Parsing priority**:
1. Try 6-column regex: `| idx | status | group | agent | model | state |`
2. Fall back to 5-column regex: `| idx | status | agent | model | state |` (current)
3. Fall back to 4-column regex: `| idx | status | agent | state |` (legacy)

When 6-column format is detected, `AgentStep.group_label` is populated.

---

### 8. Tracking Table Markdown Schema

**6-column format** (new — when groups are configured):

```
| # | Status | Group | Agent | Model | State |
|---|--------|-------|-------|-------|-------|
| {index} | {status_name} | {group_label} | `{agent_slug}` | {model_display} | {state_emoji} |
```

**Group label format**: `G{n} ({mode})` where:
- `n` = 1-based group number within the status (resets per status)
- `mode` = `"series"` or `"parallel"` (abbreviated for display)

**5-column format** (existing — no groups):
```
| # | Status | Agent | Model | State |
|---|--------|-------|-------|-------|
```

**4-column format** (legacy — no model):
```
| # | Status | Agent | State |
|---|--------|-------|-------|
```

---

## Unchanged Interfaces

The following interfaces are **NOT modified**:

| Interface | File | Reason |
|-----------|------|--------|
| Pipeline CRUD REST API | `backend/src/api/pipelines.py` routes | Already accepts group-based PipelineStage |
| `PipelineConfig` model | `backend/src/models/pipeline.py` | Already has `groups` field on `PipelineStage` |
| Frontend types/components | `frontend/src/types/index.ts` | Already supports ExecutionGroup |
| `AgentAssignment` model | `backend/src/models/agent.py` | Unchanged — used within groups |
| `update_agent_state()` | `backend/src/services/agent_tracking.py` | Preserves group_label through parse → modify → re-render cycle |
| `determine_next_action()` | `backend/src/services/agent_tracking.py` | Operates on AgentStep; group info passes through transparently |
