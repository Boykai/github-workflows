# Quickstart: Add Green Background Color to App

**Feature**: 018-green-background | **Date**: 2026-03-04

## What This Feature Does

Changes the application's background color from white (light mode) / dark blue (dark mode) to green (#4CAF50 light / #2E7D32 dark) by updating CSS custom properties in the design token system.

## Prerequisites

- Node.js 18+ and npm
- Access to the repository

## How to Implement

### Step 1: Modify CSS Custom Properties

Edit `frontend/src/index.css` and update the following values:

**In `:root` selector (light mode):**
```css
--background: 122 39% 49%;    /* was: 0 0% 100% */
--foreground: 0 0% 100%;      /* was: 222.2 84% 4.9% */
```

**In `.dark` selector (dark mode):**
```css
--background: 125 35% 33%;    /* was: 222.2 84% 4.9% */
--foreground: 0 0% 100%;      /* was: 210 40% 98% */
```

### Step 2: Verify

```bash
cd frontend
npm run dev
```

1. Open http://localhost:5173 in a browser
2. Verify the background is green (#4CAF50)
3. Toggle dark mode (via app settings or browser DevTools)
4. Verify the background changes to darker green (#2E7D32)
5. Verify all text is readable (white on green)
6. Navigate between pages — green background should be consistent
7. Check that cards, popovers, and modals retain their original colors

### Step 3: Accessibility Check

Run Lighthouse or axe DevTools to confirm:
- Color contrast ratio ≥ 4.5:1 for normal text
- No accessibility regressions

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/index.css` | Update `--background` and `--foreground` CSS custom properties in `:root` and `.dark` |

## Rollback

To revert, restore the original values in `frontend/src/index.css`:

```css
/* :root */
--background: 0 0% 100%;
--foreground: 222.2 84% 4.9%;

/* .dark */
--background: 222.2 84% 4.9%;
--foreground: 210 40% 98%;
```
