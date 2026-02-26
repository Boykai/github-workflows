# Data Model: Add Red Background Color to App

**Feature**: 011-red-background
**Date**: 2026-02-26

## Overview

This feature does not introduce, modify, or remove any data entities, database tables, API models, or state structures. The change is purely presentational — a CSS custom property value modification.

## Entities

*No new entities. No existing entities modified.*

## Design Tokens (CSS Custom Properties)

The only "data" affected by this feature are CSS design tokens defined in `frontend/src/index.css`:

### Modified Tokens

| Token | Scope | Before | After | Purpose |
|-------|-------|--------|-------|---------|
| `--color-bg-secondary` | `:root` (light mode) | `#f6f8fa` | `#E53E3E` | Primary app background surface |
| `--color-bg-secondary` | `html.dark-mode-active` | `#161b22` | `#E53E3E` | Primary app background surface (dark mode) |

### Unchanged Tokens (referenced for completeness)

| Token | Value (Light) | Value (Dark) | Relationship |
|-------|--------------|-------------|--------------|
| `--color-bg` | `#ffffff` | `#0d1117` | Component-level backgrounds (cards, header, sidebar) — **not changed** |
| `--color-text` | `#24292f` | `#e6edf3` | Primary text color — **not changed** |
| `--color-border` | `#d0d7de` | `#30363d` | Border color — **not changed** |

## State Transitions

*N/A — no state changes involved.*

## Validation Rules

- The `--color-bg-secondary` value MUST be a valid CSS color (6-digit hex)
- The body background MUST include a fallback: `background: var(--color-bg-secondary, #E53E3E)`
- Text on the red background MUST meet WCAG AA contrast ratio (4.5:1 for normal text)

## Relationships

```text
:root tokens
  └── --color-bg-secondary: #E53E3E
        └── body { background: var(--color-bg-secondary) }
              └── Visible as app-level background behind all components
```
