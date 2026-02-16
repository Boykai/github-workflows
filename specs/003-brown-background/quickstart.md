# Quickstart Guide: Apply Brown Background Color to App Interface

**Feature**: 003-brown-background  
**Branch**: copilot/update-background-color-brown  
**Created**: 2026-02-16  
**Estimated Time**: 10-15 minutes

## Purpose

This guide provides step-by-step instructions for implementing the brown background color feature. Follow these steps in order to apply the brown background to the application interface while maintaining accessibility and theme functionality.

---

## Prerequisites

- [ ] Git repository cloned locally
- [ ] Branch `copilot/update-background-color-brown` checked out
- [ ] Code editor (VS Code, Sublime, etc.) installed
- [ ] Web browser (Chrome, Firefox, or Safari) for testing
- [ ] Read access to feature specification (`specs/003-brown-background/spec.md`)

---

## Implementation Steps

### Step 1: Locate the CSS File

**Duration**: 1 minute

**Action**: Navigate to the CSS theming file that contains the color variables.

```bash
cd /home/runner/work/github-workflows/github-workflows
```

Open `frontend/src/index.css` in your code editor.

**Verification**: Confirm the file contains `:root` and `html.dark-mode-active` selectors with CSS custom properties.

---

### Step 2: Update Light Mode Background Color

**Duration**: 1 minute

**Action**: Modify the `--color-bg-secondary` variable in the `:root` selector.

**File**: `frontend/src/index.css`  
**Line**: 9

**Change**:
```diff
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #8B5E3C;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

**Verification**: 
- Line 9 now reads: `--color-bg-secondary: #8B5E3C;`
- Semicolon and spacing preserved
- No other lines modified

---

### Step 3: Update Dark Mode Background Color

**Duration**: 1 minute

**Action**: Modify the `--color-bg-secondary` variable in the `html.dark-mode-active` selector.

**File**: `frontend/src/index.css`  
**Line**: 25

**Change**:
```diff
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
-  --color-bg-secondary: #161b22;
+  --color-bg-secondary: #8B5E3C;
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Verification**: 
- Line 25 now reads: `--color-bg-secondary: #8B5E3C;`
- Semicolon and spacing preserved
- No other lines modified

---

### Step 4: Save the File

**Duration**: < 1 minute

**Action**: Save the `frontend/src/index.css` file.

**Verification**: File saved successfully with no syntax errors in editor.

---

### Step 5: Start Development Server (if not already running)

**Duration**: 1 minute

**Action**: Start the frontend development server to see live changes.

```bash
cd frontend
npm run dev
```

**Expected Output**: Vite dev server starts on `http://localhost:5173` (or similar port).

**Verification**: Server runs without errors. Browser opens or navigate manually to the local URL.

---

### Step 6: Visual Verification - Light Mode

**Duration**: 2 minutes

**Action**: Open the application in your browser and verify the brown background appears in light mode.

**Checklist**:
- [ ] Open `http://localhost:5173` in Chrome
- [ ] Main page background displays brown color (not gray)
- [ ] Brown background visible on all screens (login, main app, etc.)
- [ ] Text is readable against brown background
- [ ] UI elements (buttons, cards) display properly with brown backgrounds

