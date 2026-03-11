# Contract: Sweep Dispatch for Activated Entries

**Branch**: `035-blocking-queue-guard` | **Phase**: 2

## Purpose

Ensure that issues activated by `sweep_stale_entries()` receive agent dispatch in the same sweep cycle. The sweep function returns activated entries alongside swept issue numbers; the polling loop iterates over activated entries and dispatches agents using the existing `_activate_queued_issue()` pattern.

## Interface

### sweep_stale_entries() (blocking_queue.py)

```python
async def sweep_stale_entries(
    access_token: str,
    owner: str,
    repo: str,
) -> tuple[list[int], list[BlockingQueueEntry]]:
    """Sweep stale blocking queue entries and activate next in line.

    Checks all ACTIVE and IN_REVIEW entries. For each entry whose
    corresponding GitHub issue is closed, marks the entry as COMPLETED
    and activates the next PENDING entry (if any).

    Args:
        access_token: GitHub access token for API calls.
        owner: Repository owner.
        repo: Repository name.

    Returns:
        Tuple of:
        - list[int]: Issue numbers of swept (completed) entries.
        - list[BlockingQueueEntry]: Entries newly activated by the sweep.
    """
```

**Key implementation detail**: Each call to `mark_completed()` returns `list[BlockingQueueEntry]` — the activated entries. The sweep function collects all activated entries across all mark_completed calls and returns them in the second tuple element.

### _step_sweep_blocking_queue() (polling_loop.py)

```python
async def _step_sweep_blocking_queue(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list,
) -> list:
    """Sweep stale blocking queue entries and dispatch agents for activated issues.

    Steps:
    1. Call sweep_stale_entries() to mark stale entries completed and activate next.
    2. Iterate over activated entries.
    3. For each activated entry, call _activate_queued_issue() to dispatch an agent.
    4. Catch per-entry exceptions to prevent one failure from blocking others.
    """
    from src.services import blocking_queue as bq_service

    swept, activated = await bq_service.sweep_stale_entries(
        access_token=access_token,
        owner=owner,
        repo=repo,
    )

    if activated:
        from src.services.copilot_polling.pipeline import _activate_queued_issue

        for entry in activated:
            try:
                await _activate_queued_issue(
                    access_token=access_token,
                    project_id=project_id,
                    owner=owner,
                    repo=repo,
                    issue_number=entry.issue_number,
                )
            except Exception:
                logger.warning(
                    "Failed to dispatch agent for activated issue #%d",
                    entry.issue_number,
                    exc_info=True,
                )

    return tasks
```

### Recovery Deferred Dispatch Logging (blocking_queue.py)

```python
async def recover_all_repos() -> None:
    """Recover blocking queue state for all repositories.

    Activates next PENDING entries where possible. Agent dispatch is
    deferred to the polling loop since recovery lacks access_token.
    """
    # ... existing recovery logic ...
    if activated:
        logger.info(
            "Blocking queue recovery activated %d entries for %s — "
            "agent dispatch deferred to polling loop",
            len(activated),
            repo_key,
        )
```

## Behavioral Contract

| Scenario | sweep_stale_entries() | _step_sweep_blocking_queue() |
|----------|----------------------|------------------------------|
| Stale entry found, next PENDING exists | Returns ([swept_num], [activated_entry]) | Dispatches agent for activated entry |
| Stale entry found, no PENDING exists | Returns ([swept_num], []) | No dispatch, continues normally |
| No stale entries | Returns ([], []) | No dispatch, continues normally |
| Dispatch fails for one entry | N/A | Logs warning, continues to next entry |
