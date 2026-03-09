# Data Model: Frontend Style Audit & Celestial/Cosmic Theme Animation Enhancement

**Feature**: 031-celestial-theme-animations | **Date**: 2026-03-09

## Overview

This feature is a pure frontend visual/animation enhancement with no database, API, or persistent state changes. The "data model" for this feature consists of: (1) CSS design token definitions, (2) TypeScript component prop interfaces, (3) the audit tracking structure, and (4) animation state definitions.

## Design Token Catalog

### Existing Motion Tokens (in `index.css` @theme block)

| Token | Value | Usage |
|-------|-------|-------|
| `--transition-cosmic-fast` | `200ms ease` | Button hovers, input focus, quick micro-interactions |
| `--transition-cosmic-base` | `400ms ease-in-out` | Card hover lifts, panel transitions, theme switch |
| `--transition-cosmic-slow` | `800ms ease-in-out` | Halo glow pulses, orbit border transitions |
| `--transition-cosmic-drift` | `1600ms ease-in-out` | Background gradient shifts, ambient decorative motion |

### Existing Animation Tokens

| Token | Keyframe | Duration | Usage |
|-------|----------|----------|-------|
| `--animate-twinkle` | `twinkle` | 3s infinite | Small decorative star dots |
| `--animate-pulse-glow` | `pulse-glow` | 4s infinite | Halo/badge/indicator glow |
| `--animate-orbit-spin` | `orbit-spin` | 24s infinite | Decorative orbit rings |
| `--animate-shimmer` | `shimmer` | 2s infinite | Loading skeleton sweep |
| `--animate-float` | `float` | 6s infinite | Hero decorative bodies drift |
| `--animate-cosmic-fade-in` | `cosmic-fade-in` | 0.5s both | Entry animation for cards/sections |
| `--animate-star-wink` | `star-wink` | 5s infinite | Background star disappear/reappear |

### New Tokens to Add

| Token | Value | Usage | Traces To |
|-------|-------|-------|-----------|
| `--animate-celestial-loader` | `orbit-spin 1.8s linear infinite` | Loading spinner orbital speed | FR-005 |
| `--transition-theme-shift` | `600ms ease-in-out` | Theme toggle transition duration | FR-006 |

### Existing Keyframes

```
twinkle:       0%,100% → opacity:0.4, scale(1) | 50% → opacity:1, scale(1.3)
pulse-glow:    0%,100% → box-shadow 8px | 50% → box-shadow 24px+48px
orbit-spin:    0deg → 360deg
shimmer:       -200% → 200% background-position
float:         0%,100% → translateY(0) | 50% → translateY(-6px)
cosmic-fade-in: opacity:0, translateY(8px), scale(0.98) → opacity:1, translateY(0), scale(1)
star-wink:     0%,80%,100% → opacity:1 | 90% → opacity:0.3
cosmic-gradient-cycle: 0% → 50% → 100% background-position shift
```

### New Keyframes to Add

| Keyframe | Definition | Usage | Traces To |
|----------|------------|-------|-----------|
| `theme-shift` | `0% { opacity: 0 } → 50% { opacity: 0.3 } → 100% { opacity: 0 }` | Gradient overlay during theme toggle | FR-006 |

### Existing Color Tokens (Celestial Palette)

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--glow` | `47 100% 79%` | `47 100% 79%` | Halo glow, decorative highlights |
| `--gold` | `42 92% 52%` | `42 84% 42%` | Gold accents, primary warm color |
| `--night` | `226 28% 19%` | `226 28% 12%` | Deep blue, shadow depth |
| `--star` | `38 72% 42%` | `38 60% 52%` | Star dot color (warm amber) |
| `--star-soft` | `43 84% 62%` | `43 70% 58%` | Soft star color (light gold) |

## Component Interfaces

### CelestialLoader (NEW)

```typescript
interface CelestialLoaderProps {
  /** Size variant controlling the orbit radius and dot sizes */
  size?: 'sm' | 'md' | 'lg';
  /** Accessible label for the loading state */
  label?: string;
  /** Additional CSS classes */
  className?: string;
}

// Size mappings
const sizes = {
  sm: { orbit: 'h-8 w-8', sun: 'h-2 w-2', planet: 'h-1.5 w-1.5' },
  md: { orbit: 'h-12 w-12', sun: 'h-3 w-3', planet: 'h-2 w-2' },
  lg: { orbit: 'h-16 w-16', sun: 'h-4 w-4', planet: 'h-2.5 w-2.5' },
};
```

**Renders**: A `<div role="status">` containing:
1. Central sun dot (`rounded-full bg-primary celestial-pulse-glow`)
2. Orbital ring (`rounded-full border border-primary/30 celestial-orbit-spin-fast`)
3. Planet dot on the orbit ring
4. Optional text label below (`<span className="sr-only">` for screen readers, visible label optional)

### ThemeProvider Updates

```typescript
// Existing interface (no changes)
interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: 'dark' | 'light' | 'system';
  storageKey?: string;
}

