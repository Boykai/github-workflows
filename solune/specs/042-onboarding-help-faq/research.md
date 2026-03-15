# Research: Onboarding Spotlight Tour & Help/FAQ Page

**Feature**: `042-onboarding-help-faq` | **Date**: 2026-03-15

## 1. Spotlight Overlay Approach

### Decision: CSS `clip-path` with `inset()` for the cutout mask

### Rationale
The overlay needs a translucent backdrop with a transparent "window" around the highlighted element. Three approaches were evaluated:

1. **CSS `clip-path: inset()`** — A single `<div>` covers the viewport. The `clip-path` property with `polygon()` creates a rectangular hole. Transitions are hardware-accelerated via the compositor.
2. **CSS `mask-image` with radial gradient** — Uses `mask-image` to create a transparent circle/rectangle. Less browser support for animated mask transitions.
3. **Four surrounding divs** — Four absolutely-positioned rectangles surround the target, leaving a gap. Simple but creates visible seams during transitions and doesn't support rounded cutouts.

### Alternatives Considered
- **react-joyride / driver.js** — External tour libraries that handle spotlight mechanics. Rejected because: (a) adds new npm dependency violating the "no new dependencies" constraint, (b) their styling systems conflict with the celestial CSS design system, (c) customization to match `.celestial-panel` / `.golden-ring` aesthetics would be more work than building from scratch.
- **Radix Dialog as overlay** — The existing Radix tooltip/dialog could serve as the tooltip, but doesn't provide a spotlight cutout mechanism. Would still need custom overlay code.

### Implementation Notes
- Use `getBoundingClientRect()` to compute the target element's position
- Add 8px padding around the cutout for visual breathing room
- Use `ResizeObserver` + scroll listener to reposition on layout changes
- Apply `transition: clip-path var(--transition-cosmic-base)` for smooth cutout movement
- Fallback for elements not found: skip the step and advance to next

---

## 2. Tooltip Positioning Strategy

### Decision: Manual viewport-aware positioning (no library)

### Rationale
The tooltip must appear near the highlighted element without overflowing the viewport. With only 9 fixed tour steps targeting known layout elements, a full positioning engine is unnecessary.

### Algorithm
1. Get target element rect via `getBoundingClientRect()`
2. Each step defines a `preferredPlacement` (top, bottom, left, right)
3. Check if preferred placement fits within viewport with 16px margin
4. If not, flip to opposite side; if still no fit, use bottom (most space available in typical layouts)
5. On mobile (<768px), ignore placement and render as bottom sheet (fixed to bottom of viewport)

### Alternatives Considered
- **Floating UI / Popper.js** — Full-featured positioning library. Rejected: adds dependency, overkill for 9 static targets with known positions.
- **Radix Tooltip positioning** — Already in the project but designed for hover tooltips, not persistent positioned panels with navigation controls.

---

## 3. Tour State Persistence

### Decision: localStorage with `solune-onboarding-completed` key

### Rationale
Follows the exact pattern established by `useSidebarState` (`sidebar-collapsed` key) and `ThemeProvider` (`vite-ui-theme` key). All existing client-side persistence uses localStorage with try/catch error handling for quota/privacy exceptions.

### State Shape
- `solune-onboarding-completed`: `"true"` or absent (no value = first-time user)
- Tour step index is ephemeral React state (not persisted) — if user refreshes mid-tour, it restarts from step 1 or doesn't show if already completed

### Alternatives Considered
- **Backend API persistence** — Would survive across devices/browsers. Rejected: spec explicitly states "no backend changes required" and the tour is a one-time UX affordance where cross-device sync has no meaningful benefit.
- **sessionStorage** — Would limit to current tab. Rejected: user who closes and reopens browser should not see the tour again.

---

## 4. Tour Step Target Identification

### Decision: `data-tour-step` HTML attributes on existing elements

### Rationale
CSS class-based selectors are fragile — classes change during styling updates. ID-based selectors conflict with React Router's DOM management. Data attributes are:
- Semantically clear (`data-tour-step="sidebar-nav"` reads as intent)
- Stable across refactors (unlikely to be accidentally removed during styling changes)
- Standard HTML (no special React handling needed)
- Easy to query: `document.querySelector('[data-tour-step="sidebar-nav"]')`

### Mapping
| Step | data-tour-step | Target Component | File |
|------|----------------|------------------|------|
| 1 | (none — centered welcome) | N/A | N/A |
| 2 | `sidebar-nav` | `<nav>` element in Sidebar.tsx | `layout/Sidebar.tsx` |
| 3 | `project-selector` | Project selector button in Sidebar.tsx | `layout/Sidebar.tsx` |
| 4 | `chat-toggle` | ChatPopup toggle button | `components/chat/ChatPopup.tsx` |
| 5 | `projects-link` | NavLink for `/projects` | `layout/Sidebar.tsx` |
| 6 | `pipeline-link` | NavLink for `/pipeline` | `layout/Sidebar.tsx` |
| 7 | `agents-link` | NavLink for `/agents` | `layout/Sidebar.tsx` |
| 8 | `theme-toggle` | Theme toggle button (Sun/Moon) in Sidebar brand | `layout/Sidebar.tsx` |
| 9 | `help-link` | NavLink for `/help` | `layout/Sidebar.tsx` |

