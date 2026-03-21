# Feature Specification: Breadcrumb Deep Route Support

**Feature Branch**: `055-breadcrumb-deep-routes`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "Breadcrumb Doesn't Handle Deep Routes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Segment Breadcrumb Trail (Priority: P1)

As a user navigating into a deeply nested page (e.g., `/apps/my-cool-app`), I see a breadcrumb trail that reflects every segment of the current path, not just "Home > Apps." The breadcrumb should render "Home > Apps > My Cool App" so I always know exactly where I am and can navigate back to any ancestor page with a single click.

**Why this priority**: This is the core defect. Without multi-segment breadcrumb rendering, users lose spatial awareness in the application hierarchy and cannot navigate efficiently. Every other improvement depends on this foundational change.

**Independent Test**: Navigate to any route deeper than one segment (e.g., `/apps/my-cool-app`) and verify the breadcrumb renders all intermediate segments as clickable links, with the final segment displayed as plain text.

**Acceptance Scenarios**:

1. **Given** the user is on the page `/apps/my-cool-app`, **When** the breadcrumb renders, **Then** it displays "Home > Apps > My Cool App" with "Home" and "Apps" as clickable links and "My Cool App" as non-clickable text.
2. **Given** the user is on a top-level route like `/apps`, **When** the breadcrumb renders, **Then** it displays "Home > Apps" (existing two-segment behavior is preserved).
3. **Given** the user is on the home page `/`, **When** the breadcrumb renders, **Then** it displays only "Home" with no separator or additional segments.
4. **Given** the breadcrumb displays "Home > Apps > My Cool App", **When** the user clicks "Apps", **Then** they are navigated to `/apps`.

---

### User Story 2 - Dynamic Labels via Breadcrumb Context (Priority: P1)

As a page component rendering a detail view (e.g., an individual app page), I can set a human-readable breadcrumb label for my route segment so that the breadcrumb shows the entity's real name (e.g., "My Cool App") instead of a raw URL slug or parameter value (e.g., "my-cool-app").

**Why this priority**: Without dynamic labels, deep breadcrumbs would show raw URL slugs or parameter IDs, which are meaningless to users. This is essential for the breadcrumb to be useful at depth.

**Independent Test**: Navigate to a detail page whose component sets a breadcrumb label via the context. Verify the breadcrumb displays the human-readable label rather than the raw URL segment.

**Acceptance Scenarios**:

1. **Given** a detail page component calls the breadcrumb context to set the label "My Cool App" for path segment `:appName`, **When** the breadcrumb renders at `/apps/my-cool-app`, **Then** it displays "Home > Apps > My Cool App" using the provided label.
2. **Given** a detail page component has not set a breadcrumb label for a dynamic segment, **When** the breadcrumb renders, **Then** it falls back to a title-cased version of the raw URL segment (e.g., "my-cool-app" becomes "My Cool App").
3. **Given** a detail page component updates its breadcrumb label after initial render (e.g., after an API response returns the entity name), **When** the label changes, **Then** the breadcrumb updates to reflect the new label without a full page reload.

---

### User Story 3 - Breadcrumb for Three-or-More-Level Routes (Priority: P2)

As a user navigating to a deeply nested page with three or more path segments (e.g., `/apps/my-cool-app/settings`), I see a full breadcrumb trail such as "Home > Apps > My Cool App > Settings" so that I can navigate back to any level of the hierarchy.

**Why this priority**: Extends the core two-plus-segment breadcrumb to arbitrary depth, handling real-world navigation patterns where settings, sub-pages, or related resources are nested under detail views.

**Independent Test**: Navigate to a route with three or more segments and verify all intermediate segments appear as clickable links in the correct order.

**Acceptance Scenarios**:

1. **Given** the user is on `/apps/my-cool-app/settings`, **When** the breadcrumb renders, **Then** it displays "Home > Apps > My Cool App > Settings" with all segments except the last as clickable links.
2. **Given** the user is on `/apps/my-cool-app/settings/notifications`, **When** the breadcrumb renders, **Then** it displays four segments plus Home, all correctly linked to their respective paths.

---

### User Story 4 - Static Route Label Resolution (Priority: P2)

As a user navigating to a known static route (e.g., `/apps`, `/settings`, `/tools`), the breadcrumb uses the human-readable label defined in the application's route configuration rather than a raw title-cased slug, so that labels are consistent with the navigation menu.

