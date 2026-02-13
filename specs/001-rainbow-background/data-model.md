# Data Model: Rainbow Background Option

**Feature**: Rainbow Background Option  
**Branch**: `001-rainbow-background`  
**Date**: 2026-02-13

## Overview

This document defines the data entities, state management, and relationships for the rainbow background feature. The feature is entirely frontend-focused with no backend data persistence.

---

## Entities

### Entity 1: Rainbow Background Preference

**Description**: User's preference for whether the rainbow background effect is enabled or disabled.

**Attributes**:

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `enabled` | boolean | Yes | `false` | Whether rainbow background is currently active |
| `lastModified` | timestamp | No | - | ISO 8601 timestamp of last preference change (optional, for future analytics) |

**Validation Rules**:
- `enabled` must be boolean (true/false)
- `lastModified` if present must be valid ISO 8601 string

**Storage Location**: `localStorage` with key `tech-connect-rainbow-background`

**Storage Format**:
```typescript
// Stored as simple string for consistency with existing theme storage
type StoredValue = 'enabled' | 'disabled';

// Internal representation
interface RainbowPreference {
  enabled: boolean;
  lastModified?: string; // ISO 8601 format
}
```

**Lifecycle**:
1. **Read on mount**: Hook reads from localStorage on initial render
2. **Write on toggle**: Preference saved immediately when user toggles
3. **Persist across sessions**: Survives page reload, browser restart
4. **Graceful degradation**: If localStorage unavailable, defaults to `false` (disabled)

**Example**:
```typescript
// localStorage key: 'tech-connect-rainbow-background'
// localStorage value: 'enabled' or 'disabled'

const preference: RainbowPreference = {
  enabled: true,
  lastModified: '2026-02-13T22:30:00Z'
};
```

---

### Entity 2: Rainbow Background State

**Description**: Runtime UI state managed by React hook. Separate from persisted preference to allow session-only toggling when localStorage is unavailable.

**Attributes**:

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `isRainbowEnabled` | boolean | Yes | `false` | Current state of rainbow background in UI |
| `isStorageAvailable` | boolean | Yes | `true` | Whether localStorage is accessible |

**Managed By**: `useRainbowBackground` custom React hook

**State Transitions**:

```
┌─────────────────────────────────────────────────────────────┐
│                 Rainbow Background State Machine             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   [Initial Mount]                                            │
│         │                                                    │
│         ├──→ Read localStorage                              │
│         │                                                    │
│         ├──→ If value = 'enabled'  → State: enabled         │
│         ├──→ If value = 'disabled' → State: disabled        │
│         └──→ If no value/error     → State: disabled        │
│                                                             │
│   [User Clicks Toggle]                                       │
│         │                                                    │
│         ├──→ Toggle state: enabled ↔ disabled               │
│         │                                                    │
│         ├──→ Try write to localStorage                      │
│         │    ├──→ Success: Persisted                        │
│         │    └──→ Failure: Session-only (no error shown)   │
│         │                                                    │
│         └──→ Apply/remove CSS class on body element         │
│                                                             │
│   [Page Reload]                                              │
│         │                                                    │
│         └──→ Return to [Initial Mount]                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## State Management Architecture

### React Hook: useRainbowBackground

**Purpose**: Encapsulate rainbow background preference logic in reusable hook

**API**:
```typescript
interface UseRainbowBackgroundReturn {
  /**
   * Current state of rainbow background
   */
  isRainbowEnabled: boolean;
  
  /**
   * Toggle rainbow background on/off
   */
  toggleRainbow: () => void;
}

export function useRainbowBackground(): UseRainbowBackgroundReturn;
```

**Internal Implementation**:
```typescript
const STORAGE_KEY = 'tech-connect-rainbow-background';
const RAINBOW_CLASS = 'rainbow-background-active';

export function useRainbowBackground() {
  // 1. Initialize state from localStorage
  const [isRainbowEnabled, setIsRainbowEnabled] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored === 'enabled';
    } catch {
      return false; // localStorage unavailable
    }
  });

  // 2. Apply CSS class when state changes
  useEffect(() => {
    const bodyElement = document.body;
    if (isRainbowEnabled) {
      bodyElement.classList.add(RAINBOW_CLASS);
    } else {
      bodyElement.classList.remove(RAINBOW_CLASS);
    }
  }, [isRainbowEnabled]);

  // 3. Toggle function with localStorage persistence
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

**Integration in App Component**:
```typescript
function AppContent() {
  const { isRainbowEnabled, toggleRainbow } = useRainbowBackground();
  
  return (
    <div className="app-container">
      <header className="app-header">
        {/* ... */}
        <div className="header-actions">
          <button 
            className="rainbow-toggle-btn"
            onClick={toggleRainbow}
            aria-label={isRainbowEnabled ? 'Disable rainbow background' : 'Enable rainbow background'}
          >
            🌈
          </button>
          {/* Existing theme toggle */}
        </div>
      </header>
      {/* ... */}
    </div>
  );
}
```

---

