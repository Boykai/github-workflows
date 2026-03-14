# Feature Specification: Deep UI/UX Tooltip & Hover Coverage

**Feature Branch**: `041-tooltip-hover-coverage`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "Full-coverage tooltip and hover UX across all 8 pages and all component groups. Three-tier approach: install missing Radix primitives, fill every gap per component, then validate consistency, motion, and accessibility."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consistent Tooltip Guidance on Icon-Only Buttons (Priority: P1)

A user navigates the application and encounters icon-only buttons throughout the interface — in the sidebar navigation, pipeline builder toolbar, agent card actions, board column headers, and settings page. When the user hovers over any icon-only button, a tooltip appears within 300 milliseconds displaying a clear, concise description of the button's function. The tooltip text matches the button's `aria-label` exactly, ensuring a consistent experience for both sighted and assistive-technology users. When the user moves the cursor away, the tooltip dismisses cleanly.

**Why this priority**: Icon-only buttons without tooltips are the single largest usability gap in the current interface. Users cannot discover functionality without trial-and-error clicking. This story delivers immediate, broad value across every page of the application with no structural changes — it fills known gaps using the existing Tooltip component and content registry.

**Independent Test**: Can be fully tested by hovering over every icon-only button across all 8 pages and verifying that a tooltip appears with descriptive text. Delivers value immediately because users can understand every button's purpose before clicking.

**Acceptance Scenarios**:

1. **Given** the user is on any page of the application, **When** they hover over an icon-only button (e.g., sidebar nav items, card action buttons, toolbar buttons), **Then** a tooltip appears within 300ms displaying a description that matches the button's `aria-label`.
2. **Given** the user hovers over an icon-only button that previously used a browser-native `title=` attribute, **When** the tooltip appears, **Then** it renders as a styled Radix Tooltip (not a browser-native tooltip) consistent with all other tooltips in the application.
3. **Given** the user navigates by keyboard (Tab key), **When** focus lands on an icon-only button, **Then** the same tooltip content is accessible to screen readers via the matching `aria-label`.

---

### User Story 2 - Rich Entity Previews via Hover Cards (Priority: P1)

A user is working in the pipeline builder, agents page, or project board and wants to quickly preview details about an entity (agent, issue card, or model) without navigating away from the current view. When the user hovers over an agent node in the pipeline, an agent card on the agents page, or an issue card on the board, a rich hover card appears after a brief delay showing key details — for agents: description, model, tools, and last-run status; for issues: full title, assignees, labels, and pipeline stage. The hover card disappears when the user moves the cursor away, and no navigation occurs.

**Why this priority**: Rich hover previews are the highest-value new capability in this feature. They reduce context-switching by letting users inspect entities without clicking into detail views. This directly improves workflow speed for power users who manage many agents and issues.

**Independent Test**: Can be tested by hovering over agent nodes in the pipeline builder and agent cards on the agents page, then verifying that a hover card renders with the correct entity details. Delivers standalone value by enabling quick entity inspection.

**Acceptance Scenarios**:

1. **Given** the user hovers over an AgentNode in the pipeline builder, **When** 300ms have elapsed, **Then** a hover card appears showing the agent's description, assigned model, configured tools, and last-run status.
2. **Given** the user hovers over an AgentCard on the agents page, **When** 300ms have elapsed, **Then** a hover card appears showing the agent's description snippet, active tools, and run count.
3. **Given** the user hovers over an IssueCard on the project board, **When** 300ms have elapsed, **Then** a hover card appears showing the full issue title (if truncated on the card), assignees, labels, and pipeline stage.
4. **Given** the user moves the cursor away from the hover card trigger, **When** 150ms have elapsed, **Then** the hover card dismisses with a smooth fade-out animation.
5. **Given** the user has the `prefers-reduced-motion` accessibility setting enabled, **When** a hover card appears or dismisses, **Then** it renders without animation (instant show/hide).

---

### User Story 3 - Accessible Popover Replacement for Manual Overlays (Priority: P2)

