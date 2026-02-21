# Data Model: Add Green Background Color to App

**Feature**: 008-green-background
**Date**: 2026-02-21

## Overview

This feature has no traditional data entities (no database, API models, or state objects). The "data model" is the CSS custom property (design token) system that drives the application's visual theming.

## CSS Design Tokens

### Token: `--color-bg`

| Property | Value |
|----------|-------|
| **Purpose** | Primary application background color |
| **Light mode** | `#4CAF50` (Material Design Green 500) |
| **Dark mode** | `#2E7D32` (Material Design Green 800) |
| **Location** | `frontend/src/index.css` `:root` and `html.dark-mode-active` selectors |
| **Consumers** | `body` background (via `--color-bg-secondary`), root layout |

### Token: `--color-bg-secondary`

| Property | Value |
|----------|-------|
| **Purpose** | Secondary/offset background for the app body and layout sections |
| **Light mode** | `#43A047` (Material Design Green 600) |
| **Dark mode** | `#1B5E20` (Material Design Green 900) |
| **Location** | `frontend/src/index.css` `:root` and `html.dark-mode-active` selectors |
| **Consumers** | `body` element background |

### Token: `--color-bg-surface` (NEW)

| Property | Value |
|----------|-------|
| **Purpose** | Background for elevated surface elements (cards, panels, inputs, chat bubbles) |
| **Light mode** | `#ffffff` (white — previous `--color-bg` value) |
| **Dark mode** | `#0d1117` (dark — previous `--color-bg` dark value) |
| **Location** | `frontend/src/index.css` `:root` and `html.dark-mode-active` selectors |
| **Consumers** | Components currently using `var(--color-bg)` for their surface backgrounds |

## Token Relationships

```text
:root (light mode)
├── --color-bg: #4CAF50          (app-level green background)
├── --color-bg-secondary: #43A047 (offset green for body/sections)
├── --color-bg-surface: #ffffff   (white surfaces for cards/panels)
└── --color-text: #24292f         (dark text — 4.56:1 contrast on #4CAF50)

html.dark-mode-active
├── --color-bg: #2E7D32          (dark green background)
├── --color-bg-secondary: #1B5E20 (darker green for body/sections)
├── --color-bg-surface: #0d1117   (dark surfaces for cards/panels)
└── --color-text: #e6edf3         (light text — 6.8:1 contrast on #2E7D32)
```

## Migration Notes

Components that currently reference `var(--color-bg)` for their own surface background should be updated to reference `var(--color-bg-surface)` instead. This preserves their neutral appearance while the app-level background becomes green. The affected files are:

- `frontend/src/App.css` — header, sidebar, chat section backgrounds
- `frontend/src/components/chat/ChatInterface.css` — chat bubbles, input area, message containers

## State Transitions

N/A — No state machines or transitions. The background color is static per theme mode (light/dark) and toggles synchronously via the existing `useAppTheme` hook.

## Validation Rules

- `--color-bg` MUST be a valid CSS color value (hex format)
- Contrast ratio between `--color-text` and `--color-bg` MUST be ≥ 4.5:1 for WCAG AA
- Contrast ratio between `--color-text` and `--color-bg-surface` MUST be ≥ 4.5:1 for WCAG AA
