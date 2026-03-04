# Quickstart: Add Golden Background to App

**Feature**: `018-golden-background` | **Date**: 2026-03-04

## Overview

Apply a golden background color globally across the application by updating CSS custom properties in the existing theme system. Light mode gets a rich gold (#FFD700), dark mode gets a deepened dark-gold variant. All text maintains WCAG AA contrast compliance. Cards, popovers, and overlays retain their own backgrounds.

## Prerequisites

- Running instance of the app (frontend via `npm run dev` or `docker compose up`)
- A modern browser (Chrome, Firefox, Safari, or Edge)

## Quick Walkthrough

### Verifying the Golden Background

1. Start the frontend development server:
   ```bash
   cd frontend && npm run dev
   ```
2. Open `http://localhost:5173` in your browser
3. **Light mode**: The page background should be a rich gold color (#FFD700)
4. **Dark mode**: Toggle to dark mode via Settings → Advanced Settings → Display Preferences → Theme → Dark
   - The background should display a deepened dark-gold tone
5. **Responsive check**: Resize the browser to mobile, tablet, and desktop widths
   - The golden background should remain consistent with no layout breakage
6. **Component check**: Navigate to various pages (board, settings, chat)
   - Cards, modals, and dropdowns should retain their own backgrounds (white in light mode, dark in dark mode)
   - All text should be clearly readable against the golden background

### Verifying Contrast Compliance

1. Open browser DevTools → Elements
2. Select the `<body>` element
3. Inspect the computed `background-color` — should show `rgb(255, 215, 0)` in light mode
4. Use the browser's accessibility tools or an external contrast checker:
   - Enter the background color: `#FFD700`
   - Enter the foreground color: `#020817` (the existing dark text)
   - Verify the contrast ratio is ≥4.5:1 (expected: ~13.6:1)

### Verifying the Design Token

1. Open `frontend/src/index.css`
2. In the `:root` block, verify `--background: 51 100% 50%;`
3. In the `.dark` block, verify `--background: 43 74% 15%;`
4. Open DevTools → Elements → `<html>` element → Computed Styles
5. Verify `--background` resolves to the correct HSL values

## Key Files

### Modified
- `frontend/src/index.css` — Updated `--background` CSS variable in `:root` and `.dark` selectors

### Unchanged (no modifications needed)
- `frontend/tailwind.config.js` — Already maps `background` to `hsl(var(--background))`
- `frontend/src/components/ThemeProvider.tsx` — Already toggles `.dark` class on `documentElement`

## Color Reference

| Mode | Token | HSL Value | Hex Equivalent | Description |
|------|-------|-----------|----------------|-------------|
| Light | `--background` | `51 100% 50%` | #FFD700 | Standard CSS "gold" |
| Dark | `--background` | `43 74% 15%` | ~#43330A | Deepened dark gold |
| Light | `--foreground` | `222.2 84% 4.9%` | #020817 | Unchanged dark text |
| Dark | `--foreground` | `210 40% 98%` | #F8FAFC | Unchanged light text |
