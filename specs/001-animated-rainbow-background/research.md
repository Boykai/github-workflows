# Research: Animated Rainbow Background

**Feature Branch**: `copilot/add-animated-rainbow-background-again`  
**Created**: 2026-02-16  
**Phase**: Phase 0 - Research and Technical Discovery

## Executive Summary

This document resolves all technical unknowns and establishes architectural decisions for implementing an animated rainbow gradient background with accessibility support, theme integration, and user preference controls.

## Clarifications Resolved

### 1. Contrast Ratio Requirement (WCAG AA vs AAA)

**Decision**: Target WCAG AA (4.5:1 for normal text, 3:1 for large text)

**Rationale**:
- WCAG AA is the industry standard for web accessibility and legally required in many jurisdictions (ADA, Section 508)
- AAA (7:1) is aspirational but often impractical for colorful designs without significant UI restructuring
- The specification allows for semi-transparent overlay techniques to maintain AA compliance
- Modern web applications (GitHub, Twitter, Google) typically target AA, not AAA
- AA provides sufficient readability for most users while allowing design flexibility

**Implementation Approach**:
- Use a semi-transparent dark overlay (rgba(0, 0, 0, 0.4-0.6)) over the rainbow gradient
- Alternatively, use muted/desaturated rainbow colors that naturally provide better contrast
- Test contrast at multiple animation cycle points to ensure compliance throughout
- Provide fallback to standard background if contrast cannot be maintained

**Alternatives Considered**:
- AAA compliance: Rejected due to requiring very muted colors that defeat the "vibrant" requirement
- No contrast guarantee: Rejected due to accessibility requirements and potential legal issues
- Dynamic text shadow: Rejected due to performance concerns and visual artifacts

### 2. Minimum Acceptable Frame Rate

**Decision**: 30fps minimum, 60fps target

**Rationale**:
- 30fps is the threshold for "smooth" animation perception by human eye
- 60fps matches display refresh rates and provides noticeably smoother experience
- The specification states "moderate specifications" (devices from last 5 years), which can reliably hit 30fps
- CSS animations with GPU acceleration can easily achieve 60fps on modern devices
- 30fps minimum ensures graceful degradation on lower-powered devices

**Implementation Approach**:
- Use CSS keyframe animations (GPU-accelerated via `transform` or `background-position`)
- Leverage `will-change` CSS property for optimization hints
- Use `@media (prefers-reduced-motion: reduce)` to disable or slow animation for accessibility
- Monitor via browser Performance API during development
- Consider RequestAnimationFrame for JavaScript-based fallbacks (if needed)

**Alternatives Considered**:
- 60fps strict minimum: Rejected due to excluding some legitimate use cases (older tablets, budget laptops)
- 24fps minimum: Rejected as below smooth perception threshold, would feel "choppy"
- No frame rate requirement: Rejected due to lack of quality guarantee

### 3. Animation Duration/Speed

**Decision**: 20-second cycle duration (one complete rainbow rotation)

**Rationale**:
- Specification requires "subtle and not distracting" animation
- Research shows 15-30 seconds is ideal for background animations that shouldn't draw attention
- Faster animations (5-10s) are too attention-grabbing and can cause motion sickness
- Slower animations (30s+) feel static and lose the "animated" quality
- 20 seconds provides noticeable but gentle movement

**Implementation Approach**:
- CSS `animation-duration: 20s` on the gradient animation
- Use `animation-iteration-count: infinite` for seamless looping
- Use `animation-timing-function: linear` for consistent motion
- Support reduced motion by extending duration to 60s or disabling entirely

**Alternatives Considered**:
- 5-10 seconds: Rejected as too fast and potentially distracting
- 30+ seconds: Rejected as too slow to feel animated
- Variable speed based on user preference: Rejected to minimize complexity in MVP

## Technical Research

### 4. CSS Animation Technique for Rainbow Gradients

**Decision**: CSS linear-gradient with background-position animation

