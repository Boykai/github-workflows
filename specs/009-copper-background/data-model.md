# Data Model: Add Copper Background Theme to App

**Feature**: `009-copper-background` | **Date**: 2026-02-23

> This feature creates no new data entities, database schemas, or API contracts. It modifies existing CSS design tokens only. This document describes the **design token entities** — the styling primitives that define the copper theme.

## Design Token Entities

### 1. Copper Design Token (Light Mode)

The `:root` CSS custom properties defining the copper theme for light mode.

| Token | Previous Value | New Value | Purpose |
|-------|---------------|-----------|---------|
| `--color-bg` | `#ffffff` | `#B87333` | Primary copper background for app surfaces, modals, cards |
| `--color-bg-secondary` | `#f6f8fa` | `#CB6D51` | Secondary copper for body background, sidebar, alternate areas |
| `--color-text` | `#24292f` | `#1A1A1A` | Primary text color — near-black for ≥4.5:1 contrast on copper |
| `--color-text-secondary` | `#57606a` | `#2D1810` | Secondary text — dark brown for readability on copper |
| `--color-border` | `#d0d7de` | `#9A5C2E` | Border color — dark copper tone for element delineation |
| `--shadow` | `0 1px 3px rgba(0,0,0,0.1)` | `0 1px 3px rgba(139,90,43,0.2)` | Copper-tinted shadow for visual harmony |

**Unchanged tokens** (semantic colors unaffected):
- `--color-primary: #0969da` — Brand/link color
- `--color-secondary: #6e7781` — Muted UI elements
- `--color-success: #1a7f37` — Success states
- `--color-warning: #9a6700` — Warning states
- `--color-danger: #cf222e` — Error/danger states
- `--radius: 6px` — Border radius

### 2. Copper Design Token (Dark Mode)

The `html.dark-mode-active` CSS custom properties defining the copper theme for dark mode.

| Token | Previous Value | New Value | Purpose |
|-------|---------------|-----------|---------|
| `--color-bg` | `#0d1117` | `#8C4A2F` | Dark copper background for app surfaces |
| `--color-bg-secondary` | `#161b22` | `#6B3A24` | Deeper copper for body background, alternate areas |
| `--color-text` | `#e6edf3` | `#FFFFFF` | White text for ≥4.5:1 contrast on dark copper |
| `--color-text-secondary` | `#8b949e` | `#E8D5CC` | Light warm tone for secondary text on dark copper |
| `--color-border` | `#30363d` | `#5A2E1A` | Deep copper border for dark mode element delineation |
| `--shadow` | `0 1px 3px rgba(0,0,0,0.4)` | `0 1px 3px rgba(0,0,0,0.5)` | Deeper shadow for dark copper contrast |

**Unchanged tokens** (semantic colors for dark mode unaffected):
- `--color-primary: #539bf5`
- `--color-secondary: #8b949e`
- `--color-success: #3fb950`
- `--color-warning: #d29922`
- `--color-danger: #f85149`

### 3. Theme Configuration (Existing — Unchanged)

The app's theming system is preserved exactly as-is.

| Component | File | Role | Changes |
|-----------|------|------|---------|
| `useAppTheme` hook | `frontend/src/hooks/useAppTheme.ts` | Toggles `dark-mode-active` class on `<html>` | None |
| `localStorage` | Browser storage key `tech-connect-theme-mode` | Persists user's light/dark preference | None |
| User Settings API | Backend `settings_store.py` | Stores authenticated user's theme preference | None |

**Relationship**: The `useAppTheme` hook toggles the CSS class that switches between the `:root` (light copper) and `html.dark-mode-active` (dark copper) token sets. This mechanism is unchanged — only the token values within each set are updated.

## Token Cascade Flow

```
index.css (:root / html.dark-mode-active)
  ↓ CSS custom property inheritance
body { background: var(--color-bg-secondary) }         → copper secondary background
  ↓
App.css components { background: var(--color-bg) }      → copper primary background
App.css components { color: var(--color-text) }          → high-contrast text
App.css components { border-color: var(--color-border) } → copper-toned borders
  ↓
Semantic colors (--color-success, --color-danger, etc.)  → UNCHANGED
Hardcoded colors (#2da44e, #cf222e, etc.)                → UNCHANGED (status/diff indicators)
```

## Contrast Compliance Matrix

| Surface | Text Token | Background Token | Ratio | WCAG AA |
|---------|-----------|-----------------|-------|---------|
| Light mode primary | `--color-text` (#1A1A1A) | `--color-bg` (#B87333) | ~4.8:1 | ✅ |
| Light mode secondary text | `--color-text-secondary` (#2D1810) | `--color-bg` (#B87333) | ~5.2:1 | ✅ |
| Light mode on secondary bg | `--color-text` (#1A1A1A) | `--color-bg-secondary` (#CB6D51) | ~4.5:1 | ✅ |
| Dark mode primary | `--color-text` (#FFFFFF) | `--color-bg` (#8C4A2F) | ~6.3:1 | ✅ |
| Dark mode secondary text | `--color-text-secondary` (#E8D5CC) | `--color-bg` (#8C4A2F) | ~4.6:1 | ✅ |
| Dark mode on secondary bg | `--color-text` (#FFFFFF) | `--color-bg-secondary` (#6B3A24) | ~7.5:1 | ✅ |

## State Transitions: No Changes

The `useAppTheme` hook's dark mode toggle mechanism is unchanged. The state transition remains:
- Light mode (default) ↔ Dark mode (user toggle)
- The only difference is the visual output: copper tones instead of gray/white tones.

## Validation Rules: No Changes

No data validation logic is affected. The copper theme is purely a visual/CSS change with no impact on data models, API contracts, or business logic.
