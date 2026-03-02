# Quickstart: Add Pink Background Color to App

**Feature**: 016-pink-background
**Date**: 2026-03-02

## Overview

This feature updates the application's background color from white (light mode) / near-black (dark mode) to pink across all screens. The change modifies two CSS custom property values in `frontend/src/index.css`. No new files, dependencies, or backend changes are required.

## Prerequisites

- Node.js 18+ (existing dev setup)
- npm (existing)

## Development Setup

```bash
# From repo root — start the frontend dev server
cd frontend && npm install && npm run dev
```

The Vite dev server will start at `http://localhost:5173` (default) with hot module replacement. Any CSS changes to `index.css` will be reflected immediately without a page reload.

## Key File to Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/index.css` | Modify | Update `--background` CSS variable in `:root` (light) and `.dark` (dark) scopes |

## Implementation Steps

1. **Open** `frontend/src/index.css`
2. **Light mode**: In the `:root` block, change `--background: 0 0% 100%;` to `--background: 350 100% 88%;`
3. **Dark mode**: In the `.dark` block, change `--background: 222.2 84% 4.9%;` to `--background: 340 33% 41%;`
4. **Save** — Vite HMR will apply the change immediately

## Verification

### Light Mode
1. Open the app in a browser
2. Confirm the background is light pink (`#FFC0CB`) on all pages
3. Confirm all text is readable (dark text on pink background)
4. Confirm component backgrounds (cards, modals, popovers) are unchanged (still white)
5. Confirm no layout shifts or visual regressions

### Dark Mode
1. Toggle dark mode in the app (or via browser DevTools: add `class="dark"` to `<html>`)
2. Confirm the background is muted dark pink (`#8B475D`)
3. Confirm all text is readable (light text on dark pink background)
4. Confirm component backgrounds are unchanged

### Responsive
1. Test on mobile viewport (375px width)
2. Test on tablet viewport (768px width)
3. Test on desktop viewport (1440px width)
4. Confirm pink background fills the full viewport on all sizes

### Accessibility
1. Use a contrast checker (e.g., WebAIM Contrast Checker) to verify:
   - Light mode: foreground `#020817` on `#FFC0CB` → ~16.5:1 ✅
   - Dark mode: foreground `#f8fafc` on `#8B475D` → ~7.2:1 ✅

## Build Verification

```bash
# Lint check
cd frontend && npm run lint

# Build check
cd frontend && npm run build

# Test check (existing tests should still pass)
cd frontend && npm test
```

## Rollback

To revert the change, restore the original CSS variable values:

```css
/* :root */
--background: 0 0% 100%;

/* .dark */
--background: 222.2 84% 4.9%;
```
