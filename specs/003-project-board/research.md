# Research: Standalone Project Board Page

**Feature**: 003-project-board | **Date**: 2026-02-16  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature adds a standalone Kanban-style project board page with real-time data from GitHub Projects V2 GraphQL API. Research covers GraphQL query design for board data (including linked PRs, assignees, and custom fields), frontend component architecture for the Kanban layout, auto-refresh strategy, and integration with the existing FastAPI backend and React frontend patterns.

## Decision Areas

### 1. GitHub Projects V2 GraphQL API Strategy

**Decision**: Extend the existing `github_projects_service` with new GraphQL queries that fetch full board data including custom fields (Priority, Size, Estimate), assignee details with avatars, and linked pull requests.

**Rationale**:
- The existing `github_projects_service` already handles authentication, rate limiting, and error handling for GitHub GraphQL API
- GitHub Projects V2 API uses `ProjectV2Item` nodes with `fieldValues` for custom fields (Single Select, Number, etc.)
- Linked PRs require a separate query on issue content nodes (`Issue.timelineItems` or `Issue.closingIssuesReferences`)
- Assignee avatars are available via `Issue.assignees` with `avatarUrl` field

**Alternatives Considered**:
- **REST API**: Rejected — GitHub Projects V2 is only available via GraphQL. REST API does not expose project board data.
- **New standalone service class**: Rejected — violates DRY. Existing service already manages GitHub GraphQL client, auth headers, rate limiting, and retry logic.
- **Client-side GraphQL (Apollo/urql)**: Rejected — would expose GitHub token to the browser. Current architecture proxies all GitHub API calls through the FastAPI backend for security.

**Implementation**: Add new methods to `github_projects_service`:
1. `list_board_projects()` — reuse existing `list_user_projects()` (already returns project ID, title, status columns)
2. `get_board_data(project_id)` — new query fetching all items with full field values, assignees, and content details
3. `get_linked_prs(content_ids)` — new query fetching linked PRs for a batch of issue content IDs

---

### 2. GraphQL Query Design for Board Data

**Decision**: Use a single comprehensive GraphQL query that fetches project items with all field values, assignee details, and repository info in one request, with pagination support for large projects.

**Rationale**:
- GitHub Projects V2 `items` connection supports pagination via `first`/`after` cursor
- Each item has `fieldValues` containing Status, Priority, Size, Estimate as `ProjectV2ItemFieldSingleSelectValue` or `ProjectV2ItemFieldNumberValue`
- Issue content (via `content { ... on Issue { } }`) provides title, number, repository, assignees, and state
- Single query reduces API calls and latency vs. N+1 per-item queries

**Alternatives Considered**:
- **Multiple small queries**: Rejected — would require N+1 calls (one per item for details). Inefficient and slower.
- **Fetch all fields generically**: Rejected — over-fetching. Query only the fields needed for the board display.

**Implementation**: GraphQL query structure:
```graphql
query GetBoardData($projectId: ID!, $first: Int!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: $first, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } }
              ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2Field { name } } }
              ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2Field { name } } }
            }
          }
          content {
            ... on Issue {
              number title state url body
              repository { name nameWithOwner }
              assignees(first: 10) { nodes { login avatarUrl } }
            }
            ... on DraftIssue { title body }
          }
        }
      }
    }
  }
}
```

---

### 3. Linked Pull Requests Strategy

**Decision**: Fetch linked PRs via `Issue.timelineItems` filtering for `CrossReferencedEvent` with pull request references, executed as a batched secondary query after the main board data query.

**Rationale**:
- GitHub's `timelineItems` with `CROSS_REFERENCED_EVENT` filter reliably captures PRs that reference the issue (via "Fixes #N", "Closes #N", or manual linking)
- Batching multiple issue IDs into a single query (using GraphQL aliases) reduces API calls
- Separating PR fetch from main board query keeps the primary query fast and the PR data optional/lazy

**Alternatives Considered**:
- **Include in main board query**: Rejected — significantly increases query complexity and size, may hit GraphQL query depth limits
- **REST API `/issues/{id}/timeline`**: Rejected — requires per-issue REST calls, much slower for boards with many issues
- **`closingIssuesReferences`**: This field works in the reverse direction (PR → issues it closes), not issue → linked PRs

**Implementation**: Secondary query using aliases:
```graphql
query GetLinkedPRs($issueId0: ID!, $issueId1: ID!, ...) {
  issue0: node(id: $issueId0) {
    ... on Issue {
      timelineItems(first: 5, itemTypes: [CROSS_REFERENCED_EVENT]) {
        nodes {
          ... on CrossReferencedEvent {
            source { ... on PullRequest { number title state url } }
          }
        }
      }
    }
  }
  ...
}
```