**Why this priority**: Ensures breadcrumb labels for known routes match the sidebar/navigation labels, providing a consistent user experience.

**Independent Test**: Navigate to a static route that has a label defined in the route configuration and verify the breadcrumb uses that label.

**Acceptance Scenarios**:

1. **Given** a route `/apps` has the label "Apps" defined in the route configuration, **When** the user navigates to `/apps`, **Then** the breadcrumb displays "Home > Apps" using the configured label.
2. **Given** a path segment does not match any known route in the route configuration, **When** the breadcrumb renders, **Then** it falls back to title-casing the URL segment.

---

### Edge Cases

- What happens when a breadcrumb segment's path does not correspond to a navigable page (e.g., an intermediate grouping path that has no page)? The segment should still appear in the breadcrumb but as non-clickable text.
- What happens when the URL contains query parameters or hash fragments? Breadcrumb generation should use only the pathname, ignoring query strings and hash fragments.
- What happens when multiple components on the same page try to set breadcrumb labels? The last label set for a given path segment should take precedence.
- What happens when the user navigates away from a page that set a dynamic label? The label should be cleaned up from the context so it does not leak into unrelated routes.
- What happens when the URL has trailing slashes (e.g., `/apps/` vs `/apps`)? Both should produce the same breadcrumb output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The breadcrumb component MUST parse the current URL pathname into individual path segments and render a breadcrumb item for each segment, preceded by "Home."
- **FR-002**: The breadcrumb component MUST render all segments except the final one as clickable links that navigate to the corresponding cumulative path.
- **FR-003**: The breadcrumb component MUST render the final segment as non-clickable text (current page indicator).
- **FR-004**: The system MUST provide a breadcrumb context that allows any page component to register a human-readable label for a specific path segment.
- **FR-005**: When a dynamic label is registered via the breadcrumb context for a path segment, the breadcrumb MUST display that label instead of the raw URL segment.
- **FR-006**: When no dynamic label is registered and the segment matches a known route in the route configuration, the breadcrumb MUST use the route's configured label.
- **FR-007**: When no dynamic label is registered and the segment does not match a known route, the breadcrumb MUST fall back to a title-cased version of the URL segment (replacing hyphens and underscores with spaces).
- **FR-008**: Dynamic breadcrumb labels MUST be cleaned up from the context when the component that registered them unmounts, preventing label leakage across routes.
- **FR-009**: The breadcrumb MUST support arbitrary depth — any number of path segments must be handled without a hard-coded limit.
- **FR-010**: The breadcrumb component MUST ignore query parameters and hash fragments when generating segments.
- **FR-011**: The breadcrumb component MUST normalize trailing slashes so that `/apps/` and `/apps` produce identical breadcrumb output.
- **FR-012**: The breadcrumb MUST update dynamically when the route changes (single-page application navigation) without requiring a full page reload.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users navigating to any page at depth 2 or greater see a complete breadcrumb trail reflecting every path segment, verified across all application routes.
- **SC-002**: 100% of detail/entity pages display human-readable entity names in the breadcrumb rather than raw URL slugs or IDs.
- **SC-003**: Users can click any intermediate breadcrumb segment and be navigated to the correct ancestor page within the standard navigation response time.
- **SC-004**: The breadcrumb correctly renders for routes up to at least 5 levels deep without truncation or layout issues.
- **SC-005**: Breadcrumb labels for known routes match the labels displayed in the application's navigation menu with 100% consistency.
- **SC-006**: No stale or leaked breadcrumb labels appear after navigating away from a page that set a dynamic label.

## Assumptions

- The application uses client-side routing (single-page application) with a defined route configuration that includes path patterns and labels.
- The existing flat route configuration array will continue to serve as the source of truth for known static route labels.
- "Home" is always the root breadcrumb segment, linked to `/`.
- The title-casing fallback converts hyphens and underscores to spaces and capitalizes the first letter of each word (e.g., "my-cool-app" becomes "My Cool App").
- Page components are responsible for providing meaningful dynamic labels for their route segments; the system provides the mechanism (context) but the content is supplied by each page.
- The breadcrumb context uses a path-segment-to-label mapping, allowing components to override only their own segment without affecting others.
