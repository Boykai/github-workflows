# Contract: Label Write Path

**Branch**: `034-label-pipeline-state` | **Phase**: 2

## Purpose

Apply and manage pipeline state labels at every pipeline transition point. Labels are written alongside existing tracking table updates to maintain dual-source state tracking.

## Interface

### Issue Creation (orchestrator.py)

```python
@staticmethod
def _build_labels(
    recommendation: IssueRecommendation,
    pipeline_config_name: str | None = None,
) -> list[str]:
    """Build labels including pipeline:<config> when config name provided."""
    ...
```

### Agent Assignment (orchestrator.py)

```python
async def assign_agent_for_status(
    self,
    ctx: WorkflowContext,
    issue_number: int,
    status: str,
    agents: list[str],
    ...
) -> dict[str, Any] | None:
    """Assign agent with label swap: remove old agent:*, add new agent:<slug>.
    
    Also moves 'active' label between sub-issues and removes 'stalled' if present.
    """
    ...
```

### Pipeline Completion (pipeline.py)

```python
async def _process_pipeline_completion(...) -> dict[str, Any] | None:
    """On pipeline completion, removes agent:* label from parent issue."""
    ...
```

### Stalled Detection (recovery.py)

```python
async def recover_stalled_issues(...) -> list[dict[str, Any]]:
    """Applies 'stalled' label when recovery detects idle agent.
    
    Stalled label is removed by assign_agent_for_status() on re-assignment.
    """
    ...
```

### Label Pre-Creation

```python
async def ensure_pipeline_labels_exist(
    access_token: str,
    owner: str,
    repo: str,
) -> None:
    """Pre-create pipeline labels with correct colors in the repository.
    
    Creates: active (green), stalled (red).
    Pipeline:* and agent:* labels are created dynamically on first use.
    Idempotent — safe to call multiple times (422 = already exists).
    """
    ...
```

## Invariants

- Label write failures are **non-blocking** — logged as warnings, never raise to caller. Pipeline progression continues via tracking table.
- At most **one** `agent:` label exists on a parent issue at any time. Swap removes old before adding new.
- `pipeline:<config>` label is **set-once** at issue creation. Never modified or removed.
- `active` label exists on at most **one** sub-issue at a time. Moved atomically on agent transition.
- `stalled` label is applied by recovery, removed by `assign_agent_for_status()`. If assignment succeeds but stalled-label removal fails, next polling cycle reconciles.
- All label writes use existing `update_issue_state()` — no new GitHub API integration.
- Label operations are **idempotent**: adding an existing label is a no-op; removing a non-existent label is handled gracefully.
