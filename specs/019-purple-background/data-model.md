# Data Model: Add Purple Background Color to App

**Feature**: 019-purple-background
**Date**: 2026-03-05
**Status**: Complete

## Entities

### 1. CSS Design Tokens (Light Mode — `:root`)

**Description**: CSS custom properties defined on the `:root` selector in `frontend/src/index.css`. These tokens define the light mode color palette and are consumed by Tailwind CSS via `hsl(var(--token-name))` references in `tailwind.config.js`.

| Token | Current Value (HSL) | New Value (HSL) | Hex Equivalent | Purpose |
|-------|-------------------|-----------------|----------------|---------|
| `--background` | `0 0% 100%` (white) | `271 75% 40%` | #6B21A8 | Primary page background |
| `--foreground` | `222.2 84% 4.9%` (near-black) | `0 0% 100%` | #FFFFFF | Primary text color |
| `--card` | `0 0% 100%` (white) | `271 60% 50%` | #8B3EC9 | Card surface background |
| `--card-foreground` | `222.2 84% 4.9%` | `0 0% 100%` | #FFFFFF | Card text color |
| `--popover` | `0 0% 100%` (white) | `271 60% 50%` | #8B3EC9 | Popover/dropdown background |
| `--popover-foreground` | `222.2 84% 4.9%` | `0 0% 100%` | #FFFFFF | Popover text color |
| `--primary` | `222.2 47.4% 11.2%` | `271 90% 70%` | #C084FC | Primary interactive color |
| `--primary-foreground` | `210 40% 98%` | `271 75% 20%` | #3B0764 | Text on primary elements |
| `--secondary` | `210 40% 96.1%` | `271 40% 60%` | #A368C9 | Secondary surfaces |
| `--secondary-foreground` | `222.2 47.4% 11.2%` | `0 0% 100%` | #FFFFFF | Text on secondary surfaces |
| `--muted` | `210 40% 96.1%` | `271 30% 55%` | #9568A8 | Muted/subdued surfaces |
| `--muted-foreground` | `215.4 16.3% 46.9%` | `271 20% 85%` | #D5C4E0 | Muted text |
| `--accent` | `210 40% 96.1%` | `271 40% 55%` | #9B5CC0 | Accent/highlight surfaces |
| `--accent-foreground` | `222.2 47.4% 11.2%` | `0 0% 100%` | #FFFFFF | Text on accent surfaces |
| `--destructive` | `0 84.2% 60.2%` | `0 84.2% 60.2%` | #EF4444 | Destructive action (unchanged) |
| `--destructive-foreground` | `210 40% 98%` | `0 0% 100%` | #FFFFFF | Text on destructive (unchanged) |
| `--border` | `214.3 31.8% 91.4%` | `271 30% 65%` | #B08AC0 | Border color |
| `--input` | `214.3 31.8% 91.4%` | `271 30% 65%` | #B08AC0 | Input border color |
| `--ring` | `222.2 84% 4.9%` | `271 90% 80%` | #D8B4FE | Focus ring color |

---

### 2. CSS Design Tokens (Dark Mode — `.dark`)

**Description**: CSS custom properties under the `.dark` class selector, activated when dark mode is enabled via the ThemeProvider.

