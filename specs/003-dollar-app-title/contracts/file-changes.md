# File Modification Contract: Add Dollar Sign to Application Title

**Feature**: 003-dollar-app-title  
**Branch**: `copilot/add-dollar-sign-to-header`  
**Date**: 2026-02-16  
**Phase**: 1 (Design & Contracts)

## Overview

This contract specifies the exact file changes required to add a dollar sign ($) prefix to the application title. Three files will be modified: one HTML file and one TypeScript React component file (with 2 instances).

## Modification Summary

| File | Lines Changed | Change Type | Risk Level |
|------|---------------|-------------|------------|
| `frontend/index.html` | 1 | String replacement | Low |
| `frontend/src/App.tsx` | 2 | String replacement | Low |

**Total Impact**: 3 lines across 2 files  
**Breaking Changes**: None  
**Rollback Complexity**: Trivial (revert string changes)

---

## File 1: `frontend/index.html`

**Purpose**: HTML entry point with browser tab title  
**Change Type**: String replacement in `<title>` element

### Current State (Relevant Sections)

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Welcome to Tech Connect 2026!</title>
  </head>
```

**Line Number**: 7  
**Current Value**: `<title>Welcome to Tech Connect 2026!</title>`

### Required Changes

**Operation**: Replace title text content  
**Old String**: `Welcome to Tech Connect 2026!`  
**New String**: `$Welcome to Tech Connect 2026!`

### Expected New State (Relevant Sections)

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>$Welcome to Tech Connect 2026!</title>
  </head>
```

**Line Number**: 7 (unchanged)  
**New Value**: `<title>$Welcome to Tech Connect 2026!</title>`

### Side Effects

- Browser tab title will display with $ prefix
- Search engine indexing will capture new title
- Browser history entries will show new title
- Bookmarks created after change will use new title

### Validation

1. Open `frontend/index.html` in editor
2. Navigate to line 7
3. Verify `<title>` tag contains exactly `$Welcome to Tech Connect 2026!`
4. Build project with `npm run build` (from frontend directory)
5. Open built `dist/index.html`, verify title persists

---

## File 2: `frontend/src/App.tsx`

**Purpose**: React component with application headers  
**Change Type**: String replacement in 2 JSX `<h1>` elements

### Current State (Relevant Sections)

