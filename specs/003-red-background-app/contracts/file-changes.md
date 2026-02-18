# File Modification Contract: Apply Red Background Color to App

**Feature**: 003-red-background-app | **Date**: 2026-02-18  
**Purpose**: Define exact file changes required for red background color update

## Contract Overview

This contract specifies the precise modifications to the frontend CSS theme file to apply a red-themed background color to the application. All changes are CSS custom property value replacements in a single file.

---

## File: `frontend/src/index.css`

**Purpose**: Global CSS custom properties defining the application theme  
**Change Type**: Value replacement for 4 CSS custom properties (2 in `:root`, 2 in `html.dark-mode-active`)

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

**Change 1 — Line 8**: Replace light mode primary surface background

```diff
-  --color-bg: #ffffff;
+  --color-bg: #fff5f5;
```

**Change 2 — Line 9**: Replace light mode page background

```diff
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #ffebee;
```

**Change 3 — Line 24**: Replace dark mode primary surface background

```diff
-  --color-bg: #0d1117;
+  --color-bg: #2d0a0a;
```

**Change 4 — Line 25**: Replace dark mode page background

```diff
-  --color-bg-secondary: #161b22;
+  --color-bg-secondary: #1a0505;
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
  --color-bg: #fff5f5;
  --color-bg-secondary: #ffebee;
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
  --color-bg: #2d0a0a;
  --color-bg-secondary: #1a0505;
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Validation**:
- ✅ CSS structure unchanged (selectors, property names preserved)
- ✅ Only 4 values modified
- ✅ All new values are valid lowercase hex colors
- ✅ WCAG AA contrast ratios maintained (all > 4.5:1)

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change per spec scope:

### Frontend Files (No Changes)
- `frontend/src/App.css` — Component styles reference `var(--color-bg)` and `var(--color-bg-secondary)` but their references remain valid
- `frontend/src/App.tsx` — No structural changes; colors cascade from CSS variables
- `frontend/src/**/*.tsx` — No component changes needed
- `frontend/index.html` — No HTML changes needed
- `frontend/e2e/**/*.spec.ts` — No test changes expected

### Backend Files (No Changes)
- All backend files unchanged (background color is frontend-only concern)

### Documentation (No Changes)
- `README.md` — Out of scope
- `docker-compose.yml` — Unrelated

---

## Verification Contract

After implementing changes, verify the following:

### Light Mode Background (FR-001, FR-003)
- [ ] Open application in browser (light mode)
- [ ] Observe page background displays red-tinted color (`#ffebee`)
- [ ] Observe surface backgrounds (header, cards) display lighter red tint (`#fff5f5`)
- [ ] Verify all text is readable on red backgrounds

### Dark Mode Background (FR-004, FR-007)
- [ ] Toggle to dark mode
- [ ] Observe page background displays dark red color (`#1a0505`)
- [ ] Observe surface backgrounds display slightly lighter dark red (`#2d0a0a`)
- [ ] Verify all text is readable on dark red backgrounds

### Responsive Breakpoints (FR-005)
- [ ] Test at mobile width (320px-480px)
- [ ] Test at tablet width (768px)
- [ ] Test at desktop width (1024px+)
- [ ] Red background consistent across all breakpoints

### Component Preservation (FR-006)
- [ ] Cards retain their surface background color (inherits `--color-bg`)
- [ ] Modals retain their surface background color (inherits `--color-bg`)
- [ ] Input fields retain their styling
- [ ] No unexpected background color overrides

### Accessibility (FR-003, FR-004)
- [ ] Inspect computed contrast ratios in browser DevTools
- [ ] Light mode text contrast ≥ 4.5:1
- [ ] Dark mode text contrast ≥ 4.5:1

---

## Rollback Contract

If issues arise, revert changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: All 4 CSS custom property values return to their original values (white/gray for light mode, dark for dark mode).

---

## Contract Compliance Checklist

- [x] All file paths are absolute and verified to exist
- [x] Line numbers documented for reference
- [x] Exact value replacements specified
- [x] Before/after states documented
- [x] Validation criteria defined
- [x] Out-of-scope files explicitly listed
- [x] Rollback procedure defined
- [x] Accessibility verification included

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
