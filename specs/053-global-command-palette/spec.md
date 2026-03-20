# Feature Specification: Global Search / Command Palette

**Feature Branch**: `053-global-command-palette`  
**Created**: 2026-03-20  
**Status**: Draft  
**Input**: User description: "No Global Search / Command Palette — There's no Ctrl+K / Cmd+K command palette or global search. The Ctrl+K shortcut currently only focuses the chat input. Users have no way to quickly search issues, agents, pipelines, tools, or navigate by name — they must browse each page manually."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open and Navigate via Command Palette (Priority: P1)

A user is working in the application and wants to quickly navigate to a specific page or section without clicking through the sidebar. They press Ctrl+K (or Cmd+K on macOS) to open a command palette overlay. The palette appears centered on the screen with an input field auto-focused and ready for typing. The user types a few characters of their destination (e.g., "set" for Settings) and sees matching navigation options appear instantly. They select one using keyboard arrows and Enter, and are taken directly to that page.

**Why this priority**: This is the core interaction of the feature. Without the command palette overlay and basic navigation, no other functionality is possible. It replaces the current Ctrl+K behavior (focus chat input) with a much more powerful global command palette, providing immediate value to power users.

**Independent Test**: Can be fully tested by pressing Ctrl+K, verifying the palette opens with focus in the search field, typing a page name, selecting a result, and confirming navigation to the correct page.

**Acceptance Scenarios**:

1. **Given** the user is on any page, **When** they press Ctrl+K (or Cmd+K), **Then** a command palette overlay appears centered on screen with a search input auto-focused
2. **Given** the command palette is open, **When** the user types "agents", **Then** navigation results matching "Agents" appear in the results list
3. **Given** results are displayed, **When** the user presses the Down arrow to highlight a result and presses Enter, **Then** the palette closes and the user is navigated to the selected page
4. **Given** the command palette is open, **When** the user clicks a result, **Then** the palette closes and the user is navigated to the selected page
5. **Given** the command palette is open, **When** the user presses Escape or clicks outside the palette, **Then** the palette closes and focus returns to the previously focused element

---

### User Story 2 - Search Across Entities (Priority: P2)

A user wants to find a specific agent, pipeline, tool, chore, or app by name without navigating to each page and browsing manually. They open the command palette and type a query. The palette searches across all entity types and shows categorized results — agents, pipelines, tools, chores, and apps — grouped by type. The user selects a result and is navigated to the relevant page or detail view for that entity.

**Why this priority**: Cross-entity search is the primary reason users need a command palette beyond simple page navigation. It eliminates the need to visit each page individually to find a specific item. However, it depends on User Story 1 (the palette overlay) being in place first.

**Independent Test**: Can be tested by opening the command palette, typing an entity name (e.g., an agent name), verifying categorized results appear from multiple entity types, and selecting one to confirm navigation to the correct detail view.

**Acceptance Scenarios**:

1. **Given** the command palette is open, **When** the user types a query that matches an agent name, **Then** the matching agent appears under an "Agents" category heading in the results
2. **Given** the command palette is open, **When** the user types a query that matches items across multiple entity types, **Then** results are grouped by category (Pages, Agents, Pipelines, Tools, Chores, Apps) with clear category labels
3. **Given** the user selects an agent from the results, **Then** the palette closes and the user is navigated to the agents page with that agent highlighted or opened
4. **Given** the command palette is open, **When** the user types a query with no matches, **Then** a friendly "No results found" message is displayed

---

### User Story 3 - Quick Actions from the Palette (Priority: P3)

A user wants to perform common actions without navigating to the relevant page first. They open the command palette, type an action keyword (e.g., "new" or "create"), and see a list of available quick actions such as "New Pipeline", "Focus Chat", or "Toggle Theme". Selecting an action executes it immediately — opening a creation flow, toggling a setting, or focusing an element.

**Why this priority**: Quick actions enhance productivity for power users but are a convenience layer on top of the core search and navigation features. The command palette is fully useful without quick actions, making this a valuable but lower-priority enhancement.

**Independent Test**: Can be tested by opening the command palette, typing an action keyword, selecting a quick action, and verifying the corresponding action is executed (e.g., theme toggles, chat input receives focus, or a creation flow begins).

**Acceptance Scenarios**:

1. **Given** the command palette is open, **When** the user types "theme", **Then** a "Toggle Theme" action appears in the results
2. **Given** the user selects "Toggle Theme", **Then** the palette closes and the application theme switches between light and dark modes
3. **Given** the command palette is open, **When** the user types "chat", **Then** a "Focus Chat" action appears, and selecting it closes the palette and focuses the chat input

---

### User Story 4 - Keyboard-Driven Navigation Within the Palette (Priority: P1)

A user who prefers keyboard-driven workflows opens the command palette and interacts with it entirely via the keyboard. They type to filter results, use Up/Down arrow keys to navigate through the results list, press Enter to select the highlighted result, and press Escape to dismiss the palette. The currently highlighted result is clearly visually distinguished.

**Why this priority**: Keyboard accessibility is critical for the command palette — this is a keyboard-first feature by design. Users who invoke the palette with a keyboard shortcut expect to complete their entire interaction without reaching for the mouse.

