# Contract: CSS Design Token Variables

**Feature**: 019-purple-background
**Date**: 2026-03-05
**Type**: CSS Custom Properties (frontend-only, no REST/GraphQL)

## Overview

This feature is entirely frontend CSS-based. There are no REST API endpoints, GraphQL mutations, or new TypeScript interfaces. The primary contract is the CSS custom property (design token) system defined in `frontend/src/index.css` and consumed by `frontend/tailwind.config.js`.

## CSS Variable Contract

### File: `frontend/src/index.css`

#### Light Mode (`:root`)

```css
:root {
  --background: 271 75% 40%;       /* #6B21A8 — primary purple background */
  --foreground: 0 0% 100%;          /* #FFFFFF — white text */

  --card: 271 60% 50%;              /* Lighter purple for card surfaces */
  --card-foreground: 0 0% 100%;     /* White text on cards */

  --popover: 271 60% 50%;           /* Lighter purple for popovers */
  --popover-foreground: 0 0% 100%;  /* White text on popovers */

  --primary: 271 90% 70%;           /* Bright purple for interactive elements */
  --primary-foreground: 271 75% 20%; /* Dark purple text on primary elements */

  --secondary: 271 40% 60%;         /* Muted purple for secondary surfaces */
  --secondary-foreground: 0 0% 100%; /* White text on secondary */

  --muted: 271 30% 55%;             /* Subdued purple for muted areas */
  --muted-foreground: 271 20% 85%;  /* Light purple for muted text */

  --accent: 271 40% 55%;            /* Purple accent for highlights */
  --accent-foreground: 0 0% 100%;   /* White text on accents */

  --destructive: 0 84.2% 60.2%;     /* Red — unchanged */
  --destructive-foreground: 0 0% 100%; /* White on destructive */

  --border: 271 30% 65%;            /* Purple-tinted border */
  --input: 271 30% 65%;             /* Purple-tinted input border */
  --ring: 271 90% 80%;              /* Light purple focus ring */

  --radius: 0.5rem;                  /* Unchanged */
}
```

#### Dark Mode (`.dark`)

```css
.dark {
  --background: 271 80% 10%;        /* Deep purple — dark background */
  --foreground: 271 20% 90%;        /* Light lavender text */

  --card: 271 60% 15%;              /* Slightly lighter deep purple */
  --card-foreground: 271 20% 90%;

  --popover: 271 60% 15%;
  --popover-foreground: 271 20% 90%;

  --primary: 271 80% 70%;           /* Bright purple for interactive elements */
  --primary-foreground: 271 80% 10%;

  --secondary: 271 50% 20%;
  --secondary-foreground: 271 20% 90%;

  --muted: 271 40% 20%;
  --muted-foreground: 271 20% 65%;

  --accent: 271 50% 22%;
  --accent-foreground: 271 20% 90%;

  --destructive: 0 62.8% 30.6%;     /* Dark red — unchanged */
  --destructive-foreground: 271 20% 90%;

  --border: 271 40% 25%;
  --input: 271 40% 25%;
  --ring: 271 70% 60%;
}
```

## Tailwind Config Contract

### File: `frontend/tailwind.config.js`

**No changes required.** The Tailwind config already references CSS variables via `hsl(var(--variable-name))`. Updating the CSS variable values in `index.css` automatically propagates through the Tailwind utility classes.

```javascript
// Existing config — unchanged
colors: {
  background: "hsl(var(--background))",
  foreground: "hsl(var(--foreground))",
  // ... all other tokens reference CSS variables
}
```

## Body Styles Contract

### File: `frontend/src/index.css` (base layer)

**No changes required.** The body already applies the background and foreground tokens:

```css
@layer base {
  body {
    @apply bg-background text-foreground;
  }
}
```

## Integration Points

### Components Using `bg-background`

These components automatically inherit the new purple background:

| Component | Class Usage | Impact |
|-----------|-------------|--------|
| `body` | `bg-background text-foreground` (index.css base) | ✅ Automatic — gets purple background |
| `AppContent` | `bg-background text-foreground` (App.tsx line 113) | ✅ Automatic — gets purple background |
| `header` | `bg-background` (App.tsx line 114) | ✅ Automatic — matches page background |
| `select option` | `background-color: hsl(var(--background))` (index.css) | ✅ Automatic |

### Components That May Need Audit

Components using hardcoded white/gray backgrounds that may need updating for visual consistency:

| Pattern to Search | Risk |
|-------------------|------|
| `bg-white` | Hardcoded white background visible against purple |
| `bg-gray-*` | Gray surfaces that clash with purple theme |
| `bg-slate-*` | Slate surfaces that clash with purple theme |
| `bg-amber-*` | Signal banner — should be evaluated for contrast |
| Inline `style={{ backgroundColor: ... }}` | Bypasses CSS variable system |

## Contrast Verification

| Surface | Background | Foreground | Contrast Ratio | WCAG AA |
|---------|------------|------------|---------------|---------|
| Page background | #6B21A8 | #FFFFFF | 8.21:1 | ✅ Pass |
| Card surface | ~#8B3EC9 | #FFFFFF | ~5.5:1 | ✅ Pass |
| Dark background | ~#1A0530 | ~#E3D5EE | ~10.5:1 | ✅ Pass |

## Error Handling

No error handling needed — CSS custom properties gracefully fall back. If a variable is undefined, the browser uses the `initial` value for the property. The Tailwind `hsl()` wrapper ensures valid CSS output.
