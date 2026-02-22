# Quickstart: Add Black Background Theme to App

**Feature**: `009-black-background` | **Date**: 2026-02-22

## Prerequisites

- Node.js with npm (frontend)
- Docker + Docker Compose (optional — for full-stack verification only)

## Development Setup

```bash
# 1. Switch to the feature branch
git checkout 009-black-background

# 2. Frontend: install dependencies
cd frontend
npm install
```

## Implementation Order

The changes should be applied in this order to avoid intermediate visual breakage:

### Step 1: Prevent Flash of White (index.html)

Add inline background to the `<html>` element:

```html
<html lang="en" style="background-color: #000000">
```

**Verify**: Open the app — background should be black immediately, even before CSS loads.

### Step 2: Update Light Mode Tokens (index.css — `:root`)

Replace all `:root` custom property values:

```css
:root {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #000000;
  --color-bg-secondary: #121212;
  --color-border: #2C2C2C;
  --color-text: #ffffff;
  --color-text-secondary: #b0b0b0;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Verify**: All pages show black background with white text. No light patches.

### Step 3: Update Dark Mode Tokens (index.css — `html.dark-mode-active`)

Replace all dark mode custom property values:

```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #000000;
  --color-bg-secondary: #0a0a0a;
  --color-border: #1e1e1e;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Verify**: Toggle dark mode — background stays black, surfaces and borders shift subtly.

### Step 4: Audit and Fix Hardcoded Colors (App.css)

Replace light-background hardcoded colors:

| Find | Replace | Context |
|------|---------|---------|
| `background: #dafbe1` | `background: rgba(63, 185, 80, 0.15)` | Success alert |
| `background: #fff1f0` | `background: rgba(248, 81, 73, 0.15)` | Error alert/message |

**Verify**: Trigger success and error states — alert backgrounds should be semi-transparent dark-tinted, not bright green/red patches.

### Step 5: Verify All Views

Navigate through:
1. Login page
2. Project board (with cards, columns)
3. Chat interface
4. Settings page
5. Sidebar navigation

**Check at each**:
- Black root background visible
- Text readable (white/light)
- Cards/modals use dark gray surfaces
- Borders visible but subtle
- No white patches or flashes

## Running Tests

```bash
# Frontend unit tests
cd frontend && npm test

# Frontend type check
npm run type-check

# Frontend lint
npm run lint

# E2E tests (if Playwright is configured)
npm run test:e2e
```

## Verification Checklist

- [ ] Root background is `#000000` on all pages
- [ ] No flash of white on page load or route transition
- [ ] All primary text passes WCAG AA 4.5:1 contrast against black
- [ ] All secondary text passes WCAG AA 4.5:1 contrast against black
- [ ] Cards, sidebar, modals use dark gray (`#121212`) surface
- [ ] Borders and dividers are visible but subtle (`#2C2C2C`)
- [ ] Buttons, links, inputs are clearly visible and interactive
- [ ] Success/error alerts use dark semi-transparent backgrounds
- [ ] Theme persists after page refresh
- [ ] Responsive: consistent at 375px, 768px, 1280px viewports
- [ ] Dark mode toggle still functions (both modes have black base)

## Common Pitfalls

- **Missed hardcoded colors**: Search `App.css` for any remaining `#fff`, `#FFF`, `white`, `#f6f8fa`, or similar light values.
- **Third-party component styles**: If any library injects light backgrounds, override via CSS specificity or theme configuration.
- **Transparent backgrounds on surfaces**: Some components may have `background: transparent` which is correct — they inherit from their parent's background.
- **Shadow visibility**: On a black background, dark shadows may be invisible. The `--shadow` token uses `rgba(0,0,0,0.4)` which provides subtle depth on elevated surfaces (`#121212`).
