# Feature Specification: Deep UI/UX Tooltip & Hover Coverage

**Feature Branch**: `002-tooltip-hover-ux`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Full-coverage tooltip and hover UX across all 8 pages and all component groups. Three-tier approach: install missing Radix primitives, fill every gap per component, then validate consistency, motion, and accessibility."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Icon-Only Button Tooltips Across All Pages (Priority: P1)

A user navigating the application encounters numerous icon-only buttons (sidebar navigation, drag handles, clone buttons, action icons in toolbars). Currently many of these buttons lack tooltips, forcing users to guess their purpose. After this feature, every icon-only button displays a descriptive tooltip on hover within 300 milliseconds, using consistent language drawn from a centralized content registry.

**Why this priority**: Icon-only buttons without tooltips are the single largest usability gap. Users cannot discover functionality they cannot name. This story eliminates guesswork across every page and directly improves discoverability for new and returning users alike.

**Independent Test**: Can be fully tested by tabbing through or hovering over every icon-only button in the application and verifying that a tooltip appears with correct descriptive text. Delivers immediate value: users understand what every button does.

**Acceptance Scenarios**:

1. **Given** a user is on the Pipeline Builder page, **When** they hover over the drag handle on an AgentNode, **Then** a tooltip reading "Drag to reorder agent" appears within 300 ms.
2. **Given** a user is on the Agents page, **When** they hover over the expand/collapse toggle on an AgentCard, **Then** a tooltip reading "Expand agent details" (or "Collapse agent details") appears within 300 ms.
3. **Given** a user is viewing the sidebar in collapsed mode, **When** they hover over any icon-only navigation item (Projects, Agents, Pipeline, Chores, Tools, Settings), **Then** a tooltip with the page name appears within 300 ms.
4. **Given** a user is on the Settings page, **When** they hover over the theme toggle, **Then** a tooltip appears (not a browser-native `title` attribute popup).
5. **Given** a user navigates entirely by keyboard, **When** they Tab-focus onto any icon-only button, **Then** the same tooltip text is exposed via `aria-label` to screen readers.

---

### User Story 2 — Rich Entity Hover Cards (Priority: P2)

A user working with agents, issues, or models wants quick context without navigating away from their current view. After this feature, hovering over an agent name/avatar, an issue card, or a model reference displays a rich hover card showing a preview of that entity's key information (description, tools, status, labels, etc.). The hover card appears after a short delay, stays visible while the cursor remains over it, and disappears gracefully when the cursor moves away.

**Why this priority**: Rich hover previews reduce navigation friction and give power users rapid context. They transform the application from a "click-to-discover" model into a "glance-to-understand" model, significantly improving workflow speed for users managing multiple agents or triaging issues.

**Independent Test**: Can be fully tested by hovering over agent names in the Pipeline Builder, agent cards on the Agents page, issue cards on the Board, and `@agent-name` chips in Chat, and verifying that a rich preview card with correct entity data appears.

**Acceptance Scenarios**:

1. **Given** a user is on the Pipeline Builder, **When** they hover over an AgentNode for 300 ms, **Then** a hover card appears showing the agent's description, assigned model, configured tools, and last-run status.
2. **Given** a user is on the Agents page, **When** they hover over an AgentCard name or avatar, **Then** a hover card appears showing a description snippet, list of active tools, and run count.
3. **Given** a user is on the Board page, **When** they hover over a truncated IssueCard, **Then** a hover card appears showing the full title, assignees, labels, and current pipeline stage.
4. **Given** a user is composing a chat message, **When** they hover over an `@agent-name` mention chip, **Then** a hover card appears showing a compact agent preview.
5. **Given** the user has enabled reduced-motion preferences in their operating system, **When** a hover card appears, **Then** it renders without any slide or fade animation.

---

### User Story 3 — Popover Migration for Consistency and Accessibility (Priority: P2)

Several components (ModelSelector, AddAgentPopover, AgentPresetSelector) use manually implemented dropdown/overlay patterns with custom open/close state management. These manual implementations have inconsistent keyboard behavior — some don't close on Escape, some don't return focus to the trigger, and some lack proper ARIA attributes. After this feature, all popover-style overlays use a shared, accessible popover primitive that is focus-trapped, closes on outside click or Escape, and correctly manages `aria-haspopup` and `aria-expanded`.

**Why this priority**: Accessibility compliance and interaction consistency are fundamental to a professional UX. Manual overlay implementations create maintenance burden and introduce accessibility regressions. Migrating to a shared primitive eliminates an entire class of bugs.

**Independent Test**: Can be fully tested by opening each popover-style overlay, verifying Escape closes it, verifying focus returns to the trigger, and running an accessibility audit confirming `aria-haspopup` and `aria-expanded` are correctly set.

**Acceptance Scenarios**:

