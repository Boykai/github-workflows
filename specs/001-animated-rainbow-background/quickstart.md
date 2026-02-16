# Implementation Quickstart: Animated Rainbow Background

**Feature Branch**: `copilot/add-animated-rainbow-background-again`  
**Created**: 2026-02-16  
**Estimated Time**: 2-3 hours

## Prerequisites

- Node.js and npm installed
- Repository cloned and dependencies installed (`npm install` in frontend/)
- Familiarity with React hooks and CSS animations
- Browser devtools for testing and validation

## Overview

This guide walks through implementing the animated rainbow background feature in dependency order. Each step includes validation to ensure correctness before proceeding.

## Step 1: Add CSS Animation Styles (30 minutes)

**File**: `frontend/src/index.css`

**Action**: Add rainbow background CSS after line 30 (after dark theme overrides)

**Code to Add**:

```css
/* Rainbow Background Animation - Feature: animated-rainbow-background */

@keyframes rainbow-flow {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 200% 50%;
  }
}

body.rainbow-background-active {
  background: linear-gradient(
    90deg,
    #ff0000 0%,
    #ff7f00 14%,
    #ffff00 28%,
    #00ff00 42%,
    #0000ff 57%,
    #4b0082 71%,
    #9400d3 85%,
    #ff0000 100%
  );
  background-size: 200% 200%;
  animation: rainbow-flow 20s linear infinite;
}

body.rainbow-background-active::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  pointer-events: none;
  z-index: -1;
}

@media (prefers-reduced-motion: reduce) {
  body.rainbow-background-active {
    animation: none;
    background: linear-gradient(90deg, #ff0000 0%, #9400d3 100%);
    background-size: 100% 100%;
  }
}

html.dark-mode-active body.rainbow-background-active::before {
  background: rgba(0, 0, 0, 0.6);
}
```

**Validation**:

```bash
# In frontend/ directory
cd frontend

# Run linter
npm run lint

# Start dev server
npm run dev
```

**Manual Test**:
1. Open http://localhost:5173 in browser
2. Open browser devtools (F12)
3. In console, run: `document.body.classList.add('rainbow-background-active')`
4. Verify: Rainbow animation appears and loops smoothly
5. Verify: Text is readable with dark overlay
6. In console, run: `document.body.classList.remove('rainbow-background-active')`
7. Verify: Background returns to normal

**Success Criteria**:
- ✅ No lint errors
- ✅ Animation runs smoothly (~20 second cycle)
- ✅ Text remains readable
- ✅ Overlay doesn't block clicks
- ✅ All hex colors are lowercase

---

## Step 2: Create Rainbow Background Hook (30 minutes)

**File**: `frontend/src/hooks/useRainbowBackground.ts` (new file)

**Action**: Create the hook file with state management logic

**Full File Content**:

```typescript
import { useState, useEffect } from 'react';

/**
 * Hook to manage rainbow background preference
 * 
 * Reads from and persists to localStorage under key 'rainbow-background-enabled'
 * Applies/removes 'rainbow-background-active' class on body element
 * 
 * @returns Tuple of [enabled: boolean, setEnabled: (value: boolean) => void]
 * 
 * @example
 * const [rainbowEnabled, setRainbowEnabled] = useRainbowBackground();
 * 
 * return (
 *   <input 
 *     type="checkbox" 
 *     checked={rainbowEnabled}
 *     onChange={(e) => setRainbowEnabled(e.target.checked)}
 *   />
 * );
 */
export function useRainbowBackground(): [boolean, (enabled: boolean) => void] {
  const [enabled, setEnabledState] = useState<boolean>(() => {
    try {
      const stored = localStorage.getItem('rainbow-background-enabled');
      return stored !== null ? stored === 'true' : true; // default true per spec
    } catch (error) {
      console.warn('Failed to read rainbow background preference:', error);
      return true; // default to enabled on error
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('rainbow-background-enabled', String(enabled));
    } catch (error) {
      console.warn('Failed to save rainbow background preference:', error);
    }

    if (enabled) {
      document.body.classList.add('rainbow-background-active');
    } else {
      document.body.classList.remove('rainbow-background-active');
    }
  }, [enabled]);

  return [enabled, setEnabledState];
}
```

