# Quickstart Guide: Pink Background Color

**Feature**: 005-pink-background | **Date**: 2026-02-19  
**Estimated Time**: 5-10 minutes  
**Prerequisites**: Git access, text editor, web browser

## Overview

This guide walks through implementing the pink background color change by updating 2 CSS custom property values in `frontend/src/index.css`. The application's existing theming system handles propagation to all screens and components automatically.

**Complexity**: ⭐ Trivial (1/5)  
**Risk Level**: Low  
**Rollback**: Instant (single git revert)

---

## Step 1: Verify Current State

**Purpose**: Confirm you're working with the expected baseline

### 1.1 Check Current Branch

```bash
cd /home/runner/work/github-workflows/github-workflows
git status
```

**Expected**: On branch `005-pink-background` or related feature branch

### 1.2 Verify Current Background Color

```bash
grep "color-bg-secondary" frontend/src/index.css
```

**Expected Output**:
```
  --color-bg-secondary: #f6f8fa;
  --color-bg-secondary: #161b22;
```

If you see 2 matches (one in `:root`, one in `html.dark-mode-active`), proceed to Step 2.

### 1.3 Verify Body Uses the Variable

```bash
grep "background.*color-bg-secondary" frontend/src/index.css
```

**Expected Output**:
```
  background: var(--color-bg-secondary);
```

This confirms the body element uses `--color-bg-secondary` for its background.

---

## Step 2: Update Light Mode Background Color

**Purpose**: Change the page background to pink in light mode

### 2.1 Edit `frontend/src/index.css`

Open the file:
```bash
nano frontend/src/index.css
# or use your preferred editor
```

### 2.2 Locate the `:root` Block

Find the CSS custom properties block (near the top of the file):
```css
:root {
  /* ... other variables ... */
  --color-bg-secondary: #f6f8fa;
  /* ... */
}
```

### 2.3 Update Light Mode Value

Change `--color-bg-secondary` from `#f6f8fa` to `#FFC0CB`:

```css
--color-bg-secondary: #FFC0CB;
```

---

## Step 3: Update Dark Mode Background Color

**Purpose**: Apply a dark pink variant for dark mode

### 3.1 Locate the `html.dark-mode-active` Block

In the same file, find the dark mode overrides:
```css
html.dark-mode-active {
  /* ... other variables ... */
  --color-bg-secondary: #161b22;
  /* ... */
}
```

### 3.2 Update Dark Mode Value

Change `--color-bg-secondary` from `#161b22` to `#2d1a1e`:

```css
--color-bg-secondary: #2d1a1e;
```

### 3.3 Save and Verify

Save the file and verify both changes:
```bash
grep "color-bg-secondary" frontend/src/index.css
```

**Expected**:
```
  --color-bg-secondary: #FFC0CB;
  --color-bg-secondary: #2d1a1e;
```

---

## Step 4: Visual Verification

**Purpose**: Confirm the change works in a running application

### 4.1 Start Development Server

```bash
cd frontend
npm run dev
```

**Expected**: Server starts on http://localhost:5173 (or similar)

### 4.2 Verify Light Mode

Open http://localhost:5173 in your browser:

- [ ] Page background is visibly pink
- [ ] Text is readable (dark text on pink background)
- [ ] Cards/panels appear white against the pink background
- [ ] Buttons and interactive elements are distinguishable

### 4.3 Verify Dark Mode

Click the theme toggle button (🌙/☀️) in the header:

