# Data Model: Add Green Background Color to App

**Feature**: 018-green-background | **Date**: 2026-03-04

## Overview

This feature does not introduce new data entities, database schemas, or state models. The change is purely presentational — it modifies existing CSS custom property values in the design token system.

## Design Tokens (Modified)

The following existing CSS custom properties are modified. These are not data model entities but are documented here as the "data" that changes.

### Token: `--background`

| Attribute | Light Mode (`:root`) | Dark Mode (`.dark`) |
|-----------|---------------------|---------------------|
| **Current value** | `0 0% 100%` (white) | `222.2 84% 4.9%` (dark blue) |
| **New value** | `122 39% 49%` (#4CAF50, Material Green 500) | `125 35% 33%` (#2E7D32, Material Green 800) |
| **Format** | HSL (space-separated, no wrapper) | HSL (space-separated, no wrapper) |
| **Consumed by** | Tailwind `bg-background` → `hsl(var(--background))` | Same |

### Token: `--foreground`

| Attribute | Light Mode (`:root`) | Dark Mode (`.dark`) |
|-----------|---------------------|---------------------|
| **Current value** | `222.2 84% 4.9%` (near-black) | `210 40% 98%` (near-white) |
| **New value** | `222.2 84% 4.9%` (unchanged — near-black on green gives ~6.6:1 contrast) | `0 0% 100%` (white) |
| **Format** | HSL (space-separated, no wrapper) | HSL (space-separated, no wrapper) |
| **Consumed by** | Tailwind `text-foreground` → `hsl(var(--foreground))` | Same |

## Relationships

```text
index.css (:root / .dark)
  └── --background ──→ tailwind.config.js (background color) ──→ body (bg-background)
  └── --foreground ──→ tailwind.config.js (foreground color) ──→ body (text-foreground)
```

## Validation Rules

- `--background` MUST be valid HSL values (H: 0-360, S: 0-100%, L: 0-100%)
- Contrast ratio between `--background` and `--foreground` MUST be ≥ 4.5:1 (WCAG AA)
- Values MUST NOT include the `hsl()` wrapper (Tailwind adds this)

## State Transitions

N/A — CSS custom properties are static values with no state transitions. Theme switching (light ↔ dark) is handled by the existing `ThemeProvider` component toggling the `.dark` class.
