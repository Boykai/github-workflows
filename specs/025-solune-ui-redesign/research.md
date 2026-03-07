# Research: Solune UI Redesign

**Feature Branch**: `025-solune-ui-redesign`  
**Date**: 2026-03-06

## R1: React Router Integration Strategy

**Decision**: Use `react-router-dom` v7 with `BrowserRouter` + `Routes` + `Route`  
**Rationale**: The codebase uses React 19.2, Vite 7.3, and TanStack Query 5. React Router v7 is the current stable release compatible with React 19. The existing hash routing (`getViewFromHash`, `changeView`, `hashchange` listener in App.tsx) is ~30 lines that will be fully replaced. BrowserRouter is preferred over HashRouter to achieve clean URLs per spec FR-001.  
**Alternatives considered**:
- TanStack Router — More type-safe but adds complexity; the team already uses TanStack Query, not TanStack Router. Unnecessary learning curve.
- Wouter — Lightweight but lacks nested layout support needed for `<AppLayout>` wrapping all routes.

**Integration notes**:
- `QueryClientProvider` stays in App.tsx wrapping `BrowserRouter`
- `nginx.conf` already has `try_files $uri $uri/ /index.html` — no changes needed
- Vite dev proxy for `/api` already handles backend routing — no conflicts with client routes

## R2: Design System Migration (Theme Tokens)

**Decision**: Replace all HSL CSS custom properties in `index.css` in-place. No new CSS framework.  
**Rationale**: The current design system uses Tailwind CSS v4 with `@theme` directive and `@layer base` for light/dark HSL variables. The architecture is already sound — only the values need to change. The warm/brown palette (primary: `24 50% 22%`, accent: `36 80% 55%`) swaps to purple/violet (primary: `262 80% 55%`, accent: blue).  
**Alternatives considered**:
- CSS Modules or styled-components — Would require rewriting every component. Tailwind + CSS variables is already working well.
- Chakra UI or Mantine — Adds a heavy dependency for what is effectively a palette swap.

**Migration checklist**:
- Replace `:root` light theme HSL values (11 properties)
- Replace `.dark` theme HSL values (11 properties)
- Replace `--font-display` from `'Rye'` to `'Plus Jakarta Sans'` (or similar modern sans-serif)
- Replace `--shadow-warm-*` with neutral shadow tokens (use `rgba(0,0,0,...)` base)
- Update `--radius` from `0.375rem` to `0.5rem`
- Add priority color tokens: `--priority-p0`, `--priority-p1`, `--priority-p2`, `--priority-p3`

## R3: Font Replacement

**Decision**: Replace Rye (serif/display) with Plus Jakarta Sans (modern geometric sans-serif)  
**Rationale**: Plus Jakarta Sans is a free Google Font with 400/500/600/700 weights, supporting the modern aesthetic. Inter (already loaded) remains as the body/sans font. The `font-display` CSS variable is used by `h1`, `h2`, `h3` elements globally.  
**Alternatives considered**:
- Geist Sans — Modern but not on Google Fonts (requires self-hosting)
- DM Sans — Good but Plus Jakarta Sans has more character distinction at display sizes

**Changes**:
- `index.html`: Replace `family=Rye` with `family=Plus+Jakarta+Sans:wght@500;600;700` in Google Fonts URL
- `index.css`: Update `--font-display` value

## R4: Sidebar Collapse State Persistence

**Decision**: Use `localStorage` with key `sidebar-collapsed` (boolean)  
**Rationale**: Simple, synchronous, no dependencies. The sidebar is a layout component that mounts once. Reading from localStorage on mount is negligible overhead.  
**Alternatives considered**:
- User settings API — Adds a network call for a local-only UI preference. Overkill.
- React context — Still needs localStorage for persistence across refreshes.

## R5: Chat Popup Global Placement

**Decision**: Lift `ChatPopup` + `useChat` + `useWorkflow` from `ProjectBoardPage` to `AppLayout`  
**Rationale**: Currently ChatPopup is rendered inside ProjectBoardPage with chat hooks instantiated there. Moving both to the layout level makes chat available on all 6 pages. The `useChatHistory` hook already persists to localStorage, satisfying the "persist across refreshes" clarification. The `useChat` hook manages in-memory messages via TanStack Query — which survives route navigation since `QueryClientProvider` wraps the entire app at the root level. Combined with `useChatHistory` localStorage persistence, this satisfies full persistence across navigation AND refreshes.  
**Alternatives considered**:
- Dedicated chat page — Conflicts with the "floating popup on every page" decision.
- React Portal — Unnecessary; rendering in layout is simpler and achieves the same result.

