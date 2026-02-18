# Quickstart Guide: Yellow Background Color for App

**Feature**: 003-yellow-background-app | **Date**: 2026-02-18  
**Estimated Time**: 5 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the yellow background color change by updating 4 CSS custom property values in `frontend/src/index.css`. No other files require modification.

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

**Expected**: On feature branch for yellow background implementation

### 1.2 Verify Current Colors

```bash
grep -n "color-bg" frontend/src/index.css
```

**Expected Output**:
```
8:  --color-bg: #ffffff;
9:  --color-bg-secondary: #f6f8fa;
24:  --color-bg: #0d1117;
25:  --color-bg-secondary: #161b22;
43:  background: var(--color-bg-secondary);
```

If you see these 5 matches (4 variable definitions + 1 usage), proceed to Step 2.

---

## Step 2: Update Light Mode Colors

**Purpose**: Change light-mode background from neutral to yellow

### 2.1 Edit `frontend/src/index.css`

Open the file in your editor.

### 2.2 Locate `:root` Block (Lines 2-15)

Find the two background color variables:
```css
--color-bg: #ffffff;
--color-bg-secondary: #f6f8fa;
```

### 2.3 Replace Values

Change to:
```css
--color-bg: #FFFFF0;
--color-bg-secondary: #FFFDE7;
```

### 2.4 Verify Light Mode Changes

```bash
grep -n "color-bg" frontend/src/index.css | head -2
```

**Expected**:
```
8:  --color-bg: #FFFFF0;
9:  --color-bg-secondary: #FFFDE7;
```

---

## Step 3: Update Dark Mode Colors

**Purpose**: Change dark-mode background from neutral to warm-yellow tint

### 3.1 Locate `html.dark-mode-active` Block (Lines 18-30)

Find the two dark-mode background color variables:
```css
--color-bg: #0d1117;
--color-bg-secondary: #161b22;
```

### 3.2 Replace Values

Change to:
```css
--color-bg: #0D0A00;
--color-bg-secondary: #1A1500;
```

### 3.3 Verify Dark Mode Changes

```bash
grep -n "color-bg" frontend/src/index.css | head -5
```

**Expected**:
```
8:  --color-bg: #FFFFF0;
9:  --color-bg-secondary: #FFFDE7;
24:  --color-bg: #0D0A00;
25:  --color-bg-secondary: #1A1500;
43:  background: var(--color-bg-secondary);
```

---

## Step 4: Verify Complete File State

**Purpose**: Confirm all 4 changes are correct

```bash
head -30 frontend/src/index.css
```

**Expected**: Both `:root` and `html.dark-mode-active` blocks show updated yellow values while all other variables remain unchanged.

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

Navigate to http://localhost:5173:
- **Check**: Page background is soft yellow (#FFFDE7)
- **Check**: Header/card surfaces are ivory (#FFFFF0)
- **Check**: All text is legible

### 5.3 Verify Dark Mode

Toggle dark mode:
- **Check**: Page background shows dark warm-yellow tint (#1A1500)
- **Check**: Surface elements show deeper dark yellow (#0D0A00)
- **Check**: All text is legible

### 5.4 Stop Server

Press `Ctrl+C` to stop the dev server

---

## Step 6: Commit Changes

**Purpose**: Persist changes to git

### 6.1 Stage and Commit

```bash
cd /home/runner/work/github-workflows/github-workflows

git add frontend/src/index.css
git commit -m "Apply yellow background color to app

- Change light-mode page background to #FFFDE7 (Material Yellow 50)
- Change light-mode surface background to #FFFFF0 (Ivory)
- Change dark-mode page background to #1A1500 (warm dark yellow)
- Change dark-mode surface background to #0D0A00 (deep dark yellow)

All color pairs exceed WCAG AA contrast requirements.
Addresses FR-001 through FR-008"
```

---

## Troubleshooting

### Issue: Colors Don't Change in Browser

**Symptom**: Browser still shows old background colors  
**Solution**: 
1. Hard refresh: `Ctrl+Shift+R` (Chrome) or `Cmd+Shift+R` (Mac)
2. Clear browser cache
3. Check if you saved the CSS file

### Issue: Text Is Hard to Read

**Symptom**: Text appears low-contrast against yellow background  
**Solution**: 
1. Verify correct hex values (common mistake: using #FFD700 instead of #FFFDE7)
2. Check that `--color-text` variables were NOT changed (should remain #24292f / #e6edf3)

### Issue: Dark Mode Not Working

**Symptom**: Dark mode still shows neutral dark colors  
**Solution**: 
1. Verify `html.dark-mode-active` selector values were updated (not just `:root`)
2. Check dark mode toggle functionality hasn't changed

### Issue: Build Fails

**Symptom**: Vite/CSS compilation fails  
**Solution**: 
1. Ensure hex values are valid 6-digit format (e.g., `#FFFDE7` not `#FFFDE`)
2. Check that no CSS syntax was accidentally corrupted (semicolons, braces)

---

## Rollback Procedure

If you need to undo changes:

### Quick Rollback (Before Push)

```bash
git checkout frontend/src/index.css
```

### Rollback After Push

```bash
git revert <commit-hash>
git push origin <branch-name>
```

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Yellow background visible across all pages (light mode) ✅
- [ ] **FR-002**: Light-mode text legible (14.27:1 contrast ratio) ✅
- [ ] **FR-003**: Dark-mode text legible (15.44:1 contrast ratio) ✅
- [ ] **FR-004**: Light-mode surfaces are ivory (#FFFFF0) ✅
- [ ] **FR-005**: Dark-mode surfaces are deep dark yellow (#0D0A00) ✅
- [ ] **FR-006**: Consistent across Chrome, Firefox, Safari, Edge ✅
- [ ] **FR-007**: Existing UI components preserved ✅
- [ ] **FR-008**: Colors defined as CSS custom properties ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. Light-mode page background is #FFFDE7 (soft yellow)
2. Light-mode surface background is #FFFFF0 (ivory)
3. Dark-mode page background is #1A1500 (warm dark yellow)
4. Dark-mode surface background is #0D0A00 (deep dark yellow)
5. All text remains legible (WCAG AA contrast verified)
6. Changes committed to git

**Total Time**: ~5 minutes for experienced developer

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
