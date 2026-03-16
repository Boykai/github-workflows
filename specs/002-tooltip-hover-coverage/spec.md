# Feature Specification: Deep UI/UX Tooltip & Hover Coverage

**Feature Branch**: `002-tooltip-hover-coverage`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Full-coverage tooltip and hover UX across all 8 pages and all component groups. Three-tier approach: install missing Radix primitives, fill every gap per component, then validate consistency, motion, and accessibility."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Icon-Only Button Discoverability (Priority: P1)

A new user navigates the application for the first time and encounters icon-only buttons throughout the interface — in the sidebar navigation, pipeline builder toolbar, agent card actions, board column headers, and settings page. The user hovers over each icon button and a descriptive tooltip appears within 300 milliseconds, clearly explaining the button's purpose. This eliminates guesswork and reduces onboarding friction across every page.

**Why this priority**: Icon-only buttons without tooltips are the most common usability gap. Users cannot perform core actions if they do not understand what buttons do. This story covers the highest-traffic interaction pattern across all 8 pages.

**Independent Test**: Can be fully tested by navigating to each page, hovering over every icon-only button, and verifying a tooltip appears with accurate, consistent text. Delivers immediate discoverability value.

**Acceptance Scenarios**:

1. **Given** the sidebar is collapsed, **When** a user hovers over any navigation icon, **Then** a styled tooltip appears within 300ms showing the page name (e.g., "Projects", "Agents", "Pipeline")
2. **Given** the pipeline builder is open, **When** a user hovers over a drag handle on an AgentNode, **Then** a tooltip reads "Drag to reorder"
3. **Given** the agents page is displayed, **When** a user hovers over the expand/collapse toggle on an AgentCard, **Then** a tooltip reads "Expand agent details" or "Collapse agent details" depending on current state
4. **Given** any page with icon-only actions, **When** a user tabs to an icon button via keyboard, **Then** the same tooltip appears on focus as it does on hover
5. **Given** any interactive element that previously used native browser `title=` attributes, **When** a user hovers over it, **Then** a styled tooltip from the centralized registry appears instead of the browser-native tooltip

---

### User Story 2 — Rich Entity Previews via Hover Cards (Priority: P2)

A user working on the pipeline builder hovers over an agent node and sees a rich preview card showing the agent's description, assigned model, available tools, and last-run status — without clicking or navigating away. The same pattern applies to agent cards on the Agents page (showing description snippet, active tools, run count), issue cards on the Board (showing full title, assignees, labels, pipeline stage), and @agent-name mentions in the chat composer.

**Why this priority**: Rich hover previews reduce navigation depth and context-switching. Users can scan and compare entities quickly without opening detail views. This is a high-value feature for power users managing complex pipelines and boards.

**Independent Test**: Can be tested by hovering over specific entity elements and verifying the hover card displays correct, complete data. Each entity type (agent node, agent card, issue card, mention chip) can be tested independently.

**Acceptance Scenarios**:

1. **Given** the pipeline builder is open, **When** a user hovers over an AgentNode for 300ms, **Then** a hover card appears showing agent description, model name, list of tools, and last-run status
2. **Given** the agents page is displayed, **When** a user hovers over an AgentCard name or avatar, **Then** a hover card shows the agent's description snippet, active tools count, and total run count
3. **Given** the project board is displayed, **When** a user hovers over an IssueCard with a truncated title, **Then** a hover card shows the full title, assignees, labels, and current pipeline stage
4. **Given** the chat composer has an @agent-name mention chip, **When** a user hovers over it, **Then** a hover card shows an agent preview with description and tools
5. **Given** a user moves the mouse away from a hover card trigger, **Then** the card fades out after 150ms, allowing the user to move into the card before it closes
6. **Given** the user has enabled reduced-motion preferences, **When** a hover card opens or closes, **Then** no slide or fade animation plays; the card appears and disappears instantly

---

### User Story 3 — Accessible Popover Menus (Priority: P2)

