# Feature Specification: Breadcrumb Deep Route Support

**Feature Branch**: `054-breadcrumb-deep-routes`  
**Created**: 2026-03-20  
**Status**: Draft  
**Input**: User description: "The Breadcrumb component matches the current pathname against the flat NAV_ROUTES array and always renders exactly two segments: 'Home' + the matched route label. At /apps/my-cool-app, it finds the apps route via pathname.startsWith(r.path) and shows Home > Apps — the :appName param is ignored. There's no mechanism for dynamic segments, route metadata, or depth beyond 2. The fix: make the breadcrumb parse all path segments, resolve params against route data, and support a useBreadcrumb context so pages can inject dynamic labels (e.g., the actual app name)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Full-Depth Breadcrumb Trail for Nested Routes (Priority: P1)

As a user navigating deep into the application, I want the breadcrumb to reflect every segment of the current URL path so that I always know where I am and can navigate back to any ancestor page in one click.

**Why this priority**: This is the core problem — the breadcrumb currently caps at two segments ("Home > Apps") regardless of depth. Fixing this delivers immediate navigational value across all pages and is a prerequisite for all other stories.

**Independent Test**: Can be fully tested by navigating to a multi-segment route (e.g., /apps/my-cool-app/settings) and verifying the breadcrumb renders all path segments as clickable links. Delivers clear wayfinding value.

**Acceptance Scenarios**:

1. **Given** a user is at the root path `/`, **When** the breadcrumb renders, **Then** only "Home" is displayed with no separator or additional segments.
2. **Given** a user navigates to `/apps`, **When** the breadcrumb renders, **Then** it shows "Home > Apps" where "Home" is a clickable link and "Apps" is the current (non-linked) segment.
3. **Given** a user navigates to `/apps/my-cool-app`, **When** the breadcrumb renders, **Then** it shows "Home > Apps > my-cool-app" with "Home" and "Apps" as clickable links and "my-cool-app" as the current segment.
4. **Given** a user navigates to `/apps/my-cool-app/settings`, **When** the breadcrumb renders, **Then** it shows "Home > Apps > my-cool-app > settings" with all ancestor segments as clickable links.
5. **Given** a user clicks on an ancestor breadcrumb segment, **When** the click is processed, **Then** the user is navigated to that segment's corresponding path.

---

### User Story 2 - Dynamic Labels via Breadcrumb Context (Priority: P1)

As a page owner, I want to programmatically set a human-readable label for the current breadcrumb segment so that users see meaningful names (e.g., "My Cool App") instead of raw URL slugs (e.g., "my-cool-app").

**Why this priority**: Without dynamic labels, deep breadcrumbs would show raw URL segments which are often unintelligible slugs, IDs, or parameterized tokens. This story makes the breadcrumb truly useful by allowing pages to inject the actual display name once data is loaded.

**Independent Test**: Can be fully tested by navigating to a page that uses the breadcrumb context to set a custom label and verifying the breadcrumb displays the friendly name instead of the URL slug.

**Acceptance Scenarios**:

1. **Given** a page sets a dynamic breadcrumb label for its path segment (e.g., replacing "my-cool-app" with "My Cool App"), **When** the breadcrumb renders, **Then** the overridden segment displays the dynamic label.
2. **Given** a page has not yet loaded its data (e.g., still fetching the app name), **When** the breadcrumb renders, **Then** the segment falls back to displaying the URL slug until the dynamic label is set.
3. **Given** a page sets a dynamic label and the user navigates away, **When** the user returns to the page, **Then** the breadcrumb re-renders with the dynamic label once the page re-sets it via context.
4. **Given** multiple nested pages each set their own dynamic labels, **When** the breadcrumb renders, **Then** each segment reflects its respective dynamic label independently.

---

### User Story 3 - Route-Aware Label Resolution (Priority: P2)

As a user, I want the breadcrumb to automatically resolve known route labels from the application's route configuration so that static routes display their proper titles without every page needing to manually set them.

**Why this priority**: This reduces boilerplate by automatically mapping well-known route paths (from the navigation or route configuration) to their human-readable labels. It ensures breadcrumbs are useful out of the box for static routes.

**Independent Test**: Can be fully tested by navigating to a static route (e.g., /apps or /settings) and verifying the breadcrumb resolves the correct label from route configuration without any page-level context override.

**Acceptance Scenarios**:

1. **Given** a route is defined in the application's route configuration with a label (e.g., path "/apps" has label "Apps"), **When** the breadcrumb renders for that path, **Then** the segment displays the configured label.
2. **Given** a route segment is not found in the route configuration and no dynamic label is set, **When** the breadcrumb renders, **Then** the segment displays the URL slug formatted in title case (e.g., "my-cool-app" becomes "My Cool App").
3. **Given** a route has both a configured label and a dynamic label set via context, **When** the breadcrumb renders, **Then** the dynamic label takes precedence over the configured label.

---

### User Story 4 - Breadcrumb Accessibility (Priority: P2)