## R6: Notification Bell Data Sources

**Decision**: Combine agent workflow events (`useWorkflow`) and chore events (`useChoresList`) into a unified notification feed  
**Rationale**: Both hooks already fetch event data from existing APIs. The notification bell aggregates counts/items from both sources. No new backend endpoint needed.  
**Implementation approach**:
- Create a lightweight `useNotifications` hook that subscribes to workflow event data and chore completion data
- Derive unread count from events newer than last-viewed timestamp (localStorage)
- Dropdown renders recent items sorted by timestamp descending

## R7: Priority Badge Color Mapping

**Decision**: Map `BoardItem.priority.name` → color token using P0=red, P1=orange, P2=blue, P3=green  
**Rationale**: The `BoardItem` type already has `priority?: BoardCustomFieldValue` with `name` (string like "P0") and `color` (StatusColor enum). The backend model (`IssuePriority` in recommendation.py) defines P0=Critical, P1=High, P2=Medium, P3=Low. The existing `IssueCard.tsx` already renders priority badges but with generic border colors via `statusColorToCSS()`. The redesign adds filled background badges with the P0-P3 mapping.  
**Note**: The `IssueRecommendationPreview.tsx` component already implements a similar mapping (P0=destructive, P1=orange, P2=blue, P3=muted) which validates the pattern.

## R8: Component Migration Plan

**Decision**: Migrate existing panel components to dedicated pages by composition, not duplication  
**Rationale**: The existing components (`AgentsPanel`, `ChoresPanel`, `AgentCard`, `AddAgentModal`, etc.) contain working business logic. The new pages should import and compose these components rather than rewrite them. This keeps code DRY per constitution Principle V.

**Migration map**:
| Current Location | New Location | Strategy |
|---|---|---|
| `AgentsPanel` (agents/) | `AgentsPage.tsx` (pages/) | Import as section within new page layout |
| `ChoresPanel` (chores/) | `ChoresPage.tsx` (pages/) | Import as section within new page layout |
| `AgentConfigRow`, `AddAgentPopover`, `AgentPresetSelector`, `AgentSaveBar` (board/) | `AgentsPipelinePage.tsx` (pages/) | Import from current location; these are board/ components reused on pipeline page |
| `CleanUpButton`, `CleanUpConfirmModal`, `CleanUpSummary`, `CleanUpAuditHistory` (board/) | `ChoresPage.tsx` (pages/) | Import from current location into chores page cleanup section |
| `ChatPopup` (chat/) | `AppLayout.tsx` (layout/) | Lift rendering to layout level |
| `ProjectBoard`, `BoardColumn`, `IssueCard` (board/) | `ProjectsPage.tsx` (pages/) | Enhance in-place; import into new page |
| `CowboyAvatar` (components/) | Deleted | Remove file entirely |

## R9: Scaffolding vs Functional Buttons

**Decision**: Audit existing hooks/APIs to determine which toolbar actions can be wired up  
**Findings**:
- **"Add new column"** → No existing API for creating board columns (GitHub Projects V2 mutations not implemented). **Scaffolding with "Coming soon" tooltip.**
- **"+" add card button** → No existing mutation for creating draft issues in columns. **Scaffolding with "Coming soon" tooltip.**
- **Filter** → Board data includes labels, assignees, priority. Client-side filtering is feasible. **Wire to functional client-side filter.**
- **Sort by** → Client-side sort by priority, date, assignee is feasible. **Wire to functional client-side sort.**
- **Group by** → Columns are already grouped by status. Additional grouping (by assignee, priority) requires client-side re-arrangement. **Scaffolding with "Coming soon" tooltip** — this is complex and not explicitly requested as functional.

## R10: Deep-Link Redirect After Auth

**Decision**: Store pre-auth URL in `sessionStorage`, redirect after successful auth callback  
**Rationale**: The auth flow uses GitHub OAuth redirect. Before redirecting to GitHub, store `window.location.pathname` in sessionStorage. After the callback resolves and `useAuth` confirms authentication, read the stored path and navigate there via React Router. Falls back to `/` if no stored path.  
**Alternatives considered**:
- URL state parameter in OAuth flow — More complex, requires backend changes (out of scope).
- localStorage — sessionStorage is more appropriate for single-session redirect intent.
