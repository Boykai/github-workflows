# Quickstart: Rainbow Background Option

**Feature**: Rainbow Background Option  
**Branch**: `001-rainbow-background`  
**Date**: 2026-02-13

## Overview

This guide helps developers set up their environment, understand the implementation, and test the rainbow background feature.

---

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager
- Git for cloning repository
- Modern browser (Chrome 90+, Firefox 88+, Safari 14+, or Edge 90+)
- Basic React and TypeScript knowledge
- Familiarity with CSS animations (helpful but not required)

---

## Setup Instructions

### 1. Clone and Install

```bash
# Navigate to project root
cd github-workflows

# Install frontend dependencies (if not already done)
cd frontend
npm install

# Return to project root
cd ..
```

### 2. Verify Existing Infrastructure

Before implementing the feature, verify the existing theme system works:

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser and:
1. Log in with GitHub OAuth
2. Click the theme toggle button (🌙/☀️) in the header
3. Verify dark/light mode switches correctly
4. Check browser DevTools → Application → Local Storage
5. Confirm `tech-connect-theme-mode` key exists

**Expected**: Theme toggle works, preference persists after reload.

---

## Implementation Steps

### Step 1: Create the useRainbowBackground Hook

**File**: `frontend/src/hooks/useRainbowBackground.ts`

```typescript
/**
 * Custom hook for managing rainbow background preference
 */

import { useState, useEffect } from 'react';

const STORAGE_KEY = 'tech-connect-rainbow-background';
const RAINBOW_CLASS = 'rainbow-background-active';

export function useRainbowBackground() {
  // Initialize state from localStorage
  const [isRainbowEnabled, setIsRainbowEnabled] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored === 'enabled';
    } catch {
      return false; // localStorage unavailable
    }
  });

  // Apply CSS class when state changes
  useEffect(() => {
    const bodyElement = document.body;
    if (isRainbowEnabled) {
      bodyElement.classList.add(RAINBOW_CLASS);
    } else {
      bodyElement.classList.remove(RAINBOW_CLASS);
    }
  }, [isRainbowEnabled]);

  // Toggle function with localStorage persistence
  const toggleRainbow = () => {
    setIsRainbowEnabled((current) => {
      const newState = !current;
      try {
        localStorage.setItem(STORAGE_KEY, newState ? 'enabled' : 'disabled');
      } catch {
        // Silently fail - user still gets session-only toggle
      }
      return newState;
    });
  };

  return {
    isRainbowEnabled,
    toggleRainbow,
  };
}
```

**Verification**:
```bash
# Check syntax
npm run type-check
```

---

### Step 2: Add Rainbow Background CSS

**File**: `frontend/src/index.css`

Add the following at the end of the file:

```css
/* Rainbow Background Feature */
body.rainbow-background-active {
  background: linear-gradient(
    45deg,
    #ff0000 0%,   /* Red */
    #ff7f00 14%,  /* Orange */
    #ffff00 28%,  /* Yellow */
    #00ff00 42%,  /* Green */
    #0000ff 57%,  /* Blue */
    #4b0082 71%,  /* Indigo */
    #9400d3 85%,  /* Violet */
    #ff0000 100%  /* Red (loop) */
  );
  background-size: 200% 200%;
  animation: rainbow-slide 15s ease infinite;
}

@keyframes rainbow-slide {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 200% 50%;
  }
}

/* Accessibility: disable animation for users with reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  body.rainbow-background-active {
    animation: none;
  }
}
```

---

### Step 3: Add Readability Overlay

**File**: `frontend/src/App.css`

Add the following after the `.app-container` rule:

```css
/* Readability overlay for rainbow background */
.app-container::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-bg-secondary);
  opacity: 0.85;
  z-index: -1;
  pointer-events: none;
}
```

---

### Step 4: Add Toggle Button Styles

**File**: `frontend/src/App.css`

Add after the `.theme-toggle-btn` styles:

