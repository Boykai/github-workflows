# Contracts: Add Copper Background Theme to App

**Feature**: `009-copper-background` | **Date**: 2026-02-23

> This feature introduces no new API endpoints and changes no existing request/response contracts. The copper background theme is implemented entirely through CSS design token updates in the frontend. No backend changes are required.

## CSS Design Token Contract

The only "contract" for this feature is the CSS custom property interface between `index.css` (token definitions) and all consuming stylesheets/components.

### Token Interface

```css
/* Light mode copper theme tokens */
:root {
  --color-bg: #B87333;           /* Primary copper background */
  --color-bg-secondary: #CB6D51; /* Secondary copper background */
  --color-text: #1A1A1A;         /* Primary text (high contrast) */
  --color-text-secondary: #2D1810; /* Secondary text */
  --color-border: #9A5C2E;       /* Copper-toned border */
  --shadow: 0 1px 3px rgba(139, 90, 43, 0.2); /* Copper-tinted shadow */
}

/* Dark mode copper theme tokens */
html.dark-mode-active {
  --color-bg: #8C4A2F;           /* Dark copper background */
  --color-bg-secondary: #6B3A24; /* Deeper copper background */
  --color-text: #FFFFFF;          /* White text (high contrast) */
  --color-text-secondary: #E8D5CC; /* Light warm secondary text */
  --color-border: #5A2E1A;       /* Deep copper border */
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.5); /* Deeper shadow */
}
```

### Consumers

All files that reference `var(--color-bg)`, `var(--color-bg-secondary)`, `var(--color-text)`, `var(--color-text-secondary)`, `var(--color-border)`, or `var(--shadow)` are automatic consumers of this contract. No consumer code changes are needed — the token values cascade through CSS inheritance.

### Backward Compatibility

- Token names are unchanged — only values change
- All `var()` references in `App.css` and component styles continue to work without modification
- The `useAppTheme` hook and dark mode toggle mechanism are unaffected
- No JavaScript/TypeScript code changes are required

## Existing API Contracts (Unchanged)

All backend API endpoints, request/response shapes, authentication mechanisms, and WebSocket protocols remain identical. This feature has zero backend impact.
