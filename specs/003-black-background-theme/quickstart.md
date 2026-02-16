# Quickstart: Black Background Theme Implementation

**Feature**: 003-black-background-theme  
**Date**: 2026-02-16  
**Estimated Time**: 2 hours  
**Skill Level**: Intermediate (CSS, React basics)

## Prerequisites

- Node.js and npm installed
- Repository cloned locally
- Familiarity with CSS custom properties
- Basic understanding of React hooks
- Access to browser developer tools

---

## Step 1: Understand Current State (10 minutes)

### 1.1 Explore Existing Theme System

```bash
# Navigate to frontend directory
cd frontend

# Open the main CSS file
cat src/index.css | grep "dark-mode-active" -A 15
```

**What to observe**:
- CSS custom properties defined in `:root` (light theme)
- Override block `html.dark-mode-active` (current dark mode)
- Variable naming convention: `--color-*`

### 1.2 Check Theme Hook

```bash
# View the theme management hook
cat src/hooks/useAppTheme.tsx
```

**What to observe**:
- `isDarkMode` state variable
- `toggleTheme` function
- `useEffect` that adds/removes `dark-mode-active` class on `<html>`

### 1.3 Run Application

```bash
# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

**Expected**: Application opens at http://localhost:5173 with light theme by default

---

## Step 2: Update CSS Variables (30 minutes)

### 2.1 Modify Black Theme Colors

**File**: `frontend/src/index.css`

**Find** the `html.dark-mode-active` block (around line 18):

```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;              /* ← CHANGE THIS */
  --color-bg-secondary: #161b22;    /* ← CHANGE THIS */
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4); /* ← CHANGE THIS */
}
```

**Replace** with:

```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #000000;              /* ← PURE BLACK */
  --color-bg-secondary: #0a0a0a;    /* ← VERY DARK GRAY */
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(255, 255, 255, 0.05); /* ← LIGHT SHADOW */
}
```

**Save** the file.

### 2.2 Add High Contrast Mode Support

**File**: `frontend/src/index.css`

**Add** at the end of the file (after line 66):

```css
/* High contrast mode support */
@media (forced-colors: active) {
  :root,
  html.dark-mode-active {
    --color-bg: Canvas;
    --color-text: CanvasText;
    --color-border: ButtonBorder;
    --color-primary: LinkText;
  }
}
```

**Save** the file.

---

## Step 3: Update Component Styles (25 minutes)

### 3.1 Fix Error Toast for Black Background

**File**: `frontend/src/App.css`

**Find** the `.error-toast` styles (around line 399):

```css
.error-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fff1f0;
  border: 1px solid #cf222e;
  /* ... */
}
```

**Add** dark mode override **after** the `.error-toast` block:

```css
html.dark-mode-active .error-toast {
  background: rgba(248, 81, 73, 0.1);
  border: 1px solid #f85149;
}

html.dark-mode-active .error-toast-message {
  color: #f85149;
}
```

### 3.2 Fix Error Banner for Black Background

**Find** the `.error-banner` styles (around line 441):

```css
.error-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fff1f0;
  border: 1px solid #cf222e;
  /* ... */
}
```

**Add** dark mode override **after** the `.error-banner-message` block:

```css
html.dark-mode-active .error-banner {
  background: rgba(248, 81, 73, 0.1);
  border: 1px solid #f85149;
}

