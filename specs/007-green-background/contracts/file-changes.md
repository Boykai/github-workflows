# File Modification Contract: Add Green Background Color

**Feature**: 007-green-background | **Date**: 2026-02-20
**Purpose**: Define exact file changes required for green background implementation

## Contract Overview

This contract specifies the precise modification to the global stylesheet to add a green background color to the application. All changes are confined to a single CSS file (`frontend/src/index.css`), adding a new CSS custom property and updating the body background declaration.

---

## File: `frontend/src/index.css`

**Purpose**: Global CSS — defines design tokens (CSS custom properties) and base element styles
**Change Type**: Add new CSS custom property; modify body background declaration

### Current State

```css
/* Base styles */
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

/* Dark theme overrides */
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

/* ... */

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg-secondary);
}
```

### Required Changes

**Change 1 — `:root` block**: Add `--color-bg-primary` custom property after `--color-bg-secondary`

```diff
   --color-bg: #ffffff;
   --color-bg-secondary: #f6f8fa;
+  --color-bg-primary: #2D6A4F;
   --color-border: #d0d7de;
```

**Change 2 — `html.dark-mode-active` block**: Add `--color-bg-primary` custom property after `--color-bg-secondary`

```diff
   --color-bg: #0d1117;
   --color-bg-secondary: #161b22;
+  --color-bg-primary: #2D6A4F;
   --color-border: #30363d;
```

**Change 3 — `body` rule**: Update background to use `--color-bg-primary` with hardcoded fallback

```diff
 body {
   font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
   font-size: 14px;
   line-height: 1.5;
   color: var(--color-text);
-  background: var(--color-bg-secondary);
+  background: #2D6A4F;
+  background: var(--color-bg-primary);
 }
```

### Expected New State

```css
/* Base styles */
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;
  --color-bg-primary: #2D6A4F;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Dark theme overrides */
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #161b22;
  --color-bg-primary: #2D6A4F;
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

/* ... */

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  background: #2D6A4F;
  background: var(--color-bg-primary);
}
```

**Validation**:
- ✅ CSS custom property naming follows existing convention (`--color-bg-*`)
- ✅ Property placement is consistent (after `--color-bg-secondary` in both blocks)
- ✅ Hardcoded fallback precedes `var()` declaration (standard CSS fallback pattern)
- ✅ Both light and dark mode blocks define the variable
- ✅ No other CSS rules or files modified

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change per spec scope:

### Frontend Files (No Changes)
- `frontend/src/App.css` — Component-level styles unchanged; components retain own backgrounds
- `frontend/src/App.tsx` — No React component changes
- `frontend/src/main.tsx` — No entry point changes
- `frontend/index.html` — No HTML changes
- `frontend/package.json` — No dependency changes

### Backend Files (No Changes)
- All backend files unchanged (background color is a frontend-only concern)

### Test Files (No Changes)
- No test assertions affected by CSS background color

---

## Verification Contract

After implementing changes, verify the following:

### Green Background Visible (FR-001, SC-001)
- [ ] Open application in browser
- [ ] Observe green background color visible as base layer
- [ ] Navigate between pages — green remains consistent

### CSS Variable Defined (FR-002, SC-006)
- [ ] Inspect `:root` in browser DevTools — `--color-bg-primary: #2D6A4F` present
- [ ] Change variable value in DevTools — background updates (confirms variable is active)

### UI Components Readable (FR-006)
- [ ] Text on cards, headers, sidebar remains legible
- [ ] Buttons, inputs, navigation remain functional and visually compatible

### Responsive (FR-005, SC-003)
- [ ] Resize browser to mobile width — green fills viewport without gaps
- [ ] Resize to tablet/desktop — no overflow artifacts

### Dark Mode (FR-004)
- [ ] Toggle dark mode — green background persists
- [ ] Components still readable in dark mode

### Fallback (FR-007)
- [ ] Verify two `background` declarations exist in body rule (fallback pattern)

---

## Rollback Contract

If issues arise, revert changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: `body` background returns to `var(--color-bg-secondary)` (light grey) and `--color-bg-primary` variable is removed.

---

## Contract Compliance Checklist

- [x] All file paths verified to exist
- [x] Exact CSS changes specified with diffs
- [x] Before/after states documented
- [x] Validation criteria defined
- [x] Out-of-scope files explicitly listed
- [x] Rollback procedure defined
- [x] Verification checklist aligned with spec requirements

**Status**: ✅ **CONTRACT COMPLETE** — Ready for implementation
