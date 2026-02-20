# Quickstart Guide: Add Green Background Color to App

**Feature**: 001-green-background | **Date**: 2026-02-20  
**Estimated Time**: 5 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the green background color change. The implementation involves updating 3 CSS variable values and adding 2 body style properties in a single file: `frontend/src/index.css`.

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

**Expected**: On feature branch `001-green-background` or similar

### 1.2 Verify Current Colors

```bash
grep -n "color-bg-secondary\|color-text:" frontend/src/index.css
```

**Expected Output**:
```
9:  --color-bg-secondary: #f6f8fa;
11:  --color-text: #24292f;
```

If you see these values, proceed to Step 2.

---

## Step 2: Update CSS Variables in `:root`

**Purpose**: Change background and text color design tokens

### 2.1 Edit `frontend/src/index.css`

Open the file and locate the `:root` block (lines 2-15).

### 2.2 Update Background Color Variable

Find:
```css
--color-bg-secondary: #f6f8fa;
```

Change to:
```css
--color-bg-secondary: #2D6A4F;
```

### 2.3 Update Text Color Variables

Find:
```css
--color-text: #24292f;
--color-text-secondary: #57606a;
```

Change to:
```css
--color-text: #ffffff;
--color-text-secondary: #d4e7d0;
```

### 2.4 Save and Verify Variables

```bash
grep -n "color-bg-secondary\|color-text" frontend/src/index.css | head -6
```

**Expected**:
```
9:  --color-bg-secondary: #2D6A4F;
11:  --color-text: #ffffff;
12:  --color-text-secondary: #d4e7d0;
```

---

## Step 3: Update Body Styles

**Purpose**: Add fallback color and full viewport coverage

### 3.1 Locate Body Rule

Find the `body` rule (around line 38):
```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg-secondary);
}
```

### 3.2 Add Fallback and Min-Height

Change to:
```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  background: #2D6A4F;
  background: var(--color-bg-secondary);
  min-height: 100vh;
}
```

**Note**: The hardcoded `background: #2D6A4F;` line before the `var()` line provides a fallback for browsers that don't support CSS custom properties.

### 3.3 Save and Verify

```bash
grep -A 8 "^body {" frontend/src/index.css
```

**Expected**: Body rule with both background declarations and min-height

---

## Step 4: Verify No Unintended Changes

**Purpose**: Confirm only intended files were modified

### 4.1 Check Git Diff

```bash
git diff --stat
```

**Expected**: Only `frontend/src/index.css` shows changes

### 4.2 Verify Dark Mode Unchanged

```bash
grep -A 12 "dark-mode-active" frontend/src/index.css
```

**Expected**: Dark mode variables unchanged (original values)

---

## Step 5: Manual Verification

**Purpose**: Confirm changes work in running application

### 5.1 Start Development Server

```bash
cd frontend
npm run dev
```

**Expected**: Server starts on http://localhost:5173

### 5.2 Verify in Browser

1. Open http://localhost:5173
2. **Check**: Page background is green (#2D6A4F)
3. **Check**: Text is white and readable
4. **Check**: Cards and UI components have their own (white) backgrounds
5. **Check**: No white gaps at bottom of viewport

### 5.3 Test Responsive

1. Resize browser window to mobile width (~375px)
2. **Check**: Green background fills entire viewport
3. Resize to tablet (~768px) and desktop (~1440px)
4. **Check**: No gaps or overflow

### 5.4 Stop Server

Press `Ctrl+C` to stop the dev server

---

## Step 6: Run Existing Tests

**Purpose**: Confirm no regressions

### 6.1 Run Unit Tests

```bash
cd frontend
npm run test
```

**Expected**: All tests pass (background color changes don't affect component tests)

### 6.2 Run E2E Tests (Optional)

```bash
npm run test:e2e
```

**Expected**: All tests pass (tests don't assert background colors)

---

## Troubleshooting

### Issue: White Text Not Visible on Cards

**Symptom**: Text on white card backgrounds becomes invisible  
**Solution**: This shouldn't happen — cards use `--color-bg` (#ffffff) with their own text styles. If seen, check that `--color-bg` was NOT changed (should remain #ffffff).

### Issue: Green Not Visible

**Symptom**: Background still appears gray/white  
**Solution**:
1. Hard refresh: `Ctrl+Shift+R`
2. Verify `--color-bg-secondary` is `#2D6A4F` (not `#f6f8fa`)
3. Ensure body rule has `background: var(--color-bg-secondary);`

### Issue: White Gap at Bottom

**Symptom**: White space visible below green when content is short  
**Solution**: Ensure `min-height: 100vh;` is in the `body` rule

### Issue: Dark Mode Shows Green

**Symptom**: Green background appears in dark mode (should use existing dark colors)  
**Solution**: Ensure changes are only in `:root` block, NOT in `html.dark-mode-active` block

---

## Rollback Procedure

### Quick Rollback (Before Push)

```bash
git checkout -- frontend/src/index.css
```

### Rollback After Push

```bash
git revert <commit-hash>
git push origin <branch>
```

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Green background visible on all pages
- [ ] **FR-002**: Color defined via `--color-bg-secondary` CSS variable
- [ ] **FR-003**: Text meets WCAG AA contrast (4.5:1) against green
- [ ] **FR-004**: Green consistent across all views
- [ ] **FR-005**: Green fills full viewport without gaps
- [ ] **FR-006**: Existing UI components remain legible
- [ ] **FR-007**: Hardcoded fallback `#2D6A4F` before `var()` declaration
- [ ] **FR-008**: No visual regressions in layout or spacing

---

## Success Criteria

✅ **Feature Complete** when:
1. Green background (#2D6A4F) visible across application
2. White text readable against green background
3. CSS variable allows single-location color updates
4. Full viewport covered without gaps
5. No regressions in existing UI components

**Total Time**: ~5 minutes for experienced developer

---

## Key Files Modified

| File | Change |
|------|--------|
| `frontend/src/index.css` | Update `--color-bg-secondary` to `#2D6A4F`, `--color-text` to `#ffffff`, `--color-text-secondary` to `#d4e7d0`; add fallback background and `min-height: 100vh` to body |

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
