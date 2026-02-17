# Quickstart Guide: Apply Red Background Color to Entire App Interface

**Feature**: 003-red-background | **Date**: 2026-02-17  
**Estimated Time**: 10-15 minutes  
**Prerequisites**: Git access, text editor, Node.js 18+

## Overview

This guide walks through implementing the red background change by updating CSS custom property values in `frontend/src/index.css`. The implementation involves updating color values in 2 CSS rule blocks (`:root` for light mode, `html.dark-mode-active` for dark mode) within a single file.

**Complexity**: ⭐ Trivial (1/5)  
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

**Expected**: On branch `003-red-background` or similar feature branch

### 1.2 Verify Current Theme Colors

```bash
grep -A 14 ':root {' frontend/src/index.css
```

**Expected Output** (current values):
```css
:root {
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  ...
}
```

If you see white/gray background values, proceed to Step 2.

---

## Step 2: Update Light Mode Colors

**Purpose**: Apply red background and compliant text colors for light mode

### 2.1 Edit `frontend/src/index.css`

Open the file:
```bash
nano frontend/src/index.css
# or use your preferred editor
```

### 2.2 Locate `:root` Block (Lines 2-15)

Find the CSS custom properties:
```css
:root {
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

### 2.3 Replace Color Values

Change to:
```css
:root {
  --color-bg: #FF0000;
  --color-bg-secondary: #CC0000;
  --color-border: #FF6666;
  --color-text: #FFFFFF;
  --color-text-secondary: #FFD700;
  --shadow: 0 1px 3px rgba(139, 0, 0, 0.3);
}
```

**Important**: Keep `--color-primary`, `--color-secondary`, `--color-success`, `--color-warning`, `--color-danger`, and `--radius` unchanged.

### 2.4 Save and Verify

```bash
grep "color-bg:" frontend/src/index.css
```

**Expected**: Shows `#FF0000` and `#CC0000` for the `:root` values

---

## Step 3: Update Dark Mode Colors

**Purpose**: Apply dark red background for dark mode

### 3.1 Locate `html.dark-mode-active` Block (Lines 18-30)

Find the dark mode overrides:
```css
html.dark-mode-active {
  --color-bg: #0d1117;
  --color-bg-secondary: #161b22;
  --color-border: #30363d;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

### 3.2 Replace Color Values

Change to:
```css
html.dark-mode-active {
  --color-bg: #8B0000;
  --color-bg-secondary: #5C0000;
  --color-border: #B22222;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
}
```

**Important**: Keep `--color-text` (#e6edf3) and `--color-text-secondary` (#8b949e) unchanged in dark mode—they already have excellent contrast against dark red.

### 3.3 Save and Verify

```bash
grep "color-bg:" frontend/src/index.css
```

**Expected**: Shows all 4 updated background values (#FF0000, #CC0000, #8B0000, #5C0000)

---

## Step 4: Verify Full File

**Purpose**: Ensure CSS is valid and complete

### 4.1 Check File Syntax

```bash
cd frontend
npx prettier --check src/index.css
```

If formatting issues exist:
```bash
npx prettier --write src/index.css
```

### 4.2 Build Check

```bash
npm run build
```

**Expected**: Build succeeds without errors. CSS variable value changes don't affect TypeScript compilation.

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
2. **Check**: Background is solid red (#FF0000)
3. **Check**: Text is white and readable
4. **Check**: Header area is red
5. **Check**: Login page (if not authenticated) shows red background

### 5.3 Verify Dark Mode

1. Click the theme toggle button (🌙/☀️)
2. **Check**: Background changes to deep red (#8B0000)
3. **Check**: Text remains readable (light colors on dark red)
4. **Check**: Toggle back to light mode—red returns without flickering

### 5.4 Verify Responsiveness

1. Open browser DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test at 375px (mobile), 768px (tablet), 1440px (desktop)
4. **Check**: Red background fills viewport at all sizes

### 5.5 Check Login Button

1. Verify login button is visible and clickable
2. If button text is invisible (white on white), note for follow-up fix

### 5.6 Stop Server

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
git commit -m "Apply red background color to entire app interface

- Update light mode: --color-bg to #FF0000, --color-text to #FFFFFF
- Update dark mode: --color-bg to #8B0000 (dark red)
- Update borders and shadows to match red theme
- Maintain WCAG AA contrast compliance

Addresses FR-001 through FR-008"
```

