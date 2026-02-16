# Quickstart Guide: Red Background Interface

**Feature**: Red Background Interface  
**Branch**: `copilot/apply-red-background-interface-again`  
**Date**: 2026-02-16  
**Estimated Time**: 15-20 minutes

## Overview

This guide walks through implementing the red background feature from start to finish. The implementation requires changing 2 lines of CSS in a single file to apply a red (#FF0000) background to the main application container.

## Prerequisites

Before starting, ensure you have:

- [ ] Git repository cloned locally
- [ ] Node.js 18+ installed
- [ ] npm installed
- [ ] Branch `copilot/apply-red-background-interface-again` checked out
- [ ] Frontend dependencies installed (`cd frontend && npm install`)
- [ ] Basic text editor or IDE

## Quick Implementation (5 minutes)

If you just want to make the change quickly:

```bash
# 1. Navigate to repository root
cd /home/runner/work/github-workflows/github-workflows

# 2. Edit the CSS file
# Open frontend/src/index.css in your editor
# Find line with: --color-bg-secondary: #f6f8fa;
# Change to:      --color-bg-secondary: #FF0000;
# Find line with: --color-bg-secondary: #161b22;
# Change to:      --color-bg-secondary: #FF0000;

# 3. Verify the build
cd frontend
npm run build

# 4. Test in development mode
npm run dev
# Open http://localhost:5173 and verify red background

# 5. Commit and push
git add src/index.css
git commit -m "Apply red background to application interface"
git push origin copilot/apply-red-background-interface-again
```

Done! The application now has a red background.

## Detailed Step-by-Step Guide

### Step 1: Verify Current State

Before making changes, verify the application works:

```bash
cd /home/runner/work/github-workflows/github-workflows/frontend
npm run dev
```

Expected output:
```
VITE v5.x.x ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

Open http://localhost:5173 in your browser. You should see:
- Light gray background (light mode) or dark gray background (dark mode)
- Application loads without errors
- Theme toggle button works

Stop the dev server (Ctrl+C) before proceeding.

---

### Step 2: Locate the CSS File

Navigate to the CSS file to be modified:

```bash
cd /home/runner/work/github-workflows/github-workflows/frontend/src
ls -la index.css
```

Expected output:
```
-rw-r--r-- 1 user user xxx index.css
```

---

### Step 3: Backup Current State (Optional)

If you want a quick backup:

```bash
cd /home/runner/work/github-workflows/github-workflows/frontend/src
cp index.css index.css.backup
```

---

### Step 4: View Current CSS Variables

Check the current variable values:

```bash
cd /home/runner/work/github-workflows/github-workflows/frontend/src
grep -n "color-bg-secondary" index.css
```

Expected output:
```
8:  --color-bg-secondary: #f6f8fa;
20:  --color-bg-secondary: #161b22;
```

Line numbers may vary slightly depending on formatting changes.

---

### Step 5: Make the Changes

**Option A: Using a text editor**

Open `frontend/src/index.css` in your preferred editor and make these changes:

**Change 1** (Light mode - around line 8):
```css
/* Before */
--color-bg-secondary: #f6f8fa;

/* After */
--color-bg-secondary: #FF0000;
```

**Change 2** (Dark mode - around line 20):
```css
/* Before */
--color-bg-secondary: #161b22;

/* After */
--color-bg-secondary: #FF0000;
```

**Option B: Using sed (command line)**

```bash
cd /home/runner/work/github-workflows/github-workflows/frontend/src

# Change light mode
sed -i 's/--color-bg-secondary: #f6f8fa;/--color-bg-secondary: #FF0000;/' index.css

# Change dark mode
sed -i 's/--color-bg-secondary: #161b22;/--color-bg-secondary: #FF0000;/' index.css
```

---

### Step 6: Verify the Changes

Confirm both changes were applied:

```bash
cd /home/runner/work/github-workflows/github-workflows/frontend/src
grep -n "color-bg-secondary" index.css
```

Expected output:
```
8:  --color-bg-secondary: #FF0000;
20:  --color-bg-secondary: #FF0000;
```

Both lines should now show `#FF0000` (red).

---

### Step 7: Validate CSS Syntax

Ensure the CSS file is still valid:

```bash
cd /home/runner/work/github-workflows/github-workflows/frontend
npm run build
```

Expected output (should succeed):
```
vite v5.x.x building for production...
✓ xxx modules transformed.
dist/index.html                  x.xx kB
dist/assets/index-xxxxx.js      xxx.xx kB
dist/assets/index-xxxxx.css      xx.xx kB
✓ built in xxxms
```

If build fails, check for syntax errors (missing semicolons, typos).

---

### Step 8: Test in Development Mode

Start the development server:

```bash
cd /home/runner/work/github-workflows/github-workflows/frontend
npm run dev
```

Open http://localhost:5173 in your browser.

**Visual Verification Checklist:**

- [ ] **Initial Load**: Background is red when page loads
- [ ] **Theme Toggle**: Click theme toggle button - background stays red in both modes
- [ ] **Navigation**: If multiple routes exist, navigate between them - background stays red
- [ ] **Refresh**: Press F5 or Ctrl+R - background remains red after refresh
- [ ] **Responsive**: Resize browser window - background spans full width at all sizes

**Browser DevTools Verification:**

1. Open DevTools (F12)
2. Go to Elements/Inspector tab
3. Select `<body>` element
4. In Computed styles, verify:
   ```
   background-color: rgb(255, 0, 0)
   ```
5. In Styles panel, find `:root` or `html.dark-mode-active` and verify:
   ```
   --color-bg-secondary: #FF0000;
   ```

---

### Step 9: Test Side Effects

Verify expected side effects (these are ACCEPTABLE):

**Theme Toggle Button:**
- Background should be red (inherits `--color-bg-secondary`)
- Button should still be visible and clickable
- Text/icon should still be visible

**Task Preview Panels** (if visible in UI):
- Background may be red (inherits variable)
- Content should still be readable

**Rate Limit Bar** (if visible):
- May have red background
- Should still function

These are expected based on the CSS architecture and documented in the contract.

---

### Step 10: Check for Unexpected Issues

Verify these are NOT broken:

- [ ] No console errors in browser DevTools
- [ ] Text is visible (even if contrast is lower)
- [ ] Buttons and links are clickable
- [ ] Layout is not broken or shifted
- [ ] Theme toggle still works
- [ ] No JavaScript errors

If any of these fail, review your CSS changes for typos.

---

### Step 11: Run Linter (Optional)

If the project has CSS linting:

```bash
cd /home/runner/work/github-workflows/github-workflows/frontend
npm run lint
```

CSS changes should not cause linting errors.

---

### Step 12: Commit the Changes

Stop the dev server (Ctrl+C), then commit:

```bash
cd /home/runner/work/github-workflows/github-workflows

# Check what changed
git status
git diff frontend/src/index.css

# Stage the changes
git add frontend/src/index.css

# Commit with descriptive message
git commit -m "Apply red background to application interface

- Update --color-bg-secondary to #FF0000 in light mode
- Update --color-bg-secondary to #FF0000 in dark mode
- Background now persists across navigation and theme switches

Implements FR-001, FR-002, FR-003 from spec"

# Push to remote branch
git push origin copilot/apply-red-background-interface-again
```

---

### Step 13: Verify Remote Build (CI/CD)

If the project has CI/CD:

1. Go to GitHub repository
2. Navigate to Actions tab
3. Find the workflow run for your commit
4. Verify build passes

If build fails, check the logs for errors.

---

## Verification Test Scenarios

### Scenario 1: First-Time User

1. Open application in incognito/private browsing window
2. Navigate to http://localhost:5173 (or deployed URL)
3. **Expected**: Red background visible immediately on load
4. **Result**: ✓ Pass / ✗ Fail

### Scenario 2: Theme Switching

1. Load application in light mode (default)
2. Click theme toggle button to switch to dark mode
3. **Expected**: Background remains red in dark mode
4. Click theme toggle to switch back to light mode
5. **Expected**: Background remains red in light mode
6. **Result**: ✓ Pass / ✗ Fail

### Scenario 3: Page Refresh

1. Load application
2. Interact with UI (if interactive features exist)
3. Press F5 or Ctrl+R to refresh
4. **Expected**: Red background restored immediately
5. **Result**: ✓ Pass / ✗ Fail

### Scenario 4: Navigation (if routes exist)

1. Load application on home route
2. Navigate to another route (if applicable)
3. **Expected**: Red background persists across navigation
4. Use browser back button
5. **Expected**: Red background persists
6. **Result**: ✓ Pass / ✗ Fail

### Scenario 5: Responsive Design

1. Open application on desktop browser
2. Open DevTools responsive mode (Ctrl+Shift+M)
3. Test these viewport sizes:
   - Mobile: 375x667 (iPhone SE)
   - Tablet: 768x1024 (iPad)
   - Desktop: 1920x1080
4. **Expected**: Red background spans full width at all sizes
5. **Result**: ✓ Pass / ✗ Fail

### Scenario 6: Multiple Browsers

Test in at least 2 browsers:

- [ ] Chrome/Edge (Chromium): Red background works
- [ ] Firefox: Red background works
- [ ] Safari (if available): Red background works

---

## Troubleshooting

### Issue: Background is not red

**Symptom**: Background remains gray after changes

**Possible Causes**:
1. CSS file not saved
2. Browser cache showing old CSS
3. Typo in color value

**Solutions**:
```bash
# Verify file was saved
grep "FF0000" frontend/src/index.css
# Should show 2 matches

# Hard refresh browser
# Chrome/Firefox: Ctrl+Shift+R
# Safari: Cmd+Shift+R

# Clear Vite dev server cache
rm -rf frontend/node_modules/.vite
npm run dev
```

---

### Issue: Build fails

**Symptom**: `npm run build` produces errors

**Possible Causes**:
1. Syntax error in CSS (missing semicolon, bracket)
2. Invalid color format

**Solutions**:
```bash
# Check for syntax errors
cd frontend/src
cat index.css | grep -A2 -B2 "color-bg-secondary"

# Verify format exactly matches:
# --color-bg-secondary: #FF0000;
# (Note: uppercase FF, 6 hex digits, semicolon)

# If broken, restore backup
cp index.css.backup index.css
# Then retry the changes carefully
```

---

### Issue: Theme toggle broken

**Symptom**: Clicking theme button doesn't switch modes

**Possible Causes**:
1. Accidentally modified JavaScript/React code
2. CSS syntax broke theme system

**Solutions**:
```bash
# Verify ONLY CSS was changed
git diff

# Should show only 2 lines changed in index.css
# If other files changed, revert them:
git checkout frontend/src/SomeOtherFile.tsx

# If index.css is broken, restore and retry
git checkout frontend/src/index.css
# Then make changes again carefully
```

---

### Issue: Text not visible

**Symptom**: Text appears invisible or very hard to read

**Expected Behavior**: 
- Light mode: Text contrast is low (known issue, documented)
- Dark mode: Text should be clearly visible

**If text is completely invisible**:
```bash
# Verify you didn't accidentally change text color
grep "color-text:" frontend/src/index.css

# Should show:
# --color-text: #24292f;  (light mode)
# --color-text: #e6edf3;  (dark mode)

# If wrong, fix or restore from backup
```

---

### Issue: Components look broken

**Symptom**: Buttons, cards, or panels have weird styling

**Expected Behavior**: Some components inherit red background (theme button, task previews) - this is ACCEPTABLE per spec

**If components are completely broken**:
```bash
# Verify you only changed bg-secondary, not bg
grep "color-bg:" frontend/src/index.css

# Should show TWO variables:
# --color-bg: #ffffff;  (light mode)
# --color-bg: #0d1117;  (dark mode)
# --color-bg-secondary: #FF0000;  (both modes)

# If bg was changed, revert it
```

---

## Rollback Instructions

If you need to revert the changes:

```bash
cd /home/runner/work/github-workflows/github-workflows

# Option 1: Revert the commit
git revert HEAD
git push origin copilot/apply-red-background-interface-again

# Option 2: Manual revert
# Edit frontend/src/index.css and change:
# --color-bg-secondary: #FF0000;  (in :root)
# back to: --color-bg-secondary: #f6f8fa;

# --color-bg-secondary: #FF0000;  (in dark mode)
# back to: --color-bg-secondary: #161b22;

# Then commit the revert
git add frontend/src/index.css
git commit -m "Revert: Remove red background"
git push origin copilot/apply-red-background-interface-again
```

---

## Next Steps

After successful implementation:

1. **Create Pull Request**: Open PR from `copilot/apply-red-background-interface-again` to `main`
2. **Request Review**: Tag reviewers for code review
3. **Run E2E Tests**: If project has automated tests, ensure they pass
4. **Deploy to Staging**: Test in staging environment
5. **Monitor Accessibility**: Track contrast ratio feedback from users
6. **Plan Follow-up**: Consider text color adjustments if accessibility feedback received

---

## Additional Resources

**Related Documentation**:
- Feature Specification: `specs/001-red-background/spec.md`
- Implementation Plan: `specs/001-red-background/plan.md`
- Research Findings: `specs/001-red-background/research.md`
- Data Model: `specs/001-red-background/data-model.md`
- CSS Contract: `specs/001-red-background/contracts/css-changes.md`

**Technical References**:
- [CSS Custom Properties (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [WCAG Contrast Ratio Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [Vite CSS Documentation](https://vitejs.dev/guide/features.html#css)

**Tools**:
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) - Check text contrast ratios
- [Chrome DevTools Color Picker](https://developer.chrome.com/docs/devtools/css/reference/#color-picker) - Verify color values

---

## Summary

This guide covered implementing the red background feature in ~15-20 minutes:

✓ Modified 2 lines of CSS in 1 file  
✓ Tested across theme modes, navigation, and refresh  
✓ Verified build and visual appearance  
✓ Committed and pushed changes  
✓ Documented side effects and known issues

The implementation is complete when all verification tests pass and the red background is visible in both light and dark theme modes across all application screens.
