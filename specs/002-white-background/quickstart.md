# Quickstart Guide: White Background Interface

**Feature**: 002-white-background  
**Date**: 2026-02-16  
**Estimated Time**: 15-30 minutes  
**Difficulty**: Beginner

## Overview

This guide walks you through implementing a consistent white background across the entire application interface. The implementation is straightforward: update a single CSS custom property value.

## Prerequisites

- Git repository cloned
- Node.js and npm installed
- Basic understanding of CSS custom properties (CSS variables)
- Text editor or IDE

## Architecture Context

The application uses CSS custom properties (variables) defined in `frontend/src/index.css` for centralized theme management. All components reference these variables, creating a single source of truth for colors.

**Key Variables**:
- `--color-bg`: Primary background color (already white)
- `--color-bg-secondary`: Secondary surfaces, cards, columns (currently light gray)

**Component Inheritance**: Over 20 components reference these variables, so changing the variable values automatically updates the entire application.

## Step-by-Step Implementation

### Step 1: Verify Current State

**Action**: Open the application in a browser to see current styling

```bash
cd frontend
npm install  # If not already done
npm run dev
```

**Expected**: Application loads with light gray secondary backgrounds (columns, buttons)

**Screenshot Checkpoint**: Take a screenshot of the current interface for comparison

### Step 2: Open CSS File

**Action**: Navigate to and open the global styles file

```bash
# Path: frontend/src/index.css
```

**Expected**: File contains `:root` selector with CSS custom properties

### Step 3: Locate Color Variables

**Action**: Find the `:root` selector (should be at the top of the file)

```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;           /* Line 8 */
  --color-bg-secondary: #f6f8fa; /* Line 9 - THIS IS WHAT WE'LL CHANGE */
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

### Step 4: Update Secondary Background

**Action**: Change line 9 from `#f6f8fa` to `#FFFFFF`

**Before**:
```css
--color-bg-secondary: #f6f8fa;
```

**After**:
```css
--color-bg-secondary: #FFFFFF;
```

**⚠️ Important**: 
- Use uppercase `#FFFFFF` (not lowercase `#ffffff`) per specification
- Keep the semicolon at the end
- Don't change any other lines

### Step 5: Optional Consistency Update

**Action**: Update line 8 to use uppercase for consistency (optional)

**Before**:
```css
--color-bg: #ffffff;
```

**After**:
```css
--color-bg: #FFFFFF;
```

**Note**: This is purely stylistic - the color value is identical.

### Step 6: Save File

**Action**: Save `frontend/src/index.css`

**Expected**: No syntax errors in your editor

### Step 7: Verify Hot Reload

**Action**: Check if the browser automatically reloaded (Vite hot module replacement)

**Expected**: 
- Browser should refresh automatically
- If not, manually refresh the page

### Step 8: Visual Verification - Main Interface

**Action**: Inspect the main application interface

**Checklist**:
- [ ] Body background is white
- [ ] Header background is white
- [ ] Sidebar background is white
- [ ] Status columns are white (previously light gray)
- [ ] Task cards remain white with visible borders
- [ ] Chat section background is white

**Debugging**: If something looks wrong:
- Check browser console for CSS errors
- Verify the file saved correctly
- Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)

### Step 9: Test Navigation Transitions

**Action**: Navigate between different screens/sections

**Test Cases**:
1. Switch between different projects in the sidebar
2. Click on different task cards
3. Perform any navigation actions available

**Expected**:
- [ ] No background color flashing
- [ ] Smooth transitions
- [ ] Consistent white background maintained

### Step 10: Verify Text Readability

**Action**: Check that all text is still readable against white background

**Areas to Check**:
- [ ] Main heading text
- [ ] Body text in chat area
- [ ] Task card text
- [ ] Sidebar text
- [ ] Button labels
- [ ] Status badges

**Expected**: All text should have high contrast and be easily readable

**Known Good**: The existing text colors (dark grays and blues) have excellent contrast ratios against white (>4.5:1).

### Step 11: Test Interactive Elements

**Action**: Hover over and interact with buttons and other elements

