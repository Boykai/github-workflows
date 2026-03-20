# Feature Specification: Breadcrumb Deep Route Support

**Feature Branch**: `054-breadcrumb-deep-routes`  
**Created**: 2026-03-20  
**Status**: Draft  
**Input**: User description: "Breadcrumb Doesn't Handle Deep Routes — The Breadcrumb component matches the current pathname against the flat NAV_ROUTES array and always renders exactly two segments: 'Home' + the matched route label. At /apps/my-cool-app, it finds the apps route via pathname.startsWith(r.path) and shows Home > Apps — the :appName param is ignored. There's no mechanism for dynamic segments, route metadata, or depth beyond 2. The fix: make the breadcrumb parse all path segments, resolve params against route data, and support a useBreadcrumb context so pages can inject dynamic labels (e.g., the actual app name)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Full-Depth Breadcrumb Trail for Nested Routes (Priority: P1)

A user navigates to a deeply nested page such as `/apps/my-cool-app` or `/agents/code-reviewer/settings`. Today, the breadcrumb only shows two segments (e.g., "Home > Apps") regardless of how deep the URL is. The user sees no indication of which specific app or sub-page they are viewing. With this feature, the breadcrumb parses every segment of the URL path and renders a complete trail — e.g., "Home > Apps > My Cool App" or "Home > Agents > Code Reviewer > Settings" — giving the user a clear sense of where they are in the application hierarchy.

**Why this priority**: The breadcrumb is a fundamental wayfinding element. Without depth awareness, users navigating deep routes lose spatial context, cannot trace their location, and must rely on the browser's back button or sidebar navigation. This is the core deficiency described in the issue.

**Independent Test**: Can be fully tested by navigating to any route with 3+ path segments and verifying that the breadcrumb displays a segment for each level of the path hierarchy, with each ancestor segment being a clickable link.

**Acceptance Scenarios**:

1. **Given** the user is on the route `/apps`, **When** they view the breadcrumb, **Then** it displays "Home > Apps" (two segments, same as today for top-level routes).
2. **Given** the user is on the route `/apps/my-cool-app`, **When** they view the breadcrumb, **Then** it displays "Home > Apps > my-cool-app" (three segments), where "Home" links to `/`, "Apps" links to `/apps`, and the last segment is not a link.
3. **Given** the user is on the route `/agents/code-reviewer/settings`, **When** they view the breadcrumb, **Then** it displays "Home > Agents > code-reviewer > Settings" (four segments), with each ancestor segment linking to its respective path.
4. **Given** the user is on a top-level route like `/tools`, **When** they view the breadcrumb, **Then** it displays "Home > Tools" (existing behavior is preserved).
5. **Given** the user clicks an ancestor breadcrumb segment (e.g., "Apps" while on `/apps/my-cool-app`), **When** the navigation completes, **Then** the user is taken to that ancestor route (`/apps`) and the breadcrumb updates to reflect the new location.

---

### User Story 2 — Dynamic Labels via Breadcrumb Context (Priority: P1)

A user navigates to `/apps/my-cool-app`. The breadcrumb currently shows a raw path segment like "my-cool-app" because there is no way for a page to tell the breadcrumb what human-readable label to use. With this feature, individual pages can inject dynamic, user-friendly labels into the breadcrumb. For example, the app detail page can set the breadcrumb label for its segment to the actual app name ("My Cool App" instead of "my-cool-app"). This works through a breadcrumb context that pages can update when their data loads.

**Why this priority**: Without dynamic labels, breadcrumbs display raw URL slugs or parameter values, which are often unfriendly (e.g., UUIDs, kebab-case slugs). Dynamic labels are essential for the breadcrumb to serve its purpose as a human-readable navigation aid.

**Independent Test**: Can be fully tested by navigating to a page that resolves a dynamic parameter (e.g., an app detail page), verifying the breadcrumb initially shows the raw segment, and then — once the page data loads and injects a label — the breadcrumb updates to display the friendly name.

**Acceptance Scenarios**:

