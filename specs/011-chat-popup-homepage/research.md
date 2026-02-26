# Research: Move Chat Experience to Project-Board Page as Pop-Up Module & Simplify Homepage

**Feature**: 011-chat-popup-homepage  
**Date**: 2026-02-26  
**Status**: Complete

## Research Tasks

### R1: Current Chat Architecture and Extraction Feasibility

**Question**: Can the existing chat UI be cleanly extracted into a standalone pop-up component without significant re-architecture?

**Findings**:
- The chat UI is rendered via `<ChatInterface>` component (`frontend/src/components/chat/ChatInterface.tsx`) which accepts all data/callbacks as props
- Chat state is managed by the `useChat()` hook (`frontend/src/hooks/useChat.ts`) which uses `@tanstack/react-query` for data fetching and local state for pending proposals
- Currently, `App.tsx` calls `useChat()` at the top level and passes results to `<ChatInterface>` as props
- The chat component is already self-contained in terms of rendering — it has its own CSS file and no direct DOM coupling to the homepage layout
- **No socket connections** are used for chat; all communication is via HTTP (react-query mutations) despite `socket.io-client` being in dependencies

**Decision**: Extract a `ChatPopup` wrapper component that internally calls `useChat()` and renders `<ChatInterface>`, managing its own open/closed toggle state. This avoids modifying `ChatInterface` at all.  
**Rationale**: The existing `ChatInterface` component is purely presentational (receives props). A thin `ChatPopup` wrapper provides the popup shell (toggle button, overlay, animation) while reusing `ChatInterface` unchanged.  
**Alternatives considered**: (1) Modifying `ChatInterface` directly to include popup behavior — rejected because it would break the single-responsibility pattern and make the component harder to reuse. (2) Using a global state store (e.g., Zustand) for popup state — rejected because React local state in the `ChatPopup` component is sufficient for session-scoped persistence.

### R2: Animation Approach

**Question**: What animation approach should be used for the chat pop-up open/close transition?

**Findings**:
- The project already uses CSS transitions extensively (buttons, theme toggle, form elements in `App.css` and `ChatInterface.css`)
- No animation library (e.g., Framer Motion) is currently installed
- The spec states: "Standard web animation approaches (CSS transitions or existing animation utilities) are sufficient"
- Existing transition patterns: `transition: background 0.15s ease` and `transition: all 0.2s ease` in the codebase

**Decision**: Use CSS `transition` on `transform` and `opacity` for the popup open/close animation.  
**Rationale**: Consistent with existing codebase patterns; avoids adding a new dependency; `transform` and `opacity` are GPU-accelerated for smooth 60fps performance.  
**Alternatives considered**: (1) Framer Motion — rejected because spec explicitly allows CSS transitions and no animation library is installed. (2) CSS `@keyframes` — rejected because CSS transitions are simpler for a binary open/close state toggle.

### R3: Popup Positioning and Z-Index Strategy

**Question**: How should the chat pop-up be positioned to avoid obstructing project-board elements?

**Findings**:
- The project-board page uses a standard flow layout with `board-page` as the container
- The `IssueDetailModal` in the board already uses overlay patterns (likely high z-index)
- The app layout uses `height: 100vh` with flexbox columns
- No z-index management system exists; values are used ad-hoc

**Decision**: Use `position: fixed` with `bottom: 24px; right: 24px` for the toggle button and popup panel. Z-index of `1000` for the toggle button and `999` for the popup panel (below modal overlays which typically use `1000+`).  
**Rationale**: Fixed positioning ensures the popup stays visible regardless of scroll position. Bottom-right is the conventional location for chat widgets. Z-index values are chosen to layer below modals but above regular content.  
**Alternatives considered**: (1) Side panel (full-height drawer) — rejected because it would consume significant board real estate on smaller screens. (2) Absolute positioning within the board container — rejected because it wouldn't stay fixed during scroll.

### R4: Homepage Simplification Scope

**Question**: What exactly needs to change on the homepage to meet the spec?

**Findings**:
- Current `App.tsx` has three views controlled by `activeView` state: `'chat'`, `'board'`, `'settings'`
- The `'chat'` view renders: `<ProjectSidebar>` + `<ChatInterface>` (or a placeholder)
- The `'chat'` view calls `useChat()` hook which triggers `react-query` fetches for chat messages
- Navigation buttons in the header toggle between views
- The spec requires the "Chat" button to be removed from nav and the default view to become a hero CTA page

**Decision**: Replace the `'chat'` view in `App.tsx` with a homepage hero section (nav + centered "Create Your App Here" CTA). Remove the "Chat" nav button. Remove `useChat()` and related imports from `App.tsx`. The `ChatPopup` component on the project-board page will independently call `useChat()`.  
**Rationale**: This ensures zero chat-related API calls on the homepage (FR-011) while preserving all chat functionality on the project-board page.  
**Alternatives considered**: (1) Keep `useChat()` in `App.tsx` and pass down to `ProjectBoardPage` — rejected because it would still trigger chat API calls on homepage load, violating FR-011. (2) Lazy-load the chat hook — overcomplicated; cleaner to just move the hook usage to the popup component.

### R5: Chat Pop-Up State Persistence

**Question**: How should the open/closed state of the chat pop-up persist during the user's session?

**Findings**:
- The spec requires persistence "for the duration of the user's session on the project-board page" (FR-006)
- The spec's Assumptions section clarifies: "Session state refers to in-memory or local component state during the current browser session"
- The project-board page is a view within a single-page app (SPA) — the component stays mounted while on the board view
- React local state (`useState`) persists as long as the component is mounted

**Decision**: Use `useState` in the `ChatPopup` component for open/closed state. State naturally persists while the user stays on the project-board view.  
**Rationale**: Simplest possible implementation that meets the spec requirements. The component stays mounted while the user is on the board page, so `useState` is sufficient.  
**Alternatives considered**: (1) `sessionStorage` — would persist across page refreshes but spec doesn't require this. (2) Global store (Zustand/Context) — overkill for a single boolean toggle within one page view.

### R6: Responsive Design Approach

**Question**: How should the chat pop-up adapt to mobile viewports?

**Findings**:
- Current app layout uses a mix of flexbox and basic responsive patterns
- No existing media queries or breakpoint system found in App.css
- The board page uses standard flow layout that naturally collapses
- The spec requires responsiveness from 320px to 1920px (SC-005)

**Decision**: On viewports below 768px, the chat popup expands to near-full width/height (with small margins). The toggle button remains fixed at bottom-right but sized appropriately for touch targets (min 44x44px). Use CSS media queries at `768px` breakpoint.  
**Rationale**: Near-full-screen chat on mobile provides usable space; fixed toggle button ensures discoverability. 768px is a standard tablet/mobile breakpoint.  
**Alternatives considered**: (1) Bottom sheet pattern — more complex to implement; CSS-only approach preferred. (2) Same size on all viewports — would be too small on mobile or too large on desktop.

## Summary

All NEEDS CLARIFICATION items resolved. Key decisions:
1. **ChatPopup wrapper** around existing `ChatInterface` — minimal code changes
2. **CSS transitions** for animation — no new dependencies
3. **Fixed positioning** at bottom-right with z-index layering
4. **React local state** for open/closed persistence — simplest solution
5. **Homepage becomes hero CTA** — remove chat view, add centered heading with link
6. **Responsive at 768px** breakpoint — full-width popup on mobile
