# Contract: Label Fast-Path Reconstruction

**Branch**: `034-label-pipeline-state` | **Phase**: 3

## Purpose

Provide zero-additional-API-call pipeline state reconstruction from labels. When both `pipeline:<config>` and `agent:<slug>` labels are present on a parent issue, build a valid `PipelineState` directly from labels and the pipeline configuration — bypassing the expensive issue-body-fetch → tracking-table-parse → sub-issue-fetch reconstruction chain.

## Interface

### Fast-Path Layer (pipeline.py)

```python
async def _get_or_reconstruct_pipeline(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    project_id: str,
    status: str,
    agents: list[str],
    expected_status: str | None = None,
    labels: list[dict[str, str]] | None = None,  # NEW parameter
) -> PipelineState:
    """Get or reconstruct pipeline state.

    Reconstruction chain (in order of preference):
    1. In-memory cache hit → return cached state
    2. NEW: Label fast-path → build from pipeline:<config> + agent:<slug>
    3. Issue body → parse tracking table
    4. Sub-issues → self-heal tracking table
    5. Full reconstruction → _reconstruct_pipeline_state()
    """
    ...
```

### Fast-Path Builder (pipeline.py, internal)

```python
def _build_pipeline_from_labels(
    issue_number: int,
    project_id: str,
    status: str,
    pipeline_config_name: str,
    agent_slug: str,
    pipeline_config: PipelineConfig,
) -> PipelineState | None:
    """Build PipelineState from label data and pipeline configuration.

    Returns None if the agent slug is not found in the config's agent list,
    triggering fallthrough to the next reconstruction method.
    """
    ...
```

### Task Model Extension (task.py)

```python
class Task(BaseModel):
    # ... existing fields ...
    labels: list[dict[str, str]] | None = None
```

### Polling Loop Integration (polling_loop.py)

```python
# Labels propagated from get_project_items() (GET_PROJECT_ITEMS_QUERY extended with labels) through to polling steps.
# NOTE: GET_PROJECT_ITEMS_QUERY must include labels(first: 20) { nodes { id name color } } in the Issue content type.
parent_tasks = [t for t in all_tasks if not is_sub_issue(t)]
# Each task.labels is now populated from the GraphQL response
```

## Invariants

- Fast-path produces **identical** `PipelineState` to full reconstruction for the same inputs. Specifically: `current_agent_index`, `agents` list, and `completed_agents` must match.
- Fast-path **never blocks** on failure — any error or missing data triggers graceful fallthrough to the existing reconstruction chain.
- Fast-path requires **zero GitHub API calls** — uses only label data (already fetched) + pipeline config (local database lookup).
- When multiple `agent:` labels exist (transient inconsistency from non-atomic swap), the **first** match is used.
- `labels` parameter is optional in `_get_or_reconstruct_pipeline()` — callers that don't have labels simply skip the fast-path.
- Label-based `is_sub_issue()` detection via `"parent"` label is additive — existing title-pattern matching remains as fallback.
