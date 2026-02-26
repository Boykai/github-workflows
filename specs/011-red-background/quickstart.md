# Quickstart: Add Red Background Color to App

**Feature**: 011-red-background
**Date**: 2026-02-26

## What This Feature Does

Changes the application's primary background color from light gray (`#f6f8fa`) to red (`#E53E3E`) by updating the `--color-bg-secondary` CSS custom property in `frontend/src/index.css`.

## Prerequisites

- Node.js (for frontend development server)
- The repository cloned locally

## Quick Verification

### 1. Start the frontend dev server

```bash
cd frontend
npm install
npm run dev
```

### 2. Open the application

Navigate to `http://localhost:5173` in your browser.

### 3. Verify the red background

- **Expected**: The page background behind all components (header, sidebar, cards) is red (#E53E3E)
- **Check light mode**: Background should be red
- **Check dark mode**: Click the theme toggle (🌙/☀️) — background should remain red
- **Check contrast**: All text on the red background surface should be readable

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/index.css` | Updated `--color-bg-secondary` from `#f6f8fa` to `#E53E3E` (light mode) and from `#161b22` to `#E53E3E` (dark mode). Added fallback to body background declaration. |

## Rollback

To revert the red background, restore the original values in `frontend/src/index.css`:

```css
/* Light mode (:root) */
--color-bg-secondary: #f6f8fa;

/* Dark mode (html.dark-mode-active) */
--color-bg-secondary: #161b22;
```
