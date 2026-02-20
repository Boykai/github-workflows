# Quickstart Guide: Add Yellow Background Color to App

**Feature**: 008-add-yellow-background | **Date**: 2026-02-20
**Estimated Time**: 2-3 minutes
**Prerequisites**: Git access, text editor

## Overview

This guide walks through applying a soft yellow background color (#FFFDE7) to the application by updating a single CSS variable in the global stylesheet. The change is scoped to light mode only; dark mode is unaffected.

**Complexity**: ⭐ Trivial (1/5)
**Risk Level**: Minimal
**Rollback**: Instant (single git revert)

---

## Step 1: Verify Current State

**Purpose**: Confirm the current background color

```bash
cd /home/runner/work/github-workflows/github-workflows
grep "color-bg-secondary" frontend/src/index.css
```

**Expected Output**:
```
  --color-bg-secondary: #f6f8fa;
  --color-bg-secondary: #161b22;
```

The first line is light mode (will be changed), the second is dark mode (will not be changed).

---

## Step 2: Update CSS Variable

**Purpose**: Change the light mode background to yellow

### 2.1 Edit `frontend/src/index.css`

Open the file and locate the `:root` selector (approximately line 1-13).

### 2.2 Find the `--color-bg-secondary` line

```css
--color-bg-secondary: #f6f8fa;
```

### 2.3 Replace with yellow value

```css
--color-bg-secondary: #FFFDE7;
```

### 2.4 Save and Verify

```bash
grep "color-bg-secondary" frontend/src/index.css
```

**Expected Output**:
```
  --color-bg-secondary: #FFFDE7;
  --color-bg-secondary: #161b22;
```

---

## Step 3: Verify Dark Mode Unchanged

**Purpose**: Confirm dark mode is not affected

```bash
grep -A1 "dark-mode-active" frontend/src/index.css | head -5
```

**Expected**: The `html.dark-mode-active` selector should still exist with `--color-bg-secondary: #161b22`.

---

## Step 4: Manual Verification

**Purpose**: Confirm the change works visually

### 4.1 Start Development Server

```bash
cd frontend
npm run dev
```

### 4.2 Verify Light Mode

1. Open http://localhost:5173 in a browser
2. **Check**: Page background should be a soft yellow color
3. **Check**: Cards and modals should remain white
4. **Check**: All text should be clearly readable

### 4.3 Verify Dark Mode

1. Click the theme toggle button (🌙/☀️ in the header)
2. **Check**: Background should switch to dark theme (#0d1117)
3. **Check**: No yellow visible in dark mode

### 4.4 Stop Server

Press `Ctrl+C` to stop the dev server.

---

## Step 5: Build Verification

**Purpose**: Confirm the build succeeds

```bash
cd frontend
npm run build
```

**Expected**: Build completes with no errors.

---

## Troubleshooting

### Issue: Background not changing

**Symptom**: Page still shows gray background after edit
**Solution**:
1. Hard refresh: `Ctrl+Shift+R`
2. Check you edited the `:root` selector, not the dark mode selector
3. Verify the file was saved

### Issue: Components look wrong

**Symptom**: Some UI elements have unexpected yellow tint
**Expected**: Secondary surfaces (board columns, sidebar sections) will have a yellow tint. This is correct behavior — cards and primary containers remain white via `--color-bg`.

### Issue: Build fails

**Symptom**: `npm run build` fails
**Solution**: Ensure the CSS value is valid — should be `#FFFDE7` with no typos.

---

## Rollback Procedure

If the change needs to be reverted:

```bash
# Revert the single line change
# In frontend/src/index.css, change:
#   --color-bg-secondary: #FFFDE7;
# back to:
#   --color-bg-secondary: #f6f8fa;
```

---

## Validation Checklist

- [ ] Light mode background is soft yellow (#FFFDE7)
- [ ] Dark mode background is unchanged (#161b22)
- [ ] All text remains legible against yellow background
- [ ] Cards and modals remain white
- [ ] No build errors
- [ ] Theme toggle switches correctly between yellow (light) and dark backgrounds

---

## Success Criteria

✅ **Feature Complete** when:
1. Light mode shows yellow background globally
2. Dark mode is unaffected
3. All text and UI elements remain legible
4. Build succeeds with no errors

**Total Time**: ~2-3 minutes

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (5 steps)
- [x] Prerequisites documented
- [x] Time estimate included (2-3 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec
- [x] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** — Ready for implementation by speckit.tasks
