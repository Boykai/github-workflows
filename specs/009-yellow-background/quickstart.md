# Quickstart: Add Yellow Background to App

**Feature**: `009-yellow-background`
**Date**: 2026-02-23

---

## Prerequisites

- Node.js with dependencies installed (`cd frontend && npm install`)
- A browser for visual verification

## Implementation Steps

### Step 1: Update Light-Mode CSS Tokens

Edit `frontend/src/index.css` and change two values in the `:root` block:

```css
/* Before */
:root {
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;
  /* ... other tokens unchanged ... */
}

/* After */
:root {
  --color-bg: #FFF9C4;
  --color-bg-secondary: #FFF9C4;
  /* ... other tokens unchanged ... */
}
```

**That's it.** No other files need to be changed. The body background already uses `var(--color-bg-secondary)` and components use `var(--color-bg)`.

### Step 2: Verify (do NOT change dark mode)

Confirm that the `html.dark-mode-active` block in the same file is **untouched**:

```css
/* These values must remain unchanged */
html.dark-mode-active {
  --color-bg: #0d1117;
  --color-bg-secondary: #161b22;
  /* ... */
}
```

## Verification

### Visual Check

```bash
cd frontend
npm run dev
```

1. Open the app in a browser (default: http://localhost:5173)
2. Confirm the background is soft yellow (#FFF9C4) on all pages
3. Toggle dark mode — confirm background switches to dark (#0d1117)
4. Toggle back to light mode — confirm yellow returns

### Contrast Audit

Run a Lighthouse accessibility audit or use axe DevTools in the browser:

1. Open Chrome DevTools → Lighthouse tab
2. Select "Accessibility" category
3. Run audit
4. Verify no contrast-related failures

Or manually check with Chrome DevTools color picker:
1. Inspect any text element
2. In the Styles panel, click the color swatch for the text color
3. The contrast ratio tooltip should show ≥4.5:1 against the yellow background

### Cross-Browser Check

Open the app in each target browser and confirm the yellow background renders:
- Chrome (desktop + mobile viewport)
- Firefox (desktop + mobile viewport)
- Safari (desktop + mobile viewport)
- Edge (desktop + mobile viewport)

## Files Modified

| File | Change |
|------|--------|
| `frontend/src/index.css` | Lines 7-8: `--color-bg` and `--color-bg-secondary` values changed to `#FFF9C4` |

## Rollback

To revert, change the two values back:

```css
:root {
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;
}
```
