# Contract: Label Validation

**Branch**: `034-label-pipeline-state` | **Phase**: 4

## Purpose

Provide a consolidated validation function that cross-checks pipeline labels against the Markdown tracking table and corrects whichever source is stale. This replaces scattered consistency checks with a single, testable validation entry point.

## Interface

### State Validation Service (state_validation.py — new file)

```python
"""Consolidated label vs tracking table validation."""

async def validate_pipeline_labels(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    labels: list[dict[str, str]],
    tracking_steps: list,  # list[AgentStep]
    pipeline_config_name: str | None = None,
) -> tuple[bool, list[str]]:
    """Cross-check labels vs tracking table, fix stale source.

    Comparison logic:
    1. Extract agent:<slug> from labels → label_agent
    2. Find active agent from tracking_steps → table_agent
    3. If label_agent == table_agent → consistent, no action
    4. If label_agent != table_agent:
       a. Check GitHub ground truth (sub-issue state, assignment)
       b. Determine which source is stale
       c. Fix stale source (update label or update tracking table)

    Returns:
        (corrections_made, correction_descriptions)
        - corrections_made: True if any fixes were applied
        - correction_descriptions: List of human-readable fix descriptions
    """
    ...
```

### Simplified Recovery Functions

```python
# In agent_tracking.py — _self_heal_tracking_table()
# When pipeline:<config> label is present:
#   → Get agent list from config directly (skip get_sub_issues() API call)
#   → Saves 1–2 API calls per self-heal

# In recovery.py — _validate_and_reconcile_tracking_table()
# When agent:<slug> label is present:
#   → Use agent slug as cursor into agent list
#   → Only validate agents from that index onward
#   → Saves N-1 "Done!" checks for completed agents

# In pipeline.py — _reconstruct_pipeline_state()
# When labels provide current agent index:
#   → Only verify CURRENT agent's status (1 API call vs N)
#   → Saves N-1 API calls for completed agents
```

## Invariants

- Validation **never blocks** pipeline progression — corrections are best-effort.
- Validation runs **at most once per polling cycle** per issue — not on every fast-path hit.
- When labels and tracking table disagree, **GitHub ground truth** (sub-issue state, Copilot assignment, PR existence) is the tiebreaker.
- Label corrections use `update_issue_state()` — same API as write path.
- Tracking table corrections use `update_issue_body()` — same API as self-heal.
- Validation is **idempotent** — running twice in succession produces no additional changes.
- The function logs all corrections at `WARNING` level for audit trail visibility.
- If ground truth is ambiguous (e.g., both sources could be correct), the **tracking table wins** (it has more detailed state information).
