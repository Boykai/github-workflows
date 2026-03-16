# Feature Specification: Tools Page Audit

**Feature Branch**: `043-tools-page-audit`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Comprehensive audit of the Tools page to ensure modern best practices, modular design, accurate text/copy, and zero bugs. Covers component decomposition, accessibility, error/loading/empty states, type safety, test coverage, and UI/UX polish."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable Tool Management Without Errors (Priority: P1)

As a user managing MCP tool configurations on the Tools page, I need every interaction — uploading, editing, syncing, and deleting tools — to provide clear feedback, handle errors gracefully, and never leave me staring at a blank or broken screen, so that I can confidently manage my tools without confusion or data loss.

**Why this priority**: Core tool management is the primary purpose of the Tools page. If users encounter blank screens, unhandled errors, or silent failures when performing basic CRUD operations, the page is fundamentally broken. Fixing reliability issues is the highest-value improvement.

**Independent Test**: Can be tested by performing each tool operation (upload, edit, sync, delete) under normal conditions and under failure conditions (network error, rate limit, server error) and verifying appropriate feedback is shown in every case.

**Acceptance Scenarios**:

1. **Given** the Tools page is loading data, **When** the user navigates to the page, **Then** a loading indicator is displayed until data is fully loaded — never a blank screen.
2. **Given** an API call to list tools fails, **When** the error is returned, **Then** a user-friendly error message is shown with a retry action.
3. **Given** a rate-limit error occurs, **When** the system detects the error, **Then** a specific rate-limit message is displayed with guidance on when to retry.
4. **Given** the user has no tools configured, **When** the tools list is empty, **Then** a meaningful empty state is shown with a clear call-to-action to upload the first tool.
5. **Given** the user deletes a tool that is assigned to agents, **When** the delete button is clicked, **Then** a confirmation dialog warns which agents are affected before proceeding.
6. **Given** the user successfully uploads a tool, **When** the upload completes, **Then** a success notification is displayed and the tools list refreshes to show the new tool.
7. **Given** multiple independent sections (tools list, repository config, presets gallery) are on the page, **When** one section's data fails to load, **Then** the other sections continue to display normally and only the failed section shows an error.

---

### User Story 2 - Accessible and Keyboard-Navigable Tools Page (Priority: P2)

As a user who relies on keyboard navigation or assistive technologies, I need the Tools page to be fully navigable via keyboard, properly labeled for screen readers, and visually distinguishable for focus states, so that I can manage tools without requiring a mouse.

**Why this priority**: Accessibility is a fundamental quality requirement. Users with disabilities must be able to use the Tools page effectively. This also ensures compliance with WCAG AA standards and improves the experience for power users who prefer keyboard navigation.

**Independent Test**: Can be tested by navigating the entire Tools page using only the keyboard (Tab, Enter, Space, Escape) and verifying all interactive elements are reachable, activatable, and properly announced by a screen reader.

**Acceptance Scenarios**:

1. **Given** the Tools page is loaded, **When** the user presses Tab repeatedly, **Then** every interactive element (buttons, links, form fields, modals) receives focus in a logical order.
2. **Given** a modal dialog is open (upload, edit, delete confirmation), **When** the user presses Tab, **Then** focus is trapped within the modal and does not escape to the background.
3. **Given** a modal dialog is dismissed, **When** the user closes it, **Then** focus returns to the element that triggered the modal.
4. **Given** a screen reader is active, **When** navigating interactive controls, **Then** each control has a descriptive label (buttons announce their action, icons convey meaning, status indicators are described).
5. **Given** the page uses color to indicate status (e.g., sync status), **When** viewed without color perception, **Then** status is also conveyed through text labels or icons — not color alone.
6. **Given** an interactive element receives focus, **When** it is focused, **Then** a visible focus ring or indicator is displayed.

---

### User Story 3 - Consistent and Polished User Experience (Priority: P2)

As a user of the application, I need the Tools page to use consistent terminology, button labels, spacing, and visual patterns that match the rest of the application, so that the page feels cohesive and professional.

**Why this priority**: Inconsistent copy, mismatched button labels, or visual discrepancies erode user trust and make the application feel unfinished. This story ensures the Tools page meets the same quality bar as the rest of the application.

**Independent Test**: Can be tested by reviewing all visible text, button labels, timestamps, and visual elements against the application's established conventions and style guide.

**Acceptance Scenarios**:

