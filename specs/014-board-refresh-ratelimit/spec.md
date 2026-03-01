# Feature Specification: Add Manual Refresh Button & Auto-Refresh to Project Board with GitHub API Rate Limit Optimization

**Feature Branch**: `014-board-refresh-ratelimit`  
**Created**: 2026-02-28  
**Status**: Draft  
**Input**: User description: "Add Manual Refresh Button & Auto-Refresh (5min) to Project Board with GitHub API Rate Limit Optimization"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manual Refresh of Project Board (Priority: P1)

As a project board user, I want a clearly visible refresh button on the project board so that I can instantly reload the latest data from GitHub whenever I need the most current information, without having to reload the entire page.

**Why this priority**: This is the core interaction — a visible, reliable way for users to trigger an immediate data refresh. Without this, users must rely solely on full page reloads, which is disruptive and slow. This delivers immediate, tangible value as a standalone feature.

**Independent Test**: Can be fully tested by clicking the refresh button on the project board and verifying that the displayed data updates to reflect the latest state from GitHub.

**Acceptance Scenarios**:

1. **Given** the project board is displayed with data, **When** the user clicks the refresh button, **Then** the board data reloads from GitHub and the displayed content updates to reflect the latest state.
2. **Given** the project board is displayed, **When** the user hovers over the refresh button, **Then** a tooltip appears indicating the automatic refresh frequency (e.g., "Auto-refreshes every 5 minutes").
3. **Given** a data refresh is already in progress, **When** the user clicks the refresh button again, **Then** the system does not trigger a duplicate refresh and instead lets the in-progress refresh complete.
4. **Given** the project board is displayed, **When** the user clicks the refresh button, **Then** a visual indicator (e.g., spinner or animation) shows that a refresh is in progress, and it disappears once the refresh completes.

---

### User Story 2 - Automatic Background Refresh (Priority: P2)

As a project board user, I want the board to automatically refresh its data every 5 minutes in the background so that I always see reasonably up-to-date information without needing to manually trigger refreshes.

**Why this priority**: Automatic refresh ensures data freshness without user intervention, which is essential for a monitoring/dashboard experience. It builds on the manual refresh infrastructure (P1) but adds the timer-based scheduling layer.

**Independent Test**: Can be tested by opening the project board, waiting at least 5 minutes without interaction, and verifying that the displayed data updates automatically.

**Acceptance Scenarios**:

1. **Given** the project board is open and the browser tab is visible, **When** 5 minutes elapse since the last refresh (manual or automatic), **Then** the board data automatically refreshes in the background.
2. **Given** the user manually triggers a refresh, **When** the auto-refresh timer was partially elapsed, **Then** the auto-refresh countdown resets to 5 minutes from the time of the manual refresh.
3. **Given** the browser tab containing the project board is hidden (user switched to another tab), **When** the auto-refresh interval elapses, **Then** the auto-refresh is paused or skipped to conserve resources.
4. **Given** the browser tab was hidden and is brought back into focus, **When** the tab becomes visible again, **Then** the system triggers an immediate refresh if the data is older than 5 minutes, and resumes the normal auto-refresh cycle.

---

### User Story 3 - Rate Limit Awareness and Error Handling (Priority: P2)

As a project board user, I want to be clearly informed when data refreshes fail due to GitHub API rate limits, including when the limit will reset, so that I understand why data may be stale and know when to expect normal operation to resume.

**Why this priority**: Without rate limit awareness, users face silent failures and stale data with no explanation. This is critical for trust and usability — users need to understand system state. Ranked P2 because it's essential for production reliability but depends on the refresh infrastructure from P1.

**Independent Test**: Can be tested by simulating a rate-limited API response and verifying that the warning indicator appears with the correct reset time information.

**Acceptance Scenarios**:

