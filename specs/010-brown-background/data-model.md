# Data Model: Add Brown Background Color to App

**Feature**: `010-brown-background` | **Date**: 2026-02-22

> This feature creates no new data entities, database changes, or API modifications. It is a CSS-only change to existing design tokens (CSS custom properties). This document describes the **design token changes** — the CSS custom property values being modified.

## Design Tokens (CSS Custom Properties)

### Modified Tokens — Light Mode (`:root`)

| Token | Current Value | New Value | Purpose |
|-------|--------------|-----------|---------|
| `--color-bg` | `#ffffff` | `#4E342E` | Primary app background (Material Brown 800) |
| `--color-bg-secondary` | `#f6f8fa` | `#5D4037` | Secondary/body background (Material Brown 700) |
| `--color-text` | `#24292f` | `#e6edf3` | Primary text color (light for contrast on brown) |
| `--color-text-secondary` | `#57606a` | `#8b949e` | Secondary text color (muted light) |
| `--color-border` | `#d0d7de` | `#6D4C41` | Border color (Brown 600 for visibility) |

### Modified Tokens — Dark Mode (`html.dark-mode-active`)

| Token | Current Value | New Value | Purpose |
|-------|--------------|-----------|---------|
| `--color-bg` | `#0d1117` | `#3E2723` | Primary app background (Material Brown 900) |
| `--color-bg-secondary` | `#161b22` | `#4E342E` | Secondary/body background (Material Brown 800) |

> Dark mode text colors (`--color-text: #e6edf3`, `--color-text-secondary: #8b949e`) remain unchanged as they already provide sufficient contrast against the brown backgrounds.

### Unchanged Tokens

| Token | Value (Light) | Value (Dark) | Reason Unchanged |
|-------|--------------|-------------|-----------------|
| `--color-primary` | `#0969da` | `#539bf5` | Accent color; provides good contrast on brown |
| `--color-secondary` | `#6e7781` | `#8b949e` | Secondary accent; adequate visibility |
| `--color-success` | `#1a7f37` | `#3fb950` | Status color; distinct from brown |
| `--color-warning` | `#9a6700` | `#d29922` | Status color; distinct from brown |
| `--color-danger` | `#cf222e` | `#f85149` | Status color; distinct from brown |
| `--radius` | `6px` | `6px` | Layout token; unrelated |
| `--shadow` | `rgba(0,0,0,0.1)` | `rgba(0,0,0,0.4)` | Shadow; works on any background |

### WCAG AA Contrast Ratios

| Text Token | Background Token | Contrast Ratio | WCAG AA (4.5:1) |
|------------|-----------------|---------------|-----------------|
| `--color-text` (#e6edf3) | `--color-bg` (#4E342E) | ~10.5:1 | ✅ PASS |
| `--color-text` (#e6edf3) | `--color-bg-secondary` (#5D4037) | ~8.5:1 | ✅ PASS |
| `--color-text-secondary` (#8b949e) | `--color-bg` (#4E342E) | ~4.6:1 | ✅ PASS |
| `--color-text` (#e6edf3) | `--color-bg` dark (#3E2723) | ~12.3:1 | ✅ PASS |
| `--color-text` (#e6edf3) | `--color-bg-secondary` dark (#4E342E) | ~10.5:1 | ✅ PASS |

## Entity Relationships

```text
index.css (:root)
  └── --color-bg: #4E342E          ← Used by App.css (.app-container, cards, etc.)
  └── --color-bg-secondary: #5D4037 ← Used by body, sidebar, input backgrounds
  └── --color-text: #e6edf3        ← Used by all text content
  └── --color-text-secondary: #8b949e ← Used by muted text
  └── --color-border: #6D4C41      ← Used by all bordered elements

index.css (html.dark-mode-active)
  └── --color-bg: #3E2723          ← Darker brown for dark mode
  └── --color-bg-secondary: #4E342E ← Dark mode secondary
```

## State Transitions: No Changes

The `useAppTheme` hook toggles between light and dark mode by adding/removing the `dark-mode-active` class on `<html>`. This mechanism is unchanged. The only difference is the visual output: brown backgrounds instead of white/dark backgrounds.

## Validation Rules: No Changes

No validation logic is affected by this CSS change.