```css
.rainbow-toggle-btn {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  padding: 6px 12px;
  font-size: 18px;
  transition: all 0.2s ease;
}

.rainbow-toggle-btn:hover {
  background: var(--color-border);
  transform: scale(1.05);
}
```

---

### Step 5: Integrate into App Component

**File**: `frontend/src/App.tsx`

Add the import at the top:

```typescript
import { useRainbowBackground } from '@/hooks/useRainbowBackground';
```

Inside the `AppContent` function, add the hook:

```typescript
function AppContent() {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const { isDarkMode, toggleTheme } = useAppTheme();
  const { isRainbowEnabled, toggleRainbow } = useRainbowBackground(); // Add this line
  
  // ... rest of code
}
```

In the header actions section, add the rainbow toggle button:

```typescript
<div className="header-actions">
  <button 
    className="rainbow-toggle-btn"
    onClick={toggleRainbow}
    aria-label={isRainbowEnabled ? 'Disable rainbow background' : 'Enable rainbow background'}
    title={isRainbowEnabled ? 'Disable rainbow background' : 'Enable rainbow background'}
  >
    🌈
  </button>
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

**Verification**:
```bash
npm run type-check
npm run lint
```

---

## Testing the Feature

### Manual Testing

1. **Start the development server**:
   ```bash
   npm run dev
   ```

2. **Test basic functionality**:
   - Navigate to http://localhost:5173
   - Log in with GitHub OAuth
   - Click the rainbow button (🌈) in the header
   - **Expected**: Background displays animated rainbow gradient
   - Click again
   - **Expected**: Rainbow background disappears

3. **Test persistence**:
   - Enable rainbow background
   - Refresh the page (F5 or Cmd+R)
   - **Expected**: Rainbow background still enabled
   - Disable rainbow background
   - Refresh the page
   - **Expected**: Rainbow background still disabled

4. **Test theme interaction**:
   - Enable rainbow background
   - Toggle dark/light mode (🌙/☀️ button)
   - **Expected**: Rainbow background works in both modes
   - Text remains readable in both modes

5. **Test accessibility (if available)**:
   - Open System Preferences/Settings
   - Enable "Reduce motion" accessibility setting
   - Return to browser and enable rainbow background
   - **Expected**: Rainbow colors visible but static (no animation)

6. **Test localStorage unavailable**:
   - Open DevTools → Application → Local Storage
   - Right-click → Clear all (or disable in browser settings)
   - Toggle rainbow background
   - **Expected**: Works for current session
   - Refresh page
   - **Expected**: Returns to disabled (no persistence)

7. **Test button accessibility**:
   - Tab to rainbow button using keyboard
   - **Expected**: Focus visible on button
   - Press Enter or Space
   - **Expected**: Rainbow toggles
   - Hover over button
   - **Expected**: Tooltip shows "Enable/Disable rainbow background"

---

### Automated Testing

#### Unit Tests

**File**: `frontend/src/hooks/useRainbowBackground.test.ts`

```typescript
import { renderHook, act } from '@testing-library/react';
import { useRainbowBackground } from './useRainbowBackground';

