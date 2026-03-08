# API Contracts: Fix 'Every X Issues' Chore Counter to Only Count GitHub Parent Issues

**Feature**: 030-fix-chore-issue-counter | **Date**: 2026-03-08

## Base URL

All endpoints are prefixed with `/api/v1` and require an authenticated session (same auth pattern as existing endpoints in `/api/v1/chores/*`).

---

## No New Endpoints

This bug fix does not require any new API endpoints. The existing endpoints are sufficient.

---

## Existing Endpoints (Unchanged)

### List Chores

```
GET /api/v1/chores/{project_id}
```

**No changes**. Response already includes `last_triggered_count` on each Chore, which is used by the frontend to compute the per-Chore counter.

### Trigger Chore

```
POST /api/v1/chores/{project_id}/{chore_id}/trigger
```

**No changes**. The trigger endpoint already:
1. Creates a GitHub issue with `labels=["chore"]`
2. Updates `last_triggered_count` to the current `parent_issue_count` via CAS update
3. Increments `execution_count`

The caller must pass the corrected `parentIssueCount` (excluding chore-labelled issues) via the request body or query parameter if the backend trigger evaluation is used. Currently, the frontend triggers chores directly and the `evaluate_triggers` endpoint is used for automated evaluation.

### Evaluate Triggers

```
POST /api/v1/chores/evaluate-triggers
```

**Behavioural note**: This endpoint accepts an optional `parent_issue_count` parameter. When the caller passes the corrected count (excluding chore-labelled issues and sub-issues), the trigger evaluation will correctly fire only when the qualifying parent issue threshold is met. The endpoint itself requires no code changes — the fix is in the count computation on the caller side.

**Request Body** (unchanged):
```json
{
  "project_id": "optional-project-id",
  "parent_issue_count": 42
}
```

**Response** (unchanged):
```json
{
  "evaluated": 5,
  "triggered": 1,
  "skipped": 4,
  "results": [
    {
      "chore_id": "uuid",
      "chore_name": "Weekly Security Scan",
      "triggered": true,
      "issue_number": 123,
      "issue_url": "https://github.com/owner/repo/issues/123"
    }
  ]
}
```

---

## Data Contract: parentIssueCount

The core contract change is in the **definition** of `parentIssueCount`, not in any API endpoint.

### Before (Bug)

```
parentIssueCount = count of BoardItems where:
  - content_type === 'issue'
  - NOT a sub-issue
  - unique by item_id
```

### After (Fix)

```
parentIssueCount = count of BoardItems where:
  - content_type === 'issue'
  - NOT a sub-issue
  - NOT labelled 'chore'     ← NEW FILTER
  - unique by item_id
```

This corrected count is used for:
1. Tile display (`ChoreCard` remaining calculation)
2. Featured Rituals panel (Next Run ranking)
3. Trigger evaluation (when passed to backend `evaluate_triggers` endpoint)
