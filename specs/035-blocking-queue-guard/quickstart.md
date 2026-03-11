# Quickstart: Enforce Blocking Queue in Polling Loop & Fix Branch Ancestry

**Branch**: `035-blocking-queue-guard` | **Date**: 2026-03-11

## Developer Guide — Blocking Queue Guard Integration

### Section 1: Shared Guard Function

#### Before: No blocking queue check in polling

```python
# In pipeline.py — check_backlog_issues()
for task in backlog_tasks:
    issue_number = task.issue_number
    if not issue_number:
        continue
    # Directly proceeds to pipeline reconstruction — even if PENDING in blocking queue
    pipeline = await _get_or_reconstruct_pipeline(
        access_token, owner, repo, issue_number, project_id, status, agents
    )
```

#### After: Guard skips PENDING issues before pipeline reconstruction

```python
# In pipeline.py — shared guard function
async def _is_pending_in_blocking_queue(repo_key: str, issue_number: int) -> bool:
    try:
        from src.services import blocking_queue as bq_service
        entry = await bq_service.get_entry(repo_key, issue_number)
        if entry and entry.queue_status == bq_service.BlockingQueueStatus.PENDING:
            return True
    except Exception:
        pass  # Fail open — allow processing if blocking queue is unavailable
    return False

# In pipeline.py — check_backlog_issues()
for task in backlog_tasks:
    issue_number = task.issue_number
    if not issue_number:
        continue
    repo_key = f"{owner}/{repo}"
    if await _is_pending_in_blocking_queue(repo_key, issue_number):
        continue  # Skip — blocked by predecessor
    pipeline = await _get_or_reconstruct_pipeline(...)
```

The same guard is inserted in `check_ready_issues()` and `check_in_progress_issues()`.

---

### Section 2: Recovery Fail-Closed Exception Handler

#### Before: Exception allows recovery to proceed (fail-open)

```python
# In recovery.py — _should_skip_recovery()
try:
    bq_entry = await bq_service.get_entry(repo_key, issue_number)
    if bq_entry and bq_entry.queue_status == bq_service.BlockingQueueStatus.PENDING:
        return True
except Exception:
    return False  # BUG: allows recovery when blocking queue is unavailable
```

#### After: Exception skips recovery (fail-closed)

```python
# In recovery.py — _should_skip_recovery()
try:
    bq_entry = await bq_service.get_entry(repo_key, issue_number)
    if bq_entry and bq_entry.queue_status == bq_service.BlockingQueueStatus.PENDING:
        return True
except Exception:
    logger.debug("Blocking queue check failed for #%d — skipping recovery", issue_number)
    return True  # FIXED: skip recovery when blocking queue is unavailable (fail-closed)
```

---

### Section 3: Sweep Dispatch for Activated Entries

#### Before: Sweep activates but doesn't dispatch

```python
# In polling_loop.py — _step_sweep_blocking_queue()
swept = await bq_service.sweep_stale_entries(access_token, owner, repo)
# swept is just a list of issue numbers — no activated entries returned
# Activated issues sit idle until next polling cycle picks them up
```

#### After: Sweep returns activated entries and dispatches agents

```python
# In polling_loop.py — _step_sweep_blocking_queue()
swept, activated = await bq_service.sweep_stale_entries(
    access_token=access_token, owner=owner, repo=repo
)
if activated:
    from src.services.copilot_polling.pipeline import _activate_queued_issue
    for entry in activated:
        try:
            await _activate_queued_issue(
                access_token, project_id, owner, repo, entry.issue_number
            )
        except Exception:
            logger.warning("Failed to dispatch agent for #%d", entry.issue_number)
```

---

### Section 4: Branch Ancestry via Entry-Specific Blocking Source

#### Before: Global oldest blocker determines branch

```python
# In blocking_queue.py — get_base_ref_for_issue()
async def get_base_ref_for_issue(repo_key: str, issue_number: int) -> str:
    oldest_blocking = await store.get_open_blocking(repo_key)
    return await _resolve_base_branch(oldest_blocking)
    # BUG: If A→B→C chain exists and D→E chain exists,
    # C gets A's branch instead of B's branch
```

#### After: Issue-specific blocking source determines branch

```python
# In blocking_queue.py — get_base_ref_for_entry()
async def get_base_ref_for_entry(repo_key: str, issue_number: int) -> str:
    entry = await store.get_by_issue(repo_key, issue_number)
    if entry and entry.blocking_source_issue:
        source_entry = await store.get_by_issue(repo_key, entry.blocking_source_issue)
        if source_entry:
            branch = await _resolve_base_branch(source_entry)
            if branch != "main":
                return branch  # Use predecessor's specific branch
    return await get_base_ref_for_issue(repo_key, issue_number)  # Fallback to global

# In orchestrator.py — _determine_base_ref()
try:
    blocking_base = await bq_service.get_base_ref_for_entry(repo_key, ctx.issue_number)
    if blocking_base != "main":
        base_ref = blocking_base  # Use entry-specific branch
except Exception:
    pass  # Fall through to existing branch resolution
```

---

### Section 5: Recovery Deferred Dispatch Logging

#### Before: Silent activation with no audit trail

```python
# In blocking_queue.py — recover_all_repos()
activated = await try_activate_next(repo_key)
# No logging — operator can't tell if dispatch was deferred or completed
```

#### After: Explicit deferred dispatch log

```python
# In blocking_queue.py — recover_all_repos()
activated = await try_activate_next(repo_key)
if activated:
    logger.info(
        "Blocking queue recovery activated %d entries for %s — "
        "agent dispatch deferred to polling loop",
        len(activated),
        repo_key,
    )
```

---

## Verification Commands

```bash
# Run all backend tests
cd backend && python -m pytest tests/ -v

# Run blocking queue tests specifically
cd backend && python -m pytest tests/unit/test_blocking_queue.py -v

# Run polling tests specifically
cd backend && python -m pytest tests/unit/test_copilot_polling.py -v

# Run recovery tests specifically
cd backend && python -m pytest tests/unit/test_recovery.py -v

# Run orchestrator tests specifically
cd backend && python -m pytest tests/unit/test_workflow_orchestrator.py -v

# Run integration tests
cd backend && python -m pytest tests/integration/test_blocking_pipeline.py -v
```
