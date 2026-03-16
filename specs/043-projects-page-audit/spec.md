# Feature Specification: Projects Page Audit

**Feature Branch**: `043-projects-page-audit`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Comprehensive audit of the Projects page to ensure modern best practices, modular design, accurate text/copy, and zero bugs. Covers component decomposition, accessibility, error/loading/empty states, type safety, test coverage, and UI/UX polish."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Page Loads Reliably with Clear Feedback (Priority: P1)

A user navigates to the Projects page and sees immediate, informative feedback at every stage: a loading indicator while data is being retrieved, a clear error message with a retry option if something goes wrong, and a meaningful empty state when no projects exist or none is selected. No blank screens or cryptic error codes appear at any point.

**Why this priority**: Reliable loading and clear error communication are the foundation of a usable page. If the page doesn't load properly or fails silently, no other improvement matters.

**Independent Test**: Can be fully tested by navigating to the Projects page under four conditions — normal load, slow network, API failure, and empty data — and verifying appropriate feedback in each case.

**Acceptance Scenarios**:

1. **Given** the user navigates to the Projects page and the API is responding, **When** data is being fetched, **Then** a visible loading indicator appears (never a blank screen).
2. **Given** the user navigates to the Projects page and the API returns an error, **When** the error response is received, **Then** a user-friendly error message displays with a retry action and no raw error codes or stack traces.
3. **Given** the user navigates to the Projects page and no projects exist, **When** the page finishes loading, **Then** a meaningful empty state appears with guidance on how to get started.
4. **Given** the user has a project selected but the board data fails to load, **When** the board error is displayed, **Then** only the board section shows the error — the project selector and page header remain functional.
5. **Given** the GitHub API rate limit has been exceeded, **When** the user interacts with the page, **Then** a clear rate-limit banner appears showing when the limit resets, and the page does not attempt further API calls until recovery.

---

### User Story 2 - Page is Modular and Maintainable (Priority: P1)

A developer working on the Projects page can understand, modify, and extend it without reading through a single monolithic file. The page is decomposed into focused sub-components, each with a single responsibility. Complex state logic lives in dedicated hooks, not inline in the render tree. No component file exceeds 250 lines.

**Why this priority**: Maintainability directly impacts the team's ability to iterate on the page safely and efficiently. A 630-line page file is a blocker for parallel work and increases the risk of regressions.

**Independent Test**: Can be verified by checking that the page file is ≤250 lines, sub-components live in a dedicated feature folder, and no prop drilling exceeds two levels.

**Acceptance Scenarios**:

1. **Given** the Projects page file, **When** a developer inspects the file, **Then** the page file is ≤250 lines and delegates rendering to sub-components.
2. **Given** the Projects page uses sub-components, **When** a developer looks at the file structure, **Then** all board-related sub-components reside in a dedicated feature folder.
3. **Given** the Projects page passes data to child components, **When** a developer traces prop flow, **Then** no prop drilling exceeds two levels — composition, context, or hook extraction is used instead.
4. **Given** complex state logic exists (more than 15 lines of state management), **When** a developer inspects the code, **Then** that logic is extracted into dedicated hooks.
5. **Given** the page uses interactive UI elements, **When** a developer inspects the render tree, **Then** no business logic (computation, data transformation, conditional formatting) appears inline in the component markup.

---

### User Story 3 - Page is Fully Accessible (Priority: P2)

A user relying on a keyboard or screen reader can navigate and interact with every feature of the Projects page. All interactive elements are reachable via Tab, activatable via Enter/Space, and announced correctly by assistive technology. Dialogs trap focus, and color is never the sole indicator of status.

**Why this priority**: Accessibility is a core quality requirement that affects a significant portion of users. Gaps in keyboard navigation or missing ARIA attributes block users from completing critical tasks.

**Independent Test**: Can be tested by navigating the entire page using only a keyboard and verifying all interactions work, then running an automated accessibility audit tool to check ARIA compliance and color contrast.

**Acceptance Scenarios**:

1. **Given** the user navigates the Projects page using only a keyboard, **When** the user presses Tab, **Then** every interactive element (buttons, links, dropdowns, cards) receives visible focus in a logical order.
2. **Given** the pipeline selector dropdown is focused, **When** the user presses Enter or Space, **Then** the dropdown opens, options are navigable with arrow keys, and selection is confirmed with Enter.
3. **Given** a modal dialog (e.g., issue detail) is open, **When** the user presses Tab, **Then** focus is trapped within the dialog and does not escape to background elements.
4. **Given** a modal dialog is closed, **When** the dialog dismisses, **Then** focus returns to the element that triggered the dialog.
5. **Given** the board displays status indicators, **When** a user views the board, **Then** status is conveyed by both an icon (or text label) and color — never by color alone.
6. **Given** decorative icons are present, **When** a screen reader reads the page, **Then** decorative icons are hidden from assistive technology and meaningful icons have descriptive labels.

