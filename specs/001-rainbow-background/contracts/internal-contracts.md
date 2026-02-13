# Rainbow Background Contracts

**Feature**: Rainbow Background Option  
**Branch**: `001-rainbow-background`  
**Date**: 2026-02-13

## Overview

This feature is entirely frontend-only with no API contracts. This document defines the internal contracts between React components, hooks, and CSS.

---

## Internal Contracts

### 1. React Hook Contract: useRainbowBackground

**Location**: `frontend/src/hooks/useRainbowBackground.ts`

**Purpose**: Provide stateful rainbow background preference management

**Public API**:
```typescript
interface UseRainbowBackgroundReturn {
  /**
   * Current state of rainbow background (true = enabled, false = disabled)
   */
  isRainbowEnabled: boolean;
  
  /**
   * Toggle rainbow background on/off
   * Updates React state, localStorage, and DOM class
   */
  toggleRainbow: () => void;
}

/**
 * Custom hook for managing rainbow background preference
 * 
 * @returns {UseRainbowBackgroundReturn} Rainbow background state and toggle function
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { isRainbowEnabled, toggleRainbow } = useRainbowBackground();
 *   
 *   return (
 *     <button onClick={toggleRainbow}>
 *       {isRainbowEnabled ? 'Disable' : 'Enable'} Rainbow
 *     </button>
 *   );
 * }
 * ```
 */
export function useRainbowBackground(): UseRainbowBackgroundReturn;
```

**Behavior Contract**:
- Hook reads from localStorage on mount (synchronous)
- Returns `false` if localStorage unavailable or contains invalid value
- Toggle function is stable (doesn't change across re-renders)
- State updates trigger body class changes via useEffect
- localStorage writes are wrapped in try-catch (never throws)

**Side Effects**:
- Applies/removes `rainbow-background-active` class on `document.body`
- Writes to localStorage with key `tech-connect-rainbow-background`
- Triggers React re-render when state changes

---

### 2. localStorage Contract

**Storage Key**: `tech-connect-rainbow-background`

**Value Type**: `'enabled' | 'disabled'`

**Read Behavior**:
```typescript
const value = localStorage.getItem('tech-connect-rainbow-background');
// value = 'enabled'  → Rainbow is on
// value = 'disabled' → Rainbow is off
// value = null       → No preference (default: off)
// value = anything else → Invalid (default: off)
```

**Write Behavior**:
```typescript
// Enable rainbow
localStorage.setItem('tech-connect-rainbow-background', 'enabled');

// Disable rainbow
localStorage.setItem('tech-connect-rainbow-background', 'disabled');
```

**Error Handling**:
- All localStorage operations wrapped in try-catch
- Read errors return default value (`false`)
- Write errors silently ignored (feature becomes session-only)

**Storage Lifecycle**:
- Created on first toggle
- Persists until user clears browser data
- No automatic expiration
- No server-side backup

---

### 3. CSS Contract

**Required CSS Classes**:

```css
/* Applied to body when rainbow is enabled */
.rainbow-background-active {
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

/* Animation keyframes */
@keyframes rainbow-slide {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}

/* Accessibility: disable animation for reduced-motion users */
@media (prefers-reduced-motion: reduce) {
  .rainbow-background-active {
    animation: none;
  }
}
```

**Overlay for Readability**:
```css
/* Applied to app-container to ensure text is readable */
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

**Button Styles**:
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

## Summary

The rainbow background feature has the following contracts:

1. **React Hook Contract**: useRainbowBackground() provides isRainbowEnabled + toggleRainbow
2. **localStorage Contract**: Key 'tech-connect-rainbow-background', values 'enabled'/'disabled'
3. **CSS Contract**: Class 'rainbow-background-active' on body, animation keyframes, overlay styles
4. **DOM Contract**: Body element receives class, classList API used
5. **Component Contract**: Integration in App.tsx header-actions
6. **Accessibility Contract**: WCAG AA compliant, reduced-motion support, keyboard accessible

All contracts are internal (no external API contracts needed).
