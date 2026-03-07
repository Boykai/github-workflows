# Research: Agents Page — Sun/Moon Avatars, Featured Agents, Inline Editing with PR Flow, Bulk Model Update, Repo Name Display & Tools Editor

**Feature**: 029-agents-page-ux | **Date**: 2026-03-07

## R1: Sun/Moon Avatar Implementation Strategy

**Task**: Determine how to implement deterministic sun/moon themed avatars for agents without adding external dependencies.

**Decision**: Create a custom `AgentAvatar` component containing 12 inline SVG sun/moon icon variants. Use a simple string hash of the agent's `slug` field mapped to an index in the icon array (`hash % 12`). Each SVG is a compact 32×32 or 40×40 icon using the existing Tailwind color palette (amber/yellow for sun variants, slate/indigo for moon variants). The component accepts the agent slug as a prop and renders the deterministic icon.

**Rationale**: The existing codebase uses `lucide-react` for UI icons but has no avatar system. A custom inline SVG approach adds zero runtime dependencies and renders instantly (no network requests, no library initialization). The deterministic hash ensures the same agent always displays the same avatar across page loads (FR-002). Using 12 variants (6 sun, 6 moon) provides sufficient visual diversity for typical agent counts (5–20 agents). The hash function is a simple character-code summation, which is fast and produces adequate distribution for non-cryptographic purposes. SVGs can be styled with Tailwind classes for consistency with the existing design system.

**Alternatives Considered**:
- **`boring-avatars` library**: Rejected — adds a dependency (~5 KB) for a simple use case. The library generates geometric/abstract avatars, not themed sun/moon icons. Our requirement is specifically for celestial-themed icons, which the library does not support. Violates Constitution Principle V (simplicity).
- **External SVG sprite sheet**: Rejected — adds a network request for the sprite file. Inline SVGs eliminate the HTTP round-trip and render synchronously with the component.
- **Canvas-based generative avatars**: Rejected — over-engineered. Requires canvas rendering, adds complexity, and would not produce recognizable sun/moon shapes without significant drawing code.

**Icon Variants** (12 total):
1. Full Sun (☀️) — circle with radiating rays
2. Half Sun / Sunrise (🌅) — semicircle with rays above horizon line
3. Sun with Face (🌞) — stylized sun with simple facial features
4. Sun Behind Cloud (⛅) — sun partially obscured
5. Solar Eclipse (🌑☀️) — dark circle with corona
6. Sunburst — starburst pattern with alternating long/short rays
7. Full Moon (🌕) — complete circle with subtle crater marks
8. Crescent Moon (🌙) — classic crescent shape
9. Half Moon (🌓) — first quarter phase
10. Waning Crescent (🌘) — thin sliver
11. Moon with Stars (🌙✨) — crescent with small stars
12. Moonrise — moon rising over horizon line

---

## R2: Featured Agents — Supplementing with Recently Created Agents

**Task**: Determine how to enhance the existing Featured Agents logic to supplement usage-ranked agents with recently created agents when fewer than 3 high-usage agents exist.

**Decision**: Modify the `spotlightAgents` computation in `AgentsPanel.tsx` to use a two-pass algorithm: (1) Select agents with usage count > 0, sorted by usage descending, take up to 3. (2) If fewer than 3 were selected, supplement with agents whose `created_at` is within the past 3 days (72 hours), sorted by creation date descending, excluding any already selected. Cap at 3 total. If still fewer than 3 (no high-usage agents and no recently created agents), hide the Featured Agents section or show an empty state.

**Rationale**: The current implementation in `AgentsPanel.tsx` (lines 67–73) already sorts by usage count and takes the top 3, but does not filter out zero-usage agents or supplement with recently created ones. The `created_at` field is available on the `AgentConfig` type (populated from SQLite `datetime('now')` or from the repo discovery flow). The 3-day window aligns with the spec requirement (FR-004). The two-pass approach is simple and efficient — it runs entirely on the client side using the already-fetched agents list, requiring no backend changes.

**Alternatives Considered**:
- **Backend endpoint for featured agents**: Rejected — the client already has all agent data (including `created_at` and usage counts). Adding a backend endpoint adds latency and a round-trip for no benefit. Usage counts are computed client-side from column assignments.
- **Weighted scoring (usage × recency)**: Rejected — more complex and harder to explain to users. The spec clearly prioritizes usage count first, then supplements with recency. A simple two-pass approach matches the spec exactly.
- **Always show 3 agents (even with no qualifiers)**: Rejected — spec says "hide or show empty state" (FR-005) when no agents qualify. Showing random agents when none are featured would mislead users.

---

## R3: Inline Editing Architecture — Modal vs. True Inline