1. **Given** a user opens the ModelSelector dropdown on the Pipeline Builder, **When** they press Escape, **Then** the dropdown closes and focus returns to the trigger button.
2. **Given** a user opens the AddAgentPopover on the Board page, **When** they click outside the popover, **Then** the popover closes.
3. **Given** a screen reader user interacts with any popover trigger, **When** the popover is closed, **Then** the trigger has `aria-haspopup="dialog"` and `aria-expanded="false"`. **When** the popover is open, **Then** `aria-expanded="true"`.
4. **Given** a user opens any popover, **When** they press Tab repeatedly, **Then** focus cycles within the popover content (focus trap) and does not escape to background elements.

---

### User Story 4 — Uniform Hover Styling and Drag Affordances (Priority: P3)

Interactive cards and draggable elements across the application use inconsistent hover styles — some show a ring, some change background, some show no visual change. Drag handles are invisible until interaction. After this feature, all interactive card surfaces (AgentCard, IssueCard, ToolCard, ChoreCard, AgentNode, StageCard) share a uniform hover style, and all draggable items display a visible drag-handle icon on hover with an appropriate cursor.

**Why this priority**: Visual consistency reinforces user confidence and learnability. Uniform hover states communicate interactivity, and visible drag handles reduce the discovery cost of drag-and-drop functionality. This is a polish layer that builds on the functional improvements in P1–P2.

**Independent Test**: Can be fully tested by hovering over each card type and draggable element across all pages and visually confirming consistent hover ring/background and drag handle visibility.

**Acceptance Scenarios**:

1. **Given** a user hovers over an AgentCard on the Agents page, **When** the cursor enters the card boundary, **Then** a consistent hover ring and subtle background shift appear matching the same style used on IssueCard, ToolCard, and all other interactive cards.
2. **Given** a user hovers over a draggable AgentNode in the Pipeline Builder, **When** the cursor enters the node, **Then** a drag-handle icon becomes visible and the cursor changes to a grab cursor.
3. **Given** a user is dragging an item over a valid drop zone, **When** the item enters the drop zone boundary, **Then** the drop zone displays a distinct visual indicator (ring or background shift) signaling it can accept the drop.

---

### User Story 5 — Tooltip Content Registry Completeness and Consistency (Priority: P3)

The centralized tooltip content registry serves as the single source of truth for all tooltip text in the application. After this feature, the registry contains entries for every tooltip in the application, organized by a consistent `{area}.{section}.{element}` naming convention. Orphaned keys (registry entries with no corresponding UI usage) are removed. All tooltip text uses exact UI terminology (e.g., "execution group" not "group").

**Why this priority**: A complete, clean registry is the foundation for future localization (i18n) and ensures terminology consistency. It also prevents drift between tooltip text and UI labels over time. This is infrastructure that supports long-term maintainability.

**Independent Test**: Can be fully tested by auditing the registry file for orphaned keys (keys with no `contentKey=` reference in any component), verifying every component tooltip references a registry key, and checking that registry text matches UI labels exactly.

**Acceptance Scenarios**:

1. **Given** a developer inspects the tooltip content registry, **When** they search the codebase for each registry key, **Then** every key has at least one corresponding `contentKey=` usage in a component.
2. **Given** a developer searches the codebase for `title=` attributes on interactive elements, **When** the search completes, **Then** zero results are found (all have been migrated to tooltip components).
3. **Given** a reviewer reads tooltip text for execution group elements, **When** they compare the tooltip text to the UI label, **Then** the text says "execution group" (not "group" or "exec group").

---

### Edge Cases

