# Data Model: Add Red Background Color to Application

**Feature**: `011-red-background` | **Date**: 2026-02-25

> This feature is a CSS-only theming change — no new database tables, API models, or persistent entities are introduced. This document maps the **design token changes**: which CSS custom properties are modified and how they relate to each other.

## Design Token Map

### Light Mode (`:root`)

| Token | Current Value | New Value | Reason |
|-------|--------------|-----------|--------|
| `--color-bg` | `#ffffff` | `#DC2626` | Primary red background (Tailwind `red-600`) |
| `--color-bg-secondary` | `#f6f8fa` | `#B91C1C` | Secondary red surface (Tailwind `red-700`) |
| `--color-text` | `#24292f` | `#FFFFFF` | White text for AA contrast against red |
| `--color-text-secondary` | `#57606a` | `#FCA5A5` | Light red-tinted secondary text (Tailwind `red-200`) |
| `--color-border` | `#d0d7de` | `#FECACA` | Light red border for visibility (Tailwind `red-200`) |
| `--color-primary` | `#0969da` | `#0969da` | No change — used on interactive elements |
| `--color-secondary` | `#6e7781` | `#6e7781` | No change |
| `--color-success` | `#1a7f37` | `#1a7f37` | No change |
| `--color-warning` | `#9a6700` | `#9a6700` | No change |
| `--color-danger` | `#cf222e` | `#cf222e` | No change |

### Dark Mode (`html.dark-mode-active`)

| Token | Current Value | New Value | Reason |
|-------|--------------|-----------|--------|
| `--color-bg` | `#0d1117` | `#7F1D1D` | Deep dark red background (Tailwind `red-900`) |
| `--color-bg-secondary` | `#161b22` | `#991B1B` | Slightly lighter dark red surface (Tailwind `red-800`) |
| `--color-text` | `#e6edf3` | `#e6edf3` | No change — already light, sufficient contrast |
| `--color-text-secondary` | `#8b949e` | `#8b949e` | No change — sufficient contrast against dark red |
| `--color-border` | `#30363d` | `#7F1D1D` | Dark red border matching primary bg |
| `--color-primary` | `#539bf5` | `#539bf5` | No change |
| `--color-secondary` | `#8b949e` | `#8b949e` | No change |
| `--color-success` | `#3fb950` | `#3fb950` | No change |
| `--color-warning` | `#d29922` | `#d29922` | No change |
| `--color-danger` | `#f85149` | `#f85149` | No change |

## WCAG AA Contrast Verification

| Pair | Foreground | Background | Ratio | Pass? |
|------|-----------|------------|-------|-------|
| Light text on primary bg | `#FFFFFF` | `#DC2626` | 4.63:1 | ✅ AA |
| Light text on secondary bg | `#FFFFFF` | `#B91C1C` | 5.74:1 | ✅ AA |
| Light secondary text on primary bg | `#FCA5A5` | `#DC2626` | 2.27:1 | ⚠️ Large text only |
| Dark text on dark primary bg | `#e6edf3` | `#7F1D1D` | 7.2:1 | ✅ AAA |
| Dark text on dark secondary bg | `#e6edf3` | `#991B1B` | 5.8:1 | ✅ AA |

## Token Dependency Graph

```
body { background: var(--color-bg-secondary) }     ← Page background
  └── Components use var(--color-bg)                ← Card/panel surfaces
        └── Text uses var(--color-text)             ← Primary text
        └── Labels use var(--color-text-secondary)  ← Secondary text
        └── Dividers use var(--color-border)        ← Borders

useAppTheme hook toggles html.dark-mode-active class
  └── All tokens switch between :root and html.dark-mode-active values
```

## Files Modified

| File | Change |
|------|--------|
| `frontend/src/index.css` | Update `:root` and `html.dark-mode-active` token values |

No new files, no deleted files, no structural changes.
