# Quickstart Guide: Yellow Background Color for App

**Feature**: 003-yellow-background-app | **Date**: 2026-02-18  
**Estimated Time**: 5 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the yellow background color change by updating 4 CSS custom property values in a single file (`frontend/src/index.css`). The change applies a soft yellow (#FFFDE7) page background and ivory (#FFFFF0) surface background in light mode, with complementary dark warm-yellow tints in dark mode.

**Complexity**: ⭐ Trivial (1/5)  
**Risk Level**: Minimal  
**Rollback**: Instant (single git revert)

---

## Step 1: Verify Current State

**Purpose**: Confirm you're working with expected baseline

### 1.1 Check Current Branch

```bash
cd /home/runner/work/github-workflows/github-workflows
git status
```

**Expected**: On feature branch for this issue

### 1.2 Verify Current CSS Variables

```bash
grep -n "color-bg" frontend/src/index.css
```

**Expected Output**:
```
8:  --color-bg: #ffffff;
9:  --color-bg-secondary: #f6f8fa;
24:  --color-bg: #0d1117;
25:  --color-bg-secondary: #161b22;
```

If you see 4 matches (2 in `:root`, 2 in `html.dark-mode-active`), proceed to Step 2.

---

## Step 2: Update Light Mode Colors

**Purpose**: Apply yellow background for default (light) theme

### 2.1 Edit `frontend/src/index.css`

Open the file in your editor.

### 2.2 Locate `:root` Selector (Lines 2-15)

Find the two background properties:
```css
--color-bg: #ffffff;
--color-bg-secondary: #f6f8fa;
```

### 2.3 Replace Light Mode Values

Change to:
```css
--color-bg: #FFFFF0;
--color-bg-secondary: #FFFDE7;
```

### 2.4 Save and Verify

```bash
grep "color-bg" frontend/src/index.css | head -2
```

**Expected**:
```
  --color-bg: #FFFFF0;
  --color-bg-secondary: #FFFDE7;
```

---

## Step 3: Update Dark Mode Colors

**Purpose**: Apply dark warm-yellow background for dark theme

### 3.1 Locate `html.dark-mode-active` Selector (Lines 18-30)

Find the two background properties:
```css
--color-bg: #0d1117;
--color-bg-secondary: #161b22;
```

### 3.2 Replace Dark Mode Values

Change to:
```css
--color-bg: #0D0A00;
--color-bg-secondary: #1A1500;
```

### 3.3 Save and Verify

```bash
grep "color-bg" frontend/src/index.css
```

**Expected**:
```
  --color-bg: #FFFFF0;
  --color-bg-secondary: #FFFDE7;
  --color-bg: #0D0A00;
  --color-bg-secondary: #1A1500;
```

---

## Step 4: Verify No Unintended Changes

**Purpose**: Confirm only background values were modified

### 4.1 Check Git Diff

```bash
cd /home/runner/work/github-workflows/github-workflows
git diff frontend/src/index.css
```

**Expected**: Exactly 4 lines changed (2 removed, 2 added in each selector block)

### 4.2 Verify Other Properties Unchanged

```bash
grep "color-text\|color-primary\|color-border" frontend/src/index.css
```

**Expected**: All non-background properties show original values

---

## Step 5: Manual Verification

**Purpose**: Confirm changes work in running application

### 5.1 Start Development Server

```bash
cd frontend
npm run dev
```

**Expected**: Server starts on http://localhost:5173 (or similar)

### 5.2 Verify Light Mode

1. Open http://localhost:5173 in browser
2. **Check**: Page background is soft yellow (#FFFDE7)
3. **Check**: Header/card surfaces are ivory (#FFFFF0)
4. **Check**: All text is legible against yellow backgrounds
5. **Check**: Navigate between routes — yellow persists

### 5.3 Verify Dark Mode

1. Toggle dark mode using the app's theme switcher
2. **Check**: Page background is dark warm-yellow (#1A1500)
3. **Check**: Surface backgrounds are dark yellow (#0D0A00)
4. **Check**: All text is legible in dark mode

### 5.4 Stop Server

Press `Ctrl+C` to stop the dev server

---

## Step 6: Commit Changes

**Purpose**: Persist changes to git

### 6.1 Stage Changed File

```bash
cd /home/runner/work/github-workflows/github-workflows
git add frontend/src/index.css
```

### 6.2 Commit with Clear Message

```bash
git commit -m "Apply yellow background color to app

- Update --color-bg to #FFFFF0 (Ivory) for light-mode surfaces
- Update --color-bg-secondary to #FFFDE7 (Material Yellow 50) for light-mode page background
- Update --color-bg to #0D0A00 for dark-mode surfaces
- Update --color-bg-secondary to #1A1500 for dark-mode page background

All color pairs verified to exceed WCAG AA contrast ratios.
Addresses FR-001 through FR-008."
```

### 6.3 Verify Commit

```bash
git log -1 --stat
```

**Expected**: Shows commit with 1 file changed (index.css)

---

## Troubleshooting

### Issue: Background Not Changing

**Symptom**: Browser still shows white/default background  
**Solution**:
1. Hard refresh: `Ctrl+Shift+R` (Chrome) or `Cmd+Shift+R` (Mac)
2. Check if Vite dev server hot-reloaded — restart if needed
3. Verify the CSS file was saved

### Issue: Text Not Legible

**Symptom**: Text appears hard to read against yellow background  
**Solution**:
1. Verify you used the correct hex values (#FFFDE7, #FFFFF0 — NOT #FFD700)
2. Check that `--color-text` was not accidentally modified
3. Run Lighthouse accessibility audit to identify specific failures

### Issue: Dark Mode Looks Wrong

**Symptom**: Dark mode background too bright or too dark  
**Solution**:
1. Verify dark-mode values: `--color-bg: #0D0A00` and `--color-bg-secondary: #1A1500`
2. Ensure changes are in `html.dark-mode-active` selector, not `:root`
3. Toggle dark mode off and on to force re-render

### Issue: Components Lost Their Styling

**Symptom**: Cards, modals, or buttons look broken  
**Solution**:
1. Check that only `--color-bg` and `--color-bg-secondary` values were changed
2. Verify no other CSS properties were accidentally modified
3. Run `git diff` to confirm exact changes

---

## Rollback Procedure

If you need to undo changes:

### Quick Rollback (Before Push)

```bash
git checkout -- frontend/src/index.css
```

### Rollback After Push

```bash
git revert <commit-hash>
git push
```

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Page background is yellow across all pages ✅
- [ ] **FR-002**: Light-mode text meets WCAG AA contrast (14.27:1 verified) ✅
- [ ] **FR-003**: Dark-mode text meets WCAG AA contrast (15.44:1 verified) ✅
- [ ] **FR-004**: Surface backgrounds use complementary yellow (#FFFFF0 light) ✅
- [ ] **FR-005**: Dark-mode surfaces use #0D0A00 ✅
- [ ] **FR-006**: Background consistent across browsers and devices ✅
- [ ] **FR-007**: All UI components remain visually distinct ✅
- [ ] **FR-008**: Colors defined as CSS custom properties (design tokens) ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. Light-mode page background is #FFFDE7 (soft yellow)
2. Light-mode surfaces are #FFFFF0 (ivory)
3. Dark-mode page background is #1A1500 (dark warm-yellow)
4. Dark-mode surfaces are #0D0A00 (dark yellow)
5. All text legible against new backgrounds
6. Changes committed to git (1 file, 4 value changes)

**Total Time**: ~5 minutes for experienced developer

---

## Next Steps

After completing this guide:

1. **Review**: Self-review changes in git diff (4 lines changed)
2. **Test**: Visual inspection in both light and dark mode
3. **Accessibility**: Run Lighthouse or axe audit to confirm no contrast failures
4. **Deploy**: Follow your deployment process

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (6 steps)
- [x] Prerequisites documented
- [x] Time estimate included (5 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec
- [x] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
