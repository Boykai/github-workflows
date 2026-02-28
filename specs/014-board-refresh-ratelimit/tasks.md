# Tasks: Add Manual Refresh Button & Auto-Refresh to Project Board with GitHub API Rate Limit Optimization

**Input**: Design documents from `/specs/014-board-refresh-ratelimit/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not mandated by the feature specification (Constitution Principle IV). Existing test files may be extended but no new test tasks are generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add shared constants and type definitions that all user stories depend on

- [ ] T001 Add AUTO_REFRESH_INTERVAL_MS (300000) and RATE_LIMIT_LOW_THRESHOLD (10) constants to frontend/src/constants.ts
- [ ] T002 [P] Add RateLimitInfo, RefreshErrorType, and RefreshError type definitions to frontend/src/types/index.ts

---

## Phase 2: Foundational (Backend Rate Limit & Caching Infrastructure)

**Purpose**: Backend changes that MUST be complete before ANY user story can be implemented — rate limit model, cache ETag support, header extraction, and endpoint updates

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Add RateLimitInfo Pydantic model and add optional rate_limit field to BoardDataResponse in backend/src/models/board.py
- [ ] T004 [P] Add etag and last_modified optional fields to CacheEntry in backend/src/services/cache.py
- [ ] T005 Modify _request_with_retry and _graphql to extract X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers and store them on the service instance in backend/src/services/github_projects/service.py
- [ ] T006 Update get_board_data and list_board_projects endpoints to populate rate_limit from service headers in responses and return HTTP 429 with rate_limit body on rate limit errors in backend/src/api/board.py

**Checkpoint**: Backend infrastructure ready — rate limit info flows from GitHub API → service → endpoint → response body. User story implementation can now begin.

---

## Phase 3: User Story 1 — Manual Refresh of Project Board (Priority: P1) 🎯 MVP

**Goal**: A clearly visible refresh button on the project board that triggers an immediate data reload from GitHub, with a tooltip indicating auto-refresh frequency and a spinner during refresh.

**Independent Test**: Click the refresh button on the project board, verify the displayed data updates and a spinner shows during the operation. Hover over the button and verify tooltip "Auto-refreshes every 5 minutes" appears. Click rapidly 5 times and verify only 1 API call is made.

### Implementation for User Story 1

- [ ] T007 [P] [US1] Create RefreshButton component with refresh icon, spinning animation when isRefreshing is true, disabled state during refresh, and tooltip "Auto-refreshes every 5 minutes" in frontend/src/components/board/RefreshButton.tsx
- [ ] T008 [US1] Create useBoardRefresh hook with manual refresh() trigger, isRefreshing deduplication guard, lastRefreshedAt timestamp, and error state management in frontend/src/hooks/useBoardRefresh.ts
- [ ] T009 [US1] Update useProjectBoard to expose queryClient refetch and isFetching state for useBoardRefresh integration in frontend/src/hooks/useProjectBoard.ts
- [ ] T010 [US1] Add RefreshButton to ProjectBoardPage header area, wire onRefresh to useBoardRefresh.refresh(), pass isRefreshing state in frontend/src/pages/ProjectBoardPage.tsx

**Checkpoint**: Manual refresh button is visible, triggers data reload, shows spinner, prevents duplicate requests on rapid clicks. Tooltip displays on hover. User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 — Automatic Background Refresh (Priority: P2)

**Goal**: The board automatically refreshes every 5 minutes in the background, pauses when the tab is hidden, resumes with an immediate refresh when the tab becomes visible (if data is stale), and resets the timer on manual refresh or WebSocket events.

**Independent Test**: Open the project board, wait 5+ minutes without interaction, verify data refreshes automatically. Switch to another tab for 6+ minutes, switch back, verify an immediate refresh occurs. Manually refresh and verify the 5-minute countdown resets.

### Implementation for User Story 2

- [ ] T011 [US2] Add 5-minute auto-refresh setInterval timer to useBoardRefresh that resets on every successful manual refresh in frontend/src/hooks/useBoardRefresh.ts
- [ ] T012 [US2] Add Page Visibility API listener (document.visibilitychange) to useBoardRefresh to pause timer when tab hidden and resume with immediate refresh if stale > 5 minutes when tab visible in frontend/src/hooks/useBoardRefresh.ts
- [ ] T013 [US2] Add onRefreshComplete callback to useRealTimeSync so WebSocket-triggered cache invalidations reset the useBoardRefresh auto-refresh timer in frontend/src/hooks/useRealTimeSync.ts

**Checkpoint**: Auto-refresh fires every 5 minutes, pauses when tab hidden, resumes on tab visible with immediate refresh if stale, timer resets on manual refresh and WebSocket events. User Story 2 is fully functional and testable independently.

---

## Phase 5: User Story 3 — Rate Limit Awareness and Error Handling (Priority: P2)

**Goal**: When refresh fails due to rate limits, display a non-intrusive amber warning banner with reset time countdown. For non-rate-limit errors, display a red error banner. Auto-dismiss warnings on next successful refresh. Show preemptive warning when remaining quota is critically low (<10 requests).

**Independent Test**: Simulate a 429 rate limit response, verify the amber warning banner appears with reset time (e.g., "Rate limit reached. Resets in 12 minutes."). Trigger a successful refresh and verify the warning dismisses automatically. Verify a low quota warning appears when remaining < 10.

### Implementation for User Story 3

- [ ] T014 [US3] Add rate_limit field parsing from API response body in boardApi.getBoardData and boardApi.listProjects in frontend/src/services/api.ts
- [ ] T015 [US3] Add rate limit error detection (429 / 403 with rate limit headers), RateLimitInfo state tracking, isRateLimitLow computed flag, and auto-clear on success to useBoardRefresh in frontend/src/hooks/useBoardRefresh.ts
- [ ] T016 [US3] Add non-intrusive amber rate limit warning banner with reset countdown, red error banner for non-rate-limit failures, low quota preemptive warning, and auto-dismiss logic to ProjectBoardPage in frontend/src/pages/ProjectBoardPage.tsx

**Checkpoint**: Rate limit errors show amber warning with countdown, non-rate-limit errors show red banner, low quota shows preemptive warning, all warnings auto-dismiss on success. User Story 3 is fully functional and testable independently.

---

## Phase 6: User Story 4 — API Call Optimization and Caching (Priority: P3)

**Goal**: Minimize unnecessary GitHub API calls through ETag-based conditional requests (304 Not Modified), server-side cache integration, and frontend TanStack Query deduplication. Repeated calls for unchanged data should return cached results without consuming rate limit quota.

**Independent Test**: Monitor network calls during a series of refreshes. Verify that when data has not changed, the backend sends If-None-Match and receives 304 Not Modified. Verify that rapid refreshes deduplicate to a single API call via TanStack Query and backend cache.

### Implementation for User Story 4

- [ ] T017 [US4] Implement ETag-based conditional requests by sending If-None-Match header with stored ETag in _graphql and _request_with_retry in backend/src/services/github_projects/service.py
- [ ] T018 [US4] Handle 304 Not Modified responses to refresh cache TTL without replacing cached data and update ETag storage in backend/src/services/cache.py
- [ ] T019 [US4] Audit and verify request deduplication: confirm TanStack Query deduplicates concurrent fetches for same query key, confirm backend cache prevents duplicate GitHub API calls within TTL window in frontend/src/hooks/useProjectBoard.ts

**Checkpoint**: Conditional requests use ETags, 304 responses preserve cached data, duplicate requests are eliminated. API calls per refresh cycle reduced. User Story 4 is fully functional and testable independently.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cross-cutting improvements across all user stories

- [ ] T020 [P] Update quickstart.md with refresh feature manual testing steps and rate limit simulation instructions in specs/014-board-refresh-ratelimit/quickstart.md
- [ ] T021 Validate all edge cases from spec.md: rapid clicks dedup, concurrent auto+manual refresh suppression, network loss handling, token expiry error display, 500/503 transient error retry
- [ ] T022 Code cleanup: ensure consistent error handling patterns across all modified files and verify no regressions in existing board functionality

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Stories (Phases 3–6)**: All depend on Foundational phase (Phase 2) completion
  - User stories can proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3)
  - US2 builds on useBoardRefresh from US1 (same file — sequential recommended)
  - US3 builds on useBoardRefresh from US1/US2 (same file — sequential recommended)
  - US4 backend tasks (T017, T018) are independent of frontend stories and can run in parallel
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 2 (P2)**: Extends useBoardRefresh from US1 — Recommended after US1; independently testable
- **User Story 3 (P2)**: Extends useBoardRefresh from US1/US2 — Recommended after US2; independently testable
- **User Story 4 (P3)**: Backend tasks (T017, T018) independent of frontend stories; T019 audits existing behavior — Can start after Phase 2

### Within Each User Story

- Models/types before hooks
- Hooks before components
- Components before page integration
- Core implementation before cross-cutting concerns

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (different files)
- **Phase 2**: T003 and T004 can run in parallel (different files); T005 after T004; T006 after T003 and T005
- **Phase 3**: T007 (RefreshButton component) can run in parallel with T008/T009 (hook work)
- **Phase 6**: T017 and T018 (backend) can run in parallel with T019 (frontend audit)
- **Cross-phase**: US4 backend tasks (T017, T018) can run in parallel with US1–US3 frontend work

---

## Parallel Example: User Story 1

```bash
# Launch component and hook in parallel (different files):
Task T007: "Create RefreshButton component in frontend/src/components/board/RefreshButton.tsx"
Task T008: "Create useBoardRefresh hook in frontend/src/hooks/useBoardRefresh.ts"