---

### 4. Frontend Routing Strategy

**Decision**: Use a simple state-based routing approach within the existing `App.tsx` component, adding a `currentPage` state that toggles between the chat view and the project board view, with URL hash-based navigation (`#/project-board`).

**Rationale**:
- The existing application does not use a routing library (no react-router)
- Adding a full routing library for a single new page is overkill (YAGNI)
- Hash-based navigation (`window.location.hash`) provides URL bookmarkability without requiring server-side routing configuration
- Simple state toggle matches the existing single-component architecture

**Alternatives Considered**:
- **react-router**: Rejected — adding a new dependency for a single additional route violates Simplicity principle. Would require refactoring the entire App.tsx structure.
- **Window location pathname**: Rejected — requires nginx/server-side routing config changes for SPA fallback on the new route
- **Separate HTML entry point**: Rejected — duplicates shared layout, auth, and query client setup

**Implementation**: Add `currentPage` state to `AppContent`, render `ProjectBoardPage` when `currentPage === 'project-board'`, add navigation link in sidebar/header.

---

### 5. Auto-Refresh Implementation

**Decision**: Use `@tanstack/react-query` with `refetchInterval` option for 15-second auto-refresh, with conditional pausing when the detail modal is open.

**Rationale**:
- `@tanstack/react-query` is already a project dependency and handles caching, refetching, loading/error states out of the box
- `refetchInterval` provides built-in polling with automatic cleanup on component unmount
- Setting `refetchInterval` to `false` when modal is open cleanly pauses refresh
- Background refetch preserves scroll position and current view state (stale-while-revalidate)

**Alternatives Considered**:
- **Custom `setInterval` + `useEffect`**: Rejected — reinvents what react-query already provides. Would require manual cache management, race condition handling, and cleanup.
- **WebSocket/Server-Sent Events**: Rejected — GitHub does not provide real-time push for project changes. Would still require polling the GitHub API on the backend.
- **Service Worker background sync**: Rejected — overkill for simple periodic refresh. Adds significant complexity.

**Implementation**: Custom hook `useProjectBoard`:
```typescript
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['project-board', projectId],
  queryFn: () => projectBoardApi.getBoardData(projectId),
  refetchInterval: isModalOpen ? false : 15000,
  staleTime: 10000,
});
```

---

### 6. Backend Endpoint Design

**Decision**: Add three new FastAPI endpoints under `/api/v1/project-board/` prefix: list projects, get board data by project ID, and get linked PRs for issue IDs.

**Rationale**:
- Separating project board endpoints from existing `/projects` endpoints maintains clean API boundaries (project board is a different view/use case)
- Three endpoints map directly to the three distinct data needs: project list, board items, and linked PRs
- Reuses existing session authentication (`get_session_dep`) and caching patterns
- Backend proxy pattern keeps GitHub token server-side (security)

**Alternatives Considered**:
- **Extend existing `/projects` endpoints**: Rejected — would bloat the existing API with board-specific fields and query parameters. Violates single responsibility.
- **Single mega-endpoint returning all data**: Rejected — monolithic response would be slow for large projects. Separate endpoints allow lazy loading of linked PRs.
- **GraphQL backend**: Rejected — adding a GraphQL layer to the backend is overkill for 3 endpoints. FastAPI REST is the established pattern.

**Implementation**:
1. `GET /api/v1/project-board/projects` — returns list of projects (can reuse existing service)
2. `GET /api/v1/project-board/{project_id}/board` — returns board data grouped by status
3. `POST /api/v1/project-board/linked-prs` — accepts list of content IDs, returns linked PRs

---

### 7. Component Architecture

**Decision**: Create 4 new React components in `frontend/src/components/project-board/`: `ProjectBoardPage`, `BoardColumn`, `BoardIssueCard`, `IssueDetailModal`.

**Rationale**:
- Component decomposition follows the visual hierarchy: Page → Columns → Cards → Modal
- Each component has a single responsibility matching the spec requirements
- Separate directory (`project-board/`) keeps board components isolated from existing sidebar/chat components
- Components are pure presentational where possible, with data fetching centralized in `useProjectBoard` hook

**Alternatives Considered**:
- **Single monolithic component**: Rejected — would be unmaintainable at 500+ lines. Violates component responsibility principle.
- **Reuse existing `TaskCard` component**: Rejected — `TaskCard` is designed for the sidebar task list with different data shape (no repo name, no linked PRs, no priority badges). Board issue cards have significantly different UI requirements.
- **Shared component library**: Rejected — premature abstraction. Board components have unique requirements. Can refactor later if patterns emerge.