**Validation**:

```bash
# Type check
npm run type-check

# Should pass with no errors
```

**Manual Test** (temporary component):

Create a temporary test file `frontend/src/TestRainbow.tsx`:

```typescript
import { useRainbowBackground } from './hooks/useRainbowBackground';

export function TestRainbow() {
  const [enabled, setEnabled] = useRainbowBackground();
  
  return (
    <div style={{ padding: '20px' }}>
      <label>
        <input 
          type="checkbox" 
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
        />
        Rainbow Background
      </label>
      <p>Current state: {enabled ? 'Enabled' : 'Disabled'}</p>
    </div>
  );
}
```

Import and render in `App.tsx` temporarily:

```typescript
import { TestRainbow } from './TestRainbow';

// In App component, add:
<TestRainbow />
```

**Test Steps**:
1. Reload the app
2. Verify rainbow background appears by default
3. Uncheck the checkbox
4. Verify rainbow background disappears
5. Check the checkbox
6. Verify rainbow background reappears
7. Open devtools > Application > Local Storage
8. Verify `rainbow-background-enabled` key exists
9. Reload the page
10. Verify preference is maintained

**Success Criteria**:
- ✅ No TypeScript errors
- ✅ Hook toggles body class correctly
- ✅ Preference persists in localStorage
- ✅ Preference persists across page reloads
- ✅ Defaults to enabled (true)

**Cleanup**: Remove `TestRainbow.tsx` and its import from `App.tsx` after validation

---

## Step 3: Initialize on App Load (15 minutes)

**File**: `frontend/src/App.tsx`

**Action**: Add hook initialization to main App component

**Code Change**:

At the top of `App.tsx`, add import:

```typescript
import { useRainbowBackground } from './hooks/useRainbowBackground';
```

Inside the `App` function, at the beginning, add:

```typescript
function App() {
  // Initialize rainbow background on app load
  useRainbowBackground();
  
  // ... rest of App component code
}
```

**Alternative**: If initialization should be in `main.tsx` instead, follow a similar pattern

**Validation**:

```bash
# Type check
npm run type-check

# Run dev server
npm run dev
```

**Manual Test**:
1. Clear localStorage in devtools (Application > Local Storage > Clear All)
2. Reload the app
3. Verify rainbow background appears by default
4. Open devtools console
5. Run: `localStorage.setItem('rainbow-background-enabled', 'false')`
6. Reload the app
7. Verify rainbow background does NOT appear
8. Open devtools console
9. Run: `localStorage.setItem('rainbow-background-enabled', 'true')`
10. Reload the app
11. Verify rainbow background appears

**Success Criteria**:
- ✅ No TypeScript errors
- ✅ Rainbow background auto-initializes on load
- ✅ Respects saved localStorage preference
- ✅ Defaults to enabled when no preference saved

---

## Step 4: Add Settings UI Toggle (45 minutes)

**Action**: Locate existing settings interface and add rainbow background toggle

### Step 4a: Locate Settings Component

**Search for settings-related files**:

```bash
# Search for settings components
find frontend/src -name "*settings*" -o -name "*Settings*"

# Or search for theme toggle (rainbow toggle should go near it)
grep -r "theme" frontend/src/components --include="*.tsx" --include="*.ts"

# Or search for useAppTheme usage
grep -r "useAppTheme" frontend/src --include="*.tsx"
```

**Expected**: Find a settings component or section where theme toggle exists

### Step 4b: Add Rainbow Toggle

**File**: `frontend/src/components/[SettingsComponent].tsx` (replace with actual file)

**Import the hook**:

```typescript
import { useRainbowBackground } from '../../hooks/useRainbowBackground';
```

**Add state**:

