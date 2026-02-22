# Theme Tokens Contract

**Feature**: `009-black-background` | **Date**: 2026-02-22

> This feature introduces no new API endpoints. The only contract is the **CSS design token interface** — the set of CSS custom properties that all components depend on for theming.

## CSS Custom Property Interface

All frontend components MUST reference colors exclusively through these CSS custom properties. Direct hex/rgb values are permitted only for context-specific accents (notification tints, button variants) that do not represent the global theme.

### Token Schema

```css
:root {
  /* Background tokens */
  --color-bg: <color>;              /* Root/app-level background */
  --color-bg-secondary: <color>;    /* Body, alternate areas, elevated surfaces */

  /* Text tokens */
  --color-text: <color>;            /* Primary text */
  --color-text-secondary: <color>;  /* Secondary/muted text */

  /* Accent tokens */
  --color-primary: <color>;         /* Primary action (buttons, links) */
  --color-secondary: <color>;       /* Secondary elements */
  --color-success: <color>;         /* Success indicators */
  --color-warning: <color>;         /* Warning indicators */
  --color-danger: <color>;          /* Danger/error indicators */

  /* Structural tokens */
  --color-border: <color>;          /* Borders, dividers, outlines */
  --radius: <length>;               /* Border radius */
  --shadow: <shadow>;               /* Elevation shadow */
}
```

### Black Theme Values

| Token | Light Mode (`:root`) | Dark Mode (`html.dark-mode-active`) |
|-------|---------------------|-------------------------------------|
| `--color-bg` | `#000000` | `#000000` |
| `--color-bg-secondary` | `#121212` | `#0a0a0a` |
| `--color-text` | `#ffffff` | `#f0f0f0` |
| `--color-text-secondary` | `#a0a0a0` | `#8a8a8a` |
| `--color-border` | `#2c2c2c` | `#1f1f1f` |
| `--color-primary` | `#539bf5` | `#539bf5` |
| `--color-secondary` | `#8b949e` | `#8b949e` |
| `--color-success` | `#3fb950` | `#3fb950` |
| `--color-warning` | `#d29922` | `#d29922` |
| `--color-danger` | `#f85149` | `#f85149` |
| `--radius` | `6px` | `6px` |
| `--shadow` | `0 1px 3px rgba(0,0,0,0.6)` | `0 1px 3px rgba(0,0,0,0.8)` |

### Contrast Requirements

All text-on-background combinations MUST achieve WCAG AA minimum contrast ratio of 4.5:1:

| Combination | Ratio | Status |
|-------------|-------|--------|
| `--color-text` on `--color-bg` | ≥21:1 | Required |
| `--color-text-secondary` on `--color-bg` | ≥10:1 | Required |
| `--color-text` on `--color-bg-secondary` | ≥17:1 | Required |
| `--color-text-secondary` on `--color-bg-secondary` | ≥8:1 | Required |
| `--color-primary` on `--color-bg` | ≥6:1 | Required |

### Flash Prevention Contract

The `<html>` element in `index.html` MUST include an inline `style="background-color: #000000"` attribute to prevent white flash before CSS loads. This inline style MUST match the `--color-bg` token value.

### Theme Toggle Behavior

- Both light and dark modes use black-based backgrounds
- The `useAppTheme` hook toggles `dark-mode-active` class on `<html>`
- Theme preference persists via localStorage (`tech-connect-theme-mode` key)
- When authenticated, preference syncs to user settings API