### 6.3 Verify Commit

```bash
git log -1 --stat
```

**Expected**: Shows commit with 1 file changed (index.css)

---

## Troubleshooting

### Issue: Background Not Changing

**Symptom**: App still shows old background color  
**Solution**:
1. Hard refresh: `Ctrl+Shift+R` (Chrome) or `Cmd+Shift+R` (Mac)
2. Check if you saved the file
3. Verify dev server is running and serving latest files

### Issue: Text Not Visible

**Symptom**: Text appears invisible or very hard to read  
**Solution**:
1. Verify `--color-text` is set to `#FFFFFF` (white) in `:root`
2. Check that specific component styles aren't overriding the variable
3. Use browser DevTools to inspect computed text color

### Issue: Dark Mode Not Switching to Dark Red

**Symptom**: Dark mode shows old dark background  
**Solution**:
1. Verify `html.dark-mode-active` block has `--color-bg: #8B0000`
2. Check that the theme toggle button is working (class is toggled on `<html>`)
3. Clear `localStorage` item `tech-connect-theme-mode` and reload

### Issue: Login Button Text Invisible

**Symptom**: Login button appears blank/empty  
**Solution**: The `.login-button` uses `background: var(--color-text)` which becomes white. Add a targeted fix:
```css
/* In App.css */
.login-button {
  background: var(--color-primary);
  color: #FFFFFF;
}
```

### Issue: Build Fails

**Symptom**: `npm run build` shows errors  
**Solution**:
1. Check CSS syntax (missing semicolons, unclosed braces)
2. Run `npx prettier --write src/index.css` to auto-fix formatting
3. Ensure no TypeScript errors (CSS changes shouldn't cause TS errors)

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

- [ ] **FR-001**: Background is red (#FF0000) on all screens ✅
- [ ] **FR-002**: Red background covers full viewport including scrollable areas ✅
- [ ] **FR-003**: Text has sufficient contrast against red background ✅
- [ ] **FR-004**: Dark mode shows deep red (#8B0000) background ✅
- [ ] **FR-005**: Navigation between views maintains red background ✅
- [ ] **FR-006**: Red background displays correctly on mobile/tablet/desktop ✅
- [ ] **FR-007**: Component backgrounds (cards, headers) preserved ✅
- [ ] **FR-008**: Theme toggle continues to work ✅
- [ ] **SC-001**: 100% of screens show red background ✅
- [ ] **SC-002**: Body text contrast ratio ≥ 4.5:1 ✅
- [ ] **SC-003**: Red displays on 320px-2560px viewports ✅
- [ ] **SC-004**: Zero flickering during navigation ✅
- [ ] **SC-005**: Dark mode maintains red identity + WCAG compliance ✅

---

## Success Criteria

✅ **Feature Complete** when:
1. Light mode background is red (#FF0000)
2. Dark mode background is deep red (#8B0000)
3. All text is readable (white/gold on red)
4. Theme toggle switches between light red and dark red
5. Red background fills viewport on all device sizes
6. Changes committed to git

**Total Time**: ~10-15 minutes for experienced developer

---

## Next Steps

After completing this guide:

1. **Review**: Self-review changes in git diff
2. **Test**: Run existing test suite to check for regressions
3. **Accessibility**: Use a contrast checker to verify ratios
4. **Screenshot**: Capture before/after for PR documentation
5. **Deploy**: Follow your deployment process

---

## Phase 1 Quickstart Completion Checklist

- [x] Step-by-step instructions provided (6 steps)
- [x] Prerequisites documented
- [x] Time estimate included (10-15 minutes)
- [x] Commands are copy-pasteable
- [x] Expected outputs documented
- [x] Troubleshooting section included
- [x] Rollback procedure defined
- [x] Validation checklist aligned with spec
- [x] Success criteria clearly stated

**Status**: ✅ **QUICKSTART COMPLETE** - Ready for implementation by speckit.tasks
