# Feature Specification: Solune UI Redesign

**Feature Branch**: `025-solune-ui-redesign`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Complete UI redesign from 'Agent Projects' (warm/western theme, 3-view hash routing) to Solune (modern purple/blue theme, 6-page React Router app with full sidebar). Frontend-only — all existing hooks and backend APIs are preserved."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Navigate the Solune App via Sidebar (Priority: P1)

An authenticated user opens the application and sees a modern sidebar on the left with the "Solune" branding, navigation links (App, Projects, Agents Pipeline, Agents, Chores, Settings), and a "Recent Interactions" section. They click any navigation link and the corresponding page loads in the main content area. The URL updates cleanly (no hash fragments). Browser back/forward navigation works as expected.

**Why this priority**: Navigation is the skeleton of the entire redesign. Without working routing and the layout shell, no other page can be accessed or tested. This is the foundational user journey.

**Independent Test**: Can be fully tested by logging in, clicking each sidebar link, verifying the correct page renders, and confirming URL changes. Delivers a navigable 6-page application.

**Acceptance Scenarios**:

1. **Given** the user is authenticated, **When** they load the app, **Then** the sidebar displays with Solune branding, 6 nav links, and the selected project name at the bottom.
2. **Given** the user is on the App (home) page, **When** they click "Projects" in the sidebar, **Then** the URL changes to `/projects` and the Projects page renders in the main content area.
3. **Given** the user is on the Projects page, **When** they press the browser back button, **Then** the app navigates to the previous page without a full reload.
4. **Given** the user clicks the sidebar collapse toggle, **When** the sidebar collapses, **Then** only icons are shown, the collapsed state persists on page refresh, and the main content area expands.
5. **Given** the user is on any page, **When** they view the top bar, **Then** a breadcrumb reflecting the current route, a theme toggle, a notification bell, and their user avatar are visible.

---

### User Story 2 — View and Manage the Project Board (Priority: P1)

An authenticated user navigates to the Projects page and sees their selected GitHub project displayed as a Kanban board. Each column shows a header with item count, cards display color-coded priority badges, assignee avatars, description snippets, date, and label pills. The user can drag and drop cards between columns. Real-time sync continues to work.

**Why this priority**: The project board is the core feature of the application. Preserving and enhancing it is critical to user value and ensures no regression of primary functionality.

**Independent Test**: Can be fully tested by navigating to `/projects`, verifying the board loads with enhanced card styling, dragging a card between columns, and confirming the change persists via the existing real-time sync mechanism.

**Acceptance Scenarios**:

1. **Given** the user navigates to `/projects`, **When** the page loads, **Then** the project board renders with columns, each showing a header with the column name and item count badge.
2. **Given** a board is displayed, **When** the user views an issue card, **Then** the card shows a color-coded priority badge (P0=red, P1=orange, P2=blue, P3=green from the `BoardItem.priority` field), assignee avatar and name, a description snippet, date, and pastel-colored label pills.
3. **Given** a board is displayed, **When** the user drags a card from one column to another, **Then** the card moves and the change is synced to the backend.
4. **Given** the board is displayed, **When** the user views the page header, **Then** the project title, visibility badge, collaborator avatars, and a progress bar are visible.
5. **Given** the board is displayed, **When** the user looks at the end of the columns, **Then** an "Add new column" button is visible.

---

### User Story 3 — Use the Solune Design System (Light & Dark Mode) (Priority: P1)

A user opens the application and sees the new Solune visual design: purple/violet primary colors, modern sans-serif typography, soft rounded corners, and cool/neutral shadows. They toggle between light and dark mode using the top bar toggle, and both themes are cohesive and readable.

**Why this priority**: The design system underpins every visual element. It must be in place before any page can match the target aesthetic. This is also a key part of the rebranding from "Agent Projects" to "Solune."

**Independent Test**: Can be fully tested by loading the app, visually confirming the Solune theme (colors, fonts, shadows), toggling dark mode, and verifying proper contrast and no remnants of the old western/warm theme.

**Acceptance Scenarios**:

