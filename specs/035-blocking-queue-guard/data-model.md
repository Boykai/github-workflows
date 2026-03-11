# Data Model: Enforce Blocking Queue in Polling Loop & Fix Branch Ancestry

**Branch**: `035-blocking-queue-guard` | **Date**: 2026-03-11

## Existing Entities (No Changes Required)

### BlockingQueueStatus Enum

**Location**: `backend/src/services/blocking_queue.py:10-16` (existing, unchanged)

```python
class BlockingQueueStatus(StrEnum):
    """Lifecycle states of a blocking queue entry."""

    PENDING = "pending"
    ACTIVE = "active"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
```

**Used by**: Guard function checks `== BlockingQueueStatus.PENDING`; sweep processes `ACTIVE`/`IN_REVIEW` entries.

### BlockingQueueEntry Model

**Location**: `backend/src/services/blocking_queue.py:19-33` (existing, unchanged)

```python
class BlockingQueueEntry(BaseModel):
    """A single entry in a repository's blocking queue."""

    id: int
    repo_key: str
    issue_number: int
    project_id: str
    is_blocking: bool
    queue_status: BlockingQueueStatus = BlockingQueueStatus.PENDING
    parent_branch: str | None = None
    blocking_source_issue: int | None = None
    created_at: str
    activated_at: str | None = None
    completed_at: str | None = None
```

**Key fields for this feature**:
- `queue_status`: Checked by guard function (PENDING → skip), by sweep (ACTIVE/IN_REVIEW → check staleness)
- `blocking_source_issue`: Used by `get_base_ref_for_entry()` to resolve the predecessor's branch
- `issue_number`: Primary lookup key alongside `repo_key`

---

## New Functions

### _is_pending_in_blocking_queue()

**Location**: `backend/src/services/copilot_polling/pipeline.py` (new private function)

```python
async def _is_pending_in_blocking_queue(repo_key: str, issue_number: int) -> bool:
    """Check whether an issue is PENDING in the blocking queue.

    Returns True if the issue has a blocking queue entry with PENDING status.
    Fails open on any exception (returns False) to avoid breaking non-blocking-queue users.
    """
    try:
        from src.services import blocking_queue as bq_service

        entry = await bq_service.get_entry(repo_key, issue_number)
        if entry and entry.queue_status == bq_service.BlockingQueueStatus.PENDING:
            logger.debug(
                "Issue #%d in %s is PENDING in blocking queue — skipping",
                issue_number,
                repo_key,
            )
            return True
    except Exception:
        logger.debug(
            "Blocking queue lookup failed for #%d in %s — failing open",
            issue_number,
            repo_key,
        )
    return False
```

**Parameters**:
- `repo_key` (`str`): Repository identifier in `"owner/repo"` format
- `issue_number` (`int`): GitHub issue number

**Returns**: `bool` — `True` if issue is PENDING (should be skipped), `False` otherwise (including on error)

**Used by**: `check_backlog_issues()`, `check_ready_issues()`, `check_in_progress_issues()`

---

### get_base_ref_for_entry()

**Location**: `backend/src/services/blocking_queue.py` (new public function)

```python
async def get_base_ref_for_entry(repo_key: str, issue_number: int) -> str:
    """Return the base branch using the issue's own ``blocking_source_issue``.

    Looks up the issue's queue entry, reads its ``blocking_source_issue``
    field, and resolves that specific issue's branch.  Falls back to the
    global ``get_base_ref_for_issue()`` if no entry or no source issue.
    """
    entry = await store.get_by_issue(repo_key, issue_number)
    if entry and entry.blocking_source_issue:
        source_entry = await store.get_by_issue(repo_key, entry.blocking_source_issue)
        if source_entry:
            branch = await _resolve_base_branch(source_entry)
            if branch != "main":
                return branch
    return await get_base_ref_for_issue(repo_key, issue_number)
```

**Parameters**:
- `repo_key` (`str`): Repository identifier in `"owner/repo"` format
- `issue_number` (`int`): GitHub issue number of the blocked issue

**Returns**: `str` — Branch name resolved from the blocking source issue, or fallback to global/main

**Resolution chain**:
1. Look up issue's own queue entry
2. Read `blocking_source_issue` from entry
3. Look up source issue's entry → resolve its branch via `_resolve_base_branch()`
4. If branch ≠ "main", return it
5. Otherwise, fall back to `get_base_ref_for_issue()` (global oldest blocker)
6. Ultimate fallback: "main"

**Used by**: `orchestrator._determine_base_ref()`

---

## Modified Return Types

### sweep_stale_entries()

**Location**: `backend/src/services/blocking_queue.py:472` (modified return type)

```python
async def sweep_stale_entries(
    access_token: str,
    owner: str,
    repo: str,
) -> tuple[list[int], list[BlockingQueueEntry]]:
    """Sweep stale blocking queue entries and return both swept and activated.

    Returns:
        tuple of:
        - list[int]: Issue numbers that were swept (marked completed)
        - list[BlockingQueueEntry]: Entries that were newly activated
    """
```

**Change**: The return type includes `list[BlockingQueueEntry]` for activated entries (from `mark_completed()` return values), enabling callers to dispatch agents without re-querying the store.

**Used by**: `polling_loop._step_sweep_blocking_queue()`

---

## State Transitions

```text
Issue Lifecycle in Blocking Queue:

  ┌─────────┐    mark_completed()    ┌─────────┐
  │ PENDING │ ──────────────────────▶│ ACTIVE  │
  └─────────┘    (predecessor done)  └─────────┘
       │                                  │
       │  Guard: skip in polling          │  Allowed through polling
       │  Guard: skip in recovery         │  Agent dispatched
       │                                  │
       ▼                                  ▼
  (no pipeline started)            ┌───────────┐
                                   │ IN_REVIEW │
                                   └───────────┘
                                        │
                                        ▼
                                   ┌───────────┐
                                   │ COMPLETED │
                                   └───────────┘
```

---

## No Schema Changes

The existing SQLite schema and Pydantic models are sufficient for all changes in this feature. No new tables, columns, or model fields are required. The `blocking_source_issue` field already exists on `BlockingQueueEntry` and is populated during queue entry creation.
