# Quickstart Guide: Add Black Background Theme

**Feature**: 007-black-background | **Date**: 2026-02-19  
**Estimated Time**: 15-25 minutes  
**Prerequisites**: Git access, text editor, Node.js 18+

## Overview

This guide walks through implementing the black background theme by updating CSS design tokens and auditing hardcoded light colors. The implementation leverages the existing CSS custom property architecture so most components update automatically.

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

**Expected**: On a feature branch for this work

### 1.2 Verify Current Theme Tokens

```bash
grep -n "color-bg:" frontend/src/index.css
```

**Expected Output**:
```
8:  --color-bg: #ffffff;
24:  --color-bg: #0d1117;
```

If you see `#ffffff` for the `:root` value, proceed to Step 2.

### 1.3 Check for Hardcoded Light Backgrounds

```bash
grep -rn "#fff1f0\|#dafbe1\|#82071e" frontend/src/App.css
```

**Expected**: Matches at lines 388, 407, 446, 471

---

## Step 2: Prevent White Flash (index.html)

**Purpose**: Add inline background color to prevent FOWC (FR-005)

### 2.1 Edit `frontend/index.html`

Find:
```html
<html lang="en">
```

Change to:
```html
<html lang="en" style="background-color: #000000">
```

### 2.2 Verify

```bash
grep "background-color" frontend/index.html
```

**Expected**: `<html lang="en" style="background-color: #000000">`

---

## Step 3: Update Design Tokens (index.css)

**Purpose**: Change centralized color values to black theme (FR-001, FR-006)

### 3.1 Edit `frontend/src/index.css`

Replace the entire `:root` block (lines 2-15):

**From**:
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

**To**:
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

### 3.2 Verify Token Values

```bash
grep -A 13 "^:root" frontend/src/index.css
```

**Expected**: All values match the black theme values above

---

## Step 4: Fix Hardcoded Light Colors (App.css)

**Purpose**: Replace light backgrounds that bypass the token system (FR-007)

### 4.1 Update Highlight Animation

Find (line ~388):
```css
    background: #dafbe1;
```

Change to:
```css
    background: rgba(45, 164, 78, 0.2);
```

### 4.2 Update Error Toast Background

Find (line ~407):
```css
  background: #fff1f0;
```

Change to:
```css
  background: rgba(207, 34, 46, 0.15);
```

### 4.3 Update Error Banner Background

Find (line ~446):
```css
  background: #fff1f0;
```

Change to:
```css
  background: rgba(207, 34, 46, 0.15);
```

### 4.4 Update Error Banner Message Color

Find (line ~471):
```css
  color: #82071e;
```

Change to:
```css
  color: #ff6b6b;
```

### 4.5 Update Board Error Content Color

Find (line ~1476):
```css
  color: #82071e;
```

Change to:
```css
  color: #ff6b6b;
```

### 4.6 Verify Changes

```bash
grep -n "fff1f0\|dafbe1\|82071e" frontend/src/App.css
```

**Expected**: No matches (all replaced)

---

## Step 5: Visual Verification

**Purpose**: Confirm changes work in running application

### 5.1 Start Development Server

```bash
cd frontend
npm install
npm run dev
```

**Expected**: Server starts on http://localhost:5173

### 5.2 Check in Browser

Navigate to http://localhost:5173

**Verify**:
- [ ] Page background is black (#000000)
- [ ] No white flash on page load
- [ ] All text is readable (light text on dark background)
- [ ] Header has dark background
- [ ] Cards and sidebars have dark secondary background (#121212)
- [ ] Borders are visible but subtle
- [ ] Buttons and links are visible and interactive

### 5.3 Check Multiple Views

- [ ] Login page (if applicable)
- [ ] Chat interface
- [ ] Project board
- [ ] Error states (if testable)

### 5.4 Stop Server

Press `Ctrl+C` to stop the dev server

---

## Step 6: Verify No Remaining Light Backgrounds

**Purpose**: Complete audit (FR-007)

```bash
# Check for remaining hardcoded white/light backgrounds
grep -rn "#fff\b\|#ffffff\|#f6f8fa\|#f5f5f5" frontend/src/*.css frontend/src/**/*.css
```

**Expected**: No matches in background properties. Some `#fff` occurrences in `color: #fff` (white text on buttons) are acceptable and intentional.

---

## Step 7: Commit Changes

**Purpose**: Persist changes to git

### 7.1 Stage Changed Files

```bash
cd /home/runner/work/github-workflows/github-workflows
git add frontend/index.html
git add frontend/src/index.css
git add frontend/src/App.css
```

### 7.2 Commit

```bash
git commit -m "Apply black background theme to app

- Update :root design tokens to black theme values
- Add inline background-color on <html> to prevent white flash
- Replace hardcoded light background values in App.css
- All text colors pass WCAG AA contrast requirements

Addresses FR-001 through FR-009"
```

---

## Troubleshooting

### Issue: White Flash Still Visible

**Symptom**: Brief white background on page load  
**Solution**: Verify `frontend/index.html` has `style="background-color: #000000"` on `<html>` tag. Check browser cache — hard refresh with Ctrl+Shift+R.

### Issue: Text Not Readable

**Symptom**: Text appears too dark against black background  
**Solution**: Verify `--color-text: #e6edf3` in `:root`. Check if component has hardcoded color overriding the token.

### Issue: Components Still Light

**Symptom**: Some cards or sections have light backgrounds  
**Solution**: Search for hardcoded background values:
```bash
grep -rn "background.*#f\|background.*white" frontend/src/
```
Replace with `var(--color-bg)` or `var(--color-bg-secondary)`.

### Issue: Dark Mode Toggle Broken

**Symptom**: Toggle doesn't seem to change anything  
**Solution**: This is expected — both modes are now dark. The toggle switches between black (#000000) and GitHub dark (#0d1117). If distinct visual difference is needed, that's a separate feature.

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Black background on all pages ✅
- [ ] **FR-002**: Text contrast ≥ 4.5:1 ✅
- [ ] **FR-003**: Icons and interactive elements visible ✅
- [ ] **FR-004**: All components use dark backgrounds ✅
- [ ] **FR-005**: No white flash on page load ✅
- [ ] **FR-006**: Background color defined in single token ✅
- [ ] **FR-007**: No hardcoded light backgrounds remaining ✅
- [ ] **SC-001**: 100% of pages have black background ✅
- [ ] **SC-005**: Single centralized token for background ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. All pages display black background
2. All text passes WCAG AA contrast
3. No white flash during page load
4. All components themed consistently
5. Single centralized token controls background color
6. Changes committed to git

**Total Time**: ~15-25 minutes for experienced developer

---

## Next Steps

After completing this guide:

1. **Review**: Self-review changes in git diff
2. **Test**: Run existing E2E tests to check for regressions
3. **Screenshot**: Capture before/after for PR description
4. **Deploy**: Follow deployment process

---

## Phase 1 Quickstart Completion Checklist

- [X] Step-by-step instructions provided (7 steps)
- [X] Prerequisites documented
- [X] Time estimate included (15-25 minutes)
- [X] Commands are copy-pasteable
- [X] Expected outputs documented
- [X] Troubleshooting section included
- [X] Rollback procedure available (git revert)
- [X] Validation checklist aligned with spec
- [X] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
