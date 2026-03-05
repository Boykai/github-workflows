# Quickstart: Add Purple Background Color to App

**Feature**: 019-purple-background
**Date**: 2026-03-05

## Overview

This feature updates the app's global background from white/neutral to a purple color scheme (#6B21A8). The change is implemented entirely through CSS custom property (design token) updates in the existing theming system. No new components, hooks, or dependencies are needed.

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────┐
│              frontend/src/index.css                   │
│                                                       │
│  :root {                                              │
│    --background: 271 75% 40%;  ← Purple (#6B21A8)    │
│    --foreground: 0 0% 100%;    ← White (#FFFFFF)      │
│    --card: 271 60% 50%;        ← Lighter purple       │
│    --border: 271 30% 65%;      ← Purple-tinted        │
│    ...                                                │
│  }                                                    │
│                                                       │
│  .dark {                                              │
│    --background: 271 80% 10%;  ← Deep purple          │
│    --foreground: 271 20% 90%;  ← Light lavender       │
│    ...                                                │
│  }                                                    │
│                                                       │
│  body { @apply bg-background text-foreground; }       │
│         │                                             │
│         ▼ already applied via Tailwind                │
│  ┌─────────────────────────────────┐                  │
│  │ All components using bg-*       │                  │
│  │ tokens get purple automatically │                  │
│  └─────────────────────────────────┘                  │
└───────────────────────────────────────────────────────┘
```

## Key Files

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/index.css` | **Modify** | Update CSS custom property values for both `:root` (light) and `.dark` themes |

## Implementation Steps (High Level)

### Step 1: Update Light Mode CSS Variables (`:root`)

Replace the existing HSL values in the `:root` block of `frontend/src/index.css` with purple-themed values:

```css
:root {
  --background: 271 75% 40%;        /* #6B21A8 purple */
  --foreground: 0 0% 100%;          /* white text */
  --card: 271 60% 50%;              /* lighter purple for cards */
  --card-foreground: 0 0% 100%;
  --popover: 271 60% 50%;
  --popover-foreground: 0 0% 100%;
  --primary: 271 90% 70%;
  --primary-foreground: 271 75% 20%;
  --secondary: 271 40% 60%;
  --secondary-foreground: 0 0% 100%;
  --muted: 271 30% 55%;
  --muted-foreground: 271 20% 85%;
  --accent: 271 40% 55%;
  --accent-foreground: 0 0% 100%;
  --destructive: 0 84.2% 60.2%;      /* unchanged */
  --destructive-foreground: 0 0% 100%;
  --border: 271 30% 65%;
  --input: 271 30% 65%;
  --ring: 271 90% 80%;
  --radius: 0.5rem;
}
```

### Step 2: Update Dark Mode CSS Variables (`.dark`)

Replace the existing HSL values in the `.dark` block:

```css
.dark {
  --background: 271 80% 10%;
  --foreground: 271 20% 90%;
  --card: 271 60% 15%;
  --card-foreground: 271 20% 90%;
  --popover: 271 60% 15%;
  --popover-foreground: 271 20% 90%;
  --primary: 271 80% 70%;
  --primary-foreground: 271 80% 10%;
  --secondary: 271 50% 20%;
  --secondary-foreground: 271 20% 90%;
  --muted: 271 40% 20%;
  --muted-foreground: 271 20% 65%;
  --accent: 271 50% 22%;
  --accent-foreground: 271 20% 90%;
  --destructive: 0 62.8% 30.6%;       /* unchanged */
  --destructive-foreground: 271 20% 90%;
  --border: 271 40% 25%;
  --input: 271 40% 25%;
  --ring: 271 70% 60%;
}
```

### Step 3: Audit for Hardcoded Colors

Search the codebase for hardcoded background overrides:

```bash
cd frontend && grep -rn "bg-white\|bg-gray\|bg-slate\|backgroundColor.*white\|backgroundColor.*#fff" src/
```

Update any occurrences to use the design token classes (`bg-background`, `bg-card`, `bg-muted`, etc.) instead.

### Step 4: Verify

```bash
cd frontend && npm run build       # Verify no build errors
cd frontend && npx vitest run src/ # Verify no test failures
```

Then visually inspect:
1. Light mode — all pages show purple background
2. Dark mode — all pages show deep purple background
3. Text contrast is readable on all surfaces
4. Cards/modals have visual separation from background

## User Story → Code Mapping

| Story | Priority | Implementation |
|-------|----------|----------------|
| US1: Purple background all pages | P1 | Update `--background` in `:root` to `271 75% 40%` |
| US2: Text readability | P1 | Update `--foreground` to `0 0% 100%`; all dependent tokens get white/light foreground |
| US3: UI component consistency | P2 | Update `--card`, `--popover`, `--muted`, `--accent`, `--border` to purple variants |
| US4: Cross-browser consistency | P2 | Standard CSS custom properties — inherently cross-browser; test in major browsers |
| US5: Maintainable color definition | P3 | Colors defined centrally in CSS variables in index.css — already single source of truth |

## Dependencies

- **No new npm packages required**
- Uses existing: Tailwind CSS 3.4, CSS custom properties (browser built-in)
- No backend changes needed

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Hardcoded `bg-white` in components | Search and replace with `bg-background` or `bg-card` |
| Components with inline styles | Audit for `style={{ backgroundColor: ... }}` patterns |
| Signal banner (amber bg) visible on purple | Verify amber-50/amber-900 remain legible against purple context |
| Third-party component styles | Components from shadcn/ui use CSS variables — automatically updated |
| Dark mode purple too dark/indistinguishable | Use `271 80% 10%` (not pure black); card uses `271 60% 15%` for separation |