A user interacts with UI elements that currently use manually implemented overlays — the model selector dropdown in the pipeline builder, the add-agent popover on the board, and the agent preset selector. These manual implementations have inconsistent keyboard behavior: some do not close on Escape, some do not trap focus, and some do not return focus to the trigger on close. After migration to the standardized Popover component, every popover closes on Escape or outside click, traps focus within the popover content while open, and returns focus to the trigger element when closed.

**Why this priority**: Popover migration is critical for accessibility compliance and interaction consistency. Manual overlay implementations create unpredictable keyboard experiences and fail ARIA requirements. This story prevents accessibility regressions and ensures all overlay interactions behave identically.

**Independent Test**: Can be tested by opening each popover via click, pressing Escape to close, and verifying focus returns to the trigger. Tab navigation within the popover should cycle through all interactive elements without escaping to the background page.

**Acceptance Scenarios**:

1. **Given** the user clicks the model selector trigger in the pipeline builder, **When** the popover opens, **Then** focus moves into the popover content and Tab key cycles through options within the popover.
2. **Given** a popover is open, **When** the user presses Escape, **Then** the popover closes and focus returns to the trigger element that opened it.
3. **Given** a popover is open, **When** the user clicks outside the popover, **Then** the popover closes and the correct `aria-expanded` attribute updates to `false`.
4. **Given** a popover trigger element, **When** inspecting the DOM, **Then** the trigger has `aria-haspopup` set to `dialog` and `aria-expanded` reflects the popover's open/closed state.

---

### User Story 4 - Full-Text Display for Truncated Content (Priority: P2)

A user is browsing the saved workflows list, issue cards on the board, or agent cards with long names. Some text content is truncated with ellipsis due to layout constraints. When the user hovers over truncated text, the full content is revealed — either via a tooltip (for short text) or a hover card (for longer structured content). The user no longer needs to click into a detail view just to read the full name or title.

**Why this priority**: Truncated text without hover reveal is a common frustration. Users cannot distinguish between similarly-named items when names are cut off. This story eliminates all remaining `title=` attributes on interactive elements and replaces them with consistent styled tooltips.

**Independent Test**: Can be tested by creating items with long names (agents, workflows, issues) and verifying that hovering over truncated text reveals the full content in a styled tooltip rather than a browser-native `title=` tooltip.

**Acceptance Scenarios**:

1. **Given** a saved workflow name is truncated with ellipsis in the workflows list, **When** the user hovers over the truncated name, **Then** a styled tooltip appears showing the full workflow name.
2. **Given** an issue card title is truncated on the project board, **When** the user hovers over the card, **Then** a hover card appears showing the full title along with other issue metadata.
3. **Given** any interactive element previously using `title=` for hover text, **When** the user hovers over it, **Then** a styled Radix Tooltip appears instead of a browser-native tooltip.

---

### User Story 5 - Uniform Hover States and Drag Affordances (Priority: P3)

A user scans the interface looking for interactive elements. All interactive cards (agent cards, issue cards, tool cards, chore cards, agent nodes, stage cards) display a consistent hover state — a subtle ring or background shift — when the cursor passes over them. Draggable items additionally reveal a drag-handle icon on hover with a `cursor-grab` pointer, clearly signaling that the element can be repositioned. Drop zones highlight with a distinct visual treatment when a dragged item hovers over them.

**Why this priority**: Visual consistency for hover states is a polish layer that reinforces the interface's design language. While not functionally blocking, inconsistent hover treatments make the UI feel unfinished and reduce user confidence about which elements are interactive or draggable.

**Independent Test**: Can be tested by hovering over each card type across all pages and verifying that hover states are visually consistent. Drag handles can be tested by hovering over draggable items and confirming the drag icon appears and cursor changes to `grab`.

**Acceptance Scenarios**:

1. **Given** the user hovers over any interactive card (AgentCard, IssueCard, ToolCard, ChoreCard, AgentNode, StageCard), **When** the cursor enters the card area, **Then** the card displays a uniform hover state using consistent visual treatment across all card types.
2. **Given** a draggable item (AgentNode, ExecutionGroupCard, StageCard, chore row), **When** the user hovers over it, **Then** a drag-handle icon becomes visible and the cursor changes to `grab`.
3. **Given** the user is dragging an item over a valid drop zone, **When** the dragged item enters the drop zone, **Then** the drop zone displays a distinct visual highlight indicating it will accept the drop.

