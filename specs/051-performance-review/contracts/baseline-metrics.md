# Contract: Baseline Metrics

**Feature**: `051-performance-review`
**Date**: 2026-03-18

---

## Overview

This contract defines the metrics that must be captured before any optimization code changes, the procedures for capturing them, and the success criteria for each metric.

## Metric Definitions

### Backend Metrics

#### BM-1: Idle API Call Rate

**Definition**: Number of external GitHub API calls made by the backend while a board is open and idle (no user interaction, no data changes) over a 5-minute measurement window, averaged per minute.

**Measurement Procedure**:
1. Open a project board with a WebSocket connection
2. Ensure no other users are modifying the project
3. Wait for initial data load to complete
4. Start a 5-minute timer
5. Count all HTTP requests to `api.github.com` (via logging or network inspection)
6. Divide total calls by 5 to get per-minute average

**Success Criterion (SC-001)**: ≤2 calls/minute average, and at least 50% reduction from baseline.

**Current Expected Behavior**: The WebSocket handler checks every 30 seconds (≈10 checks in 5 minutes). Each check may or may not hit cache. With a 300-second cache TTL, at most 1–2 cache misses should occur, resulting in 1–2 external calls over 5 minutes (≈0.4 calls/minute). If the baseline exceeds this, the stale-revalidation or sub-issue fetch paths are generating excess calls.

---

#### BM-2: Board Endpoint Request Cost

**Definition**: Total number of external API calls and response time for a single board data endpoint call (`GET /api/v1/board/projects/{project_id}`), broken down by:
- Board data fetch (1 call expected)
- Sub-issue fetches (N calls, one per board item with sub-issues)
- Rate-limit info fetch (0 additional calls, extracted from headers)

**Measurement Procedure**:
1. Clear all caches (restart backend or call with `refresh=true`)
2. Make a single board data request
3. Count external API calls triggered during the request
4. Record total response time
5. Repeat with warm caches (no `refresh=true`) and compare

**Success Criterion (SC-003)**: Sub-issue fetch calls reduced by at least 40% during non-manual refreshes (warm cache reuse).

---

#### BM-3: Polling Cycle Cost

**Definition**: Number of external API calls made during a single fallback polling cycle (SSE endpoint) when no data has changed.

**Measurement Procedure**:
1. Disable WebSocket (force SSE fallback)
2. Wait for a polling cycle to complete
3. Count external API calls during that cycle
4. Repeat for 5 consecutive cycles

**Success Criterion (SC-005)**: ≤1 lightweight check per polling interval; no expensive full board refresh triggered.

---

### Frontend Metrics

#### FM-1: Board Time-to-Interactive (Warm Cache)

**Definition**: Time from navigation start to board being fully interactive (all columns rendered, cards clickable, no pending spinners) when board data is cached.

**Measurement Procedure**:
1. Navigate to a board and wait for full load (priming cache)
2. Navigate away from the board
3. Navigate back to the board
4. Measure time from route change to last meaningful paint (React Profiler or Performance API)

**Success Criterion (SC-002)**: At least 30% improvement over baseline.

---

#### FM-2: Render Cycle Count

**Definition**: Number of React component render cycles during a board data load, measured via React Profiler.

**Measurement Procedure**:
1. Enable React Profiler in development mode
2. Navigate to a board
3. Record the number of commits (render cycles) until the board is stable
4. Note which components re-render most frequently

**Success Criterion**: Reduction in render cycles, particularly for `BoardColumn` and `IssueCard` components.

---

#### FM-3: Interaction Frame Rate

**Definition**: Frame rate (FPS) during board interactions (card drag, popover open, column scroll) on a board with 50+ cards.

**Measurement Procedure**:
1. Load a board with 50+ cards across 4+ columns
2. Use Chrome DevTools Performance panel
3. Record a 5-second trace while:
   a. Dragging a card between columns
   b. Opening and closing a popover
   c. Scrolling through a column
4. Calculate average FPS during each interaction

**Success Criterion (SC-006)**: ≥30 FPS for all interactions.

---

#### FM-4: Network Request Count During Board Load

**Definition**: Number of network requests (XHR/Fetch) made during a full board page load.

**Measurement Procedure**:
1. Clear browser cache and cookies
2. Navigate to a board
3. Count all network requests in DevTools Network panel until board is stable
4. Categorize by type (board data, tasks, sub-issues, auth, static assets)

**Success Criterion**: Reduced request count compared to baseline, particularly for sub-issue and redundant refresh requests.

---

#### FM-5: Real-Time Update Latency

**Definition**: Time from a teammate's task status change to the card visually updating on the viewing user's board.

**Measurement Procedure**:
1. Open the same board in two browser sessions
2. In session A, change a task's status
3. In session B, measure time from the change to the card visually updating
4. Verify scroll position and open popovers are preserved

**Success Criterion (SC-004)**: Update visible within 3 seconds; no full board re-render; scroll position preserved.

## Baseline Capture Checklist

| # | Metric | Tool | Target | Baseline Value | Post-Optimization Value |
|---|--------|------|--------|---------------|------------------------|
| BM-1 | Idle API Call Rate | Backend logs / network inspector | ≤2/min | _TBD_ | _TBD_ |
| BM-2 | Board Endpoint Cost (cold) | Backend logs | Record | _TBD_ | _TBD_ |
| BM-2 | Board Endpoint Cost (warm) | Backend logs | 40% fewer sub-issue fetches | _TBD_ | _TBD_ |
| BM-3 | Polling Cycle Cost | Backend logs | ≤1 call/cycle | _TBD_ | _TBD_ |
| FM-1 | Board TTI (warm cache) | Performance API / Profiler | 30% faster | _TBD_ | _TBD_ |
| FM-2 | Render Cycle Count | React Profiler | Reduction | _TBD_ | _TBD_ |
| FM-3 | Drag FPS | DevTools Performance | ≥30 FPS | _TBD_ | _TBD_ |
| FM-3 | Popover FPS | DevTools Performance | ≥30 FPS | _TBD_ | _TBD_ |
| FM-3 | Scroll FPS | DevTools Performance | ≥30 FPS | _TBD_ | _TBD_ |
| FM-4 | Network Request Count | DevTools Network | Reduction | _TBD_ | _TBD_ |
| FM-5 | Real-Time Update Latency | Manual timing | ≤3 seconds | _TBD_ | _TBD_ |
