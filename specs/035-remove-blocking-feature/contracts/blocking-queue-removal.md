# API Contract: Blocking Queue Endpoint Removal

**Branch**: `035-remove-blocking-feature` | **Date**: 2026-03-12 | **Plan**: [plan.md](../plan.md)

## Endpoints Being Removed

The following API endpoints are referenced in test files but were never implemented in the production router. They must be confirmed absent and all test references removed.

---

### POST `/api/v1/board/projects/{project_id}/blocking-queue/{issue_number}/skip`

**Purpose**: Mark an issue as non-blocking and dispatch agents for any newly activated pending issues.

**Current status**: Endpoint not registered in `backend/src/api/board.py` (confirmed: zero "blocking" references in the file). Tests in `test_api_board.py::TestSkipBlockingIssue` mock the underlying service calls.

**Action**: Remove `TestSkipBlockingIssue` test class from `test_api_board.py`.

**Request**: `POST` with no body
**Response** (planned):
```json
{
  "skipped": { "issue_number": 100, "queue_status": "active" },
  "activated": [{ "issue_number": 101, "queue_status": "active" }],
  "queue": []
}
```

---

### DELETE `/api/v1/board/projects/{project_id}/blocking-queue/{issue_number}`

**Purpose**: Remove an issue from the blocking queue and activate pending issues.

**Current status**: Endpoint not registered in `backend/src/api/board.py`. Tests in `test_api_board.py::TestDeleteBlockingIssue` mock the underlying service calls.

**Action**: Remove `TestDeleteBlockingIssue` test class from `test_api_board.py`.

**Request**: `DELETE` with no body
**Response** (planned):
```json
{
  "removed": { "issue_number": 100 },
  "activated": [{ "issue_number": 101 }],
  "queue": []
}
```

---

## API Fields Being Removed

### Blocking Queue Enqueue (internal)

The following internal service calls in `api/chat.py` will be removed:

```python
# REMOVE: Lines 913-928 in chat.py
from src.services import blocking_queue as bq_service
_bq_entry, issue_activated = await bq_service.enqueue_issue(
    repo_key, issue_number, project_id, proposal_is_blocking
)
```

### Workflow Execution Parameter

```python
# REMOVE: is_blocking parameter from workflow.py:269
result = await orchestrator.execute_full_workflow(
    ctx,
    recommendation,
    is_blocking=recommendation.is_blocking,  # ← Remove this parameter
)
```

After removal, the `execute_full_workflow` call will not pass any blocking-related parameter.

---

## Labels Being Removed

| Label | Purpose | Applied by |
|-------|---------|-----------|
| `blocking` | Indicates issue is in the blocking queue | `with_blocking_label()` in constants.py (never implemented) |

The `with_blocking_label()` function was never defined in `constants.py`. Import references in `signal_chat.py` and `orchestrator.py` must be removed.
