# Quickstart Guide: Brown Background Color

**Feature**: 003-brown-background | **Date**: 2026-02-17  
**Estimated Time**: 15-20 minutes  
**Prerequisites**: Git access, text editor, Node.js 18+

## Overview

This guide walks through implementing the brown background color across the Tech Connect app. The implementation involves updating CSS custom property values in `frontend/src/index.css` and selectively adjusting hardcoded colors in `frontend/src/App.css`.

**Complexity**: ⭐⭐ Low (2/5)  
**Risk Level**: Low  
**Rollback**: Instant (single git revert)

---

## Step 1: Verify Current State

**Purpose**: Confirm you're working with expected baseline

### 1.1 Check Current Branch

```bash
cd /home/runner/work/github-workflows/github-workflows
git status
```

**Expected**: On branch `003-brown-background` or the assigned feature branch

### 1.2 Verify Current Theme Variables

```bash
grep -n "color-bg" frontend/src/index.css
```

**Expected Output**:
```
6:  --color-bg: #ffffff;
7:  --color-bg-secondary: #f6f8fa;
20:  --color-bg: #0d1117;
21:  --color-bg-secondary: #161b22;
```

If you see 4 matches (2 in `:root`, 2 in `dark-mode-active`), proceed to Step 2.

---

## Step 2: Update Light Mode Colors

**Purpose**: Apply brown background to light mode theme (FR-001, FR-002, FR-009)

### 2.1 Edit `frontend/src/index.css`

Open the file and locate the `:root` block (lines 2-14).

### 2.2 Update CSS Custom Properties

Replace these values in the `:root` block:

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| `--color-bg` | `#ffffff` | `#8B5C2B` |
| `--color-bg-secondary` | `#f6f8fa` | `#7A4F24` |
| `--color-border` | `#d0d7de` | `#A67B4A` |
| `--color-text` | `#24292f` | `#FFFFFF` |
| `--color-text-secondary` | `#57606a` | `#E8D5B5` |
| `--shadow` | `rgba(0, 0, 0, 0.1)` | `rgba(0, 0, 0, 0.2)` |

### 2.3 Save and Verify

```bash
grep "color-bg:" frontend/src/index.css
```

**Expected**: `--color-bg: #8B5C2B;` and `--color-bg-secondary: #7A4F24;`

---

## Step 3: Update Dark Mode Colors

**Purpose**: Apply dark brown variant for dark mode (FR-005)

### 3.1 Locate Dark Mode Block

Find the `html.dark-mode-active` block (lines 18-29).

### 3.2 Update Dark Mode Properties

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| `--color-bg` | `#0d1117` | `#2C1A0E` |
| `--color-bg-secondary` | `#161b22` | `#3D2817` |
| `--color-border` | `#30363d` | `#5A3D25` |

### 3.3 Save and Verify

```bash
grep "dark-mode-active" -A 12 frontend/src/index.css | grep "color-bg"
```

**Expected**: Dark brown values visible

---

## Step 4: Add Fallback and Print Styles

**Purpose**: Provide fallback for unsupported browsers (FR-006) and print handling (edge case)

### 4.1 Add Fallback to Body

In the `body` rule, add a hardcoded fallback before the CSS variable:

```css
body {
  /* ... existing properties ... */
  background: #8B5C2B;
  background: var(--color-bg-secondary);
}
```

### 4.2 Add Print Media Query

Add at the end of `index.css`:

```css
@media print {
  body {
    background: #ffffff !important;
    color: #000000 !important;
  }
}
```

---

## Step 5: Update Hardcoded Colors in App.css

**Purpose**: Harmonize hardcoded colors that clash with brown theme (FR-007)

### 5.1 Login Button Hover

Find `.login-button:hover` and change:
- From: `background: #32383f;`
- To: `background: #5A3D25;`

### 5.2 Task Highlight Animation

Find `@keyframes highlightTask` and change:
- From: `background-color: #dafbe1;`
- To: `background-color: #C4956A;`

---

## Step 6: Build and Verify