---

### User Story 6 - Tooltip Content Registry Completeness and Accuracy (Priority: P3)

A developer or content editor audits the tooltip content registry to ensure every tooltip key used in the application has a corresponding entry, no orphaned keys exist without a matching component reference, and all tooltip copy uses terminology consistent with the UI labels (e.g., "execution group" not "group," "stage" not "column").

**Why this priority**: Registry hygiene prevents silent tooltip failures (where a component references a key that does not exist) and ensures content accuracy. This is a maintenance story that keeps the tooltip system healthy as the application evolves.

**Independent Test**: Can be tested by running a grep audit — comparing all `contentKey=` references in components against the registry keys in `tooltip-content.ts`, and vice versa. Any mismatches indicate orphaned or missing keys.

**Acceptance Scenarios**:

1. **Given** a developer runs a registry audit, **When** comparing all `contentKey=` usages in components against registry entries, **Then** every `contentKey` has a matching registry entry and every registry entry has at least one `contentKey` usage.
2. **Given** a developer reviews tooltip copy in the registry, **When** checking terminology against UI labels, **Then** all tooltip text uses the exact terminology displayed in the UI (e.g., "execution group" not "group").
3. **Given** a component references a `contentKey` that does not exist in the registry, **When** the tooltip renders, **Then** the component gracefully skips tooltip rendering (no errors, no empty tooltip bubbles).

---

### Edge Cases

- What happens when a hover card's data source is unavailable (e.g., agent was deleted after the pipeline was rendered)? The hover card displays a graceful fallback message (e.g., "Agent details unavailable") instead of crashing or showing an empty card.
- What happens when a user moves the cursor rapidly between multiple hover card triggers? Only the most recently hovered trigger's card renders; previous pending cards are cancelled, preventing a cascade of overlapping cards.
- What happens when a tooltip trigger is inside a scrollable container and the user scrolls while the tooltip is visible? The tooltip repositions or dismisses cleanly; it does not float disconnected from its trigger.
- What happens on touch devices where hover is not available? Tooltips do not render on touch (hover-only); hover cards degrade gracefully with no broken UI. If mobile support is planned in the future, a tap-to-expand fallback would be needed, but that is out of scope for this feature.
- What happens when a popover is open and the user resizes the browser window? The popover repositions itself to remain visible within the viewport, following built-in collision detection.
- What happens when two tooltips would overlap (e.g., adjacent icon buttons)? Only one tooltip renders at a time — hovering away from one trigger and onto another smoothly transitions between tooltips via the global TooltipProvider skip delay.
- What happens when `prefers-reduced-motion` is enabled? All tooltip, hover card, and popover animations are suppressed — components appear and disappear instantly without fade, slide, or zoom effects.
- What happens when a `contentKey` is referenced but has no entry in the registry? The Tooltip component silently skips rendering (existing behavior), logging no errors.

## Requirements *(mandatory)*

### Functional Requirements

#### Infrastructure

- **FR-001**: System MUST provide a HoverCard UI primitive that renders rich content when a user hovers over a trigger element, with configurable open delay (default 300ms) and close delay (default 150ms).
- **FR-002**: System MUST provide a Popover UI primitive that renders interactive content anchored to a trigger element, with focus trapping, Escape-to-close, outside-click-to-close, and focus-return-to-trigger behavior.
- **FR-003**: Both HoverCard and Popover primitives MUST respect the `prefers-reduced-motion` user preference by suppressing all entrance/exit animations when the preference is active.
- **FR-004**: System MUST include the HoverCard and Popover primitives as shared UI components available to all feature areas of the application.

#### Tooltip Coverage

- **FR-005**: Every icon-only button across all 8 pages MUST display a tooltip on hover with descriptive text sourced from the tooltip content registry.
- **FR-006**: Every icon-only button's `aria-label` attribute MUST match its tooltip text exactly.
- **FR-007**: All interactive elements currently using browser-native `title=` attributes MUST be migrated to use styled tooltips. The `title=` attribute is permitted only on non-interactive truncated text elements.
- **FR-008**: The tooltip content registry MUST contain entries for all tooltip keys referenced by components, using the hierarchical `{area}.{section}.{element}` naming convention.

