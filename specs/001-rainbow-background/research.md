# Research: Rainbow Background Option

**Feature**: Rainbow Background Option  
**Branch**: `001-rainbow-background`  
**Date**: 2026-02-13

## Overview

This document captures technical decisions for implementing a rainbow background option in the Tech Connect 2026 web application. The feature requires adding UI controls, visual rendering, accessibility considerations, and user preference persistence.

## Technology Stack Analysis

### Current Application Architecture

- **Frontend**: React 18.3 with TypeScript 5.4
- **Build Tool**: Vite 5.4
- **State Management**: TanStack Query 5.17 for server state, React hooks for local state
- **Styling**: CSS custom properties (CSS variables) for theming
- **Storage**: localStorage for client-side preference persistence
- **Existing Theme System**: useAppTheme hook managing dark/light mode

### Existing Theme Infrastructure

The application already has a robust theming system:
- CSS custom properties defined in `frontend/src/index.css`
- Theme hook at `frontend/src/hooks/useAppTheme.ts`
- Theme toggle button in app header
- localStorage persistence with key `tech-connect-theme-mode`
- Dark mode class applied to `document.documentElement`: `dark-mode-active`

## Technical Decisions

### Decision 1: Rainbow Background Implementation Method

**Options Considered:**
1. CSS linear-gradient with multiple color stops
2. CSS animated gradient using keyframes
3. Canvas-based rendering with requestAnimationFrame
4. SVG gradient with animation
5. CSS conic-gradient for circular rainbow effect

**Decision**: Use CSS linear-gradient with animation

**Rationale**:
- **Performance**: Pure CSS solution has minimal performance overhead (SC-005: <100ms page load increase)
- **Browser Support**: Linear gradients supported in all modern browsers without polyfills
- **Simplicity**: No JavaScript needed for visual effect, reducing complexity
- **Accessibility**: CSS animations can be disabled via `prefers-reduced-motion` media query
- **Maintainability**: Declarative CSS is easier to maintain than imperative canvas code

**Implementation Approach**:
```css
@keyframes rainbow-slide {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}

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
```

**Alternatives Rejected**:
- Canvas: More complex, requires JavaScript, higher CPU usage
- SVG: Additional HTTP request, complexity in managing DOM updates
- Conic-gradient: Less familiar rainbow pattern, harder to animate smoothly

---

### Decision 2: Accessibility and Readability Strategy

**Options Considered:**
1. Semi-transparent overlay between background and content
2. Reduce background gradient saturation/brightness
3. Apply backdrop-filter: blur() to background
4. Add text-shadow to all text elements
5. Increase content container background opacity

**Decision**: Semi-transparent white/dark overlay + subtle desaturation

**Rationale**:
- **WCAG AA Compliance**: Overlay ensures minimum 4.5:1 contrast ratio for normal text (FR-004, SC-003)
- **Theme Consistency**: Overlay color adapts to dark/light mode using existing CSS variables
- **Non-Intrusive**: Maintains rainbow visibility while ensuring readability
- **Simple Implementation**: Single CSS pseudo-element, no changes to text elements

**Implementation Approach**:
```css
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

body.rainbow-background-active {
  /* Rainbow background on body */
}
```

**Alternatives Rejected**:
- Backdrop-filter: Poor browser support, high performance cost
- Text-shadow: Doesn't guarantee contrast, affects all text uniformly
- Saturation reduction alone: Loses "rainbow" visual appeal

---

### Decision 3: User Preference Storage

**Options Considered:**
1. Extend existing theme localStorage key with rainbow flag
2. Create separate localStorage key for rainbow preference
3. Store in backend user preferences (requires API changes)
4. Use sessionStorage (lost on tab close)

**Decision**: Separate localStorage key `tech-connect-rainbow-background`

**Rationale**:
- **Separation of Concerns**: Rainbow background is independent of dark/light theme
- **User Flexibility**: Users can combine rainbow with either theme mode
- **Consistency**: Follows existing pattern (see `tech-connect-theme-mode`, `tech-connect-weather-cache`)
- **No API Changes**: Client-only implementation (FR-007, FR-008)
- **Graceful Degradation**: Defaults to disabled if localStorage unavailable (FR-009)

**Storage Schema**:
```typescript
// Value: 'enabled' | 'disabled'
localStorage.setItem('tech-connect-rainbow-background', 'enabled');
```

**Alternatives Rejected**:
- Combined theme key: Complicates existing theme logic, harder to maintain
- Backend storage: Requires API changes, authentication dependency, out of scope
- sessionStorage: Violates requirement for persistence across sessions (FR-008)