**Independent Test**: Can be tested by opening the palette, typing a query, using arrow keys to navigate results, verifying the highlight moves visually, pressing Enter, and confirming the correct action fires. Also test that Escape dismisses the palette cleanly.

**Acceptance Scenarios**:

1. **Given** the command palette is open with results visible, **When** the user presses Down arrow, **Then** the next result is highlighted with a visible focus indicator
2. **Given** the first result is highlighted, **When** the user presses Up arrow, **Then** the highlight wraps to the last result (or stays on first if wrapping is not supported)
3. **Given** a result is highlighted, **When** the user presses Enter, **Then** the highlighted result's action is executed
4. **Given** the command palette is open, **When** the user presses Escape, **Then** the palette closes and focus returns to the previously focused element

---

### Edge Cases

- What happens when the user presses Ctrl+K while a modal dialog is already open? The command palette should not open over existing modal dialogs.
- What happens when the user presses Ctrl+K while already inside the command palette? The palette should remain open and the input should remain focused (no-op or select-all text).
- How does the system handle extremely long search queries? The input should accept any length but results should be computed based on a reasonable character limit.
- What happens if entity data is still loading? The palette should display a loading indicator in the results area while data is being fetched.
- What happens on mobile devices where keyboard shortcuts are unavailable? The command palette should also be accessible via a clickable UI trigger (e.g., a search icon in the header or toolbar).
- What happens when the user types very quickly? Results should update with minimal delay and not cause the UI to freeze or flicker.
- What happens when the Ctrl+K shortcut conflicts with browser behavior? The shortcut should prevent default browser behavior (e.g., browser search bar) when the application is focused.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a command palette overlay when the user presses Ctrl+K (or Cmd+K on macOS)
- **FR-002**: System MUST auto-focus the search input field when the command palette opens
- **FR-003**: System MUST display matching results as the user types, filtered in real-time with no perceptible delay for typical queries
- **FR-004**: System MUST support searching across the following entity types: pages/navigation targets, agents, pipelines, tools, chores, and apps
- **FR-005**: System MUST group search results by category with visible category labels
- **FR-006**: System MUST allow users to navigate results using Up and Down arrow keys with a clear visual highlight on the currently selected result
- **FR-007**: System MUST execute the selected result's action (navigate or perform action) when the user presses Enter or clicks the result
- **FR-008**: System MUST close the command palette when the user presses Escape, clicks outside the overlay, or selects a result
- **FR-009**: System MUST return focus to the previously focused element when the command palette closes
- **FR-010**: System MUST display a "No results found" message when the search query has no matches
- **FR-011**: System MUST support quick actions (e.g., "Toggle Theme", "Focus Chat") as searchable items within the palette
- **FR-012**: System MUST prevent the command palette from opening when a modal dialog is already active
- **FR-013**: System MUST provide a clickable UI trigger for opening the command palette (for users without keyboard access)
- **FR-014**: System MUST display an appropriate icon or visual indicator for each result category to help users distinguish result types at a glance
- **FR-015**: System MUST update the keyboard shortcuts help modal to reflect the new Ctrl+K behavior (command palette instead of focus chat)

### Key Entities

- **Search Result**: Represents a single item in the command palette results list. Attributes include: display name, category (Page, Agent, Pipeline, Tool, Chore, App, Action), icon, description or subtitle, and the action to perform on selection (navigate to path or execute callback).
- **Result Category**: A grouping label for search results. Represents the entity type that a result belongs to. Used for visually organizing results within the palette.
- **Quick Action**: A predefined action that can be invoked from the command palette without navigating to a page. Attributes include: action name, description, icon, and execution callback.

## Assumptions

- The Ctrl+K shortcut is being **reassigned** from "focus chat input" to "open command palette." The "Focus Chat" action will remain available as a quick action within the palette itself, preserving the original functionality through a different interaction path.
- Search is performed client-side against already-loaded or cached entity data. No new backend search endpoint is required for the initial implementation.
- Result ranking uses simple substring/fuzzy matching. Advanced search features (e.g., full-text search, relevance scoring with weights) are out of scope for the initial version.
- The command palette UI follows the existing celestial design system tokens and patterns.
- Maximum results shown at any time are capped at a reasonable number (e.g., 10–15 visible results with scrolling for additional matches) to maintain UI performance and readability.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can open the command palette and navigate to any page in the application within 3 seconds (from pressing Ctrl+K to arriving at the destination)
- **SC-002**: Users can find and navigate to a specific entity (agent, pipeline, tool, chore, or app) by name within 5 seconds using the command palette
- **SC-003**: The command palette returns matching results within 200 milliseconds of the user stopping typing, with no visible UI jank or freezing
- **SC-004**: 100% of pages accessible via sidebar navigation are also reachable through the command palette
- **SC-005**: The command palette is fully operable using only keyboard input (open, search, navigate results, select, close)
- **SC-006**: Users who previously relied on Ctrl+K to focus the chat input can still access that functionality within 2 additional interactions via the command palette
- **SC-007**: The command palette is accessible on both desktop (via keyboard shortcut) and mobile (via clickable UI trigger)
