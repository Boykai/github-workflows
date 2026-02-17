# Quickstart Guide: Green Background for Tech Connect App

**Feature**: 003-green-background-app | **Date**: 2026-02-17
**Estimated Time**: 5 minutes
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the green background by updating 4 CSS custom property values in a single file (`frontend/src/index.css`). The application's existing CSS variable theming system propagates the color change to all components automatically.

**Complexity**: ⭐ Trivial (1/5)
**Risk Level**: Minimal
**Rollback**: Instant (single git revert)

---

## Step 1: Verify Current State

**Purpose**: Confirm you're working with the expected baseline

### 1.1 Check Current Branch

```bash
cd /home/runner/work/github-workflows/github-workflows
git status
```

**Expected**: On feature branch for green background

### 1.2 Verify Current Background Colors

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

## Step 2: Update Light Mode Background Colors

**Purpose**: Set green background for light mode

### 2.1 Edit `frontend/src/index.css`

Open the file and locate the `:root` selector (lines 2-15).

### 2.2 Change `--color-bg` (Line 8)

```diff
-  --color-bg: #ffffff;
+  --color-bg: #E8F5E9;
```

### 2.3 Change `--color-bg-secondary` (Line 9)

```diff
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #C8E6C9;
```

### 2.4 Save and Verify

```bash
grep "color-bg" frontend/src/index.css | head -2
```

**Expected**:
```
  --color-bg: #E8F5E9;
  --color-bg-secondary: #C8E6C9;
```

---

## Step 3: Update Dark Mode Background Colors

**Purpose**: Set green background for dark mode

### 3.1 Locate Dark Mode Selector

In the same file, find the `html.dark-mode-active` selector (lines 18-30).

### 3.2 Change `--color-bg` (Line 24)

```diff
-  --color-bg: #0d1117;
+  --color-bg: #0D2818;
```

### 3.3 Change `--color-bg-secondary` (Line 25)

```diff
-  --color-bg-secondary: #161b22;
+  --color-bg-secondary: #1A3A2A;
```

### 3.4 Save and Verify

```bash
grep "color-bg" frontend/src/index.css | tail -2
```

**Expected**:
```
  --color-bg: #0D2818;
  --color-bg-secondary: #1A3A2A;
```

---

## Step 4: Verify Complete File State

**Purpose**: Confirm all 4 changes applied correctly

```bash
grep -n "color-bg" frontend/src/index.css
```

**Expected Output**:
```
8:  --color-bg: #E8F5E9;
9:  --color-bg-secondary: #C8E6C9;
24:  --color-bg: #0D2818;
25:  --color-bg-secondary: #1A3A2A;
```

---

## Step 5: Manual Verification

**Purpose**: Confirm changes work in running application

### 5.1 Start Development Server

```bash
cd frontend
npm run dev
```

**Expected**: Server starts on http://localhost:5173

### 5.2 Verify Light Mode