- What happens when a tooltip trigger element is removed from the DOM while the tooltip is visible (e.g., during a drag operation)? The tooltip must close gracefully without errors.
- How does the system handle hover cards for entities that are still loading data? A loading skeleton or brief loading indicator should appear inside the hover card.
- What happens when a user hovers over a truncated text element that is not truncated at the current viewport width? No tooltip should appear for text that is fully visible.
- How does the system behave when multiple hover cards or tooltips could trigger simultaneously (e.g., hovering over a nested element)? Only the most specific (innermost) tooltip should display.
- What happens when a popover is open and the user scrolls the page? The popover should reposition or close gracefully.
- How does the system handle tooltip display on touch devices where hover is not available? Tooltips should not interfere with tap interactions; hover cards may need a tap-to-expand fallback if mobile support is planned.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a descriptive tooltip on every icon-only button across all pages within 300 ms of hover or keyboard focus.
- **FR-002**: System MUST provide a shared hover card primitive that supports JSX-rich content, configurable open delay (default 300 ms) and close delay (default 150 ms), and fade/slide animation.
- **FR-003**: System MUST provide a shared popover primitive that is focus-trapped, closes on outside click or Escape keypress, and returns focus to the trigger element on close.
- **FR-004**: System MUST display rich hover cards on AgentNode (Pipeline Builder), AgentCard (Agents page), IssueCard (Board page), and `@agent-name` chips (Chat) showing relevant entity details.
- **FR-005**: System MUST centralize all tooltip text in a single content registry using the naming convention `{area}.{section}.{element}`.
- **FR-006**: System MUST replace all `title=` attributes on interactive elements with tooltip components. `title=` is permitted only on non-interactive truncated text.
- **FR-007**: System MUST migrate all manually implemented popover/overlay patterns (ModelSelector, AddAgentPopover, AgentPresetSelector) to the shared popover primitive.
- **FR-008**: System MUST apply a uniform hover style (consistent ring and background treatment) to all interactive card surfaces: AgentCard, IssueCard, ToolCard, ChoreCard, AgentNode, StageCard.
- **FR-009**: System MUST show a visible drag-handle icon on hover for all draggable elements (AgentNode, ExecutionGroupCard, StageCard, chore rows) with an appropriate grab cursor.
- **FR-010**: System MUST provide visual feedback on drop zones when a draggable item hovers over them (distinct ring or background shift).
- **FR-011**: System MUST ensure every icon-only button has an `aria-label` attribute whose text matches the corresponding tooltip text.
- **FR-012**: System MUST respect the user's `prefers-reduced-motion` setting by disabling all slide and fade animations on hover cards, popovers, and tooltips when reduced motion is preferred.
- **FR-013**: System MUST ensure all tooltip triggers are reachable via keyboard Tab navigation.
- **FR-014**: System MUST ensure all popovers are focus-trapped (Tab cycles within content) and set correct `aria-haspopup` and `aria-expanded` attributes on triggers.
- **FR-015**: System MUST add tooltip content registry entries for all elements identified in the component gap analysis, including but not limited to: drag handles, clone buttons, toolbar actions, sidebar navigation items, settings controls, and tool page actions.
- **FR-016**: System MUST remove orphaned keys from the tooltip content registry (keys with no corresponding UI usage).
- **FR-017**: System MUST ensure all tooltip copy uses exact UI terminology (e.g., "execution group" not "group", "stage" not "column").

### Key Entities

- **Tooltip Content Registry Entry**: A key-value pair in the centralized registry. Key follows `{area}.{section}.{element}` convention (e.g., `pipeline.agent.dragHandle`). Value is the user-facing tooltip text string. Each entry must have exactly one corresponding UI usage.
- **Hover Card Entity Preview**: A structured data display shown inside a hover card. Contains entity-specific fields: for agents (description, model, tools, last-run status), for issues (full title, assignees, labels, pipeline stage), for models (name, provider, capabilities).
- **Interactive Card Surface**: Any card component (AgentCard, IssueCard, ToolCard, ChoreCard, AgentNode, StageCard) that responds to user hover and click. Must share a uniform hover style token.

## Assumptions

- The existing Radix Tooltip is already installed with a global `TooltipProvider` and centralized tooltip content registry (`tooltip-content.ts`). This feature extends the existing foundation rather than replacing it.
- The existing `tooltipAwareRender()` test utility will continue to work and may need extension for hover card and popover testing.
- Hover cards do not require a mobile/touch fallback in the current scope. If mobile support is planned in the future, a tap-to-expand pattern will be designed separately.
- The global tooltip delay of 300 ms is appropriate for most UI contexts. Dense areas like the pipeline board may benefit from per-component delay overrides (e.g., 0 ms for icon-only buttons), which is supported by the existing tooltip component API.
- The tooltip content registry is already structured for future i18n/localization. No localization work is included in this scope.
- Standard web accessibility expectations apply: WCAG 2.1 AA compliance is the target for all tooltip, hover card, and popover interactions.
- Drop zone visual feedback will use existing design tokens and will not require new design system additions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of icon-only buttons across all 8 pages display a descriptive tooltip within 300 ms of hover or keyboard focus.
- **SC-002**: Zero interactive elements use the HTML `title` attribute for tooltip-like behavior (verified by codebase search).
- **SC-003**: All 4 entity types (agent, issue, model, chat mention) display rich hover cards with correct, up-to-date data.
- **SC-004**: 100% of popovers close on Escape keypress and return focus to their trigger element.
- **SC-005**: Zero accessibility violations reported by automated accessibility testing across all pages.
- **SC-006**: All tooltip content registry keys have exactly one corresponding UI usage (zero orphaned keys).
- **SC-007**: All interactive card surfaces share a visually uniform hover state across all pages.
- **SC-008**: All draggable elements display a visible drag-handle icon on hover with a grab cursor.
- **SC-009**: No animations play when the user has `prefers-reduced-motion` enabled (verified by toggling the OS setting and observing hover cards, tooltips, and popovers).
- **SC-010**: Every icon-only button has an `aria-label` whose text matches its tooltip text exactly.
