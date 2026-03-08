# Feature Specification: Fix Tooltip Z-Index & Component Layer Audit for Correct Stacking Order

**Feature Branch**: `031-tooltip-zindex-audit`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "Update tool tips so they are on the top layer, they are hidden by other components. Do a deep check of all components, ensure they are on the right layer for best UX."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tooltips Always Visible Above All UI Elements (Priority: P1)

As a user of Project Solune, I want tooltips to always appear fully visible on the topmost visual layer so that I can read helpful context without it being obscured by modals, sidebars, panels, dropdowns, or any other overlapping UI element.

Currently, tooltips are being clipped or hidden behind sibling or parent components, making them unreadable and degrading the user experience. This story addresses the core bug: tooltips must float above everything.

**Why this priority**: This is the primary user-reported problem. Tooltips that are hidden provide zero value and actively frustrate users who rely on them for guidance. Fixing this delivers immediate, visible improvement.

**Independent Test**: Can be fully tested by hovering over any tooltip-triggering element across all UI surfaces (agent pipeline views, chat panels, configuration pages, modal dialogs) and confirming the tooltip is fully visible and not clipped or hidden by any other element.

**Acceptance Scenarios**:

1. **Given** a user is viewing an agent pipeline page with overlapping panels, **When** the user hovers over an element with a tooltip, **Then** the tooltip appears fully visible above all other UI elements on screen.
2. **Given** a modal dialog is open, **When** the user hovers over a tooltip-triggering element inside the modal, **Then** the tooltip renders above the modal and is fully readable.
3. **Given** a tooltip-triggering element is inside a scrollable container, **When** the user hovers over it, **Then** the tooltip is not clipped or cut off by the container boundaries.
4. **Given** a sidebar or dropdown menu is open, **When** a tooltip is triggered on an element near or behind the sidebar/dropdown, **Then** the tooltip is displayed above the sidebar/dropdown.

---

### User Story 2 - Consistent Stacking Order Across All Components (Priority: P2)

As a user of Project Solune, I want all UI components to be layered in a clear, intentional order (e.g., base content → sticky headers → dropdowns → modals → tooltips → notifications) so that overlapping elements never obscure each other in unexpected or confusing ways.

A comprehensive audit of all components is needed to identify and correct any component that has an incorrect visual layer, creates an unintended stacking trap, or causes child elements to be hidden.

**Why this priority**: While the tooltip fix (P1) addresses the most visible symptom, this story addresses the root cause — an inconsistent and undocumented stacking order across the application. Without this, new tooltip-like issues will recur as new components are added.

**Independent Test**: Can be tested by navigating through all major UI surfaces and interacting with overlapping elements (opening dropdowns near modals, triggering overlays near sidebars, etc.) and confirming that every component appears at its correct visual depth.

**Acceptance Scenarios**:

1. **Given** a user opens a dropdown menu near a sticky header, **When** the dropdown expands, **Then** the dropdown appears above the sticky header content.
2. **Given** a user opens a modal dialog, **When** the modal is displayed, **Then** it renders above all base content, sticky headers, and dropdowns.
3. **Given** a notification appears while a modal is open, **When** both are visible simultaneously, **Then** the notification is displayed above the modal.
4. **Given** any component that previously created an unintended stacking context, **When** that component is rendered, **Then** its child elements (especially tooltips and overlays) are not trapped beneath other elements.

---

### User Story 3 - Documented Layer Scale for Future Maintainability (Priority: P3)

As a developer working on Project Solune, I want a centralized, documented layer scale that defines the intended stacking order for all UI component categories so that I can assign the correct layer to new components without guessing or creating conflicts.

**Why this priority**: This is a quality-of-life improvement for developers that prevents future regressions. It builds on the audit (P2) by formalizing the corrected stacking order into a reusable, documented system.

**Independent Test**: Can be tested by verifying that a centralized layer scale document/reference exists, that all components in the codebase reference it consistently, and that a new developer can determine the correct layer for a new component by consulting the scale.

**Acceptance Scenarios**:

1. **Given** a developer needs to add a new overlay component, **When** they consult the layer scale documentation, **Then** they can determine the correct stacking level without inspecting other component styles.
2. **Given** the layer scale is defined, **When** all existing components are reviewed, **Then** every component's layer assignment matches the documented scale.
3. **Given** a component's layer assignment is changed, **When** the change is reviewed, **Then** reviewers can verify correctness by referencing the centralized scale.