1. **Given** the user loads the app in light mode, **When** the page renders, **Then** the interface uses soft whites, light grays, and purple/violet primary colors with modern sans-serif typography.
2. **Given** the user toggles to dark mode, **When** the theme changes, **Then** the interface uses deep slate backgrounds with lighter purple accents and meets proper contrast ratios.
3. **Given** any page is loaded, **When** the user inspects visual elements, **Then** no remnants of the old warm/western theme (Rye font, warm shadows, cowboy avatar) are present.
4. **Given** the user views priority indicators anywhere in the app, **When** they compare priorities, **Then** P0 (critical) is red, P1 (high) is orange, P2 (medium) is blue, and P3 (low) is green, sourced from the existing `priority` field on `BoardItem`.

---

### User Story 4 — Access Chat from Any Page (Priority: P2)

A user is on any page of the application (Projects, Agents Pipeline, Settings, etc.) and can open a floating chat popup. The chat connects to the existing backend and functions identically to the current implementation, but is now globally accessible rather than tied to the project board.

**Why this priority**: Chat is a key user interaction. Making it globally available improves discoverability and workflow continuity when navigating between pages.

**Independent Test**: Can be fully tested by navigating to each of the 6 pages, opening the chat popup from each, sending a message, and confirming the response is received.

**Acceptance Scenarios**:

1. **Given** the user is on the Projects page, **When** they open the chat popup, **Then** the chat interface appears and is functional.
2. **Given** the user is on the Settings page, **When** they open the chat popup, **Then** the same chat interface appears and is functional.
3. **Given** the user has an active chat conversation on one page, **When** they navigate to another page and reopen chat, **Then** the full chat history is preserved.
4. **Given** the user has chat history and refreshes the browser, **When** the page reloads and they open the chat popup, **Then** the previous chat history is still available.

---

### User Story 5 — Manage Agents via Pipeline and Agents Pages (Priority: P2)

A user navigates to the Agents Pipeline page to see board columns represented as pipeline stages with assigned agents, their statuses (running/idle/error), and an execution timeline. They can assign or remove agents per column. On the separate Agents page, they see a visual assignment map and an agent catalog for adding, editing, or deleting agents.

**Why this priority**: Agent management is a core differentiating feature. Splitting it into Pipeline (operational view) and Agents (catalog/configuration view) improves usability over the current combined panel approach.

**Independent Test**: Can be fully tested by navigating to `/pipeline`, verifying agent status display and configuration controls, then navigating to `/agents` and verifying the assignment map and catalog display.

**Acceptance Scenarios**:

1. **Given** the user navigates to `/pipeline`, **When** the page loads, **Then** board columns appear as pipeline stages showing assigned agents with status indicators.
2. **Given** the user is on the Pipeline page, **When** they assign an agent to a column, **Then** the agent appears in that column's stage and the configuration is saved.
3. **Given** the user navigates to `/agents`, **When** the page loads, **Then** a visual agent-to-column assignment map and an agent catalog grid are displayed.
4. **Given** the user is on the Agents page, **When** they add a new agent via the catalog, **Then** the agent appears in the catalog and can be assigned to columns.

---

### User Story 6 — Manage Chores from a Dedicated Page (Priority: P2)

A user navigates to the Chores page and sees a catalog of automated chores with rich metadata (status, schedule, last/next run, results). They can create new chores, pause/resume existing ones, and access the cleanup utility.

**Why this priority**: Chores are a distinct feature area that benefits from dedicated space. Consolidating chore management and cleanup in one location improves discoverability.

**Independent Test**: Can be fully tested by navigating to `/chores`, viewing chore metadata, toggling a chore's pause/resume state, and triggering the cleanup utility.

**Acceptance Scenarios**:

1. **Given** the user navigates to `/chores`, **When** the page loads, **Then** a chore catalog displays with status, schedule, last run, and next run metadata.
2. **Given** the user clicks "Add Chore," **When** the modal opens, **Then** they can browse templates and create a new chore.
3. **Given** the user views a chore entry, **When** they toggle pause/resume, **Then** the chore state updates accordingly.
4. **Given** the user scrolls to the cleanup section, **When** they trigger cleanup, **Then** the cleanup confirmation modal appears with expected behavior.

---

### User Story 7 — Select and Switch Projects (Priority: P2)

