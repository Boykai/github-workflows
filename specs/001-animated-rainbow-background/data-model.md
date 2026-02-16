# Data Model: Animated Rainbow Background

**Feature Branch**: `copilot/add-animated-rainbow-background-again`  
**Created**: 2026-02-16  
**Phase**: Phase 1 - Design

## Overview

This document defines the entities, state management, and CSS variable changes required for the animated rainbow background feature. The design integrates with the existing theme system while remaining orthogonal to light/dark mode preferences.

## Entities

### 1. Rainbow Background Preference

**Description**: User's persistent choice to enable or disable the rainbow background.

**Storage**: Browser localStorage

**Key**: `rainbow-background-enabled`

**Type**: boolean (stored as string "true" or "false")

**Default Value**: `true` (enabled by default per spec requirement)

**Lifecycle**:
- **Created**: On first application launch (reads from localStorage, defaults to true if not present)
- **Updated**: When user toggles the setting in the settings UI
- **Read**: On application initialization and during settings UI render
- **Deleted**: Never (can be set to false but not removed)

**Validation Rules**:
- Must be parseable as boolean (strings "true" or "false")
- Invalid values default to true

**Related Code**:
- Hook: `frontend/src/hooks/useRainbowBackground.ts` (to be created)
- Settings component: Location TBD during implementation

### 2. Background Animation State

**Description**: Current state of the rainbow background animation system.

**Storage**: CSS class on `<body>` element + CSS animation state

**Representation**:
```typescript
// Implicit state via DOM
document.body.classList.contains('rainbow-background-active') // boolean

// Animation state tracked by browser CSS engine
// - animation-play-state (running | paused)
// - animation-iteration (current cycle position)
```

**Lifecycle**:
- **Created**: When rainbow preference is enabled and page loads
- **Updated**: When user toggles rainbow preference or reduced motion setting changes
- **Destroyed**: When rainbow preference is disabled or page unloads

**State Transitions**:
```
Initial (load) → Check localStorage → Apply class (enabled=true) | No class (enabled=false)
User toggle ON → Add class + save localStorage
User toggle OFF → Remove class + save localStorage
Reduced motion detected → Override animation via CSS media query
```

**Related Code**:
- CSS: `frontend/src/index.css` (rainbow-background-active styles)
- Hook: `frontend/src/hooks/useRainbowBackground.ts` (manages class toggle)

### 3. CSS Custom Properties (Unchanged)

**Description**: Existing theme system CSS variables remain unchanged.

**Existing Variables** (from `frontend/src/index.css`):
- `--color-bg`: Component surface background
- `--color-bg-secondary`: Page/body background (currently used, will be overridden when rainbow active)
- `--color-text`: Primary text color
- All other theme variables remain functional

**Rainbow Background Implementation**:
- Does NOT modify CSS custom properties
- Directly sets `background` on `body.rainbow-background-active`
- Overlay (if needed for contrast) applied via `body.rainbow-background-active::before`

**Rationale**:
- Avoids breaking existing component styling
- Keeps rainbow system isolated and removable
- Maintains compatibility with light/dark theme switching

## CSS Changes

### Modified Files

#### frontend/src/index.css

**Additions** (approximately 45 new lines):

```css
/* Rainbow Background Animation - Added for animated-rainbow-background feature */

@keyframes rainbow-flow {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 200% 50%;
  }
}

/* Rainbow background active state */
body.rainbow-background-active {
  background: linear-gradient(
    90deg,
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
  animation: rainbow-flow 20s linear infinite;
}

/* Contrast overlay for readability */
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

/* Accessibility: Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
  body.rainbow-background-active {
    animation: none;
    background: linear-gradient(90deg, #ff0000 0%, #9400d3 100%);
    background-size: 100% 100%;
  }
}

/* Dark mode adjustment for overlay (optional enhancement) */
html.dark-mode-active body.rainbow-background-active::before {
  background: rgba(0, 0, 0, 0.6); /* Slightly darker overlay for dark mode */
}
```

**No Deletions**: All existing CSS remains unchanged

**Line Count**: +45 lines (approximately)

**Impact Analysis**:
- Isolated to body element with specific class
- No impact when class is not applied
- Existing theme system unaffected
- Performance impact: Minimal (GPU-accelerated CSS animation)

### New Files

None. All CSS changes are additions to existing `index.css`.

## Component State Changes

### New Hook: useRainbowBackground

**File**: `frontend/src/hooks/useRainbowBackground.ts` (to be created)