---

### Edge Cases

- What happens when multiple tooltips are triggered simultaneously (e.g., via keyboard focus navigation)? Each tooltip must render on the topmost layer without obscuring other active tooltips.
- What happens when a tooltip-triggering element is positioned at the very edge of the viewport? The tooltip must remain fully visible and not be clipped by the viewport boundary.
- What happens when a tooltip appears inside a deeply nested component hierarchy with multiple stacking contexts? The tooltip must still render above all other elements regardless of nesting depth.
- How does the system handle tooltips inside components that use visual effects (e.g., opacity transitions, transforms, or filters) that may create new stacking contexts? Tooltips must not be trapped by these effects.
- What happens when the user scrolls while a tooltip is visible? The tooltip should either follow its trigger element or dismiss gracefully — it must not become orphaned or overlap incorrectly.
- What happens when a modal is dismissed while a tooltip inside it is still visible? The tooltip must be dismissed along with the modal and not linger on screen.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render all tooltip components on the highest visual layer, above modals, panels, sidebars, dropdowns, overlays, and any other overlapping UI elements.
- **FR-002**: System MUST perform a comprehensive audit of every UI component to identify incorrect layer assignments or unintended stacking context creation caused by visual effect properties (such as transforms, partial opacity, filters, will-change, or isolation).
- **FR-003**: System MUST establish a centralized layer scale that defines the intended stacking order for all component categories (e.g., base content → sticky headers → dropdowns → modals → tooltips → notifications).
- **FR-004**: System MUST document the centralized layer scale so that all current and future components reference consistent, intentional layer values.
- **FR-005**: System MUST fix any component discovered during the audit that creates a stacking context trapping tooltip or overlay children, without breaking the component's intended visual behavior.
- **FR-006**: System MUST ensure tooltips are not clipped by ancestor elements that restrict visible overflow, by rendering tooltips at a top-level position in the document structure.
- **FR-007**: System MUST regression-test all affected components after layer changes to confirm no visual regressions in layout, spacing, or interactive states.
- **FR-008**: System SHOULD validate all fixes across the full range of UI surfaces including agent pipeline views, chat panels, configuration pages, and modal dialogs.
- **FR-009**: System SHOULD include inline documentation on layer assignments to clarify the intended stacking order for future developers.

### Key Entities

- **Layer Scale**: A defined hierarchy of visual stacking levels that categorizes all UI components into ordered tiers (e.g., base content, sticky elements, dropdowns, modals, tooltips, notifications). Each tier has a clear position relative to others.
- **Stacking Context**: A conceptual grouping created by certain visual properties that constrains the layering of child elements. Components that inadvertently create stacking contexts can trap child elements at lower visual layers.
- **UI Component**: Any visual element in the application that participates in the stacking order, including but not limited to: tooltips, modals, sidebars, panels, cards, dropdowns, overlays, sticky headers, and notifications.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tooltips are fully visible and readable 100% of the time across all UI surfaces, with zero instances of tooltips being hidden, clipped, or obscured by other UI elements.
- **SC-002**: All UI components follow a single, documented layer scale — no component has a layer assignment that conflicts with the defined hierarchy.
- **SC-003**: Zero visual regressions are introduced by the layer changes — all existing layouts, spacing, and interactive states remain unchanged.
- **SC-004**: A new developer can determine the correct layer for any new component type in under 1 minute by consulting the centralized layer scale documentation.
- **SC-005**: All UI surfaces (agent pipeline views, chat panels, configuration pages, modal dialogs) pass manual visual inspection with no stacking order issues.
- **SC-006**: No component in the codebase creates an unintended stacking context that traps child tooltips or overlays at an incorrect visual depth.

## Assumptions

- Tooltips are the highest priority interactive visual layer, positioned above modals and below only persistent system notifications.
- The existing tooltip behavior (positioning logic, animation, content) should not change — only the visual layering is being corrected.
- All current UI surfaces in the application should be included in the audit scope, not just the surfaces where the bug was initially reported.
- The centralized layer scale applies to all current components and should be designed to accommodate future components without modification to the scale itself.
- The branch `copilot/add-comprehensive-tooltips-ui` may contain related tooltip work and should be reviewed for conflicts or reuse opportunities before implementation begins.
- Standard web application stacking conventions will be followed for the layer hierarchy (content → headers → dropdowns → modals → tooltips → notifications).