**Elements to Test**:
- [ ] Theme toggle button
- [ ] Logout button
- [ ] Project selector dropdown
- [ ] Task cards (hover effect)
- [ ] Any other interactive elements

**Expected**:
- Hover states still visible (may be more subtle)
- Elements remain distinguishable from background
- Borders provide adequate separation

### Step 12: Check Border Visibility

**Action**: Verify that borders between components are visible

**Critical Borders**:
- [ ] Header bottom border
- [ ] Sidebar right border
- [ ] Task card borders
- [ ] Column borders (if applicable)

**Potential Issue**: If borders appear too faint, they may need darkening (see Troubleshooting below)

### Step 13: Test Edge Cases

**Action**: Test less common UI states

**Test Cases**:
1. Loading state (refresh page, watch spinner)
2. Error state (if you can trigger one)
3. Empty state (project with no tasks)
4. Modal/dialog (if applicable to your test scenario)

**Expected**:
- Loading spinner displays on white background
- Error messages maintain red-tinted backgrounds (intentional)
- Empty states readable on white

## Verification Summary

### Success Criteria Checklist

From the specification, verify:

- [ ] **SC-001**: All screens show white background consistently
- [ ] **SC-002**: Text contrast meets WCAG standards (visual inspection)
- [ ] **SC-003**: No background flashing during navigation
- [ ] **SC-005**: Modals/dialogs use white background (if tested)

### Visual Comparison

**Before**: Light gray (#f6f8fa) secondary backgrounds  
**After**: Pure white (#FFFFFF) throughout

Take a screenshot and compare with your "before" screenshot from Step 1.

## Troubleshooting

### Issue: Borders Too Faint

**Symptom**: Component borders barely visible against white

**Solution**: Darken the border color

```css
/* In :root selector, find: */
--color-border: #d0d7de;

/* Change to: */
--color-border: #c0c7ce;  /* Slightly darker */
```

**Note**: This is only needed if borders are genuinely hard to see.

### Issue: Changes Not Showing

**Symptoms**: File saved but browser shows old colors

**Solutions**:
1. Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. Check file saved correctly (look for unsaved indicator in editor)
3. Restart dev server: Stop (Ctrl+C) and run `npm run dev` again
4. Clear browser cache

### Issue: Syntax Error

**Symptom**: CSS not loading, console shows errors

**Solution**: Check for:
- Missing semicolon after property value
- Typo in property name
- Extra or missing bracket in :root selector

### Issue: Dark Mode Shows White Background

**Symptom**: Dark mode toggle shows white background (if dark mode is accessible)

**Expected**: This is out of scope - feature only updates light mode

**Clarification**: Dark mode values remain unchanged. If users can access dark mode, it should still work with dark backgrounds.

## Testing in Multiple Browsers

### Recommended Testing

While Chrome/Edge should be sufficient for CSS variable changes, consider:

**Chrome/Edge** (Primary): Test all functionality here  
**Firefox** (Secondary): Quick visual check  
**Safari** (If available): Quick visual check

**Expected**: Identical appearance across browsers (CSS variables widely supported)

## Commit and Push

### Git Workflow

```bash
# Stage the changed file
git add frontend/src/index.css

# Commit with descriptive message
git commit -m "Apply white background to app interface

- Update --color-bg-secondary to #FFFFFF
- Update --color-bg to uppercase #FFFFFF for consistency
- Ensures consistent white background across all components

Resolves: 002-white-background"

# Push to feature branch
git push origin 002-white-background
```

## Next Steps

### After Implementation

1. **Code Review**: Request review from team member
2. **Accessibility Audit**: Run automated contrast checker (optional)
3. **User Testing**: Get feedback on visual appeal
4. **Documentation**: Update any style guides that reference old colors

### Future Enhancements (Out of Scope)

- Implement dark mode toggle functionality
- Add theme customization options
- Create theme switching animation

## Summary

**What You Changed**: 1 line in 1 file  
**Impact**: Entire application now has consistent white background  
**Time Spent**: ~15-30 minutes including testing  
**Complexity**: Low  
**Risk**: Minimal (easily reversible)

The simplicity of this implementation demonstrates the power of CSS custom properties for theme management. A single variable change propagated across the entire application.