#### Hover Cards

- **FR-009**: AgentNode in the pipeline builder MUST display a hover card showing the agent's description, assigned model, configured tools, and last-run status.
- **FR-010**: AgentCard on the agents page MUST display a hover card showing the agent's description snippet, active tools, and run count.
- **FR-011**: IssueCard on the project board MUST display a hover card showing the full title (if truncated), assignees, labels, and pipeline stage.
- **FR-012**: The `@agent-name` mention chip in the chat message composer MUST display a hover card showing an agent card preview.
- **FR-013**: Hover cards MUST display a graceful fallback message when entity data is unavailable.

#### Popover Migration

- **FR-014**: The ModelSelector dropdown in the pipeline builder MUST be migrated from a manual overlay to the standardized Popover primitive.
- **FR-015**: The AddAgentPopover on the board MUST be migrated from a manual overlay to the standardized Popover primitive.
- **FR-016**: The AgentPresetSelector on the board MUST be migrated from a manual overlay to the standardized Popover primitive.
- **FR-017**: All migrated popovers MUST close on Escape key press and return focus to the trigger element.
- **FR-018**: All migrated popovers MUST have correct `aria-haspopup` and `aria-expanded` attributes on their trigger elements.

#### Hover Styling

- **FR-019**: All interactive card components (AgentCard, IssueCard, ToolCard, ChoreCard, AgentNode, StageCard) MUST display a uniform hover state using consistent visual treatment.
- **FR-020**: All draggable items (AgentNode, ExecutionGroupCard, StageCard, chore rows) MUST display a visible drag-handle icon on hover with `cursor-grab` pointer.
- **FR-021**: All drop zones MUST display a distinct visual highlight when a dragged item hovers over them.

#### Registry & Consistency

- **FR-022**: The tooltip content registry MUST NOT contain orphaned keys — every registry entry MUST have at least one corresponding `contentKey` usage in a component.
- **FR-023**: All tooltip copy in the registry MUST use terminology that exactly matches the UI labels (e.g., "execution group" not "group," "stage" not "column").
- **FR-024**: The sidebar navigation MUST use styled tooltips with registry-sourced content for all icon-only nav items (Projects, Agents, Pipeline, Chores, Tools, Settings) and the collapse/expand toggle.

#### Accessibility

- **FR-025**: All tooltip triggers MUST be reachable via keyboard Tab navigation.
- **FR-026**: All popovers MUST trap focus within the popover content when open and cycle focus through interactive elements with the Tab key.
- **FR-027**: The application MUST pass automated accessibility testing with zero violations on all pages after this feature is complete.

### Key Entities

- **Tooltip**: A lightweight, text-only overlay that appears on hover or focus to describe a UI element. Sourced from the centralized content registry via a `contentKey`. Attributes: content key, summary text, optional title, optional learn-more URL, placement side, delay duration.
- **Hover Card**: A rich, content-capable overlay that appears on hover to preview entity details (agents, issues, models). Attributes: trigger element, content (structured entity data), open delay, close delay, animation behavior.
- **Popover**: An interactive overlay anchored to a trigger element that contains focusable content (forms, selectors, lists). Attributes: trigger element, content, focus-trap behavior, close-on-escape, close-on-outside-click, aria attributes.
- **Tooltip Content Registry**: A centralized data store mapping hierarchical keys (`{area}.{section}.{element}`) to tooltip text entries. Attributes: key, summary, optional title, optional learn-more URL.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of icon-only buttons across all 8 pages display a descriptive tooltip on hover — verified by a comprehensive hover audit across every page.
- **SC-002**: Every icon-only button has both an `aria-label` and a tooltip, with text that matches exactly — verified by automated accessibility tests.
- **SC-003**: Zero browser-native `title=` attributes remain on interactive elements — verified by a codebase grep audit. `title=` is permitted only on non-interactive truncated text.
- **SC-004**: All popovers (including migrated ones) close on Escape key press and return focus to the trigger — verified by keyboard-only navigation testing on every popover instance.
- **SC-005**: All hover cards display correct, up-to-date entity data matching the source data — verified by comparing hover card content against entity detail views for at least 5 sample entities per type.
- **SC-006**: Automated accessibility testing reports zero violations across all 8 pages — verified by running the existing accessibility test suite.
- **SC-007**: No animations play when `prefers-reduced-motion` is enabled — verified by enabling the preference and confirming instant show/hide behavior for all tooltips, hover cards, and popovers.
- **SC-008**: Users can identify the purpose of any icon-only button within 1 second via tooltip — measured by the tooltip appearing within 300ms of hover.
- **SC-009**: The tooltip content registry contains zero orphaned keys and zero missing keys — verified by a bidirectional audit comparing registry entries against component `contentKey` usages.

