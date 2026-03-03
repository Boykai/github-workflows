# Quickstart: Add Blue Background Color to App

**Feature**: 016-blue-background  
**Date**: 2026-03-03

## Overview

This feature changes the application's root background color from white (light mode) / dark navy (dark mode) to blue (light mode: Dodger Blue `#1E90FF`, dark mode: Deep Blue `#1A3A5C`). The change is made by modifying two CSS variable values in `frontend/src/index.css`.

## Prerequisites

- Node.js 18+ (existing)
- npm (existing)
- A modern browser (Chrome, Firefox, Safari, or Edge)

## Development Setup

```bash
# From repo root — start frontend dev server
cd frontend && npm install && npm run dev
```

The dev server starts at `http://localhost:5173` with hot module replacement. CSS changes take effect immediately without a full page reload.

## Key File to Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/index.css` | Modify | Update `--background` CSS variable in `:root` and `.dark` selectors |

No other files need modification.

## Implementation Steps

1. Open `frontend/src/index.css`
2. In the `:root` selector, change `--background: 0 0% 100%;` to `--background: 210 100% 56%;`
3. In the `.dark` selector, change `--background: 222.2 84% 4.9%;` to `--background: 210 54% 23%;`
4. Save — hot reload applies the change instantly

## Testing the Feature

### Manual Visual Testing

1. **Light mode blue background**: Open the app at `http://localhost:5173`. The page background should be Dodger Blue (`#1E90FF`).
2. **Dark mode blue background**: Click the theme toggle button (🌙/☀️). The background should change to Deep Blue (`#1A3A5C`).
3. **Text readability**: Verify that all text (headings, body, navigation, buttons) is clearly legible against the blue backgrounds.
4. **Component integrity**: Open modals, cards, and popovers — verify they retain their own background colors (white/dark) and remain readable.
5. **Responsive**: Resize the browser from 320px to 2560px width — the blue background should fill the entire viewport at all sizes with no gaps.
6. **Navigation**: Navigate between Home, Project Board, and Settings views — the blue background should persist across all routes.
7. **Loading state**: Refresh the page — the blue background should appear during the loading spinner, not flash white first.
8. **Unauthenticated state**: Log out — the login page should also show the blue background.

### Contrast Verification

Use a browser's accessibility tools or a WCAG contrast checker to verify:

| Theme | Background | Foreground | Expected Ratio | Minimum |
|-------|-----------|------------|-----------------|---------|
| Light | `#1E90FF` | `#020817` | ~7.9:1 | ≥4.5:1 ✅ |
| Dark | `#1A3A5C` | `#F8FAFC` | ~8.5:1 | ≥4.5:1 ✅ |

### Edge Cases to Verify

- Page with no content (loading state): Blue background still visible
- Overlay/modal open: Modal backdrop renders correctly over blue
- Very narrow viewport (<320px): No horizontal scrollbars or white gaps
- Browser zoom (up to 200%): Background still covers full viewport
