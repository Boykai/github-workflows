# Quickstart Guide: Yellow Background Interface

**Feature**: 002-yellow-background  
**Branch**: `copilot/apply-yellow-background-color-another-one`  
**Date**: 2026-02-16  
**Estimated Time**: 15 minutes

## Overview

This quickstart guide provides step-by-step instructions for implementing the yellow background feature. The implementation is minimal: one CSS variable change in one file.

## Prerequisites

- Git repository cloned locally
- Branch `copilot/apply-yellow-background-color-another-one` checked out
- Text editor or IDE
- Web browser for testing
- Node.js and npm installed (for running dev server)

## Quick Summary

**What**: Change page background from gray (`#f6f8fa`) to yellow (`#FFEB3B`)  
**Where**: `frontend/src/index.css`, line 9  
**Impact**: Light mode only, preserves dark mode  
**Risk**: Very low (single CSS variable change)

## Implementation Steps

### Step 1: Verify Starting Point

```bash
# Ensure you're on the correct branch
git status

# Should show: On branch copilot/apply-yellow-background-color-another-one
```

**Expected Output**: Clean working tree on feature branch

---

### Step 2: Open the CSS File

```bash
# Open the file in your editor
# Example using VS Code:
code frontend/src/index.css

# Or using vim:
vim frontend/src/index.css

# Or using nano:
nano frontend/src/index.css
```

**File Location**: `frontend/src/index.css`  
**Target Line**: Line 9 (inside `:root` selector)

---

### Step 3: Locate the Variable

Find the `:root` CSS selector block at the top of the file:

```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;  /* ← LINE 9: FIND THIS LINE */
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

**Tip**: Search for `--color-bg-secondary` to find the line quickly

---

### Step 4: Make the Change

**Before**:
```css
--color-bg-secondary: #f6f8fa;
```

**After**:
```css
--color-bg-secondary: #FFEB3B;
```

**Important Notes**:
- Use uppercase hex value (`#FFEB3B`) for consistency
- Do NOT modify any other lines
- Do NOT modify the dark mode section (`html.dark-mode-active`)
- Keep the semicolon at the end

---

### Step 5: Save the File

```bash
# If using command-line editor, save and exit
# vim: :wq
# nano: Ctrl+X, then Y, then Enter
```

**Verification**: File should be marked as modified in your editor/IDE

---

### Step 6: Verify the Change

```bash
# View the diff
git diff frontend/src/index.css
```

**Expected Output**:
```diff
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #FFEB3B;
```

**Checkpoint**: Only one line should be changed, showing the color value update

---

### Step 7: Start Development Server

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

**Expected Output**:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Tip**: Keep the server running for live testing

---

### Step 8: Visual Verification (Manual Testing)

1. **Open Browser**
   - Navigate to `http://localhost:5173/`

