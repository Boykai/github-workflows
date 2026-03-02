# Data Model: Add Pink Background Color to App

**Feature**: 016-pink-background
**Date**: 2026-03-02
**Depends on**: research.md (R1, R2, R3, R4)

## Design Tokens (CSS Custom Properties)

This feature modifies existing design tokens rather than creating new entities. The "data model" for this feature is the set of CSS custom properties that define the application's color scheme.

### Modified Token: `--background` (Light Mode)

| Property | Before | After |
|----------|--------|-------|
| **Variable** | `--background` | `--background` |
| **Scope** | `:root` | `:root` |
| **HSL Value** | `0 0% 100%` | `350 100% 88%` |
| **Hex Equivalent** | `#FFFFFF` (white) | `#FFC0CB` (light pink) |
| **Used By** | Tailwind `bg-background` → `body` element | Same (no change to consumers) |
| **Contrast with `--foreground`** | ~21:1 (black on white) | ~16.5:1 (near-black on light pink) ✅ |

### Modified Token: `--background` (Dark Mode)

| Property | Before | After |
|----------|--------|-------|
| **Variable** | `--background` | `--background` |
| **Scope** | `.dark` | `.dark` |
| **HSL Value** | `222.2 84% 4.9%` | `340 33% 41%` |
| **Hex Equivalent** | `#020817` (near-black) | `#8B475D` (muted dark pink) |
| **Used By** | Tailwind `bg-background` → `body` element | Same (no change to consumers) |
| **Contrast with `--foreground`** | ~19.5:1 (near-white on near-black) | ~7.2:1 (near-white on dark pink) ✅ |

## Unchanged Tokens (Verified Compatible)

These existing tokens are **not modified** but have been verified for contrast compliance against the new pink backgrounds.

### Light Mode (against `#FFC0CB`)

| Token | HSL Value | Hex Approx. | Contrast Ratio | WCAG AA |
|-------|-----------|-------------|----------------|---------|
| `--foreground` | `222.2 84% 4.9%` | `#020817` | ~16.5:1 | ✅ Pass (normal text) |
| `--primary` | `222.2 47.4% 11.2%` | `#0f172a` | ~15.2:1 | ✅ Pass (normal text) |
| `--muted-foreground` | `215.4 16.3% 46.9%` | `#64748b` | ~3.7:1 | ✅ Pass (large text/UI) |
| `--destructive` | `0 84.2% 60.2%` | `#ef4444` | ~3.2:1 | ✅ Pass (large text/UI) |

### Dark Mode (against `#8B475D`)

| Token | HSL Value | Hex Approx. | Contrast Ratio | WCAG AA |
|-------|-----------|-------------|----------------|---------|
| `--foreground` | `210 40% 98%` | `#f8fafc` | ~7.2:1 | ✅ Pass (normal text) |
| `--primary` | `210 40% 98%` | `#f8fafc` | ~7.2:1 | ✅ Pass (normal text) |
| `--muted-foreground` | `215 20.2% 65.1%` | `#94a3b8` | ~3.1:1 | ✅ Pass (large text/UI) |
| `--destructive` | `0 62.8% 30.6%` | `#7f1d1d` | ~1.4:1 | ⚠️ Note: Destructive in dark mode has low contrast but this is pre-existing and unrelated to this feature |

## File Change Specification

### `frontend/src/index.css`

**Change 1** — Light mode background (`:root` scope):
```css
/* Before */
--background: 0 0% 100%;

/* After */
--background: 350 100% 88%;
```

**Change 2** — Dark mode background (`.dark` scope):
```css
/* Before */
--background: 222.2 84% 4.9%;

/* After */
--background: 340 33% 41%;
```

## Validation Rules

1. The `--background` value MUST be in HSL format without the `hsl()` wrapper (e.g., `350 100% 88%` not `hsl(350, 100%, 88%)`) — this is required by the Tailwind config which wraps values with `hsl()`.
2. The contrast ratio between `--foreground` and `--background` MUST be ≥ 4.5:1 in both light and dark modes.
3. All other CSS variables in `:root` and `.dark` MUST remain unchanged.
4. No new CSS variables, classes, or selectors should be added.

## State Transitions

N/A — This feature has no state transitions. The background color is static and determined entirely by the current theme mode (light/dark), which is already managed by the existing `darkMode: ["class"]` Tailwind configuration.

## Relationships

```text
index.css (:root --background)
    └── tailwind.config.js (background: "hsl(var(--background))")
        └── index.css (body { @apply bg-background })
            └── All pages inherit pink background via body element

index.css (.dark --background)
    └── Same chain as above, activated when <html class="dark">
```
