# Implementation Contracts: Animated Rainbow Background

**Feature Branch**: `copilot/add-animated-rainbow-background-again`  
**Created**: 2026-02-16  
**Phase**: Phase 1 - Design

## Overview

This document specifies the exact changes required to implement the animated rainbow background feature. Each contract defines inputs, outputs, acceptance criteria, and validation steps for specific code changes.

## Contract 1: CSS Animation Styles

**File**: `frontend/src/index.css`

**Type**: Enhancement (additions only)

**Location**: After existing dark theme overrides (after line 30)

**Changes Required**:

1. Add rainbow-flow keyframes animation
2. Add rainbow-background-active body class styles
3. Add contrast overlay via pseudo-element
4. Add reduced motion media query
5. Add dark mode overlay adjustment

**Exact Addition** (insert after line 30):

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

**Acceptance Criteria**:
- [ ] CSS is valid and lint-free
- [ ] No conflicts with existing styles
- [ ] Animation runs at ~20 seconds per cycle
- [ ] Background loops seamlessly without jumps
- [ ] Overlay does not block pointer events
- [ ] Reduced motion media query disables animation
- [ ] Hex color values use lowercase (per codebase convention)

**Validation**:
```bash
# Lint CSS
npm run lint

# Visual test
npm run dev
# Manually add "rainbow-background-active" class to body in devtools
# Verify animation runs smoothly
# Verify text is readable with overlay
```

**Dependencies**: None

**Risks**: Low - isolated CSS additions with clear class gate

---

## Contract 2: Rainbow Background Hook

**File**: `frontend/src/hooks/useRainbowBackground.ts` (new file)

**Type**: New file

**Purpose**: Manage rainbow background state and localStorage persistence

**Full Implementation**:

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

**Acceptance Criteria**:
- [ ] TypeScript compiles without errors
- [ ] Hook reads from localStorage on mount
- [ ] Hook defaults to `true` if no stored value
- [ ] Hook defaults to `true` on localStorage errors
- [ ] setEnabled updates both state and localStorage
- [ ] setEnabled adds/removes body class correctly
- [ ] useEffect only runs when enabled changes
- [ ] No memory leaks (cleanup not needed as body persists)

**Validation**:
```bash
# Type check
npm run type-check

# Unit test (if implemented)
npm run test -- useRainbowBackground

# Manual test
# Import and use hook in a component
# Verify localStorage updates
# Verify body class toggles
# Verify preference persists across reloads
```

**Dependencies**: React (useState, useEffect)

**Risks**: Low - standard React hook pattern

---

## Contract 3: Settings UI Integration

**File**: To be determined during implementation (likely `frontend/src/components/settings/*` or similar)

**Type**: Enhancement (add toggle control)

**Purpose**: Provide user interface to toggle rainbow background

**Requirements**:

1. Locate existing settings interface
2. Import `useRainbowBackground` hook
3. Add toggle control with label "Rainbow Background"
4. Wire toggle to hook state

**Example Implementation** (adapt to actual settings component):

```typescript
import { useRainbowBackground } from '../hooks/useRainbowBackground';

// Inside settings component
const [rainbowEnabled, setRainbowEnabled] = useRainbowBackground();

return (
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
);
```

**Acceptance Criteria**:
- [ ] Toggle is visible in settings interface
- [ ] Toggle reflects current rainbow background state
- [ ] Clicking toggle immediately updates background
- [ ] Label is accessible (associated with input)
- [ ] Matches existing settings UI patterns
- [ ] Placed near theme toggle (related visual preferences)

**Validation**:
```bash
# Visual test
npm run dev
# Navigate to settings
# Verify toggle appears and functions
# Toggle on/off and verify background changes immediately
# Reload page and verify preference persists
```

**Dependencies**: 
- useRainbowBackground hook (Contract 2)
- Existing settings component structure

**Risks**: Medium - requires locating and modifying existing settings component

---

## Contract 4: App Initialization

**File**: `frontend/src/main.tsx` OR `frontend/src/App.tsx` (determine during implementation)

**Type**: Enhancement (add hook initialization)

**Purpose**: Initialize rainbow background on app load

**Option A - If using main.tsx**:
```typescript
import { useRainbowBackground } from './hooks/useRainbowBackground';

// Inside a wrapper component or App component
function AppWithRainbow() {
  useRainbowBackground(); // Initialize on mount
  return <App />;
}
```

**Option B - If using App.tsx**:
```typescript
import { useRainbowBackground } from './hooks/useRainbowBackground';

function App() {
  useRainbowBackground(); // Initialize on mount
  
  // ... rest of App component
}
```