1. **Given** the user navigates to `/apps/my-cool-app` and the page loads the app with display name "My Cool App", **When** the page injects the label via the breadcrumb context, **Then** the breadcrumb updates from "Home > Apps > my-cool-app" to "Home > Apps > My Cool App".
2. **Given** a page sets a dynamic breadcrumb label for its path segment, **When** the user navigates away from that page, **Then** the injected label is cleaned up and does not persist in the breadcrumb for unrelated routes.
3. **Given** the user navigates to `/agents/abc123` where `abc123` is an agent ID, **When** the agent detail page loads and injects the label "Code Reviewer", **Then** the breadcrumb displays "Home > Agents > Code Reviewer" instead of "Home > Agents > abc123".
4. **Given** the page data is still loading, **When** the user views the breadcrumb, **Then** the breadcrumb displays the raw path segment as a fallback until the dynamic label is injected.

---

### User Story 3 — Route Metadata Labels for Known Routes (Priority: P2)

Some routes have well-known labels defined in the navigation configuration (e.g., `/apps` → "Apps", `/tools` → "Tools", `/agents` → "Agents"). When the breadcrumb encounters a path segment that matches a known route, it should use the configured label rather than just title-casing the segment. This ensures consistent naming between the sidebar navigation and the breadcrumb trail.

**Why this priority**: Using route metadata for known segments provides immediate value without requiring individual pages to inject labels. It covers the majority of static routes and ensures consistency between the breadcrumb and the sidebar or top-level navigation.

**Independent Test**: Can be fully tested by navigating to any route whose path matches a known route in the navigation configuration, and verifying the breadcrumb uses the configured label (e.g., "Apps" not "apps").

**Acceptance Scenarios**:

1. **Given** the navigation configuration defines the route `/apps` with the label "Apps", **When** the user visits `/apps/some-app`, **Then** the breadcrumb segment for `/apps` displays "Apps" (from route metadata) rather than "apps" (from the raw path).
2. **Given** a path segment does not match any known route label, **When** the breadcrumb renders that segment, **Then** it falls back to title-casing the raw segment (e.g., "my-cool-app" → "My Cool App").
3. **Given** a route is renamed in the navigation configuration (e.g., "Apps" changed to "Applications"), **When** the breadcrumb renders that route, **Then** it automatically uses the updated label without any additional changes.

---

### User Story 4 — Accessible Breadcrumb Navigation (Priority: P2)

A user who relies on assistive technology (screen reader, keyboard navigation) navigates the application. The breadcrumb trail must be accessible: it should be wrapped in a semantic navigation landmark, use proper list structure, indicate the current page to screen readers, and support keyboard navigation between breadcrumb links.

**Why this priority**: Accessibility is a core quality requirement. As the breadcrumb gains depth and dynamic labels, ensuring it remains accessible prevents regressions and keeps the application usable for all users.

**Independent Test**: Can be fully tested by navigating to a deep route, using a screen reader to read the breadcrumb, and verifying that it announces the navigation landmark, each breadcrumb item, and the current page indicator.

**Acceptance Scenarios**:

1. **Given** the user is on a deep route, **When** a screen reader reads the breadcrumb, **Then** it identifies the breadcrumb as a navigation landmark (e.g., "breadcrumb navigation") and reads each segment in order.
2. **Given** the breadcrumb has multiple segments, **When** the user navigates via keyboard (Tab key), **Then** each clickable breadcrumb segment receives focus in order, and the current (last) segment is identified as the current page.
3. **Given** the breadcrumb renders a separator between segments, **When** a screen reader reads the breadcrumb, **Then** the separators are not announced as content (they are purely decorative).

---

### Edge Cases

- What happens when the URL contains a trailing slash (e.g., `/apps/my-cool-app/`)? The breadcrumb should produce the same trail as without the trailing slash and should not render an empty trailing segment.
- What happens when a path segment is a UUID or other opaque identifier (e.g., `/agents/550e8400-e29b-41d4-a716-446655440000`)? The breadcrumb should display the raw segment as a fallback and allow the page to inject a friendly label via context.
- What happens when the URL contains encoded characters (e.g., `/apps/my%20cool%20app`)? The breadcrumb should decode the segment for display (showing "my cool app" rather than "my%20cool%20app").
- What happens when the user navigates to a route that does not match any known route (e.g., a 404 page)? The breadcrumb should still parse all segments and display them, with the last segment shown as the current location.
- What happens when multiple pages attempt to set dynamic labels for the same path segment? The most recently set label should take precedence, and cleanup on unmount should restore the previous label or fall back to the default.
- What happens when a dynamic label is set and then the data fetch fails on retry? The breadcrumb should continue displaying whatever label was last set (or the raw fallback), without crashing or showing an error state in the breadcrumb itself.

## Requirements *(mandatory)*

### Functional Requirements

#### Path Segment Parsing

