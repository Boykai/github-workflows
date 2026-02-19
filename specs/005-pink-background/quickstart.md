# Quickstart Guide: Pink Background Color

**Feature**: 005-pink-background | **Date**: 2026-02-19  
**Estimated Time**: 2-5 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through applying a pink background color globally to the application by updating 2 CSS custom property values in 1 file. The change leverages the existing CSS variable system for automatic propagation.

**Complexity**: ⭐ Trivial (1/5)  
**Risk Level**: Minimal  
**Rollback**: Instant (single git revert)

---

## Step 1: Verify Current State

**Purpose**: Confirm you're working with expected baseline

### 1.1 Check Current Background Color Variables

```bash
cd /home/runner/work/github-workflows/github-workflows
grep "color-bg-secondary" frontend/src/index.css
```

**Expected Output**:
```
  --color-bg-secondary: #f6f8fa;
  --color-bg-secondary: #161b22;
```

If you see these 2 matches (light mode + dark mode), proceed to Step 2.

---

## Step 2: Update Light Mode Background

**Purpose**: Change page background to pink in light mode

### 2.1 Edit `frontend/src/index.css`

Open the file and locate the `:root` section (lines 1-15).

### 2.2 Find Line 9

```css
  --color-bg-secondary: #f6f8fa;
```

### 2.3 Replace Value

Change to:
```css
  --color-bg-secondary: #FFC0CB;
```

---

## Step 3: Update Dark Mode Background

**Purpose**: Change page background to dark pink in dark mode

### 3.1 Find Dark Mode Section

Locate the `html.dark-mode-active` section (lines 17-30).

### 3.2 Find Line 25

```css
  --color-bg-secondary: #161b22;
```

### 3.3 Replace Value

Change to:
```css
  --color-bg-secondary: #3D2027;
```

### 3.4 Save and Verify

Save the file and verify both changes:
```bash
grep "color-bg-secondary" frontend/src/index.css
```

**Expected Output**:
```
  --color-bg-secondary: #FFC0CB;
  --color-bg-secondary: #3D2027;
```

---

## Step 4: Visual Verification

**Purpose**: Confirm changes render correctly

### 4.1 Start Development Server

```bash
cd frontend
npm run dev
```

### 4.2 Check Light Mode

1. Open browser to http://localhost:5173
2. Verify page background is pink
3. Verify all text is readable
4. Verify buttons, cards, and inputs are visually distinct
5. Navigate between views — pink background should persist

### 4.3 Check Dark Mode

1. Toggle dark mode (if dark mode toggle exists in app)
2. Verify page background is dark pink (`#3D2027`)
3. Verify all text remains readable

### 4.4 Check Responsiveness

1. Resize browser to mobile width (~375px)
2. Resize to tablet (~768px)
3. Resize to desktop (~1440px)
4. Pink background should render correctly at all sizes

### 4.5 Stop Server

Press `Ctrl+C` to stop the dev server.

---

## Step 5: Run Existing Tests

**Purpose**: Ensure no regressions

```bash
cd frontend
npm run test
```

**Expected**: All existing tests pass (no background-color assertions exist in current tests).

---

## Step 6: Commit Changes

**Purpose**: Persist changes to git

### 6.1 Stage and Commit

```bash
cd /home/runner/work/github-workflows/github-workflows

git add frontend/src/index.css
git commit -m "Apply pink background color via CSS variables

- Update --color-bg-secondary to #FFC0CB (light mode)
- Update --color-bg-secondary to #3D2027 (dark mode)
- WCAG AA contrast ratios verified for all text

Addresses FR-001, FR-002, FR-003, FR-005, FR-008"
```

---

## Troubleshooting

### Issue: Background Not Changing

**Symptom**: Page still shows old gray background  
**Solution**: 
1. Hard refresh: `Ctrl+Shift+R`
2. Verify you saved the file
3. Check Vite dev server is running and hot-reloading

### Issue: Text Hard to Read

**Symptom**: Text appears low-contrast on pink background  
**Solution**: 
1. Verify you used `#FFC0CB` (light pink), not a brighter shade
2. Check contrast ratio at https://webaim.org/resources/contrastchecker/
3. Text color `#24292f` on `#FFC0CB` should be ~10.3:1

### Issue: Dark Mode Not Pink

**Symptom**: Dark mode still shows original dark background  
**Solution**: 
1. Verify you updated the `html.dark-mode-active` section (not just `:root`)
2. Check the dark-mode-active class is being toggled in browser DevTools

---

## Rollback Procedure

If you need to undo changes:

```bash
# Revert CSS variable values to original
# In frontend/src/index.css:
# :root section: --color-bg-secondary: #f6f8fa;
# dark-mode-active section: --color-bg-secondary: #161b22;
```

Or via git:
```bash
git revert <commit-hash>
```

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Pink background renders on all primary screens ✅
- [ ] **FR-002**: Color defined as centralized CSS variable ✅
- [ ] **FR-003**: Text contrast ratio ≥ 4.5:1 ✅
- [ ] **FR-004**: UI components legible on pink background ✅
- [ ] **FR-005**: Responsive across mobile/tablet/desktop ✅
- [ ] **FR-006**: No visual regressions ✅
- [ ] **FR-007**: No hardcoded background overrides remain ✅
- [ ] **FR-008**: Dark mode has adjusted pink variant ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. Page background is pink (`#FFC0CB`) in light mode
2. Page background is dark pink (`#3D2027`) in dark mode
3. All text meets WCAG AA contrast (4.5:1 minimum)
4. UI components remain visually distinct and functional
5. Background renders correctly on all screen sizes
6. Changes committed to git

**Total Time**: ~2-5 minutes

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (6 steps)
- [x] Prerequisites documented
- [x] Time estimate included (2-5 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec
- [x] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
