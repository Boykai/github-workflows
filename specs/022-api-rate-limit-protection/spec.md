# Feature Specification: Reduce GitHub API Rate Limit Consumption

**Feature Branch**: `022-api-rate-limit-protection`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Reduce GitHub API Rate Limit Consumption — The app is burning through GitHub rate limits while idle on the project board page due to three compounding issues: a WebSocket refresh loop triggering cascading frontend re-fetches, the board data endpoint making N+M API calls per request, and misaligned cache TTLs. The fix reduces ~1,000+ API calls/hour (idle) down to ~70-100."

## Assumptions

- The application uses GitHub's authenticated REST and GraphQL APIs with a standard rate limit of 5,000 requests/hour.
- The WebSocket subscription currently sends a refresh message with the full task list every ~30 seconds, regardless of whether data has changed.
- The frontend invalidates both the tasks query and the board data query on every WebSocket message, even when the board data query is expensive (~23 API calls per refresh).
- The board data endpoint fetches sub-issues individually (1 REST call per issue) and runs repository reconciliation (1 GraphQL call per repo), resulting in N+M API calls per board refresh.
- The board data cache TTL is currently 120 seconds while the frontend auto-refreshes every 5 minutes, creating a mismatch that causes unnecessary cache misses.
- Sub-issue data changes infrequently and is suitable for independent caching with a longer TTL.
- Copilot polling already has adaptive backoff and does not need changes in this feature.
- The existing in-memory cache infrastructure in the codebase can be reused for sub-issue caching.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Idle Board Does Not Waste API Calls (Priority: P1)

As a developer with the project board open and idle, I want the application to stop making redundant GitHub API calls so that my rate limit budget is preserved for actual work.

**Why this priority**: This is the highest-impact fix. The idle refresh loop is responsible for the majority of wasted API calls (~750/hour). Eliminating unnecessary WebSocket-triggered re-fetches immediately reduces idle consumption by over 75%.

**Independent Test**: Open the project board, leave it idle for 5 minutes, and verify that no repeated "Refreshed N tasks" log entries appear when data hasn't changed. Rate limit remaining should stay stable.

**Acceptance Scenarios**:

1. **Given** the project board is open and idle with no external changes, **When** the WebSocket refresh cycle runs, **Then** no refresh message is sent to the frontend because the data has not changed.
2. **Given** the project board is open and idle, **When** 5 minutes pass without user interaction, **Then** the total number of GitHub API calls made is fewer than 20 (down from ~500+).
3. **Given** an external change occurs (e.g., issue updated via GitHub UI), **When** the next WebSocket refresh cycle detects the change, **Then** a refresh message is sent and the frontend updates normally.

---

### User Story 2 — Board Data Refresh Uses Cached Sub-Issues (Priority: P2)

As a developer, I want sub-issue data to be cached independently so that board data refreshes do not make redundant per-issue API calls for data that rarely changes.

**Why this priority**: Each board refresh currently makes N individual REST calls for sub-issues. Independent sub-issue caching eliminates the majority of per-request API calls, reducing the cost of each board refresh from ~23 calls to ~3 calls.

**Independent Test**: Trigger two consecutive board data refreshes within 10 minutes and verify that the second refresh shows cache hits for sub-issue data in the logs, with significantly fewer outbound API calls.

**Acceptance Scenarios**:

1. **Given** sub-issue data was fetched within the last 10 minutes, **When** a board refresh is triggered, **Then** sub-issue data is served from cache without making new REST calls.
2. **Given** 20 issues on the board with sub-issues, **When** a board refresh occurs and all sub-issue caches are warm, **Then** the board refresh makes no more than 3 outbound API calls (project data + reconciliation, no sub-issue calls).
3. **Given** the sub-issue cache has expired for a specific issue, **When** a board refresh is triggered, **Then** only that issue's sub-issues are re-fetched while all other cached sub-issues are served from cache.

---

### User Story 3 — Frontend Does Not Trigger Expensive Board Re-fetches on WebSocket Messages (Priority: P3)

As a developer, I want the frontend to only invalidate the lightweight tasks query when receiving WebSocket messages, not the expensive board data query, so that each WebSocket message does not trigger 23+ API calls.

**Why this priority**: Even when WebSocket sends a legitimate change notification, the frontend should not cascade into an expensive board re-fetch. Board data has its own 5-minute refresh schedule. Decoupling these eliminates ~690 unnecessary API calls per hour.

**Independent Test**: Trigger a WebSocket refresh message and verify via network inspection that only the tasks API is called, not the board data endpoint.

**Acceptance Scenarios**:

