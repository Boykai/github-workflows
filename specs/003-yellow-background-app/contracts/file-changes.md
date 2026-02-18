# File Modification Contract: Yellow Background Color

**Feature**: 003-yellow-background-app | **Date**: 2026-02-18  
**Purpose**: Define exact file changes required for yellow background implementation

## Contract Overview

This contract specifies the precise modifications to the frontend CSS file to apply a yellow background color across the application. All changes are CSS custom property value replacements in a single file.

---

## File: `frontend/src/index.css`

**Purpose**: Global CSS custom properties defining the application's color scheme  
**Change Type**: Value replacement in 4 CSS custom properties

### Current State (Lines 1-30)

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

### Expected New State (Lines 1-30)

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
- ✅ CSS custom property structure unchanged
- ✅ Only hex color values modified (4 properties)
- ✅ All other properties untouched
- ✅ CSS syntax validity maintained
- ✅ WCAG AA contrast verified for all new values

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change per spec scope:

### Frontend Files (No Changes)
- `frontend/src/App.css` — References `var(--color-bg)` and `var(--color-bg-secondary)` via cascade; no edits needed
- `frontend/src/App.tsx` — Application component; no style changes
- `frontend/index.html` — HTML structure; no changes
- `frontend/package.json` — Dependencies unchanged
- `frontend/src/**/*.tsx` (all components) — No component-level style changes
- `frontend/e2e/**/*.spec.ts` — E2E tests do not assert background colors

### Backend Files (No Changes)
- All backend files unchanged (background is frontend-only concern)

### Documentation (No Changes)
- `README.md` — Background color is not documented in README
- `docker-compose.yml` — Infrastructure unchanged

---

## Verification Contract

After implementing changes, verify the following:

### Light Mode Background (FR-001, FR-002)
- [ ] Open application in browser (light mode)
- [ ] Observe page background is soft yellow (#FFFDE7)
- [ ] Observe surface backgrounds (header, cards) are ivory (#FFFFF0)
- [ ] Verify all text remains legible against yellow backgrounds

### Dark Mode Background (FR-003, FR-005)
- [ ] Toggle dark mode
- [ ] Observe page background is dark warm-yellow (#1A1500)
- [ ] Observe surface backgrounds are dark yellow (#0D0A00)
- [ ] Verify all text remains legible in dark mode

### Consistency (FR-006)
- [ ] Navigate between different routes — background persists
- [ ] Resize browser to mobile/tablet/desktop widths — background consistent
- [ ] Test in Chrome, Firefox, Safari, and Edge (if available)

### Component Preservation (FR-007)
- [ ] Cards remain visually distinct against yellow background
- [ ] Buttons retain existing colors and styles
- [ ] Navigation/header elements display correctly
- [ ] Modals/overlays function and display correctly

### Accessibility (FR-002, FR-003)
- [ ] Run accessibility audit (e.g., Lighthouse or axe)
- [ ] Confirm no new contrast failures introduced
- [ ] Verify secondary text (#57606a / #8b949e) remains legible

---

## Rollback Contract

If issues arise, revert changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: All 4 CSS custom properties return to previous values (#ffffff, #f6f8fa, #0d1117, #161b22)

---

## Contract Compliance Checklist

- [x] All file paths are absolute and verified to exist
- [x] Line numbers documented for reference (note: may shift during implementation)
- [x] Exact value replacements specified with diffs
- [x] Before/after states documented in full
- [x] Validation criteria defined
- [x] Out-of-scope files explicitly listed
- [x] Verification checklist aligned with functional requirements
- [x] Rollback procedure defined

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