A user interacts with dropdown-style menus throughout the application — the model selector in the pipeline builder, the add-agent popover on the board, and the agent preset selector. Each popover opens on click, traps keyboard focus inside, closes when pressing Escape, and returns focus to the trigger button. Screen readers announce the popover state correctly.

**Why this priority**: Manually built popovers lack consistent keyboard navigation and focus management, creating accessibility barriers for keyboard and assistive technology users. Migrating to a standardized popover component ensures WCAG 2.1 AA compliance across all overlay menus.

**Independent Test**: Can be tested by clicking each popover trigger, verifying focus is trapped, pressing Escape to close, and confirming focus returns to the trigger. Automated accessibility scans detect missing ARIA attributes.

**Acceptance Scenarios**:

1. **Given** the pipeline builder is open, **When** a user clicks the model selector, **Then** a popover opens with focus trapped inside, and pressing Escape closes it and returns focus to the trigger button
2. **Given** the board page is displayed, **When** a user clicks "Add Agent", **Then** a popover appears with the agent list, `aria-haspopup="true"` is set on the trigger, and `aria-expanded` reflects the open state
3. **Given** any popover is open, **When** a user clicks outside the popover boundary, **Then** the popover closes
4. **Given** any popover is open, **When** a user presses Tab repeatedly, **Then** focus cycles within the popover content and does not escape to elements behind it

---

### User Story 4 — Consistent Hover Styling Across All Cards (Priority: P3)

A user scans the interface and sees a visually consistent hover treatment across all interactive card surfaces — agent cards, issue cards, tool cards, chore cards, agent nodes, and stage cards. Hovering over any card produces a subtle ring highlight and background accent shift. Drag handles appear on hover with a grab cursor, and drop zones visually respond when a draggable item is held over them.

**Why this priority**: Visual consistency reinforces learnability. When hover states look and behave the same everywhere, users build accurate mental models faster. Drag-and-drop affordances reduce trial-and-error for reordering operations.

**Independent Test**: Can be tested by hovering over each card type across different pages and verifying identical visual feedback. Drag handle visibility can be tested by hovering over draggable items.

**Acceptance Scenarios**:

1. **Given** any page with interactive cards, **When** a user hovers over a card, **Then** a consistent ring highlight and background accent shift appears
2. **Given** a draggable item (agent node, execution group, stage card, chore row), **When** a user hovers over it, **Then** a drag-handle icon becomes visible and the cursor changes to a grab cursor
3. **Given** a drag operation is in progress, **When** the user drags an item over a valid drop zone, **Then** the drop zone displays a distinct visual highlight indicating it will accept the drop
4. **Given** the user is not hovering over a draggable item, **Then** the drag handle icon is hidden to reduce visual clutter

---

### User Story 5 — Tooltip Registry Completeness and Accuracy (Priority: P3)

A content editor or developer audits the tooltip registry and finds that every tooltip key used in the application has a corresponding entry, no orphaned keys exist without a matching component reference, and all tooltip copy matches the UI labels exactly (e.g., "execution group" not "group", "stage" not "column").

**Why this priority**: Registry hygiene prevents stale or missing tooltip text and ensures the application is ready for future localization without rework. Consistent terminology reduces user confusion.

**Independent Test**: Can be tested by running an automated check that compares registry keys to `contentKey=` usages in the codebase, and by verifying tooltip text against on-screen UI labels.

**Acceptance Scenarios**:

1. **Given** the tooltip content registry, **When** an audit tool scans for orphaned keys, **Then** every key in the registry has at least one corresponding `contentKey=` usage in the codebase
2. **Given** the codebase, **When** a search is performed for `title=` on interactive elements (buttons, links, toggles), **Then** zero results are found (`title=` is only permitted on non-interactive truncated text)
3. **Given** any tooltip text, **When** compared to the UI label of its associated element, **Then** the terminology matches exactly

---

### Edge Cases

