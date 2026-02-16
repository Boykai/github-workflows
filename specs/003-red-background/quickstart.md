# Quickstart Guide: Red Background Color

**Branch**: `copilot/apply-red-background-color-again` | **Date**: 2026-02-16 | **Spec**: [spec.md](./spec.md)

## Overview

This quickstart guide provides step-by-step instructions for implementing the red background color feature. The implementation is straightforward: modify 3 CSS custom property values in one file.

**Estimated Time**: 15-20 minutes (including testing)  
**Difficulty**: Easy  
**Prerequisites**: Basic CSS and Git knowledge

---

## Step 1: Verify Current Branch

**Time**: 1 minute

Ensure you're working on the correct feature branch.

```bash
git status
```

**Expected Output**: You should be on branch `copilot/apply-red-background-color-again`

**If not**:
```bash
git fetch origin
git checkout copilot/apply-red-background-color-again
```

---

## Step 2: Open Target File

**Time**: 1 minute

Open the CSS file containing color custom properties.

```bash
# From repository root
code frontend/src/index.css
# or your preferred editor
```

**File Location**: `frontend/src/index.css`  
**Lines to Modify**: 9, 11, 25

---

## Step 3: Modify Light Mode Background Color

**Time**: 1 minute

Update line 9 to change the light mode background color to red.

**Current Line 9**:
```css
  --color-bg-secondary: #f6f8fa;
```

**New Line 9**:
```css
  --color-bg-secondary: #ff0000;
```

**Why**: Changes page background from light gray to bright red for light mode

---

## Step 4: Modify Light Mode Text Color

**Time**: 1 minute

Update line 11 to change text color to white for contrast on red background.

**Current Line 11**:
```css
  --color-text: #24292f;
```

**New Line 11**:
```css
  --color-text: #ffffff;
```

**Why**: White text provides sufficient contrast on red background (WCAG AA compliance)

---

## Step 5: Modify Dark Mode Background Color

**Time**: 1 minute

Update line 25 to change the dark mode background color to dark red.

**Current Line 25**:
```css
  --color-bg-secondary: #161b22;
```

**New Line 25**:
```css
  --color-bg-secondary: #8b0000;
```

**Why**: Dark red maintains red branding in dark mode while preventing eye strain

---

## Step 6: Save and Verify Syntax

**Time**: 1 minute

Save the file and verify no syntax errors were introduced.

1. Save file (Ctrl+S / Cmd+S)
2. Check for editor warnings (should be none)
3. Verify lowercase hex values (codebase convention)

**Quick Check**:
- All hex values lowercase? ✅
- All lines end with semicolon? ✅
- No typos in property names? ✅

---

## Step 7: Start Development Server

**Time**: 2 minutes

Start the frontend development server to preview changes.

```bash
cd frontend
npm run dev
```

**Expected Output**:
```
VITE v5.x.x  ready in XXX ms
➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

**If errors**: Check that dependencies are installed (`npm install`)

---

## Step 8: Visual Verification - Light Mode

**Time**: 3 minutes

Open the application in your browser and verify red background.

1. Open http://localhost:5173/ in Chrome/Firefox/Safari
2. Observe page background color
3. Navigate to different sections

**Expected Results**:
- ✅ Page background is bright red (#ff0000)
- ✅ Text is white and readable
- ✅ Red background visible on all pages
- ✅ UI components (buttons, panels) may also be red

**Screenshot**: Take a screenshot for documentation

---

## Step 9: Visual Verification - Dark Mode

**Time**: 2 minutes

Toggle to dark mode and verify dark red background.

1. Find theme toggle button (usually in header/settings)
2. Switch to dark mode
3. Observe background color change

**Expected Results**:
- ✅ Page background is dark red (#8b0000)
- ✅ Text remains readable with good contrast
- ✅ Dark red less bright than light mode (appropriate for low-light)
- ✅ Theme toggle works smoothly

**Screenshot**: Take a screenshot for documentation

---

## Step 10: Accessibility Check

**Time**: 3 minutes

Verify text contrast meets accessibility standards.

### Using Browser DevTools

1. Right-click on text → Inspect
2. Open "Accessibility" tab in DevTools
3. Check "Contrast" section

**Expected**:
- White on red: ~4.0:1 ratio
- Acceptable for large text (3:1 min)
- Marginal for normal text (4.5:1 ideal)

### Using Online Tool (Optional)

1. Visit https://webaim.org/resources/contrastchecker/
2. Foreground: #ffffff (white)
3. Background: #ff0000 (red)
4. Check results

**Pass Criteria**: At least 3:1 for large text, aim for 4.5:1 for normal text

---

## Step 11: Component Usability Check

**Time**: 2 minutes

Verify all UI components remain functional and visible.

### Test Checklist

- [ ] Click buttons (do they respond?)
- [ ] Type in input fields (is text visible?)
- [ ] Hover over interactive elements (hover states visible?)
- [ ] Open any modals/dialogs (do they stand out from background?)
- [ ] Navigate between sections (does red persist?)

**Expected**: All elements remain usable, though some may have red backgrounds

**Issues?**: If buttons/panels are not visible due to red backgrounds, document for follow-up (may need additional CSS adjustments)

---

## Step 12: Commit Changes

**Time**: 2 minutes

Commit your changes to the feature branch.

```bash
git add frontend/src/index.css
git commit -m "Apply red background color to main application layout

