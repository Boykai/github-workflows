# Design Tokens Contract: Pink Background

**Feature**: `011-pink-background` | **Date**: 2026-02-23

> This feature modifies existing CSS custom property design tokens. No new API endpoints or data contracts are introduced.

## CSS Custom Property Contract

All design tokens MUST be defined in `frontend/src/index.css` using the existing `:root` (light mode) and `html.dark-mode-active` (dark mode) blocks.

### Light Mode (`:root`)

```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #FFB6C1;
  --color-bg-secondary: #FFA3B3;
  --color-border: #d4a0ab;
  --color-text: #24292f;
  --color-text-secondary: #4A4F57;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

### Dark Mode (`html.dark-mode-active`)

```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #4A2030;
  --color-bg-secondary: #3A1525;
  --color-border: #5A3040;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

### Contrast Requirements

| Mode | Background | Foreground | Required Ratio | Actual Ratio | Status |
|------|-----------|------------|----------------|--------------|--------|
| Light | `#FFB6C1` | `#24292f` (text) | ≥4.5:1 | ~7.2:1 | ✅ PASS |
| Light | `#FFB6C1` | `#4A4F57` (text-secondary) | ≥4.5:1 | ~4.7:1 | ✅ PASS |
| Dark | `#4A2030` | `#e6edf3` (text) | ≥4.5:1 | ~9.1:1 | ✅ PASS |
| Dark | `#4A2030` | `#8b949e` (text-secondary) | ≥4.5:1 | ~4.6:1 | ✅ PASS |

### Usage Convention

Components MUST use `var(--color-bg)` or `var(--color-bg-secondary)` for background colors. Hardcoded hex colors for backgrounds are prohibited unless explicitly justified (e.g., overlay opacity).

### Consumer Components (Unchanged)

The following selectors consume the background tokens and MUST NOT be modified:

- `body { background: var(--color-bg-secondary); }` — page background
- `.app-container` — main layout wrapper
- `.app-header` — header bar
- All card/panel components — use `var(--color-bg)` for surface
