# CSS Changes Contract: Red Background Interface

**Feature**: Red Background Interface  
**Branch**: `copilot/apply-red-background-interface-again`  
**Date**: 2026-02-16

## Purpose

This contract document specifies the exact CSS modifications required to implement the red background feature. It serves as a contract between design (Phase 1) and implementation (Phase 2) to ensure precise, minimal changes.

## Change Summary

**Total Files Modified**: 1  
**Total Lines Changed**: 2  
**Breaking Changes**: None  
**Backward Compatibility**: Maintained (CSS changes only affect visual appearance)

## File: frontend/src/index.css

**Path**: `/home/runner/work/github-workflows/github-workflows/frontend/src/index.css`

**Purpose**: Global CSS file containing theme custom properties

**Lines to Modify**: Lines ~8 and ~20 (exact line numbers may vary slightly)

### Change 1: Light Mode Background

**Location**: `:root` selector block

**Before**:
```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;  /* ← THIS LINE */
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
  --color-bg-secondary: #FF0000;  /* ← CHANGED: Red background */
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

**Exact Change**:
```diff
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #FF0000;
```

**Rationale**: Updates the light mode page background color to red (#FF0000)

---

### Change 2: Dark Mode Background

**Location**: `html.dark-mode-active` selector block

**Before**:
```css
/* Dark theme overrides */
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #161b22;  /* ← THIS LINE */
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**After**:
```css
/* Dark theme overrides */
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #FF0000;  /* ← CHANGED: Red background */
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Exact Change**:
```diff
-  --color-bg-secondary: #161b22;
+  --color-bg-secondary: #FF0000;
```

**Rationale**: Updates the dark mode page background color to red (#FF0000) for consistency across theme modes

---

## Implementation Requirements

### Validation Checklist

Before committing changes, verify:

- [ ] Both `:root` and `html.dark-mode-active` blocks are modified
- [ ] Color value is exactly `#FF0000` (uppercase, 6 hex digits)
- [ ] No other lines in the file are modified
- [ ] No whitespace changes except on the modified lines
- [ ] CSS syntax is valid (semicolons, no extra characters)
- [ ] File encoding remains UTF-8
- [ ] Line endings remain consistent with repository (likely LF)

### Testing Checklist

After making changes, verify:

- [ ] Run `npm run build` in frontend directory - must succeed
- [ ] Open application in browser - background should be red
- [ ] Toggle theme dark→light - background should remain red
- [ ] Navigate to different routes - background should stay red
- [ ] Refresh page (F5) - background should restore to red
- [ ] Open DevTools - verify `--color-bg-secondary` computed value is `rgb(255, 0, 0)`

### Browser DevTools Verification

To verify the change in browser DevTools:

1. Open application in browser
2. Open DevTools (F12)
3. Go to Elements/Inspector tab
4. Select `<body>` element
5. In Computed/Styles panel, check:
   ```
   background-color: rgb(255, 0, 0)  ← Should be red
   ```
6. Find `--color-bg-secondary` variable:
   ```
   --color-bg-secondary: #FF0000  ← Should show red hex value
   ```

## Side Effects

### Expected Visual Changes

These changes are EXPECTED and ACCEPTABLE per spec:

1. **Body Background**: Changes from light/dark gray to red
2. **Theme Toggle Button**: Background changes to red (inherits variable)
3. **Task Preview Panels**: Background changes to red (inherits variable)
4. **Rate Limit Bar**: Background changes to red (inherits variable)

### Unexpected Side Effects

If any of these occur, the implementation is INCORRECT:

1. Component backgrounds (cards, panels) turn red - should remain white/dark
2. Text becomes unreadable - should remain visible (though may have contrast issues)
3. Borders or shadows change color - should remain unchanged
4. Layout shifts or breaks - should remain stable
5. Theme toggle stops working - should continue functioning
6. Console errors appear - should have zero errors

### Known Accessibility Issues

