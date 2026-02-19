# Data Model: Add Teal Background Color to App

**Feature**: 007-teal-background | **Date**: 2026-02-19

---

## Entity Relationship Overview

This feature introduces no new entities, models, or data structures. The change is purely a CSS design token update.

---

## Modified Entities

### CSS Design Tokens (`:root` custom properties in `index.css`)

The existing CSS custom property system serves as the data model for theme values.

| Token | Current Value | New Value (Light) | New Value (Dark) | Description |
|-------|--------------|-------------------|------------------|-------------|
| `--color-bg-app` | *(new)* | `#0D9488` | `#0F766E` | Root application background color |

**No other tokens are modified.** Existing tokens remain unchanged:

| Token | Light Mode | Dark Mode | Usage |
|-------|-----------|-----------|-------|
| `--color-bg` | `#ffffff` | `#0d1117` | Component backgrounds (cards, header, sidebar, modals) |
| `--color-bg-secondary` | `#f6f8fa` | `#161b22` | Secondary surfaces (columns, form fields) |

### Validation Rules

- The `--color-bg-app` value MUST be a valid CSS color (hex, rgb, hsl).
- White text (#FFFFFF) on the light mode value MUST achieve ≥4.5:1 contrast ratio (WCAG AA).
- Light text (#E6EDF3) on the dark mode value MUST achieve ≥4.5:1 contrast ratio (WCAG AA).

### State Transitions

| Trigger | From | To | Mechanism |
|---------|------|----|-----------|
| Dark mode toggle | `--color-bg-app: #0D9488` | `--color-bg-app: #0F766E` | `html.dark-mode-active` class toggle via `useAppTheme` hook |
| Light mode toggle | `--color-bg-app: #0F766E` | `--color-bg-app: #0D9488` | Remove `html.dark-mode-active` class |

---

## No Backend Changes

This feature does not modify any backend models, API responses, or database schemas.
