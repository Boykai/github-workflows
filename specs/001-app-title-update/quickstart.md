# Quick Start Guide: Update App Title to "GitHub Workflows"

**Feature**: 001-app-title-update  
**Phase**: 1 - Implementation Guide  
**Date**: 2026-02-14

## Overview

This guide provides step-by-step instructions for implementing the application title update from "Welcome to Tech Connect 2026!" to "GitHub Workflows".

**Estimated Time**: 10 minutes  
**Difficulty**: Beginner  
**Prerequisites**: Text editor, browser for testing

---

## Step 1: Update HTML Title (2 minutes)

**File**: `frontend/index.html`

**Change**: Line 7

```diff
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
-   <title>Welcome to Tech Connect 2026!</title>
+   <title>GitHub Workflows</title>
  </head>
```

**Why**: This sets the initial browser tab title that appears while the page is loading and before React mounts.

**Verification**: Save the file and open `frontend/index.html` in a browser (or refresh if running dev server) - tab should show "GitHub Workflows".

---

## Step 2: Update Login Screen Title (2 minutes)

**File**: `frontend/src/App.tsx`

**Change**: Line ~69 (in the login screen JSX)

```diff
  if (!isAuthenticated) {
    return (
      <div className="app-login">
-       <h1>Welcome to Tech Connect 2026!</h1>
+       <h1>GitHub Workflows</h1>
        <p>Manage your GitHub Projects with natural language</p>
        <LoginButton />
      </div>
    );
  }
```

**Why**: This updates the visible title shown on the login screen before users authenticate.

**Verification**: View the login screen in your browser - header should display "GitHub Workflows".

---

## Step 3: Update Main Header Title (2 minutes)

**File**: `frontend/src/App.tsx`

**Change**: Line ~85 (in the main app header JSX)

```diff
  return (
    <div className="app-container">
      <header className="app-header">
-       <h1>Welcome to Tech Connect 2026!</h1>
+       <h1>GitHub Workflows</h1>
        <div className="header-actions">
          <button 
            className="theme-toggle-btn"
```

**Why**: This updates the visible title in the main application header after users log in.

**Verification**: Log in and view the main app - header should display "GitHub Workflows".

---

## Step 4: Add Document Title Effect (3 minutes)

**File**: `frontend/src/App.tsx`

**Location**: Near the top of the App component function (after hooks, before conditionals)

**Add this code**:

```typescript
// Add at the top of App.tsx imports if not already present
import { useEffect, useState } from 'react';

// Inside the App component function, after existing hooks:
useEffect(() => {
  document.title = "GitHub Workflows";
}, []);
```

**Full context example**:

```typescript
function App() {
  // Existing hooks
  const { isDarkMode, toggleTheme } = useAppTheme();
  const { isAuthenticated, handleLogout, isLoading } = useAuth();
  
  // Add this NEW useEffect
  useEffect(() => {
    document.title = "GitHub Workflows";
  }, []);
  
  // Rest of component logic...
```

**Why**: This ensures the browser document title is set programmatically after React mounts, providing consistency even if the HTML title was somehow different or changed by other code.

**Verification**: Open browser dev tools, type `document.title` in console - should return "GitHub Workflows".

---

## Step 5: Build and Test (1 minute)

**Commands**:

```bash
# From the repository root
cd frontend

# Install dependencies (if not already installed)
npm install

# Run development server
npm run dev

# Or build for production
npm run build
```

**Verification Checklist**:

1. ✅ Browser tab shows "GitHub Workflows" when page loads
2. ✅ Login screen header displays "GitHub Workflows"
3. ✅ Main app header displays "GitHub Workflows" after login
4. ✅ Bookmark the page - bookmark title is "GitHub Workflows"
5. ✅ Navigate around the app - title stays "GitHub Workflows"

---

## Step 6: Cross-Browser Testing (Optional - 2 minutes)

**Test in multiple browsers**:

- Chrome/Chromium
- Firefox
- Safari (macOS/iOS)
- Edge

**What to verify**:
- Tab title displays correctly in all browsers
- No truncation or encoding issues
- Bookmark behavior works as expected

---

## Complete Example

Here's the complete modified App component section with all changes:

```typescript
// frontend/src/App.tsx

import { useEffect, useState } from 'react';
import { useAppTheme } from './hooks/useAppTheme';
import { useAuth } from './hooks/useAuth';
// ... other imports

function App() {
  // Existing hooks
  const { isDarkMode, toggleTheme } = useAppTheme();
  const { isAuthenticated, handleLogout, isLoading } = useAuth();
  
  // NEW: Set document title on mount
  useEffect(() => {
    document.title = "GitHub Workflows";
  }, []);
  
  // Loading state
  if (isLoading) {
    return (
      <div className="app-loading">
        <div className="spinner" />
        <p>Loading...</p>
      </div>
    );
  }

  // Login screen with UPDATED title
  if (!isAuthenticated) {
    return (
      <div className="app-login">
        <h1>GitHub Workflows</h1>
        <p>Manage your GitHub Projects with natural language</p>
        <LoginButton />
      </div>
    );
  }

  // Main app with UPDATED header title
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>GitHub Workflows</h1>
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
      {/* ... rest of app ... */}
    </div>
  );
}

export default App;
```

