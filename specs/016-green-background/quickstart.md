# Quickstart: Add Green Background Color to App

**Feature**: 016-green-background  
**Date**: 2026-03-02

## Overview

This feature changes the application's global background color from white to green (#4CAF50) by updating a single CSS custom property in the existing Tailwind/shadcn theming system. The change affects all pages and routes in light mode while preserving overlay component backgrounds (modals, popovers, cards, dropdowns).

## Prerequisites

- Node.js 18+ (existing dev setup)
- npm (existing)
- Modern browser for visual verification

## Development Setup

```bash
# From repo root — start frontend dev server
cd frontend && npm install && npm run dev
```

The dev server runs at `http://localhost:5173` by default (Vite).

## Key File to Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/index.css` | Modify | Update `--background` CSS custom property from white HSL to green HSL |

## The Change

In `frontend/src/index.css`, within the `:root` block:

```css
/* Before */
--background: 0 0% 100%;

/* After */
--background: 122 39% 49%;
```

This single change propagates green to:
- `body` (via `@apply bg-background` in CSS base layer)
- Root `<div>` in `App.tsx` (via `className="bg-background"`)
- Header in `App.tsx` (via `className="bg-background"`)
- All other elements using the `bg-background` Tailwind utility

## Verification Checklist

### Visual Verification

1. **Home page**: Navigate to `/` — background should be green
2. **Board page**: Navigate to `/#board` — background should be green
3. **Settings page**: Navigate to `/#settings` — background should be green
4. **Page transitions**: Click between Home, Board, and Settings — no flash of white
5. **Text readability**: All text should be clearly legible against green background
6. **Dark mode toggle**: Click the theme toggle (☀️/🌙) — dark mode should retain dark background, light mode should show green

### Overlay Verification

1. **Modals**: Open any modal (e.g., issue detail) — modal should have white/card background, not green
2. **Dropdowns**: Open any dropdown — should retain its own background color
3. **Tooltips**: Hover over any tooltipped element — tooltip should not be green
4. **Cards**: Board columns and issue cards should retain their own backgrounds

### Contrast Verification

1. **Normal text**: Verify dark text on green background is readable
2. **Headings**: Verify heading text is clearly visible
3. **Icons**: Verify icons are distinguishable against green
4. **Buttons**: Verify button text and borders remain clear

## Build Verification

```bash
cd frontend

# Type-check (no changes expected — CSS only)
npm run type-check

# Lint (no changes expected — CSS only)
npm run lint

# Run tests (no changes expected — CSS only)
npm test

# Build for production
npm run build
```

## Rollback

To revert to white background, change the `:root` `--background` value back to `0 0% 100%` in `frontend/src/index.css`.