As a user relying on assistive technology, I want the breadcrumb navigation to be fully accessible so that I can understand and navigate the page hierarchy using a screen reader or keyboard.

**Why this priority**: Accessibility is essential for all users. The breadcrumb must follow established accessibility patterns to be usable by everyone regardless of ability.

**Independent Test**: Can be fully tested by using a screen reader or keyboard navigation to traverse the breadcrumb and verifying proper landmark, role, and label announcements.

**Acceptance Scenarios**:

1. **Given** the breadcrumb is rendered on a page, **When** a screen reader encounters it, **Then** it is announced as a navigation landmark with an accessible label (e.g., "Breadcrumb").
2. **Given** a breadcrumb has multiple segments, **When** a user tabs through the breadcrumb, **Then** each clickable segment is focusable and the current (last) segment is identified as the current page.
3. **Given** a breadcrumb segment is the current page, **When** a screen reader reads it, **Then** it is announced as the current location (e.g., via aria-current="page").

### Edge Cases

- What happens when the URL contains consecutive slashes (e.g., `/apps//settings`)? The breadcrumb must ignore empty path segments and not render blank crumbs.
- What happens when the URL contains encoded characters (e.g., `/apps/my%20app`)? The breadcrumb must decode URL-encoded segments for display.
- What happens when a dynamic label is set for a segment that no longer exists in the current path? The orphaned label must be cleaned up and not affect the rendered breadcrumb.
- What happens at the root path `/`? Only "Home" should be displayed with no separator.
- What happens when the URL has a trailing slash (e.g., `/apps/my-cool-app/`)? The breadcrumb must treat it identically to the path without a trailing slash.
- What happens when a path segment is a long string? The breadcrumb should not break the page layout; overflow handling should be graceful.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The breadcrumb MUST parse the current URL pathname into individual path segments and render one breadcrumb item per segment, plus a leading "Home" segment.
- **FR-002**: Each breadcrumb segment except the last (current page) MUST be a clickable link that navigates the user to the corresponding ancestor path.
- **FR-003**: The last breadcrumb segment MUST represent the current page and MUST NOT be a link.
- **FR-004**: The system MUST provide a breadcrumb context that allows any page to set a custom display label for one or more path segments.
- **FR-005**: Dynamic labels set via the breadcrumb context MUST take precedence over route-configured labels and URL slug fallbacks.
- **FR-006**: The system MUST resolve breadcrumb labels from the application's existing route configuration for known static routes.
- **FR-007**: When no label is available from the route configuration or breadcrumb context, the system MUST fall back to displaying the URL slug formatted in title case (e.g., "my-cool-app" → "My Cool App").
- **FR-008**: The breadcrumb MUST ignore empty path segments caused by trailing slashes or consecutive slashes.
- **FR-009**: The breadcrumb MUST decode URL-encoded characters in path segments for display purposes.
- **FR-010**: Dynamic labels MUST be cleaned up when the component that set them unmounts, preventing stale labels from persisting.
- **FR-011**: The breadcrumb navigation MUST include appropriate accessibility attributes: a navigation landmark with an accessible name, and the current page segment marked with aria-current="page".
- **FR-012**: The breadcrumb MUST support routes of arbitrary depth (3, 4, 5+ segments) without a hard-coded segment limit.

### Key Entities

- **Breadcrumb Segment**: Represents a single item in the breadcrumb trail. Attributes: path (the URL path up to and including this segment), label (the display text), isCurrentPage (whether this is the last segment), link (the navigation target URL).
- **Breadcrumb Context**: A shared context that holds a mapping of path segments to custom display labels. Pages can register and unregister labels. The context notifies the breadcrumb component when labels change.
- **Route Configuration**: The existing application route definitions that include path patterns and human-readable labels. Used as a lookup source for resolving breadcrumb segment labels.

## Assumptions

- The application uses client-side routing, so the breadcrumb reads the current pathname from the router.
- The existing NAV_ROUTES or equivalent route configuration array is available and can be referenced for label resolution.
- "Home" is always the first breadcrumb segment, linking to the root path `/`.
- Path segments are separated by `/` and are non-hierarchical tokens (no query strings or hash fragments affect the breadcrumb).
- Title-casing the slug means capitalizing the first letter of each word and replacing hyphens/underscores with spaces (e.g., "my-cool-app" → "My Cool App").

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Breadcrumbs correctly render all path segments for routes with 3 or more levels of nesting, verified across all existing application routes.
- **SC-002**: Pages that set dynamic labels via the breadcrumb context see the correct label displayed within the same render cycle (no flicker beyond initial data load).
- **SC-003**: 100% of existing static routes resolve their labels from route configuration without requiring page-level overrides.
- **SC-004**: All breadcrumb links navigate to the correct ancestor path when clicked — zero navigation errors across tested routes.
- **SC-005**: The breadcrumb passes accessibility audits for navigation landmarks, focusable links, and aria-current="page" on the current segment.
- **SC-006**: Users can identify their current location in the application within 2 seconds of page load by reading the breadcrumb trail.
