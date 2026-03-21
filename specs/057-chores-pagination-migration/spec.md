# Feature Specification: ChoresPanel Pagination Migration

**Feature Branch**: `057-chores-pagination-migration`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "ChoresPanel Pagination Migration — migrate ChoresPanel from client-side filtering to server-side filtering with cursor-based infinite scroll pagination"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Paginated Chores Loading (Priority: P1)

As a user with a large number of chores in a project, I want the ChoresPanel to load chores incrementally so that the initial page load is fast and I can scroll to see more chores on demand, matching the experience I already have in Agents, Tools, Apps, Activity, and Board panels.

**Why this priority**: This is the core behavioral change. Without paginated loading, the ChoresPanel fetches all chores at once, which degrades performance for projects with many chores. Every other panel already uses infinite scroll — this closes the last gap and delivers the primary performance benefit.

**Independent Test**: Can be fully tested by creating a project with 50+ chores, opening the ChoresPanel, and verifying that only 25 chores load initially with a scroll indicator showing more are available.

**Acceptance Scenarios**:

1. **Given** a project with 60 chores and no active filters, **When** the user opens the ChoresPanel, **Then** only the first 25 chores are displayed, and a visual indicator shows that more chores are available by scrolling.
2. **Given** the initial 25 chores are displayed, **When** the user scrolls to the bottom of the list, **Then** the next batch of 25 chores loads automatically and appends to the list.
3. **Given** the user has scrolled to load 50 chores, **When** they scroll further, **Then** the remaining 10 chores load and no further loading indicator is shown.
4. **Given** a project with fewer than 25 chores, **When** the user opens the ChoresPanel, **Then** all chores are displayed and no scroll-to-load indicator is shown.

---

### User Story 2 - Server-Side Filtering (Priority: P1)

As a user browsing my chores, I want to filter by status, schedule type, and search text so that I see only the chores that match my criteria — and the filter applies across all chores, not just the ones currently loaded on screen.

**Why this priority**: This is equally critical to pagination because client-side filtering on paginated data would only filter the loaded pages, missing matching items on later pages. Users would see incomplete or misleading results. Server-side filtering is a prerequisite for pagination to be useful with filters.

**Independent Test**: Can be fully tested by creating 50+ chores with varying statuses and schedule types, applying a status filter, and verifying that all matching chores across all pages are returned — not just those from the first loaded page.

**Acceptance Scenarios**:

1. **Given** a project with 60 chores (30 active, 30 completed), **When** the user filters by "active" status, **Then** only active chores are returned from the server, paginated in batches of 25, and no completed chores appear regardless of scrolling.
2. **Given** a project with chores of different schedule types, **When** the user filters by a specific schedule type, **Then** only chores matching that schedule type are displayed.
3. **Given** a project with many chores, **When** the user types a search term, **Then** only chores whose name or description match the search term are returned from the server.
4. **Given** an active filter is applied, **When** the user scrolls to load more results, **Then** subsequent pages also respect the active filter — only matching chores are loaded.

---

### User Story 3 - Server-Side Sorting (Priority: P2)

As a user viewing my chores list, I want to sort chores by different criteria (e.g., name, creation date) and have the sort applied consistently across the entire dataset, so that the ordering is meaningful even when not all chores are loaded.

**Why this priority**: Sorting partial (paginated) data client-side produces meaningless results — the user would see sorted results only within each loaded page, not across the full dataset. Server-side sorting is necessary for pagination to produce a coherent, predictable list order.

**Independent Test**: Can be fully tested by creating 50+ chores, applying a sort order, and verifying that the first 25 chores displayed are correctly ordered and that subsequently loaded pages continue the correct global sort order.

**Acceptance Scenarios**:

1. **Given** a project with 50+ chores, **When** the user selects a sort criterion and sort direction, **Then** chores are returned in the correct global order from the server, and scrolling loads subsequent pages in the same consistent order.
2. **Given** the user changes the sort order while viewing chores, **When** the new sort is applied, **Then** the list resets to page 1 and re-fetches chores in the new order from the server.

---

### User Story 4 - Filter and Sort State Reset on Change (Priority: P2)

As a user who changes filters or sort options while browsing chores, I want the list to automatically reset to the beginning so that I always see results from page 1 with my new criteria applied, without stale data from a previous filter/sort combination.

**Why this priority**: Without resetting pagination when filters change, users could see stale data, empty states, or confusing mixed results from two different query sets. This is essential for a coherent user experience.

**Independent Test**: Can be fully tested by loading chores with a filter, scrolling to page 3, then changing the filter, and verifying the list resets to page 1 with fresh results.

**Acceptance Scenarios**:

1. **Given** the user has scrolled and loaded 3 pages of chores with a status filter of "active", **When** the user changes the status filter to "completed", **Then** the list resets, the scroll position returns to the top, and the first page of "completed" chores loads from the server.
2. **Given** the user has loaded chores sorted ascending, **When** the user changes sort to descending, **Then** the list resets to page 1 and re-fetches in the new order.
3. **Given** the user types a new search term, **When** the debounced search value updates, **Then** pagination resets and fresh results matching the new search term load from page 1.

---

### User Story 5 - Cleanup of Non-Paginated Code Paths (Priority: P3)