A user sees their currently selected GitHub project name at the bottom of the sidebar. They click it to open a project selector, choose a different project, and the board and related data refresh to reflect the newly selected project.

**Why this priority**: Project switching is essential for users working across multiple GitHub projects. Moving it to the sidebar provides persistent, easy access.

**Independent Test**: Can be fully tested by clicking the project name in the sidebar, selecting a different project, and verifying the board data reloads.

**Acceptance Scenarios**:

1. **Given** the user has a project selected, **When** they look at the sidebar bottom, **Then** the selected project name is displayed.
2. **Given** the user clicks the project name, **When** the project selector opens, **Then** available projects are listed.
3. **Given** the user selects a different project, **When** the selection is confirmed, **Then** the board and related data refresh for the new project.

---

### User Story 8 — Unauthenticated Login Experience (Priority: P3)

A user who is not authenticated visits the application and sees a Solune-branded login page (no sidebar or app chrome). They authenticate via GitHub and are redirected into the full application with sidebar navigation.

**Why this priority**: The login gate is necessary but affects only the entry point. The existing auth flow is preserved; only the visual presentation changes.

**Independent Test**: Can be fully tested by visiting the app while unauthenticated, verifying the branded login page appears, authenticating, and confirming redirect to the authenticated layout.

**Acceptance Scenarios**:

1. **Given** the user is not authenticated, **When** they visit any URL, **Then** they see a Solune-branded login page without sidebar or top bar.
2. **Given** the user is on the login page, **When** they authenticate via GitHub, **Then** they are redirected to the originally requested URL (or `/` if none) with the full layout shell.

---

### User Story 9 — View Recent Interactions in Sidebar (Priority: P3)

An authenticated user sees a "Recent Interactions" section in the sidebar showing the most recent parent issues (descending), providing quick context and navigation back to recently active items.

**Why this priority**: This is a convenience feature that enhances daily workflow but is not blocking for core functionality.

**Independent Test**: Can be fully tested by loading the app with board data, verifying the sidebar displays recent parent issues, and clicking one to navigate or scroll to it.

**Acceptance Scenarios**:

1. **Given** the user is authenticated and has board data loaded, **When** they view the sidebar, **Then** a "Recent Interactions" section displays up to 8 recent parent issues sorted descending.
2. **Given** the user clicks a recent interaction entry, **When** the action completes, **Then** they are navigated to the relevant context for that issue.

---

### Edge Cases

- What happens when the user navigates to a non-existent route? The app displays a "Page Not Found" message within the layout shell.
- What happens when the sidebar is collapsed and the user resizes the window? The collapsed state is preserved; the main content area adapts to fill available space.
- What happens when there are no recent parent issues? The "Recent Interactions" section displays a subtle empty state message (e.g., "No recent activity").
- What happens when the user has no projects available? The project selector shows an empty state with a prompt to connect a GitHub project.
- What happens when board data is still loading? Loading indicators appear in place of content (skeleton states or spinners), consistent with Solune design.
- What happens when the user has a deep-link URL and is not authenticated? They are redirected to the login page; after authentication, they are returned to the original URL.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1: Foundation (Design System + Routing + Layout Shell)

- **FR-001**: The application MUST use client-side routing with clean URLs (no hash fragments) supporting 6 routes: `/` (home), `/projects`, `/pipeline`, `/agents`, `/chores`, `/settings`.
- **FR-002**: The application MUST render a persistent layout shell consisting of a collapsible sidebar (left) and a main content area (right), with a top bar above the content area.
- **FR-003**: The sidebar MUST display the "Solune" brand identity at the top, navigation links with a purple active-state indicator and left border accent, a "Recent Interactions" section, and the selected project name at the bottom.
- **FR-004**: The sidebar collapse/expand state MUST persist across page reloads via local storage, showing only icons when collapsed.
- **FR-005**: The top bar MUST display a dynamic breadcrumb (reflecting the current route) on the left, and a notification bell, theme toggle, and user avatar on the right.
- **FR-006**: The design system MUST replace the existing warm/western theme with a purple/violet primary palette, modern sans-serif typography, neutral/cool shadows, and 0.5rem border radius.
- **FR-007**: The design system MUST support both light mode (soft whites, light grays, purple primary) and dark mode (deep slate backgrounds, lighter purple, proper contrast).
- **FR-008**: Priority indicators throughout the app MUST use consistent color tokens mapped from the GitHub Project "Priority" custom field: P0 (critical) = red, P1 (high) = orange, P2 (medium) = blue, P3 (low) = green. Issues without a priority field default to P2 styling.
- **FR-009**: The `nginx.conf` MUST include SPA fallback (`try_files $uri $uri/ /index.html`) so that direct URL access and browser refresh work for all routes.
- **FR-010**: Unauthenticated users MUST see a Solune-branded login page without sidebar or top bar; authenticated users MUST see the full layout shell. After authentication, the user MUST be redirected to the originally requested URL, falling back to `/` if no prior URL was requested.
- **FR-011**: All hash-based routing logic (`getViewFromHash`, `changeView`, `hashchange` listeners) MUST be removed.