1. **Given** a refresh (manual or automatic) fails due to GitHub API rate limits, **When** the failure occurs, **Then** a non-intrusive warning indicator is displayed on the project board informing the user that the rate limit has been reached.
2. **Given** a rate limit error has occurred and the API response includes the time until the limit resets, **When** the warning indicator is displayed, **Then** it includes the approximate time remaining until the rate limit resets (e.g., "Rate limit reached. Resets in 12 minutes.").
3. **Given** a rate limit warning is displayed, **When** the rate limit resets and the next refresh succeeds, **Then** the warning indicator is automatically dismissed.
4. **Given** a refresh fails for a non-rate-limit reason (e.g., network error), **When** the failure occurs, **Then** a non-intrusive error indicator is displayed with an appropriate message (e.g., "Refresh failed. Will retry automatically.").

---

### User Story 4 - API Call Optimization and Caching (Priority: P3)

As a project board user, I want the system to minimize unnecessary GitHub API calls through caching, deduplication, and conditional requests so that I can use the project board throughout the day without exhausting my GitHub API rate limit.

**Why this priority**: This is a behind-the-scenes optimization that directly impacts the sustainability of using the project board over extended periods. While not user-facing in the traditional sense, it prevents rate limit exhaustion and improves performance. Ranked P3 because the board is functional without it, but long-term usability depends on it.

**Independent Test**: Can be tested by monitoring the number of API calls made during a series of refreshes and verifying that duplicate or redundant calls are eliminated, and that unchanged data is served from cache when possible.

**Acceptance Scenarios**:

1. **Given** the project board performs a refresh and the data has not changed since the last refresh, **When** the system makes requests to GitHub, **Then** it uses conditional requests so that unchanged data does not consume rate limit quota.
2. **Given** the project board makes multiple requests for the same data within a short time window (e.g., rapid manual refreshes), **When** subsequent requests are made, **Then** the system returns cached results instead of making duplicate API calls.
3. **Given** the project board needs data from multiple GitHub resources during a refresh, **When** the refresh is executed, **Then** the system batches or consolidates requests where possible to minimize the total number of API calls per refresh cycle.
4. **Given** the project board has previously fetched data, **When** a new refresh returns no new data (e.g., 304 Not Modified), **Then** the existing displayed data remains unchanged and no unnecessary re-renders occur.

---

### Edge Cases

- What happens when the user rapidly clicks the refresh button multiple times in quick succession? The system must deduplicate these into a single refresh operation.
- What happens when the auto-refresh fires at the exact moment the user clicks manual refresh? One of the operations must be suppressed to prevent duplicate API calls.
- What happens when the user's GitHub token expires or is revoked during an active session? The system should display an appropriate authentication error rather than a generic failure.
- What happens when the GitHub API returns a 500 or 503 error? The system should display a transient error message and retry on the next scheduled auto-refresh cycle.
- What happens when network connectivity is lost? The system should detect the failure, display an offline indicator, and resume auto-refresh when connectivity is restored.
- What happens when the project board is opened for the first time (cold start with no cached data)? The initial load should fetch all required data and establish the auto-refresh cycle.
- What happens when rate limit quota is nearly exhausted (e.g., fewer than 10 requests remaining)? The system should proactively reduce refresh frequency or warn the user before the limit is fully exhausted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a manual refresh button on the project board UI that is always visible and accessible when the board is displayed.
- **FR-002**: System MUST trigger an immediate full data reload from GitHub when the user clicks the manual refresh button.
- **FR-003**: System MUST display a tooltip on the refresh button indicating the automatic refresh frequency (e.g., "Auto-refreshes every 5 minutes").
- **FR-004**: System MUST display a visual loading indicator (e.g., spinner animation on the refresh button) while a refresh operation is in progress.
- **FR-005**: System MUST implement an automatic background refresh on a 5-minute interval when the project board is active and the browser tab is visible.
- **FR-006**: System MUST reset the auto-refresh countdown timer whenever a manual refresh is triggered, preventing redundant consecutive API calls.
- **FR-007**: System MUST prevent concurrent duplicate refresh operations — if a refresh is already in progress, additional refresh triggers must be ignored or queued.
- **FR-008**: System SHOULD pause or skip automatic refreshes when the browser tab or window is hidden, and resume the refresh cycle (with an immediate refresh if data is stale) when the tab becomes visible again.
- **FR-009**: System MUST display a non-intrusive warning indicator when a refresh fails due to GitHub API rate limits, including the approximate time until the rate limit resets when that information is available.
- **FR-010**: System MUST automatically dismiss the rate limit warning once a subsequent refresh succeeds.
- **FR-011**: System MUST display a non-intrusive error indicator when a refresh fails for non-rate-limit reasons (e.g., network errors, server errors), with an appropriate user-friendly message.
- **FR-012**: System MUST audit and eliminate any duplicate, redundant, or unnecessary GitHub API calls made during the project board's data loading and refresh operations.
- **FR-013**: System MUST implement request deduplication so that repeated requests for the same data within a short time window return cached results rather than making new API calls.
- **FR-014**: System SHOULD use conditional requests (using ETag/If-None-Match or If-Modified-Since headers) where supported by the GitHub API, so that requests for unchanged data do not count against the rate limit.
- **FR-015**: System SHOULD batch or consolidate GitHub API requests where possible to minimize the total number of HTTP requests per refresh cycle.
- **FR-016**: System SHOULD proactively reduce refresh frequency or warn the user when the remaining rate limit quota is critically low (e.g., fewer than 10 requests remaining).

