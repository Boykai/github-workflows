# File Changes Contract: Add Teal Background Color to App

**Feature**: 007-teal-background | **Date**: 2026-02-19

---

## Overview

This feature requires changes to exactly **one file**: `frontend/src/index.css`. No API endpoints, backend models, or new components are created.

---

## File: `frontend/src/index.css`

### Change 1: Add `--color-bg-app` to `:root`

**Location**: `:root` block (line ~2-15)

**Before**:
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

**After**:
```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;
  --color-bg-app: #0D9488;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

### Change 2: Add `--color-bg-app` to dark mode overrides

**Location**: `html.dark-mode-active` block (line ~18-30)

**Add** to the existing dark mode overrides:
```css
  --color-bg-app: #0F766E;
```

### Change 3: Update `body` background

**Location**: `body` rule (line ~38-44)

**Before**:
```css
body {
  /* ... */
  background: var(--color-bg-secondary);
}
```

**After**:
```css
body {
  /* ... */
  background: var(--color-bg-app);
}
```

---

## Summary

| File | Type | Lines Changed |
|------|------|--------------|
| `frontend/src/index.css` | Modified | +3 lines (1 new token in :root, 1 new token in dark mode, 1 body background value change) |

**Total files changed**: 1
**Total lines added**: 2
**Total lines modified**: 1
