# Quickstart: Add Copper Background Theme to App

**Feature**: `009-copper-background` | **Date**: 2026-02-23

## Prerequisites

- Node.js with npm (frontend)
- A modern browser (Chrome, Firefox, Safari, or Edge)

## Development Setup

```bash
# 1. Switch to the feature branch
git checkout 009-copper-background

# 2. Frontend: install dependencies
cd frontend
npm install
```

## Running the App

```bash
# Start the frontend dev server
cd frontend
npm run dev
```

Open `http://localhost:5173` in a browser to see the copper background.

## Implementation Steps

This feature requires changes to **one file only**: `frontend/src/index.css`.

### Step 1: Update Light Mode Tokens

In `frontend/src/index.css`, update the `:root` block:

```css
:root {
  --color-primary: #0969da;         /* unchanged */
  --color-secondary: #6e7781;       /* unchanged */
  --color-success: #1a7f37;         /* unchanged */
  --color-warning: #9a6700;         /* unchanged */
  --color-danger: #cf222e;          /* unchanged */
  --color-bg: #B87333;              /* ← copper primary */
  --color-bg-secondary: #CB6D51;    /* ← copper secondary */
  --color-border: #9A5C2E;          /* ← copper border */
  --color-text: #1A1A1A;            /* ← near-black for contrast */
  --color-text-secondary: #2D1810;  /* ← dark brown for secondary text */
  --radius: 6px;                    /* unchanged */
  --shadow: 0 1px 3px rgba(139, 90, 43, 0.2); /* ← copper-tinted shadow */
}
```

### Step 2: Update Dark Mode Tokens

In the same file, update the `html.dark-mode-active` block:

```css
html.dark-mode-active {
  --color-primary: #539bf5;         /* unchanged */
  --color-secondary: #8b949e;       /* unchanged */
  --color-success: #3fb950;         /* unchanged */
  --color-warning: #d29922;         /* unchanged */
  --color-danger: #f85149;          /* unchanged */
  --color-bg: #8C4A2F;              /* ← dark copper primary */
  --color-bg-secondary: #6B3A24;    /* ← deep copper secondary */
  --color-border: #5A2E1A;          /* ← deep copper border */
  --color-text: #FFFFFF;             /* ← white text for contrast */
  --color-text-secondary: #E8D5CC;  /* ← warm light secondary text */
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.5); /* ← deeper shadow */
}
```

### Step 3: Visual Audit

After making changes:

1. **Light mode check**: Navigate to every page and verify copper background is visible
2. **Dark mode check**: Toggle dark mode via the theme switch and verify dark copper variant
3. **Contrast check**: Verify all text is readable against the copper background
4. **Component check**: Open modals, drawers, and sidebars to verify copper harmonization
5. **Responsive check**: Test on mobile, tablet, and desktop viewport sizes

## Verification Workflow

### 1. Visual Verification
```bash
# Start dev server
cd frontend && npm run dev

# Open browser, navigate through all pages
# Toggle dark mode
# Open modals, sidebars, and drawers
```

### 2. Accessibility Audit
```bash
# Use browser DevTools → Lighthouse → Accessibility
# Or install axe-core browser extension
# Verify no contrast violations reported
```

### 3. Existing Tests (Regression)
```bash
# Frontend unit tests
cd frontend && npm test

# Frontend e2e tests (if applicable)
cd frontend && npx playwright test
```

### 4. Lint Check
```bash
cd frontend && npm run lint
```

## Common Pitfalls

- **Contrast failures**: If any text becomes unreadable, check that `--color-text` and `--color-text-secondary` provide sufficient contrast against the copper backgrounds. Use a contrast checker tool (e.g., WebAIM Contrast Checker).
- **Hardcoded colors**: Some components in `App.css` use hardcoded colors (e.g., `#2da44e` for status indicators). These are intentional semantic colors and should NOT be changed to copper.
- **Browser caching**: If changes don't appear, hard-refresh the browser (Ctrl+Shift+R) to clear the CSS cache.
- **Third-party components**: If any third-party component doesn't inherit the copper background, wrap it with a styled container or override its background in component-specific CSS.
