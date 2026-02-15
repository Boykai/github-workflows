# Quickstart Guide: Heart Logo Implementation

**Feature**: 002-heart-logo | **Date**: 2026-02-15  
**Estimated Time**: 30-45 minutes  
**Skill Level**: Beginner to Intermediate

## Overview

This guide provides step-by-step instructions to implement the heart logo feature. The implementation involves adding an inline SVG element to two locations in the React application and adding corresponding CSS styles.

## Prerequisites

- [x] Node.js and npm installed
- [x] Repository cloned locally
- [x] Frontend development environment set up
- [x] Basic understanding of React JSX and CSS
- [x] Code editor (VS Code recommended)

## Quick Reference

**Files to Modify**:
1. `frontend/src/App.tsx` - Add logo SVG (2 locations)
2. `frontend/src/App.css` - Add logo styles

**No New Files Created**: This is an in-place modification

**Testing**: Manual browser verification + optional E2E test update

---

## Step 1: Add CSS Styles

**File**: `frontend/src/App.css`  
**Location**: After existing styles (end of file recommended)

**Action**: Add the following CSS rules

```css
/* Heart logo styles */
.heart-logo {
  width: clamp(40px, 8vw, 120px);
  height: auto;
  display: block;
  margin: 0 auto 16px auto;
  fill: var(--color-primary);
  transition: fill 0.2s ease;
}

/* High contrast mode support */
@media (forced-colors: active) {
  .heart-logo {
    fill: CanvasText;
  }
}
```

**Why this order**: Adding CSS first ensures styles are available when we add the SVG element.

**Checkpoint**: 
```bash
# Verify CSS syntax (optional)
cd frontend
npm run lint
```

---

## Step 2: Add Logo to Login Page

**File**: `frontend/src/App.tsx`  
**Location**: Inside the `.app-login` div, before the `<h1>` element (around line 68-69)

**Current Code**:
```jsx
if (!isAuthenticated) {
  return (
    <div className="app-login">
      <h1>Welcome to Tech Connect 2026!</h1>
      <p>Manage your GitHub Projects with natural language</p>
      <LoginButton />
    </div>
  );
}
```

**Updated Code**:
```jsx
if (!isAuthenticated) {
  return (
    <div className="app-login">
      <svg 
        className="heart-logo"
        role="img"
        aria-label="Heart logo"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
      </svg>
      <h1>Welcome to Tech Connect 2026!</h1>
      <p>Manage your GitHub Projects with natural language</p>
      <LoginButton />
    </div>
  );
}
```

**Key Points**:
- SVG is inserted as the **first child** of `.app-login` div
- Logo appears **before** the `<h1>` title
- All required accessibility attributes are included (`role`, `aria-label`)

---

## Step 3: Add Logo to Authenticated Header

**File**: `frontend/src/App.tsx`  
**Location**: Inside the `.app-header`, before the `<h1>` element (around line 84-85)

**Current Code**:
```jsx
return (
  <div className="app-container">
    <header className="app-header">
      <h1>Welcome to Tech Connect 2026!</h1>
      <div className="header-actions">
        <button 
          className="theme-toggle-btn"
          onClick={toggleTheme}
          aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDarkMode ? '☀️' : '🌙'}
        </button>
        <LoginButton />
      </div>
    </header>
    ...
  </div>
);
```

**Challenge**: The current header uses `display: flex` with `justify-content: space-between`, which spreads items horizontally. We need to center the logo above this content.

**Solution**: Wrap the title and actions in a content div, then stack logo on top.

**Updated Code**:
```jsx
return (
  <div className="app-container">
    <header className="app-header">
      <svg 
        className="heart-logo"
        role="img"
        aria-label="Heart logo"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
      </svg>
      <div className="app-header-content">
        <h1>Welcome to Tech Connect 2026!</h1>
        <div className="header-actions">
          <button 
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
          <LoginButton />
        </div>
      </div>
    </header>
    ...
  </div>
);
```

---

## Step 4: Update Header Layout CSS

**File**: `frontend/src/App.css`  
**Location**: Find the `.app-header` rule (around line 52-59)

**Current CSS**:
```css
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
}
```

**Updated CSS**:
```css
.app-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 24px;
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
}

.app-header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}
```

**Changes Explained**:
- Add `flex-direction: column` to stack logo above content
- Remove `justify-content: space-between` from header (moved to content)
- New `.app-header-content` class maintains existing title/actions layout
- `width: 100%` ensures content uses full header width