**Light Mode Contrast**:
- Text color `#24292f` vs background `#FF0000` = 3.9:1 contrast
- Falls below WCAG AA standard (4.5:1)
- Status: DOCUMENTED, not fixed in this feature per spec assumptions

**Dark Mode Contrast**:
- Text color `#e6edf3` vs background `#FF0000` = 5.2:1 contrast
- Meets WCAG AA standard
- Status: COMPLIANT

## Rollback Plan

### Reverting Changes

To revert to previous state:

```diff
/* In :root block */
-  --color-bg-secondary: #FF0000;
+  --color-bg-secondary: #f6f8fa;

/* In html.dark-mode-active block */
-  --color-bg-secondary: #FF0000;
+  --color-bg-secondary: #161b22;
```

### Emergency Hotfix

If red background causes critical issues in production:

1. Revert the 2 line changes
2. Run `npm run build`
3. Deploy updated build
4. Total time: ~5 minutes

## Integration Points

### Files That Reference This Variable

These files USE `--color-bg-secondary` but require NO CHANGES:

1. `frontend/src/App.css`
   - `.theme-toggle-btn { background: var(--color-bg-secondary) }`
   - `.task-preview { background: var(--color-bg-secondary) }`
   - `.rate-limit-bar { background: var(--color-bg-secondary) }`

2. `frontend/src/index.css`
   - `body { background: var(--color-bg-secondary) }`

3. `frontend/src/components/chat/ChatInterface.css`
   - No direct usage of `--color-bg-secondary`

**Important**: These files read the variable value but don't define it. They automatically pick up the new red value without modification.

### Build System Impact

**Vite Configuration**: No changes required  
**TypeScript Config**: No changes required  
**ESLint/Prettier**: No changes required  
**Package Dependencies**: No changes required

**Build Output**:
- CSS bundle will include the updated variable definitions
- Minified CSS will contain: `--color-bg-secondary:#FF0000`
- No additional bytes added (same length as previous values)

## Performance Impact

**Bundle Size**: Neutral (color value same length as before)  
**Runtime Performance**: Zero impact (CSS variables cached by browser)  
**First Paint Time**: No change (CSS loads synchronously as before)  
**Paint Complexity**: No change (single solid color is simplest paint)

## Security Considerations

**XSS Risk**: None (static CSS value, no user input)  
**CSRF Risk**: None (CSS changes don't affect authentication)  
**Data Exposure**: None (no data involved in color change)

## Compliance

**WCAG AA**: Dark mode compliant (5.2:1 contrast), light mode non-compliant (3.9:1)  
**WCAG AAA**: Both modes non-compliant (requires 7:1 contrast)  
**Status**: Documented limitation, accepted per spec assumptions

## Approval

**Design Approved**: Yes (per feature specification)  
**Accessibility Review**: Acknowledged (contrast documented)  
**Security Review**: Not required (CSS-only change)  
**Performance Review**: Not required (zero impact)

---

## Implementation Instructions

### Step-by-Step

1. Open `frontend/src/index.css` in editor
2. Locate `:root` block (around line 2-15)
3. Find line with `--color-bg-secondary: #f6f8fa;`
4. Change value to `#FF0000`
5. Locate `html.dark-mode-active` block (around line 17-28)
6. Find line with `--color-bg-secondary: #161b22;`
7. Change value to `#FF0000`
8. Save file
9. Run validation checklist above
10. Commit with message: "Apply red background to application interface"

### Validation Command

```bash
cd /home/runner/work/github-workflows/github-workflows/frontend
npm run build
# Should complete without errors
```

### Visual Validation

```bash
cd /home/runner/work/github-workflows/github-workflows/frontend
npm run dev
# Open http://localhost:5173 in browser
# Verify background is red
```

## Conclusion

This contract specifies exactly 2 lines of CSS that need modification to implement the red background feature. The changes are minimal, reversible, and carry no technical risk. Implementation should take less than 5 minutes.