**Interface**:
```typescript
export function useRainbowBackground(): [boolean, (enabled: boolean) => void] {
  // Returns [enabled, setEnabled] tuple
  // enabled: current rainbow background state
  // setEnabled: function to update state and persist to localStorage
}
```

**Responsibilities**:
1. Read initial state from localStorage on mount
2. Apply/remove `rainbow-background-active` class on body element
3. Persist state changes to localStorage
4. Provide React-friendly state management interface

**Dependencies**:
- React (useState, useEffect)
- Browser APIs (localStorage, document.body.classList)

**Example Usage**:
```typescript
// In settings component
const [rainbowEnabled, setRainbowEnabled] = useRainbowBackground();

return (
  <label>
    <input
      type="checkbox"
      checked={rainbowEnabled}
      onChange={(e) => setRainbowEnabled(e.target.checked)}
    />
    Rainbow Background
  </label>
);
```

### Modified Component: Settings

**File**: Location TBD (to be located during implementation)

**Changes**:
1. Import `useRainbowBackground` hook
2. Add rainbow background toggle UI element
3. Wire toggle to hook state

**No Changes to**:
- App.tsx (no initialization required, hook handles everything)
- index.css theme variables
- Any other components

## Database Schema

**N/A** - This feature uses client-side localStorage only. No backend persistence required.

## API Contracts

**N/A** - This is a frontend-only feature with no backend API requirements.

## State Management Flow

```
User Loads App
    ↓
useRainbowBackground hook initializes
    ↓
Read localStorage['rainbow-background-enabled']
    ↓
Default to true if not set
    ↓
Apply/remove 'rainbow-background-active' class on body
    ↓
CSS animations activate if class present
    ↓
User toggles setting
    ↓
setRainbowEnabled(newValue) called
    ↓
Update localStorage
    ↓
Update body class
    ↓
CSS animations update immediately
```

## Browser Compatibility

**Minimum Requirements**:
- CSS animations support (all modern browsers)
- localStorage API (all browsers since IE8)
- CSS `@media (prefers-reduced-motion)` (graceful degradation if not supported)

**Tested Browsers** (per spec assumptions):
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Fallback Behavior**:
- Browsers without CSS animation support: standard background displays
- Browsers without prefers-reduced-motion: animation always runs (acceptable per spec)
- Browsers without localStorage: preference resets each session (acceptable degradation)

## Performance Considerations

**Memory**:
- CSS animations: Negligible (<1KB browser memory)
- localStorage: ~50 bytes for preference storage
- No memory leaks (CSS engine managed)

**CPU**:
- GPU-accelerated CSS animation: <1% CPU on modern devices
- No JavaScript RAF loop required
- No continuous re-renders

**Network**:
- No additional network requests
- CSS bundled with existing stylesheet

**Optimization Strategies**:
1. Use CSS `will-change: background` hint for GPU acceleration
2. Avoid JavaScript-based animation (uses CSS engine)
3. Reduced motion disables animation for affected users

## Testing Considerations

**Unit Tests** (if applicable):
- useRainbowBackground hook: state management and localStorage persistence
- Mock localStorage for isolated testing

**Integration Tests** (if applicable):
- Settings toggle updates body class
- Preference persists across page reloads

**Manual Testing Required**:
1. Visual confirmation of rainbow animation
2. Contrast validation across all screens
3. Reduced motion accessibility testing
4. Performance testing on older devices
5. Cross-browser compatibility validation

**Accessibility Testing**:
- Screen reader compatibility (ensure background doesn't interfere)
- Keyboard navigation with rainbow background enabled
- Reduced motion preference respected
- Contrast ratio validation (4.5:1 minimum)

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Contrast insufficient on some screens | Medium | High | Add/adjust overlay opacity, test all screens |
| Performance issues on older devices | Low | Medium | Reduced motion fallback, GPU acceleration |
| Conflicts with future theme changes | Low | Low | Isolated implementation, clear documentation |
| Users disable due to distraction | Medium | Low | Clear toggle in settings, off by default option |

## Future Enhancements (Out of Scope)

1. Customizable rainbow speed setting
2. Alternative gradient patterns (vertical, diagonal, radial)
3. Color palette customization
4. Sync preference across devices (requires backend)
5. A/B testing for default on/off state

## Summary

The data model for this feature is intentionally minimal:
- One boolean preference in localStorage
- One body class for activation
- One CSS animation definition
- One React hook for state management

This simplicity ensures:
- Easy implementation and testing
- Minimal risk to existing functionality
- Clear rollback path if needed
- Performance characteristics remain excellent
