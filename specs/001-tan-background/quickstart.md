# Quickstart: Apply Tan Background Color to App

**Feature**: 001-tan-background  
**Date**: 2026-02-20  
**Estimated effort**: ~30 minutes

## Prerequisites

- Node.js and npm installed
- Repository cloned and on the `001-tan-background` branch
- `cd frontend && npm install` completed

## Implementation Steps

### Step 1: Update Light Mode CSS Tokens

**File**: `frontend/src/index.css`

In the `:root` selector, update the following custom properties:

```css
/* Before */
--color-bg-secondary: #f6f8fa;
--color-text-secondary: #57606a;

/* After */
--color-bg-secondary: #D2B48C;
--color-text-secondary: #3D4451;
```

**Why**: `--color-bg-secondary` is used by the `body` element as its background color. Changing it to `#D2B48C` applies the tan background globally. `--color-text-secondary` is darkened from `#57606a` to `#3D4451` to maintain WCAG AA contrast (≥ 4.5:1) against the new tan background.

### Step 2: Update Dark Mode CSS Tokens

**File**: `frontend/src/index.css`

In the `html.dark-mode-active` selector, update:

```css
/* Before */
--color-bg-secondary: #161b22;

/* After */
--color-bg-secondary: #2C1E12;
```

**Why**: Maps the tan design token to a warm dark-brown equivalent for dark mode, preserving the tan color family while maintaining WCAG AA contrast with dark-mode text colors.

### Step 3: Visual Verification

1. Start the dev server:
   ```bash
   cd frontend && npm run dev
   ```

2. Verify in browser:
   - **Light mode**: All pages show tan (#D2B48C) background
   - **Dark mode**: Toggle via theme button → background shows dark warm brown (#2C1E12)
   - **Components**: Cards, modals, sidebars should appear white/light against tan (visually distinct)
   - **Text**: All text remains readable — no washed-out or low-contrast text

3. Check responsive breakpoints:
   - Resize browser to mobile, tablet, desktop widths
   - Confirm tan background persists at all sizes

### Step 4: Accessibility Audit

Run a contrast check to confirm no WCAG AA violations:

```bash
# After starting dev server, open browser DevTools:
# - Lighthouse → Accessibility audit
# - Or use axe DevTools extension
# Verify: 0 new contrast violations
```

**Expected contrast ratios on tan (#D2B48C)**:
| Text Token | Color | Contrast | Status |
|-----------|-------|---------|--------|
| `--color-text` | #24292f | 7.43:1 | ✅ Pass |
| `--color-text-secondary` | #3D4451 | 4.97:1 | ✅ Pass |

**Expected contrast ratios on dark-tan (#2C1E12)**:
| Text Token | Color | Contrast | Status |
|-----------|-------|---------|--------|
| `--color-text` (dark) | #e6edf3 | 13.65:1 | ✅ Pass |
| `--color-text-secondary` (dark) | #8b949e | 5.25:1 | ✅ Pass |

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/index.css` | Update `--color-bg-secondary` and `--color-text-secondary` CSS custom properties in `:root` and `html.dark-mode-active` |

## Rollback

To revert, restore the original values in `frontend/src/index.css`:

```css
:root {
  --color-bg-secondary: #f6f8fa;
  --color-text-secondary: #57606a;
}

html.dark-mode-active {
  --color-bg-secondary: #161b22;
}
```
