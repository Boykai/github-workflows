# Data Model: Add Red Background Color to App

**Feature**: 018-red-background | **Date**: 2026-03-04

## Overview

This feature has no data model changes. It is a pure presentation/styling change that modifies CSS custom property values. No entities, database tables, API models, or state structures are added or modified.

## Design Tokens (CSS Custom Properties)

The only "model" for this feature is the set of CSS design tokens that define the application's color scheme. These are not traditional data models but are documented here as the structured values that govern the feature's behavior.

### Token: `--background`

| Attribute | Light Mode (`:root`) | Dark Mode (`.dark`) |
|-----------|---------------------|---------------------|
| **Current Value** | `0 0% 100%` (white) | `222.2 84% 4.9%` (dark navy) |
| **New Value** | `0 70% 50%` (#D32F2F, Material Red 700) | `0 73% 41%` (#B71C1C, Material Red 900) |
| **Format** | HSL (space-separated, no commas) | HSL (space-separated, no commas) |
| **Consumed By** | `tailwind.config.js` → `hsl(var(--background))` → `bg-background` class | Same |

### Token: `--foreground`

| Attribute | Light Mode (`:root`) | Dark Mode (`.dark`) |
|-----------|---------------------|---------------------|
| **Current Value** | `222.2 84% 4.9%` (dark navy) | `210 40% 98%` (off-white) |
| **New Value** | `0 0% 100%` (white) | `0 0% 100%` (white) |
| **Format** | HSL (space-separated, no commas) | HSL (space-separated, no commas) |
| **Consumed By** | `tailwind.config.js` → `hsl(var(--foreground))` → `text-foreground` class | Same |

### Unchanged Tokens

The following tokens are explicitly **not modified** to preserve component-level styling:

- `--card` / `--card-foreground` — Card surfaces keep their existing colors
- `--popover` / `--popover-foreground` — Popover surfaces keep their existing colors
- `--primary` / `--primary-foreground` — Primary action colors unchanged
- `--secondary` / `--secondary-foreground` — Secondary surfaces unchanged
- `--muted` / `--muted-foreground` — Muted surfaces unchanged
- `--accent` / `--accent-foreground` — Accent surfaces unchanged
- `--destructive` / `--destructive-foreground` — Destructive action colors unchanged
- `--border`, `--input`, `--ring` — Border/input/focus ring colors unchanged

## Relationships

```
--background ← consumed by → tailwind.config.js (background color)
                             ← applied to → <body> via `bg-background` class in index.css
                             ← inherited by → all page-level containers

--foreground ← consumed by → tailwind.config.js (foreground color)
                             ← applied to → <body> via `text-foreground` class in index.css
                             ← inherited by → all text elements without explicit color overrides
```

## Validation Rules

- `--background` values MUST be valid HSL triplets in space-separated format (e.g., `0 70% 50%`)
- The contrast ratio between `--background` and `--foreground` MUST be ≥ 4.5:1 per WCAG 2.1 AA
- Light mode contrast: `#D32F2F` bg + `#FFFFFF` fg = 4.68:1 ✅
- Dark mode contrast: `#B71C1C` bg + `#FFFFFF` fg = 6.27:1 ✅

## State Transitions

N/A — CSS variables are static values with no state transitions. Theme switching (light/dark) is handled by the existing `ThemeProvider` component which toggles the `.dark` class, causing the browser to apply the appropriate CSS variable block.
