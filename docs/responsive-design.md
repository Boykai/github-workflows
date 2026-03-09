# Responsive Design

This document describes the responsive design system used by the Agent Projects frontend: breakpoints, CSS tokens, layout patterns, hooks, accessibility standards, and testing strategy.

## Breakpoints

The application defines six responsive breakpoints covering mobile through large desktop. These are defined in two places that must stay in sync:

| Token | CSS Variable | TS Constant | Width | Typical Device |
|-------|-------------|-------------|-------|----------------|
| xs | `--bp-xs` | `BREAKPOINTS.xs` | 320 px | Small phones |
| sm | `--bp-sm` | `BREAKPOINTS.sm` | 640 px | Large phones |
| md | `--bp-md` | `BREAKPOINTS.md` | 768 px | Tablets |
| lg | `--bp-lg` | `BREAKPOINTS.lg` | 1024 px | Small laptops |
| xl | `--bp-xl` | `BREAKPOINTS.xl` | 1280 px | Desktops |
| 2xl | `--bp-2xl` | `BREAKPOINTS['2xl']` | 1440 px | Large desktops |

- **CSS custom properties** are declared in `frontend/src/index.css` inside the `@theme` block (e.g., `--bp-md: 768px`).
- **TypeScript constants** are declared in `frontend/src/constants.ts` as the `BREAKPOINTS` object.

Tailwind CSS 4 uses the CSS custom properties directly. The TypeScript constants are used by hooks and E2E tests.

## Layout System

### Desktop (≥ 768 px)

The app uses a horizontal layout with a collapsible inline sidebar and a top bar:

```text
┌──────────────────────────────────────────┐
│ TopBar (breadcrumb, notifications, user) │
├──────┬───────────────────────────────────┤
│ Side │                                   │
│ bar  │        Main Content               │
│      │                                   │
└──────┴───────────────────────────────────┘
```

The sidebar collapses to an icon-only rail. Collapse state is persisted to `localStorage`.

### Mobile (< 768 px)

The sidebar is hidden. A hamburger button appears in the top bar. Tapping it opens the sidebar as a full-height overlay drawer with a semi-transparent backdrop. The drawer auto-closes on route changes.

```text
┌──────────────────────────┐
│ ☰ TopBar                 │
├──────────────────────────┤
│                          │
│     Main Content         │
│                          │
└──────────────────────────┘
```

### Modal Components

Modals follow a dual pattern:

- **Large form modals** (e.g., AddAgentModal, IssueDetailModal, ToolSelectorModal) go full-screen on small viewports using: `max-sm:max-w-none max-sm:h-full max-sm:rounded-none max-sm:border-0`.
- **Small confirmation dialogs** (e.g., UnsavedChangesDialog, ConfirmChoreModal) use `max-sm:h-auto` instead of `h-full` to remain compact.

## Hooks

### `useMediaQuery(query: string): boolean`

Generic hook that wraps `window.matchMedia`. SSR-safe (defaults to `false` when `window` is unavailable). Defined in `frontend/src/hooks/useMediaQuery.ts`.

### `useIsMobile(): boolean`

Convenience wrapper that returns `true` when the viewport is below the `md` breakpoint (< 768 px). Uses `useMediaQuery` internally.

### `useSidebarState()`

Manages sidebar state for both desktop and mobile. Returns:

| Property | Type | Description |
|----------|------|-------------|
| `isCollapsed` | `boolean` | Desktop sidebar collapse state (persisted to `localStorage`) |
| `toggle` | `() => void` | Toggle desktop collapse |
| `isMobileOpen` | `boolean` | Mobile drawer open state |
| `openMobile` | `() => void` | Open mobile drawer |
| `closeMobile` | `() => void` | Close mobile drawer |

Defined in `frontend/src/hooks/useSidebarState.ts`.

## Touch Targets

All interactive elements on mobile must meet the WCAG 2.5.8 minimum of 44 × 44 px. The `.touch-target` utility class in `index.css` enforces this:

```css
.touch-target {
  min-height: 44px;
  min-width: 44px;
}
```

Apply this class to buttons, icon buttons, and other tap targets that might otherwise be too small on mobile.

## Responsive Testing

### E2E Viewport Presets

E2E tests use standardized viewport sizes defined in `frontend/e2e/viewports.ts`:

| Preset | Width × Height | Purpose |
|--------|---------------|---------|
| `mobileSmall` | 320 × 568 | Smallest supported phone |
| `mobile` | 375 × 667 | Standard phone (iPhone SE) |
| `mobileLarge` | 390 × 844 | Modern phone (iPhone 14) |
| `tablet` | 768 × 1024 | Tablet (iPad) |
| `desktopSmall` | 1024 × 768 | Small laptop / large tablet landscape |
| `desktop` | 1280 × 800 | Standard desktop |
| `desktopLarge` | 1440 × 900 | Large desktop |

### E2E Test Files

| File | What It Tests |
|------|---------------|
| `responsive-layouts.spec.ts` | No horizontal overflow at each viewport; page layout integrity |
| `responsive-navigation.spec.ts` | Hamburger menu visibility, sidebar drawer open/close, route navigation on mobile |
| `responsive-touch-targets.spec.ts` | Minimum 44 × 44 px size for interactive elements on mobile viewports |
| `responsive-typography.spec.ts` | Font scaling, readability, and text overflow at each breakpoint |
| `responsive-board.spec.ts` | Project board layout, card reflow, and column stacking on small screens |
| `responsive-home.spec.ts` | Home/landing page layout across breakpoints |
| `responsive-settings.spec.ts` | Settings page form layout and input usability on mobile |

### Running Responsive Tests

```bash
cd frontend

# Run all E2E tests (includes responsive)
npm run test:e2e

# Run only responsive tests
npx playwright test --grep "responsive"

# Run with browser visible
npm run test:e2e:headed
```

### Unit Tests

Responsive hooks and components have co-located unit tests:

- `hooks/useMediaQuery.test.ts` — media query matching and SSR fallback
- `hooks/useSidebarState.test.ts` — collapse persistence, mobile drawer state, auto-close on route change
- `layout/Sidebar.test.tsx` — desktop sidebar and mobile drawer rendering
- `layout/TopBar.test.tsx` — hamburger button visibility and mobile menu toggle
- `constants.test.ts` — breakpoint constant values and CSS token alignment

## Adding a New Responsive Component

1. Use Tailwind responsive prefixes (`sm:`, `md:`, `lg:`, etc.) for layout changes.
2. Use the centralized `BREAKPOINTS` constant or CSS variables (`--bp-*`) — do not hard-code pixel values in media queries.
3. Apply `.touch-target` to interactive elements that need to meet the 44 × 44 px minimum.
4. For modals, follow the existing full-screen mobile pattern (`max-sm:max-w-none max-sm:h-full max-sm:rounded-none max-sm:border-0`).
5. Test at all six viewport presets (import `VIEWPORTS` from `e2e/viewports.ts`).
6. Ensure no horizontal scrollbar appears at any breakpoint.
