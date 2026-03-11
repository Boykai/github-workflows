# Contract: Blocking Queue Guard in Polling Loop

**Branch**: `035-blocking-queue-guard` | **Phase**: 1

## Purpose

Prevent PENDING blocking queue issues from starting agent pipelines during polling. A shared guard function checks each issue's blocking queue status before pipeline reconstruction; all three polling check functions call it as an early-exit condition.

## Interface

### Shared Guard Function (pipeline.py)

```python
async def _is_pending_in_blocking_queue(repo_key: str, issue_number: int) -> bool:
    """Check whether an issue is PENDING in the blocking queue.

    Returns True if the issue has a blocking queue entry with PENDING status.
    Fails open on any exception (returns False) to avoid breaking
    non-blocking-queue users.

    Args:
        repo_key: Repository identifier in "owner/repo" format.
        issue_number: GitHub issue number to check.

    Returns:
        True if PENDING (caller should skip this issue), False otherwise.
    """
```

**Error handling**: All exceptions caught, logged at debug level, returns `False` (fail-open).

### Guard Call Site: check_backlog_issues() (pipeline.py)

```python
async def check_backlog_issues(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list | None = None,
) -> list[dict[str, Any]]:
    # ... existing filtering ...
    for task in backlog_tasks:
        issue_number = task.issue_number
        if not issue_number:
            continue

        # NEW: Blocking queue guard — skip PENDING issues
        repo_key = f"{owner}/{repo}"
        if await _is_pending_in_blocking_queue(repo_key, issue_number):
            continue

        # Existing: reconstruct pipeline, process, etc.
        pipeline = await _get_or_reconstruct_pipeline(...)
```

### Guard Call Site: check_ready_issues() (pipeline.py)

Same pattern as `check_backlog_issues()` — guard inserted before pipeline reconstruction.

### Guard Call Site: check_in_progress_issues() (pipeline.py)

Same pattern as `check_backlog_issues()` — guard inserted before pipeline reconstruction.

## Recovery Exception Handler (recovery.py)

```python
async def _should_skip_recovery(
    issue_number: int,
    task_owner: str,
    task_repo: str,
    now: Any,
) -> bool:
    # ... existing cooldown check ...

    try:
        from src.services import blocking_queue as bq_service
        repo_key = f"{task_owner}/{task_repo}"
        bq_entry = await bq_service.get_entry(repo_key, issue_number)
        if bq_entry and bq_entry.queue_status == bq_service.BlockingQueueStatus.PENDING:
            return True  # Skip recovery for PENDING issues
    except Exception:
        logger.debug(
            "Blocking queue check failed for #%d — skipping recovery (fail-closed)",
            issue_number,
        )
        return True  # FAIL CLOSED: skip recovery on exception

    return False
```

**Error handling**: All exceptions caught, logged at debug level, returns `True` (fail-closed).

## Behavioral Contract

| Scenario | Polling Guard | Recovery Handler |
|----------|--------------|-----------------|
| Issue is PENDING | Skip (return True) | Skip (return True) |
| Issue is ACTIVE | Allow (return False) | Allow (return False) |
| Issue has no entry | Allow (return False) | Allow (return False) |
| Service exception | Allow (return False) — **fail-open** | Skip (return True) — **fail-closed** |