html.dark-mode-active .error-banner-message {
  color: #f85149;
}
```

### 3.3 Fix Highlight Animation for Black Background

**Find** the `@keyframes highlight-pulse` (around line 385):

```css
@keyframes highlight-pulse {
  0% {
    background: #dafbe1;
    border-color: #2da44e;
    box-shadow: 0 0 0 4px rgba(45, 164, 78, 0.2);
  }
  100% {
    background: var(--color-bg);
    border-color: var(--color-border);
    box-shadow: none;
  }
}
```

**Replace** with:

```css
@keyframes highlight-pulse {
  0% {
    background: rgba(63, 185, 80, 0.2);
    border-color: #3fb950;
    box-shadow: 0 0 0 4px rgba(63, 185, 80, 0.15);
  }
  100% {
    background: var(--color-bg);
    border-color: var(--color-border);
    box-shadow: none;
  }
}
```

**Save** the file.

---

## Step 4: Set Black Theme as Default (5 minutes)

### 4.1 Update Theme Hook Default

**File**: `frontend/src/hooks/useAppTheme.tsx`

**Find** the state initialization:

```typescript
const [isDarkMode, setIsDarkMode] = useState(false);
```

**Replace** with:

```typescript
const [isDarkMode, setIsDarkMode] = useState(true);
```

**Save** the file.

---

## Step 5: Visual Verification (20 minutes)

### 5.1 Check Development Server

If dev server is still running, it should hot-reload automatically. Otherwise:

```bash
npm run dev
```

**Expected**: Application now displays with black background by default

### 5.2 Visual Inspection Checklist

Open http://localhost:5173 and verify:

- [ ] **Login screen**: Black background (#000000)
- [ ] **Main app header**: Black background visible
- [ ] **Project sidebar**: Black background, text readable
- [ ] **Chat section**: Black background, placeholder text visible
- [ ] **Theme toggle button**: Click to toggle light/black themes
- [ ] **All text readable**: White/light gray text on black, high contrast
- [ ] **Buttons visible**: Blue buttons stand out against black
- [ ] **Task cards** (if any): Black backgrounds with subtle borders

### 5.3 Test Theme Toggle

1. Click the theme toggle button (🌙/☀️ icon in header)
2. **Expected**: Theme switches to light mode (white background)
3. Click again
4. **Expected**: Theme switches back to black background

---

## Step 6: Keyboard Navigation Test (10 minutes)

### 6.1 Test Focus Indicators

1. Press `Tab` key repeatedly to navigate through interactive elements
2. **Expected**: Bright blue outline (2px) appears around focused element
3. **Verify** blue outline visible on:
   - Login button
   - Theme toggle button
   - Project selector dropdown
   - Chat input (when authenticated)
   - All clickable task cards

### 6.2 Test Keyboard Shortcuts

If application has keyboard shortcuts, test them on black background:

- All shortcuts should still work
- Focus indicators remain visible throughout

---

## Step 7: Contrast Verification (15 minutes)

### 7.1 Use Browser DevTools Color Picker

1. Open Chrome DevTools (F12)
2. Right-click on any text element → Inspect
3. In Styles panel, click color swatch next to color property
4. DevTools shows contrast ratio automatically

**Verify these ratios**:
- Primary text (#e6edf3): Should show ~21:1 (AAA)
- Secondary text (#8b949e): Should show ~13:1 (AAA)
- Blue buttons (#539bf5): Should show ~8.6:1 (AA)

### 7.2 Automated Contrast Check

```bash
# Run Lighthouse accessibility audit
npm run build
npm run preview
# Open http://localhost:4173 in Chrome
# Open DevTools → Lighthouse → Run accessibility audit
```

**Expected**: All color contrast tests pass

---

## Step 8: Test Different Screens (10 minutes)

### 8.1 Test All Primary Screens

Navigate through the application:

1. **Login screen** (logged out state)
   - Black background
   - White text readable
   - Login button visible

2. **Authenticated main screen**
   - Black background throughout
   - Header, sidebar, chat section all black
   - Text readable in all sections

3. **Project sidebar**
   - Black background
   - Task cards have subtle backgrounds (#0a0a0a)
   - Status badges colored and readable

### 8.2 Test Modals (if any)

If application has modal dialogs:

1. Trigger a modal/popup
2. **Expected**: Modal content has black background
3. **Expected**: Backdrop is semi-transparent black
4. **Expected**: Modal clearly distinguishable from backdrop

---

## Step 9: Edge Case Testing (10 minutes)

### 9.1 Test Browser Zoom

1. Zoom in (Ctrl/Cmd + `+`) to 150%, then 200%
2. **Verify**: Text remains readable, shadows still visible
3. Zoom out (Ctrl/Cmd + `-`) to 75%, then 50%
4. **Verify**: Layout doesn't break, black theme persists

### 9.2 Test Window Resize

1. Resize browser window from desktop → tablet → mobile widths
2. **Verify**: Black background scales properly
3. **Verify**: No white flashes or layout breaks

### 9.3 Test Page Reload

1. Refresh page (F5 or Ctrl/Cmd + R)
2. **Expected**: Black theme loads immediately (default)
3. **Expected**: No flash of light content (FOUC)

---

## Step 10: Build and Preview (5 minutes)

### 10.1 Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

**Expected**: Production build displays black theme correctly

### 10.2 Check Build Output

```bash
# Verify CSS is bundled correctly
ls -lh dist/assets/*.css
```

**Expected**: CSS file exists, contains black theme variables

---

## Step 11: Commit Changes (5 minutes)

### 11.1 Check Git Status

```bash
git status
```

**Expected changes**:
- `frontend/src/index.css` (modified)
- `frontend/src/App.css` (modified)
- `frontend/src/hooks/useAppTheme.tsx` (modified)

### 11.2 Review Diffs

```bash
git diff frontend/src/index.css
git diff frontend/src/App.css
git diff frontend/src/hooks/useAppTheme.tsx
```

**Verify**: Only expected changes present (no accidental edits)

### 11.3 Commit

```bash
git add frontend/src/index.css frontend/src/App.css frontend/src/hooks/useAppTheme.tsx
git commit -m "Implement black background theme

- Update CSS variables to use pure black (#000000) backgrounds
- Add high contrast mode support for accessibility
- Fix error toast/banner colors for black background
- Update highlight animation for visibility on black
- Set black theme as default on app load
- Maintain WCAG AA contrast ratios for all text elements"
```

---

## Troubleshooting

### Issue: Text not readable on black background

**Solution**: Check CSS variables are correctly applied:

```bash
# Open browser DevTools
# Inspect <html> element
# Verify "dark-mode-active" class is present
# Check Computed styles tab for --color-bg value (should be rgb(0, 0, 0))
```

### Issue: Theme toggle not working

**Solution**: Check useAppTheme hook:

```typescript
// Verify useEffect is running
useEffect(() => {
  if (isDarkMode) {
    document.documentElement.classList.add('dark-mode-active');
  } else {
    document.documentElement.classList.remove('dark-mode-active');
  }
}, [isDarkMode]);
```

### Issue: Shadows not visible

**Solution**: Increase shadow opacity slightly:

```css
--shadow: 0 1px 3px rgba(255, 255, 255, 0.08); /* Increase from 0.05 */
```

### Issue: Focus indicators not visible

**Solution**: Check focus-visible styles exist:

```css
button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

