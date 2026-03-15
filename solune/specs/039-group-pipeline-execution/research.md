# Research: Group-Aware Pipeline Execution & Tracking Table

**Feature Branch**: `039-group-pipeline-execution`
**Date**: 2026-03-13
**Input**: [spec.md](./spec.md), [plan.md](./plan.md)

## 1. Group Information Bottleneck — Where Groups Are Lost

### Decision
Introduce a `group_mappings` field on `WorkflowConfiguration` and thread it through every layer that currently uses the flat `agent_mappings` dict. The conversion point in `load_pipeline_as_agent_mappings()` will iterate `stage.groups` instead of the deprecated `stage.agents` field.

### Rationale
The root cause of the feature gap is a single function: `load_pipeline_as_agent_mappings()` in `backend/src/services/workflow_orchestrator/config.py` (line ~350). It iterates `stage.agents` — the flattened backward-compat view created by `_normalize_groups()` — and discards all group structure. By adding a parallel `group_mappings: dict[str, list[ExecutionGroupMapping]]` field alongside the existing `agent_mappings`, we can:

- Preserve the existing flat pipeline for all backward-compat consumers
- Thread group information through to the orchestrator and tracking table only where needed
- Avoid modifying any code that only reads `agent_mappings` (majority of consumers)

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Replace `agent_mappings` with a grouped structure | Breaking change; every consumer of `agent_mappings` would need updates; high risk |
| Embed group info inside `AgentAssignment.config` | Mixes concerns; group membership is structural, not agent-level config |
| Derive groups at execution time from `PipelineConfig` | Requires re-loading pipeline config during orchestration; slow and fragile |

---

## 2. ExecutionGroupMapping Model Design

### Decision
Create a new Pydantic model `ExecutionGroupMapping` in `backend/src/models/workflow.py` with fields: `group_id: str`, `order: int`, `execution_mode: str`, and `agents: list[AgentAssignment]`. Add `group_mappings: dict[str, list[ExecutionGroupMapping]]` to `WorkflowConfiguration` with `default_factory=dict` for backward compatibility.

### Rationale
This mirrors the existing `ExecutionGroup` model from `pipeline.py` but uses `AgentAssignment` (the workflow layer type) instead of `PipelineAgentNode` (the pipeline config layer type). This separation keeps the pipeline config layer decoupled from the workflow execution layer, following the existing pattern where `load_pipeline_as_agent_mappings()` converts `PipelineAgentNode` to `AgentAssignment`.

### Key Design Details
- `group_id` is opaque at this layer — used for display labeling ("G1", "G2") and reconstruction
- `order` determines execution sequence within a stage (same semantics as `ExecutionGroup.order`)
- `execution_mode` is `"sequential"` or `"parallel"` — group-level, not stage-level
- The `agents` list preserves per-agent config (model_id, model_name) through the `AgentAssignment.config` dict

---

## 3. PipelineGroupInfo Runtime Model

### Decision
Add a `PipelineGroupInfo` dataclass to `backend/src/services/workflow_orchestrator/models.py` with fields: `group_id: str`, `execution_mode: str`, `agents: list[str]`, and `agent_statuses: dict[str, str]` (for parallel tracking). Add group-related fields to `PipelineState`: `groups: list[PipelineGroupInfo]`, `current_group_index: int`, `current_agent_index_in_group: int`.

### Rationale
`PipelineState` currently tracks a flat agent list with a single `current_agent_index`. For group-aware execution, we need a two-level index: which group we're in (`current_group_index`) and which agent within that group (`current_agent_index_in_group`). The `PipelineGroupInfo` dataclass provides runtime tracking per group, including parallel agent completion status.