#### Phase 2: Page Migration

- **FR-012**: The App (home) page MUST display a clean welcome/landing view with quick-access cards linking to Projects, Pipeline, Agents, Chores, and Settings.
- **FR-013**: The Projects page MUST display the project board with a page header (project title, visibility badge, collaborator avatars, progress bar), toolbar scaffolding (Filter, Sort by, Group by), and enhanced board columns and cards.
- **FR-014**: Issue cards MUST display a color-coded priority badge, description snippet, assignee name and avatar, date, and label pills with pastel colors.
- **FR-015**: Board columns MUST display a header with the column name and item count badge, and a "+" add button.
- **FR-016**: The project board MUST display an "Add new column" button after the last column.
- **FR-017**: The Agents Pipeline page MUST display a pipeline visualization (columns as stages with agent status), an agent configuration section (assign/remove agents per column), and an activity feed of recent agent notifications.
- **FR-018**: The Agents page MUST display an agent-to-column assignment map and an agent catalog (grid of agent cards with add/edit/delete, source badges, enable/disable).
- **FR-019**: The Chores page MUST display a chore catalog with rich metadata (status, schedule, last/next run, results), chore creation via modal with template browser, and a cleanup section.
- **FR-020**: The Settings page MUST retain all existing configuration sections, restyled to match the Solune design system.

#### Phase 3: Global Components & Polish

- **FR-021**: The chat popup MUST be rendered at the layout level so it is accessible and functional from every page, not just the Projects page. Chat history MUST persist across page navigation and browser refreshes (via local storage or backend persistence).
- **FR-022**: The notification bell MUST display a count badge reflecting unread notifications and provide a dropdown listing recent notifications. Data sources include agent workflow events (started, completed, errored) and chore completion events, sourced from existing hooks.
- **FR-023**: The sidebar "Recent Interactions" section MUST display up to 8 recent parent issues sorted descending, derived from board data.
- **FR-024**: All references to "Agent Projects" MUST be replaced with "Solune" throughout the UI, including page titles and branding elements.
- **FR-025**: The `CowboyAvatar` component, Rye font references, and any western-theme assets MUST be removed.
- **FR-026**: All existing unit tests MUST pass after updates. Test fixtures MUST be updated to reflect the new component structure.

### Key Entities