---

### User Story 4 - Text, Copy, and UX Are Polished (Priority: P2)

Every piece of user-visible text on the Projects page is final, meaningful, and consistent with the rest of the application. Action buttons use verb labels, destructive actions require confirmation, mutations provide success or failure feedback, and long text is truncated with a tooltip showing the full content.

**Why this priority**: Polished copy and consistent UX patterns build user trust and reduce confusion. Inconsistent terminology or missing feedback creates friction in daily workflows.

**Independent Test**: Can be tested by reviewing all user-visible strings for placeholder text, verifying button labels are action verbs, confirming destructive actions show confirmation dialogs, and checking that mutations display success/error feedback.

**Acceptance Scenarios**:

1. **Given** the Projects page is rendered, **When** a reviewer inspects all visible text, **Then** no placeholder text, TODOs, or lorem ipsum strings are present.
2. **Given** the page has action buttons, **When** a reviewer inspects button labels, **Then** all action buttons use verb phrases (e.g., "Create Project", "Assign Pipeline", "Clear Filters") rather than noun-only labels.
3. **Given** a destructive action exists (e.g., removing a pipeline assignment), **When** the user triggers the action, **Then** a confirmation dialog appears before the action is executed.
4. **Given** a mutation (e.g., pipeline assignment) succeeds, **When** the operation completes, **Then** the user sees success feedback (toast notification, inline status change, or visual confirmation).
5. **Given** a mutation fails, **When** the error is received, **Then** a user-friendly error message appears in the format: "Could not [action]. [Reason]. [Suggested next step]."
6. **Given** long text (project names, descriptions, URLs) appears on the page, **When** the text exceeds its container, **Then** it is truncated with ellipsis and a tooltip reveals the full content on hover.

---

### User Story 5 - Styling Is Consistent and Responsive (Priority: P3)

The Projects page renders correctly across viewport widths from 768px to 1920px, supports both light and dark modes without visual issues, uses the application's design system consistently, and avoids inline styles or hardcoded colors.

**Why this priority**: Visual consistency and responsiveness are important for professional polish but are lower risk than functional or accessibility issues.

**Independent Test**: Can be tested by resizing the browser viewport from 768px to 1920px and toggling between light and dark modes, verifying no layout breaks, contrast failures, or hardcoded colors.

**Acceptance Scenarios**:

1. **Given** the Projects page is displayed at 768px viewport width, **When** the user views the page, **Then** the layout adapts without horizontal scrolling, overflow, or overlapping elements.
2. **Given** the Projects page is displayed at 1920px viewport width, **When** the user views the page, **Then** content uses available space appropriately without excessive whitespace or stretching.
3. **Given** the system is set to dark mode, **When** the user views the page, **Then** all elements are visible with adequate contrast and no hardcoded light-mode colors leak through.
4. **Given** the page uses spacing and layout, **When** a developer inspects the styles, **Then** all spacing uses the application's design scale — no arbitrary pixel values.
5. **Given** the page uses conditional styling, **When** a developer inspects the code, **Then** no inline `style={}` attributes exist — all styling uses the application's utility class system.

---

### User Story 6 - Page Performs Well Under Load (Priority: P3)

The Projects page renders efficiently even with large numbers of board items. Lists use stable keys, expensive computations are memoized, and no unnecessary re-renders occur when unrelated state changes.

**Why this priority**: Performance issues degrade the user experience over time but are less critical than correctness, accessibility, or maintainability for this audit.

**Independent Test**: Can be tested by loading a board with 50+ items and verifying smooth scrolling, no visible jank, and no duplicate API calls in the network panel.

**Acceptance Scenarios**:

1. **Given** the board has more than 50 items, **When** the user scrolls through the board, **Then** the page remains responsive without visible lag or frame drops.
2. **Given** the board renders a list of items, **When** a developer inspects the render output, **Then** all list items use stable, unique identifiers as keys — never array indices.
3. **Given** the user changes a filter or sort option, **When** the board re-renders, **Then** only affected components re-render — unrelated sections remain stable.
4. **Given** the page has multiple data sources, **When** all data is loaded, **Then** no duplicate API calls are made for the same data.

