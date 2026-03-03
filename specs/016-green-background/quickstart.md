# Quickstart: Add Green Background Color to App

**Feature**: 016-green-background  
**Date**: 2026-03-03

## Overview

This feature changes the application's background color to green by updating CSS custom properties (design tokens) in the existing `frontend/src/index.css` file. The change uses `#22c55e` for light mode and `#166534` for dark mode, with foreground text colors adjusted for WCAG AA contrast compliance.

## Prerequisites

- Node.js 18+ (existing dev setup)
- npm (existing)

## Development Setup

```bash
# From repo root — start the frontend dev server
cd frontend && npm install && npm run dev
```

The Vite dev server will hot-reload CSS changes automatically.

## Key File to Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/index.css` | Modify | Update `--background` and `--foreground` HSL values in `:root` and `.dark` |

## Implementation

### Step 1: Update Light Mode Variables

In `frontend/src/index.css`, within the `:root` selector, change:

```css
/* Before */
--background: 0 0% 100%;
--foreground: 222.2 84% 4.9%;

/* After */
--background: 142.1 76.2% 36.3%;
--foreground: 144.3 80.4% 10%;
```

### Step 2: Update Dark Mode Variables

In the same file, within the `.dark` selector, change:

```css
/* Before */
--background: 222.2 84% 4.9%;
--foreground: 210 40% 98%;

/* After */
--background: 142.1 64.2% 24.1%;
--foreground: 138.5 76.5% 96.7%;
```

### Step 3: Verify

1. Open the app in a browser
2. Confirm green background on all pages (Home, Project Board, Settings)
3. Toggle dark mode and confirm darker green background
4. Verify text is readable on the green background

## Testing the Feature

### Manual Testing

1. Start the frontend dev server: `cd frontend && npm run dev`
2. Open `http://localhost:5173` in Chrome
3. **Light mode checks**:
   - Background is green (#22c55e)
   - Body text is dark green (#052e16) and readable
   - Cards and popovers remain white with dark text
   - Navigate between Home, Project Board, and Settings — green persists
4. **Dark mode checks** (click the theme toggle):
   - Background is dark green (#166534)
   - Body text is light green (#f0fdf4) and readable
   - Cards and popovers remain dark with light text
5. **Cross-browser**: Open in Firefox, Safari, and Edge — verify same appearance
6. **Responsive**: Resize browser to mobile width (~375px) — verify no gaps or scrolling artifacts
7. **Contrast verification**: Use a tool like the Chrome DevTools color contrast checker to verify:
   - Body text on green: ≥ 4.5:1
   - Large text on green: ≥ 3:1

### Build Verification

```bash
cd frontend && npm run build
```

Ensure no CSS compilation errors.

### Lint Check

```bash
cd frontend && npm run lint
```

No changes to TypeScript/JavaScript files, so this should pass unchanged.

## Edge Cases to Verify

- Loading state (spinner) on green background is visible
- Login page (unauthenticated state) shows green background
- Signal banner bar remains visible against green background
- Dark mode toggle transitions smoothly between green variants
- Cards, modals, and popovers maintain their own backgrounds (not green)
