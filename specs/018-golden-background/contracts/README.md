# Contracts: Add Golden Background to App

**Feature**: `018-golden-background` | **Date**: 2026-03-04

## API Contracts

No API contracts are required for this feature. The golden background is implemented entirely via CSS custom property changes in `frontend/src/index.css`. No backend endpoints are added, modified, or consumed.

## CSS Contract

The implicit "contract" for this feature is the CSS custom property interface:

| Property | Light Mode Value | Dark Mode Value | Consumer |
|----------|-----------------|-----------------|----------|
| `--background` | `51 100% 50%` | `43 74% 15%` | `tailwind.config.js` → `hsl(var(--background))` → `bg-background` utility |

This property is consumed by:
1. `body { @apply bg-background }` in `index.css`
2. Any component using the Tailwind `bg-background` utility class
3. Any component using `hsl(var(--background))` directly
