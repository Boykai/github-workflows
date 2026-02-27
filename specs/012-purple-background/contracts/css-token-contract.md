# CSS Token Contract: Add Purple Background Color

**Date**: 2026-02-27 | **Branch**: `012-purple-background` | **Plan**: [plan.md](plan.md)

## Overview

This feature involves no backend API changes and no new component interfaces. The contract is defined entirely at the CSS design token level. The `--background` and related CSS custom properties in `frontend/src/index.css` serve as the centralized contract between the theming system and all consuming components.

## CSS Custom Property Contract

### Token Interface

All tokens follow the shadcn/ui HSL format: `H S% L%` (space-separated, no `hsl()` wrapper).

Consumed via Tailwind utility classes which wrap values in `hsl(var(--token))`.

```css
/* Light mode contract (:root) */
:root {
  --background: 270 50% 40%;           /* Purple primary surface */
  --foreground: 210 40% 98%;           /* Light text on purple */
  --card: 270 50% 45%;                 /* Slightly lighter purple cards */
  --card-foreground: 210 40% 98%;
  --popover: 270 50% 45%;
  --popover-foreground: 210 40% 98%;
  --primary: 210 40% 98%;              /* Light primary buttons */
  --primary-foreground: 270 50% 40%;   /* Purple text on light buttons */
  --secondary: 270 40% 50%;
  --secondary-foreground: 210 40% 98%;
  --muted: 270 30% 50%;
  --muted-foreground: 270 20% 80%;
  --accent: 270 40% 50%;
  --accent-foreground: 210 40% 98%;
  --destructive: 0 84.2% 60.2%;       /* Unchanged */
  --destructive-foreground: 210 40% 98%;
  --border: 270 30% 55%;
  --input: 270 30% 55%;
  --ring: 210 40% 98%;
  --radius: 0.5rem;                    /* Unchanged */
}

/* Dark mode contract (.dark) */
.dark {
  --background: 270 50% 20%;           /* Deep purple */
  --foreground: 210 40% 98%;           /* Unchanged */
  --card: 270 50% 25%;
  --card-foreground: 210 40% 98%;
  --popover: 270 50% 25%;
  --popover-foreground: 210 40% 98%;
  --primary: 210 40% 98%;              /* Unchanged */
  --primary-foreground: 270 50% 20%;
  --secondary: 270 40% 30%;
  --secondary-foreground: 210 40% 98%;
  --muted: 270 30% 30%;
  --muted-foreground: 270 20% 70%;
  --accent: 270 40% 30%;
  --accent-foreground: 210 40% 98%;
  --destructive: 0 62.8% 30.6%;       /* Unchanged */
  --destructive-foreground: 210 40% 98%;
  --border: 270 30% 35%;
  --input: 270 30% 35%;
  --ring: 270 30% 70%;
}
```

### Consuming Components (No Changes Required)

| Component | Token(s) Used | Behavior |
|-----------|--------------|----------|
| `body` (index.css) | `bg-background text-foreground` | Inherits purple background automatically |
| `App.tsx` container | `bg-background text-foreground` | Inherits purple background automatically |
| `App.tsx` header | `bg-background border-border` | Inherits purple background and border |
| `Button` (default) | `bg-primary text-primary-foreground` | Light button on purple background |
| `Button` (outline) | `border-input bg-background` | Purple background with purple border |
| `Button` (secondary) | `bg-secondary text-secondary-foreground` | Lighter purple variant |
| `Button` (ghost) | `hover:bg-accent hover:text-accent-foreground` | Purple accent on hover |
| `Input` | `border-input bg-background` | Purple background with purple border |
| `Card` | `bg-card text-card-foreground` | Slightly lighter purple surface |
| `select option` (index.css) | `background-color: hsl(var(--background))` | Purple option background |

### WCAG AA Contrast Requirements

| Surface Token | Text Token | Required Ratio | Expected Ratio |
|--------------|------------|----------------|----------------|
| `--background` (light) | `--foreground` (light) | ≥ 4.5:1 | ~11:1 |
| `--background` (dark) | `--foreground` (dark) | ≥ 4.5:1 | ~12:1 |
| `--card` (light) | `--card-foreground` (light) | ≥ 4.5:1 | ~9:1 |
| `--card` (dark) | `--card-foreground` (dark) | ≥ 4.5:1 | ~10:1 |
| `--primary` (light) | `--primary-foreground` (light) | ≥ 4.5:1 | ~11:1 |
| `--primary` (dark) | `--primary-foreground` (dark) | ≥ 4.5:1 | ~12:1 |

## API Contracts (Unchanged)

No backend API changes. All existing endpoints continue to function identically.