---

## Success Criteria Verification

Before considering the feature complete, verify:

- ✅ **SC-001**: All primary screens display solid black (#000000) backgrounds
  - **Test**: Use browser color picker on different screens
  
- ✅ **SC-002**: All text meets WCAG AA contrast requirements
  - **Test**: Run Lighthouse accessibility audit, all contrast tests pass
  
- ✅ **SC-003**: Users can complete core tasks without readability issues
  - **Test**: Manually navigate through all user workflows
  
- ✅ **SC-004**: Black background applies immediately on launch
  - **Test**: Refresh page, no white flash visible
  
- ✅ **SC-005**: 100% of navigation and modals use black backgrounds
  - **Test**: Open all menus, modals, dropdowns - all have black backgrounds

---

## Next Steps

After completing this quickstart:

1. Request code review from team member
2. Run full test suite: `npm test`
3. Run E2E tests: `npm run test:e2e`
4. Create pull request with screenshots showing before/after
5. Deploy to staging environment for QA testing

---

## Additional Resources

- **WCAG 2.1 Contrast Guidelines**: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
- **CSS Custom Properties MDN**: https://developer.mozilla.org/en-US/docs/Web/CSS/--*
- **Forced Colors Mode**: https://developer.mozilla.org/en-US/docs/Web/CSS/@media/forced-colors

---

## Time Breakdown

| Step | Estimated Time | Actual Time |
|------|----------------|-------------|
| 1. Understand Current State | 10 min | _____ |
| 2. Update CSS Variables | 30 min | _____ |
| 3. Update Component Styles | 25 min | _____ |
| 4. Set Default Theme | 5 min | _____ |
| 5. Visual Verification | 20 min | _____ |
| 6. Keyboard Navigation | 10 min | _____ |
| 7. Contrast Verification | 15 min | _____ |
| 8. Test Different Screens | 10 min | _____ |
| 9. Edge Case Testing | 10 min | _____ |
| 10. Build and Preview | 5 min | _____ |
| 11. Commit Changes | 5 min | _____ |
| **Total** | **2h 25min** | _____ |

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-16  
**Maintainer**: Development Team
