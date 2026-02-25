# Quickstart: Add Red Background Color to Application

**Feature**: `011-red-background` | **Date**: 2026-02-25

## Prerequisites

- Node.js 18+ (`node --version`)
- npm (`npm --version`)

## Environment Setup

```bash
# Clone and switch to feature branch
git checkout 011-red-background

# Frontend
cd frontend
npm install
```

## Build & Verify

### Frontend

```bash
cd frontend

# Build (catches any CSS/TypeScript errors)
npm run build

# Unit tests
npm run test -- --run

# Start dev server for visual verification
npm run dev
```

### Visual Verification

After starting the dev server:

1. Open `http://localhost:5173` in a browser
2. **Light mode**: Confirm the page background is visibly red (`#DC2626`)
3. **Dark mode**: Toggle dark mode and confirm a deep dark red background (`#7F1D1D`)
4. **Navigate**: Visit multiple pages/routes — background should be consistently red
5. **Responsive**: Resize the browser from mobile (320px) to desktop (1920px+) — background fills the entire viewport
6. **Text readability**: All text, buttons, links, and cards should be clearly readable

### Contrast Check

```bash
# Install a contrast checker (optional, for automated verification)
npx color-contrast-checker "#FFFFFF" "#DC2626"
# Expected: ratio >= 4.5:1 (WCAG AA pass)

npx color-contrast-checker "#e6edf3" "#7F1D1D"
# Expected: ratio >= 4.5:1 (WCAG AA pass)
```

### Full Stack (Docker)

```bash
# From repo root
docker compose build
docker compose up -d

# Visual check at http://localhost:3000 (or configured port)
# Tear down
docker compose down
```

## Verification Checklist

| Check | How | Expected |
|-------|-----|----------|
| Red background (light mode) | Open app in browser | Red background visible on all pages |
| Red background (dark mode) | Toggle dark mode | Deep dark red background visible |
| Text readable (light) | Read body text | White text on red — clear and legible |
| Text readable (dark) | Read body text in dark mode | Light text on dark red — clear and legible |
| Responsive | Resize browser 320px → 2560px | Red fills entire viewport |
| Components intact | Navigate all pages | Buttons, cards, modals, forms all visible and usable |
| Frontend builds | `cd frontend && npm run build` | Exit 0, no errors |
| Frontend tests pass | `cd frontend && npm run test -- --run` | All green |
| Single token change | Edit `--color-bg` value in index.css | Background updates globally on reload |
