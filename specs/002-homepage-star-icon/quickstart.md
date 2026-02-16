# Quickstart Guide: Homepage Star Icon Implementation

**Feature**: 002-homepage-star-icon | **Date**: 2026-02-16  
**Branch**: copilot/add-star-icon-homepage-again  
**Estimated Time**: 30-45 minutes

## Overview

This guide provides step-by-step instructions to implement a star icon button in the application header with full accessibility support and visual feedback. The implementation involves adding ~65 lines of code to 2 existing files (App.tsx, App.css).

**Prerequisites**:
- Repository cloned locally
- Node.js 18+ installed
- Frontend development server can run (`npm run dev`)
- Familiarity with React and TypeScript

## Quick Start (5 minutes)

For experienced developers who want minimal guidance:

1. Add star icon button JSX to `frontend/src/App.tsx` header-actions div
2. Add event handlers `handleStarClick` and `handleKeyDown` in AppContent
3. Add state `useState(false)` for `isStarClicked`
4. Add `.star-icon-btn` CSS styles to `frontend/src/App.css`
5. Test: Run dev server, verify icon visible, click works, keyboard accessible

Full details in sections below.

---

## Step-by-Step Implementation

### Step 1: Open Files (2 minutes)

```bash
cd frontend/src
```

Open in editor:
- `App.tsx` (component logic)
- `App.css` (styling)

**Checkpoint**: Both files open and ready for editing.

---

### Step 2: Add CSS Styles First (5 minutes)

**Why first**: Prevents Flash of Unstyled Content (FOUC) when component renders.

**File**: `frontend/src/App.css`  
**Location**: After line 83 (after `.theme-toggle-btn:hover { ... }`)

**Add**:
```css
.star-icon-btn {
  background: transparent;
  border: none;
  padding: 6px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
}

.star-icon-btn:hover {
  color: #DAA520;
  transform: scale(1.1);
}

.star-icon-btn:active {
  transform: scale(0.95);
  color: #DAA520;
}

.star-icon-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

**Checkpoint**: Save file, no syntax errors.

---

### Step 3: Add React State (3 minutes)

**File**: `frontend/src/App.tsx`  
**Location**: Inside `AppContent` function, after line 26 (after existing hooks like `useAuth`, `useAppTheme`)

**Add**:
```tsx
  const [isStarClicked, setIsStarClicked] = useState(false);
```

**Import check**: Ensure `useState` is imported at top of file:
```tsx
import { useState } from 'react'; // Add if not present
```

**Checkpoint**: No TypeScript errors. State hook added to component.

---

### Step 4: Add Event Handlers (5 minutes)

**File**: `frontend/src/App.tsx`  
**Location**: Inside `AppContent` function, after line 50 (after all hooks, before `if (authLoading)` check)

**Add**:
```tsx
  const handleStarClick = () => {
    if (isStarClicked) return; // Debounce rapid clicks
    
    setIsStarClicked(true);
    setTimeout(() => setIsStarClicked(false), 300);
    
    // Visual feedback provided by CSS animation
    console.log('Star icon clicked - Favorites feature');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault(); // Prevent Space key scrolling
      handleStarClick();
    }
  };
```

**Checkpoint**: No TypeScript errors. Handlers defined above JSX return statement.

---

### Step 5: Add Star Icon Button JSX (7 minutes)

**File**: `frontend/src/App.tsx`  
**Location**: Inside `.header-actions` div, **before** the theme toggle button (around line 86)

**Find this code**:
```tsx
        <div className="header-actions">
          <button 
            className="theme-toggle-btn"
```

**Insert BEFORE theme-toggle-btn**:
```tsx
        <div className="header-actions">
          <button 
            className="star-icon-btn"
            onClick={handleStarClick}
            onKeyDown={handleKeyDown}
            aria-label="Favorites"
            tabIndex={0}
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
            </svg>
          </button>
          <button 
            className="theme-toggle-btn"
```

**Checkpoint**: 
- Star icon button added before theme toggle
- Proper JSX indentation maintained
- No syntax errors

---

### Step 6: Type Check (2 minutes)

```bash
cd frontend
npm run type-check
```

**Expected output**: No errors

**If errors occur**:
- Check `useState` is imported
- Verify handler function signatures match
- Ensure JSX is properly closed

**Checkpoint**: Type check passes.

---

### Step 7: Start Development Server (3 minutes)

```bash
cd frontend
npm run dev
```

**Expected output**:
```
VITE ready in XXX ms
➜  Local:   http://localhost:5173/
```

Open browser to `http://localhost:5173/`