**Rationale**:
- Pure CSS approach requires no JavaScript for core animation
- GPU-accelerated via `transform` or `background-position`
- Seamlessly loops without visual discontinuities
- Works across all modern browsers (Chrome, Firefox, Safari, Edge)
- Minimal performance impact compared to canvas or WebGL approaches

**Implementation Approach**:
```css
@keyframes rainbow-flow {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}

body {
  background: linear-gradient(
    90deg,
    #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3,
    #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3
  );
  background-size: 200% 200%;
  animation: rainbow-flow 20s linear infinite;
}
```

**Alternatives Considered**:
- Canvas-based animation: Rejected due to complexity and accessibility concerns (screen readers)
- SVG gradients with SMIL animation: Rejected due to limited browser support and complexity
- JavaScript RAF loop: Rejected due to performance concerns and battery impact
- CSS filter hue-rotate: Rejected as it affects entire page, not just background

### 5. Accessibility: Reduced Motion Support

**Decision**: Respect `prefers-reduced-motion` media query

**Rationale**:
- WCAG 2.1 Success Criterion 2.3.3 requires respecting reduced motion preferences
- Affects users with vestibular disorders, motion sensitivity, epilepsy
- Modern browsers (Chrome 74+, Firefox 63+, Safari 10.1+) support this media query
- Graceful degradation: static gradient or standard background

**Implementation Approach**:
```css
@media (prefers-reduced-motion: reduce) {
  body {
    animation: none;
    background: linear-gradient(90deg, #ff0000, #9400d3);
    background-size: 100% 100%;
  }
}
```

**Alternatives Considered**:
- Ignore reduced motion: Rejected due to accessibility requirements and potential user harm
- Slow animation instead of disabling: Considered viable, may implement as enhancement
- User setting overrides OS preference: Possible future enhancement

### 6. Contrast Overlay Technique

**Decision**: Semi-transparent dark overlay with backdrop-filter

**Rationale**:
- Maintains vibrant rainbow colors while ensuring text readability
- Simple to implement via a single pseudo-element
- No changes to existing component styles required
- Can be toggled on/off independently of rainbow background

**Implementation Approach**:
```css
body::before {
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
```

**Alternatives Considered**:
- Muted rainbow colors: Rejected as reduces "vibrant" quality
- Text shadows on all elements: Rejected due to performance and visual inconsistency
- White text on all screens: Rejected as conflicts with existing theme system

### 7. Preference Persistence Pattern

**Decision**: localStorage with React hook wrapper

**Rationale**:
- Application already uses localStorage for theme preferences (see `useAppTheme.ts`)
- Consistent with existing patterns in the codebase
- No backend changes required
- Synchronizes across tabs via storage events
- Works offline

**Implementation Approach**:
```typescript
// hooks/useRainbowBackground.ts
export function useRainbowBackground() {
  const [enabled, setEnabled] = useState(() => {
    const stored = localStorage.getItem('rainbow-background-enabled');
    return stored !== null ? stored === 'true' : true; // default true
  });

  useEffect(() => {
    localStorage.setItem('rainbow-background-enabled', String(enabled));
    document.body.classList.toggle('rainbow-background-active', enabled);
  }, [enabled]);

  return [enabled, setEnabled] as const;
}
```

**Alternatives Considered**:
- Backend persistence: Rejected as overkill for UI preference
- sessionStorage: Rejected as preference should persist across sessions
- Cookies: Rejected as localStorage is simpler and already used

### 8. Integration with Existing Theme System

**Decision**: Parallel system that respects but doesn't replace theme colors

**Rationale**:
- Existing theme system (`index.css`) controls UI component colors, not body background
- Rainbow background should work with both light and dark themes
- Theme toggle should remain functional with rainbow background enabled
- No breaking changes to existing theme variables