```typescript
const [rainbowEnabled, setRainbowEnabled] = useRainbowBackground();
```

**Add UI element** (adapt to match existing toggle pattern):

```typescript
<div className="setting-item">
  <label htmlFor="rainbow-background-toggle">
    Rainbow Background
  </label>
  <input
    id="rainbow-background-toggle"
    type="checkbox"
    checked={rainbowEnabled}
    onChange={(e) => setRainbowEnabled(e.target.checked)}
    aria-label="Toggle animated rainbow background"
  />
</div>
```

**Note**: Adapt the HTML structure and CSS classes to match the existing settings UI pattern

**Validation**:

```bash
# Type check
npm run type-check

# Lint check
npm run lint

# Run dev server
npm run dev
```

**Manual Test**:
1. Navigate to settings in the app
2. Verify "Rainbow Background" toggle appears
3. Verify toggle is checked by default (rainbow active)
4. Click toggle off
5. Verify rainbow background disappears immediately (<0.5s)
6. Click toggle on
7. Verify rainbow background reappears immediately (<0.5s)
8. Reload the app
9. Navigate to settings
10. Verify toggle state matches rainbow background state

**Success Criteria**:
- ✅ Toggle appears in settings UI
- ✅ Toggle matches existing UI patterns
- ✅ Toggle reflects current state accurately
- ✅ Toggle updates background immediately
- ✅ Preference persists across reloads
- ✅ Keyboard accessible (can tab to it and toggle with Space)

---

## Step 5: Accessibility Testing (30 minutes)

### Test Reduced Motion

**Enable reduced motion**:
- **macOS**: System Preferences > Accessibility > Display > Reduce motion
- **Windows**: Settings > Ease of Access > Display > Show animations
- **Linux**: Varies by desktop environment

**Test**:
1. Enable reduced motion in OS settings
2. Reload the app
3. Verify animation stops (static gradient instead of animated)
4. Verify no console errors

### Test Keyboard Navigation

1. Use Tab key to navigate to rainbow background toggle
2. Verify toggle gets focus indicator
3. Press Space key to toggle
4. Verify background changes

### Test Contrast

**Tool**: Use browser devtools color picker or online contrast checker

**Steps**:
1. Enable rainbow background
2. Select text element in devtools
3. Note text color (e.g., `#24292f` in light mode)
4. Sample background color at multiple points:
   - Start of animation (red area)
   - Middle of animation (green/blue area)
   - End of animation (violet area)
5. Calculate contrast ratios using tool like WebAIM Contrast Checker
6. Verify all ratios ≥ 4.5:1 (WCAG AA)

**If contrast fails**:
- Increase overlay opacity in `index.css` (e.g., `rgba(0, 0, 0, 0.6)`)
- Or adjust rainbow color saturation/brightness
- Re-test until all pass

---

## Step 6: Performance Testing (20 minutes)

### Frame Rate Test

1. Open Chrome DevTools > Performance tab
2. Click Record button
3. Let recording run for 30 seconds with rainbow active
4. Stop recording
5. Check frame rate in the performance chart
6. Verify: Average FPS ≥ 30 (target 60)

**If performance issues**:
- Check for CSS `will-change` optimization
- Verify GPU acceleration is active (no CPU-based animation)
- Consider reducing animation complexity

### Memory Test

1. Open Chrome DevTools > Memory tab
2. Take heap snapshot
3. Use app normally for 5 minutes with rainbow active
4. Take another heap snapshot
5. Compare snapshots
6. Verify: No significant memory increase (<5MB growth)

### Responsiveness Test

1. Enable rainbow background
2. Perform typical user tasks (navigate, interact with UI)
3. Verify no lag or delays compared to without rainbow
4. Test on different screen sizes (responsive design)

---

## Step 7: Cross-Browser Testing (30 minutes)

Test in each browser:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**For each browser**:
1. Open app
2. Verify rainbow background appears
3. Verify animation is smooth
4. Verify text is readable
5. Toggle off in settings
6. Verify background disappears
7. Reload and verify preference persists
8. Check console for errors (should be none)