As a maintainer of the codebase, I want unused non-paginated chore fetching code to be removed so that the codebase stays clean and there is a single, consistent approach to loading chores.

**Why this priority**: This is a cleanup step that reduces code complexity and prevents future confusion about which hook or function to use. It depends on the paginated path being fully wired up first.

**Independent Test**: Can be fully tested by searching the codebase for references to the non-paginated chore listing functions and verifying they are no longer imported or called anywhere.

**Acceptance Scenarios**:

1. **Given** the paginated chores hook is fully wired up in ChoresPanel, **When** a codebase search is performed for the non-paginated list hook and list function, **Then** they are either removed entirely (if unused elsewhere) or documented as deprecated with a migration note.

---

### Edge Cases

- What happens when the user scrolls rapidly past multiple page boundaries? The system must handle concurrent fetch requests gracefully without duplicate or out-of-order results.
- What happens when a filter returns zero results? The user must see an appropriate empty state message, not a loading spinner.
- What happens when the user types a search query very quickly? Search input must be debounced (existing behavior via useDeferredValue) so that rapid keystrokes do not trigger excessive server requests.
- What happens when the server is slow or returns an error during a page fetch? The user must see an appropriate loading state during fetch and an error message if the request fails, with the ability to retry.
- What happens when chores are added or deleted while the user is browsing paginated results? The cursor-based pagination must handle this gracefully (consistent with how other panels handle it).
- What happens when filters are combined (e.g., status + schedule type + search)? All filters must be applied together on the server, and the results must be the intersection of all active filters.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The chores listing endpoint MUST accept optional query parameters for filtering: status, schedule type, and search text.
- **FR-002**: The chores listing endpoint MUST accept optional query parameters for sorting: sort field and sort direction (ascending/descending).
- **FR-003**: The server MUST apply all filter and sort parameters before pagination, so that paginated results reflect the filtered and sorted dataset.
- **FR-004**: The ChoresPanel MUST load chores in pages of 25 items, consistent with all other paginated panels in the application.
- **FR-005**: The ChoresPanel MUST use cursor-based infinite scroll for loading additional pages, matching the existing pattern used by Agents, Tools, Apps, Activity, and Board panels.
- **FR-006**: When the user changes any filter or sort parameter, the system MUST reset pagination to page 1 and fetch fresh results from the server.
- **FR-007**: The ChoresPanel MUST pass pagination state (has more pages, is loading next page, fetch next page) to the ChoresGrid component for rendering the infinite scroll experience.
- **FR-008**: Client-side filter and sort logic in ChoresPanel MUST be removed, since filtering and sorting are now handled server-side.
- **FR-009**: Search text filtering MUST continue to use debouncing (existing useDeferredValue behavior) to avoid excessive server requests during rapid typing.
- **FR-010**: When multiple filters are active simultaneously, the server MUST return results matching the intersection of all active filter criteria.
- **FR-011**: If the non-paginated chores list hook and its corresponding function are not used elsewhere in the codebase, they MUST be removed as part of cleanup.
- **FR-012**: All filter parameters MUST be included in the query cache key so that changing a filter triggers a fresh fetch rather than returning stale cached data.

### Key Entities

- **Chore**: A scheduled task within a project. Key attributes: name, description, status (e.g., active, completed), schedule type (e.g., daily, weekly, one-time), creation date, project association.
- **Project**: A container for chores. Each chore belongs to exactly one project. Chores are listed per project.
- **Pagination Cursor**: An opaque token representing the current position in the paginated result set. Used to fetch the next page of results.

### Assumptions

- The default page size of 25 items is consistent with all other paginated panels and does not need to be configurable by the user.
- The existing ChoresGrid component already supports pagination props (hasNextPage, isFetchingNextPage, fetchNextPage) and InfiniteScrollContainer — no changes are needed to ChoresGrid.
- The existing useDeferredValue for search debouncing is sufficient and does not need to be replaced with a different debouncing mechanism.
- The chores listing endpoint already supports cursor-based pagination via an apply_pagination() function — only filtering and sorting parameters need to be added before that call.
- Filter and sort parameter names and accepted values will follow conventions already established by similar endpoints in the application.
- The non-paginated chores list hook may still be referenced elsewhere; if so, it should be retained and documented rather than removed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ChoresPanel initial load displays no more than 25 chores, reducing initial data transfer for projects with large chore counts.
- **SC-002**: Users can scroll to load additional chores in batches of 25, with each batch loading within 2 seconds under normal conditions.
- **SC-003**: Applying a filter (status, schedule type, or search) returns correct results across the entire chore dataset, not just the currently loaded pages.
- **SC-004**: Changing any filter or sort parameter resets the list to the first page within 1 second, with no stale results from the previous query visible.
- **SC-005**: Rapid filter toggling or search typing does not cause errors, duplicate results, or race conditions — the UI remains responsive and eventually consistent.
- **SC-006**: The ChoresPanel pagination experience is visually and behaviorally consistent with the existing paginated panels (Agents, Tools, Apps, Activity, Board).
- **SC-007**: All automated tests for chores filtering with pagination pass, including tests for individual filters, combined filters, and cursor behavior with active filters.
- **SC-008**: The codebase has a single, consistent approach to loading chores — no duplicate or conflicting code paths remain (unless explicitly retained for backward compatibility).
