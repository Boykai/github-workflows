# Quickstart: Reduce GitHub API Rate Limit Consumption

**Feature**: 022-api-rate-limit-protection  
**Branch**: `022-api-rate-limit-protection`

## What This Feature Does

Reduces GitHub API consumption from ~1,000+ calls/hour to ~70-100 calls/hour while idle on the project board page by fixing three compounding issues:

1. **WebSocket change detection** — Only sends refresh messages when data actually changes
2. **Frontend query decoupling** — Stops invalidating the expensive board data query on every WebSocket message
3. **Sub-issue caching** — Caches sub-issue data per-issue with a 10-minute TTL
4. **Cache TTL alignment** — Aligns backend board cache (300s) with frontend auto-refresh (5 min)

## Files Changed

| File | Change |
|------|--------|
| `backend/src/api/projects.py` | Add SHA-256 hash comparison to WebSocket refresh loop |
| `backend/src/api/board.py` | Change board cache TTL from 120 → 300 seconds |
| `backend/src/services/github_projects/service.py` | Add cache check in `get_sub_issues()` |
| `backend/src/services/cache.py` | Add `get_sub_issues_cache_key()` helper |
| `backend/src/constants.py` | Add `CACHE_PREFIX_SUB_ISSUES` constant |
| `frontend/src/hooks/useRealTimeSync.ts` | Remove board data query invalidation from WebSocket handler |

## Verification Steps

### 1. Run existing tests
```bash
cd backend && python -m pytest tests/
```
All tests should pass without modification.

### 2. Verify idle behavior (Docker)
```bash
docker compose up
# Open project board in browser
# Wait 5 minutes while idle
# Check backend logs
```
**Expected**: No repeated "Refreshed N tasks" log entries when data hasn't changed.

### 3. Verify sub-issue caching
```bash
# In backend logs, look for:
# "Cache hit: sub_issues:owner/repo#123" — cache is working
# "Cache set: sub_issues:owner/repo#123 (TTL: 600s)" — first fetch
```

### 4. Verify rate limit stability
```bash
# Check GitHub rate limit headers in responses
# Rate limit remaining should decrease by <100 over 1 hour of idle viewing
```

### 5. Verify manual refresh still works
- Click refresh button on the board
- All data should be fresh (full API call count in logs)
- New sub-issue cache entries should appear in logs

## Rollback

All changes are independent and can be reverted individually:
- WebSocket hash: remove hash comparison, restore unconditional send
- Frontend invalidation: restore `['board', 'data', projectId]` invalidation
- Sub-issue cache: remove cache check, restore direct API call
- Board TTL: change 300 back to 120
