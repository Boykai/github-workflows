# File Modification Contract: Add Yellow Background Color

**Feature**: 008-add-yellow-background | **Date**: 2026-02-20
**Purpose**: Define exact file changes required for yellow background implementation

## Contract Overview

This contract specifies the single CSS modification required to apply a yellow background color globally in light mode. The change involves updating one CSS custom property value in the global stylesheet.

---

## File: `frontend/src/index.css`

**Purpose**: Global stylesheet defining CSS custom properties and base styles
**Change Type**: CSS variable value update in `:root` selector

### Current State (`:root` selector)

```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

### Required Change

**Line ~7**: Update `--color-bg-secondary` value from `#f6f8fa` to `#FFFDE7`

```diff
 :root {
   --color-primary: #0969da;
   --color-secondary: #6e7781;
   --color-success: #1a7f37;
   --color-warning: #9a6700;
   --color-danger: #cf222e;
   --color-bg: #ffffff;
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #FFFDE7;
   --color-border: #d0d7de;
   --color-text: #24292f;
   --color-text-secondary: #57606a;
   --radius: 6px;
   --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
 }
```

### Expected New State (`:root` selector)

```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #FFFDE7;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

### Dark Mode (NO CHANGES)

The dark mode selector remains unchanged:

```css
/* Dark theme overrides — NO CHANGES */
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #161b22;
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

---

## Files NOT Modified

| File | Reason |
|------|--------|
| `frontend/src/App.css` | No background overrides to update |
| `frontend/src/App.tsx` | No inline styles to change |
| `frontend/index.html` | No body styles defined here |
| `backend/*` | Backend is unaffected by CSS changes |
| `frontend/e2e/*` | E2E tests do not assert background colors |

---

## Verification Commands

```bash
# Verify the change was applied
grep "color-bg-secondary" frontend/src/index.css

# Expected output:
#   --color-bg-secondary: #FFFDE7;       (in :root)
#   --color-bg-secondary: #161b22;       (in dark mode — unchanged)

# Verify no other files reference the old value
grep -r "#f6f8fa" frontend/src/

# Expected: No matches (old value fully replaced)
```

## Impact Summary

| Area | Impact |
|------|--------|
| Global page background | Changes from light gray to soft yellow |
| Board columns, status sections | Secondary backgrounds become yellow-tinted |
| Cards, modals, headers | Unchanged (use `--color-bg: #ffffff`) |
| Dark mode | Unchanged |
| Text contrast | Maintained (17.6:1 for primary text) |
| File count | 1 file modified |
| Line count | 1 line changed |
