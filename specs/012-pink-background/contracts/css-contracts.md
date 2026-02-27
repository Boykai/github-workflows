# Component Contracts: Add Pink Background Color to App

**Date**: 2026-02-27 | **Branch**: `012-pink-background` | **Plan**: [plan.md](plan.md)

## Overview

This feature involves no backend API changes and no frontend component interface changes. The only modification is to CSS custom property values in `frontend/src/index.css`. No component props, hooks, or state management are affected.

## CSS Contract

### File: `frontend/src/index.css`

The `--background` CSS custom property is the single contract point for the app-level background color. It is consumed by:

1. **Body element** — via `@apply bg-background` in the `@layer base` block
2. **Tailwind utility** — `bg-background` maps to `hsl(var(--background))` via `tailwind.config.js`
3. **Select options** — via `background-color: hsl(var(--background))` inline in the `@layer base` block

### Contract Change

```css
/* Light mode: :root selector */
/* Before */
--background: 0 0% 100%;
/* After */
--background: 350 100% 88%;

/* Dark mode: .dark selector */
/* Before */
--background: 222.2 84% 4.9%;
/* After */
--background: 350 30% 12%;
```

### Consumers (Unchanged)

| Consumer | File | Usage | Impact |
|----------|------|-------|--------|
| `body` | `frontend/src/index.css:74` | `@apply bg-background` | Background color changes automatically |
| `select option` | `frontend/src/index.css:84` | `background-color: hsl(var(--background))` | Select dropdown background changes automatically |
| Any element using `bg-background` | Various components | Tailwind utility class | Background color changes automatically |

## API Contracts

**None.** No backend API changes. No new endpoints, no modified request/response schemas.

## Component Contracts

**None.** No React component prop changes, no new components, no modified component interfaces.