### Assumptions

- The existing tooltip infrastructure (global TooltipProvider, centralized `tooltip-content.ts` registry, and `tooltipAwareRender()` test utility) is stable and does not require changes to its core API.
- The HoverCard and Popover packages provide built-in support for focus trapping, collision detection, and `prefers-reduced-motion` integration.
- The existing animation tokens and motion-reduce utilities in the project are sufficient for implementing accessible animations on the new primitives.
- The application currently has 8 pages that require tooltip coverage: Pipeline Builder, Agents, Chat, Board/Projects, Tools, Settings, Chores, and the global Sidebar/Navigation.
- Entity data for hover cards (agent details, issue metadata) is already available in the component's local state or can be passed as props — no new data-fetching endpoints are required.
- The `tooltipAwareRender()` test utility can be extended to support HoverCard testing without structural changes.
- The existing automated accessibility test suite covers all 8 pages and can detect ARIA violations introduced or resolved by this feature.

### Dependencies

- Existing tooltip infrastructure (`tooltip.tsx`, TooltipProvider in `App.tsx`, `tooltip-content.ts` registry).
- Existing component architecture for all target components (AgentNode, AgentCard, IssueCard, ModelSelector, AddAgentPopover, AgentPresetSelector, Sidebar, etc.).
- Existing drag-and-drop integration for drag handle and drop zone styling.
- Existing CSS configuration and design tokens for consistent styling.
- Existing automated accessibility test suite for verification.

### Scope Boundaries

**In scope:**

- Creating HoverCard and Popover UI primitives modeled on the existing Tooltip component
- Adding tooltips to all icon-only buttons across all 8 pages
- Adding hover cards for agent, issue, and model entity previews
- Migrating manual overlay implementations (ModelSelector, AddAgentPopover, AgentPresetSelector) to the Popover primitive
- Replacing all `title=` attributes on interactive elements with styled tooltips
- Extending the tooltip content registry with all missing keys
- Establishing uniform hover states and drag handle affordances across all card types
- Adding drop zone visual feedback for drag-and-drop interactions
- Ensuring full keyboard accessibility for all new and migrated components
- Pruning orphaned registry keys and normalizing terminology
- Unit tests for new primitives and migrated components

**Out of scope:**

- Mobile/touch-specific hover alternatives (tap-to-expand fallback for hover cards)
- Internationalization (i18n) of tooltip content — the registry structure supports future localization, but translations are not part of this feature
- Changes to the core Tooltip component API or the TooltipProvider configuration
- Adding tooltips to non-interactive decorative elements
- Creating new data-fetching endpoints for hover card content — only existing available data is used
- Performance optimization of tooltip rendering (e.g., lazy loading, virtualization)
- Visual design changes beyond establishing consistent hover tokens — no redesign of card layouts or color schemes

### Considerations

1. **Tooltip delay tuning** — The global `delayDuration={300}` is appropriate for most UI areas, but icon-only buttons in dense layouts (pipeline builder, board toolbar) may benefit from `delayDuration={0}` for rapid scanning. This can be scoped per-component via the `delayDuration` prop without changing the global default.
2. **Mobile/touch** — Tooltips and hover cards are hover-only and will not fire on touch devices. If mobile support is planned in the future, hover cards would need a tap-to-expand fallback pattern. This is documented as out of scope.
3. **i18n readiness** — The tooltip content registry's `{area}.{section}.{element}` key structure is already i18n-friendly. No code changes are needed if translation is added later — only the registry entries would need translated variants.
4. **Performance** — Hover cards render entity data that is already in component state. No additional network requests are triggered on hover, preventing latency or loading states in hover cards.
