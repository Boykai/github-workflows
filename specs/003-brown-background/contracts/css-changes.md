# File Modification Contract: Brown Background Color

**Feature**: 003-brown-background | **Date**: 2026-02-17  
**Purpose**: Define exact file changes required for brown background implementation

## Contract Overview

This contract specifies the precise CSS modifications to apply a brown background color across all app screens and components. All changes leverage the existing CSS custom property theming system. Changes are limited to CSS value updates in `frontend/src/index.css`, with selective adjustments to hardcoded colors in `frontend/src/App.css` and `frontend/src/components/chat/ChatInterface.css`.

---

## File: `frontend/src/index.css`

**Purpose**: Global CSS custom properties defining the color theme  
**Change Type**: CSS custom property value updates in `:root` and `html.dark-mode-active`

### Current State (Light Mode — `:root`)

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

### Required Changes (Light Mode)

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
+  --color-bg: #8B5C2B;
+  --color-bg-secondary: #7A4F24;
+  --color-border: #A67B4A;
+  --color-text: #FFFFFF;
+  --color-text-secondary: #E8D5B5;
   --radius: 6px;
-  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
+  --shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
 }
```

### Current State (Dark Mode — `html.dark-mode-active`)

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

### Required Changes (Dark Mode)

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
+  --color-bg: #2C1A0E;
+  --color-bg-secondary: #3D2817;
+  --color-border: #5A3D25;
   --color-text: #e6edf3;
   --color-text-secondary: #8b949e;
   --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
 }
```

### Body Fallback Addition

```diff
 body {
   font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
   font-size: 14px;
   line-height: 1.5;
   color: var(--color-text);
-  background: var(--color-bg-secondary);
+  background: #8B5C2B;
+  background: var(--color-bg-secondary);
 }
```

### Print Stylesheet Addition

Add at the end of `index.css`:

```css
@media print {
  body {
    background: #ffffff !important;
    color: #000000 !important;
  }
}
```

**Validation**:
- ✅ CSS syntax valid
- ✅ Custom properties cascade to all components using `var(--color-*)`
- ✅ Fallback provided for `body` background (FR-006)
- ✅ Print override prevents ink waste (edge case from spec)
- ✅ Semantic colors (primary, success, warning, danger) preserved unchanged

---

## File: `frontend/src/App.css`

**Purpose**: Component-level styles for the main app layout  
**Change Type**: Selective hardcoded color adjustments for visual harmony

### Change 1 — Login Button Hover

```diff
 .login-button:hover {
-  background: #32383f;
+  background: #5A3D25;
 }
```

**Rationale**: Dark gray hover clashes with brown theme. Warm brown hover harmonizes.

### Change 2 — Task Highlight Animation

```diff
 @keyframes highlightTask {
   0% {
-    background-color: #dafbe1;
+    background-color: #C4956A;
   }
 }
```

**Rationale**: Green-tinted highlight clashes with brown. Warm golden-brown highlight fits the theme.

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change:

### Frontend Files (No Changes Expected)
- `frontend/src/App.tsx` — No component logic changes; dark mode toggle works via CSS class
- `frontend/src/hooks/useAppTheme.ts` — Theme hook unchanged; still toggles `dark-mode-active` class
- `frontend/src/components/chat/ChatInterface.css` — Hardcoded colors are semantic (confirm/reject buttons, send button hover) and intentionally distinct from background theme
- `frontend/src/components/**/*.tsx` — All components use CSS variables and inherit theme automatically
- `frontend/package.json` — No dependency changes
- `frontend/index.html` — No HTML changes

### Backend Files (No Changes)
- All backend files unchanged — brown background is a frontend-only concern

### Documentation
- `README.md` — Out of scope per spec assumptions

---

## Verification Contract

After implementing changes, verify the following:

### Visual Verification
- [ ] **FR-001**: All main screens display brown background (#8B5C2B in light mode)
- [ ] **FR-003**: Modals, sidebars, navigation bars display harmonized brown shades
- [ ] **FR-004**: Brown background renders correctly on mobile, tablet, and desktop viewports
- [ ] **FR-005**: Dark mode displays darker brown variant (#2C1A0E)
- [ ] **FR-008**: No UI rendering errors or broken interactive elements

### Accessibility Verification
- [ ] **FR-002**: Text meets WCAG AA contrast ratio (4.5:1 normal, 3:1 large)
- [ ] Run Lighthouse or axe audit — no new contrast violations

### Technical Verification
- [ ] **FR-006**: Body has hardcoded fallback color before CSS variable
- [ ] **FR-009**: All color changes in single file (`index.css`)
- [ ] **SC-006**: Brown color defined centrally — future change requires only one file edit
- [ ] Print preview shows white background (not brown)

### Theme Toggle
- [ ] **SC-004**: Toggle light ↔ dark mode — smooth transition, no glitches
- [ ] Both modes display appropriate brown shades

---

## Rollback Contract

If issues arise, revert all CSS changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: All CSS custom properties return to previous white/gray/dark values.

---

## Contract Compliance Checklist

- [x] All file paths verified to exist in repository
- [x] Exact CSS value changes specified with diffs
- [x] Before/after states documented
- [x] WCAG AA contrast ratios pre-validated
- [x] Fallback strategy documented
- [x] Print handling documented
- [x] Out-of-scope files explicitly listed
- [x] Rollback procedure defined

**Status**: ✅ **CONTRACT COMPLETE** — Ready for implementation