---

### Decision 4: UI Control Placement and Type

**Options Considered:**
1. Add toggle button next to theme toggle in header
2. Create settings modal/panel with multiple appearance options
3. Add dropdown menu with background options
4. Add to sidebar with other controls

**Decision**: Toggle button next to theme toggle in header

**Rationale**:
- **Discoverability**: Visible location, next to similar control (SC-001: findable in 30 seconds)
- **Minimal UI Changes**: Uses existing header-actions pattern
- **Consistency**: Matches theme toggle UX (emoji button, hover effects)
- **Accessibility**: Single-purpose button with clear aria-label
- **No Modal**: Avoids adding complexity of settings panel for single option

**Implementation**:
```tsx
<button 
  className="rainbow-toggle-btn"
  onClick={toggleRainbow}
  aria-label={isRainbowEnabled ? 'Disable rainbow background' : 'Enable rainbow background'}
>
  🌈
</button>
```

**Alternatives Rejected**:
- Settings modal: Over-engineering for single feature, violates simplicity principle
- Sidebar placement: Less discoverable, inconsistent with theme control location
- Dropdown: Unnecessary complexity for boolean toggle

---

### Decision 5: React Hook Architecture

**Options Considered:**
1. Create new `useRainbowBackground` hook
2. Extend existing `useAppTheme` hook with rainbow support
3. Use useState directly in App component
4. Create context provider for appearance settings

**Decision**: Create separate `useRainbowBackground` hook

**Rationale**:
- **Single Responsibility**: Hook manages only rainbow background state
- **Reusability**: Can be imported in any component if needed
- **Consistency**: Follows pattern established by useAppTheme, useAuth, useProjects
- **Testability**: Isolated logic easier to unit test
- **Future Extensibility**: Easy to add more background options without affecting theme

**Hook API**:
```typescript
interface UseRainbowBackgroundReturn {
  isRainbowEnabled: boolean;
  toggleRainbow: () => void;
}

export function useRainbowBackground(): UseRainbowBackgroundReturn {
  // Implementation
}
```

**Alternatives Rejected**:
- Extending useAppTheme: Violates SRP, couples unrelated features
- Direct useState: Not reusable, doesn't follow codebase patterns
- Context provider: Over-engineering, no need for deep component tree access

---

### Decision 6: Reduced Motion Accessibility

**Options Considered:**
1. Disable animation when prefers-reduced-motion is active
2. Show static gradient (no animation)
3. Disable feature entirely for reduced-motion users
4. Ignore prefers-reduced-motion

**Decision**: Static gradient when prefers-reduced-motion is active

**Rationale**:
- **Accessibility Compliance**: Respects user's system preference (Edge Case: accessibility settings)
- **Inclusive Design**: Users still get rainbow option without motion
- **Standard Practice**: Follows WCAG WCAG 2.1 Success Criterion 2.3.3
- **Simple Implementation**: CSS media query only

**Implementation**:
```css
@media (prefers-reduced-motion: reduce) {
  .rainbow-background-active {
    animation: none;
  }
}
```

**Alternatives Rejected**:
- Disable feature: Removes customization option unnecessarily
- Ignore preference: Violates accessibility standards, may cause discomfort

---

### Decision 7: Testing Strategy

**Current Testing Infrastructure**:
- Frontend unit tests: Vitest
- Frontend E2E tests: Playwright
- No existing visual regression tests

**Decision**: Unit tests for hook + E2E test for user flow

**Test Coverage**:
1. **Unit Tests (useRainbowBackground)**:
   - Initial state loads from localStorage
   - Toggle updates state and localStorage
   - Graceful handling of unavailable localStorage

2. **E2E Tests (Playwright)**:
   - Locate and click rainbow toggle button
   - Verify class applied to body/html element
   - Verify preference persists after page reload
   - Verify button aria-label changes

**No Visual Regression Tests**:
- Not part of existing test infrastructure
- Manual QA sufficient for visual appearance
- Automated contrast checking out of scope

**Alternatives Rejected**:
- Visual regression: No existing tooling, high setup overhead
- Integration tests: Overkill for simple preference storage

---

## Performance Considerations

### CSS Animation Performance

**Monitoring Points**:
- CSS animations use GPU acceleration (transform/opacity optimized)
- Background-position animation is slightly less performant but acceptable
- No JavaScript in render loop

**Optimization**:
- Use `will-change: background-position` hint for compositor
- Limit animation to body element (not per-component)
- 15-second animation duration (smooth, not distracting)