- **Page**: One of 6 navigable views (App, Projects, Pipeline, Agents, Chores, Settings), each rendered at a distinct URL path within the application layout.
- **Sidebar**: Persistent navigation component displaying brand identity, nav links, recent interactions, and project selector. Has a collapsed/expanded state.
- **Issue Card**: Visual representation of a GitHub issue on the board, displaying priority, assignee, description, date, and labels with enhanced styling.
- **Board Column**: A named column in the project board representing a workflow stage, displaying a header with item count and containing issue cards.
- **Agent Pipeline Stage**: A board column viewed through the lens of agent assignment, showing which agents are assigned and their operational status.
- **Chore**: An automated task with metadata (status, schedule, last/next run, results) manageable from the dedicated Chores page.
- **Project Selector**: A modal or dropdown component accessed from the sidebar bottom, allowing users to switch between available GitHub projects.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can navigate between all 6 pages using the sidebar, with each page loading in under 2 seconds on a standard connection.
- **SC-002**: The application builds with zero compile errors after each implementation phase.
- **SC-003**: All existing unit tests pass with updated fixtures reflecting the new component structure.
- **SC-004**: Browser back/forward navigation works correctly across all 6 routes without full page reloads.
- **SC-005**: Direct URL access to any route (e.g., typing `/settings` in the address bar) loads the correct page without errors.
- **SC-006**: Light mode visual appearance matches the reference design aesthetic (purple/violet primary, modern sans-serif, cool shadows).
- **SC-007**: Dark mode maintains proper contrast ratios (WCAG AA minimum) and consistent use of the Solune color palette.
- **SC-008**: The chat popup is functional from every page, with full chat history preserved across page navigation and browser refreshes.
- **SC-009**: Existing board functionality is preserved: drag-and-drop, real-time sync, and agent configuration save all work as before.
- **SC-010**: Sidebar collapse/expand works correctly, with collapsed state persisting across browser refreshes.
- **SC-011**: No visual or textual remnants of the old "Agent Projects" branding, Rye font, or western theme are present anywhere in the UI.
- **SC-012**: The login page renders with Solune branding when unauthenticated, and the full layout shell appears after successful authentication.

## Clarifications

### Session 2026-03-06

- Q: What should happen after a user authenticates — always home, preserve deep-link, or always projects? → A: Redirect to the originally requested URL (deep-link preserved), falling back to `/` if none.
- Q: When the user navigates between pages, what chat state should persist? → A: Full chat history persists across navigation AND page refreshes (via local storage or backend persistence).
- Q: What is the notification bell's data source? → A: Agent notifications + chore completion events (combines workflow + chore data from existing hooks).
- Q: Should scaffolding buttons show a visual indicator that they are not yet functional? → A: Show "Coming soon" tooltip for truly unimplemented features, but wire buttons to existing functionality wherever hooks/APIs already support the action.
- Q: How should issue priority be determined for the color-coded badges? → A: From the existing GitHub Project "Priority" custom field already on `BoardItem.priority`. Mapping: P0=red (critical), P1=orange (high), P2=blue (medium), P3=green (low). Default to P2 if absent.

## Assumptions

- The existing backend API endpoints remain unchanged and serve all data needed by the new UI. No new endpoints are required.
- The existing auth flow (GitHub OAuth) is preserved; only the login page presentation changes.
- All existing React hooks (`useAuth`, `useProjects`, `useChat`, `useProjectBoard`, `useBoardRefresh`, `useRealTimeSync`, `useWorkflow`, `useAgentConfig`, `useAvailableAgents`, `useChores`, `useCleanup`, `useSettings`, `useAppTheme`, `useCommands`, `useMetadata`) are preserved without modification.
- The application targets desktop browsers at 1024px minimum width; responsive behavior below 1024px is out of scope.
- CSS transitions are used for animations; no additional animation libraries are added.
- The "Add new column" button, toolbar controls (Filter, Sort by, Group by), and the "+" card add button on columns MUST be wired to existing functionality where the underlying hooks/APIs already support the action. Only buttons whose functionality has no existing backend or hook support should render as scaffolding with a "Coming soon" tooltip on click.

## Scope Exclusions

- Global search functionality
- New backend API endpoints
- Mobile/responsive designs below 1024px viewport width
- Internationalization (i18n)
- Animation library additions (CSS transitions only)
- Drag-and-drop for sidebar navigation items or page reordering

## Decisions

- **React Router over hash routing**: Clean URLs, proper browser history support, and industry-standard SPA routing.
- **Complete theme replacement**: No backward compatibility with the western theme. The old design system is fully replaced.
- **Project selector in sidebar bottom**: Provides persistent, always-accessible project switching rather than a per-page dropdown.
- **Chat as global floating popup**: Chat is available from every page, not confined to a dedicated route or a single page.
- **Agent management split into two pages**: Pipeline page for operational view (status, assignment, activity); Agents page for catalog management (add/edit/delete, assignment map).
- **Cleanup consolidated on Chores page**: The cleanup utility is grouped with chores as related maintenance operations.
- **No new backend APIs**: All data needs are served by existing endpoints.