### Key Entities

- **Refresh State**: Represents the current state of the refresh mechanism, including whether a refresh is in progress, the timestamp of the last successful refresh, and the auto-refresh countdown timer status.
- **Cache Entry**: Represents a cached API response, including the response data, the ETag or last-modified timestamp for conditional requests, and a time-to-live (TTL) for cache expiration.
- **Rate Limit Status**: Represents the current GitHub API rate limit state, including the total limit, remaining requests, and the timestamp when the limit resets.
- **Refresh Error**: Represents a failed refresh attempt, including the error type (rate limit, network, authentication, server error), the error message, and any associated metadata (e.g., rate limit reset time).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can trigger a manual data refresh and see updated board content within 5 seconds of clicking the refresh button under normal network conditions.
- **SC-002**: The project board automatically refreshes its data every 5 minutes without user intervention when the board is open and the browser tab is visible.
- **SC-003**: 100% of rate-limit-induced refresh failures display a visible warning to the user, including the approximate reset time when available.
- **SC-004**: The total number of GitHub API calls per refresh cycle is reduced by at least 50% compared to the current implementation through deduplication, caching, and request consolidation.
- **SC-005**: Automatic refreshes are paused within 1 second of the browser tab becoming hidden, and resumed within 1 second of the tab becoming visible again.
- **SC-006**: Rapid consecutive manual refresh clicks (e.g., 5 clicks within 1 second) result in at most 1 actual API refresh operation.
- **SC-007**: Users can use the project board for an 8-hour workday without encountering rate limit exhaustion under typical usage patterns (manual refresh no more than once per minute, auto-refresh every 5 minutes).
- **SC-008**: When data has not changed between refreshes, the system consumes zero or negligible rate limit quota by using conditional requests.

## Assumptions

- The project board already has an existing mechanism for fetching and displaying data from the GitHub API; this feature enhances that mechanism rather than building it from scratch.
- The 5-minute auto-refresh interval is appropriate for the expected data change frequency on project boards and provides a reasonable balance between freshness and API conservation.
- GitHub API rate limits follow the standard documented limits (5,000 requests/hour for authenticated users) and conditional requests (304 responses) do not count against the rate limit.
- Users interact with a single project board instance per browser tab; multiple simultaneous board views in different tabs each manage their own refresh cycles independently.
- The tooltip text ("Auto-refreshes every 5 minutes") is sufficient for communicating the auto-refresh behavior; no additional settings UI is needed to configure the refresh interval.
- Standard web browser APIs (Page Visibility API) are available in all supported browsers for detecting tab visibility changes.