- Update --color-bg-secondary to #ff0000 (light mode)
- Update --color-bg-secondary to #8b0000 (dark mode)
- Update --color-text to #ffffff for contrast (light mode)
- Fulfills FR-001, FR-002, FR-003, FR-005"

git push origin copilot/apply-red-background-color-again
```

**Verify**: Check that commit appears on GitHub PR

---

## Troubleshooting

### Issue: Background Not Changing

**Symptom**: Page still shows gray background after changes

**Solutions**:
1. Hard refresh browser (Ctrl+Shift+R / Cmd+Shift+R)
2. Clear browser cache
3. Verify CSS variable names match exactly (no typos)
4. Check browser DevTools Console for CSS errors

### Issue: Text Not Readable

**Symptom**: Text too dark or hard to read on red background

**Solutions**:
1. Verify `--color-text: #ffffff;` on line 11
2. Check if some text uses `--color-text-secondary` (may need adjustment)
3. Increase font-weight if contrast still insufficient
4. Consider updating line 13 to `--color-text-secondary: #f0f0f0;`

### Issue: Components Invisible

**Symptom**: Buttons/panels blend into red background

**Solutions**:
1. Expected if they use `--color-bg-secondary`
2. May need to adjust specific components to use `--color-bg` instead
3. Add borders or shadows to improve visibility
4. Document for follow-up if extensive changes needed

### Issue: Red Too Bright

**Symptom**: Red background causes eye strain

**Solutions**:
1. Verify using correct values (#ff0000 light, #8b0000 dark)
2. Consider slightly darker red if brightness is problematic
3. Add user feedback about brightness
4. May need to adjust color values based on user testing

---

## Testing Checklist

Before marking this feature as complete, verify all requirements:

### User Story 1: View Application with Red Background (P1)

- [ ] **US1-AC1**: Background color is red (#ff0000 or similar) on main page
- [ ] **US1-AC2**: Red background visible across all primary screens/pages

### User Story 2: Readable Content on Red Background (P2)

- [ ] **US2-AC1**: All text has sufficient contrast and is readable
- [ ] **US2-AC2**: UI elements remain visible and usable on red background

### Functional Requirements

- [ ] **FR-001**: Red background applied to main application container ✅
- [ ] **FR-002**: Red background visible and consistent across all screens ✅
- [ ] **FR-003**: Text contrast meets WCAG AA standards (manual check)
- [ ] **FR-004**: Interactive elements preserve visibility and usability ✅
- [ ] **FR-005**: Red background applies to both light and dark modes ✅

### Cross-Cutting Concerns

- [ ] Theme toggle works correctly
- [ ] No browser console errors
- [ ] Performance not degraded
- [ ] Changes committed and pushed to feature branch

---

## Next Steps

1. **Request Review**: Ask team member to review visual changes
2. **User Testing**: Get feedback from stakeholders on red background
3. **Accessibility Audit**: Run full accessibility scan with tools like axe DevTools
4. **Edge Cases**: Test with various screen sizes, browsers, zoom levels
5. **Documentation**: Update any user-facing docs mentioning color scheme

---

## Additional Notes

- **Rollback**: If issues arise, revert `frontend/src/index.css` to previous commit
- **Iteration**: Color values can be adjusted based on feedback (e.g., darker/lighter red)
- **Extensions**: Future work could add color customization settings for users
- **Browser Support**: CSS variables supported in all modern browsers (no fallback needed)

---

## File Summary

**Modified Files**: 1  
**Lines Changed**: 3  
**New Files**: 0  
**Deleted Files**: 0

**Changes**:
```diff
frontend/src/index.css:
  Line 9:  --color-bg-secondary: #f6f8fa → #ff0000
  Line 11: --color-text: #24292f → #ffffff
  Line 25: --color-bg-secondary: #161b22 → #8b0000
```

**Total Implementation Time**: 15-20 minutes  
**Total Testing Time**: 10-15 minutes  
**Overall Estimate**: 25-35 minutes

---

## Success Criteria

✅ **Feature Complete** when:

1. Red background visible on all screens (both themes)
2. Text remains readable with sufficient contrast
3. All UI components remain functional
4. No accessibility violations
5. Changes committed to feature branch
6. Manual testing completed successfully

🎉 **Congratulations!** You've successfully implemented the red background color feature.