1. **Given** the Tools page is displayed, **When** reviewing all button labels, **Then** every action button uses a verb-based label (e.g., "Upload Config", "Sync Tool", "Delete Tool") — not noun-only labels.
2. **Given** long tool names or descriptions appear, **When** they exceed the available space, **Then** text is truncated with an ellipsis and the full text is shown on hover via a tooltip.
3. **Given** timestamps are displayed (e.g., last synced time), **When** the timestamp is recent, **Then** relative time is shown (e.g., "2 hours ago"); for older timestamps, absolute dates are displayed.
4. **Given** destructive actions (delete tool, delete repo server), **When** the user initiates the action, **Then** a confirmation dialog appears before the action is executed — never immediate deletion.
5. **Given** error messages are shown to users, **When** an error occurs, **Then** the message follows the format "Could not [action]. [Reason]. [Suggested next step]." — no raw error codes or stack traces.
6. **Given** the page is viewed in dark mode, **When** switching between light and dark themes, **Then** all elements are legible and use theme-appropriate colors — no hardcoded colors.

---

### User Story 4 - Responsive and Performant Tools Page (Priority: P3)

As a user accessing the application on different screen sizes, I need the Tools page to adapt its layout gracefully from tablet to desktop viewports and render efficiently even with many tools, so that the page is usable and fast regardless of my device or data volume.

**Why this priority**: While not a critical blocker, performance and responsive design directly impact user satisfaction. A page that breaks on smaller screens or becomes sluggish with many tools degrades the overall experience.

**Independent Test**: Can be tested by resizing the browser from 768px to 1920px width and verifying layout adapts without breaking, and by loading the page with 50+ tools to verify performance remains acceptable.

**Acceptance Scenarios**:

1. **Given** the page is viewed at 768px viewport width, **When** the layout renders, **Then** the grid adapts from multi-column to fewer columns without horizontal overflow or overlapping elements.
2. **Given** the page is viewed at 1920px viewport width, **When** the layout renders, **Then** content uses available space effectively without excessive whitespace or tiny elements.
3. **Given** a project has more than 50 tools, **When** the page loads, **Then** the tools list renders without noticeable lag or janky scrolling.
4. **Given** the user filters or searches tools, **When** typing in the search field, **Then** results update in real time without perceptible delay.

---

### User Story 5 - Maintainable and Well-Tested Codebase (Priority: P3)

As a developer maintaining the Tools page, I need the code to follow established project conventions — modular components, extracted hooks, full type safety, and meaningful test coverage — so that future changes are safe, easy to understand, and unlikely to introduce regressions.

**Why this priority**: Code quality and test coverage reduce the long-term cost of maintaining the Tools page. While users don't see this directly, it prevents future bugs and makes the page easier to extend.

**Independent Test**: Can be tested by running the existing linter with zero warnings, the type checker with zero errors, and the test suite with all tests passing, plus verifying the page component stays within the line-count limit.

**Acceptance Scenarios**:

1. **Given** the Tools page file, **When** checked for line count, **Then** it contains no more than 250 lines; larger sections are extracted into dedicated sub-components.
2. **Given** complex state logic exists, **When** it exceeds 15 lines of state management code, **Then** it is extracted into a dedicated custom hook.
3. **Given** the codebase, **When** the linter is run against Tools page files, **Then** zero warnings or errors are reported.
4. **Given** the codebase, **When** the type checker is run, **Then** zero type errors exist in Tools page files — no use of `any` type.
5. **Given** the Tools page features, **When** tests are run, **Then** hook tests, component tests, and edge-case tests (empty state, error state, loading state, rate-limit error) all pass.

---

### Edge Cases

