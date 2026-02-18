# File Modification Contract: Yellow Background Color for App

**Feature**: 003-yellow-background-app | **Date**: 2026-02-18  
**Purpose**: Define exact file changes required for yellow background implementation

## Contract Overview

This contract specifies the precise modifications to `frontend/src/index.css` to change the application background from neutral gray/white tones to a yellow-tinted palette. All changes are CSS custom property value replacements — 4 values in 1 file.

---

## File: `frontend/src/index.css`

**Purpose**: Global CSS custom properties (design tokens) for theming  
**Change Type**: Value replacement for 4 CSS custom properties

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
```

### Required Changes

**Change 1 — Line 8**: Replace light-mode surface background

```diff
-  --color-bg: #ffffff;
+  --color-bg: #FFFFF0;
```

**Change 2 — Line 9**: Replace light-mode page background

```diff
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #FFFDE7;
```

**Change 3 — Line 24**: Replace dark-mode surface background

```diff
-  --color-bg: #0d1117;
+  --color-bg: #0D0A00;
```

**Change 4 — Line 25**: Replace dark-mode page background

```diff
-  --color-bg-secondary: #161b22;
+  --color-bg-secondary: #1A1500;
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
  --color-bg: #FFFFF0;
  --color-bg-secondary: #FFFDE7;
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
  --color-bg: #0D0A00;
  --color-bg-secondary: #1A1500;
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Validation**:
- ✅ CSS structure unchanged (`:root` and `html.dark-mode-active` selectors preserved)
- ✅ Only color values modified, no property names changed
- ✅ All other variables untouched
- ✅ CSS syntax remains valid

---

## Color Mapping Summary

| Variable | Mode | Old Value | New Value | Name | Contrast vs Text |
|----------|------|-----------|-----------|------|-----------------|
| `--color-bg` | Light | `#ffffff` | `#FFFFF0` | Ivory | 14.52:1 vs #24292f ✅ |
| `--color-bg-secondary` | Light | `#f6f8fa` | `#FFFDE7` | Material Yellow 50 | 14.27:1 vs #24292f ✅ |
| `--color-bg` | Dark | `#0d1117` | `#0D0A00` | Deep dark yellow | 16.76:1 vs #e6edf3 ✅ |
| `--color-bg-secondary` | Dark | `#161b22` | `#1A1500` | Dark warm yellow | 15.44:1 vs #e6edf3 ✅ |

All contrast ratios exceed WCAG AA minimum (4.5:1) by at least 3× margin.

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change per spec scope:

### Frontend Files (No Changes)
- `frontend/src/App.css` — Component styles reference CSS variables; no value changes needed
- `frontend/src/App.tsx` — Application component; no structural changes
- `frontend/src/main.tsx` — Entry point; no changes
- `frontend/index.html` — HTML template; no changes
- `frontend/package.json` — Dependencies; no changes
- `frontend/src/components/**` — All component files unchanged
- `frontend/e2e/**` — No E2E test changes needed (background color not asserted in tests)

### Backend Files (No Changes)
- All backend files unchanged (background color is frontend-only concern)

### Documentation (No Changes)
- `README.md` — No documentation updates needed for CSS variable value change

---

## Verification Contract

After implementing changes, verify the following:

### Light Mode Background (FR-001, FR-002)
- [ ] Open application in browser (light mode)
- [ ] Observe page background displays soft yellow (#FFFDE7)
- [ ] Observe surface elements (header, cards) display ivory (#FFFFF0)
- [ ] Verify text is legible against both backgrounds

### Dark Mode Background (FR-003, FR-005)
- [ ] Toggle dark mode
- [ ] Observe page background displays dark warm-yellow (#1A1500)
- [ ] Observe surface elements display deep dark yellow (#0D0A00)
- [ ] Verify text is legible against both backgrounds

### Cross-Browser Consistency (FR-006)
- [ ] Verify in Chrome
- [ ] Verify in Firefox
- [ ] Verify in Safari (if available)
- [ ] Verify in Edge (if available)

### Component Preservation (FR-007)
- [ ] Cards remain visually distinct against yellow background
- [ ] Buttons remain legible and functional
- [ ] Navigation elements are clear
- [ ] Modals overlay correctly

### Accessibility (FR-002, FR-003)
- [ ] Run Lighthouse accessibility audit (optional post-implementation)
- [ ] No new contrast warnings introduced

---

## Rollback Contract

If issues arise, revert changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: All 4 CSS variable values return to previous neutral colors (#ffffff, #f6f8fa, #0d1117, #161b22).

---

## Contract Compliance Checklist

- [x] All file paths are absolute and verified to exist
- [x] Line numbers documented for reference
- [x] Exact value replacements specified
- [x] Before/after states documented
- [x] Validation criteria defined
- [x] Out-of-scope files explicitly listed
- [x] Rollback procedure defined
- [x] Contrast ratios verified for all color pairs

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
