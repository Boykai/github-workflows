# Quickstart: Add 'Clean Up' Button to Delete Stale Branches and PRs

**Feature**: 015-stale-cleanup-button  
**Date**: 2026-03-01

## Overview

This feature adds a 'Clean Up' button to the project board that allows maintainers to remove stale branches and pull requests while preserving `main` and any items linked to open issues on the associated GitHub Projects v2 board. The implementation includes a preflight check, confirmation modal, progress tracking, and an audit trail.

## Prerequisites

- Docker and Docker Compose (existing dev setup)
- GitHub OAuth app configured (existing)
- Node.js 18+ and Python 3.11+ (existing)
- Repository with a linked GitHub Projects v2 board
- User with `push` access to the repository

## Development Setup

```bash
# From repo root — start all services
docker compose up -d

# Or run frontend/backend separately for dev:
cd backend && pip install -e ".[dev]" && uvicorn src.main:app --reload
cd frontend && npm install && npm run dev
```

The database migration (`008_cleanup_audit_logs.sql`) runs automatically on backend startup.

## Key Files to Modify/Create

### Backend

| File | Action | Purpose |
|------|--------|---------|
| `backend/src/migrations/008_cleanup_audit_logs.sql` | Create | Audit trail table |
| `backend/src/models/cleanup.py` | Create | Pydantic models (request/response) |
| `backend/src/services/cleanup_service.py` | Create | Preflight logic, execution, audit storage |
| `backend/src/api/cleanup.py` | Create | REST endpoints (preflight, execute, history) |
| `backend/src/api/__init__.py` | Modify | Register cleanup router |

### Frontend

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/types/index.ts` | Modify | Add cleanup TypeScript interfaces |
| `frontend/src/services/api.ts` | Modify | Add cleanup API client methods |
| `frontend/src/hooks/useCleanup.ts` | Create | React hook for cleanup workflow state |
| `frontend/src/components/board/CleanUpButton.tsx` | Create | Button with tooltip trigger |
| `frontend/src/components/board/CleanUpConfirmModal.tsx` | Create | Confirmation modal with item lists |
| `frontend/src/components/board/CleanUpSummary.tsx` | Create | Post-operation summary/audit trail |
| `frontend/src/pages/ProjectBoardPage.tsx` | Modify | Add CleanUpButton to board header |

## Implementation Order

1. **Database migration** — Create `cleanup_audit_logs` table (008)
2. **Backend models** — Pydantic models for request/response types
3. **Backend service** — Cleanup service with preflight, execute, and audit methods
   - Preflight: Fetch branches (REST), PRs (REST), project board issues (GraphQL)
   - Cross-reference: 3-layer linking strategy (naming, PR body, timeline events)
   - Permission check: Verify user has push access
   - Execute: Sequential branch deletion + PR closure with rate-limit handling
   - Audit: Store operation results in SQLite
4. **Backend API** — REST endpoints with auth dependency
5. **Frontend types** — TypeScript interfaces for all API shapes
6. **Frontend API client** — `cleanupApi` methods in `api.ts`
7. **Frontend hook** — `useCleanup` for workflow state management (idle → loading → confirming → executing → summary)
8. **Frontend CleanUpButton** — Button with tooltip on board header
9. **Frontend CleanUpConfirmModal** — Modal with deletion/preservation lists
10. **Frontend CleanUpSummary** — Post-operation summary with audit details
11. **Board integration** — Add CleanUpButton to ProjectBoard component

## Testing the Feature

### Manual Testing

1. Start the app and authenticate via GitHub OAuth
2. Navigate to a project board that has a linked GitHub Projects v2 board
3. Verify the "Clean Up" button appears in the board header area
4. Hover over the button and verify the tooltip explains the operation
5. Click the button and wait for the preflight to complete
6. Verify the confirmation modal shows:
   - `main` branch in the preserved list with reason "Default protected branch"
   - Branches linked to open issues in the preserved list with issue references
   - Stale branches in the deletion list
   - PRs categorized correctly
7. Click "Cancel" and verify no deletions occur
8. Click the button again, review the modal, and click "Confirm"
9. Verify the progress indicator shows during execution
10. Verify the summary report shows accurate counts
11. Verify the audit trail is accessible after dismissing the summary

### API Testing (curl)

```bash
# Preflight check (requires session cookie)
curl -b cookies.txt -X POST http://localhost:8000/api/v1/cleanup/preflight \
  -H "Content-Type: application/json" \
  -d '{"owner": "Boykai", "repo": "github-workflows", "project_id": "PVT_kwHOABcRss4A..."}'

# Execute cleanup
curl -b cookies.txt -X POST http://localhost:8000/api/v1/cleanup/execute \
  -H "Content-Type: application/json" \
  -d '{"owner": "Boykai", "repo": "github-workflows", "project_id": "PVT_kwHOABcRss4A...", "branches_to_delete": ["stale-branch"], "prs_to_close": [999]}'

# View audit history
curl -b cookies.txt "http://localhost:8000/api/v1/cleanup/history?owner=Boykai&repo=github-workflows"
```

### Validation Test Cases

- No branches except main → modal shows empty deletion list, confirm button disabled
- No open issues on project board → all branches (except main) in deletion list
- Branch linked to closed issue → appears in deletion list
- PR references open issue on board → appears in preserved list
- User without push access → 403 permission error before modal
- Network error during preflight → error message, no modal shown
- Rate limit during execution → individual item marked failed, operation continues
- Main branch in deletion request → 400 error, server-side rejection

### Edge Cases to Verify

- Repository with 200+ branches → pagination works correctly, no truncation
- Branch name with special characters → URL-encoded correctly in API calls
- PR with no referenced issues → appears in deletion list
- Multiple PRs for same issue → all preserved if issue is open on board
- Concurrent cleanup attempts → handled gracefully (second attempt sees updated state)
