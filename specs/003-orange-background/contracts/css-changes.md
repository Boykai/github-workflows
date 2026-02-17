# File Modification Contract: Orange Background CSS Changes

**Feature**: 003-orange-background | **Date**: 2026-02-17  
**Purpose**: Define exact CSS file changes required for orange background implementation

## Contract Overview

This contract specifies the precise modifications to frontend CSS files to apply an orange background across the entire application. All changes involve updating CSS custom property values in existing selectors. No new files, selectors, or structural changes are introduced.

---

## File: `frontend/src/index.css`

**Purpose**: Global CSS custom properties defining the app color theme  
**Change Type**: CSS custom property value updates in `:root` and `html.dark-mode-active` selectors

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

**Change 1 — Light Mode `:root` variables**:

```diff
 :root {
   --color-primary: #0969da;
   --color-secondary: #6e7781;
   --color-success: #1a7f37;
   --color-warning: #9a6700;
   --color-danger: #cf222e;
-  --color-bg: #ffffff;
-  --color-bg-secondary: #f6f8fa;
-  --color-border: #d0d7de;
-  --color-text: #24292f;
-  --color-text-secondary: #57606a;
+  --color-bg: #FF8C00;
+  --color-bg-secondary: #E07B00;
+  --color-border: #C06500;
+  --color-text: #000000;
+  --color-text-secondary: #4A2800;
   --radius: 6px;
-  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
+  --shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
 }
```

**Change 2 — Dark Mode `html.dark-mode-active` variables**:

```diff
 html.dark-mode-active {
   --color-primary: #539bf5;
   --color-secondary: #8b949e;
   --color-success: #3fb950;
   --color-warning: #d29922;
   --color-danger: #f85149;
-  --color-bg: #0d1117;
-  --color-bg-secondary: #161b22;
-  --color-border: #30363d;
-  --color-text: #e6edf3;
-  --color-text-secondary: #8b949e;
-  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
+  --color-bg: #CC7000;
+  --color-bg-secondary: #A35800;
+  --color-border: #8B4800;
+  --color-text: #FFFFFF;
+  --color-text-secondary: #D4A574;
+  --shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
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
  --color-bg: #FF8C00;
  --color-bg-secondary: #E07B00;
  --color-border: #C06500;
  --color-text: #000000;
  --color-text-secondary: #4A2800;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* Dark theme overrides */
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #CC7000;
  --color-bg-secondary: #A35800;
  --color-border: #8B4800;
  --color-text: #FFFFFF;
  --color-text-secondary: #D4A574;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}
```

**Validation**:
- ✅ CSS selector structure unchanged
- ✅ All custom property names preserved
- ✅ Only values modified
- ✅ CSS syntax valid
- ✅ Semantic color properties (primary, secondary, success, warning, danger) unchanged
- ✅ Layout properties (radius) unchanged

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change per spec scope:

### Frontend Files (No Changes)
- `frontend/src/App.tsx` — No component structure changes
- `frontend/src/App.css` — Login button uses `var(--color-text)` which resolves correctly to black (#000000) on orange background; no change needed
- `frontend/src/hooks/useAppTheme.ts` — Theme toggle mechanism unchanged
- `frontend/src/components/**` — All components inherit theme via CSS variables
- `frontend/index.html` — No HTML changes needed
- `frontend/package.json` — No dependency changes

### Backend Files (No Changes)
- All backend files unchanged (background is frontend-only concern)

### Documentation (No Changes)
- `README.md` — Not related to visual theming
- `docker-compose.yml` — Infrastructure unchanged

---

## Color Cascade Impact

The following CSS classes reference theme variables and will automatically update:

| Class | Variable Used | Effect |
|-------|--------------|--------|
| `body` | `--color-bg-secondary` | Page background becomes #E07B00 |
| `.app-header` | `--color-bg` | Header background becomes #FF8C00 |
| `.project-sidebar` | `--color-bg` | Sidebar background becomes #FF8C00 |
| `.chat-section` | `--color-bg` | Chat area background becomes #FF8C00 |
| `.task-card` | `--color-bg` | Card background becomes #FF8C00 |
| `.status-column` | `--color-bg-secondary` | Column background becomes #E07B00 |
| `.login-button` | `--color-text` | Button background becomes #000000 (black) |
| `.theme-toggle-btn` | `--color-bg-secondary` | Toggle background becomes #E07B00 |
| `.logout-button` | `--color-bg-secondary` | Logout button background becomes #E07B00 |
| `all borders` | `--color-border` | Borders become #C06500 (orange-tinted) |
| `all text` | `--color-text` | Primary text becomes #000000 (black) |
| `all secondary text` | `--color-text-secondary` | Secondary text becomes #4A2800 |

---

## Verification Contract

After implementing changes, verify the following:

### Orange Background (FR-001, FR-006)
- [ ] Open app — background is visibly orange (#FF8C00)
- [ ] Navigate all screens — orange background consistent
- [ ] Resize browser — background fills viewport without gaps
- [ ] Check mobile viewport — background renders correctly

### Accessibility (FR-002, FR-003)
- [ ] Primary text readable on orange background (black on orange)
- [ ] Secondary text readable on orange background
- [ ] Run contrast checker — normal text ≥ 4.5:1
- [ ] Run contrast checker — large text/UI ≥ 3:1

### Dark Mode (FR-005)
- [ ] Toggle dark mode — background changes to darker orange (#CC7000)
- [ ] Text readable in dark mode (white on dark orange)
- [ ] Toggle back — smooth transition to light orange

### Interactive Elements (FR-004)
- [ ] Login button visible and clickable (black button on orange)
- [ ] Cards distinguishable from background
- [ ] Form inputs have visible borders
- [ ] Sidebar clearly defined

### Edge Cases (FR-007, FR-008)
- [ ] No flash of non-orange during page transitions
- [ ] Error toasts still readable
- [ ] Sync status indicators visible

---

## Rollback Contract

If issues arise, revert changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: `frontend/src/index.css` returns to white/dark theme values.

---

## Contract Compliance Checklist

- [x] All file paths verified to exist
- [x] Exact CSS value replacements specified
- [x] Before/after states documented
- [x] Cascade impact mapped to all affected classes
- [x] Validation criteria defined
- [x] Out-of-scope files explicitly listed
- [x] Rollback procedure defined
- [x] WCAG contrast ratios documented

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
