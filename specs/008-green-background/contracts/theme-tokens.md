# Style Contract: Theme Tokens

**Feature**: 008-green-background
**Date**: 2026-02-21

## CSS Custom Property Contract

This contract defines the CSS custom properties (design tokens) that constitute the application's theme. All component stylesheets MUST reference these tokens rather than hard-coded color values.

### Light Mode (`:root`)

```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #4CAF50;           /* App-level green background */
  --color-bg-secondary: #43A047; /* Offset green for body/sections */
  --color-bg-surface: #ffffff;   /* NEW: White surface for cards/panels */
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
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
  --color-bg: #2E7D32;           /* Dark green background */
  --color-bg-secondary: #1B5E20; /* Darker green for body/sections */
  --color-bg-surface: #0d1117;   /* NEW: Dark surface for cards/panels */
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

## Token Usage Rules

| Token | Use For | Do NOT Use For |
|-------|---------|----------------|
| `--color-bg` | App root container, page-level backgrounds | Component surfaces (cards, panels, inputs) |
| `--color-bg-secondary` | Body background, section dividers | Component surfaces |
| `--color-bg-surface` | Cards, panels, chat bubbles, inputs, modals | App-level backgrounds |
| `--color-text` | Primary text on any background | Decorative elements |
| `--color-text-secondary` | Secondary/muted text | Primary content text |

## Contrast Requirements

| Foreground Token | Background Token | Min Ratio | Standard |
|-----------------|-----------------|-----------|----------|
| `--color-text` | `--color-bg` | 4.5:1 | WCAG AA normal text |
| `--color-text` | `--color-bg-surface` | 4.5:1 | WCAG AA normal text |
| `--color-text-secondary` | `--color-bg-surface` | 4.5:1 | WCAG AA normal text |
| `--color-primary` | `--color-bg-surface` | 3:1 | WCAG AA large text/UI |

## Migration Guide

Components currently using `var(--color-bg)` for surface backgrounds should migrate to `var(--color-bg-surface)`:

```css
/* Before */
.my-card {
  background: var(--color-bg);
}

/* After */
.my-card {
  background: var(--color-bg-surface);
}
```
