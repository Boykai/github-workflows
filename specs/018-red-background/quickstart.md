# Quickstart: Add Red Background Color to App

**Feature**: 018-red-background | **Date**: 2026-03-04

## What This Feature Does

Changes the application's background color from the default white/dark navy to a red theme by updating CSS design tokens. Light mode uses Material Red 700 (`#D32F2F`) and dark mode uses Material Red 900 (`#B71C1C`).

## Prerequisites

- Node.js (version compatible with project)
- npm or yarn
- Access to the `frontend/` directory

## Implementation Steps

### Step 1: Update CSS Variables (Single File Change)

**File**: `frontend/src/index.css`

Update the `--background` and `--foreground` values in both the `:root` (light mode) and `.dark` (dark mode) blocks:

```css
@layer base {
  :root {
    --background: 0 70% 50%;       /* Was: 0 0% 100% (white) → Now: Material Red 700 (#D32F2F) */
    --foreground: 0 0% 100%;       /* Was: 222.2 84% 4.9% (navy) → Now: White (#FFFFFF) */
    /* ... all other variables remain unchanged ... */
  }

  .dark {
    --background: 0 73% 41%;       /* Was: 222.2 84% 4.9% (navy) → Now: Material Red 900 (#B71C1C) */
    --foreground: 0 0% 100%;       /* Was: 210 40% 98% (off-white) → Now: White (#FFFFFF) */
    /* ... all other variables remain unchanged ... */
  }
}
```

### Step 2: Verify Locally

```bash
cd frontend
npm install     # if not already done
npm run dev     # start dev server
```

1. Open the app in a browser
2. Verify the red background is visible on all pages
3. Toggle between light and dark mode to verify both variants
4. Check that cards, modals, and other components maintain their own backgrounds
5. Verify all text is readable (white text on red background)

### Step 3: Run Accessibility Check

```bash
cd frontend
npm run test:a11y    # if accessibility tests exist
```

Or manually verify contrast ratios:
- Light mode: `#D32F2F` background + `#FFFFFF` text = 4.68:1 (passes WCAG AA)
- Dark mode: `#B71C1C` background + `#FFFFFF` text = 6.27:1 (passes WCAG AA)

### Step 4: Run Existing Tests

```bash
cd frontend
npm run test         # unit tests
npm run build        # verify production build
```

## Verification Checklist

- [ ] Red background visible on all pages in light mode
- [ ] Red background visible on all pages in dark mode (darker shade)
- [ ] System theme preference correctly selects the appropriate red shade
- [ ] All text is readable (white on red)
- [ ] Cards, modals, and popovers maintain their own background colors
- [ ] Buttons, inputs, and links remain visually distinct
- [ ] No layout or spacing changes introduced
- [ ] Production build succeeds without errors

## Rollback

To revert, restore the original CSS variable values:

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
}
.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
}
```