**Performance Budget** (SC-005):
- Target: <100ms page load time increase
- Expected: ~10-20ms (CSS parsing only)
- Mitigation: None needed, well under budget

---

## Browser Compatibility

**Target Browsers** (from assumptions):
- Chrome 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅
- Edge 90+ ✅

**Required Features**:
- CSS linear-gradient: Supported all targets
- CSS animations: Supported all targets
- CSS custom properties: Supported all targets
- localStorage: Supported all targets
- prefers-reduced-motion: Supported all targets

**Graceful Degradation**:
- localStorage unavailable → defaults to disabled (FR-009)
- CSS animations disabled → static gradient
- Older browsers → fallback to solid background (progressive enhancement)

---

## Integration Points

### Modified Components

1. **App.tsx**: Add rainbow toggle button, useRainbowBackground hook
2. **useRainbowBackground.ts** (new): Hook implementation
3. **index.css**: Rainbow background styles + animations
4. **App.css**: Rainbow toggle button styles

### No Backend Changes Required

- Feature is entirely frontend-only
- No API endpoints needed
- No database schema changes
- No authentication/authorization changes

---

## Open Questions Resolved

### Q: How does rainbow background interact with existing theme (light/dark)?
**A**: Rainbow background applies independently. Overlay uses CSS variables that adapt to current theme, ensuring readability in both modes.

### Q: What if localStorage is disabled/unavailable?
**A**: Feature defaults to disabled. Toggle button still works for current session, just won't persist (FR-009).

### Q: Performance on low-end devices?
**A**: CSS animations are GPU-accelerated and very lightweight. Testing on low-end devices recommended, but expected to be well under 100ms budget.

### Q: Mobile responsiveness?
**A**: Rainbow background scales naturally (percentage-based). Toggle button in header works on mobile (existing header is responsive).

### Q: Should rainbow background apply to modals/overlays?
**A**: No. Background only on body element. Modals have their own backgrounds defined by `var(--color-bg)`, ensuring readability.

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Contrast too low | Medium | High | Overlay with 0.85 opacity ensures contrast |
| Animation causes motion sickness | Low | Medium | prefers-reduced-motion disables animation |
| Performance regression | Low | Medium | CSS-only, GPU accelerated, <100ms budget |
| localStorage quota exceeded | Very Low | Low | Rainbow pref is 1 small string (~10 bytes) |
| Browser incompatibility | Very Low | Low | Progressive enhancement, feature detection |

---

## Implementation Phases

Based on user story priorities:

**Phase 1 (P1)**: Enable Rainbow Background (US1)
- Create useRainbowBackground hook
- Add rainbow background CSS
- Add toggle button in header
- Apply class to body when enabled

**Phase 2 (P1)**: Maintain Content Readability (US2)
- Add overlay for contrast
- Test WCAG AA compliance
- Add prefers-reduced-motion support

**Phase 3 (P2)**: Persist User Preference (US3)
- Add localStorage read/write
- Test reload persistence
- Handle unavailable storage

**Phase 4**: Testing & Polish
- Unit tests for hook
- E2E tests for user flow
- Cross-browser testing
- Accessibility audit

---

## Success Metrics Alignment

| Success Criterion | Implementation Support |
|------------------|------------------------|
| SC-001: Find setting in 30s | Toggle button in visible header location |
| SC-002: Applied in <1s | React state update + CSS class, ~10-50ms |
| SC-003: WCAG AA contrast | Overlay ensures 4.5:1 minimum ratio |
| SC-004: 100% persistence | localStorage write on every toggle |
| SC-005: <100ms page load | CSS-only, expected ~10-20ms |
| SC-006: 90% pleasant | Smooth animation, proper colors, tested |
| SC-007: Zero complaints | Readability overlay, reduced-motion support |

---

## Dependencies

**External Dependencies**: None (uses existing React, CSS features)

**Internal Dependencies**:
- Existing theming infrastructure (CSS custom properties)
- Existing localStorage usage patterns
- Existing header layout and styling

**Development Dependencies**: None (no new packages needed)

---

## Conclusion

The rainbow background feature can be implemented as a lightweight, frontend-only enhancement using existing application infrastructure. The technical approach prioritizes:

1. **Simplicity**: Pure CSS solution, no external dependencies
2. **Accessibility**: WCAG AA compliance, reduced-motion support
3. **Performance**: GPU-accelerated CSS, minimal overhead
4. **Maintainability**: Follows existing patterns (hooks, localStorage)
5. **User Experience**: Independent of theme, persistent preference

All technical unknowns have been resolved. Implementation can proceed to Phase 1 (Design & Contracts).
