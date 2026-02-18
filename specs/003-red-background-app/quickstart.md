# Quickstart Guide: Apply Red Background Color to App

**Feature**: 003-red-background-app | **Date**: 2026-02-18  
**Estimated Time**: 5 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the red background color change by updating 4 CSS custom property values in the global theme file. The implementation requires modifying only `frontend/src/index.css`.

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

**Expected**: On feature branch for red background implementation

### 1.2 Verify Current CSS Values

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

**Purpose**: Apply red-tinted backgrounds for light mode

### 2.1 Edit `frontend/src/index.css`

Open the file and locate the `:root` selector (line 2).

### 2.2 Change `--color-bg` (Line 8)

```diff
-  --color-bg: #ffffff;
+  --color-bg: #fff5f5;
```

### 2.3 Change `--color-bg-secondary` (Line 9)

```diff
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #ffebee;
```

### 2.4 Save and Verify

```bash
grep "color-bg" frontend/src/index.css | head -2
```

**Expected**:
```
  --color-bg: #fff5f5;
  --color-bg-secondary: #ffebee;
```

---

## Step 3: Update Dark Mode Background Colors

**Purpose**: Apply dark red backgrounds for dark mode

### 3.1 Locate `html.dark-mode-active` Selector (Line 18)

### 3.2 Change `--color-bg` (Line 24)

```diff
-  --color-bg: #0d1117;
+  --color-bg: #2d0a0a;
```

### 3.3 Change `--color-bg-secondary` (Line 25)

```diff
-  --color-bg-secondary: #161b22;
+  --color-bg-secondary: #1a0505;
```

### 3.4 Save and Verify

```bash
grep "color-bg" frontend/src/index.css | tail -2
```

**Expected**:
```
  --color-bg: #2d0a0a;
  --color-bg-secondary: #1a0505;
```

---

## Step 4: Verify All Changes

**Purpose**: Confirm all 4 values are updated correctly

### 4.1 Check All Background Values

```bash
grep -n "color-bg" frontend/src/index.css
```

**Expected Output**:
```
8:  --color-bg: #fff5f5;
9:  --color-bg-secondary: #ffebee;
24:  --color-bg: #2d0a0a;
25:  --color-bg-secondary: #1a0505;
```

### 4.2 Verify No Old Values Remain

```bash
grep -c "#ffffff\|#f6f8fa\|#0d1117\|#161b22" frontend/src/index.css
```

**Expected**: `0` (no matches)

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
2. **Check**: Page background has a visible red tint (`#ffebee`)
3. **Check**: Header and card surfaces have a lighter red tint (`#fff5f5`)
4. **Check**: All text is clearly readable

### 5.3 Verify Dark Mode

1. Toggle dark mode using the theme switcher (☀️/🌙 button in header)
2. **Check**: Page background is dark red (`#1a0505`)
3. **Check**: Surface backgrounds are slightly lighter dark red (`#2d0a0a`)
4. **Check**: All text is clearly readable

### 5.4 Verify Responsive

1. Resize browser to mobile width (~375px)
2. **Check**: Red background is consistent
3. Resize to tablet width (~768px)
4. **Check**: Red background is consistent

### 5.5 Stop Server

Press `Ctrl+C` to stop the dev server.

---

## Troubleshooting

### Issue: Background Not Changing

**Symptom**: Browser still shows old background color  
**Solution**: 
1. Hard refresh: `Ctrl+Shift+R` (Chrome) or `Cmd+Shift+R` (Mac)
2. Verify file was saved
3. Check dev server is running with latest changes

### Issue: Text Not Readable

**Symptom**: Text appears too low contrast against red background  
**Solution**: 
1. Verify you used the correct hex values (not a more saturated red)
2. Check that `--color-text` values were NOT changed (should remain `#24292f` / `#e6edf3`)

### Issue: Dark Mode Not Working

**Symptom**: Dark mode doesn't show dark red  
**Solution**:
1. Verify the `html.dark-mode-active` selector values are correct
2. Check browser DevTools computed styles to see which selector is active

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Red-themed background visible across all screens ✅
- [ ] **FR-002**: Colors defined in centralized CSS custom properties ✅
- [ ] **FR-003**: Light mode text contrast ≥ 4.5:1 ✅
- [ ] **FR-004**: Dark mode text contrast ≥ 4.5:1 ✅
- [ ] **FR-005**: Consistent across mobile, tablet, desktop ✅
- [ ] **FR-006**: Component-level backgrounds not overridden ✅
- [ ] **FR-007**: Red background in both light and dark modes ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. Light mode shows red-tinted backgrounds (`#fff5f5` surfaces, `#ffebee` page)
2. Dark mode shows dark red backgrounds (`#2d0a0a` surfaces, `#1a0505` page)
3. All text maintains WCAG AA contrast ratios
4. Background is consistent across all viewports
5. No component-level backgrounds are unintentionally overridden

**Total Time**: ~5 minutes for experienced developer

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (5 steps)
- [x] Prerequisites documented
- [x] Time estimate included (5 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Validation checklist aligned with spec
- [x] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