**Task**: Determine whether to implement true inline editing (directly on the card/detail view) or enhance the existing modal-based editor for the agent definition editing feature.

**Decision**: Enhance the existing `AddAgentModal` component's edit mode. The modal already supports structured form fields (name, system prompt, tools, model) and handles the create/update mutation flow. Enhancements include: (1) adding a dirty-state tracker that compares current form values against the original agent data, (2) showing a persistent "unsaved changes" banner inside the modal, (3) intercepting the modal close event (and browser `beforeunload`) to show a confirmation dialog when dirty, and (4) displaying the PR URL in a success notification after save.

**Rationale**: The `AddAgentModal` (274 lines) already has full edit mode support with pre-populated fields, validation, and success/error handling. Building a true inline editor would require duplicating all this form logic within the `AgentCard` component, significantly increasing complexity. The modal pattern is established in the codebase (`AddAgentModal`, `ToolSelectorModal`, `UploadMcpModal`) and familiar to users. The key new behaviors (unsaved-changes tracking, navigation guard, PR link display) can be added to the existing modal with minimal changes. The `useUpdateAgent` mutation already creates a PR on save — the only missing piece is surfacing the PR URL in a success notification and adding the dirty-state UX.

**Alternatives Considered**:
- **True inline editor (fields embedded in card)**: Rejected — requires complex layout changes, duplicates form validation logic, creates awkward UX with expandable/collapsible inline forms, and conflicts with the card grid layout. The modal approach keeps the card clean and focused.
- **Full-page editor route**: Rejected — violates the spec requirement for "inline" editing without leaving the page. A route change would lose the agents page context and break the unsaved-changes navigation guard pattern.
- **Drawer/side panel editor**: Considered but deferred — a side panel would provide more editing space while keeping the agents list visible. However, this adds a new UI pattern not present in the codebase. The modal approach is simpler and consistent. A drawer could be a future enhancement.

---

## R4: Unsaved Changes Detection and Navigation Guard

**Task**: Determine the best approach for detecting unsaved changes and blocking navigation.

**Decision**: Implement a three-layer approach: (1) **Dirty state tracking** — compare current form values to the original agent data using a deep equality check (or field-by-field comparison for `name`, `description`, `system_prompt`, `tools`, `default_model_id`). (2) **Modal close guard** — intercept the modal's close/cancel action; if dirty, show a confirmation dialog ("You have unsaved changes — save before leaving?") with Save, Discard, and Cancel options. (3) **Browser beforeunload guard** — add a `beforeunload` event listener when the form is dirty to catch tab close, refresh, and URL navigation.

**Rationale**: The modal close guard handles in-app navigation (closing the modal, clicking outside it). The `beforeunload` guard handles browser-level navigation (closing the tab, refreshing, navigating to a different URL). Together, they cover all navigation vectors. React Router's `useBlocker` hook could handle route changes, but since the editor is a modal (not a route), the `beforeunload` listener is sufficient. The dirty state comparison is lightweight — the agent form has ~5 fields, so field-by-field comparison is simpler and more debuggable than JSON serialization.

**Alternatives Considered**:
- **React Router `useBlocker`/`usePrompt`**: Rejected for primary guard — the editor is a modal overlay, not a separate route. Route blocking doesn't apply to modal close events. However, if the agent page has sub-routes in the future, this could be added.
- **Form library (React Hook Form / Formik)**: Rejected — adding a form library for one modal is over-engineered. The existing modal uses `useState` for form fields, which is sufficient. React Hook Form's `formState.isDirty` is nice but not worth the dependency.
- **Auto-save with debounce**: Rejected — the spec explicitly requires a save gate ("must save the page before leaving"). Auto-save would bypass the intentional review step and create PRs for incomplete edits.

---

## R5: Bulk Model Update Implementation

**Task**: Determine how to implement the "Update All Models" action, including the backend endpoint and frontend confirmation flow.

**Decision**: Add a new `PATCH /api/v1/agents/{project_id}/bulk-model` endpoint that accepts a `target_model_id` and `target_model_name`. The backend iterates over all active agents (from both SQLite and repo sources), updates each agent's `default_model_id` and `default_model_name` via the existing runtime model preference storage (SQLite `agent_model_preferences` or `agent_configs` table), and returns a summary of updated agents. On the frontend, a "Update All Models" button in the `AgentsPanel` toolbar opens a `BulkModelUpdateDialog` that: (1) shows the model selector to pick the target model, (2) lists all agents that will be affected, (3) requires explicit "Confirm" click to proceed. On success, invalidate the agents query to refresh the list.

