# Quickstart: Add Pink Background Color to App

**Feature**: `011-pink-background`
**Date**: 2026-02-23

---

## Prerequisites

- Node.js with dependencies installed (`cd frontend && npm install`)

## Implementation Steps

### Step 1: Update Light Mode Tokens

Edit `frontend/src/index.css`, `:root` block:

```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #FFB6C1;              /* ← was #ffffff */
  --color-bg-secondary: #FFA3B3;    /* ← was #f6f8fa */
  --color-border: #d4a0ab;          /* ← was #d0d7de */
  --color-text: #24292f;            /* unchanged */
  --color-text-secondary: #4A4F57;  /* ← was #57606a (darkened for contrast) */
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

### Step 2: Update Dark Mode Tokens

Edit `frontend/src/index.css`, `html.dark-mode-active` block:

```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #4A2030;              /* ← was #0d1117 */
  --color-bg-secondary: #3A1525;    /* ← was #161b22 */
  --color-border: #5A3040;          /* ← was #30363d */
  --color-text: #e6edf3;            /* unchanged */
  --color-text-secondary: #8b949e;  /* unchanged */
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

### Step 3: Verify Visually

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` in the browser:
1. Verify pink background appears on all pages (chat, board, settings)
2. Toggle dark mode using the theme button — verify dark-pink background
3. Check text readability on pink background
4. Resize browser to mobile/tablet widths — verify no layout shifts

### Step 4: Add Regression Test

Create or update a test that verifies the CSS token values are correct. See `research.md` R-005 for the recommended approach.

## Verification Checklist

- [ ] Light mode: body background is pink (`#FFA3B3`)
- [ ] Light mode: cards/containers background is light pink (`#FFB6C1`)
- [ ] Light mode: all text is readable (dark text on pink)
- [ ] Dark mode: body background is deep pink (`#3A1525`)
- [ ] Dark mode: cards/containers background is dark pink (`#4A2030`)
- [ ] Dark mode: all text is readable (light text on dark pink)
- [ ] No layout shifts when switching between light and dark mode
- [ ] No visual regressions on chat, board, settings pages
- [ ] Cross-browser: Chrome, Firefox, Safari, Edge render consistently
- [ ] Mobile responsive: no issues at narrow widths

## Running Tests

```bash
cd frontend

# Run all tests
npm test

# Run specific test for theme tokens (if added)
npx vitest run src/index.css.test.ts
```

## Troubleshooting

| Issue | Solution |
|-------|---------|
| Background still white/dark | Clear browser cache, check CSS is saved and served |
| Text hard to read on pink | Verify `--color-text-secondary` was updated to `#4A4F57` in light mode |
| Dark mode shows wrong color | Check `html.dark-mode-active` block has the new values |
| Component has hardcoded background | Search for `background:` or `background-color:` in App.css and update to use `var()` |
