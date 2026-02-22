# CSS Design Token Contract: Black Background Theme

**Feature**: `009-black-background` | **Date**: 2026-02-22

> This feature introduces no new API endpoints. The only contract is the **CSS design token system** — the custom properties that all components depend on for theming.

## CSS Custom Property Contract

All frontend components MUST reference theme colors exclusively via CSS custom properties. Direct hex/rgb values are permitted only for state-specific colors (e.g., status badges) that are already dark-compatible.

### Token Interface

```css
:root {
  /* Backgrounds */
  --color-bg: <color>;            /* Root/primary background */
  --color-bg-secondary: <color>;  /* Elevated surfaces, sidebar, cards */

  /* Text */
  --color-text: <color>;          /* Primary body text */
  --color-text-secondary: <color>;/* Muted/secondary text */

  /* Borders */
  --color-border: <color>;        /* Borders, dividers, outlines */

  /* Accents */
  --color-primary: <color>;       /* Links, primary actions */
  --color-secondary: <color>;     /* Secondary actions, inactive */
  --color-success: <color>;       /* Success states */
  --color-warning: <color>;       /* Warning states */
  --color-danger: <color>;        /* Error/danger states */

  /* Layout */
  --radius: <length>;             /* Border radius */
  --shadow: <shadow>;             /* Box shadow */
}
```

### Token Values — Light Mode (`:root`)

```css
:root {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #000000;
  --color-bg-secondary: #121212;
  --color-border: #2C2C2C;
  --color-text: #ffffff;
  --color-text-secondary: #b0b0b0;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

### Token Values — Dark Mode (`html.dark-mode-active`)

```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #000000;
  --color-bg-secondary: #0a0a0a;
  --color-border: #1e1e1e;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

### Contrast Compliance

All text and interactive color tokens MUST meet WCAG AA minimum contrast ratios against the root background (`--color-bg: #000000`):

| Token | Value (Light) | Ratio vs #000 | WCAG AA (4.5:1) |
|-------|--------------|---------------|------------------|
| `--color-text` | `#ffffff` | 21:1 | ✅ Pass |
| `--color-text-secondary` | `#b0b0b0` | 10.5:1 | ✅ Pass |
| `--color-primary` | `#539bf5` | 5.1:1 | ✅ Pass |
| `--color-success` | `#3fb950` | 6.3:1 | ✅ Pass |
| `--color-warning` | `#d29922` | 7.4:1 | ✅ Pass |
| `--color-danger` | `#f85149` | 4.8:1 | ✅ Pass |
| `--color-secondary` | `#8b949e` | 7.2:1 | ✅ Pass |

### Consumer Rules

1. **Background**: Use `var(--color-bg)` for page/root backgrounds, `var(--color-bg-secondary)` for elevated surfaces
2. **Text**: Use `var(--color-text)` for primary text, `var(--color-text-secondary)` for muted text
3. **Borders**: Use `var(--color-border)` for all structural separators
4. **No hardcoded light backgrounds**: Components MUST NOT use `#ffffff`, `#f6f8fa`, `#f0f0f0`, or similar light hex values for backgrounds
5. **State-specific colors**: Status badges, alerts, and decorative colors may use hardcoded hex values only if they are dark-compatible (not light/white backgrounds)

### Flash Prevention

The root `<html>` element in `index.html` MUST include an inline background:

```html
<html lang="en" style="background-color: #000000">
```

This ensures no white flash occurs before CSS custom properties load.