### Backward Compatibility Strategy
All new fields have defaults: `groups=[]`, `current_group_index=0`, `current_agent_index_in_group=0`. The `current_agent` and `is_complete` properties check `if self.groups:` first; if groups exist, they use the group-aware logic; otherwise they fall back to the existing flat `agents` list behavior. This ensures zero breakage for existing pipelines.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Flatten groups into `agents` list with metadata markers | Loses group boundaries; completion tracking becomes ambiguous for parallel groups |
| Store group info only in the tracking table, not in PipelineState | Requires parsing the issue body to determine execution strategy; fragile and slow |
| Separate `ParallelGroupState` and `SequentialGroupState` classes | Over-engineered; a single `PipelineGroupInfo` with an `agent_statuses` dict handles both modes |

---

## 4. Tracking Table Format — 6-Column Extension

### Decision
Add a "Group" column between "Status" and "Agent" in the tracking table markdown: `| # | Status | Group | Agent | Model | State |`. The Group column displays labels like `G1 (series)` or `G2 (parallel)`. Include 6-column regex parsing with 5-column and 4-column fallbacks.

### Rationale
The tracking table is the primary persistence mechanism for pipeline state across polling cycles (the system reconstructs `PipelineState` from the table when state is lost). Adding group information to the table ensures:

- Group membership survives process restarts
- Users can visually verify group configuration on the issue
- The existing `_reconstruct_pipeline_state()` function can rebuild group-aware state

### Format Details

**New 6-column format** (when groups are present):
```markdown
| # | Status | Group | Agent | Model | State |
|---|--------|-------|-------|-------|-------|
| 1 | Ready | G1 (series) | `speckit.plan` | claude-sonnet | ⏳ Pending |
| 2 | Ready | G1 (series) | `speckit.tasks` | claude-sonnet | ⏳ Pending |
| 3 | In Progress | G1 (parallel) | `linter` | gpt-4o | ⏳ Pending |
| 4 | In Progress | G1 (parallel) | `tester` | gpt-4o | ⏳ Pending |
| 5 | In Progress | G2 (series) | `reviewer` | claude-sonnet | ⏳ Pending |
```

**Legacy 5-column format** (backward compat — no groups):
```markdown
| # | Status | Agent | Model | State |
```

**Legacy 4-column format** (oldest backward compat):
```markdown
| # | Status | Agent | State |
```

### Group Labeling Convention
- Groups are numbered G1, G2, ... per status (reset for each status)
- Label format: `G{n} ({mode})` where mode is "series" or "parallel"
- "series" is used instead of "sequential" for brevity in the table

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Encode group info in the Agent column (e.g., `[G1] speckit.plan`) | Harder to parse; breaks existing regex patterns; visually cluttered |
| Use a separate section for group metadata | Splits related information; harder to correlate groups with agents |
| Conditionally show Group column only when multiple groups exist | Inconsistency makes parsing harder; simpler to always include when groups are configured |

---

## 5. Parallel Agent Assignment — Stagger Strategy

### Decision
When assigning agents in a parallel group, assign each agent sequentially with a 2-second `asyncio.sleep()` between assignments. Use the existing `assign_agent_for_status()` function in a loop, adjusting the agent index for each group member.

### Rationale
GitHub's API has rate limits (primary: 5000 requests/hour, secondary: point-based). Assigning multiple Copilot agents simultaneously generates several API calls per agent (create/update sub-issue, assign Copilot, update labels, update tracking table). A 2-second stagger between agents:

- Stays well within rate limits for typical group sizes (2–5 agents)
- Provides a simple, predictable delay model
- Is easy to tune later (the delay is a constant, not a complex algorithm)

### Implementation Pattern

```python
async def _assign_parallel_group(ctx, status, group):
    """Assign all agents in a parallel group with stagger delay."""
    for i, agent_slug in enumerate(group.agents):
        if i > 0:
            await asyncio.sleep(PARALLEL_STAGGER_DELAY_SECONDS)  # 2s
        await assign_agent_for_status(ctx, status, agent_index=global_index_of(agent_slug))
```

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| `asyncio.gather()` for truly simultaneous assignment | Risk of rate limit errors; order of operations unpredictable |
| Exponential backoff on rate limit error | Adds complexity; 2s stagger is sufficient prevention for typical group sizes |
| Queue-based assignment with separate worker | Over-engineered for initial implementation; can be added later if needed |