**Purpose**: Confirm changes compile and display correctly

### 6.1 Install Dependencies (if needed)

```bash
cd frontend
npm install
```

### 6.2 Build Frontend

```bash
npm run build
```

**Expected**: Build completes with no errors

### 6.3 Start Development Server

```bash
npm run dev
```

### 6.4 Visual Verification

Open browser and check:

1. ☐ Main app background is brown (#8B5C2B)
2. ☐ Text is white and readable
3. ☐ Sidebar background is brown
4. ☐ Header background is brown
5. ☐ Toggle dark mode → darker brown (#2C1A0E)
6. ☐ Toggle back to light mode → original brown
7. ☐ No rendering errors or broken elements
8. ☐ Print preview shows white background

### 6.5 Accessibility Check

Run Lighthouse accessibility audit in Chrome DevTools:
1. Open DevTools (F12)
2. Go to "Lighthouse" tab
3. Check "Accessibility" category
4. Click "Generate report"

**Expected**: No new contrast violations

---

## Step 7: Run Existing Tests

**Purpose**: Verify no regressions

```bash
cd frontend
npm run test
```

**Expected**: All existing tests pass (no component logic was changed)

---

## Step 8: Commit Changes

**Purpose**: Persist changes to git

### 8.1 Stage Changed Files

```bash
cd /home/runner/work/github-workflows/github-workflows
git add frontend/src/index.css
git add frontend/src/App.css
```

### 8.2 Commit

```bash
git commit -m "Apply brown background color to app interface

- Update CSS custom properties for brown theme (light: #8B5C2B, dark: #2C1A0E)
- Adjust text colors for WCAG AA contrast compliance
- Harmonize border colors with brown palette
- Add print stylesheet override
- Add browser fallback color

Addresses FR-001 through FR-009, SC-001 through SC-006"
```

---

## Troubleshooting

### Issue: Text Not Readable on Brown Background

**Symptom**: Text appears too dark against brown  
**Solution**: Verify `--color-text` is set to `#FFFFFF` (not the old `#24292f`)

### Issue: Dark Mode Looks Gray, Not Brown

**Symptom**: Dark mode doesn't have brown character  
**Solution**: Verify `--color-bg` in `html.dark-mode-active` is `#2C1A0E` (not `#0d1117`)

### Issue: Build Fails

**Symptom**: TypeScript/Vite compilation errors  
**Solution**: CSS-only changes should not cause build failures. Check for syntax errors (missing semicolons, unclosed braces)

### Issue: Components Still Show White Background

**Symptom**: Some areas remain white despite CSS variable changes  
**Solution**: Check if those components use hardcoded colors instead of `var(--color-bg)`. Inspect with DevTools.

---

## Rollback Procedure

```bash
git revert <commit-hash>
```

All CSS custom properties return to previous white/gray/dark values instantly.

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Brown background on all main screens ✅
- [ ] **FR-002**: WCAG AA contrast ratio met ✅
- [ ] **FR-003**: Brown background on modals, sidebars, overlays ✅
- [ ] **FR-004**: Responsive — no gaps on mobile/tablet/desktop ✅
- [ ] **FR-005**: Dark mode dark brown variant works ✅
- [ ] **FR-006**: Fallback color in body rule ✅
- [ ] **FR-007**: Gradients/highlights harmonized ✅
- [ ] **FR-008**: No UI rendering errors ✅
- [ ] **FR-009**: Colors defined centrally in index.css ✅
- [ ] **SC-004**: Light ↔ dark toggle works smoothly ✅
- [ ] **SC-006**: Single file change for future color adjustments ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. All screens display brown background
2. All text meets WCAG AA contrast
3. Dark mode shows dark brown variant
4. Theme toggle works without glitches
5. No rendering errors introduced
6. All existing tests pass

**Total Time**: ~15-20 minutes for experienced developer

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (8 steps)
- [x] Prerequisites documented
- [x] Time estimate included (15-20 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec
- [x] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** — Ready for implementation by speckit.tasks
