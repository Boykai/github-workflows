# File Modification Contract: Apply Red Background Color

**Feature**: 003-red-background | **Date**: 2026-02-17  
**Purpose**: Define exact file changes required for red background implementation

## Contract Overview

This contract specifies the precise modifications to the frontend global stylesheet to change the application background from the current colors to red (#FF0000 light, #8B0000 dark). All changes are CSS custom property value updates in a single file.

---

## File: `frontend/src/index.css`

**Purpose**: Global CSS custom properties defining the application color theme  
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

**Change 1 - Light mode `:root`**: Update background, text, border, and shadow values

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
+  --color-bg: #FF0000;
+  --color-bg-secondary: #CC0000;
+  --color-border: #FF6666;
+  --color-text: #FFFFFF;
+  --color-text-secondary: #FFD700;
   --radius: 6px;
-  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
+  --shadow: 0 1px 3px rgba(139, 0, 0, 0.3);
 }
```

**Change 2 - Dark mode `html.dark-mode-active`**: Update background, border, and shadow values

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
+  --color-bg: #8B0000;
+  --color-bg-secondary: #5C0000;
+  --color-border: #B22222;
   --color-text: #e6edf3;
   --color-text-secondary: #8b949e;
-  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
+  --shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
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
  --color-bg: #FF0000;
  --color-bg-secondary: #CC0000;
  --color-border: #FF6666;
  --color-text: #FFFFFF;
  --color-text-secondary: #FFD700;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(139, 0, 0, 0.3);
}

/* Dark theme overrides */
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #8B0000;
  --color-bg-secondary: #5C0000;
  --color-border: #B22222;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
}
```

**Validation**:
- ✅ CSS selector structure unchanged
- ✅ Variable names unchanged (only values modified)
- ✅ All values are valid CSS color/shadow values
- ✅ Dark mode override specificity maintained
- ✅ Non-color variables (`--radius`) unchanged

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change per spec scope:

### Frontend Files (No Changes)
- `frontend/src/App.tsx` - No component structure changes
- `frontend/src/App.css` - Component styles use variables (auto-inherit new values)
- `frontend/src/hooks/useAppTheme.ts` - Theme toggle logic unchanged
- `frontend/src/components/**` - All components use CSS variables
- `frontend/index.html` - No HTML changes
- `frontend/package.json` - No dependency changes

### Backend Files (No Changes)
- All backend files unchanged (background color is frontend-only concern)

### Documentation (No Changes)
- `README.md` - No documentation updates for visual change

---

## Impact Analysis

### Components Automatically Affected (via CSS variable inheritance)

| Component | Variable Used | Effect |
|-----------|--------------|--------|
| `body` | `--color-bg-secondary`, `--color-text` | Background becomes red, text becomes white |
| `.app-header` | `--color-bg`, `--color-border` | Header background becomes red |
| `.theme-toggle-btn` | `--color-bg-secondary`, `--color-border` | Button background becomes darker red |
| `.spinner` | `--color-border` | Spinner border becomes red-tinted |
| `.login-button` | `--color-text` | Button background becomes white |
| `.app-login h1` | `--color-text` | Login title becomes white |
| `.app-login p` | `--color-text-secondary` | Login subtitle becomes gold |

### Potential Issue: Login Button

The `.login-button` uses `background: var(--color-text)` which will become white (#FFFFFF). The button text is hardcoded `color: white`, which would make text invisible on a white button. This should be verified during implementation and addressed if needed with a targeted `App.css` override.

---

## Verification Contract

After implementing changes, verify the following:

### Light Mode Red Background (FR-001, FR-002)
- [ ] Open application in browser (light mode)
- [ ] Observe red (#FF0000) background covering full viewport
- [ ] Scroll content—red background fills scrollable area
- [ ] Navigate between views—red persists without flickering

### Dark Mode Red Background (FR-004)
- [ ] Toggle to dark mode
- [ ] Observe deep red (#8B0000) background
- [ ] All text remains readable against dark red

### Text Contrast (FR-003)
- [ ] Body text is white and readable on red background
- [ ] Headings are clearly visible
- [ ] Secondary text (gold) is distinguishable
- [ ] Run contrast checker tool to verify ratios

### Component Preservation (FR-007)
- [ ] Header maintains its background styling
- [ ] Sidebar maintains its background styling
- [ ] Chat area maintains functionality
- [ ] Cards and containers have appropriate depth

### Responsiveness (FR-006)
- [ ] Red background fills viewport on mobile (375px)
- [ ] Red background fills viewport on tablet (768px)
- [ ] Red background fills viewport on desktop (1440px)
- [ ] No gaps or overflow at any breakpoint

### Theme Toggle (FR-005, FR-008)
- [ ] Light/dark mode toggle works correctly
- [ ] Switching modes maintains red identity
- [ ] No flickering during mode transition

---

## Rollback Contract

If issues arise, revert changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: All CSS variables return to previous values (white/dark backgrounds).

---

## Contract Compliance Checklist

- [x] All file paths are absolute and verified to exist
- [x] Exact property value changes specified
- [x] Before/after states documented
- [x] Validation criteria defined
- [x] Impact analysis on dependent components completed
- [x] Potential issues identified (login button)
- [x] Out-of-scope files explicitly listed
- [x] Rollback procedure defined

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