1. **Given** the frontend receives a WebSocket refresh message, **When** the message is processed, **Then** only the tasks query is invalidated, not the board data query.
2. **Given** the board data was last fetched 2 minutes ago, **When** a WebSocket refresh message arrives, **Then** the board data is not re-fetched (it refreshes on its own 5-minute schedule).
3. **Given** the user manually clicks a refresh button, **When** the refresh action is triggered, **Then** both tasks and board data queries are invalidated and re-fetched.

---

### User Story 4 — Cache TTLs Are Aligned Across Layers (Priority: P4)

As a developer, I want the backend board data cache TTL to match the frontend's auto-refresh interval so that cache misses caused by TTL misalignment are eliminated.

**Why this priority**: The current 120-second backend cache TTL means every other frontend auto-refresh (every 5 minutes) hits an expired cache and triggers a full board data fetch. Aligning to 300 seconds eliminates these unnecessary full fetches.

**Independent Test**: Observe backend cache behavior during two consecutive 5-minute auto-refresh cycles and verify that the second cycle serves board data from cache when data hasn't changed.

**Acceptance Scenarios**:

1. **Given** the board data cache TTL is set to 300 seconds, **When** the frontend auto-refreshes at 5-minute intervals, **Then** the cache is still warm and serves cached data without hitting GitHub API.
2. **Given** the board data was cached 4 minutes ago, **When** a board data request arrives, **Then** the cached data is returned without making new API calls.

---

### Edge Cases

- What happens when the WebSocket connection drops and reconnects? The system should perform a single full refresh on reconnect, then resume change-detection-based updates.
- What happens when a large number of issues change simultaneously (e.g., bulk update via GitHub API)? The change detection should detect the difference and send exactly one refresh message with the updated data.
- What happens when the sub-issue cache is cold (first load or after restart)? The system should fetch all sub-issues normally on the first request and populate the cache for subsequent requests.
- What happens when a user manually forces a refresh? Manual refresh should bypass all caches and fetch fresh data from GitHub, then repopulate caches with the fresh data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement change detection on WebSocket refresh cycles by comparing a hash of the current task data against the previously sent hash, and only send a refresh message when the hash differs.
- **FR-002**: System MUST store the last-sent data hash per WebSocket subscription so that idle connections with unchanged data produce zero outbound messages.
- **FR-003**: Frontend MUST only invalidate the tasks query (`['projects', projectId, 'tasks']`) when receiving WebSocket refresh or initial_data messages, and MUST NOT invalidate the board data query (`['board', 'data', projectId]`).
- **FR-004**: Frontend MUST continue to allow manual refresh actions to invalidate both tasks and board data queries.
- **FR-005**: System MUST cache sub-issue data independently per issue with a configurable TTL (default 600 seconds), checking cache before making REST API calls.
- **FR-006**: System MUST serve sub-issue data from cache when the cache entry is valid, eliminating individual REST calls for unchanged sub-issues during board refreshes.
- **FR-007**: System MUST set the board data cache TTL to 300 seconds to align with the frontend's 5-minute auto-refresh interval.
- **FR-008**: System MUST invalidate the sub-issue cache for a specific issue when that issue is known to have changed (e.g., via WebSocket notification or user action).
- **FR-009**: Manual refresh actions MUST bypass all caches (board data cache and sub-issue cache) and fetch fresh data from GitHub API.
- **FR-010**: System SHOULD log cache hit/miss events for sub-issues to support debugging and verification of cache effectiveness.

### Key Entities

- **WebSocket Subscription State**: Tracks the last-sent data hash for each active WebSocket connection, enabling change detection on refresh cycles.
- **Sub-Issue Cache**: Per-issue cache storing sub-issue data with independent TTL. Keyed by parent issue identifier. Supports lookup, invalidation, and TTL-based expiry.
- **Board Data Cache**: Existing cache for board-level data. TTL is aligned to the frontend refresh interval (300 seconds).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idle API call consumption drops from ~1,000+ calls/hour to fewer than 100 calls/hour with the project board open and no user interaction.
- **SC-002**: No WebSocket refresh messages are sent when the underlying task data has not changed, verifiable via backend logs showing no "Refreshed N tasks" entries during idle periods.
- **SC-003**: Board data refreshes with warm sub-issue caches make no more than 5 outbound API calls (down from 23+), verifiable by monitoring outbound request count per board refresh.
- **SC-004**: Rate limit remaining counter remains stable (decreasing by fewer than 100 per hour) during idle board viewing, verifiable via GitHub API rate-limit response headers.
- **SC-005**: Manual refresh still retrieves fully fresh data by bypassing all caches, verifiable by observing full API call counts on manual refresh.
- **SC-006**: All existing backend tests pass without modification after the changes are applied.
- **SC-007**: The frontend continues to display up-to-date task data within 30 seconds of an external change occurring on GitHub.
