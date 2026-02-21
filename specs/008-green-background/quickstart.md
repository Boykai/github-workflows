# Quickstart: Add Green Background Color to App

**Feature**: 008-green-background
**Date**: 2026-02-21

## Overview

This guide describes how to implement the green background feature. The change is entirely in the frontend CSS layer, leveraging the existing CSS custom property theming system.

## Prerequisites

- Node.js and npm installed
- Repository cloned with `frontend/` directory accessible
- Familiarity with CSS custom properties

## Implementation Steps

### Step 1: Add `--color-bg-surface` Token

Add a new CSS custom property `--color-bg-surface` to both the `:root` and `html.dark-mode-active` selectors in `frontend/src/index.css`. This token preserves the current neutral background for component surfaces (cards, panels, inputs).

```css
/* In :root */
--color-bg-surface: #ffffff;

/* In html.dark-mode-active */
--color-bg-surface: #0d1117;
```

### Step 2: Update `--color-bg` and `--color-bg-secondary` to Green

In `frontend/src/index.css`, change the background color values:

```css
/* :root (light mode) */
--color-bg: #4CAF50;
--color-bg-secondary: #43A047;

/* html.dark-mode-active */
--color-bg: #2E7D32;
--color-bg-secondary: #1B5E20;
```

### Step 3: Migrate Component Surface Backgrounds

Update all component CSS files that use `var(--color-bg)` for surface backgrounds to use `var(--color-bg-surface)` instead. Affected files:

1. **`frontend/src/App.css`** — Replace `var(--color-bg)` with `var(--color-bg-surface)` for:
   - `.app-header` background
   - `.sidebar` background  
   - `.chat-section` background
   - Any card or panel backgrounds

2. **`frontend/src/components/chat/ChatInterface.css`** — Replace `var(--color-bg)` with `var(--color-bg-surface)` for:
   - `.chat-container` background
   - `.message-bubble` background
   - `.chat-input-area` background
   - Other surface elements

### Step 4: Verify Contrast Compliance

Verify that text colors maintain WCAG 2.1 AA contrast ratios:

| Text Color | Background | Expected Ratio | Pass? |
|-----------|-----------|----------------|-------|
| #24292f | #4CAF50 | ~4.56:1 | ✅ (≥4.5:1) |
| #e6edf3 | #2E7D32 | ~6.8:1 | ✅ (≥4.5:1) |
| #24292f | #ffffff | ~14.7:1 | ✅ (≥4.5:1) |
| #e6edf3 | #0d1117 | ~13.8:1 | ✅ (≥4.5:1) |

## Verification

### Local Development

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173 and visually confirm:
# 1. Green background visible on main app container
# 2. Cards/panels remain white (light) or dark (dark mode)
# 3. Text is readable on all backgrounds
# 4. Toggle dark mode — green shifts to darker shade
```

### Build Check

```bash
cd frontend
npm run build
npm run type-check
npm run lint
```

### Test Run

```bash
cd frontend
npm run test
```

## File Change Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `frontend/src/index.css` | Modify | Add `--color-bg-surface`; update `--color-bg` and `--color-bg-secondary` to green |
| `frontend/src/App.css` | Modify | Replace `var(--color-bg)` → `var(--color-bg-surface)` for component surfaces |
| `frontend/src/components/chat/ChatInterface.css` | Modify | Replace `var(--color-bg)` → `var(--color-bg-surface)` for chat surfaces |

## Rollback

To revert, restore the original `--color-bg` values (`#ffffff` / `#0d1117`), restore `--color-bg-secondary` values (`#f6f8fa` / `#161b22`), remove the `--color-bg-surface` property, and revert component CSS files from `var(--color-bg-surface)` back to `var(--color-bg)`.