| Token | Current Value (HSL) | New Value (HSL) | Hex Equivalent | Purpose |
|-------|-------------------|-----------------|----------------|---------|
| `--background` | `222.2 84% 4.9%` | `271 80% 10%` | #1A0530 | Dark mode background |
| `--foreground` | `210 40% 98%` | `271 20% 90%` | #E3D5EE | Dark mode text |
| `--card` | `222.2 84% 4.9%` | `271 60% 15%` | #2D0A50 | Dark card surface |
| `--card-foreground` | `210 40% 98%` | `271 20% 90%` | #E3D5EE | Dark card text |
| `--popover` | `222.2 84% 4.9%` | `271 60% 15%` | #2D0A50 | Dark popover surface |
| `--popover-foreground` | `210 40% 98%` | `271 20% 90%` | #E3D5EE | Dark popover text |
| `--primary` | `210 40% 98%` | `271 80% 70%` | #C084FC | Dark primary interactive |
| `--primary-foreground` | `222.2 47.4% 11.2%` | `271 80% 10%` | #1A0530 | Text on dark primary |
| `--secondary` | `217.2 32.6% 17.5%` | `271 50% 20%` | #3B1260 | Dark secondary surfaces |
| `--secondary-foreground` | `210 40% 98%` | `271 20% 90%` | #E3D5EE | Dark secondary text |
| `--muted` | `217.2 32.6% 17.5%` | `271 40% 20%` | #3B1560 | Dark muted surfaces |
| `--muted-foreground` | `215 20.2% 65.1%` | `271 20% 65%` | #A88DC0 | Dark muted text |
| `--accent` | `217.2 32.6% 17.5%` | `271 50% 22%` | #421568 | Dark accent surfaces |
| `--accent-foreground` | `210 40% 98%` | `271 20% 90%` | #E3D5EE | Dark accent text |
| `--destructive` | `0 62.8% 30.6%` | `0 62.8% 30.6%` | #7F1D1D | Dark destructive (unchanged) |
| `--destructive-foreground` | `210 40% 98%` | `271 20% 90%` | #E3D5EE | Dark destructive text |
| `--border` | `217.2 32.6% 17.5%` | `271 40% 25%` | #462070 | Dark border |
| `--input` | `217.2 32.6% 17.5%` | `271 40% 25%` | #462070 | Dark input border |
| `--ring` | `212.7 26.8% 83.9%` | `271 70% 60%` | #A855F7 | Dark focus ring |

---

### 3. Theme State (Existing — No Changes)

**Description**: The existing ThemeProvider manages light/dark mode state. No changes to the state model are needed.

| Field | Type | Description | Location |
|-------|------|-------------|----------|
| `theme` | `"dark" \| "light" \| "system"` | Current active theme | React Context via ThemeProvider |
| Storage key | `string` | localStorage persistence key | `vite-ui-theme` in localStorage |

**State Transitions**: Unchanged. The ThemeProvider toggles the `dark` class on `<html>`, which triggers the `.dark` CSS variable overrides.

## Relationships

```
┌─────────────────────────────┐
│  frontend/src/index.css      │
│                              │
│  :root {                     │
│    --background: 271 75% 40% │ ◄── Purple (light mode)
│    --foreground: 0 0% 100%   │ ◄── White text
│    ...                       │
│  }                           │
│                              │
│  .dark {                     │
│    --background: 271 80% 10% │ ◄── Deep purple (dark mode)
│    --foreground: 271 20% 90% │ ◄── Light purple text
│    ...                       │
│  }                           │
└──────────────┬──────────────┘
               │ consumed by
               ▼
┌─────────────────────────────┐
│  tailwind.config.js          │
│                              │
│  colors: {                   │
│    background:               │
│      "hsl(var(--background))"│
│    foreground:               │
│      "hsl(var(--foreground))"│
│    ...                       │
│  }                           │
└──────────────┬──────────────┘
               │ generates utilities
               ▼
┌─────────────────────────────┐
│  Components                  │
│                              │
│  body  → bg-background       │
│  App   → bg-background       │
│  cards → bg-card             │
│  text  → text-foreground     │
└─────────────────────────────┘
```

## Validation Rules

| Rule | Enforcement | Requirement |
|------|-------------|-------------|
| Purple background contrast vs white text ≥ 4.5:1 | Manual audit + accessibility tools | FR-002 (WCAG AA) |
| All pages use `bg-background` (no hardcoded whites) | Code audit for hardcoded `bg-white`, `bg-gray-*` overrides | FR-003 |
| Color defined in single source (`--background` in index.css) | Code review | FR-004, SC-004 |
| Card/popover surfaces visually distinguishable from background | Visual review | FR-005 |
| Consistent rendering across browsers | Manual cross-browser test | FR-007 |

## Type Definitions

```css
/* 
 * No TypeScript types needed — this feature is pure CSS.
 * The design tokens are CSS custom properties consumed by Tailwind.
 * 
 * HSL format: "hue saturation% lightness%"
 * Example: "271 75% 40%" → hsl(271, 75%, 40%) → #6B21A8
 *
 * The Tailwind config wraps these in hsl(): 
 *   background: "hsl(var(--background))"
 */
```
