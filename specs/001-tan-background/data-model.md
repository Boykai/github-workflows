# Data Model: Apply Tan Background Color to App

**Feature**: 001-tan-background  
**Date**: 2026-02-20  
**Status**: Complete

## Overview

This feature modifies existing CSS custom properties (design tokens) — no database entities, API models, or application state are involved. The "data model" for this feature is the CSS token system defined in `frontend/src/index.css`.

## CSS Design Tokens

### Modified Tokens

| Token | Current Value (Light) | New Value (Light) | Scope |
|-------|----------------------|-------------------|-------|
| `--color-bg-secondary` | `#f6f8fa` | `#D2B48C` | `:root` — body background |
| `--color-text-secondary` | `#57606a` | `#3D4451` | `:root` — secondary text (darkened for WCAG AA on tan) |

| Token | Current Value (Dark) | New Value (Dark) | Scope |
|-------|---------------------|-------------------|-------|
| `--color-bg-secondary` | `#161b22` | `#2C1E12` | `html.dark-mode-active` — body background |

### Unchanged Tokens (for reference)

| Token | Light Value | Dark Value | Notes |
|-------|-----------|-----------|-------|
| `--color-bg` | `#ffffff` | `#0d1117` | Component surfaces — unchanged, provides contrast against tan |
| `--color-text` | `#24292f` | `#e6edf3` | Primary text — passes WCAG AA on tan (7.43:1) |
| `--color-border` | `#d0d7de` | `#30363d` | Borders — no impact from background change |
| `--color-primary` | `#0969da` | `#539bf5` | Brand/link color — no impact |

## Token Relationships

```
body background ← --color-bg-secondary (CHANGED to tan)
    │
    ├── component surfaces ← --color-bg (unchanged, white/dark)
    │   ├── cards, modals, sidebars
    │   └── text on surfaces ← --color-text, --color-text-secondary
    │
    └── text directly on body ← --color-text (passes), --color-text-secondary (DARKENED)
```

## Validation Rules

- **WCAG AA Contrast**: All text tokens on `--color-bg-secondary` must achieve ≥ 4.5:1 contrast ratio
- **Visual Distinction**: `--color-bg` surfaces must be visually distinguishable from `--color-bg-secondary` body background
- **Dark Mode Parity**: Dark mode tokens must provide equivalent warm-tan aesthetic with passing contrast ratios

## State Transitions

N/A — CSS tokens are static values with no runtime state transitions. Theme switching (light ↔ dark) is handled by the existing `useAppTheme` hook which toggles the `dark-mode-active` class.
