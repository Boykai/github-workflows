# Feature Specification: Remove "Current Pipeline" Section from Pipeline Page

**Feature Branch**: `038-remove-current-pipeline`  
**Created**: 2026-03-12  
**Status**: Draft  
**Input**: User description: "Remove the 'Current Pipeline' section from the Pipeline page as part of a UI cleanup effort. This is a straightforward front-end change tagged as an easy task."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Pipeline Page Displays Without "Current Pipeline" Section (Priority: P1)

A user navigates to the Pipeline page to view and manage their pipeline configuration. The page loads and displays all pipeline management features — pipeline stages visualization, pipeline toolbar, save controls, and flow graph — but no longer shows the "Current Pipeline" section that previously displayed an agent configuration row with drag-and-drop agent assignment. The page layout is clean and cohesive with no empty gaps or orphaned whitespace where the section used to appear.

**Why this priority**: This is the core deliverable of the feature. Removing the visible "Current Pipeline" section is the primary user-facing change and the entire purpose of this cleanup effort. Without this, the feature has not been delivered.

**Independent Test**: Can be fully tested by navigating to the Pipeline page and verifying that the "Current Pipeline" heading and its associated agent configuration row are not rendered. The page should display pipeline stages and other sections with proper spacing.

**Acceptance Scenarios**:

1. **Given** a user has a project with a configured pipeline, **When** they navigate to the Pipeline page, **Then** the "Current Pipeline" section (including its heading and agent configuration row) is not visible anywhere on the page.
2. **Given** a user navigates to the Pipeline page, **When** the page finishes loading, **Then** the layout renders cleanly with no empty gaps, orphaned spacing, or visual artifacts where the "Current Pipeline" section previously appeared.
3. **Given** a user navigates to the Pipeline page, **When** they inspect the page, **Then** no console errors or warnings are introduced by the removal of the section.

---

### User Story 2 — Remaining Pipeline Page Features Continue to Function Correctly (Priority: P1)

A user interacts with all remaining features on the Pipeline page after the "Current Pipeline" section has been removed. The pipeline stages visualization, pipeline toolbar, save/discard controls, flow graph, model override dropdown, and all other pipeline management features continue to work exactly as before — no regressions in functionality, no broken interactions, and no missing data.

**Why this priority**: Ensuring existing functionality is preserved is equally critical to the removal itself. A removal that breaks adjacent features would be worse than leaving the section in place.

**Independent Test**: Can be fully tested by exercising all remaining Pipeline page features — adding/removing agents via the pipeline stages section, saving pipeline configurations, using the toolbar controls, viewing the flow graph — and verifying each operates correctly.

**Acceptance Scenarios**:

1. **Given** the "Current Pipeline" section has been removed, **When** a user interacts with the pipeline stages visualization (adding or removing agents from stages), **Then** all drag-and-drop and assignment interactions work correctly.
2. **Given** the "Current Pipeline" section has been removed, **When** a user saves or discards pipeline changes, **Then** the save and discard operations complete successfully without errors.
3. **Given** the "Current Pipeline" section has been removed, **When** a user views the pipeline flow graph, **Then** the flow graph renders correctly and reflects the current pipeline configuration.
4. **Given** the "Current Pipeline" section has been removed, **When** the full application test suite is run, **Then** all existing tests pass with zero new failures.

---

### User Story 3 — No Residual Code from "Current Pipeline" Section Remains (Priority: P2)

A developer reviews the codebase after the removal. All code exclusively serving the "Current Pipeline" section — including unused component imports, orphaned variables, unused styles, and dead conditional logic — has been cleaned up. The codebase is left in a tidy state with no unnecessary artifacts.

**Why this priority**: Code cleanup is important for maintainability but ranks below the user-facing removal and functional preservation. Residual dead code creates confusion for future developers but does not affect users directly.

**Independent Test**: Can be fully tested by reviewing the changed files for unused imports, variables, and styles, and by running linting and build tools to verify no warnings about unused code are introduced.

**Acceptance Scenarios**:

1. **Given** the "Current Pipeline" section has been removed from the page, **When** a developer reviews the Pipeline page source file, **Then** no imports, variables, props, or logic that were exclusively used by the "Current Pipeline" section remain.
2. **Given** the removal is complete, **When** the project is built, **Then** the build completes successfully with no new warnings about unused code.
3. **Given** the removal is complete, **When** a linter is run against the changed files, **Then** no new linting violations are introduced.

---

### Edge Cases

- What happens if the "Current Pipeline" section shares state, props, or data-fetching logic with other sections on the Pipeline page? Only the section's rendering and any code *exclusively* used by it should be removed. Shared logic must be preserved.
- What happens if removing the section changes the vertical layout or scroll behavior of the page? The surrounding content should flow naturally to fill the space, with no extra padding or margins creating visual gaps.
- What happens if tests specifically assert on the presence of the "Current Pipeline" section? Those test assertions must be updated or removed to reflect the new expected state of the page.
- What happens if the "Current Pipeline" section is conditionally rendered based on feature flags or configuration? The conditional check and the section itself should both be removed entirely.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST NOT render the "Current Pipeline" section (heading and agent configuration row) on the Pipeline page.
- **FR-002**: System MUST preserve all other Pipeline page sections and features — including pipeline stages visualization, toolbar, save/discard controls, flow graph, and model override dropdown — in fully working condition.
- **FR-003**: System MUST render the Pipeline page layout without empty gaps, extra whitespace, or visual artifacts where the "Current Pipeline" section previously appeared.
- **FR-004**: System MUST NOT introduce any new console errors or warnings as a result of the removal.
- **FR-005**: System MUST remove all code (imports, variables, components, styles, and logic) that was exclusively used to render the "Current Pipeline" section.
- **FR-006**: System MUST NOT remove any code that is shared with or used by other sections of the Pipeline page or other parts of the application.
- **FR-007**: System MUST pass all existing automated tests after the removal, with updates only to tests that specifically asserted on the removed section.

### Assumptions

- The "Current Pipeline" section refers specifically to the `AgentConfigRow` component rendered with `title="Current Pipeline"` on the Pipeline page.
- The `AgentConfigRow` component itself may be used elsewhere in the application and MUST NOT be deleted — only its usage within the Pipeline page for the "Current Pipeline" section should be removed.
- No backend or API changes are required for this removal, as the "Current Pipeline" section is a front-end-only display concern.
- The associated `AddAgentPopover` rendered inside the "Current Pipeline" section's `renderAddButton` prop is also used in the pipeline stages section and must not be removed from the codebase.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users visiting the Pipeline page see zero trace of a "Current Pipeline" section — the heading, agent configuration row, and add-agent controls from that section are completely absent.
- **SC-002**: All remaining Pipeline page features (stages visualization, toolbar, save, flow graph) function identically to their pre-removal behavior with zero regressions.
- **SC-003**: The application builds and all automated tests pass with zero new failures after the removal.
- **SC-004**: Zero new console errors or warnings appear when loading and interacting with the Pipeline page after the removal.
- **SC-005**: A code review confirms that no unused imports, variables, or dead code exclusively tied to the removed section remain in the changed files.
