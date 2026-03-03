# Data Model: Add Blue Background Color to App

**Feature**: 016-blue-background  
**Date**: 2026-03-03  
**Depends on**: research.md (R1, R2, R4)

## Entities

This feature introduces **no new data entities**. It is a CSS-only change that modifies existing CSS custom property values in `frontend/src/index.css`. No database tables, no API models, no TypeScript interfaces, and no Pydantic models are added or modified.

## CSS Variable Changes

The only data "model" affected is the set of CSS custom properties that define the application's color scheme.

### Modified Variables

| Variable | Selector | Current Value (HSL) | New Value (HSL) | Hex Equivalent |
|----------|----------|---------------------|-----------------|----------------|
| `--background` | `:root` (light) | `0 0% 100%` (#FFFFFF) | `210 100% 56%` | #1E90FF (Dodger Blue) |
| `--background` | `.dark` (dark) | `222.2 84% 4.9%` (#020817) | `210 54% 23%` | #1A3A5C (Deep Blue) |

### Unchanged Variables

The following variables are intentionally **not modified** to preserve component readability (see research.md R5):

| Variable | Selector | Value | Reason for Preservation |
|----------|----------|-------|------------------------|
| `--foreground` | `:root` | `222.2 84% 4.9%` | Dark text on blue provides ≥4.5:1 contrast |
| `--foreground` | `.dark` | `210 40% 98%` | Light text on deep blue provides ≥4.5:1 contrast |
| `--card` | `:root` / `.dark` | unchanged | Cards retain their own backgrounds for readability |
| `--popover` | `:root` / `.dark` | unchanged | Popovers retain their own backgrounds for readability |
| `--primary` | `:root` / `.dark` | unchanged | Button/accent colors unaffected |
| `--secondary` | `:root` / `.dark` | unchanged | Secondary surfaces unaffected |
| `--muted` | `:root` / `.dark` | unchanged | Muted surfaces unaffected |
| `--accent` | `:root` / `.dark` | unchanged | Accent surfaces unaffected |

### Validation Rules

| Rule | Enforcement |
|------|-------------|
| WCAG AA contrast ≥4.5:1 between `--background` and `--foreground` | Verified during research (R3); manual visual testing in quickstart |
| Blue background visible on all pages | Enforced by `body { @apply bg-background }` in index.css — all routes inherit |
| Consistent across viewports 320px–2560px | Enforced by existing CSS (body fills viewport); no viewport-specific overrides |

### State Transitions

N/A — No state machines or lifecycle transitions. The CSS variable values are static per theme. Theme toggling is handled by the existing `ThemeProvider` which adds/removes the `.dark` class on `<html>`.

## Migration

No database migration required. No schema changes.
