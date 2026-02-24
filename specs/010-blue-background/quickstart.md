# Quickstart: Add Blue Background Color to App

**Feature**: `010-blue-background`  
**Date**: 2026-02-24

---

## Prerequisites

- Node.js with dependencies installed (`cd frontend && npm install`)

## Files to Modify

1. **`frontend/src/index.css`** — Update CSS custom property values in `:root` and `html.dark-mode-active`
2. **`frontend/index.html`** — Add inline `background-color` to `<body>` for flash prevention

## Applying the Changes

### Step 1: Update CSS Custom Properties

Edit `frontend/src/index.css` and replace the color token values in both `:root` (light mode) and `html.dark-mode-active` (dark mode) selectors. Refer to `contracts/css-tokens.md` for the exact values.

### Step 2: Add Flash Prevention

Edit `frontend/index.html` and add an inline style to the `<body>` tag:

```html
<body style="background-color: #1D4ED8;">
```

### Step 3: Review Child Components

Search for any hardcoded `background`, `background-color`, or `bg-` values in component CSS/TSX files that may conflict with the new blue theme:

```bash
cd frontend
grep -rn "background" src/ --include="*.css" --include="*.tsx" | grep -v "node_modules" | grep -v "var(--"
```

## Verifying the Changes

### Local Development Server

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` and verify:
1. The background is blue across all pages
2. Text is readable (white/light text on blue)
3. Toggle dark mode — background changes to deep navy blue
4. No flash of non-blue background on page load (hard refresh with Ctrl+Shift+R)

### Accessibility Check

Use browser DevTools (Chrome: Lighthouse > Accessibility) or a contrast checker tool:
- Verify all text achieves ≥4.5:1 contrast ratio against the blue background
- Check interactive elements (buttons, links, inputs) remain visually distinct

### Cross-Browser Testing

Test in Chrome, Firefox, Safari, and Edge:
- Blue background renders identically
- Dark mode toggle works
- No layout issues at mobile (320px), tablet (768px), and desktop (1920px) widths

### Build Verification

```bash
cd frontend
npm run build
```

Ensure the production build completes without errors.

## Troubleshooting

| Issue | Solution |
|-------|---------|
| White flash on page load | Verify `<body>` inline style in `index.html` matches `--color-bg-secondary` |
| Text unreadable | Check contrast ratios in `contracts/css-tokens.md` — text tokens may need adjustment |
| Components have white backgrounds | Search for hardcoded `background: white` or `background: #fff` in component styles |
| Dark mode doesn't change | Verify `html.dark-mode-active` selector values are updated in `index.css` |
| Build fails | Run `npm run build` and check for CSS syntax errors in `index.css` |