- What happens when a tooltip trigger is near the edge of the viewport? The tooltip must reposition to remain fully visible (collision detection with appropriate padding).
- How does the system handle hover cards when the underlying data is still loading? A lightweight loading skeleton should appear inside the hover card.
- What happens when a user rapidly moves between multiple tooltip triggers? The global tooltip delay should prevent flicker — once one tooltip has been shown, subsequent tooltips in the same session appear faster (skip-delay behavior).
- How do tooltips behave on touch devices? Tooltips are hover-only and do not fire on touch. If mobile support is planned, hover cards need a tap-to-expand fallback. For now, touch users rely on visible labels and aria-labels.
- What happens when a popover trigger is inside a scrollable container and the user scrolls while the popover is open? The popover should reposition or close gracefully.
- How does the system handle very long tooltip text? Tooltip content is constrained to a maximum width with text wrapping; content exceeding reasonable length should be moved to a hover card instead.

## Requirements *(mandatory)*

### Functional Requirements

**Infrastructure**

- **FR-001**: System MUST provide a reusable hover card component that displays rich JSX content (text, lists, badges, status indicators) when a user hovers over a trigger element, with a configurable open delay (default 300ms) and close delay (default 150ms)
- **FR-002**: System MUST provide a reusable popover component that opens on click, traps keyboard focus, closes on outside click or Escape key, and returns focus to the trigger element on close
- **FR-003**: Both hover card and popover components MUST respect the user's `prefers-reduced-motion` setting by disabling all entrance/exit animations when reduced motion is preferred
- **FR-004**: System MUST wrap the application with any required providers for hover cards, alongside the existing tooltip provider

**Tooltip Coverage**

- **FR-005**: Every icon-only button across all 8 pages MUST display a descriptive tooltip on hover and keyboard focus, sourced from the centralized tooltip content registry
- **FR-006**: All sidebar navigation icon-only items MUST use the styled tooltip component instead of native browser `title=` attributes
- **FR-007**: All tooltips MUST appear within 300ms of hover or focus, with an option to reduce delay to 0ms for dense interaction areas (e.g., pipeline builder)
- **FR-008**: System MUST add tooltip registry entries for all identified gaps: drag handles (pipeline agent, execution group, stage), clone buttons, agent card actions (icon, expand/collapse), tools editor actions (move-up, move-down, remove), bulk model update scope selector, voice input stop state, board filter/sort buttons, column header actions, tool card re-sync, config panel field help, config generator copy, search input, temperature slider explanation, provider toggle explanation, theme toggle, Signal QR button, and destructive reset action warnings

**Hover Cards**

- **FR-009**: AgentNode in the pipeline builder MUST show a hover card with agent description, model name, tools list, and last-run status
- **FR-010**: AgentCard on the agents page MUST show a hover card with description snippet, active tools, and run count when hovering over the name or avatar
- **FR-011**: IssueCard on the board MUST show a hover card with full title (if truncated), assignees, labels, and pipeline stage
- **FR-012**: @agent-name mention chips in the chat composer MUST show a hover card with an agent preview

**Popover Migration**

- **FR-013**: The pipeline model selector MUST be migrated from its manual dropdown implementation to the standardized popover component
- **FR-014**: The board's add-agent overlay MUST be migrated to the standardized popover component
- **FR-015**: The board's agent preset selector MUST be migrated to the standardized popover component
- **FR-016**: All migrated popovers MUST set `aria-haspopup` and `aria-expanded` correctly on their trigger elements
- **FR-017**: System MUST audit the codebase for any remaining manual open/close toggle patterns (state-managed visibility with absolutely positioned containers) and migrate them to the standardized popover

**Hover Styling**

- **FR-018**: All interactive card surfaces (agent cards, issue cards, tool cards, chore cards, agent nodes, stage cards) MUST display a uniform hover state with consistent ring highlight and background accent
- **FR-019**: All draggable items (agent nodes, execution group cards, stage cards, chore rows) MUST show a drag-handle icon on hover that is hidden when not hovered, with a grab cursor
- **FR-020**: All drop zone targets MUST display a distinct visual highlight when a draggable item is held over them