### Alternatives Considered
- **Element IDs** — Globally unique but intrusive; React Router and rehydration can conflict with static IDs for repeated elements.
- **CSS selector strings** — e.g., `.sidebar nav a:nth-child(2)`. Fragile, breaks if nav order changes.

---

## 5. Sidebar Auto-Expand During Tour

### Decision: Tour orchestrator temporarily expands sidebar for sidebar-related steps

### Rationale
Steps 2, 3, 5, 6, 7, 8, 9 target elements inside the sidebar. If the sidebar is collapsed (`w-16`), these elements either don't render (labels hidden) or are too small to meaningfully spotlight. The tour must ensure visibility.

### Approach
1. On entering a sidebar-related step, check `isCollapsed` state
2. If collapsed, call `toggle()` from `useSidebarState` to expand
3. Store the pre-tour collapsed state
4. On tour completion/skip, restore the original collapsed state
5. Pass `sidebarState` to `SpotlightTour` via props from `AppLayout` (where both sidebar and tour are mounted)

---

## 6. Help Page Section Architecture

### Decision: Single scrollable page with anchor-linked sections

### Rationale
A tabbed interface adds navigation complexity within a help page. A single scrollable page with clear section headings is simpler and allows users to scan all content without clicking. Anchor links from the hero section provide quick jumps.

### Sections (order)
1. **Hero** — `CelestialCatalogHero` with "Replay Tour" action button
2. **Getting Started** — 3 cards: "Create a Project", "Build a Pipeline", "Chat with Solune"
3. **FAQ** — `FaqAccordion` with 12 entries grouped by category
4. **Feature Guides** — Grid of `FeatureGuideCard` components (one per major feature)
5. **Slash Commands** — Table rendered from `getAllCommands()` registry function

### Alternatives Considered
- **Tabbed layout** — Separates FAQ, Guides, Commands into tabs. Rejected: adds complexity, hides content behind clicks, no SEO benefit in SPA.
- **Separate sub-routes** — `/help/faq`, `/help/guides`, etc. Rejected: over-engineering for the amount of content; a single page is simpler and faster.

---

## 7. FAQ Accordion Implementation

### Decision: Custom accordion using React state (no Radix Accordion dependency)

### Rationale
The FAQ has 12 items in 4 groups. A simple `useState<string | null>` tracking the currently open item ID is sufficient. Adding `@radix-ui/react-accordion` would be a new dependency.

### Behavior
- One item open at a time (exclusive toggle) — reduces visual noise
- Click to expand, click again to collapse
- Animated with `grid-rows: 0fr → 1fr` transition + `.celestial-fade-in` on content
- Gold chevron rotates 180° on expand
- Keyboard: Enter/Space toggles, Tab navigates between items

### Alternatives Considered
- **Radix Accordion** — Full-featured accessible accordion. Rejected: new dependency for a simple component; we'll implement the same accessibility (keyboard nav, ARIA attributes) directly.
- **All items open simultaneously** — Multi-select accordion. Rejected: with 12 items, the page would become unwieldy; exclusive toggle keeps it scannable.

---

## 8. SVG Icon Style

### Decision: Monochrome line-art with `currentColor` stroke, 24×24 viewBox

### Rationale
Matches the Cleric hand logo aesthetic: geometric, thin strokes, clean lines. Using `currentColor` for stroke means icons automatically adapt to light/dark theme without CSS overrides.

### Specifications
- ViewBox: `0 0 24 24`
- Stroke width: 1.5
- Stroke: `currentColor`
- Fill: `none` (line-art only)
- No inline colors — all theming via CSS `color` property
- File format: `.svg` imported as React components via Vite's SVG handling

---

## 9. Focus Trap Implementation

### Decision: Manual focus trap using `focusTrapRef` with Tab/Shift+Tab interception

### Rationale
The tour tooltip must trap focus while active (FR-014). A manual implementation avoids a new dependency (e.g., `focus-trap-react`) and is straightforward for a single dialog-like element.

### Approach
1. On tooltip mount, query all focusable elements within the tooltip container
2. On Tab press, if focus is on last element, move to first element
3. On Shift+Tab, if focus is on first element, move to last element
4. On tooltip unmount, restore focus to the previously focused element
5. Use `role="dialog"` and `aria-modal="true"` on tooltip container
6. Use `aria-live="polite"` on a visually hidden region for step change announcements

---

## 10. Mobile Bottom Sheet Strategy

### Decision: Media query to conditionally render tooltip as fixed bottom panel on viewports <768px

### Rationale
On mobile, positioned tooltips near sidebar elements will clip against viewport edges. A fixed bottom sheet is the standard mobile pattern for contextual information.

### Approach
- Use `window.matchMedia('(max-width: 767px)')` in `SpotlightTooltip`
- On mobile: render tooltip as `fixed bottom-0 left-0 right-0` with `rounded-t-2xl` and swipe-up animation
- On desktop: render as positioned popover near target element
- The spotlight overlay cutout still highlights the target element on mobile
- Bottom sheet has a drag handle indicator (small gray bar) at top for visual affordance