**Expected**: Feature works consistently across all browsers

---

## Step 8: Final Validation (15 minutes)

### Run All Checks

```bash
# In frontend/ directory

# Lint
npm run lint

# Type check
npm run type-check

# Format (optional)
npm run format

# Build (ensure production build works)
npm run build
```

### Manual Checklist

- [ ] Rainbow background displays by default on fresh load
- [ ] Animation loops smoothly without stutters
- [ ] Text is readable across all screens
- [ ] Settings toggle works and persists preference
- [ ] Reduced motion is respected
- [ ] Frame rate ≥ 30fps
- [ ] No memory leaks
- [ ] No console errors or warnings
- [ ] Works in Chrome, Firefox, Safari, Edge
- [ ] Keyboard accessible
- [ ] Contrast meets WCAG AA (≥4.5:1)

### Verify Feature Completeness

All functional requirements met:
- ✅ FR-001: Animated rainbow gradient displays on all main screens by default
- ✅ FR-002: Animation loops seamlessly
- ✅ FR-003: Sufficient contrast maintained
- ✅ FR-004: Toggle control in settings
- ✅ FR-005: Preference persists between sessions
- ✅ FR-006: Changes apply immediately
- ✅ FR-007: No performance degradation
- ✅ FR-008: Respects reduced motion preference
- ✅ FR-009: Animation timing is subtle (20s cycle)
- ✅ FR-010: Fallback background if animation fails

---

## Troubleshooting

### Issue: Animation is choppy or slow

**Solution**: 
- Verify CSS is using GPU acceleration
- Check browser performance tab for bottlenecks
- Reduce overlay opacity complexity if needed

### Issue: Contrast is insufficient

**Solution**:
- Increase overlay opacity: `rgba(0, 0, 0, 0.6)` or `0.7`
- Test contrast ratios again
- Consider darkening rainbow colors slightly

### Issue: Preference not persisting

**Solution**:
- Check localStorage in devtools
- Verify no localStorage errors in console
- Ensure hook's useEffect is running
- Check for conflicting code that might clear localStorage

### Issue: Toggle not appearing in settings

**Solution**:
- Verify import path is correct
- Check component structure matches existing patterns
- Ensure settings component is actually rendering
- Check for TypeScript/build errors

### Issue: Reduced motion not working

**Solution**:
- Verify OS setting is actually enabled
- Test with `@media (prefers-reduced-motion: reduce)` media query in devtools
- Check CSS specificity (ensure media query isn't being overridden)

---

## Time Estimates

| Step | Estimated Time | Notes |
|------|----------------|-------|
| Step 1: CSS | 30 min | Straightforward CSS addition |
| Step 2: Hook | 30 min | Standard React hook pattern |
| Step 3: Init | 15 min | Simple initialization |
| Step 4: Settings | 45 min | Requires locating and adapting to existing UI |
| Step 5: A11y | 30 min | Multiple accessibility tests |
| Step 6: Performance | 20 min | Profiling and validation |
| Step 7: Cross-browser | 30 min | Testing in multiple browsers |
| Step 8: Final | 15 min | Final checks and validation |
| **Total** | **3h 35min** | Buffer included for issues |

---

## Next Steps

After completing this guide:

1. Commit changes to branch `copilot/add-animated-rainbow-background-again`
2. Push to GitHub
3. Update PR description with implementation summary
4. Request code review
5. Address any review feedback
6. Merge when approved

---

## References

- Spec: `specs/001-animated-rainbow-background/spec.md`
- Research: `specs/001-animated-rainbow-background/research.md`
- Data Model: `specs/001-animated-rainbow-background/data-model.md`
- Contracts: `specs/001-animated-rainbow-background/contracts/implementation-contracts.md`

---

## Notes

- Feature is additive and non-breaking
- All changes are isolated and can be rolled back easily
- No backend modifications required
- Follows existing codebase patterns (React hooks, localStorage, CSS themes)