---

### User Story 7 - Comprehensive Test Coverage (Priority: P3)

All custom hooks, key interactive components, and critical user flows on the Projects page have automated tests. Tests cover happy paths, error states, loading states, empty states, and edge cases using the project's established testing patterns.

**Why this priority**: Test coverage ensures audit improvements don't regress over time, but tests are a means to an end — the functional and UX improvements take priority.

**Independent Test**: Can be verified by running the test suite and confirming all project-related tests pass, with coverage for loading, error, empty, and interactive states.

**Acceptance Scenarios**:

1. **Given** custom hooks exist for the Projects page, **When** a developer checks the test suite, **Then** each hook has tests covering its happy path, error response, loading state, and empty data.
2. **Given** key interactive components exist (board toolbar, issue cards, pipeline selector), **When** a developer checks the test suite, **Then** each component has tests for user interactions (clicks, keyboard events, form submissions).
3. **Given** the Projects page has edge cases (rate limit errors, long strings, null data), **When** a developer checks the test suite, **Then** these edge cases are covered by tests.
4. **Given** the test suite runs, **When** all tests complete, **Then** zero tests fail and zero lint warnings are produced.

---

### Edge Cases

- What happens when the user rapidly switches between projects before the previous board data finishes loading?
- How does the page behave when a WebSocket connection drops and reconnects during a board refresh?
- What happens when a project has hundreds of board items across many columns?
- How does the pipeline selector behave when there are zero saved pipelines?
- What happens when the user's session expires while the page is open?
- How does the page handle a project that was deleted on GitHub but still appears in the local cache?
- What happens when board data returns items with null or missing optional fields (no assignees, no priority, no linked PRs)?
- How does the page behave when the user has no projects at all (new account with no GitHub Projects)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Page file MUST be ≤250 lines, with self-contained sections extracted into sub-components in a dedicated feature folder.
- **FR-002**: Complex state logic (more than 15 lines of state management) MUST be extracted into dedicated hooks.
- **FR-003**: Page MUST NOT drill props more than two levels — composition, context, or hook extraction MUST be used instead.
- **FR-004**: Page MUST reuse existing shared UI primitives (Button, Card, Input, Tooltip, ConfirmationDialog) rather than reimplementing them.
- **FR-005**: Page MUST reuse existing shared components (CelestialLoader, ErrorBoundary, ProjectSelectionEmptyState) where applicable.
- **FR-006**: All API calls MUST use the established query library patterns — no raw effect-based fetch calls.
- **FR-007**: All data-fetching queries MUST have appropriate staleness configuration (e.g., 30 seconds for lists, 60 seconds for settings).
- **FR-008**: All mutations MUST invalidate related queries on success and surface user-visible error feedback on failure.
- **FR-009**: Page MUST display a loading indicator while data loads — never a blank screen.
- **FR-010**: Page MUST display a clear, user-friendly error message with a retry action when an API call fails.
- **FR-011**: Page MUST detect rate-limit errors and display a specific banner showing reset time.
- **FR-012**: Page MUST show a meaningful empty state with guidance when data loads successfully but the collection is empty.
- **FR-013**: Independent page sections MUST show their own loading and error states — one failed section MUST NOT block the entire page.
- **FR-014**: Page MUST be wrapped in an error boundary at the route or page level.
- **FR-015**: All props, state, and API response types MUST be fully specified — no untyped or loosely typed values.
- **FR-016**: All interactive elements MUST be reachable via keyboard (Tab) and activatable via Enter/Space.
- **FR-017**: Dialogs and modals MUST trap focus and return focus to the trigger element on close.
- **FR-018**: Custom controls (dropdowns, toggles, pipeline selector) MUST have appropriate ARIA roles, labels, and state attributes.
- **FR-019**: All form fields MUST have associated labels (visible or accessible).
- **FR-020**: Color MUST NOT be the sole indicator of status — icon or text MUST accompany color indicators.
- **FR-021**: All interactive elements MUST have visible focus styles.
- **FR-022**: All user-visible strings MUST be final, meaningful copy — no placeholders, TODOs, or test text.
- **FR-023**: Action buttons MUST use verb-phrase labels (e.g., "Assign Pipeline" not "Pipeline").
- **FR-024**: All destructive actions MUST require confirmation via a confirmation dialog.
- **FR-025**: All mutations MUST show success feedback (toast, inline message, or visual state change).
- **FR-026**: Error messages shown to users MUST follow the format: "Could not [action]. [Reason]. [Suggested next step]."
- **FR-027**: Long text (names, descriptions, URLs) MUST be truncated with ellipsis and display full content in a tooltip on hover.
- **FR-028**: Page MUST NOT use inline style attributes — all styling MUST use the application's utility class system.
- **FR-029**: Page MUST render correctly at viewport widths from 768px to 1920px without layout breaks.
- **FR-030**: Page MUST support both light and dark modes using theme variables — no hardcoded colors.
- **FR-031**: Spacing MUST use the application's design scale — no arbitrary pixel values.
- **FR-032**: List renders MUST use stable, unique item identifiers as keys — never array indices.
- **FR-033**: Expensive computations (sorting, filtering, grouping) MUST be memoized to prevent redundant calculations on re-render.
- **FR-034**: All custom hooks for this page MUST have automated tests covering happy path, error, loading, and empty states.
- **FR-035**: Key interactive components MUST have automated tests for user interactions.
- **FR-036**: All dead code (unused imports, commented-out blocks, unreachable branches) MUST be removed.
- **FR-037**: All project imports MUST use the path alias convention — no deep relative paths.
- **FR-038**: All repeated strings (status values, route paths, query keys) MUST be defined as constants.
- **FR-039**: The page and all related files MUST pass linting with zero warnings.

