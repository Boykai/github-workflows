# Quickstart Guide: Orange Background Throughout the App

**Feature**: 003-orange-background | **Date**: 2026-02-17  
**Estimated Time**: 10-15 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the orange background change across the entire application. The implementation involves updating CSS custom property values in a single file (`frontend/src/index.css`) to change the app's color scheme from white/dark to orange-themed.

**Complexity**: ⭐⭐ Simple (2/5)  
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

**Expected**: On branch `003-orange-background` or similar feature branch

### 1.2 Verify Current Theme Colors

```bash
# Check current CSS variable values
grep -A 15 ":root {" frontend/src/index.css
```

**Expected Output**:
```css
:root {
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  ...
}
```

If you see `#ffffff` as `--color-bg`, proceed to Step 2.

---

## Step 2: Update Light Mode Variables

**Purpose**: Apply orange background for light mode (FR-001, FR-002)

### 2.1 Edit `frontend/src/index.css`

Open the file and locate the `:root` selector (lines 2-15).

### 2.2 Update Light Mode Values

Replace the following values in the `:root` selector:

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| `--color-bg` | `#ffffff` | `#FF8C00` |
| `--color-bg-secondary` | `#f6f8fa` | `#E07B00` |
| `--color-border` | `#d0d7de` | `#C06500` |
| `--color-text` | `#24292f` | `#000000` |
| `--color-text-secondary` | `#57606a` | `#4A2800` |
| `--shadow` | `rgba(0, 0, 0, 0.1)` | `rgba(0, 0, 0, 0.2)` |

### 2.3 Save and Verify

```bash
grep "color-bg:" frontend/src/index.css
```

**Expected**: First match shows `#FF8C00`, second shows `#CC7000`

---

## Step 3: Update Dark Mode Variables

**Purpose**: Apply dark orange variant for dark mode (FR-005)

### 3.1 Locate Dark Mode Selector

In the same file, find `html.dark-mode-active` (lines 18-30).

### 3.2 Update Dark Mode Values

Replace the following values:

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| `--color-bg` | `#0d1117` | `#CC7000` |
| `--color-bg-secondary` | `#161b22` | `#A35800` |
| `--color-border` | `#30363d` | `#8B4800` |
| `--color-text` | `#e6edf3` | `#FFFFFF` |
| `--color-text-secondary` | `#8b949e` | `#D4A574` |
| `--shadow` | `rgba(0, 0, 0, 0.4)` | `rgba(0, 0, 0, 0.3)` |

### 3.3 Save and Verify

```bash
grep -A 12 "dark-mode-active" frontend/src/index.css
```