## Data Flow

### User Interaction Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Rainbow Background Data Flow                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  👤 USER ACTION                                                      │
│  ─────────────                                                       │
│    │                                                                 │
│    │  Click rainbow toggle button (🌈)                              │
│    │                                                                 │
│    ▼                                                                 │
│  ┌─────────────────────────────────────────┐                        │
│  │  toggleRainbow() function called        │                        │
│  └─────────────────────────────────────────┘                        │
│    │                                                                 │
│    ▼                                                                 │
│  ┌─────────────────────────────────────────┐                        │
│  │  setIsRainbowEnabled(!current)          │                        │
│  │  ├─ Update React state                  │                        │
│  │  └─ Trigger re-render                   │                        │
│  └─────────────────────────────────────────┘                        │
│    │                                                                 │
│    ├─────────────────────────────────────────┐                      │
│    │                                         │                      │
│    ▼                                         ▼                      │
│  ┌─────────────────────────────────────────┐ ┌────────────────────┐ │
│  │  localStorage.setItem(...)              │ │  useEffect fires   │ │
│  │  Key: 'tech-connect-rainbow-background' │ │  Dependency: state │ │
│  │  Value: 'enabled' or 'disabled'         │ └────────────────────┘ │
│  └─────────────────────────────────────────┘   │                   │
│    │                                            ▼                   │
│    │                                  ┌────────────────────────────┐│
│    │                                  │ document.body.classList     ││
│    │                                  │ .add/.remove(...)           ││
│    │                                  │ 'rainbow-background-active' ││
│    │                                  └────────────────────────────┘│
│    │                                            │                   │
│    │                                            ▼                   │
│    │                                  ┌────────────────────────────┐│
│    │                                  │ CSS applies:                ││
│    │                                  │ - Animated gradient         ││
│    │                                  │ - Readability overlay       ││
│    │                                  │ - Reduced-motion handling   ││
│    │                                  └────────────────────────────┘│
│    │                                                                 │
│    ▼                                                                 │
│  ┌─────────────────────────────────────────┐                        │
│  │  UI Updates:                            │                        │
│  │  - Background animates/static           │                        │
│  │  - Button aria-label updates            │                        │
│  │  - Content remains readable             │                        │
│  └─────────────────────────────────────────┘                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Page Load Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Page Load / Initial Render                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  🌐 BROWSER LOADS PAGE                                               │
│  ──────────────────                                                  │
│    │                                                                 │
│    ▼                                                                 │
│  ┌─────────────────────────────────────────┐                        │
│  │  React component mounts                  │                        │
│  │  useRainbowBackground() called           │                        │
│  └─────────────────────────────────────────┘                        │
│    │                                                                 │
│    ▼                                                                 │
│  ┌─────────────────────────────────────────┐                        │
│  │  useState initializer executes           │                        │
│  │  ├─ Read localStorage                    │                        │
│  │  ├─ Parse value ('enabled'/'disabled')   │                        │
│  │  └─ Set initial state (true/false)       │                        │
│  └─────────────────────────────────────────┘                        │
│    │                                                                 │
│    ▼                                                                 │
│  ┌─────────────────────────────────────────┐                        │
│  │  First useEffect runs                    │                        │
│  │  ├─ Check isRainbowEnabled state         │                        │
│  │  └─ Apply/remove class on body           │                        │
│  └─────────────────────────────────────────┘                        │
│    │                                                                 │
│    ▼                                                                 │
│  ┌─────────────────────────────────────────┐                        │
│  │  Component renders with correct state    │                        │
│  │  - Toggle button shows correct state     │                        │
│  │  - Background visible if enabled         │                        │
│  └─────────────────────────────────────────┘                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## CSS Class Application

**Target Element**: `document.body`

**Applied Class**: `rainbow-background-active`

**Rationale**:
- Body element ensures background covers entire viewport
- Single class application (no multiple elements)
- Consistent with dark-mode pattern (class on `html` element)
- Easy to inspect in DevTools

**CSS Cascade**:
```css
/* Base styles - always present */
body {
  font-family: -apple-system, ...;
  color: var(--color-text);
  background: var(--color-bg-secondary);
}

/* Rainbow background - applied when enabled */
body.rainbow-background-active {
  background: linear-gradient(...); /* Rainbow gradient */
  background-size: 200% 200%;
  animation: rainbow-slide 15s ease infinite;
}

/* Accessibility - disable animation if requested */
@media (prefers-reduced-motion: reduce) {
  body.rainbow-background-active {
    animation: none;
  }
}
```