### Key Entities

- **Project**: A GitHub Project linked to the application. Key attributes: unique identifier, name, owner, type (organization/user/repository), description, status columns, item count.
- **Board**: A Kanban-style view of a project's items organized by status columns. Each board belongs to one project and contains columns with items.
- **Board Item**: An issue or pull request displayed on the board. Key attributes: title, number, repository, status, assignees, priority, size, linked pull requests.
- **Board Column**: A status-based grouping of board items (e.g., "To Do", "In Progress", "Done"). Each column has a status, color, and ordered list of items.
- **Pipeline Configuration**: A reusable agent pipeline that can be assigned to a project. Defines which agent stages process items on the board.
- **Pipeline Assignment**: The link between a project and its active pipeline configuration.
- **Rate Limit Info**: GitHub API rate limit state. Key attributes: limit, remaining calls, reset timestamp, calls used.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Projects page file is ≤250 lines after decomposition, with all sub-components organized in a dedicated feature folder.
- **SC-002**: All loading states display feedback within 100 milliseconds of navigation — users never see a blank screen.
- **SC-003**: 100% of API error scenarios display a user-friendly message with a retry action — zero raw error codes or stack traces reach the user.
- **SC-004**: 100% of interactive elements on the page are reachable and operable via keyboard-only navigation.
- **SC-005**: An automated accessibility audit of the page produces zero critical or serious violations.
- **SC-006**: The page renders without visual defects at every viewport width from 768px to 1920px in both light and dark modes.
- **SC-007**: All user-visible text is final, meaningful copy — zero placeholder strings, TODOs, or test text remain.
- **SC-008**: All custom hooks and key interactive components have automated tests — test coverage for project-related code reaches at least 80%.
- **SC-009**: The page and all related files pass linting with zero warnings and type checking with zero errors.
- **SC-010**: No duplicate API calls are made when loading the page — each data source is fetched exactly once.
- **SC-011**: All destructive actions require explicit user confirmation before execution.
- **SC-012**: Users receive clear feedback (success or failure) for every mutation within 2 seconds of the operation completing.

## Assumptions

- The existing shared UI primitives (Button, Card, Tooltip, ConfirmationDialog, etc.) are stable and suitable for use without modification.
- The established query library (TanStack Query) patterns and conventions are the standard for all data fetching on this page.
- The existing CelestialLoader and ProjectSelectionEmptyState components meet the visual and accessibility requirements for loading and empty states.
- The page audit is scoped to the Projects page and its direct sub-components — shared components and hooks used by other pages are not in scope for modification (only for reuse).
- Performance targets (responsive scrolling with 50+ items) apply to standard modern browsers and hardware — no specific device benchmarks are required.
- The existing test infrastructure (Vitest, React Testing Library, mock patterns) is sufficient — no new testing frameworks are needed.
- Dark mode support relies on the application's existing theme system (CSS custom properties and Tailwind dark variants) — no new theme infrastructure is required.
- Accessibility compliance targets WCAG 2.1 AA level as the standard for this audit.
