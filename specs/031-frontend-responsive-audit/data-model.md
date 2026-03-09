# Data Model: Full Frontend Responsiveness & Mobile-Friendly Audit

**Feature**: 031-frontend-responsive-audit | **Date**: 2026-03-09

## Frontend Types (TypeScript)

### Breakpoint Tokens (New)

```typescript
/**
 * Centralized breakpoint values matching Tailwind v4 defaults.
 * CSS custom properties (--bp-*) in index.css mirror these values.
 * Used by useMediaQuery hook and E2E viewport test definitions.
 */
export const BREAKPOINTS = {
  xs: 320,   // Small mobile (minimum supported)
  sm: 640,   // Small breakpoint (Tailwind sm:)
  md: 768,   // Medium breakpoint (Tailwind md:) — mobile/tablet threshold
  lg: 1024,  // Large breakpoint (Tailwind lg:) — tablet landscape / small desktop
  xl: 1280,  // Extra large (Tailwind xl:) — desktop
  '2xl': 1440, // 2x Extra large — large desktop
} as const;

export type BreakpointKey = keyof typeof BREAKPOINTS;
```

### useMediaQuery Hook (New)

```typescript
/**
 * Programmatic media query hook using native window.matchMedia.
 * Subscribes to viewport changes and returns a boolean match state.
 * Used for conditional rendering (e.g., mobile drawer vs. desktop sidebar).
 */
function useMediaQuery(query: string): boolean;

// Convenience variants:
function useIsMobile(): boolean;  // Returns true when viewport < 768px (md breakpoint)
```

### Sidebar State Types (Modified)

```typescript
/**
 * Extended sidebar state to support mobile drawer behavior.
 * Existing: isCollapsed, toggle (desktop collapse)
 * New: isMobileOpen, openMobile, closeMobile (mobile drawer)
 */
interface SidebarState {
  /** Desktop: sidebar is collapsed to icon-only mode (64px) */
  isCollapsed: boolean;
  /** Desktop: toggle collapse state */
  toggle: () => void;
  /** Mobile: drawer is open (overlay visible) */
  isMobileOpen: boolean;
  /** Mobile: open the drawer */
  openMobile: () => void;
  /** Mobile: close the drawer */
  closeMobile: () => void;
}
```

### Button Component Size Variants (Modified)

```typescript
/**
 * Extended button size variants to include touch-friendly size.
 * Existing: default, sm, lg, icon
 * New: touch — ensures 44×44px minimum hit area
 */
type ButtonSize = 'default' | 'sm' | 'lg' | 'icon' | 'touch';

// CVA variant definition:
// touch: 'min-h-[44px] min-w-[44px] px-4 py-2'
```

---

## CSS Custom Properties (New)

### Responsive Breakpoint Tokens

Added to `frontend/src/index.css` within the `@theme` block:

```css
@theme {
  /* Responsive breakpoint tokens (FR-009) */
  --bp-xs: 320px;
  --bp-sm: 640px;
  --bp-md: 768px;
  --bp-lg: 1024px;
  --bp-xl: 1280px;
  --bp-2xl: 1440px;
}
```

### Touch Target Utility

Added to `frontend/src/index.css`:

```css
/* Touch target minimum size (WCAG 2.5.8) — FR-002 */
.touch-target {
  min-height: 44px;
  min-width: 44px;
}
```

---

## Responsive Behavior Patterns

### Sidebar Modes

```text
┌────────────────────────────────────────────────────────────┐
│                    VIEWPORT WIDTH                           │
│                                                            │
│  < 768px (Mobile)          │  ≥ 768px (Tablet/Desktop)     │
│                            │                               │
│  Sidebar: HIDDEN           │  Sidebar: VISIBLE             │
│  (display: none)           │  (flex, shrink-0)             │
│                            │                               │
│  Hamburger: VISIBLE        │  Hamburger: HIDDEN            │
│  (in TopBar, md:hidden)    │  (md:hidden)                  │
│                            │                               │
│  Drawer: AVAILABLE         │  Collapse: AVAILABLE          │
│  (isMobileOpen state)      │  (isCollapsed state)          │
│  - Full-height overlay     │  - Toggle 240px ↔ 64px        │
│  - Semi-transparent        │  - Persisted in localStorage  │
│    backdrop                │                               │
│  - Close on route change   │                               │
│  - Close on backdrop tap   │                               │
│  - Slide-in animation      │                               │
│    (translate-x)           │                               │
└────────────────────────────────────────────────────────────┘
```

### Modal Responsive Pattern

```text
┌────────────────────────────────────────────────────────────┐
│                    VIEWPORT WIDTH                           │
│                                                            │
│  < 640px (Mobile)          │  ≥ 640px (Tablet/Desktop)     │
│                            │                               │
│  Modal: FULL-SCREEN        │  Modal: CENTERED OVERLAY      │
│  - w-screen h-screen       │  - max-w-lg / max-w-2xl      │
│  - rounded-none            │  - rounded-lg                 │
│  - m-0                     │  - centered with backdrop     │
│  - Scrollable body         │  - backdrop tap to close      │
│  - 44px close button       │  - standard close button      │
│  - No backdrop dismiss     │                               │
└────────────────────────────────────────────────────────────┘
```

### Board Responsive Pattern