**Verification Method**: Inspect element in DevTools:
1. Right-click on page background
2. Select "Inspect"
3. Check Computed styles
4. Verify `--color-bg-secondary` resolves to `rgb(139, 94, 60)` (equivalent of #8B5E3C)

---

### Step 7: Visual Verification - Dark Mode

**Duration**: 2 minutes

**Action**: Toggle to dark mode and verify brown background persists.

**Checklist**:
- [ ] Click theme toggle button (sun/moon icon in header)
- [ ] Dark mode activates
- [ ] Background remains brown (not dark gray)
- [ ] Text color changes to light (for contrast)
- [ ] Brown background still visible on all screens

**Verification**: Inspect element and confirm `--color-bg-secondary` still resolves to `rgb(139, 94, 60)`.

---

### Step 8: Modal Verification

**Duration**: 2 minutes

**Action**: Verify that modal dialogs and popups do NOT have brown backgrounds.

**Checklist**:
- [ ] Trigger a modal or popup in the application (if available)
- [ ] Modal background should be white (light mode) or dark gray (dark mode)
- [ ] Modal should NOT be brown
- [ ] Modal stands out visually from the brown page background

**Note**: If no modals are available in the UI, this can be verified in the code by checking that modal components use `var(--color-bg)` instead of `var(--color-bg-secondary)`.

---

### Step 9: Responsive Verification

**Duration**: 2 minutes

**Action**: Test the brown background across different screen sizes.

**Checklist**:
- [ ] Open Chrome DevTools (F12)
- [ ] Click "Toggle device toolbar" (Ctrl+Shift+M / Cmd+Shift+M)
- [ ] Test Desktop view (1920x1080): Brown background present ✅
- [ ] Test Tablet view (768x1024): Brown background present ✅
- [ ] Test Mobile view (375x667): Brown background present ✅

**Verification**: Brown background adapts responsively without layout issues.

---

### Step 10: Accessibility Check

**Duration**: 3 minutes

**Action**: Verify text contrast meets WCAG AA standards.

**Method 1 - Chrome DevTools**:
1. Right-click on text element → Inspect
2. Check "Contrast" section in DevTools
3. Verify contrast ratio ≥4.5:1 for normal text

**Method 2 - Online Tool**:
1. Visit WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
2. Foreground: Enter text color (e.g., #ffffff for white text)
3. Background: #8B5E3C
4. Verify WCAG AA Pass

**Expected Results**:
- White text (#ffffff) on brown (#8B5E3C): 5.2:1 ✅
- Light gray text (#e6edf3) on brown (#8B5E3C): 4.8:1 ✅

**Action if Failing**: If any text has insufficient contrast, adjust text color in CSS variables or component styles.

---

### Step 11: Cross-Browser Testing (Optional but Recommended)

**Duration**: 3 minutes

**Action**: Test in multiple browsers if available.

**Checklist**:
- [ ] Chrome: Brown background displays correctly
- [ ] Firefox: Brown background displays correctly
- [ ] Safari: Brown background displays correctly (if on macOS)

**Note**: CSS variables are supported in all modern browsers, so issues are unlikely.

---

### Step 12: Commit Changes

**Duration**: 1 minute

**Action**: Commit the CSS changes to the branch.

```bash
git add frontend/src/index.css
git commit -m "Apply brown background color (#8B5E3C) to app interface

- Update --color-bg-secondary in light mode (line 9)
- Update --color-bg-secondary in dark mode (line 25)
- Satisfies FR-001, FR-003, FR-005, FR-006, FR-007
"
```

**Verification**: Commit created successfully with descriptive message.

---

## Rollback Instructions

If the brown background needs to be reverted:

**File**: `frontend/src/index.css`

**Revert Line 9** (light mode):
```css
--color-bg-secondary: #f6f8fa;  /* Back to light gray */
```

**Revert Line 25** (dark mode):
```css
--color-bg-secondary: #161b22;  /* Back to dark gray */
```

Save the file and the application will return to the original background colors.

---

## Troubleshooting

### Issue: Brown background not appearing

**Possible Causes**:
- Dev server not running or not detecting changes
- Browser cache serving old CSS

**Solutions**:
1. Hard refresh browser (Ctrl+Shift+R / Cmd+Shift+R)
2. Restart dev server: `npm run dev`
3. Clear browser cache

### Issue: Text is unreadable on brown background

**Possible Causes**:
- Dark text (#24292f) used in light mode against brown background
- Insufficient contrast ratio

**Solutions**:
1. Check which text color is being used
2. Adjust text color to lighter shade (e.g., #ffffff or #e6edf3)
3. Update `--color-text` or component-specific text colors

### Issue: Modals have brown background

**Possible Causes**:
- Modal component uses `var(--color-bg-secondary)` instead of `var(--color-bg)`

**Solutions**:
1. Identify the modal CSS selector
2. Change `background: var(--color-bg-secondary)` to `background: var(--color-bg)`
3. Alternatively, use explicit color like `background: #ffffff` for modals

---

## Post-Implementation Checklist

- [ ] Both CSS lines updated (light mode line 9, dark mode line 25)
- [ ] Visual verification passed in light and dark modes
- [ ] Modal verification passed (modals not brown)
- [ ] Responsive verification passed (desktop, tablet, mobile)
- [ ] Accessibility verification passed (contrast ≥4.5:1)
- [ ] Cross-browser testing passed (at least 2 browsers)
- [ ] Changes committed to branch
- [ ] No console errors or warnings introduced

---

## Success Criteria Verification

Map your testing results to the specification success criteria:

| Success Criterion | Verification Method | Status |
|-------------------|---------------------|--------|
| **SC-001**: 100% of main screens display brown #8B5E3C | Visual inspection of all pages | [ ] Pass |
| **SC-002**: Text contrast ≥4.5:1 | WebAIM checker or DevTools | [ ] Pass |
| **SC-003**: Consistent across 3 browsers, 3 devices | Cross-browser + responsive testing | [ ] Pass |
| **SC-004**: Zero modals with brown background | Modal inspection | [ ] Pass |
| **SC-005**: Interface feels warmer and appealing | Subjective user feedback | [ ] N/A (post-deployment) |

---

## Next Steps

After completing this quickstart:

1. **Push to remote**: `git push origin copilot/update-background-color-brown`
2. **Open PR**: Create pull request from feature branch to main
3. **Request review**: Tag team members for visual review
4. **Deploy**: Merge PR to deploy brown background to production
5. **Monitor**: Collect user feedback on visual appeal (SC-005)

---

## Estimated Total Time: 10-15 minutes

**Breakdown**:
- Steps 1-4 (Implementation): 3 minutes
- Steps 5-7 (Basic verification): 5 minutes
- Steps 8-11 (Thorough testing): 7 minutes
- Step 12 (Commit): 1 minute

**Minimum Time** (skip optional cross-browser): ~10 minutes  
**Recommended Time** (full verification): ~15 minutes

---

**Guide Version**: 1.0  
**Last Updated**: 2026-02-16  
**Maintained By**: speckit.plan agent