- [ ] Page background changes to dark pink (#2d1a1e)
- [ ] Light text is readable against dark pink
- [ ] Cards/panels appear dark against the dark pink background

### 4.4 Verify Responsive Behavior

Use browser DevTools responsive mode:

- [ ] Mobile viewport (375px): Pink background renders correctly
- [ ] Tablet viewport (768px): Pink background renders correctly
- [ ] Desktop viewport (1440px): Pink background renders correctly

### 4.5 Stop Server

Press `Ctrl+C` to stop the dev server.

---

## Step 5: Run Existing Tests

**Purpose**: Ensure no functional regressions

### 5.1 Run Unit Tests

```bash
cd frontend
npm run test
```

**Expected**: All existing tests pass (CSS color changes don't affect functional tests)

### 5.2 Run Linter

```bash
npm run lint
```

**Expected**: No new linting errors

### 5.3 Run Type Check

```bash
npm run type-check
```

**Expected**: No type errors (no TypeScript changes made)

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
git commit -m "Apply pink background color (#FFC0CB) via CSS theme variable

- Update --color-bg-secondary to #FFC0CB in :root (light mode)
- Update --color-bg-secondary to #2d1a1e in dark mode
- Centralized change propagates to all screens via existing theming system

Addresses FR-001, FR-002, FR-005, FR-008"
```

### 6.3 Verify Commit

```bash
git log -1 --stat
```

**Expected**: Shows commit with 1 file changed (`frontend/src/index.css`)

---

## Troubleshooting

### Issue: Background Doesn't Change

**Symptom**: Page still shows gray/white background  
**Solution**: 
1. Verify you edited the correct file: `frontend/src/index.css`
2. Check you changed `--color-bg-secondary`, not `--color-bg`
3. Hard refresh browser: `Ctrl+Shift+R`
4. Verify the value: `grep "color-bg-secondary" frontend/src/index.css`

### Issue: Text Is Hard to Read

**Symptom**: Text appears washed out or low contrast against pink  
**Solution**: 
1. Verify you used `#FFC0CB` (soft pink), not a brighter pink
2. Check text color variables are unchanged: `--color-text: #24292f`
3. Use browser DevTools to inspect computed contrast ratio

### Issue: Dark Mode Not Showing Dark Pink

**Symptom**: Dark mode background is still dark gray  
**Solution**: 
1. Verify you updated `--color-bg-secondary` in the `html.dark-mode-active` block (not `:root`)
2. Check the value: should be `#2d1a1e`
3. Toggle dark mode off and on again

### Issue: Tests Fail

**Symptom**: Existing tests fail after CSS change  
**Solution**: 
1. CSS color changes should not affect functional tests
2. If a visual regression test exists, update the baseline screenshots
3. Run `npm run test` to check specific failures

---

## Rollback Procedure

If you need to undo changes:

### Quick Rollback (Before Push)

```bash
git checkout -- frontend/src/index.css
```

### Rollback After Commit

```bash
git revert <commit-hash>
```

**Expected Rollback State**: `--color-bg-secondary` returns to `#f6f8fa` (light) / `#161b22` (dark)

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] **FR-001**: Pink background visible on all primary screens ✅
- [ ] **FR-002**: Color defined in single centralized location (`index.css`) ✅
- [ ] **FR-003**: Text contrast ≥4.5:1 against pink background ✅
- [ ] **FR-004**: UI components visually distinct on pink background ✅
- [ ] **FR-005**: Pink renders correctly on mobile, tablet, desktop ✅
- [ ] **FR-006**: No visual regressions on existing components ✅
- [ ] **FR-008**: Dark mode shows appropriate dark pink variant ✅
- [ ] **SC-001**: 100% of screens display pink background ✅
- [ ] **SC-003**: Single variable change updates all screens ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. Page background is pink (#FFC0CB) in light mode
2. Page background is dark pink (#2d1a1e) in dark mode
3. All text passes WCAG AA contrast check
4. UI components remain legible and visually distinct
5. Change is centralized in one CSS variable
6. Responsive rendering verified
7. Changes committed to git

**Total Time**: ~5-10 minutes for experienced developer

---

## Next Steps

After completing this guide:

1. **Review**: Self-review the single file change in git diff
2. **Test**: Run full test suite (`npm run test`)
3. **Visual Check**: Screenshot before/after for PR documentation
4. **Deploy**: Follow your deployment process
5. **Announce**: Notify team of visual branding update

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (6 steps)
- [x] Prerequisites documented
- [x] Time estimate included (5-10 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec
- [x] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