```tsx
// Around line 66-73: Login view (unauthenticated)
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

```tsx
// Around line 82-95: Authenticated view header
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
```

**Line Numbers**: 69 (login header), 85 (authenticated header)  
**Current Value**: `<h1>Welcome to Tech Connect 2026!</h1>` (both instances)

### Required Changes

#### Change 2A: Login Header (Line 69)

**Operation**: Replace `<h1>` text content  
**Old String**: `Welcome to Tech Connect 2026!`  
**New String**: `$Welcome to Tech Connect 2026!`  
**Context**: Inside `if (!isAuthenticated)` block

#### Change 2B: Authenticated Header (Line 85)

**Operation**: Replace `<h1>` text content  
**Old String**: `Welcome to Tech Connect 2026!`  
**New String**: `$Welcome to Tech Connect 2026!`  
**Context**: Inside `<header className="app-header">` element

### Expected New State (Relevant Sections)

```tsx
// Around line 66-73: Login view (unauthenticated)
if (!isAuthenticated) {
  return (
    <div className="app-login">
      <h1>$Welcome to Tech Connect 2026!</h1>
      <p>Manage your GitHub Projects with natural language</p>
      <LoginButton />
    </div>
  );
}
```

```tsx
// Around line 82-95: Authenticated view header
return (
  <div className="app-container">
    <header className="app-header">
      <h1>$Welcome to Tech Connect 2026!</h1>
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
```

**Line Numbers**: 69, 85 (unchanged)  
**New Value**: `<h1>$Welcome to Tech Connect 2026!</h1>` (both instances)

### Side Effects

- Login page will display $ in header on page load
- Main application header will display $ after authentication
- Component re-renders will maintain $ in header (static text)
- No TypeScript type changes (still `string` content)
- No CSS class or prop changes needed

### Validation

1. Open `frontend/src/App.tsx` in editor
2. Search for `Welcome to Tech Connect 2026!` (should find 2 matches)
3. Verify line 69 is in unauthenticated block: `if (!isAuthenticated)`
4. Verify line 85 is in authenticated header: `<header className="app-header">`
5. Replace both instances with `$Welcome to Tech Connect 2026!`
6. Run TypeScript type check: `npm run type-check` (if available) or `npx tsc --noEmit`
7. Start dev server: `npm run dev`
8. Verify header displays with $ in both login and authenticated views

---

## Cross-Cutting Concerns

### 1. Styling Consistency

**Concern**: Dollar sign must inherit existing h1 styling

**Resolution**: No action needed. The $ character is plain text within `<h1>` tags and automatically inherits all CSS properties:
- Font family from `App.css` or `index.css`
- Font size defined for `h1` elements
- Color from theme variables
- Font weight (typically bold for h1)

**Verification**: Visual inspection in browser confirms $ matches rest of title styling

---

### 2. Responsive Design

**Concern**: Dollar sign must display correctly on mobile and desktop

**Resolution**: No action needed. Existing responsive CSS handles text reflow:
- Mobile layouts (320px+): $ adds 1 character, no overflow expected
- Desktop layouts: No impact on wide screens
- Font sizing: Fluid or fixed sizing applies to entire h1 including $

**Verification**: Test in browser responsive mode (320px, 768px, 1920px widths)

---

### 3. Accessibility

**Concern**: Screen readers must announce dollar sign

**Resolution**: No action needed. Screen readers handle currency symbols natively:
- HTML `<title>`: Announced when page loads
- JSX `<h1>`: Announced when element receives focus or during page scan
- Dollar sign announced as "dollar sign" or "dollar" (varies by screen reader)

**Verification**: Test with screen reader (NVDA, JAWS, or VoiceOver)

---

### 4. Testing Updates

**Concern**: Existing tests may expect old title text

**Action Required**: Update E2E tests in `frontend/e2e/ui.spec.ts` to expect new title

**Changes Needed**:
- Search for test assertions containing `"Welcome to Tech Connect 2026!"`
- Update to expect `"$Welcome to Tech Connect 2026!"`
- Run tests to verify: `npm run test:e2e` (from frontend directory)

**Example** (if test exists):
```typescript
// Before
await expect(page).toHaveTitle('Welcome to Tech Connect 2026!');

// After
await expect(page).toHaveTitle('$Welcome to Tech Connect 2026!');
```

---

### 5. Build and Deployment

**Concern**: Changes must not break build process

**Resolution**: String-only changes have no build impact:
- HTML is copied as-is by Vite
- TypeScript/JSX compiles identically (string literal change)
- No new dependencies or imports
- Bundle size increase: ~3 bytes (negligible)

**Verification**: 
1. Run build: `npm run build` (from frontend directory)
2. Verify build succeeds with no errors
3. Check dist output contains updated titles

---

## Verification Contract

After implementing changes, verify the following:

### Browser Tab Title (FR-001, SC-001)
- [ ] Open application in browser
- [ ] Observe browser tab displays "$Welcome to Tech Connect 2026!"
- [ ] Switch to another tab and back - title persists
- [ ] Test in Chrome, Firefox, Safari, Edge

### Application Headers (FR-001, FR-003, FR-004, SC-002)
- [ ] Load application (unauthenticated/login view)
- [ ] Observe login page header displays "$Welcome to Tech Connect 2026!"
- [ ] Authenticate (login with credentials)
- [ ] Observe main application header displays "$Welcome to Tech Connect 2026!"
- [ ] Test responsive layouts:
  - [ ] Mobile (320px width)
  - [ ] Tablet (768px width)
  - [ ] Desktop (1920px+ width)

### Styling Consistency (FR-002, SC-004)
- [ ] Visually inspect $ character matches title font
- [ ] Verify $ color matches title color
- [ ] Verify $ size matches title size
- [ ] Check in both light and dark mode (if applicable)

### Accessibility (FR-005, SC-003)
- [ ] Test with screen reader (optional but recommended)
- [ ] Verify $ is announced as "dollar sign" or "dollar"
- [ ] Test keyboard navigation (title should be reachable)

### Consistency Check (FR-006)
- [ ] Search codebase for old title: `grep -r "Welcome to Tech Connect 2026!" frontend/`
- [ ] Verify only test files (if any) contain old title
- [ ] Verify index.html and App.tsx show new title with $

### Build Verification
- [ ] Run `npm run build` from frontend directory
- [ ] Verify build succeeds with no errors
- [ ] Check `dist/index.html` contains new title
- [ ] Test built application: `npm run preview`

### Testing Updates
- [ ] Run E2E tests: `npm run test:e2e`
- [ ] Update test expectations if tests fail due to title change
- [ ] Verify all tests pass after updates

---

## Rollback Plan

If issues arise, revert changes:

1. **Git rollback**: `git revert <commit-hash>` or manually revert changes
2. **Manual rollback**: Replace `$Welcome to Tech Connect 2026!` with `Welcome to Tech Connect 2026!` in 3 locations
3. **Verify rollback**: Check browser tab and headers show old title
4. **Redeploy**: Build and deploy reverted version

**Rollback Risk**: Very low - simple string replacement, no dependencies or database changes

---

## Implementation Checklist

- [ ] Update `frontend/index.html` line 7 (browser tab title)
- [ ] Update `frontend/src/App.tsx` line 69 (login header)
- [ ] Update `frontend/src/App.tsx` line 85 (authenticated header)
- [ ] Run TypeScript type check (verify no type errors)
- [ ] Run build process (verify build succeeds)
- [ ] Test in browser (verify $ appears in all 3 locations)
- [ ] Test responsive layouts (verify $ displays on mobile and desktop)
- [ ] Test screen reader (optional, verify $ is announced)
- [ ] Update E2E tests (if needed)
- [ ] Run E2E tests (verify tests pass)
- [ ] Commit changes with descriptive message
- [ ] Push to feature branch

---

## Dependencies

**Prerequisites**: None  
**Blocking Issues**: None  
**Related Changes**: None

This is a self-contained feature with no dependencies on other work.

---

## Notes

- **Character encoding**: Ensure source files remain UTF-8 encoded
- **Line numbers**: May shift slightly if file is modified by auto-formatters
- **Git conflicts**: Unlikely unless other PRs modify same title locations
- **Performance**: Zero performance impact from 1-character addition per title
