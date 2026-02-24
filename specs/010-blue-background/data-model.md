# Data Model: Add Blue Background Color to App

**Feature**: `010-blue-background`  
**Date**: 2026-02-24

---

This feature does not introduce new application data models. It modifies **CSS design tokens** — the existing custom properties that define the application's visual theme.

## CSS Design Tokens (index.css)

### Entity: `:root` (Light Mode Tokens)

| Token | Current Value | New Value | Purpose |
|-------|---------------|-----------|---------|
| `--color-bg` | `#ffffff` | `#2563EB` | Primary background (cards, content areas) |
| `--color-bg-secondary` | `#f6f8fa` | `#1D4ED8` | Page/body background |
| `--color-text` | `#24292f` | `#FFFFFF` | Primary text color |
| `--color-text-secondary` | `#57606a` | `#CBD5E1` | Secondary/muted text color |
| `--color-border` | `#d0d7de` | `#3B82F6` | Border color |
| `--color-primary` | `#0969da` | `#93C5FD` | Primary action/link color (lightened for blue bg) |
| `--color-secondary` | `#6e7781` | `#94A3B8` | Secondary UI elements |
| `--color-success` | `#1a7f37` | `#4ADE80` | Success state color |
| `--color-warning` | `#9a6700` | `#FBBF24` | Warning state color |
| `--color-danger` | `#cf222e` | `#F87171` | Danger/error state color |

**Validation**: All text colors must achieve ≥4.5:1 contrast ratio against their respective background tokens.

### Entity: `html.dark-mode-active` (Dark Mode Tokens)

| Token | Current Value | New Value | Purpose |
|-------|---------------|-----------|---------|
| `--color-bg` | `#0d1117` | `#1E3A5F` | Primary background (cards, content areas) |
| `--color-bg-secondary` | `#161b22` | `#162D4A` | Page/body background |
| `--color-text` | `#e6edf3` | `#e6edf3` | Primary text (unchanged — good contrast) |
| `--color-text-secondary` | `#8b949e` | `#94A3B8` | Secondary text (slightly lightened) |
| `--color-border` | `#30363d` | `#2563EB` | Border color (blue accent) |
| `--color-primary` | `#539bf5` | `#60A5FA` | Primary action/link color |
| `--color-secondary` | `#8b949e` | `#94A3B8` | Secondary UI elements |
| `--color-success` | `#3fb950` | `#4ADE80` | Success state (unchanged) |
| `--color-warning` | `#d29922` | `#FBBF24` | Warning state |
| `--color-danger` | `#f85149` | `#F87171` | Danger/error state |

**Validation**: All dark mode text colors must achieve ≥4.5:1 contrast ratio against dark blue backgrounds.

### Entity: `<body>` Inline Style (index.html)

| Property | Value | Purpose |
|----------|-------|---------|
| `background-color` | `#1D4ED8` | Flash prevention — matches light mode `--color-bg-secondary` |

**Lifecycle**: Applied at HTML parse time, before CSS loads. Overridden by `index.css` once loaded.

## Relationships

```
:root tokens ──> body { background: var(--color-bg-secondary) }
:root tokens ──> All components via var() references
html.dark-mode-active ──> Overrides :root when dark mode toggled
useAppTheme hook ──> Toggles dark-mode-active class on <html>
index.html inline style ──> Prevents flash before CSS loads
```

## State Transitions

```
Page Load → index.html inline style (blue bg visible immediately)
         → CSS loads → :root tokens apply (light mode blue)
         → useAppTheme reads preference → optionally adds dark-mode-active
         → Dark mode tokens override → dark blue bg
User toggles theme → dark-mode-active class toggled
                   → CSS tokens swap → background transitions
```
