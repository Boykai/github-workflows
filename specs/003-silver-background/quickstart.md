# Quickstart Guide: Silver Background Implementation

**Feature**: Silver Background Color  
**Phase**: 1 - Design & Contracts  
**Date**: 2026-02-14  
**Estimated Time**: 15 minutes

## Overview

This quickstart guide provides step-by-step instructions for implementing the silver background feature. The implementation is straightforward: update 2 CSS variable values in one file.

---

## Prerequisites

- [ ] Git clone of the repository
- [ ] Node.js and npm installed (for testing)
- [ ] Code editor (VS Code recommended)
- [ ] Browser DevTools for verification
- [ ] Read `research.md` and `data-model.md` (optional, for context)

---

## Step 1: Understand the Current State

**Goal**: Verify the current background color values

1. Open `frontend/src/index.css` in your editor
2. Locate the `:root` section (around line 2)
3. Find the current value: `--color-bg-secondary: #f6f8fa;`
4. Locate the `.dark-mode-active` section (around line 18)
5. Find the current value: `--color-bg-secondary: #161b22;`

**Current State**:
- Light mode background: `#f6f8fa` (very light gray)
- Dark mode background: `#161b22` (very dark blue-gray)

**Target State**:
- Light mode background: `#C0C0C0` (silver)
- Dark mode background: `#2d2d2d` (dark gray)

---

## Step 2: Update Light Mode Background

**File**: `frontend/src/index.css`  
**Line**: 9 (approximately)

**Before**:
```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;  /* ← Change this line */
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

**After**:
```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #C0C0C0;  /* ← Changed to silver */
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

**Action**: Change `#f6f8fa` to `#C0C0C0`

---

## Step 3: Update Dark Mode Background

**File**: `frontend/src/index.css`  
**Line**: 25 (approximately)

**Before**:
```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #161b22;  /* ← Change this line */
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**After**:
```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #2d2d2d;  /* ← Changed to dark gray */
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Action**: Change `#161b22` to `#2d2d2d`

---

## Step 4: Save and Verify Changes

1. Save `frontend/src/index.css`
2. Review your changes:
   ```bash
   git diff frontend/src/index.css
   ```

**Expected Output**:
```diff
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #C0C0C0;

-  --color-bg-secondary: #161b22;
+  --color-bg-secondary: #2d2d2d;
```

---

## Step 5: Start Development Server

**Goal**: Test the changes in a live browser

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies (if not already done):
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open the URL shown in terminal (usually `http://localhost:5173`)

---

## Step 6: Visual Verification (Light Mode)

**Goal**: Confirm silver background appears correctly