- What happens when the user's session expires mid-operation (e.g., while uploading a tool)?
- How does the page behave when the API returns an unexpected response shape (e.g., missing fields)?
- What happens when a user rapidly clicks the sync button on the same tool multiple times?
- How does the delete flow behave when the tool is assigned to agents that were deleted between the initial load and the delete action?
- What happens when the MCP configuration JSON is valid but contains unexpected keys or deeply nested structures?
- How does the page handle extremely long tool names or descriptions (500+ characters)?
- What happens when the repository config section loads successfully but the tools list fails — do users still see the repo config?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Tools page MUST display a loading indicator while tool data is being fetched — never a blank screen.
- **FR-002**: The Tools page MUST display a user-friendly error message with a retry action when any data fetch fails.
- **FR-003**: The Tools page MUST detect rate-limit errors and display a specific message indicating the user should wait before retrying.
- **FR-004**: The Tools page MUST display a meaningful empty state with a call-to-action when no tools are configured for the selected project.
- **FR-005**: The Tools page MUST show independent loading and error states for each data section (tools list, repository config, presets gallery) so that one failing section does not block others.
- **FR-006**: All destructive actions (delete tool, delete repo server) MUST require confirmation via a confirmation dialog before execution.
- **FR-007**: All mutation operations (upload, edit, sync, delete) MUST display success feedback (toast, inline message, or status change) upon completion.
- **FR-008**: All mutation errors MUST surface user-friendly messages following the format: "Could not [action]. [Reason]. [Suggested next step]."
- **FR-009**: All interactive elements MUST be reachable and activatable via keyboard (Tab, Enter, Space, Escape).
- **FR-010**: Modal dialogs MUST trap focus while open and return focus to the trigger element upon close.
- **FR-011**: All form fields MUST have associated labels (visible or via aria-label) for screen reader accessibility.
- **FR-012**: Status indicators (sync status) MUST convey meaning through both icon/text and color — not color alone.
- **FR-013**: All action buttons MUST use verb-based labels (e.g., "Upload Config", "Sync Tool", "Delete Tool").
- **FR-014**: Long text (tool names, descriptions, URLs) MUST be truncated with ellipsis and show the full text in a tooltip on hover.
- **FR-015**: Timestamps MUST use relative time for recent events and absolute dates for older events, applied consistently.
- **FR-016**: The page layout MUST adapt responsively for viewport widths from 768px to 1920px without horizontal overflow or broken layouts.
- **FR-017**: The page MUST support both light and dark themes using theme variables — no hardcoded color values.
- **FR-018**: The Tools page file MUST be no more than 250 lines; larger sections MUST be extracted into sub-components.
- **FR-019**: Complex state logic (more than 15 lines of state management) MUST be extracted into dedicated custom hooks.
- **FR-020**: The codebase MUST have zero linter warnings and zero type errors for all Tools page files.
- **FR-021**: The codebase MUST NOT contain `any` types, type assertions (`as`), dead code, console.log statements, or magic strings in Tools page files.
- **FR-022**: Custom hooks and key interactive components MUST have automated tests covering happy path, error state, loading state, and empty state scenarios.
- **FR-023**: Decorative icons MUST be hidden from screen readers; meaningful icons MUST have descriptive labels.
- **FR-024**: All interactive elements MUST have visible focus indicators when focused via keyboard.

### Key Entities

- **MCP Tool Configuration**: A user-managed configuration defining an MCP server connection. Key attributes: name, description, configuration content (JSON), sync status, target repository path, active state, creation and sync timestamps.
- **Repository MCP Server Config**: A server configuration read from or written to repository files (.copilot/mcp.json, .vscode/mcp.json). Key attributes: server name, configuration object, source file paths.
- **MCP Preset**: A pre-configured template for common MCP tools available in a gallery. Key attributes: name, description, category, icon, configuration content.
- **Tool-Agent Assignment**: The relationship between a tool and the agents it is assigned to. Used during deletion to warn about affected agents.

### Assumptions

- The existing shared UI primitives (Button, Card, Tooltip, ConfirmationDialog) and common components (CelestialLoader, ErrorBoundary, ProjectSelectionEmptyState) are stable and correct — this audit focuses on their correct usage, not on auditing those components themselves.
- The backend API contracts (endpoints, request/response shapes) are stable and do not require changes as part of this audit.
- The application's existing theme system (CSS variables, Tailwind dark: variants) provides adequate support for dark mode — no new theming infrastructure is needed.
- Existing test infrastructure (Vitest, Testing Library, React Query test utilities) is already set up and functional.
- The audit scope is limited to the Tools page and its directly related components, hooks, and types — it does not extend to shared components or the backend.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users never see a blank screen on the Tools page — loading, error, and empty states are present for every data-dependent section.
- **SC-002**: 100% of destructive actions require confirmation before execution.
- **SC-003**: 100% of mutation operations display user-visible success or error feedback.
- **SC-004**: All interactive elements on the Tools page are reachable and operable via keyboard-only navigation.
- **SC-005**: The Tools page passes an automated accessibility audit (e.g., axe-core) with zero critical or serious violations.
- **SC-006**: The page layout renders correctly without overflow or broken elements at viewport widths 768px, 1024px, 1440px, and 1920px.
- **SC-007**: The page is fully usable in both light and dark themes with all text meeting WCAG AA contrast ratios (4.5:1 minimum).
- **SC-008**: The linter reports zero warnings and the type checker reports zero errors across all Tools page files.
- **SC-009**: The Tools page file is 250 lines or fewer.
- **SC-010**: Automated test coverage exists for all custom hooks (happy path, error, loading, empty states) and key interactive components.
- **SC-011**: No `any` types, type assertions, dead code, console.log statements, or magic strings remain in Tools page files.
- **SC-012**: All error messages shown to users follow the "Could not [action]. [Reason]. [Next step]." format — no raw error codes or stack traces.
