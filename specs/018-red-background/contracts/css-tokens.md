# API Contracts: Add Red Background Color to App

**Feature**: 018-red-background | **Date**: 2026-03-04

## Overview

This feature does not introduce, modify, or consume any API endpoints. The red background is implemented entirely through CSS custom property changes in the frontend. No backend changes, no REST/GraphQL endpoints, and no data transfers are involved.

## Contract: CSS Design Token Interface

While not a traditional API contract, the CSS custom properties serve as a contract between the theme system and all consuming components. This contract documents the expected interface.

### Token Contract

```css
/* Contract: Background and foreground tokens in frontend/src/index.css */

/* Light mode (:root) */
--background: <hue> <saturation> <lightness>;  /* Page-level background color in HSL */
--foreground: <hue> <saturation> <lightness>;  /* Default text color in HSL */

/* Dark mode (.dark) */
--background: <hue> <saturation> <lightness>;  /* Page-level background color in HSL */
--foreground: <hue> <saturation> <lightness>;  /* Default text color in HSL */
```

### Consumer Contract

All consumers access these tokens via Tailwind CSS utility classes:

| Tailwind Class | CSS Output | Token Referenced |
|---------------|------------|------------------|
| `bg-background` | `background-color: hsl(var(--background))` | `--background` |
| `text-foreground` | `color: hsl(var(--foreground))` | `--foreground` |

### Invariants

1. `--background` and `--foreground` MUST always have valid HSL values
2. The contrast ratio between `--background` and `--foreground` MUST be ≥ 4.5:1
3. The HSL format MUST use space-separated values (no commas), as expected by Tailwind's `hsl()` wrapper
4. Both `:root` and `.dark` blocks MUST define both tokens for theme consistency

## Existing API Endpoints

No existing API endpoints are affected by this change. The user settings API that manages theme preferences (`light`/`dark`/`system`) continues to work unchanged — it controls which CSS variable block is active, not the values within those blocks.
