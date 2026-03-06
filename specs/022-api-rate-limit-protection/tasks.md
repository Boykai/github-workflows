# Tasks: Reduce GitHub API Rate Limit Consumption

**Input**: Design documents from `/specs/022-api-rate-limit-protection/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec. Existing tests must pass (SC-006).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: No new project initialization needed — all changes are edits to existing files. This phase adds the shared constant and cache key helper used by multiple stories.

- [X] T001 Add `CACHE_PREFIX_SUB_ISSUES = "sub_issues"` constant in backend/src/constants.py
- [X] T002 [P] Add `get_sub_issues_cache_key(owner, repo, issue_number)` helper in backend/src/services/cache.py

**Checkpoint**: Shared infrastructure ready for user story implementation.

---

## Phase 2: User Story 1 — Idle Board Does Not Waste API Calls (Priority: P1) 🎯 MVP

**Goal**: Add hash-based change detection to the WebSocket refresh loop so refresh messages are only sent when data actually changes.

**Independent Test**: Open the project board, leave it idle for 5 minutes, verify no "Refreshed N tasks" log entries appear when data hasn't changed. Rate limit remaining should stay stable.

### Implementation for User Story 1

- [X] T003 [US1] Import `hashlib` and `json` at top of backend/src/api/projects.py
- [X] T004 [US1] Add `last_sent_hash: str | None = None` variable before the WebSocket refresh loop in backend/src/api/projects.py
- [X] T005 [US1] Add hash computation after task fetch: compute SHA-256 of `json.dumps([t.model_dump(mode="json") for t in tasks], sort_keys=True)` in backend/src/api/projects.py
- [X] T006 [US1] Wrap the `websocket.send_json()` call in the refresh loop with a hash comparison guard — only send if `current_hash != last_sent_hash`, then update `last_sent_hash = current_hash` in backend/src/api/projects.py
- [X] T007 [US1] Add debug log when refresh is skipped due to unchanged data in backend/src/api/projects.py

**Checkpoint**: WebSocket no longer sends redundant refresh messages. Idle board produces zero "Refreshed N tasks" log entries. External changes still trigger refresh within 30 seconds.

---

## Phase 3: User Story 2 — Board Data Refresh Uses Cached Sub-Issues (Priority: P2)

**Goal**: Cache sub-issue data per-issue with 600s TTL so board refreshes don't make N redundant REST calls.

**Independent Test**: Trigger two board refreshes within 10 minutes. Second refresh should show `Cache hit: sub_issues:...` in logs with no sub-issue REST calls.

### Implementation for User Story 2

- [X] T008 [US2] Add cache lookup at the start of `get_sub_issues()` in backend/src/services/github_projects/service.py — check `cache.get(sub_issues_key)`, return cached value on hit
- [X] T009 [US2] Add `cache.set(sub_issues_key, sub_issues, ttl_seconds=600)` after successful REST API response in `get_sub_issues()` in backend/src/services/github_projects/service.py
- [X] T010 [US2] Add sub-issue cache clearing logic in the board data endpoint's `refresh=true` path — iterate board items and delete matching `sub_issues:*` cache keys in backend/src/api/board.py
- [X] T011 [US2] Import `cache` and `get_sub_issues_cache_key` in backend/src/services/github_projects/service.py

**Checkpoint**: Board refreshes with warm sub-issue caches make ≤5 outbound API calls (down from 23+). Manual refresh (`refresh=true`) still bypasses all caches.

---

## Phase 4: User Story 3 — Frontend Does Not Trigger Expensive Board Re-fetches (Priority: P3)

**Goal**: Remove board data query invalidation from WebSocket message handler so each WebSocket message doesn't trigger 23+ API calls.

**Independent Test**: Trigger a WebSocket refresh message and verify via browser network tab that only the tasks API is called, not the board data endpoint.

### Implementation for User Story 3

- [X] T012 [P] [US3] Remove `queryClient.invalidateQueries({ queryKey: ['board', 'data', projectId] })` from the `initial_data`/`refresh` handler block in frontend/src/hooks/useRealTimeSync.ts
- [X] T013 [P] [US3] Remove `queryClient.invalidateQueries({ queryKey: ['board', 'data', projectId] })` from the `task_update`/`task_created`/`status_changed` handler block in frontend/src/hooks/useRealTimeSync.ts

**Checkpoint**: WebSocket messages only invalidate the tasks query. Board data refreshes on its own 5-minute auto-refresh schedule. Manual refresh (separate code path) still invalidates both queries.

---

## Phase 5: User Story 4 — Cache TTLs Are Aligned Across Layers (Priority: P4)

**Goal**: Align backend board data cache TTL with frontend's 5-minute auto-refresh interval.

**Independent Test**: Observe two consecutive 5-minute auto-refresh cycles. Second cycle should serve board data from cache (no GitHub API calls).

### Implementation for User Story 4

- [X] T014 [US4] Change `ttl_seconds=120` to `ttl_seconds=300` in the `cache.set()` call in backend/src/api/board.py

**Checkpoint**: Backend board cache stays warm across frontend auto-refresh cycles. No TTL-misalignment-caused cache misses.

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Validate all changes work together and existing tests pass.

- [X] T015 Run existing backend tests: `cd backend && python -m pytest tests/` — all must pass without modification
- [X] T016 [P] Start app in Docker, open board, monitor logs for 5 minutes idle — verify no "Refreshed N tasks" entries when data unchanged
- [X] T017 [P] Verify manual refresh still bypasses all caches — click refresh button and confirm full API call count in logs
- [X] T018 Run quickstart.md verification steps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **US1 (Phase 2)**: No dependencies on Setup or other stories — can start immediately (only edits `projects.py`)
- **US2 (Phase 3)**: Depends on Setup (Phase 1) for constant and cache key helper
- **US3 (Phase 4)**: No dependencies — can start immediately (only edits frontend `useRealTimeSync.ts`)
- **US4 (Phase 5)**: No dependencies — can start immediately (single line change in `board.py`)
- **Polish (Phase 6)**: Depends on all user stories being complete

### Parallel Opportunities

All four user stories operate on **different files** and can be implemented in **parallel**:

- US1 → `backend/src/api/projects.py`
- US2 → `backend/src/services/github_projects/service.py` + `backend/src/api/board.py` (refresh path)
- US3 → `frontend/src/hooks/useRealTimeSync.ts`
- US4 → `backend/src/api/board.py` (different section from US2)

### Parallel Example

```bash
# All four stories can run simultaneously after Setup:
Thread 1: T003 → T004 → T005 → T006 → T007  (US1: WebSocket hash)
Thread 2: T008 → T009 → T010 → T011          (US2: Sub-issue cache)
Thread 3: T012, T013                           (US3: Frontend decoupling — both [P])
Thread 4: T014                                 (US4: TTL alignment)
```

---

## Implementation Strategy

### MVP (Minimum Viable Product)

User Story 1 alone (T003–T007) delivers the highest impact: eliminates ~750 wasted API calls/hour by stopping redundant WebSocket refresh messages. This single change reduces idle consumption from ~1,000+ to ~250 calls/hour.

### Incremental Delivery

1. **US1** (5 tasks): WebSocket change detection → reduces idle calls by ~75%
2. **US2** (4 tasks): Sub-issue caching → reduces per-refresh cost by ~85%
3. **US3** (2 tasks): Frontend decoupling → eliminates cascading board re-fetches
4. **US4** (1 task): TTL alignment → eliminates misalignment cache misses
5. **Polish** (4 tasks): Verification and validation

### Summary

| Metric | Value |
|--------|-------|
| Total tasks | 18 |
| Setup tasks | 2 |
| US1 tasks | 5 |
| US2 tasks | 4 |
| US3 tasks | 2 |
| US4 tasks | 1 |
| Polish tasks | 4 |
| Parallelizable stories | 4 of 4 |
| Files modified | 6 |
| New files | 0 |