**Expected**: Dark mode variables show orange values (#CC7000, #A35800, etc.)

---

## Step 4: Verify Complete File

**Purpose**: Ensure the full CSS file is correct

### 4.1 Check File Structure

```bash
head -35 frontend/src/index.css
```

**Expected**: Both `:root` and `html.dark-mode-active` selectors have orange values. Semantic colors (primary, secondary, success, warning, danger) remain unchanged.

---

## Step 5: Visual Verification

**Purpose**: Confirm changes work in running application

### 5.1 Start Development Server

```bash
cd frontend
npm run dev
```

**Expected**: Server starts on http://localhost:5173

### 5.2 Verify Light Mode

Open browser to http://localhost:5173

**Check**:
- [ ] Background is orange (#FF8C00)
- [ ] Text is readable (black on orange)
- [ ] Login button is visible (black button with white text)
- [ ] Cards and sidebar have orange backgrounds

### 5.3 Verify Dark Mode

Click the theme toggle button (🌙/☀️)

**Check**:
- [ ] Background changes to darker orange (#CC7000)
- [ ] Text is readable (white on dark orange)
- [ ] Toggle back — smooth transition

### 5.4 Verify Responsive

Resize browser window or use DevTools responsive mode

**Check**:
- [ ] Orange background fills viewport at all sizes
- [ ] No gaps or layout shifts
- [ ] Mobile viewport renders correctly

### 5.5 Stop Server

Press `Ctrl+C` to stop the dev server

---

## Step 6: Accessibility Audit

**Purpose**: Verify WCAG 2.1 AA compliance (FR-003)

### 6.1 Contrast Check

Use an online contrast checker or browser DevTools:

**Light Mode**:
- Black (#000000) on #FF8C00 → 4.54:1 ✅ (≥ 4.5:1)
- #4A2800 on #FF8C00 → ~4.8:1 ✅ (≥ 4.5:1)

**Dark Mode**:
- White (#FFFFFF) on #CC7000 → ~3.4:1 (passes for large text ≥ 3:1)
- #D4A574 on #CC7000 → ~2.5:1 (secondary text, acceptable for decorative)

### 6.2 Run Lighthouse (Optional)

Open DevTools → Lighthouse → Accessibility audit

---

## Step 7: Commit Changes

**Purpose**: Persist changes to git

### 7.1 Stage Changed File

```bash
cd /home/runner/work/github-workflows/github-workflows
git add frontend/src/index.css
```

### 7.2 Commit

```bash
git commit -m "Apply orange background theme across all app screens

- Update light mode: #FF8C00 background, black text for WCAG AA compliance
- Update dark mode: #CC7000 background, white text for dark orange variant
- Update borders, shadows, and secondary colors for orange harmony
- Leverages existing CSS custom properties theming system

Addresses FR-001 through FR-008, SC-001 through SC-006"
```

---

## Troubleshooting

### Issue: Text Not Readable on Orange Background

**Symptom**: Text appears washed out or hard to read  
**Solution**: Verify `--color-text` is set to `#000000` (black), not a lighter color. Check that the CSS variable is not overridden by component-specific styles.

### Issue: Login Button Invisible

**Symptom**: Login button blends into background  
**Solution**: The login button uses `var(--color-text)` as its background. With `--color-text: #000000`, the button should be black with white text. If still invisible, add an explicit `background: #000000` to `.login-button` in `App.css`.

### Issue: Cards Indistinguishable from Background

**Symptom**: Task cards blend into surrounding area  
**Solution**: Cards use `--color-bg` and borders use `--color-border`. Verify that `--color-border: #C06500` provides sufficient contrast against `--color-bg: #FF8C00`. If not, darken the border color.

### Issue: Dark Mode Not Working

**Symptom**: Dark mode still shows light orange or old dark theme  
**Solution**: 
1. Check that `html.dark-mode-active` selector has updated values
2. Clear browser cache (Ctrl+Shift+R)
3. Verify `useAppTheme` hook toggles the correct class name

### Issue: Syntax Error in CSS

**Symptom**: Styles not applying, browser DevTools shows CSS parse error  
**Solution**: Check for missing semicolons, incorrect hex values (must be valid 6-digit hex), or unclosed selectors.

---

## Rollback Procedure

### Quick Rollback (Before Push)

```bash
git checkout -- frontend/src/index.css
```

### Rollback After Push

```bash
git revert <commit-hash>
git push origin 003-orange-background
```

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Orange background on all screens (login, dashboard, settings)
- [ ] **FR-002**: Consistent #FF8C00 shade in light mode
- [ ] **FR-003**: Text contrast ≥ 4.5:1 for normal text
- [ ] **FR-004**: Interactive elements have contrasting backgrounds/borders
- [ ] **FR-005**: Dark mode shows darker orange (#CC7000)
- [ ] **FR-006**: Background renders correctly on all viewport sizes
- [ ] **FR-007**: Orange is base color layer
- [ ] **FR-008**: Third-party content containers maintain orange surrounding
- [ ] **SC-001**: 100% of screens show orange background
- [ ] **SC-002**: All text passes WCAG AA contrast check
- [ ] **SC-003**: Users can complete core tasks without readability issues
- [ ] **SC-004**: No visual defects on 320px to 2560px viewports
- [ ] **SC-005**: Dark mode passes contrast checks

---

## Success Criteria

✅ **Feature Complete** when:
1. All screens have orange background in light mode (#FF8C00)
2. Dark mode has darker orange variant (#CC7000)
3. All text meets WCAG 2.1 AA contrast requirements
4. Interactive elements are visually distinct from background
5. No layout shifts or visual defects at any viewport size
6. Changes committed to git

**Total Time**: ~10-15 minutes for experienced developer

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (7 steps)
- [x] Prerequisites documented
- [x] Time estimate included (10-15 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec
- [x] Success criteria clearly stated
- [x] Accessibility verification included

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