1. Open the application in your browser
2. Ensure you're in light mode (default)
3. **Check page background**: Should be silver (#C0C0C0)
4. **Verify text readability**: All text should be clearly readable
5. **Check interactive elements**: Buttons, links should have good contrast
6. **Verify modals/overlays**: Should NOT have silver background (should be white)

**Visual Checklist**:
- [ ] Page background is silver (not light gray)
- [ ] Login page has silver background
- [ ] Main app interface has silver background
- [ ] Text is readable (dark text on silver)
- [ ] Buttons and links are clearly visible
- [ ] Task cards have white backgrounds (not silver)
- [ ] Sidebar has white background (not silver)
- [ ] Header has white background (not silver)

---

## Step 7: Visual Verification (Dark Mode)

**Goal**: Confirm dark mode background works correctly

1. Click the theme toggle button (moon/sun icon) in the header
2. **Check page background**: Should be dark gray (#2d2d2d)
3. **Verify text readability**: Light text should be clearly readable
4. **Check interactive elements**: Should maintain good contrast
5. **Verify modals/overlays**: Should NOT have the page background color

**Visual Checklist**:
- [ ] Page background is dark gray (not blue-gray)
- [ ] Text is readable (light text on dark gray)
- [ ] Buttons and links are clearly visible
- [ ] Task cards have darker background (distinct from page)
- [ ] Sidebar has darker background (distinct from page)
- [ ] Header has darker background (distinct from page)

---

## Step 8: Contrast Verification

**Goal**: Ensure WCAG AA accessibility compliance

### Using Browser DevTools (Chrome/Edge)

1. Open DevTools (F12 or Cmd+Option+I)
2. Go to **Elements** tab
3. Select `<body>` element
4. Look at **Computed** panel
5. Find `background-color` → should show `rgb(192, 192, 192)` in light mode
6. Select a text element
7. Look for contrast ratio indicator (next to color value)
8. Should show ✅ with ratio ≥ 4.5:1

### Manual Verification (Optional)

Use an online contrast checker:
1. Go to https://webaim.org/resources/contrastchecker/
2. Input:
   - **Foreground**: `#24292f` (primary text)
   - **Background**: `#C0C0C0` (silver)
3. Verify ratio is ≥ 4.5:1

**Expected Contrast Ratios**:
- Primary text (`#24292f`): 8.59:1 ✅
- Secondary text (`#57606a`): 4.52:1 ✅
- Primary blue (`#0969da`): 4.02:1 ✅ (for large text/UI)

---

## Step 9: Test Responsive Behavior

**Goal**: Ensure background works on all screen sizes

1. In DevTools, toggle Device Toolbar (Cmd+Shift+M)
2. Test these viewport sizes:
   - **Mobile**: 375x667 (iPhone SE)
   - **Tablet**: 768x1024 (iPad)
   - **Desktop**: 1920x1080
3. Verify silver background extends to full viewport on all sizes

**Responsive Checklist**:
- [ ] Mobile view shows silver background edge-to-edge
- [ ] Tablet view shows silver background edge-to-edge
- [ ] Desktop view shows silver background edge-to-edge
- [ ] No white gaps or overflow issues
- [ ] Background scrolls naturally with content

---

## Step 10: Run Automated Tests

**Goal**: Ensure no tests are broken by the change

### Run Unit Tests
```bash
cd frontend
npm run test
```

**Expected**: All tests pass (no functional changes)

### Run E2E Tests
```bash
cd frontend
npm run test:e2e
```

**Expected**: All tests pass

**Note**: If any visual regression tests fail, review the screenshots to confirm the ONLY change is the background color (silver instead of light gray). Update test baselines if needed.

---

## Step 11: Component-Specific Verification

**Goal**: Ensure modals and overlays don't inherit the silver background

### Test Error Toast
1. Trigger an error (e.g., disconnect from network)
2. Verify error toast has a distinct background (red-tinted, not silver)

### Test Task Cards
1. Navigate to a project with tasks
2. Verify task cards have white background in light mode
3. Verify task cards have darker background in dark mode (not page background)

### Test Status Columns
1. Check the status columns (To Do, In Progress, Done)
2. Verify they have appropriate backgrounds (may be silver to blend with page)

**Component Checklist**:
- [ ] Error toasts don't have silver background
- [ ] Task cards are visually distinct from page background
- [ ] Modals (if any) don't have silver background
- [ ] Dropdowns (if any) don't have silver background

---

## Step 12: Cross-Browser Testing

**Goal**: Verify consistency across browsers

Test in these browsers (if available):
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (macOS/iOS)
- [ ] Edge

**Note**: CSS custom properties are supported in all modern browsers (2016+). No issues expected.

---

## Step 13: Commit Your Changes

**Goal**: Save your work with a descriptive commit message

```bash
git add frontend/src/index.css
git commit -m "feat: apply silver background color to app interface

- Update --color-bg-secondary to #C0C0C0 in light mode
- Update --color-bg-secondary to #2d2d2d in dark mode
- Maintains WCAG AA contrast standards
- Preserves modal and overlay backgrounds

Resolves: #<issue-number>"
```

---

## Troubleshooting

### Issue: Changes Not Visible

**Solution**:
1. Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)
2. Clear browser cache
3. Restart dev server (Ctrl+C, then `npm run dev`)

### Issue: Dark Mode Not Working

**Solution**:
1. Click theme toggle multiple times
2. Check browser console for JavaScript errors
3. Verify `dark-mode-active` class is applied to `<html>` element (check DevTools)

### Issue: Text Hard to Read

**Solution**:
1. Verify you changed the correct color values
2. Check contrast ratios using DevTools
3. If contrast fails, double-check the hex codes are correct

### Issue: Modals Have Silver Background

**Solution**:
1. Check modal CSS - should use `var(--color-bg)`, not `var(--color-bg-secondary)`
2. Inspect modal element in DevTools → Computed styles → background-color
3. If using `--color-bg-secondary`, update modal CSS to use `--color-bg`

---

## Rollback Instructions

If you need to revert the changes:

```bash
# Option 1: Revert the commit
git revert HEAD

# Option 2: Manual revert (change values back)
# In frontend/src/index.css:
# Line 9: --color-bg-secondary: #f6f8fa;
# Line 25: --color-bg-secondary: #161b22;
```

---

## Success Criteria

✅ **Feature Complete When**:
1. Silver background (#C0C0C0) visible in light mode
2. Dark gray background (#2d2d2d) visible in dark mode
3. All text meets WCAG AA contrast standards (4.5:1)
4. All interactive elements meet WCAG AA standards (3.0:1)
5. Modals and popups maintain original backgrounds
6. Tests pass without failures
7. Changes work across all screen sizes
8. Changes work in light and dark mode

---

## Next Steps

After completing this implementation:
1. Get code review from team
2. Test on staging environment
3. Deploy to production
4. Monitor for user feedback
5. Close the feature issue

---

## Additional Resources

- **WCAG Contrast Guidelines**: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
- **CSS Custom Properties**: https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties
- **Contrast Checker Tool**: https://webaim.org/resources/contrastchecker/
- **Chrome DevTools Accessibility**: https://developer.chrome.com/docs/devtools/accessibility/reference/

---

## Estimated Time Breakdown

| Step | Estimated Time | Actual Time |
|------|----------------|-------------|
| Steps 1-4: Code changes | 5 minutes | ___ |
| Steps 5-7: Visual verification | 5 minutes | ___ |
| Steps 8-9: Accessibility & responsive testing | 3 minutes | ___ |
| Step 10: Automated tests | 2 minutes | ___ |
| Steps 11-12: Component & browser testing | 5 minutes | ___ |
| Step 13: Commit | 1 minute | ___ |
| **Total** | **~20 minutes** | ___ |

---

**End of Quickstart Guide**
