# Contracts: Add Red Background Color to App

**Date**: 2026-02-26 | **Branch**: `011-red-background`

## Overview

This feature has no API contract changes. It is a pure CSS/visual change confined to the frontend. No backend endpoints are added, modified, or removed. No request/response schemas change. No new frontend-backend communication is introduced.

## CSS Contract (Design Token Interface)

The following CSS custom properties form the "contract" between the root stylesheet and all components that consume these tokens. The values change but the interface (property names, usage patterns) remains stable.

### Modified Tokens

| Token | Type | Light Mode | Dark Mode | Consumers |
|-------|------|-----------|-----------|-----------|
| `--color-bg-secondary` | `<color>` | `#E53E3E` | `#9B2C2C` | `body` background, any element using this token |
| `--color-text` | `<color>` | `#FFFFFF` | `#FFFFFF` | Default text color, inherited by all elements |

### Unchanged Tokens

All other tokens remain at their current values, notably:

| Token | Light Mode | Dark Mode | Rationale |
|-------|-----------|-----------|-----------|
| `--color-bg` | `#ffffff` | `#0d1117` | **Intentionally unchanged** — used by component backgrounds (cards, modals, sidebars). Keeping it white/dark preserves visual hierarchy and content legibility within components. |
| `--color-primary` | `#0969da` | `#539bf5` | No change needed |
| `--color-secondary` | `#6e7781` | `#8b949e` | No change needed |
| `--color-success` | `#1a7f37` | `#3fb950` | No change needed |
| `--color-warning` | `#9a6700` | `#d29922` | No change needed |
| `--color-danger` | `#cf222e` | `#f85149` | No change needed |
| `--color-border` | `#d0d7de` | `#30363d` | No change needed |
| `--color-text-secondary` | `#57606a` | `#8b949e` | No change needed |
| `--radius` | `6px` | `6px` | No change needed |
| `--shadow` | light shadow | dark shadow | No change needed |

### Fallback Behavior

The `body` element specifies an inline fallback: `background: var(--color-bg-secondary, #E53E3E)`. If the custom property fails to resolve, the red background still renders. This satisfies FR-008.