describe('useRainbowBackground', () => {
  beforeEach(() => {
    localStorage.clear();
    document.body.className = '';
  });

  it('initializes with disabled state by default', () => {
    const { result } = renderHook(() => useRainbowBackground());
    expect(result.current.isRainbowEnabled).toBe(false);
  });

  it('reads initial state from localStorage', () => {
    localStorage.setItem('tech-connect-rainbow-background', 'enabled');
    const { result } = renderHook(() => useRainbowBackground());
    expect(result.current.isRainbowEnabled).toBe(true);
  });

  it('toggles state and updates localStorage', () => {
    const { result } = renderHook(() => useRainbowBackground());
    
    act(() => {
      result.current.toggleRainbow();
    });
    
    expect(result.current.isRainbowEnabled).toBe(true);
    expect(localStorage.getItem('tech-connect-rainbow-background')).toBe('enabled');
  });

  it('applies CSS class to body element', () => {
    const { result } = renderHook(() => useRainbowBackground());
    
    act(() => {
      result.current.toggleRainbow();
    });
    
    expect(document.body.classList.contains('rainbow-background-active')).toBe(true);
  });

  it('handles localStorage unavailable gracefully', () => {
    const mockGetItem = jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('localStorage unavailable');
    });
    
    const { result } = renderHook(() => useRainbowBackground());
    
    expect(result.current.isRainbowEnabled).toBe(false);
    expect(() => result.current.toggleRainbow()).not.toThrow();
    
    mockGetItem.mockRestore();
  });
});
```

**Run tests**:
```bash
npm test
```

---

#### E2E Tests (Playwright)

**File**: `frontend/e2e/rainbow-background.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Rainbow Background', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app and login (adjust URL and auth as needed)
    await page.goto('http://localhost:5173');
    // Add OAuth login steps here if needed
  });

  test('toggle button is visible', async ({ page }) => {
    const button = page.locator('button.rainbow-toggle-btn');
    await expect(button).toBeVisible();
    await expect(button).toHaveText('🌈');
  });

  test('clicking toggle enables rainbow background', async ({ page }) => {
    const button = page.locator('button.rainbow-toggle-btn');
    
    // Initial state: disabled
    await expect(page.locator('body.rainbow-background-active')).not.toBeVisible();
    
    // Click to enable
    await button.click();
    await expect(page.locator('body.rainbow-background-active')).toBeVisible();
    
    // Click to disable
    await button.click();
    await expect(page.locator('body.rainbow-background-active')).not.toBeVisible();
  });

  test('rainbow background persists across reload', async ({ page }) => {
    const button = page.locator('button.rainbow-toggle-btn');
    
    // Enable rainbow
    await button.click();
    await expect(page.locator('body.rainbow-background-active')).toBeVisible();
    
    // Reload page
    await page.reload();
    
    // Should still be enabled
    await expect(page.locator('body.rainbow-background-active')).toBeVisible();
  });

  test('button aria-label updates correctly', async ({ page }) => {
    const button = page.locator('button.rainbow-toggle-btn');
    
    // Initial state
    await expect(button).toHaveAttribute('aria-label', 'Enable rainbow background');
    
    // After enabling
    await button.click();
    await expect(button).toHaveAttribute('aria-label', 'Disable rainbow background');
  });
});
```

**Run E2E tests**:
```bash
npm run test:e2e
```

---

## Debugging Tips

### Issue: Button not visible

**Check**:
- Browser console for errors
- Verify import statement in App.tsx
- Verify button is inside `.header-actions` div
- Check CSS class names match

**Fix**: Review Step 5 (App integration)

---

### Issue: Rainbow background not appearing

**Check**:
- Browser DevTools → Elements → Inspect `<body>` tag
- Verify class `rainbow-background-active` is present when enabled
- Check browser console for CSS errors
- Verify CSS added to index.css

**Fix**: Review Step 2 (CSS addition)

---

### Issue: Text not readable with rainbow background

**Check**:
- Verify overlay CSS added to App.css
- Check `.app-container::before` pseudo-element in DevTools
- Verify `z-index: -1` and `opacity: 0.85`

**Fix**: Review Step 3 (readability overlay)

---

### Issue: Preference not persisting

**Check**:
- DevTools → Application → Local Storage
- Verify `tech-connect-rainbow-background` key exists
- Check value is 'enabled' or 'disabled'
- Verify no localStorage errors in console

**Fix**: Review Step 1 (hook implementation), check try-catch blocks

---

### Issue: Animation causing motion sickness

**Check**:
- System accessibility settings for "Reduce motion"
- CSS media query for `prefers-reduced-motion`
- Verify animation: none; applies in reduced motion mode

**Fix**: Review Step 2 (CSS), ensure media query present

---

## Performance Profiling

### Measure Toggle Latency

1. Open DevTools → Performance tab
2. Click "Record"
3. Click rainbow toggle button
4. Click "Stop"
5. Analyze timeline:
   - Look for React update (should be <5ms)
   - Look for localStorage write (should be <1ms)
   - Look for style recalculation (should be <10ms)

**Expected Total**: <20ms from click to visual update

---

### Monitor Animation Performance

1. Enable rainbow background
2. Open DevTools → Performance → Rendering
3. Check "FPS meter"
4. Check "Paint flashing"
5. Verify:
   - FPS stays above 55 (target: 60fps)
   - No excessive paint flashing
   - GPU layer used for animation

**Fix if performance issues**:
- Add `will-change: background-position` to CSS
- Verify GPU acceleration enabled in browser

---

## Browser Testing Checklist

Test the feature in multiple browsers:

- [ ] Chrome 90+ (Windows/Mac/Linux)
- [ ] Firefox 88+ (Windows/Mac/Linux)
- [ ] Safari 14+ (Mac/iOS)
- [ ] Edge 90+ (Windows/Mac)

For each browser:
- [ ] Rainbow toggle works
- [ ] Animation smooth (60fps)
- [ ] Text readable
- [ ] Preference persists
- [ ] Reduced motion respected (if testable)
- [ ] No console errors

---

## Deployment Checklist

Before merging to main:

- [ ] All unit tests pass (`npm test`)
- [ ] All E2E tests pass (`npm run test:e2e`)
- [ ] Linting passes (`npm run lint`)
- [ ] Type checking passes (`npm run type-check`)
- [ ] Manual testing completed (see Testing section)
- [ ] Cross-browser testing completed
- [ ] Accessibility audit completed
- [ ] Performance profiling shows <100ms overhead
- [ ] Feature works in production build (`npm run build && npm run preview`)
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow convention

---

## Rollback Plan

If critical issues found in production:

### Option 1: Feature Flag (Quick Disable)

**Not implemented in v1**, but could be added:

```typescript
const FEATURE_ENABLED = import.meta.env.VITE_RAINBOW_ENABLED !== 'false';