**Implementation Approach**:
- Apply rainbow gradient to `body` background when enabled
- Existing components use `--color-bg` and `--color-bg-secondary` (unchanged)
- Dark mode overlay (if needed) adjusts opacity based on `html.dark-mode-active`
- Theme system and rainbow system are orthogonal

**Alternatives Considered**:
- Replace theme system: Rejected as breaking change and out of scope
- Conditional theme variables: Rejected as overly complex
- Rainbow theme as third theme option: Rejected as rainbow is a background option, not a theme

### 9. Settings UI Location

**Decision**: Add toggle to existing settings interface (to be located during implementation)

**Rationale**:
- Specification assumes existing settings interface
- Consistent with existing UI patterns
- No new navigation or modal dialogs required

**Implementation Approach**:
- Locate existing settings component during implementation phase
- Add "Rainbow Background" toggle switch
- Use existing toggle component patterns from the codebase
- Place near theme toggle (related visual preferences)

**Alternatives Considered**:
- New settings modal: Rejected as spec assumes existing interface
- Command palette: Rejected as not discoverable enough
- Keyboard shortcut only: Rejected due to discoverability issues

### 10. Fallback Strategy

**Decision**: Graceful degradation to standard background on animation failure

**Rationale**:
- Some browsers may not support CSS animations (very old browsers)
- GPU memory issues could prevent animation rendering
- Provides consistent behavior across all environments

**Implementation Approach**:
```css
/* Fallback for browsers without animation support */
body {
  background: var(--color-bg-secondary); /* standard background */
}

/* Enhanced experience for modern browsers */
@supports (animation: rainbow-flow 20s linear infinite) {
  body.rainbow-background-active {
    background: linear-gradient(/* rainbow */);
    background-size: 200% 200%;
    animation: rainbow-flow 20s linear infinite;
  }
}
```

**Alternatives Considered**:
- Show error message: Rejected as too intrusive for cosmetic feature
- Fall back to static rainbow: Possible enhancement, not in MVP
- Require animation support: Rejected due to accessibility concerns

## Architecture Summary

### Component Changes

1. **CSS changes (frontend/src/index.css)**:
   - Add `@keyframes rainbow-flow` animation definition
   - Add `.rainbow-background-active` body class styles
   - Add reduced motion media query overrides
   - Add contrast overlay pseudo-element

2. **New hook (frontend/src/hooks/useRainbowBackground.ts)**:
   - Manages rainbow background enabled/disabled state
   - Persists preference to localStorage
   - Toggles body class for CSS activation

3. **Settings component modifications**:
   - Add rainbow background toggle switch
   - Wire up to useRainbowBackground hook
   - Place near theme toggle

4. **App initialization (frontend/src/main.tsx or App.tsx)**:
   - Initialize rainbow background state on mount
   - Apply saved preference from localStorage

### Risk Assessment

**Low Risk**:
- Pure CSS implementation minimizes JavaScript complexity
- No backend changes required
- Isolated feature with clear toggle for disabling
- Follows existing patterns (localStorage, theme system)

**Medium Risk**:
- Contrast maintenance across all screens requires validation
- Performance on very old devices may require optimization
- Interaction with future theme changes needs consideration

**High Risk**: None identified

## Success Metrics

1. **Accessibility**: All text elements maintain ≥4.5:1 contrast ratio with rainbow background
2. **Performance**: Animation maintains ≥30fps on devices from 2020+
3. **Compatibility**: Works in Chrome, Firefox, Safari, Edge (latest 2 versions)
4. **User Experience**: Toggle takes effect in <0.5 seconds
5. **Persistence**: Preference persists across 100% of sessions

## References

- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- CSS Animations Performance: https://web.dev/animations-guide/
- prefers-reduced-motion: https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion
- React localStorage patterns: https://react.dev/reference/react/hooks

## Next Steps

Proceed to Phase 1: Design artifacts generation
- data-model.md: Define background state entities and CSS variable changes
- contracts/: Define component contracts and CSS changes
- quickstart.md: Step-by-step implementation guide