---

## Troubleshooting

### Issue: Title not updating in browser tab

**Solution**: 
- Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
- Clear browser cache
- Check index.html was saved properly

### Issue: useEffect not imported

**Solution**: 
```typescript
import { useEffect } from 'react';
```

### Issue: TypeScript errors

**Solution**: 
- Ensure `document.title` is inside a function (not at module level)
- Verify useEffect is called inside the component function

### Issue: Title shows old value briefly then updates

**Explanation**: This is normal behavior:
1. HTML title loads first (should already be "GitHub Workflows")
2. React mounts and useEffect runs (confirms title)
3. If HTML wasn't updated, you'd see this flash

**Solution**: Ensure Step 1 (HTML update) was completed

---

## Rollback Instructions

If you need to revert these changes:

```bash
# Revert specific files
git checkout HEAD -- frontend/index.html
git checkout HEAD -- frontend/src/App.tsx

# Or revert the entire commit
git revert <commit-hash>
```

**Manual rollback**: Replace "GitHub Workflows" with "Welcome to Tech Connect 2026!" in all three locations and remove the useEffect.

---

## Testing Checklist

Use this checklist to verify the implementation:

- [ ] **Step 1**: HTML title updated in `frontend/index.html`
- [ ] **Step 2**: Login screen title updated in `frontend/src/App.tsx`
- [ ] **Step 3**: Main header title updated in `frontend/src/App.tsx`
- [ ] **Step 4**: useEffect added for `document.title`
- [ ] **Verify**: Browser tab shows "GitHub Workflows"
- [ ] **Verify**: Login screen displays "GitHub Workflows"
- [ ] **Verify**: Main header displays "GitHub Workflows"
- [ ] **Verify**: Bookmark title is "GitHub Workflows"
- [ ] **Verify**: Title persists across page navigation
- [ ] **Verify**: No console errors
- [ ] **Verify**: No TypeScript errors
- [ ] **Verify**: Build succeeds (`npm run build`)
- [ ] **Cross-browser** (Optional): Test in Chrome, Firefox, Safari, Edge

---

## Next Steps

After implementing this feature:

1. **Manual Testing**: Complete the testing checklist above
2. **Code Review**: Have a team member review changes
3. **Commit**: `git commit -m "Update app title to 'GitHub Workflows'"`
4. **Push**: `git push origin <branch-name>`
5. **Deploy**: Follow standard deployment process
6. **User Acceptance**: Verify with stakeholders

---

## Additional Notes

### Why No Automated Tests?

Per Constitution Principle IV (Test Optionality), automated tests are optional by default. For this simple text change:

- Visual verification is sufficient
- No complex logic to test
- Manual testing is faster than writing tests
- No regression risk (text-only change)

If you want to add tests anyway:

```typescript
// Example test (frontend/src/App.test.tsx)
describe('App title', () => {
  it('sets document title to GitHub Workflows', () => {
    render(<App />);
    expect(document.title).toBe('GitHub Workflows');
  });
});
```

### Performance Impact

**Zero performance impact**:
- String replacement: negligible CPU
- Same string length: no bundle size change
- Single useEffect: runs once, minimal overhead
- No network requests: no latency added

### Accessibility

**No accessibility changes needed**:
- `<h1>` semantic structure preserved
- No ARIA attributes required (text is self-describing)
- Screen readers announce title naturally
- Keyboard navigation unaffected

### SEO & Social Sharing

**Out of scope** (per spec), but if needed later:

```html
<!-- Would be added to index.html <head> if desired -->
<meta property="og:title" content="GitHub Workflows" />
<meta name="twitter:title" content="GitHub Workflows" />
```

---

## Summary

**Total Changes**: 4 modifications across 2 files  
**Lines Changed**: ~6 lines  
**New Dependencies**: 0  
**Breaking Changes**: 0  
**Risk Level**: Minimal

This is a straightforward implementation with no complex logic, no new dependencies, and no breaking changes. The entire feature can be implemented and tested in under 15 minutes.

---

## Constitution Compliance

✅ **Specification-First**: Guide follows spec requirements exactly  
✅ **Template-Driven**: Using quickstart template structure  
✅ **Agent-Orchestrated**: Single-purpose implementation guide  
✅ **Test Optionality**: Manual testing sufficient, automated tests optional  
✅ **Simplicity/DRY**: Minimal changes, no unnecessary complexity