// Behavioral change in setTheme():
// 1. Add 'theme-transitioning' class to document.documentElement
// 2. Toggle light/dark class (existing behavior)
// 3. Remove 'theme-transitioning' class after 600ms timeout
```

## Animation Utility Class Catalog

### Existing Utility Classes (no changes needed)

| Class | Animation | Applies To |
|-------|-----------|------------|
| `celestial-twinkle` | `twinkle 3s` | Small star dots |
| `celestial-twinkle-delayed` | `twinkle 3s` (delay 1.5s) | Secondary star dots |
| `celestial-twinkle-slow` | `twinkle 5s` (delay 0.8s) | Background stars |
| `celestial-pulse-glow` | `pulse-glow 4s` | Halo/glow indicators |
| `celestial-orbit-spin` | `orbit-spin 24s` | Decorative orbit rings |
| `celestial-orbit-spin-reverse` | `orbit-spin 30s reverse` | Counter-rotating orbits |
| `celestial-orbit-spin-fast` | `orbit-spin 0.8s` | Loading spinner orbit |
| `celestial-float` | `float 6s` | Hero illustrations |
| `celestial-float-delayed` | `float 6s` (delay 2s) | Secondary floating bodies |
| `celestial-star-wink` | `star-wink 5s` | Background star wink |
| `celestial-shimmer` | `shimmer 2s` + gradient bg | Loading skeletons |
| `celestial-fade-in` | `cosmic-fade-in 0.5s` | Card/section entry |
| `cosmic-gradient-shift` | `cosmic-gradient-cycle 12s` | Hero/feature sections |
| `celestial-panel` | Transition (box-shadow, border, transform) | Card hover lift |
| `solar-halo` | Transition (box-shadow) | Halo pulse on hover |
| `lunar-disc` | Transition (box-shadow) | Moon disc glow |
| `celestial-focus` | Focus-visible glow ring | Interactive element focus |
| `solar-action` | Transition + hover lift | Button hover enhancement |
| `starfield` | Pseudo-element star dots + twinkle | Background star field |

### New Utility Classes to Add

| Class | Purpose | CSS | Traces To |
|-------|---------|-----|-----------|
| `theme-transitioning` | Theme switch overlay | Applies cosmic gradient overlay with `theme-shift` keyframe; `transition: background-color var(--transition-theme-shift), color var(--transition-theme-shift)` | FR-006 |

## Audit Tracking Structure

### Component Audit Entry (for style alignment report)

```typescript
// Conceptual structure — documented in STYLE_AUDIT.md, not code
interface StyleAuditEntry {
  component: string;           // e.g., "AgentCard.tsx"
  directory: string;           // e.g., "components/agents"
  tokenViolations: string[];   // Hard-coded values found and corrected
  casingChanges: string[];     // Text casing corrections applied
  animationsAdded: string[];   // Celestial animation classes added
  accessibilityNotes: string;  // Focus, contrast, ARIA observations
}
```

### Audit Scope (Component Inventory)

| Directory | File Count | Categories |
|-----------|-----------|------------|
| `components/agents/` | 11 | Cards, modals, panels, editors |
| `components/board/` | 30 | Board, columns, cards, overlays, popovers |
| `components/chat/` | 15 | Interface, toolbar, bubbles, previews |
| `components/chores/` | 9 | Cards, modals, panels, config |
| `components/common/` | 6 | Hero, error boundary, icons, empty states |
| `components/pipeline/` | 11 | Board, graph, nodes, cards, selectors |
| `components/settings/` | 12 | Settings sections, preferences, dropdowns |
| `components/tools/` | 10 | Cards, modals, panels, selectors |
| `components/ui/` | 5 | Button, card, input, tooltip, dialog |
| `layout/` | 8 | AppLayout, sidebar, topbar, breadcrumb, selectors |
| `pages/` | 9 | All route pages |
| **Total** | **~126** | |

## State Transitions

### Theme Transition State Machine

```
IDLE ──(user clicks toggle)──> TRANSITIONING ──(600ms timeout)──> IDLE

IDLE:
  - No 'theme-transitioning' class on html
  - Normal rendering

TRANSITIONING:
  - 'theme-transitioning' class added to html
  - Cosmic gradient overlay fades in/out
  - background-color and color transition smoothly
  - After 600ms: class removed, return to IDLE
```

### Animation Lifecycle (per component)

```
UNMOUNTED ──(component mounts)──> FADE_IN ──(animation ends)──> STATIC

STATIC ──(hover/focus)──> INTERACTIVE ──(blur/leave)──> STATIC

INTERACTIVE:
  - celestial-panel: box-shadow lift + glow
  - solar-action: translateY(-1px) + glow
  - celestial-focus: focus-visible glow ring

REDUCED_MOTION (prefers-reduced-motion: reduce):
  - All keyframe animations: animation: none
  - All transitions: transition: none
  - All transforms on hover: transform: none
  - celestial-fade-in: instant opacity: 1
```

## Accessibility Data

### Contrast Requirements

| Element | Minimum Ratio | Standard |
|---------|--------------|----------|
| Normal text (< 18px / < 14px bold) | 4.5:1 | WCAG AA |
| Large text (≥ 18px / ≥ 14px bold) | 3:1 | WCAG AA |
| UI components (borders, icons) | 3:1 | WCAG AA |

### Focus Indicator Requirements

- All interactive elements must have `focus-visible` outline
- The `celestial-focus` utility provides a themed glow ring: `0 0 0 2px var(--background), 0 0 0 4px var(--primary/0.5), 0 0 16px var(--glow/0.2)`
- Focus indicators must remain visible during and after animations

### Reduced Motion Behavior

- All classes listed in the `@media (prefers-reduced-motion: reduce)` block have `animation: none !important`
- All transition-based classes have `transition: none !important`
- `celestial-fade-in` shows content immediately with `opacity: 1`
- `solar-action:hover` transform is `none` (no lift effect)
- Static arrangement of decorative elements remains visible (orbits, stars) but without motion

## localStorage Keys

No new localStorage keys introduced. The existing `vite-ui-theme` key (used by `ThemeProvider`) remains unchanged.

## API Changes

None. This feature is entirely frontend CSS and component markup changes with zero backend impact.
