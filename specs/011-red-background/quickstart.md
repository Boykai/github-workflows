# Quickstart: Add Red Background Color Implementation Guide

**Date**: 2026-02-26 | **Branch**: `011-red-background`

## Prerequisites

- Node.js 18+
- Clone and checkout: `git checkout 011-red-background`

## Running Locally

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

## Environment Variables (New / Changed)

None — this feature requires no new environment variables.

## Implementation Order

This is an XS-sized change. All modifications happen in a single file. The implementation is a single phase.

### Phase A — CSS Token Update (Single File Change)

1. **`frontend/src/index.css`** — Update `:root` design tokens:
   - Change `--color-bg-secondary` from `#f6f8fa` to `#E53E3E`
   - Change `--color-text` from `#24292f` to `#FFFFFF`
   - Keep `--color-bg` as `#ffffff` (components use this for their own backgrounds)

2. **`frontend/src/index.css`** — Update `html.dark-mode-active` tokens:
   - Change `--color-bg-secondary` from `#161b22` to `#9B2C2C`
   - Change `--color-text` from `#e6edf3` to `#FFFFFF`
   - Keep `--color-bg` as `#0d1117` (components use this for their own backgrounds)

3. **`frontend/src/index.css`** — Add fallback to body background:
   - Change `background: var(--color-bg-secondary)` to `background: var(--color-bg-secondary, #E53E3E)`

**Test**: Open the app in a browser. Verify:
- Red background visible on all pages
- Text is white and readable (4.5:1 contrast)
- Toggle dark mode — background changes to darker red (#9B2C2C)
- Components (cards, modals, sidebar) retain their own backgrounds and remain legible
- Resize browser window — red background fills viewport at all sizes

### Phase B — Visual Verification (Manual)

4. **Cross-browser check**: Open in Chrome, Firefox, Safari, Edge — confirm identical red background.
5. **Responsive check**: Test at mobile (≤480px), tablet (481–1024px), and desktop (≥1025px) widths.
6. **Accessibility audit**: Run browser DevTools accessibility checker or Lighthouse to confirm contrast ratios.
7. **Component review**: Navigate through all views (board, chat, settings, login) and verify overlaid components remain legible.

## Verification Commands

```bash
# Run frontend unit tests (should still pass — no logic changes)
cd frontend && npm test

# Run E2E tests (if configured — visual assertions may need snapshot updates)
cd frontend && npx playwright test
```

## Rollback

To revert: restore the original token values in `frontend/src/index.css`:
- `:root { --color-bg-secondary: #f6f8fa; --color-text: #24292f; }`
- `html.dark-mode-active { --color-bg-secondary: #161b22; --color-text: #e6edf3; }`
- `body { background: var(--color-bg-secondary); }`