---

## Step 5: Type Check and Lint

**Action**: Verify code changes don't introduce errors

```bash
cd frontend

# TypeScript type checking
npm run type-check

# ESLint (includes accessibility checks)
npm run lint

# Fix auto-fixable issues if any
npm run lint:fix
```

**Expected Output**: No errors (warnings about unused imports are okay)

**If Errors Occur**:
- Check for missing closing tags in JSX
- Verify SVG attributes are correctly spelled
- Ensure new div wrapper is properly closed

---

## Step 6: Start Development Server

**Action**: Launch the app to see changes

```bash
cd frontend
npm run dev
```

**Expected Output**:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

**Open in Browser**: Navigate to `http://localhost:5173/`

---

## Step 7: Manual Verification

### Test 1: Visual Appearance (Login Page)

**Steps**:
1. Open `http://localhost:5173/` (unauthenticated)
2. Look for heart logo above "Welcome to Tech Connect 2026!" title
3. Logo should be centered and blue (light mode)

**Success Criteria**:
- ✅ Heart logo is visible
- ✅ Logo is centered horizontally
- ✅ Logo is positioned above the title
- ✅ Logo color matches theme (blue in light mode)

### Test 2: Visual Appearance (Authenticated Page)

**Steps**:
1. Log in to the application
2. Look for heart logo in the header
3. Logo should be centered above the title

**Success Criteria**:
- ✅ Heart logo is visible in header
- ✅ Logo is centered horizontally
- ✅ Logo does not break title/actions layout

### Test 3: Responsive Design (Mobile)

**Steps**:
1. Open Chrome DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M or Cmd+Shift+M)
3. Select "iPhone SE" (320px width)
4. Reload page

**Success Criteria**:
- ✅ Logo scales down to minimum size (40px)
- ✅ Logo remains visible and centered
- ✅ Layout does not break

### Test 4: Responsive Design (Desktop)

**Steps**:
1. In DevTools, select "Responsive" mode
2. Drag to 1920px width (or wider)
3. Observe logo size

**Success Criteria**:
- ✅ Logo scales up but caps at 120px
- ✅ Logo remains centered
- ✅ Logo quality is crisp (no pixelation)

### Test 5: Dark Mode Toggle

**Steps**:
1. Click the theme toggle button (🌙/☀️)
2. Observe logo color change

**Success Criteria**:
- ✅ Logo color changes from `#0969da` (light) to `#539bf5` (dark)
- ✅ Transition is smooth (0.2s ease)
- ✅ Logo remains visible in both themes

### Test 6: Non-Interactive Behavior

**Steps**:
1. Hover mouse over logo
2. Cursor should NOT change to pointer
3. Click on logo
4. Nothing should happen (no navigation, no popup)

**Success Criteria**:
- ✅ No pointer cursor on hover
- ✅ No click action
- ✅ Logo is purely decorative

### Test 7: Screen Reader Accessibility

**Setup**:
- Windows: Enable NVDA or JAWS
- Mac: Enable VoiceOver (Cmd+F5)
- Linux: Enable Orca

**Steps**:
1. Navigate to homepage with screen reader active
2. Tab through page elements
3. Listen for logo announcement

**Success Criteria**:
- ✅ Screen reader announces "Heart logo, image"
- ✅ Logo has descriptive text alternative
- ✅ Logo is not skipped (not marked as decorative)

### Test 8: Browser Zoom

**Steps**:
1. Press Ctrl+Plus (Cmd+Plus on Mac) multiple times
2. Zoom to 200%
3. Observe logo quality

**Success Criteria**:
- ✅ Logo scales with zoom
- ✅ No pixelation or blurriness (SVG advantage)
- ✅ Layout remains intact

### Test 9: High Contrast Mode (Windows Only)

**Steps**:
1. Windows Settings → Ease of Access → High Contrast
2. Enable high contrast theme
3. Open browser and navigate to app

**Success Criteria**:
- ✅ Logo is visible in high contrast mode
- ✅ Logo uses system color (CanvasText)
- ✅ Logo maintains contrast with background

---

## Step 8: Optional E2E Test Update

**File**: `frontend/e2e/auth.spec.ts` (or create new test file)

**Action**: Add test for logo presence

