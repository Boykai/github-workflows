# File Modification Contract: Add Black Background Theme

**Feature**: 007-black-background | **Date**: 2026-02-19  
**Purpose**: Define exact file changes required for black background theme

## Contract Overview

This contract specifies the precise modifications to frontend files to change the application's default theme from light (white background) to black. All changes are CSS value replacements and one HTML inline style addition. The existing CSS custom property architecture ensures that most component backgrounds update automatically via token inheritance.

---

## File: `frontend/index.html`

**Purpose**: Prevent flash of white content before CSS loads (FR-005)  
**Change Type**: Add inline `style` attribute to `<html>` element

### Current State

```html
<html lang="en">
```

### Required Change

**Line 2**: Add inline background style

```diff
-<html lang="en">
+<html lang="en" style="background-color: #000000">
```

### Expected New State

```html
<!DOCTYPE html>
<html lang="en" style="background-color: #000000">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Agent Projects</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Validation**:
- ✅ HTML structure unchanged
- ✅ Inline style applied before any external resources load
- ✅ Prevents white flash during page load

---

## File: `frontend/src/index.css`

**Purpose**: Update centralized design tokens to black theme values (FR-001, FR-006)  
**Change Type**: Value replacement in `:root` CSS custom properties

### Current State (Lines 2-15)

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

### Required Changes

```diff
 :root {
-  --color-primary: #0969da;
-  --color-secondary: #6e7781;
-  --color-success: #1a7f37;
-  --color-warning: #9a6700;
-  --color-danger: #cf222e;
-  --color-bg: #ffffff;
-  --color-bg-secondary: #f6f8fa;
-  --color-border: #d0d7de;
-  --color-text: #24292f;
-  --color-text-secondary: #57606a;
+  --color-primary: #539bf5;
+  --color-secondary: #8b949e;
+  --color-success: #3fb950;
+  --color-warning: #d29922;
+  --color-danger: #f85149;
+  --color-bg: #000000;
+  --color-bg-secondary: #121212;
+  --color-border: #30363d;
+  --color-text: #e6edf3;
+  --color-text-secondary: #8b949e;
   --radius: 6px;
-  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
+  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
 }
```

### Expected New State (Lines 2-15)

```css
:root {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #000000;
  --color-bg-secondary: #121212;
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Validation**:
- ✅ Token names unchanged (no component updates needed)
- ✅ All text colors pass WCAG AA contrast against new backgrounds
- ✅ `--radius` unchanged (non-color token)
- ✅ Dark mode overrides (`html.dark-mode-active`) remain unchanged

---

## File: `frontend/src/App.css`

**Purpose**: Replace hardcoded light background values (FR-007)  
**Change Type**: Color value replacements in specific selectors

### Change 1: Highlight Animation (Line 388)

```diff
 @keyframes highlight-pulse {
   0% {
-    background: #dafbe1;
+    background: rgba(45, 164, 78, 0.2);
     border-color: #2da44e;
     box-shadow: 0 0 0 4px rgba(45, 164, 78, 0.2);
   }
```

### Change 2: Error Toast Background (Line 407)

```diff
 .error-toast {
   ...
-  background: #fff1f0;
+  background: rgba(207, 34, 46, 0.15);
   border: 1px solid #cf222e;
```

### Change 3: Error Banner Background (Line 446)

```diff
 .error-banner {
   ...
-  background: #fff1f0;
+  background: rgba(207, 34, 46, 0.15);
   border: 1px solid #cf222e;
```

### Change 4: Error Banner Message Color (Line 471)

```diff
 .error-banner-message {
   font-size: 13px;
-  color: #82071e;
+  color: #ff6b6b;
 }
```

### Change 5: Error Content Color (Line 1476)

```diff
 .board-error-content p {
   font-size: 12px;
-  color: #82071e;
+  color: #ff6b6b;
   margin: 2px 0 0;
 }
```

**Validation**:
- ✅ Error states still visually distinct (red-tinted backgrounds)
- ✅ Error text readable on dark background
- ✅ Highlight animation visible on dark background
- ✅ No structural CSS changes

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change:

### Frontend Files (No Changes Needed)
- `frontend/src/components/chat/ChatInterface.css` — Already uses `var(--color-*)` tokens throughout; inherits black theme automatically
- `frontend/src/App.tsx` — No style changes; component structure unchanged
- `frontend/src/hooks/useAppTheme.ts` — Dark mode toggle unchanged per spec
- `frontend/src/main.tsx` — Entry point unchanged
- `frontend/package.json` — No dependency changes

### Backend Files (No Changes)
- All backend files unchanged (theme is frontend-only concern)

### Dark Mode Override (No Changes)
- `html.dark-mode-active` block in `index.css` — Intentionally preserved. Toggle still works, switching between two dark variants.

---

## Verification Contract

After implementing changes, verify the following:

### Global Black Background (FR-001, US1)
- [ ] Open application in browser
- [ ] All pages display black (`#000000`) background
- [ ] No white or light backgrounds visible on any route

### White Flash Prevention (FR-005, US1)
- [ ] Hard refresh page (Ctrl+Shift+R)
- [ ] No white flash visible during initial load
- [ ] Navigate between routes — no white flash during transitions

### Text Contrast (FR-002, FR-003, US2)
- [ ] All body text readable against black background
- [ ] All secondary text readable against dark backgrounds
- [ ] All icons visible and distinguishable
- [ ] Interactive elements (buttons, links, inputs) clearly visible

### Component Theming (FR-004, US3)
- [ ] Header uses dark background
- [ ] Sidebar uses dark background
- [ ] Cards use dark secondary background
- [ ] Modals use dark background
- [ ] Board columns use dark secondary background
- [ ] Chat interface uses dark background

### Error States (FR-007)
- [ ] Error toast has dark red-tinted background (not white)
- [ ] Error banner has dark red-tinted background (not white)
- [ ] Error text readable on dark background

### Centralized Token (FR-006, SC-005)
- [ ] Background color defined in single `--color-bg` token
- [ ] Changing `--color-bg` value in `:root` updates all pages

---

## Rollback Contract

If issues arise, revert changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: All files return to previous light theme values.

---

## Contract Compliance Checklist

- [X] All file paths verified to exist
- [X] Line numbers documented for reference
- [X] Exact color value replacements specified
- [X] Before/after states documented
- [X] Validation criteria defined
- [X] Out-of-scope files explicitly listed
- [X] Rollback procedure defined
- [X] WCAG AA contrast ratios verified

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