**Implementation**:
- `ProjectBoardPage`: Page layout with project dropdown, board grid, loading/error states
- `BoardColumn`: Column header (status dot, name, count, estimate), scrollable card list
- `BoardIssueCard`: Card with repo name, title, assignee avatars, badges
- `IssueDetailModal`: Modal overlay with expanded details, GitHub link, close handlers

---

### 8. Styling Approach

**Decision**: Use CSS classes in the existing `App.css` file, following the established BEM-like naming convention and CSS custom properties (variables) for theming.

**Rationale**:
- The app uses plain CSS with custom properties for light/dark mode theming (`--color-bg-primary`, `--color-text-primary`, etc.)
- No CSS-in-JS or CSS modules are used in the project
- Adding board styles to `App.css` follows the existing pattern (all component styles are in one file)
- Color-coded badges (priority, size) use the existing semantic color variables

**Alternatives Considered**:
- **Tailwind CSS**: Not installed in the project. Adding it would be a significant dependency change.
- **CSS Modules**: Not used in the project. Would require build configuration changes.
- **Separate CSS file**: Could work but the project convention is single CSS file. Follow existing pattern.

**Implementation**: Add `.project-board-*` prefixed classes to `App.css` for all board components.

---

### 9. Status Column Color Mapping

**Decision**: Map GitHub Projects V2 status option colors to CSS classes using the existing `color` field from the project's status field options.

**Rationale**:
- GitHub Projects V2 returns status options with a `color` field (e.g., "GREEN", "YELLOW", "RED", "BLUE", "PURPLE", "PINK", "ORANGE", "GRAY")
- Map these to CSS custom properties or direct color values that match the app's design system
- Colored dots next to column headers provide visual distinction per spec requirement FR-004

**Alternatives Considered**:
- **Hardcoded color map**: Would work but breaks if GitHub adds new colors
- **Use GitHub's actual hex colors**: GitHub doesn't expose hex values, only color names
- **User-configurable colors**: Out of scope per spec

**Implementation**: CSS class map:
```css
.status-dot--GREEN { background-color: var(--color-success); }
.status-dot--YELLOW { background-color: var(--color-warning); }
.status-dot--RED { background-color: var(--color-danger); }
/* etc. */
```

---

### 10. Error Handling and Loading States

**Decision**: Use react-query's built-in `isLoading`, `isError`, `error`, and `isFetching` states for all loading and error UI, with a custom retry mechanism via `refetch()`.

**Rationale**:
- react-query already provides comprehensive loading/error state management
- `isLoading` (initial load) vs `isFetching` (background refetch) distinction allows showing skeleton on first load and subtle indicator on refresh
- `error` object provides error details for display
- `refetch()` enables the retry button in error states

**Alternatives Considered**:
- **Custom loading/error state management**: Rejected — reinvents react-query capabilities
- **Global error boundary**: Rejected — board errors should be contained within the board page, not crash the entire app
- **Toast notifications for errors**: Could supplement but spec requires inline error states with retry

**Implementation**: 
- Initial load: Full-page skeleton/spinner
- Background refresh: Subtle "Refreshing..." indicator in header
- Error state: Error message with retry button
- Network loss: Retain last data, show connectivity warning

---

## Implementation Risks

**Risk Level**: MODERATE

- **Technical Risk**: Medium — GitHub Projects V2 GraphQL API has complex query structure with nested fragments; query depth limits may require adjustments
- **Performance Risk**: Low-Medium — Large projects (100+ items) may require pagination; react-query caching mitigates repeated fetches
- **User Impact**: Positive — provides visual overview of project status currently unavailable in the app
- **Testing Risk**: Low — manual verification via browser is sufficient for UI components
- **Rollback Risk**: Low — new route and endpoints are additive; removing them has no impact on existing features

## Best Practices Applied

1. **DRY**: Reuse existing `github_projects_service` for GraphQL communication, auth, and rate limiting
2. **YAGNI**: No routing library added; simple state-based navigation for single new page
3. **Separation of Concerns**: Backend proxies API calls; frontend handles presentation
4. **Security**: GitHub token never exposed to browser; all API calls proxied through backend
5. **Progressive Enhancement**: Board works with basic data; linked PRs loaded lazily as secondary query

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved
- [x] Technology choices documented with rationale
- [x] Alternatives evaluated for key decisions
- [x] Implementation approach clear and justified
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered

**Status**: ✅ **PHASE 0 COMPLETE** - Ready for Phase 1 design artifacts