**Registry & Consistency**

- **FR-021**: The tooltip content registry MUST contain no orphaned keys — every key must have at least one corresponding usage in the codebase
- **FR-022**: No interactive element (button, link, toggle) in the application MUST use the native HTML `title=` attribute; `title=` is permitted only on non-interactive elements displaying truncated text
- **FR-023**: All tooltip copy MUST match the exact terminology used in the UI labels (e.g., "execution group" not "group", "stage" not "column")

**Accessibility**

- **FR-024**: Every icon-only button MUST have an `aria-label` attribute whose text matches its tooltip content
- **FR-025**: All tooltip triggers MUST be reachable via keyboard Tab navigation
- **FR-026**: All popovers MUST trap focus and return focus to the trigger on close
- **FR-027**: The application MUST pass automated accessibility scanning with zero violations across all pages

### Key Entities

- **Tooltip Registry Entry**: A centralized record mapping a dot-notation key (e.g., `pipeline.agent.dragHandle`) to tooltip content including a required summary, optional title, and optional learn-more URL. Used for consistent text management and future localization.
- **Hover Card**: A rich preview overlay triggered by hovering over an entity reference. Contains structured data (description, metadata, status) specific to the entity type (agent, issue, tool). Distinct from tooltips in that it supports complex JSX content and interactive elements.
- **Popover**: A click-triggered overlay menu that contains interactive content (lists, forms, selectors). Focus-trapped with keyboard navigation support. Distinct from hover cards (hover-triggered, informational) and tooltips (simple text).

## Assumptions

- The existing Radix Tooltip provider and `tooltip-content.ts` registry pattern will continue to serve as the foundation; new components (hover card, popover) will follow the same architectural patterns.
- The Celestial design language tokens (colors, spacing, animation) will be used for all new components to maintain visual consistency.
- Standard web application performance expectations apply: tooltips appear within 300ms, hover cards within 300ms, popovers open instantly on click.
- Error handling for hover card data follows existing patterns: loading skeletons for async data, graceful degradation if data is unavailable.
- Mobile/touch support is out of scope for this feature. Tooltips and hover cards are desktop hover-only patterns. If touch support is planned later, it will be addressed as a separate feature.
- The existing `tooltipAwareRender()` test utility will be extended to support hover card and popover testing.
- The i18n-ready structure of the registry (`{area}.{section}.{element}` keys) is preserved; no translation work is included in this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of icon-only buttons across all 8 pages display a styled tooltip on hover — verified by navigating every page and hovering over each icon button
- **SC-002**: Zero interactive elements use native HTML `title=` attributes — verified by codebase search returning zero matches on buttons, links, and toggles
- **SC-003**: Every icon-only button has both an `aria-label` and a corresponding tooltip with matching text — verified by automated accessibility scan
- **SC-004**: All 4 entity types (agent node, agent card, issue card, mention chip) display rich hover cards with correct, complete data on hover
- **SC-005**: All migrated popovers (model selector, add-agent, agent preset, plus any additional manual overlays found during audit) close on Escape, trap focus, and return focus to trigger — verified by keyboard-only navigation testing
- **SC-006**: Automated accessibility scan reports zero violations across all 8 pages
- **SC-007**: No animations play when the user has enabled `prefers-reduced-motion` — verified by toggling the OS-level reduced motion setting and observing hover cards and popovers
- **SC-008**: All draggable items show a drag handle icon on hover with a grab cursor, and all drop zones show visual feedback when an item is dragged over them
- **SC-009**: The tooltip content registry contains zero orphaned keys — verified by comparing registry entries to `contentKey=` usages in the codebase
- **SC-010**: Users can discover the purpose of any icon-only button within 300ms of hovering, reducing guesswork and improving onboarding task completion rate