**Rationale**: The existing `update_agent()` service method handles model updates via a "runtime-only model update" path that stores model preferences in SQLite without creating a PR (for repo-sourced agents). The bulk endpoint wraps this same logic in a loop, ensuring consistency. Creating individual PRs for each agent's model change would be excessive — model preference is already a local runtime setting, not a repo-committed value. The confirmation dialog prevents accidental bulk updates (FR-013, FR-014). The `ModelSelector` component already exists and can be reused in the dialog.

**Alternatives Considered**:
- **Individual PRs per agent for model changes**: Rejected — model preferences are stored locally in SQLite as runtime overrides, not committed to the repo. Creating PRs for each would be inconsistent with the existing model update flow (which is PR-free).
- **Frontend-only batch (call update N times)**: Rejected — creates N API calls in parallel/sequence. A single bulk endpoint is more efficient, atomic (partial failures can be reported together), and avoids potential rate limiting.
- **"Update All" including repo-committed changes**: Rejected — the spec says "update all agent models," which aligns with the existing runtime preference system. Committing model choices to `.agent.md` files would be a different feature (the YAML frontmatter doesn't currently include model fields).

---

## R6: Repository Name Display and Dynamic Fitting

**Task**: Determine how to display only the repository name (not owner/repo) and fit it within a styled bubble.

**Decision**: Parse the repository identifier by splitting on `/` and taking the last segment. Display in a styled chip/bubble using Tailwind CSS: `max-w-[12rem] truncate` (CSS `text-overflow: ellipsis`, `overflow: hidden`, `white-space: nowrap`). The chip uses existing badge/pill styling patterns from the codebase (`rounded-full px-3 py-1 text-sm bg-muted`). No JavaScript-based text-fit library is needed — CSS truncation handles all practical name lengths.

**Rationale**: The `AgentCard` currently shows a source badge ("Repository" / "Local" / "Shared") but does not display the actual repository name. The repository name is available from the project context (passed to `AgentsPage` from the app state). Splitting on `/` is a simple, reliable operation — GitHub repository identifiers always follow the `owner/repo` pattern. CSS truncation with `text-overflow: ellipsis` is the standard, performant approach for fitting text in fixed-width containers. A `max-width` of `12rem` (~192px) accommodates most repo names while preventing overflow in the card grid layout. The `title` attribute provides the full name on hover for truncated names.

**Alternatives Considered**:
- **JavaScript text-fit library (e.g., `textfit`)**: Rejected — adds a dependency and requires DOM measurement for dynamic font scaling. CSS truncation is simpler and handles the requirement adequately (spec says "using ellipsis truncation as a fallback").
- **Dynamic font scaling via CSS `clamp()`**: Considered — `font-size: clamp(0.6rem, 2vw, 0.875rem)` could scale text to fit. However, this creates inconsistent font sizes across cards, which looks messy. Fixed font size with ellipsis truncation is cleaner.
- **Tooltip-only (no display)**: Rejected — the spec explicitly requires the repo name to be visible on the card, not hidden behind a tooltip.

---

## R7: Tools Editor — Reorder Implementation

**Task**: Determine how to implement the tools reorder functionality within the agent's configuration editor.

**Decision**: Implement reorder using simple "move up" / "move down" arrow buttons on each tool item in the list, rather than drag-and-drop. The tools list renders as an ordered `<ul>` with each `<li>` containing the tool name/chip and up/down arrow buttons. Clicking up/down swaps the tool with its adjacent neighbor. Add/remove is handled via the existing `ToolSelectorModal` component (multi-select checkboxes). All changes are tracked in local component state within the editor modal and merged into the agent update payload on save.

**Rationale**: The spec says "via UI controls (checkboxes, drag-and-drop, or a multi-select dropdown)" — all three are acceptable. Arrow-button reorder is the simplest implementation that satisfies the requirement. The existing codebase uses `@dnd-kit/sortable` for pipeline stage reordering, but importing the drag-and-drop library for a simple list of 3–10 tools is over-engineered. Arrow buttons are accessible, keyboard-friendly, and require no additional dependencies. The `ToolSelectorModal` already handles tool selection (add/remove) — the new `ToolsEditor` component wraps the selected tools as an ordered list with reorder controls. Tool order is preserved in the `tools: string[]` array in the agent config.

**Alternatives Considered**:
- **`@dnd-kit/sortable` drag-and-drop**: Considered — the library is already in the project for pipeline stages. However, drag-and-drop adds visual complexity (drag handles, drop indicators, animation) for a short list. The tools list is typically 3–10 items — arrow buttons are faster and less error-prone for short lists.
- **Inline text editing of tool names**: Rejected — tools are predefined MCP configurations, not free-text entries. Users should select from available tools, not type tool names.
- **Drag-and-drop only (no arrow buttons)**: Rejected — arrow buttons are more accessible (keyboard navigation, screen readers) and work well on mobile/touch devices where drag-and-drop can be finicky.