```text
┌────────────────────────────────────────────────────────────┐
│                    VIEWPORT WIDTH                           │
│                                                            │
│  < 768px (Mobile)          │  ≥ 768px (Tablet/Desktop)     │
│                            │                               │
│  Board: HORIZONTAL SCROLL  │  Board: GRID LAYOUT           │
│  - overflow-x-auto         │  - flex with wrap             │
│  - snap-x snap-mandatory   │  - Columns side by side       │
│  - Each column ~85vw       │  - Auto-sized columns         │
│  - Swipe between columns   │  - All columns visible        │
│  - Position indicator      │                               │
│    (e.g., 2/5)             │                               │
└────────────────────────────────────────────────────────────┘
```

### Grid Responsive Pattern (Agents, Tools, Chores)

```text
┌────────────────────────────────────────────────────────────┐
│  Breakpoint      │  Grid Columns  │  Card Width            │
│──────────────────│────────────────│────────────────────────│
│  < 640px (xs/sm) │  1 column      │  Full width            │
│  640–767px (sm)  │  1 column      │  Full width            │
│  768–1023px (md) │  2 columns     │  ~50% width            │
│  1024–1279px (lg)│  2–3 columns   │  ~33–50% width         │
│  ≥ 1280px (xl+)  │  3 columns     │  ~33% width            │
└────────────────────────────────────────────────────────────┘
```

---

## E2E Test Viewport Definitions (Modified)

```typescript
/**
 * Extended viewport definitions for comprehensive responsive testing.
 * Covers all FR-001 required breakpoints.
 */
export const VIEWPORTS = {
  // Existing
  mobile: { width: 375, height: 667 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1280, height: 800 },
  // New
  mobileSmall: { width: 320, height: 568 },    // iPhone SE / minimum supported
  mobileLarge: { width: 390, height: 844 },     // iPhone 14 / modern phone
  desktopLarge: { width: 1440, height: 900 },   // Large desktop / minimum "2xl"
} as const;
```

---

## Database Changes

### No Schema Changes Required

This feature is entirely frontend. No database tables, columns, or migrations are needed.

---

## localStorage Keys

### Existing Key (No Changes)

| Key | Type | Purpose |
|-----|------|---------|
| `sidebar-collapsed` | `string` (`"true"` / `"false"`) | Desktop sidebar collapse state. Unaffected by mobile drawer state. |

No new localStorage keys are introduced. The mobile drawer open/close state is ephemeral — it resets on page load and closes on route navigation.

---

## Accessibility Attributes

### Mobile Navigation Drawer

```html
<!-- Hamburger trigger in TopBar (mobile only) -->
<button
  aria-label="Open navigation menu"
  aria-expanded="false|true"
  aria-controls="mobile-sidebar"
  class="md:hidden touch-target"
>
  <Menu className="h-6 w-6" />  <!-- or X when open -->
</button>

<!-- Sidebar drawer (mobile) -->
<nav
  id="mobile-sidebar"
  role="navigation"
  aria-label="Main navigation"
  class="fixed inset-y-0 left-0 z-40 w-72 transform transition-transform"
>
  <!-- Same content as desktop Sidebar -->
</nav>

<!-- Backdrop -->
<div
  aria-hidden="true"
  class="fixed inset-0 z-30 bg-black/50"
  onClick={closeMobile}
/>
```

### Touch Target Elements

All interactive elements on mobile viewports include:
- `min-height: 44px; min-width: 44px;` (via `.touch-target` class or Button `touch` variant)
- Sufficient padding around the visual element to meet the 44×44px hit area
- `touch-action: manipulation` where appropriate to prevent double-tap zoom

---

## Component Inventory

### Pages Requiring Responsive Fixes

| Page | Priority | Key Issues |
|------|----------|------------|
| AppPage (Dashboard) | P1 | Hero section already responsive; check card grids |
| ProjectsPage | P1 | Project card grid; board columns horizontal scroll |
| AgentsPipelinePage | P1 | Pipeline board horizontal scroll; stage cards |
| AgentsPage | P1 | Agent grid already uses `md:grid-cols-2 xl:grid-cols-3`; touch targets |
| ToolsPage | P2 | Similar to AgentsPage; modal full-screen |
| ChoresPage | P2 | Similar to AgentsPage; schedule config forms |
| SettingsPage | P2 | Form layouts; tab navigation on mobile |
| LoginPage | P3 | Simple centered layout; likely already OK |
| NotFoundPage | P3 | Simple; likely already OK |

### Layout Components Requiring Changes

| Component | Changes |
|-----------|---------|
| AppLayout.tsx | Mobile drawer overlay, conditional sidebar rendering |
| Sidebar.tsx | Hidden on mobile (`hidden md:flex`), drawer mode on mobile |
| TopBar.tsx | Hamburger button (`md:hidden`), responsive padding |
| RateLimitBar.tsx | Already hidden on mobile (`hidden md:flex`) — verified OK |

### Modal Components Requiring Full-Screen Mobile Pattern

| Modal | Current Width | Mobile Pattern |
|-------|---------------|----------------|
| AddAgentModal | max-w-lg | Full-screen |
| AgentIconPickerModal | max-w-md | Full-screen |
| AddChoreModal | max-w-lg | Full-screen |
| ConfirmChoreModal | max-w-md | Full-screen |
| ToolSelectorModal | max-w-2xl | Full-screen |
| UploadMcpModal | max-w-lg | Full-screen |
| EditRepoMcpModal | max-w-lg | Full-screen |
| CleanUpConfirmModal | max-w-md | Full-screen |
| IssueDetailModal | max-w-2xl | Full-screen |
| BulkModelUpdateDialog | max-w-md | Full-screen |
| UnsavedChangesDialog | max-w-sm | Full-screen |
| ConfirmationDialog | max-w-md | Full-screen |
