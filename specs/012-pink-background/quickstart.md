# Quickstart: Pink Background Color Implementation Guide

**Date**: 2026-02-27 | **Branch**: `012-pink-background`

## Prerequisites

- Node.js 20+
- Clone and checkout: `git checkout 012-pink-background`
- Install frontend dependencies: `cd frontend && npm install`

## Environment Variables

No new environment variables required. This is a frontend-only CSS change.

## Running Locally

```bash
cd frontend && npm run dev
# Frontend: http://localhost:5173
```

For full-stack:
```bash
docker compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Implementation Order

This is a single-step change. Only one file is modified.

### Step 1 — Update CSS Custom Property Values

**File**: `frontend/src/index.css`

1. In the `:root` selector (light mode), change `--background` from `0 0% 100%` to `350 100% 88%`.
2. In the `.dark` selector (dark mode), change `--background` from `222.2 84% 4.9%` to `350 30% 12%`.

**Verify**: Open the app in a browser. The background should be pink. Toggle dark mode — the background should be a dark muted pink.

### Step 2 — Validate

1. Check contrast: use browser DevTools or an accessibility checker to confirm text contrast ratio ≥ 4.5:1 against the pink background.
2. Navigate through all pages/routes to confirm pink background is consistent everywhere.
3. Test in Chrome, Firefox, Safari, and Edge.
4. Test on mobile viewport sizes (320px, 375px, 768px).
5. Verify component backgrounds (cards, modals, popovers) are unchanged.

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

# E2E tests (requires backend)
cd frontend && npm run test:e2e
```

## Verification Checklist

- [ ] Light mode background is pink (#FFC0CB / `350 100% 88%`)
- [ ] Dark mode background is dark muted pink (#281519 / `350 30% 12%`)
- [ ] All text is readable (contrast ratio ≥ 4.5:1) in both modes
- [ ] Pink background is consistent across all pages and routes
- [ ] Component backgrounds (cards, popovers, modals) are unchanged
- [ ] No UI layout, spacing, or component style breakage
- [ ] Pink background covers full scrollable area, not just viewport
- [ ] Cross-browser rendering is consistent (Chrome, Firefox, Safari, Edge)
- [ ] Mobile viewport rendering is correct (320px–1920px)
- [ ] `npm run type-check` passes
- [ ] `npm run lint` passes
- [ ] `npm run test` passes
- [ ] `npm run build` succeeds