export function useRainbowBackground() {
  if (!FEATURE_ENABLED) {
    return { isRainbowEnabled: false, toggleRainbow: () => {} };
  }
  // ... rest of implementation
}
```

Then set `VITE_RAINBOW_ENABLED=false` in production `.env`.

---

### Option 2: Hide Button (CSS Only)

Add to production CSS:

```css
.rainbow-toggle-btn {
  display: none !important;
}
```

Users who already enabled rainbow will keep it, but new users can't enable it.

---

### Option 3: Full Revert

Revert the commit:

```bash
git revert <commit-hash>
git push origin main
```

This removes all feature code.

---

## Next Steps

After successful implementation:

1. **Monitor Usage**:
   - Add analytics to track toggle events (optional)
   - Monitor for user feedback or complaints
   - Check performance metrics in production

2. **Potential Enhancements** (out of scope for v1):
   - Add more background options (sunset, ocean, etc.)
   - Allow adjusting animation speed
   - Add color customization
   - Sync preference across devices (requires backend)

3. **Documentation**:
   - Update main README.md with feature mention
   - Add screenshots to docs
   - Create user-facing help article

---

## Support and Troubleshooting

For issues or questions:

1. Check browser console for errors
2. Verify all steps in this quickstart followed correctly
3. Review the research.md and data-model.md for design decisions
4. Check GitHub issues for similar problems
5. Open a new issue with:
   - Browser and version
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots or video

---

## Summary

**Key Files Modified**:
- `frontend/src/hooks/useRainbowBackground.ts` (new)
- `frontend/src/App.tsx` (modified)
- `frontend/src/index.css` (modified)
- `frontend/src/App.css` (modified)

**Key Features**:
- ✅ Toggle button in header
- ✅ Animated rainbow gradient
- ✅ Readability overlay
- ✅ localStorage persistence
- ✅ Theme-independent
- ✅ Accessibility support
- ✅ Cross-browser compatible

**Testing Coverage**:
- ✅ Unit tests for hook
- ✅ E2E tests for user flow
- ✅ Manual testing checklist
- ✅ Performance profiling

The rainbow background feature is ready for development! 🌈