**Checkpoint**: Server running, application loads.

---

### Step 8: Visual Verification (5 minutes)

**Test 1: Icon Visibility**
- ✓ Star icon appears in header top-right area
- ✓ Icon is between page title and theme toggle button
- ✓ Icon has neutral gray color (not gold yet)

**Test 2: Hover State** (desktop/mouse only)
- ✓ Hover mouse over star icon
- ✓ Icon changes to gold color (#DAA520)
- ✓ Icon slightly increases in size (scale 1.1)
- ✓ Cursor changes to pointer

**Test 3: Click State**
- ✓ Click star icon
- ✓ Brief scale-down animation (95% size)
- ✓ Console log appears: "Star icon clicked - Favorites feature"
- ✓ Rapid clicks are debounced (300ms cooldown)

**Checkpoint**: All visual tests pass.

---

### Step 9: Keyboard Accessibility Test (5 minutes)

**Test 1: Tab Navigation**
1. Click in browser address bar (reset focus)
2. Press Tab key repeatedly
3. ✓ Star icon receives focus (visible blue outline)
4. ✓ Star icon is 2nd or 3rd tab stop from page top

**Test 2: Keyboard Activation**
1. Tab to star icon (blue outline visible)
2. Press **Enter** key
3. ✓ Console log appears
4. ✓ Same behavior as clicking

**Test 3: Space Key Activation**
1. Tab to star icon
2. Press **Space** key
3. ✓ Console log appears (no page scroll)
4. ✓ Same behavior as clicking

**Checkpoint**: All keyboard tests pass.

---

### Step 10: Theme Testing (3 minutes)

**Test 1: Light Theme**
- ✓ Star icon visible with neutral color
- ✓ Hover shows gold color
- ✓ Focus outline is blue and visible

**Test 2: Dark Theme**
1. Click theme toggle button (sun/moon icon)
2. ✓ Star icon remains visible
3. ✓ Neutral color adjusts for dark background
4. ✓ Gold hover color still visible
5. ✓ Focus outline still visible

**Checkpoint**: Icon works in both themes.

---

### Step 11: Mobile/Touch Testing (Optional, 5 minutes)

**If you have mobile device or browser dev tools**:

1. Open Chrome DevTools (F12)
2. Click "Toggle Device Toolbar" (Ctrl+Shift+M)
3. Select mobile device (e.g., iPhone SE)

**Test**:
- ✓ Star icon visible on mobile viewport
- ✓ Tap icon triggers click (console log)
- ✓ No hover state persists (expected on touch)
- ✓ Icon fits naturally in header layout

**Checkpoint**: Mobile works as expected.

---

### Step 12: Accessibility Audit (Optional, 5 minutes)

**Using Browser Dev Tools**:

1. Open Chrome DevTools → Lighthouse tab
2. Select "Accessibility" category only
3. Click "Analyze page load"

**Or manually check**:
- ✓ aria-label="Favorites" present in HTML
- ✓ tabIndex="0" present
- ✓ Button role implicit (<button> element)
- ✓ Color contrast meets WCAG AA (use contrast checker extension)

**Or use screen reader** (if available):
- ✓ VoiceOver (Mac) or NVDA (Windows) announces "Favorites button"

**Checkpoint**: Accessibility requirements met.

---

## Verification Checklist

Use this checklist to confirm implementation:

**Code Quality**:
- [ ] TypeScript type check passes (`npm run type-check`)
- [ ] No console errors in browser
- [ ] Code follows existing patterns (similar to theme toggle)
- [ ] Proper indentation and formatting

**Visual Requirements**:
- [ ] Star icon visible in header top-right
- [ ] Icon positioned before theme toggle button
- [ ] Default color is neutral (gray)
- [ ] Hover color is gold (#DAA520)
- [ ] Click animation visible (scale down briefly)

**Functional Requirements**:
- [ ] Click logs to console
- [ ] Rapid clicks are debounced (300ms)
- [ ] Works in light theme
- [ ] Works in dark theme

**Accessibility Requirements**:
- [ ] Tab key navigates to star icon
- [ ] Focus outline visible when focused
- [ ] Enter key activates icon
- [ ] Space key activates icon (no scroll)
- [ ] Screen reader announces "Favorites" (if tested)

**Cross-Platform** (if tested):
- [ ] Works on desktop browser
- [ ] Works on mobile/tablet (touch)
- [ ] Works on narrow viewports (320px+)

---

## Troubleshooting

### Issue: Star icon not visible

**Check**:
1. CSS file saved? Re-save App.css
2. Dev server running? Restart: `npm run dev`
3. Browser cache? Hard refresh: Ctrl+Shift+R
4. Console errors? Check browser DevTools console

**Fix**: Clear browser cache, restart dev server.

---

### Issue: TypeScript errors

**Error**: `'useState' is not defined`  
**Fix**: Add import: `import { useState } from 'react';`

**Error**: `Property 'key' does not exist on type KeyboardEvent`  
**Fix**: Update signature: `React.KeyboardEvent<HTMLButtonElement>`

---

### Issue: Icon doesn't change color on hover

**Check**:
1. CSS saved? Re-save App.css
2. Hover on correct element? (icon, not empty space around it)
3. Browser supports :hover? (not touch device)

**Fix**: Verify `.star-icon-btn:hover` rule is in App.css.

---

### Issue: Click doesn't log to console

**Check**:
1. Console tab open? Open DevTools → Console
2. Handler function defined? Check `handleStarClick` exists
3. onClick prop set? Check `onClick={handleStarClick}` in JSX

**Fix**: Verify handler connected in JSX button element.

---

### Issue: Keyboard navigation doesn't focus icon

**Check**:
1. tabIndex set? Verify `tabIndex={0}` in JSX
2. Button element used? (not div or span)
3. Focus outline visible? Might be faint, check `:focus-visible` CSS

**Fix**: Ensure `tabIndex={0}` and use semantic `<button>` element.

---

## Next Steps

### Immediate (MVP Complete)

After completing this guide:
1. Commit changes: `git add . && git commit -m "Add star icon to homepage header"`
2. Push to branch: `git push origin [branch-name]`
3. Request code review
4. Merge after approval

### Post-MVP Enhancements (Optional)

**Priority 1**: Add favorites modal (P3 user story)
- Show "No favorites yet" empty state when star clicked
- Add modal backdrop with click-to-close
- Add Escape key handler to close modal

**Priority 2**: Add favorites functionality
- Backend API to persist favorites
- useFavorites hook to manage state
- Toggle star between filled/outlined based on favorite status

**Priority 3**: Extend to other pages
- Show star icon on project detail pages
- Show star icon on task detail pages
- Sync favorites across pages

---

## Time Breakdown

| Step | Estimated Time | Cumulative |
|------|----------------|------------|
| 1. Open files | 2 min | 2 min |
| 2. Add CSS | 5 min | 7 min |
| 3. Add state | 3 min | 10 min |
| 4. Add handlers | 5 min | 15 min |
| 5. Add JSX | 7 min | 22 min |
| 6. Type check | 2 min | 24 min |
| 7. Start server | 3 min | 27 min |
| 8. Visual test | 5 min | 32 min |
| 9. Keyboard test | 5 min | 37 min |
| 10. Theme test | 3 min | 40 min |
| 11. Mobile test | 5 min | 45 min |
| 12. A11y audit | 5 min | 50 min |

**Total**: 40-50 minutes (30 min minimum, 50 min with optional tests)

---

## References

**Specification**: `specs/002-homepage-star-icon/spec.md`  
**Research**: `specs/002-homepage-star-icon/research.md`  
**Data Model**: `specs/002-homepage-star-icon/data-model.md`  
**Contracts**: `specs/002-homepage-star-icon/contracts/file-changes.md`

**WCAG Guidelines**:
- 1.4.11 Non-text Contrast (Level AA) - 3:1 minimum
- 2.1.1 Keyboard - All functionality available via keyboard
- 2.4.4 Link Purpose (In Context) - Link/button purpose clear
- 4.1.2 Name, Role, Value - UI components have accessible names

**Browser Support**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