**Acceptance Criteria**:
- [ ] Hook initializes on app load
- [ ] Saved preference applies immediately on load
- [ ] No flash of unstyled content (class applied synchronously)
- [ ] No errors in console

**Validation**:
```bash
# Test fresh load
npm run dev
# Clear localStorage
# Reload and verify rainbow background appears (default true)

# Test with saved preference
# Toggle off in settings
# Reload and verify rainbow background stays off
# Toggle on in settings
# Reload and verify rainbow background appears
```

**Dependencies**: useRainbowBackground hook (Contract 2)

**Risks**: Low - single hook call in root component

---

## Cross-Cutting Concerns

### Accessibility

**Requirements**:
1. Reduced motion preference must be respected (handled in CSS Contract 1)
2. Toggle must be keyboard accessible (handled in Contract 3)
3. Contrast must meet WCAG AA (4.5:1) - requires manual validation

**Validation**:
```bash
# Test reduced motion
# Enable reduced motion in OS settings
# Verify animation stops or slows significantly

# Test keyboard navigation
# Tab to rainbow background toggle in settings
# Press Space to toggle
# Verify background changes

# Test contrast
# Use browser devtools or contrast checker tool
# Sample text color and background color at multiple animation points
# Verify all ratios ≥ 4.5:1
```

### Performance

**Requirements**:
1. Animation must maintain ≥30fps (target 60fps)
2. No memory leaks over extended use
3. No impact on app responsiveness

**Validation**:
```bash
# Monitor performance
npm run dev
# Open browser devtools > Performance tab
# Record for 30 seconds with rainbow background active
# Verify frame rate stays above 30fps
# Verify no increasing memory usage

# Test app responsiveness
# Enable rainbow background
# Perform typical user tasks
# Verify no lag or delays compared to without rainbow
```

### Browser Compatibility

**Requirements**:
1. Works in Chrome, Firefox, Safari, Edge (latest 2 versions)
2. Graceful degradation in older browsers

**Validation**:
```bash
# Manual testing across browsers required
# Chrome: Verify animation works
# Firefox: Verify animation works
# Safari: Verify animation works
# Edge: Verify animation works
# Test localStorage persistence in each browser
```

### Code Style

**Requirements**:
1. Follows existing TypeScript/React patterns
2. Follows existing CSS conventions (lowercase hex colors)
3. Passes lint checks
4. Passes type checks

**Validation**:
```bash
npm run lint
npm run type-check
npm run format
```

---

## Implementation Order

Recommended sequence to minimize risk and enable incremental testing:

1. **Contract 1**: CSS Animation Styles
   - Can be tested in isolation by manually adding class in devtools
   - No code dependencies

2. **Contract 2**: Rainbow Background Hook
   - Can be tested in isolation or with a temporary test component
   - No other code dependencies

3. **Contract 4**: App Initialization  
   - Enables hook to initialize on app load
   - Allows testing preference persistence

4. **Contract 3**: Settings UI Integration
   - Final piece enabling user control
   - Depends on all previous contracts

## Rollback Plan

If issues arise, remove in reverse order:

1. Remove settings toggle (Contract 3) - disables user control
2. Remove app initialization (Contract 4) - stops auto-initialization
3. Remove hook file (Contract 2) - removes state management
4. Remove CSS (Contract 1) - removes visual changes

Each step can be done independently without breaking the application.

## Testing Matrix

| Contract | Unit Test | Integration Test | Manual Test | Accessibility Test | Performance Test |
|----------|-----------|------------------|-------------|-------------------|------------------|
| Contract 1 (CSS) | N/A | N/A | Required | Required | Required |
| Contract 2 (Hook) | Optional | Optional | Required | N/A | N/A |
| Contract 3 (Settings) | Optional | Optional | Required | Required | N/A |
| Contract 4 (Init) | N/A | Optional | Required | N/A | N/A |

## Success Criteria (Overall)

Feature is complete when:

1. ✅ All contracts implemented and validated
2. ✅ Rainbow background displays by default on app load
3. ✅ Animation loops smoothly at ~20 seconds per cycle
4. ✅ Text is readable across all screens (≥4.5:1 contrast)
5. ✅ Settings toggle works and persists preference
6. ✅ Reduced motion preference is respected
7. ✅ Performance remains acceptable (≥30fps)
8. ✅ All lint and type checks pass
9. ✅ No console errors or warnings
10. ✅ Feature can be toggled off by users

## Notes

- CSS hex colors must use lowercase per codebase convention (memory: "CSS hex color values must use lowercase letters in all frontend CSS files")
- Existing theme system remains functional (memory: "Application uses CSS custom properties for theming")
- No backend changes required
- Feature is additive and non-breaking