1. Open http://localhost:5173 in browser
2. **Check**: Page background is mint green (#E8F5E9)
3. **Check**: Board columns are light green (#C8E6C9)
4. **Check**: All text is clearly readable
5. **Check**: Header, sidebar, cards all show green backgrounds

### 5.3 Verify Dark Mode

1. Click the theme toggle button (🌙/☀️)
2. **Check**: Page background becomes dark green (#0D2818/#1A3A2A)
3. **Check**: All text remains readable
4. **Check**: Transition is smooth, no flicker

### 5.4 Verify Responsiveness

1. Resize browser window to mobile width (~375px)
2. **Check**: Green background fills entire viewport
3. **Check**: No layout breakage or background gaps

### 5.5 Stop Server

Press `Ctrl+C` to stop the dev server.

---

## Step 6: Commit Changes

**Purpose**: Persist changes to git

### 6.1 Stage Changed File

```bash
cd /home/runner/work/github-workflows/github-workflows
git add frontend/src/index.css
```

### 6.2 Commit

```bash
git commit -m "Apply green background to Tech Connect app

- Light mode: --color-bg #E8F5E9, --color-bg-secondary #C8E6C9
- Dark mode: --color-bg #0D2818, --color-bg-secondary #1A3A2A
- All contrast ratios exceed WCAG 2.1 AA (4.5:1) requirements

Addresses FR-001 through FR-010"
```

---

## Troubleshooting

### Issue: Background Doesn't Appear Green

**Symptom**: Background appears white or unchanged after saving
**Solution**:
1. Hard refresh: `Ctrl+Shift+R`
2. Verify hex values are correct (no typos)
3. Check Vite dev server is running and hot-reloading

### Issue: Text is Hard to Read

**Symptom**: Text appears washed out or lacks contrast
**Solution**:
- Verify `--color-text` and `--color-text-secondary` values were NOT changed
- Only `--color-bg` and `--color-bg-secondary` should be modified
- If text colors were accidentally changed, revert them to original values

### Issue: Dark Mode Looks Wrong

**Symptom**: Dark mode shows bright green instead of dark green
**Solution**:
- Verify dark mode values are `#0D2818` and `#1A3A2A` (dark greens)
- These should be in the `html.dark-mode-active` block, not `:root`

### Issue: Login Button Invisible

**Symptom**: Login button blends into background
**Solution**:
- Login button uses `var(--color-text)` as background, not `var(--color-bg)`
- This is a pre-existing dark mode issue, not caused by green background change
- If needed, override `.login-button` background with a specific dark color

### Issue: Error Toast Not Visible

**Symptom**: Error messages are hard to see
**Solution**:
- Error toast/banner uses hardcoded `#fff1f0` background, not CSS variables
- Should be unaffected by this change
- If visibility is poor, it's a pre-existing issue

---

## Rollback Procedure

### Quick Rollback (Before Push)

```bash
git checkout -- frontend/src/index.css
```

### Rollback After Commit

```bash
git revert <commit-hash>
```

**Expected Rollback State**: Background returns to white (light) / dark grey (dark).

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: All screens show green background ✅
- [ ] **FR-002**: Green shade meets WCAG AA contrast (verified: 13.03:1, 10.90:1) ✅
- [ ] **FR-003**: All text/icons/buttons clearly visible ✅
- [ ] **FR-004**: Renders correctly on mobile, tablet, desktop ✅
- [ ] **FR-005**: No flicker during screen transitions ✅
- [ ] **FR-006**: Modals/overlays harmonize with green theme ✅
- [ ] **FR-007**: No layout or functionality breakage ✅
- [ ] **FR-008**: Dark mode uses darker green shade ✅
- [ ] **FR-009**: Fallback to neutral if variables fail (browser default) ✅
- [ ] **FR-010**: WCAG 2.1 AA compliance maintained ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. Light mode shows mint green backgrounds (#E8F5E9 / #C8E6C9)
2. Dark mode shows dark green backgrounds (#0D2818 / #1A3A2A)
3. All text is readable against green backgrounds
4. No layout breakage on any screen size
5. Changes committed to git

**Total Time**: ~5 minutes for experienced developer

---

## WCAG Contrast Reference

| Mode | Background | Text | Ratio | Requirement | Status |
|------|-----------|------|-------|-------------|--------|
| Light | #E8F5E9 | #24292f | 13.03:1 | 4.5:1 | ✅ |
| Light | #C8E6C9 | #24292f | 10.90:1 | 4.5:1 | ✅ |
| Light | #E8F5E9 | #57606a | 5.77:1 | 4.5:1 | ✅ |
| Light | #C8E6C9 | #57606a | 4.83:1 | 4.5:1 | ✅ |
| Dark | #0D2818 | #e6edf3 | 13.32:1 | 4.5:1 | ✅ |
| Dark | #1A3A2A | #e6edf3 | 10.56:1 | 4.5:1 | ✅ |
| Dark | #0D2818 | #8b949e | 6.81:1 | 4.5:1 | ✅ |
| Dark | #1A3A2A | #8b949e | 5.40:1 | 4.5:1 | ✅ |

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
- [x] WCAG contrast reference table included

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