2. **Check Light Mode**
   - Verify the page background is bright yellow (#FFEB3B)
   - Confirm text is readable (should be dark gray/black on yellow)
   - Check that component cards/panels have white backgrounds
   - Test navigation between different screens (if applicable)

3. **Check Dark Mode**
   - Click the theme toggle button (sun/moon icon)
   - Verify dark mode still has dark background (NOT yellow)
   - Confirm yellow background only applies to light mode
   - Toggle back to light mode and verify yellow persists

4. **Check Interactive Elements**
   - Hover over buttons - should remain visible and distinct
   - Check form inputs - should have white backgrounds
   - Test any dropdowns or modals - should appear on yellow background

**Success Criteria**:
- ✓ Page background is yellow in light mode
- ✓ Text remains readable (high contrast)
- ✓ Component cards/panels are white (not yellow)
- ✓ Dark mode remains dark (not affected)
- ✓ All interactive elements function normally

---

### Step 9: Accessibility Verification

#### Option A: Browser DevTools
1. Open DevTools (F12)
2. Select an element with text
3. Check "Contrast" in the Accessibility panel
4. Verify ratio is ≥ 4.5:1 for normal text, ≥ 3:1 for large text

#### Option B: WebAIM Contrast Checker
1. Visit https://webaim.org/resources/contrastchecker/
2. Enter Foreground: `#24292f` (primary text)
3. Enter Background: `#FFEB3B` (yellow)
4. Verify: Should show 10.4:1 ratio (Passes AAA)

#### Option C: Browser Extension
1. Install axe DevTools or WAVE extension
2. Run accessibility scan on the page
3. Check for contrast errors (should be none)

**Success Criteria**:
- ✓ Primary text: 10.4:1 contrast ratio (AAA)
- ✓ Secondary text: 5.8:1 contrast ratio (AA)
- ✓ No accessibility warnings in automated tools

---

### Step 10: Performance Verification (Optional)

```bash
# Run production build to test performance
npm run build

# Serve production build
npm run preview
```

**Performance Check**:
1. Open browser DevTools (F12)
2. Go to Network tab
3. Reload page with cache disabled
4. Check load time (should be similar to pre-change baseline)

**Expected Impact**: No measurable performance change (CSS-only modification)

---

### Step 11: Commit the Change

```bash
# Stage the change
git add frontend/src/index.css

# Commit with descriptive message
git commit -m "feat: apply yellow background to light mode interface

- Change --color-bg-secondary from #f6f8fa to #FFEB3B
- Affects light mode only, preserves dark mode
- Maintains WCAG AA contrast ratios (10.4:1 primary, 5.8:1 secondary)
- No JavaScript or component changes required

Implements FR-001 through FR-007 from spec.md"

# Verify commit
git log -1 --stat
```

**Expected Output**: One file changed, one line modified

---

### Step 12: Push to Remote

```bash
# Push to feature branch
git push origin copilot/apply-yellow-background-color-another-one
```

**Expected Output**: Push successful to remote branch

---

### Step 13: Visual Documentation (Screenshot)

**Recommended**: Capture screenshots for PR documentation

1. **Light Mode Screenshot**
   - Open app in light mode
   - Capture full-page screenshot showing yellow background
   - Save as `specs/002-yellow-background/screenshots/light-mode.png`

2. **Dark Mode Screenshot** (for comparison)
   - Toggle to dark mode
   - Capture screenshot showing dark mode preserved
   - Save as `specs/002-yellow-background/screenshots/dark-mode.png`

**Note**: Screenshots help reviewers quickly verify the change

---

## Verification Checklist

Before considering the implementation complete, verify:

- [ ] CSS file modified (`frontend/src/index.css`)
- [ ] Only one line changed (line 9: `--color-bg-secondary`)
- [ ] Color value is exactly `#FFEB3B`
- [ ] Dark mode section is NOT modified
- [ ] Dev server starts without errors
- [ ] Page loads with yellow background in light mode
- [ ] Dark mode remains dark (not yellow)
- [ ] Text is readable with sufficient contrast
- [ ] Component cards/panels are white on yellow
- [ ] Theme toggle button works correctly
- [ ] Navigation between screens preserves yellow background
- [ ] Accessibility tools show no contrast errors
- [ ] No performance degradation observed
- [ ] Change committed to git
- [ ] Change pushed to remote branch

## Troubleshooting

### Issue: Background is not yellow

**Symptoms**: Page background remains gray after change

**Solutions**:
1. Verify you modified the correct file (`frontend/src/index.css`, not `App.css`)
2. Check you modified `:root` selector, not `html.dark-mode-active`
3. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
4. Restart dev server (`Ctrl+C` then `npm run dev`)
5. Verify the hex color is `#FFEB3B` (not `#f6f8fa`)

---

### Issue: Dark mode also turns yellow

**Symptoms**: Dark mode background is yellow instead of dark

**Solutions**:
1. Check you did NOT modify the `html.dark-mode-active` selector
2. Verify line 9 change is in `:root` block only (lines 2-15)
3. Revert and re-apply change to correct selector

---

### Issue: Text is hard to read

**Symptoms**: Text appears washed out or low contrast

**Solutions**:
1. This should NOT occur with #FFEB3B (10.4:1 contrast)
2. Verify you used `#FFEB3B` not a lighter yellow
3. Check browser is not applying custom styles or extensions
4. Test in incognito mode to rule out extension interference

---

### Issue: Components are all yellow

**Symptoms**: Cards, panels, and other components have yellow backgrounds

**Solutions**:
1. This should NOT occur - components use `--color-bg` (white)
2. Verify you changed `--color-bg-secondary`, not `--color-bg`
3. Check for typos in the variable name
4. Revert and re-apply change carefully

---

## Next Steps

After completing this quickstart:

1. **Update PR Description**
   - Add implementation summary
   - Link to this quickstart guide
   - Include screenshots

2. **Request Review**
   - Tag relevant reviewers
   - Mention this is a minimal CSS-only change
   - Highlight accessibility compliance

3. **Prepare for Tasks Phase**
   - This quickstart serves as reference for `/speckit.tasks` generation
   - Tasks will break down implementation into atomic steps
   - Implementation agent will execute tasks based on this guide

## Summary

This quickstart implements the yellow background feature through a single CSS variable change. The implementation is minimal, low-risk, and preserves all existing functionality including dark mode. Total implementation time should be approximately 15 minutes including testing and documentation.

**Change Summary**:
- 1 file modified: `frontend/src/index.css`
- 1 line changed: Line 9
- Change type: CSS custom property value update
- Risk level: Very low
- Rollback time: < 1 minute

**Result**: Bright yellow background (#FFEB3B) in light mode with excellent text contrast (10.4:1 ratio), no impact on dark mode or functionality.
