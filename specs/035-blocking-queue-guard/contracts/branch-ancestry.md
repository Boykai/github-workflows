# Contract: Branch Ancestry via Entry-Specific Blocking Source

**Branch**: `035-blocking-queue-guard` | **Phase**: 2

## Purpose

Resolve correct branch ancestry for blocked issues by using the issue's own `blocking_source_issue` from its queue entry, rather than the global oldest blocker. This eliminates race conditions where multiple blocking chains exist and the global lookup returns the wrong predecessor's branch.

## Interface

### get_base_ref_for_entry() (blocking_queue.py)

```python
async def get_base_ref_for_entry(repo_key: str, issue_number: int) -> str:
    """Return the base branch using the issue's own ``blocking_source_issue``.

    Resolution chain:
    1. Look up issue's queue entry via store.get_by_issue()
    2. If entry exists and has blocking_source_issue:
       a. Look up the source issue's entry
       b. Resolve its branch via _resolve_base_branch()
       c. If resolved branch ≠ "main", return it
    3. Fall back to get_base_ref_for_issue() (global oldest blocker)
    4. Ultimate fallback: "main"

    Args:
        repo_key: Repository identifier in "owner/repo" format.
        issue_number: GitHub issue number of the blocked issue.

    Returns:
        Branch name string. Never raises — returns "main" as final fallback.
    """
```

### _determine_base_ref() Integration (orchestrator.py)

```python
async def _determine_base_ref(
    self,
    ctx: WorkflowContext,
    agent_name: str,
    agent_index: int,
) -> tuple[str, str, dict | None]:
    """Determine base branch for agent work.

    Blocking queue integration (early in the function):
    """
    # ... existing setup ...

    try:
        from src.services import blocking_queue as bq_service
        repo_key = f"{ctx.repository_owner}/{ctx.repository_name}"
        # Prefer the entry-specific blocking_source_issue branch
        blocking_base = await bq_service.get_base_ref_for_entry(
            repo_key, ctx.issue_number
        )
        if blocking_base != "main":
            base_ref = blocking_base
    except Exception as e:
        logger.debug(
            "Blocking queue base_ref lookup skipped for #%d: %s",
            ctx.issue_number,
            e,
        )

    # ... rest of existing base_ref resolution ...
```

**Error handling**: All exceptions caught in `_determine_base_ref()`, logged at debug level, falls through to existing branch resolution logic.

## Resolution Chain Diagram

```text
_determine_base_ref(ctx)
  │
  ├─▶ bq_service.get_base_ref_for_entry(repo_key, issue_number)
  │     │
  │     ├─▶ store.get_by_issue(repo_key, issue_number)
  │     │     └─ entry.blocking_source_issue = 42
  │     │
  │     ├─▶ store.get_by_issue(repo_key, 42)        ← source issue's entry
  │     │     └─ source_entry.parent_branch = "copilot/fix-42"
  │     │
  │     ├─▶ _resolve_base_branch(source_entry)
  │     │     └─ returns "copilot/fix-42"
  │     │
  │     └─ returns "copilot/fix-42"                  ← issue-specific branch ✓
  │
  ├─ (if "main" or exception) ─▶ existing base_ref logic
  │
  └─ returns (base_ref, sha, pr)
```

## Behavioral Contract

| Scenario | get_base_ref_for_entry() | _determine_base_ref() |
|----------|-------------------------|-----------------------|
| Entry exists with blocking_source_issue, source has branch | Returns source's branch | Uses source's branch as base_ref |
| Entry exists with blocking_source_issue, source has no branch | Falls back to get_base_ref_for_issue() | Uses global oldest blocker's branch |
| Entry exists without blocking_source_issue | Falls back to get_base_ref_for_issue() | Uses global oldest blocker's branch |
| No entry (issue not in blocking queue) | Falls back to get_base_ref_for_issue() | Uses global oldest blocker's branch |
| Store/service exception | N/A (exception propagates) | Caught in _determine_base_ref(), falls through to existing logic |
