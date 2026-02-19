# File Modification Contract: Pink Background Color

**Feature**: 005-pink-background | **Date**: 2026-02-19  
**Purpose**: Define exact file changes required for pink background implementation

## Contract Overview

This contract specifies the precise modifications to apply a pink background color globally across the application. All changes are CSS custom property value updates in a single file (`frontend/src/index.css`).

---

## File: `frontend/src/index.css`

**Purpose**: Global stylesheet containing CSS custom properties (design tokens) and base styles  
**Change Type**: CSS custom property value updates (2 values in 2 selectors)

### Current State (Relevant Sections)

**Light Theme (`:root`, Lines 1-15)**:
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

**Dark Theme (`html.dark-mode-active`, Lines 17-30)**:
```css
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

**Change 1 - Line 9**: Update light mode page background color

```diff
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #FFC0CB;
```

**Change 2 - Line 25**: Update dark mode page background color

```diff
-  --color-bg-secondary: #161b22;
+  --color-bg-secondary: #3D2027;
```

### Expected New State (Relevant Sections)

**Light Theme (`:root`)**:
```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #FFC0CB;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

**Dark Theme (`html.dark-mode-active`)**:
```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #3D2027;
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Validation**:
- ✅ CSS variable names unchanged
- ✅ Only hex color values modified
- ✅ CSS syntax remains valid
- ✅ Variable cascade behavior preserved

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change per spec scope and research decisions:

### Frontend Files (No Changes)
- `frontend/src/App.css` — Component styles use `var(--color-bg)` for surfaces; no page-level background overrides
- `frontend/src/App.tsx` — No inline styles or background references
- `frontend/src/components/**` — Component-level backgrounds retain their styling per spec edge case
- `frontend/index.html` — No style attributes
- `frontend/e2e/**/*.spec.ts` — No background color assertions in E2E tests
- `frontend/package.json` — No dependency changes

### Backend Files (No Changes)
- All backend files unchanged — this is a frontend CSS-only change

### Documentation (No Changes)
- `README.md` — No color documentation to update
- Spec files are separate artifacts

---

## Verification Contract

After implementing changes, verify the following:

### Light Mode Background (FR-001)
- [ ] Open application in browser (light mode)
- [ ] Observe page background is pink (`#FFC0CB`)
- [ ] Navigate between different views — pink background persists
- [ ] Resize browser window — background renders correctly at all sizes

### Dark Mode Background (FR-008)
- [ ] Toggle to dark mode
- [ ] Observe page background is dark pink (`#3D2027`)
- [ ] Navigate between views — dark pink background persists

### Component Legibility (FR-003, FR-004)
- [ ] All text is clearly readable against pink background
- [ ] Buttons, icons, and interactive elements are visually distinct
- [ ] Cards, modals, and input fields maintain white/dark surface backgrounds
- [ ] Status badges (success, warning, danger) remain visible

### Centralized Definition (FR-002)
- [ ] Change `#FFC0CB` to any other color in `:root` — verify it propagates everywhere
- [ ] Revert the test change

### Responsiveness (FR-005)
- [ ] Check on mobile viewport (~375px width)
- [ ] Check on tablet viewport (~768px width)
- [ ] Check on desktop viewport (~1440px width)

### No Regressions (FR-006)
- [ ] Sidebar layout unchanged
- [ ] Chat interface layout unchanged
- [ ] Login form layout unchanged
- [ ] Header layout unchanged

---

## Rollback Contract

If issues arise, revert changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: `--color-bg-secondary` returns to `#f6f8fa` (light) and `#161b22` (dark)

---

## Contract Compliance Checklist

- [x] All file paths are absolute and verified to exist
- [x] Line numbers documented for reference
- [x] Exact value changes specified (hex colors only)
- [x] Before/after states documented
- [x] Validation criteria defined
- [x] Out-of-scope files explicitly listed
- [x] Rollback procedure defined
- [x] Accessibility verification included

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
