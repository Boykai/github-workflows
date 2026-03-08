# Quickstart: Fix 'Every X Issues' Chore Counter to Only Count GitHub Parent Issues

**Feature**: 030-fix-chore-issue-counter | **Date**: 2026-03-08

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 030-fix-chore-issue-counter
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
# Database migrations run automatically on startup
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## Files to Modify

### Frontend

| File | Changes |
|------|---------|
| `frontend/src/pages/ChoresPage.tsx` | Add chore-label exclusion filter to `parentIssueCount` useMemo computation (line ~49) |

### Backend (Optional — Documentation Only)

| File | Changes |
|------|---------|
| `backend/src/services/chores/counter.py` | Clarify docstring to specify that `current_count` must exclude chore-labelled issues |

## No New Files

This is a bug fix — no new files, components, migrations, or endpoints are needed.

## Verification

### Manual Testing

1. Start the backend and frontend (see Setup above)
2. Navigate to the Chores page
3. Create or use an existing Chore with "Every X issues" schedule
4. Create several GitHub issues:
   - Regular issues (no special labels) — should increment counter
   - Issues with the `chore` label — should NOT increment counter
   - Sub-issues (children of existing issues) — should NOT increment counter
5. Verify:
   - The tile counter shows the correct remaining count (excluding chores and sub-issues)
   - The "Featured Rituals" Next Run card reflects the same count
   - The trigger fires at the correct threshold

### Automated Tests

```bash
# Backend counter tests (existing — should pass without changes)
cd backend
python -m pytest tests/unit/test_chores_counter.py -v

# Frontend type checking
cd frontend
npx tsc --noEmit

# Frontend tests
cd frontend
npx vitest run
```

## Key Code Paths

### Counter Computation (Frontend)

```
ChoresPage.tsx:parentIssueCount useMemo
  → Filters boardData.columns[*].items[*]
  → Excludes: non-issues, sub-issues, chore-labelled items, duplicates
  → Returns: count of qualifying parent issues
```

### Counter Display (Frontend)

```
ChoreCard.tsx:getNextTriggerInfo()
  → issuesSince = parentIssueCount - chore.last_triggered_count
  → remaining = max(0, schedule_value - issuesSince)
  → Display: "X issues remaining" or "Ready to trigger"

ChoreCard.tsx:getTopRightTriggerLabel()
  → Same calculation → Display: "remaining/schedule_value"
```

### Trigger Evaluation (Backend)

```
counter.py:evaluate_count_trigger()
  → issues_since = current_count - chore.last_triggered_count
  → Returns: issues_since >= schedule_value
```

### Trigger Reset (Backend)

```
service.py:trigger_chore()
  → Creates issue with labels=["chore"]
  → Updates last_triggered_count = parent_issue_count (CAS)
  → Increments execution_count
```