**Overlay for Readability**:
```css
/* Applied to app-container to ensure content readability */
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

## Error Handling

### localStorage Unavailable

**Scenario**: User has disabled localStorage or browser in private mode

**Behavior**:
1. Initial state defaults to `false` (disabled)
2. Toggle still works for current session
3. Preference not persisted across reloads
4. No error message shown to user (graceful degradation)

**Implementation**:
```typescript
try {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === 'enabled';
} catch {
  // localStorage unavailable - default to disabled
  return false;
}
```

---

### Invalid localStorage Value

**Scenario**: localStorage contains corrupted/unexpected value

**Behavior**:
1. Treat any value other than 'enabled' as disabled
2. No error thrown
3. First toggle will overwrite with valid value

**Implementation**:
```typescript
const stored = localStorage.getItem(STORAGE_KEY);
return stored === 'enabled'; // Strict comparison, anything else = false
```

---

## Relationships

### Relationship 1: Rainbow Background ↔ Theme Mode

**Type**: Independent / Complementary

**Description**: Rainbow background works independently of dark/light theme mode. Both can be enabled simultaneously.

**Interaction**:
- Rainbow background uses `var(--color-bg-secondary)` for overlay
- CSS variable value changes based on theme mode
- Overlay automatically adapts to current theme
- User can combine:
  - Light mode + Rainbow background
  - Dark mode + Rainbow background
  - Light mode + No rainbow
  - Dark mode + No rainbow

**Storage**:
- Theme preference: `tech-connect-theme-mode` → 'light' | 'dark'
- Rainbow preference: `tech-connect-rainbow-background` → 'enabled' | 'disabled'

---

### Relationship 2: Rainbow Background ↔ Reduced Motion Preference

**Type**: Accessibility Override

**Description**: System-level accessibility setting overrides animation behavior while preserving rainbow colors.

**Interaction**:
- User enables rainbow background → animated gradient
- If `prefers-reduced-motion: reduce` → static gradient
- Colors remain visible, animation disabled
- No JavaScript check needed (CSS media query handles it)

**Implementation**:
```css
/* Normal: animated */
body.rainbow-background-active {
  animation: rainbow-slide 15s ease infinite;
}

/* Reduced motion: static */
@media (prefers-reduced-motion: reduce) {
  body.rainbow-background-active {
    animation: none;
  }
}
```

---

## State Persistence Matrix

| Storage Location | Key | Value Type | Persistence | Scope |
|-----------------|-----|------------|-------------|-------|
| localStorage | `tech-connect-rainbow-background` | `'enabled' \| 'disabled'` | Permanent (until cleared) | Per-origin |
| React State | `isRainbowEnabled` | boolean | Session-only | Component tree |
| DOM | `body.classList` | `'rainbow-background-active'` | Session-only | Document |

---

## Testing Scenarios

### Data Layer Tests

**Unit Tests (useRainbowBackground hook)**:

1. **Initial state from localStorage**:
   - localStorage = 'enabled' → state = true
   - localStorage = 'disabled' → state = false
   - localStorage = null → state = false
   - localStorage = invalid → state = false

2. **Toggle updates state and storage**:
   - false → true → localStorage set to 'enabled'
   - true → false → localStorage set to 'disabled'

3. **localStorage unavailable**:
   - Read returns false
   - Toggle updates state but doesn't throw error
   - Subsequent toggles work in-memory

4. **CSS class application**:
   - state = true → body has class 'rainbow-background-active'
   - state = false → body lacks class 'rainbow-background-active'

**E2E Tests (Playwright)**:

1. **Persistence across reload**:
   - Enable rainbow → reload page → rainbow still enabled
   - Disable rainbow → reload page → rainbow still disabled

2. **UI state sync**:
   - Enable rainbow → button aria-label = 'Disable rainbow background'
   - Disable rainbow → button aria-label = 'Enable rainbow background'

---

## Performance Considerations

### State Updates

**React Re-renders**:
- Toggle causes single App component re-render
- No child components re-render (unless they consume hook)
- No Redux/Context, minimal propagation

**localStorage I/O**:
- Read: Once on mount (~1ms)
- Write: On every toggle (~1ms)
- No polling or continuous reads

**CSS Class Changes**:
- classList.add/remove is synchronous (~0.1ms)
- Triggers CSS recalculation + repaint
- GPU-accelerated animation (compositor thread)

**Total Toggle Latency**: <5ms (SC-002: <1s ✅)

---

## Future Extensibility

While out of scope for current feature, the data model supports future enhancements:

**Potential Extensions** (not implemented):
1. **lastModified timestamp**: Track when preference changed (analytics)
2. **animationSpeed**: Allow user to adjust animation speed
3. **gradientStyle**: Support multiple rainbow patterns
4. **analytics events**: Track feature usage
5. **A/B testing**: Randomize default state for new users

**Backward Compatibility**:
- Current storage format ('enabled'/'disabled') can be extended to object format
- Migration path: Read old format, write new format on first toggle
- No breaking changes for existing users

---

## Summary

The rainbow background feature has a simple data model:

1. **Single Entity**: Boolean preference (enabled/disabled)
2. **Storage**: localStorage with graceful degradation
3. **State Management**: Custom React hook (useRainbowBackground)
4. **CSS Integration**: Single class on body element
5. **Independence**: Works with any theme mode
6. **Accessibility**: Respects reduced-motion preference

All data flows are synchronous and local to the client. No API calls, no backend state, no shared state between users.
