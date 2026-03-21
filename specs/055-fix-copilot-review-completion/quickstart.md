# Quickstart: Fix Premature Copilot Review Completion in Agent Pipeline

**Feature**: `055-fix-copilot-review-completion` | **Date**: 2026-03-21

## Overview

This feature adds layered pipeline-position guards and durable timestamp storage to prevent the copilot-review step from being falsely marked as complete when earlier agents finish. All changes are backend-only, modifying 4 existing files and adding 1 new migration file.

## Prerequisites

- Python 3.13 with pip (backend)
- Repository cloned with `solune/` directory structure
- SQLite available (built into Python stdlib)

## Setup

```bash
cd solune/backend
pip install -r requirements.txt
```

## Key Implementation Patterns

### 1. Pipeline-Position Guard in _check_copilot_review_done() (Phase 1, Step 1.1)

**File**: `solune/backend/src/services/copilot_polling/helpers.py`

Add the guard at the top of `_check_copilot_review_done()`, before any API calls:

```python
async def _check_copilot_review_done(
    access_token: str,
    owner: str,
    repo: str,
    parent_issue_number: int,
    pipeline: "object | None" = None,  # NEW parameter
) -> bool:
    # ── Pipeline-position guard ──────────────────────────────────
    # If we know the pipeline state and copilot-review is NOT the
    # current agent, short-circuit immediately — no API calls needed.
    if pipeline is not None:
        current = getattr(pipeline, "current_agent", None)
        if current and current != "copilot-review":
            logger.warning(
                "Pipeline-position guard: copilot-review completion check skipped "
                "for issue #%d — current agent is '%s', not 'copilot-review'",
                parent_issue_number,
                current,
            )
            return False
    # ... existing function body unchanged ...
```

### 2. Pass Pipeline Through from _check_agent_done_on_sub_or_parent() (Phase 1, Step 1.2)

**File**: `solune/backend/src/services/copilot_polling/helpers.py`

Change the `copilot-review` branch (~line 194) to pass pipeline:

```python
    # ── copilot-review: completion = Copilot submitted a PR review ──
    if agent_name == "copilot-review":
        return await _check_copilot_review_done(
            access_token=access_token,
            owner=owner,
            repo=repo,
            parent_issue_number=parent_issue_number,
            pipeline=pipeline,  # NEW: pass pipeline for position guard
        )
```

### 3. Webhook Guard in update_issue_status_for_copilot_pr() (Phase 2, Step 2.1)

**File**: `solune/backend/src/api/webhooks.py`

Add the guard before the status update call (~line 557):

```python
    # ── Pipeline-position guard: only move to "In Review" when appropriate ──
    from src.services.copilot_polling import get_pipeline_state

    pipeline = get_pipeline_state(issue_number)
    if pipeline is not None:
        current_agent = getattr(pipeline, "current_agent", None)
        if current_agent and current_agent != "copilot-review":
            logger.warning(
                "Webhook guard: skipping 'In Review' move for issue #%d — "
                "pipeline current agent is '%s', not 'copilot-review'",
                issue_number,
                current_agent,
            )
            return {
                "status": "skipped",
                "event": "copilot_pr_ready",
                "pr_number": pr_number,
                "pr_author": pr_author,
                "repository": f"{repo_owner}/{repo_name}",
                "issue_number": issue_number,
                "reason": "pipeline_agent_not_copilot_review",
                "current_agent": current_agent,
                "message": (
                    f"Skipped moving issue #{issue_number} to 'In Review': "
                    f"pipeline current agent is '{current_agent}', not 'copilot-review'"
                ),
            }
```

### 4. SQLite Migration (Phase 3, Step 3.1)

**File**: `solune/backend/src/migrations/033_copilot_review_requests.sql`

```sql
CREATE TABLE IF NOT EXISTS copilot_review_requests (
    issue_number INTEGER PRIMARY KEY,
    requested_at TEXT NOT NULL,
    project_id TEXT
);
```

### 5. Persist Timestamp to SQLite (Phase 3, Step 3.2)

**File**: `solune/backend/src/services/copilot_polling/helpers.py`

In `_record_copilot_review_request_timestamp()`, after storing in-memory, add SQLite write:

```python
    _copilot_review_requested_at[issue_number] = effective_requested_at

    # Persist to SQLite for restart durability
    try:
        from src.services.database import get_db
        async with get_db() as db:
            await db.execute(
                "INSERT OR REPLACE INTO copilot_review_requests "
                "(issue_number, requested_at, project_id) VALUES (?, ?, ?)",
                (issue_number, effective_requested_at.isoformat(), None),
            )
            await db.commit()
    except Exception as e:
        logger.warning(
            "Failed to persist copilot-review request timestamp to SQLite for issue #%d: %s",
            issue_number,
            e,
        )
```

### 6. Recover Timestamp from SQLite (Phase 3, Step 3.3)

**File**: `solune/backend/src/services/copilot_polling/helpers.py`

In `_check_copilot_review_done()`, after the in-memory lookup fails (~line 303), add SQLite recovery before the HTML comment fallback:

```python
    request_ts = _copilot_review_requested_at.get(parent_issue_number)
    if request_ts is None:
        # Try SQLite recovery before HTML comment fallback
        try:
            from src.services.database import get_db
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT requested_at FROM copilot_review_requests WHERE issue_number = ?",
                    (parent_issue_number,),
                )
                row = await cursor.fetchone()
                if row:
                    from datetime import datetime, timezone
                    request_ts = datetime.fromisoformat(row[0]).replace(tzinfo=timezone.utc)
                    _copilot_review_requested_at[parent_issue_number] = request_ts
                    logger.info(
                        "Restored copilot-review request timestamp for issue #%d from SQLite",
                        parent_issue_number,
                    )
        except Exception as e:
            logger.warning(
                "Failed to recover copilot-review timestamp from SQLite for issue #%d: %s",
                parent_issue_number,
                e,
            )

        if request_ts is None:
            # Fall back to HTML comment parsing (existing behavior)
            request_ts = _extract_copilot_review_requested_at(issue_body)
            # ... rest of existing fallback chain ...
```

## Validation

```bash
# Backend lint
cd solune/backend
ruff check src/

# Backend type check
pyright src/
```

## File Change Summary

| File | Change Type | Description |
|------|------------|-------------|
| `helpers.py` | MODIFY | Add pipeline param + guard to `_check_copilot_review_done()`; pass pipeline from `_check_agent_done_on_sub_or_parent()`; add SQLite write in `_record_copilot_review_request_timestamp()`; add SQLite read in `_check_copilot_review_done()` |
| `pipeline.py` | MODIFY | Add pipeline-position guard context in `check_in_review_issues()` |
| `webhooks.py` | MODIFY | Add pipeline-position guard in `update_issue_status_for_copilot_pr()` |
| `033_copilot_review_requests.sql` | ADD | SQLite migration for durable timestamp storage |

## Architecture Notes

- **No new dependencies** — aiosqlite and SQLite are already used in the project
- **No new abstractions** — guards are inline `if` checks with early returns
- **Zero-cost when guard passes** — guard checks are in-memory pipeline cache lookups; no API calls
- **Backward compatible** — all guards are optional (skip when no pipeline context available)
- **Defense-in-depth** — three independent guard layers prevent false completion even if one fails
