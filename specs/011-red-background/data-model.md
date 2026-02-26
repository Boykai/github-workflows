# Data Model: Add Red Background Color to App

**Date**: 2026-02-26 | **Branch**: `011-red-background` | **Plan**: [plan.md](plan.md)

## Overview

This feature is a CSS-only visual change. There are no data model, schema, entity, or state changes. No database migrations, no new API models, and no application state modifications are required.

## Entities

No entities are created, modified, or removed.

## State Changes

No application state transitions are introduced.

## Design Tokens (CSS Custom Properties)

The only "data" affected by this feature is the CSS design token system defined in `frontend/src/index.css`. This is not a data model in the traditional sense, but is documented here for completeness.

### Token: `--color-bg-secondary` (modified)

| Property | Before | After |
|----------|--------|-------|
| Light mode value | `#f6f8fa` | `#E53E3E` |
| Dark mode value | `#161b22` | `#9B2C2C` |
| Used by | `body { background }` | `body { background }` (unchanged) |
| Scope | `:root` / `html.dark-mode-active` | `:root` / `html.dark-mode-active` (unchanged) |

### Token: `--color-text` (modified)

| Property | Before | After |
|----------|--------|-------|
| Light mode value | `#24292f` | `#FFFFFF` |
| Dark mode value | `#e6edf3` | `#FFFFFF` |
| Used by | `body { color }`, inherited by all text | `body { color }` (unchanged usage) |

### Token: `--color-bg` (unchanged)

| Property | Light Mode | Dark Mode |
|----------|-----------|-----------|
| Value | `#ffffff` | `#0d1117` |
| Used by | Component backgrounds (cards, modals, sidebars) | Component backgrounds |
| Rationale | Intentionally unchanged — components need a contrasting surface for their own content legibility |

### Fallback

`body { background: var(--color-bg-secondary, #E53E3E); }` — provides a hardcoded fallback if the CSS custom property fails to resolve.