- **FR-001**: System MUST parse the current URL pathname into individual path segments and render one breadcrumb item per segment, plus a leading "Home" segment linking to the root path.
- **FR-002**: System MUST ignore trailing slashes in the URL so that `/apps/my-cool-app` and `/apps/my-cool-app/` produce identical breadcrumb trails.
- **FR-003**: System MUST decode URL-encoded characters in path segments for display purposes (e.g., `%20` displayed as a space).

#### Breadcrumb Segment Links

- **FR-004**: Each breadcrumb segment except the last (current page) MUST be a clickable link that navigates to the corresponding ancestor path.
- **FR-005**: The last breadcrumb segment MUST represent the current page and MUST NOT be a clickable link.
- **FR-006**: System MUST render a visual separator (e.g., ">", "/", or a chevron icon) between each breadcrumb segment.

#### Route Metadata Resolution

- **FR-007**: System MUST resolve breadcrumb labels for path segments that match known routes in the navigation configuration, using the configured label (e.g., "Apps" for `/apps`).
- **FR-008**: When a path segment does not match any known route label and no dynamic label has been injected, the system MUST fall back to a human-readable transformation of the raw segment (e.g., converting "my-cool-app" to "My Cool App" via title-casing and replacing hyphens with spaces).

#### Dynamic Label Context

- **FR-009**: System MUST provide a breadcrumb context that allows individual pages to inject custom labels for specific path segments at runtime.
- **FR-010**: When a page injects a dynamic label for a path segment, the breadcrumb MUST update to display that label in place of the default label for that segment.
- **FR-011**: When the page that injected a dynamic label unmounts or the user navigates away, the system MUST clean up the injected label so it does not persist for unrelated routes.
- **FR-012**: System MUST support displaying a fallback label (raw segment or title-cased segment) while the dynamic label is loading, and update seamlessly once the label is available.

#### Accessibility

- **FR-013**: The breadcrumb MUST be wrapped in a semantic navigation landmark with an accessible label (e.g., "Breadcrumb").
- **FR-014**: Breadcrumb segments MUST be rendered as an ordered list to convey hierarchy to assistive technologies.
- **FR-015**: The current page segment MUST be identified with an appropriate attribute so screen readers announce it as the current location.
- **FR-016**: Visual separators between breadcrumb segments MUST be hidden from screen readers (decorative only).

### Key Entities

- **Breadcrumb Segment**: A single item in the breadcrumb trail, consisting of a label (display text), a path (the URL it links to), and a flag indicating whether it is the current page.
- **Breadcrumb Context**: A shared data store that holds a mapping of path segments to custom labels, allowing pages to inject and clean up dynamic labels at runtime.
- **Route Metadata**: The set of known route definitions (path and label pairs) used to resolve human-readable labels for static path segments.

## Assumptions

- The existing "Home" segment at the beginning of the breadcrumb trail will be preserved. "Home" always links to the root path (`/`).
- The navigation configuration (e.g., `NAV_ROUTES`) already contains route-to-label mappings for all top-level routes. No new route definitions need to be created for this feature.
- Dynamic labels are the responsibility of individual pages — each page that displays a detail view for a dynamic segment (e.g., app detail, agent detail) is expected to use the breadcrumb context to inject an appropriate label.
- The breadcrumb does not need to support routes deeper than 5 segments for the initial release. Most application routes are 2–4 segments deep.
- Performance impact of breadcrumb context updates is negligible since breadcrumb state changes are infrequent (only on navigation or data load events).
- The visual separator style (chevron, slash, etc.) will follow the existing design system and does not need to be configurable by end users.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Breadcrumb displays the correct number of segments matching the depth of the current URL path on 100% of routes with 2 or more segments.
- **SC-002**: Users can identify their current location in the application hierarchy within 2 seconds of page load by reading the breadcrumb trail.
- **SC-003**: 100% of clickable breadcrumb segments navigate to the correct ancestor route when clicked.
- **SC-004**: Dynamic labels injected via the breadcrumb context appear in the breadcrumb within 1 second of being set by the page.
- **SC-005**: Zero stale or orphaned dynamic labels persist in the breadcrumb after navigating away from the page that set them.
- **SC-006**: Screen reader users can identify the breadcrumb as a navigation landmark, read each segment in order, and determine the current page with no ambiguity.
- **SC-007**: Existing breadcrumb behavior for top-level routes (2-segment trails) is preserved with no regressions.
