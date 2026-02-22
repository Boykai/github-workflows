# Quickstart: Add Black Background Theme to App

**Feature**: `009-black-background` | **Date**: 2026-02-22

## Prerequisites

- Node.js with npm (frontend)
- Docker + Docker Compose (for full-stack testing, optional)

## Development Setup

```bash
# 1. Switch to the feature branch
git checkout 009-black-background

# 2. Frontend: install dependencies
cd frontend
npm install
```

## Running Tests (Regression Baseline)

Before making any changes, run the existing test suite to establish the baseline:

```bash
# Frontend unit tests
cd frontend
npm test

# Frontend lint + type check
npm run lint
npm run type-check
```

**All existing tests must pass after every change.**

## Implementation Order

The changes must proceed in this order to avoid intermediate visual breakage:

1. **`index.html`** — Add inline `background-color: #000000` on `<html>` to prevent flash
2. **`index.css` `:root`** — Update all light-mode tokens to black theme values
3. **`index.css` `html.dark-mode-active`** — Update all dark-mode tokens to black theme values
4. **`App.css`** — Replace hardcoded light backgrounds (`#dafbe1`, `#fff1f0`) with dark-compatible variants
5. **`ChatInterface.css`** — Verify all hardcoded values are dark-compatible (most already are)

## Verification Workflow

After each change, verify visually and programmatically:

### 1. Visual Inspection

```bash
# Start the dev server
cd frontend
npm run dev
# Open http://localhost:5173 in browser
```

Check:
- [ ] Root background is black (#000000) on all pages
- [ ] No white flash on page load (hard refresh with Ctrl+Shift+R)
- [ ] Text is white/light and readable
- [ ] Cards, sidebar, navbar use dark gray surfaces (not pure black)
- [ ] Borders and dividers are visible but subtle
- [ ] Buttons, links, inputs are clearly visible and usable
- [ ] Toggle dark mode — both modes show black background
- [ ] Mobile viewport (375px) — theme consistent
- [ ] Tablet viewport (768px) — theme consistent

### 2. Contrast Ratio Verification

Use browser DevTools or a contrast checker to verify:

| Element | Expected Ratio | Minimum |
|---------|---------------|---------|
| Primary text on black bg | 21:1 | 4.5:1 (AA) |
| Secondary text on black bg | 10.4:1 | 4.5:1 (AA) |
| Primary text on dark gray surface | 17.4:1 | 4.5:1 (AA) |
| Link color on black bg | 6.5:1 | 4.5:1 (AA) |

### 3. Regression Tests

```bash
# Run all frontend tests
cd frontend
npm test

# Lint check
npm run lint

# Type check
npm run type-check
```

### 4. Build Verification

```bash
# Production build
cd frontend
npm run build
```

## Key Files to Modify

| File | Change | Lines Affected |
|------|--------|---------------|
| `frontend/index.html` | Add `style="background-color: #000000"` to `<html>` | 1 |
| `frontend/src/index.css` | Update `:root` token values (lines 3–14) | ~12 |
| `frontend/src/index.css` | Update `html.dark-mode-active` token values (lines 19–29) | ~11 |
| `frontend/src/App.css` | Replace `#dafbe1` → `rgba(63, 185, 80, 0.15)` | 1 |
| `frontend/src/App.css` | Replace `#fff1f0` → `rgba(248, 81, 73, 0.15)` (2 instances) | 2 |

**Total**: ~27 lines changed across 3 files + 1 HTML attribute.

## Common Pitfalls

- **White flash**: If the inline style on `<html>` is missing or overridden, a white flash will appear before CSS loads. The inline style must be on the `<html>` element, not `<body>`, because `<body>` is rendered after the DOM script executes.
- **Hardcoded colors**: Some notification/alert backgrounds use hardcoded light colors (#dafbe1, #fff1f0) that will look wrong on a black background. Replace with semi-transparent variants.
- **Shadow visibility**: The existing `--shadow` uses low opacity (`rgba(0,0,0,0.1)`) which is invisible on black. Increase opacity to 0.6/0.8 or consider using a light shadow (`rgba(255,255,255,0.05)`).
- **Dark mode toggle**: Both light and dark modes now use black backgrounds. The toggle still works (different surface/text shades) but both are dark. This is by design per the spec.