---

## 6. Parallel Group Completion Detection

### Decision
For parallel groups, track each agent's completion status in `PipelineGroupInfo.agent_statuses: dict[str, str]`. A group is complete when all agents have status `"completed"` or `"failed"`. During polling, check all agents in the current parallel group rather than stopping at the first incomplete.

### Rationale
The current `_reconstruct_pipeline_state()` stops at the first incomplete agent (sequential assumption). For parallel groups, all agents run independently, so we must check each one. The `agent_statuses` dict provides O(1) lookup per agent and makes the "all done?" check a simple `all()` call.

### Failure Handling
Per spec (US-6, FR-012, FR-013):
- When one agent fails, remaining agents continue
- The group is marked as partially failed
- Failed agents are recorded in `PipelineState.failed_agents`
- The pipeline advances to the next group/status after all agents finish (completed or failed)

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Cancel remaining agents on first failure | Wastes completed work; contradicts spec requirement FR-012 |
| Retry failed agents before advancing | Adds retry loop complexity; retry is better handled by a separate recovery mechanism |
| Block pipeline on any failure | Too conservative; partial results are still valuable |

---

## 7. Pipeline State Reconstruction from Tracking Table

### Decision
Update `_reconstruct_pipeline_state()` to check for the Group column in the tracking table. When present, reconstruct `PipelineGroupInfo` objects from the parsed `AgentStep.group_label` fields. When absent, fall back to existing flat reconstruction.

### Rationale
The tracking table is the source of truth for pipeline state when in-memory state is lost (e.g., after a process restart). The Group column provides sufficient information to:

1. Determine which groups exist in the current status
2. Determine each group's execution mode (parsed from "G1 (series)" label)
3. Group agents into their respective groups
4. Check completion status for parallel groups

### Reconstruction Algorithm

```python
def _reconstruct_groups_from_steps(steps: list[AgentStep], status: str) -> list[PipelineGroupInfo]:
    """Reconstruct group info from parsed tracking table steps."""
    status_steps = [s for s in steps if s.status == status]
    if not status_steps or not any(s.group_label for s in status_steps):
        return []  # No group info — use flat fallback

    groups_by_label: dict[str, PipelineGroupInfo] = {}
    for step in status_steps:
        label = step.group_label or "G1 (series)"
        if label not in groups_by_label:
            mode = "parallel" if "parallel" in label else "sequential"
            groups_by_label[label] = PipelineGroupInfo(
                group_id=label, execution_mode=mode, agents=[], agent_statuses={}
            )
        group = groups_by_label[label]
        group.agents.append(step.agent_name)
        if mode == "parallel":
            group.agent_statuses[step.agent_name] = _state_to_status(step.state)

    return list(groups_by_label.values())
```

---

## 8. Backward Compatibility — "Groups Exist" Guard Pattern

### Decision
All group-aware code paths use an explicit guard: `if group_mappings and group_mappings.get(status):` before entering group logic. When the guard fails, the existing flat logic executes unchanged.

### Rationale
The system must support three scenarios simultaneously:
1. **New pipelines with groups**: Full group-aware execution and tracking
2. **New pipelines without groups** (user never created groups): Legacy flat behavior
3. **In-flight legacy pipelines**: Started before this feature; no group data in tracking table

The guard pattern ensures each code path handles all three scenarios without duplication or error. Every function that adds group behavior follows the same pattern:

```python
def some_function(..., group_mappings=None):
    if group_mappings and group_mappings.get(status):
        # Group-aware path
        ...
    else:
        # Existing flat path (unchanged)
        ...
```

This pattern is applied consistently across:
- `build_agent_pipeline_steps()` — group_mappings parameter added
- `render_tracking_markdown()` — detects group presence from steps
- `parse_tracking_from_body()` — 6-column regex added before 5-column
- `assign_agent_for_status()` — checks config.group_mappings
- `_advance_pipeline()` — checks pipeline.groups
- `_reconstruct_pipeline_state()` — checks for Group column