```typescript
import { test, expect } from '@playwright/test';

test('homepage displays heart logo', async ({ page }) => {
  await page.goto('/');
  
  // Verify logo is present
  const logo = page.locator('svg.heart-logo');
  await expect(logo).toBeVisible();
  
  // Verify accessibility attributes
  await expect(logo).toHaveAttribute('role', 'img');
  await expect(logo).toHaveAttribute('aria-label', 'Heart logo');
  
  // Verify logo is above title
  const logoBox = await logo.boundingBox();
  const titleBox = await page.locator('h1').first().boundingBox();
  expect(logoBox!.y).toBeLessThan(titleBox!.y);
});

test('authenticated page displays heart logo', async ({ page }) => {
  // Assuming you have a login helper or auth state
  // await loginAsTestUser(page);
  
  await page.goto('/');
  
  const logo = page.locator('header svg.heart-logo');
  await expect(logo).toBeVisible();
  await expect(logo).toHaveAttribute('aria-label', 'Heart logo');
});
```

**Run E2E Tests**:
```bash
cd frontend
npm run test:e2e
```

---

## Troubleshooting

### Issue: Logo Not Visible

**Possible Causes**:
1. CSS file not loaded → Check browser console for errors
2. Typo in class name → Verify `className="heart-logo"` matches CSS `.heart-logo`
3. Color same as background → Check `--color-primary` is defined

**Solution**:
```bash
# Check for CSS syntax errors
npm run lint

# Inspect element in DevTools
# Look for computed styles on .heart-logo
```

### Issue: Logo Too Large/Small

**Possible Causes**:
1. Missing `clamp()` support in old browser → Add fallback
2. Incorrect `clamp()` values → Verify `clamp(40px, 8vw, 120px)`

**Solution**:
```css
.heart-logo {
  width: 80px; /* Fallback */
  width: clamp(40px, 8vw, 120px);
}
```

### Issue: Logo Not Centered

**Possible Causes**:
1. Missing `display: block` → Required for margin auto centering
2. Missing `margin: 0 auto` → Required for horizontal centering

**Solution**: Verify CSS includes both properties

### Issue: Header Layout Broken

**Possible Causes**:
1. Missing `.app-header-content` wrapper → Verify Step 4 completed
2. Missing `flex-direction: column` on header → Verify CSS updated

**Solution**: Re-check Step 3 and Step 4 code changes

### Issue: Screen Reader Not Announcing Logo

**Possible Causes**:
1. Missing `role="img"` attribute
2. Missing or empty `aria-label`

**Solution**: Verify SVG has both attributes:
```jsx
<svg role="img" aria-label="Heart logo" ...>
```

---

## Rollback Instructions

If you need to undo changes:

```bash
# View changes
git diff frontend/src/App.tsx
git diff frontend/src/App.css

# Discard changes
git checkout -- frontend/src/App.tsx
git checkout -- frontend/src/App.css

# Or revert entire commit (if already committed)
git revert HEAD
```

---

## Success Confirmation

**Checklist** - All items must pass:

- [x] Logo visible on login page
- [x] Logo visible on authenticated page
- [x] Logo centered horizontally
- [x] Logo positioned above title
- [x] Logo scales responsively (40px-120px)
- [x] Logo uses brand color (blue)
- [x] Logo changes color with theme toggle
- [x] Logo non-interactive (no pointer cursor)
- [x] Screen reader announces "Heart logo"
- [x] Logo visible in high contrast mode
- [x] Logo scales correctly with browser zoom
- [x] No TypeScript or lint errors
- [x] Header layout not broken

**If all checks pass**: ✅ **Feature implementation complete!**

---

## Next Steps

1. **Commit Changes**:
```bash
git add frontend/src/App.tsx frontend/src/App.css
git commit -m "feat: add heart logo to homepage for visual branding"
```

2. **Push to Branch**:
```bash
git push origin 002-heart-logo
```

3. **Create Pull Request**: 
   - Title: "Add heart logo to homepage for visual branding"
   - Description: Reference spec.md and this quickstart
   - Reviewers: Tag team members

4. **Post-Merge**:
   - Verify in staging environment
   - Monitor for user feedback
   - Consider A/B testing if desired (out of scope for this feature)

---

## Additional Resources

- [MDN: SVG Tutorial](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial)
- [CSS Tricks: A Complete Guide to Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [CSS clamp() Function](https://developer.mozilla.org/en-US/docs/Web/CSS/clamp)

**Questions?** Refer to `research.md`, `data-model.md`, or `contracts/component-structure.md` for deeper technical details.
