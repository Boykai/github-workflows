# Quickstart: Purple Background Color Implementation Guide

**Date**: 2026-02-27 | **Branch**: `012-purple-background`

## Prerequisites

- Node.js 20+
- Clone and checkout: `git checkout 012-purple-background`
- Install frontend dependencies: `cd frontend && npm install`

## Environment Variables

No new environment variables required. This is a frontend-only CSS change.

## Running Locally

```bash
cd frontend && npm run dev
# Frontend: http://localhost:5173
```

For full-stack (to verify all pages):
```bash
docker compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Implementation Order

This is a single-file change. Work through these steps sequentially.

### Step 1 — Update Light Mode CSS Custom Properties

**File**: `frontend/src/index.css`

Update all CSS custom property values inside the `:root` selector to use purple-family HSL values:
- `--background: 270 50% 40%` (purple primary surface)
- `--foreground: 210 40% 98%` (light text)
- All related tokens (`--card`, `--popover`, `--primary`, `--secondary`, `--muted`, `--accent`, `--border`, `--input`, `--ring`) updated to purple-family values per the CSS Token Contract.

**Verify**: Open `http://localhost:5173` in a browser. The entire page background should be purple. All text should be readable (light text on purple background). Cards, buttons, and inputs should have visible boundaries.

### Step 2 — Update Dark Mode CSS Custom Properties

**File**: `frontend/src/index.css`

Update all CSS custom property values inside the `.dark` selector to use deep purple-family HSL values:
- `--background: 270 50% 20%` (deep purple)
- All related tokens updated to darker purple-family values per the CSS Token Contract.

**Verify**: Toggle to dark mode using the theme button in the header. The background should shift to a deeper purple. Text should remain readable. Toggle back to light mode — the transition should be smooth with no flash of non-purple color.

### Step 3 — Visual Audit of Secondary Surfaces

After updating both mode blocks, audit all secondary surfaces:
- Cards and popovers: should be a slightly lighter purple than the background
- Buttons: default buttons should be light-colored (inverted contrast), outline buttons should have visible borders
- Inputs: should have visible borders against the purple background
- Header: should blend with or complement the purple background
- Board columns, settings page, and any modals/drawers

**Verify**: Navigate through all pages (Home, Project Board, Settings). Interact with all UI elements. No component should have illegible text or invisible boundaries.

### Step 4 — WCAG Contrast Verification

Use a WCAG contrast checker tool (e.g., WebAIM Contrast Checker, browser DevTools accessibility audit) to verify:
- Primary text (foreground) against background: ≥ 4.5:1
- Card text against card background: ≥ 4.5:1
- Button text against button background: ≥ 4.5:1
- Muted text against background: ≥ 4.5:1

**Verify**: All text/surface combinations meet WCAG AA minimum 4.5:1 contrast ratio.

### Step 5 — Cross-Browser Verification

Open the application in each major browser and confirm the purple background renders correctly:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**Verify**: Purple color appears identical across all browsers. No rendering differences.

### Step 6 — Build & Test

```bash
# Type checking
cd frontend && npm run type-check

# Linting
cd frontend && npm run lint

# Unit tests
cd frontend && npm run test

# Build
cd frontend && npm run build
```

**Verify**: All commands pass with zero errors.

## Key Testing Commands

```bash
# Type checking
cd frontend && npm run type-check

# Linting
cd frontend && npm run lint

# Unit tests
cd frontend && npm run test

# Build
cd frontend && npm run build
```

## Verification Checklist

- [ ] Light mode: Background is purple on all pages
- [ ] Dark mode: Background is deep purple on all pages
- [ ] Light/dark mode toggle transitions smoothly
- [ ] All text is readable against purple background (both modes)
- [ ] WCAG AA contrast ratio ≥ 4.5:1 for all text/surface combinations
- [ ] Cards and popovers are visually distinct from background
- [ ] Buttons (all variants) are visible and clickable
- [ ] Input fields have visible borders
- [ ] Header is visually coherent with purple background
- [ ] Board columns are readable
- [ ] No existing components have visual regressions
- [ ] Chrome renders correctly
- [ ] Firefox renders correctly
- [ ] Safari renders correctly
- [ ] Edge renders correctly
- [ ] `npm run type-check` passes
- [ ] `npm run lint` passes
- [ ] `npm run test` passes
- [ ] `npm run build` succeeds