# Then sequentially:
Task T009: "Update useProjectBoard in frontend/src/hooks/useProjectBoard.ts"
Task T010: "Wire into ProjectBoardPage in frontend/src/pages/ProjectBoardPage.tsx"
```

## Parallel Example: Cross-Phase Backend + Frontend

```bash
# Backend US4 optimization can run alongside frontend US1–US3:
Backend Dev: T017 (ETag in service.py) + T018 (304 handling in cache.py)
Frontend Dev: T007–T016 (US1 through US3 implementation)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational backend infrastructure (T003–T006)
3. Complete Phase 3: User Story 1 — Manual Refresh (T007–T010)
4. **STOP and VALIDATE**: Test refresh button independently — click triggers reload, spinner shows, tooltip displays, rapid clicks deduplicate
5. Deploy/demo if ready — the board now has a working manual refresh button

### Incremental Delivery

1. Complete Setup + Foundational → Backend infrastructure ready
2. Add User Story 1 → Test independently → Deploy/Demo (**MVP!**)
3. Add User Story 2 → Test independently → Deploy/Demo (auto-refresh + tab visibility)
4. Add User Story 3 → Test independently → Deploy/Demo (rate limit warnings)
5. Add User Story 4 → Test independently → Deploy/Demo (ETag optimization)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - **Frontend Dev**: User Story 1 → User Story 2 → User Story 3 (sequential — same hooks)
   - **Backend Dev**: User Story 4 backend tasks (T017, T018) in parallel with frontend work
3. T019 (audit) runs after both frontend and backend changes are complete
4. Polish phase after all stories

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 22 |
| **Phase 1 (Setup)** | 2 tasks |
| **Phase 2 (Foundational)** | 4 tasks |
| **Phase 3 (US1 — Manual Refresh, P1)** | 4 tasks |
| **Phase 4 (US2 — Auto Refresh, P2)** | 3 tasks |
| **Phase 5 (US3 — Rate Limit Awareness, P2)** | 3 tasks |
| **Phase 6 (US4 — API Optimization, P3)** | 3 tasks |
| **Phase 7 (Polish)** | 3 tasks |
| **Parallel opportunities** | 5 identified (within-phase and cross-phase) |
| **Suggested MVP scope** | Phases 1–3 (US1 only): 10 tasks |
| **Format validation** | ✅ All 22 tasks follow `- [ ] [TaskID] [P?] [Story?] Description with file path` |

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests not included per spec (Constitution Principle IV: "Tests not mandated")
