# Research: Black Background Theme

**Feature**: 003-black-background-theme  
**Date**: 2026-02-16  
**Purpose**: Resolve technical unknowns and establish implementation approach

## Decision 1: CSS Custom Properties vs Inline Styles

**Decision**: Use CSS custom properties (CSS variables) for theme implementation

**Rationale**:
- The codebase already uses CSS custom properties extensively (--color-bg, --color-text, etc.)
- Existing dark-mode implementation uses `html.dark-mode-active` class with variable overrides
- Centralized theme management in index.css makes updates straightforward
- Better performance than inline styles (no re-rendering required)
- Easier to maintain and extend for future theme variations

**Alternatives Considered**:
- Inline styles: Rejected due to performance concerns and maintenance complexity
- CSS-in-JS: Rejected as the codebase doesn't use this pattern
- Separate stylesheet: Rejected as it would duplicate variable definitions

**Implementation**: Override existing CSS custom properties with black background values

---

## Decision 2: Black Theme Activation Strategy

**Decision**: Replace existing dark mode with black theme as the default

**Rationale**:
- Spec assumption: "application does not have existing theme selection functionality, so black will be the default theme"
- Current dark mode uses #0d1117 (dark gray), not true black
- Simpler implementation: replace dark mode values rather than adding a third theme option
- The `useAppTheme` hook and theme toggle already exist, we'll adapt them for black theme
- No need for theme persistence logic (out of scope per spec)

**Alternatives Considered**:
- Add black theme as third option: Rejected as out of scope (spec: no theme switcher)
- Keep dark mode and add black mode: Would violate simplicity principle
- Remove theme toggle entirely: Considered but keeping for potential light mode fallback

**Implementation**: Modify CSS variables in index.css to use true black (#000000) for backgrounds

---

## Decision 3: Accessibility Contrast Ratios

**Decision**: Use WCAG 2.1 Level AA standards with white/light gray text on black

**Rationale**:
- Spec requirement: "minimum 4.5:1 for normal text, 3:1 for large text"
- Black (#000000) background provides maximum contrast potential
- White (#ffffff) text provides 21:1 contrast ratio (exceeds WCAG AAA)
- Light gray (#e6edf3) for secondary text provides ~13:1 contrast ratio
- Existing dark mode colors already designed for dark backgrounds

**Alternatives Considered**:
- Pure white only: Would be too harsh, reduced readability for long text
- Custom gray scale: Unnecessary, existing dark mode colors already optimized

**Implementation**:
- Primary text: #e6edf3 (light gray, high contrast)
- Secondary text: #8b949e (medium gray, sufficient contrast)
- Interactive elements: #539bf5 (blue, accessible on black)
- Success/warning/danger: Use existing dark mode colors (already accessible)

---

## Decision 4: Component Background Handling

**Decision**: Use layered background approach with --color-bg and --color-bg-secondary

**Rationale**:
- Existing architecture already uses two-tier background system
- --color-bg for primary surfaces (currently #0d1117 in dark mode)
- --color-bg-secondary for elevated/nested surfaces (currently #161b22)
- This creates subtle depth perception even with black backgrounds
- Maintains existing component structure without refactoring

**Alternatives Considered**:
- Pure black everywhere: Would lose visual hierarchy and depth
- Multiple gray levels: Would violate spec requirement for "solid black"

**Implementation**:
- --color-bg: #000000 (pure black for main surfaces)
- --color-bg-secondary: #0a0a0a (very dark gray for subtle elevation)
- --color-border: #30363d (maintains existing border visibility)

---

## Decision 5: Focus Indicators

**Decision**: Use bright blue (#539bf5) with outline for focus states

**Rationale**:
- Spec requirement: "focus indicators must be clearly visible against black background"
- Current dark mode uses #539bf5 for primary actions (already tested on dark backgrounds)
- Outline provides additional visibility for keyboard navigation
- WCAG 2.1 Success Criterion 2.4.7 requires visible focus indicator

**Alternatives Considered**:
- White outline: Too stark, less accessible for colorblind users
- Yellow outline: Non-standard, inconsistent with existing design

**Implementation**:
- Use existing :focus-visible pseudo-class patterns
- Ensure all interactive elements have visible focus states
- Test keyboard navigation across all components

---

## Decision 6: Modal and Overlay Handling

**Decision**: Use semi-transparent black overlay with solid black modal backgrounds

**Rationale**:
- Modals need to stand out from underlying content
- Semi-transparent overlay (rgba(0, 0, 0, 0.8)) provides context while dimming background
- Solid black modal content area maintains consistency with main theme
- Border or subtle shadow helps distinguish modal edges

**Alternatives Considered**:
- No overlay: Would reduce modal prominence
- White/gray overlay: Would contradict black theme
- Gradient overlay: Unnecessarily complex

**Implementation**:
- Modal backdrop: rgba(0, 0, 0, 0.8)
- Modal content: #000000 with 1px border
- Maintain existing modal structure, update CSS variables only

---

## Decision 7: Loading States and Animations

**Decision**: Keep existing animations, update colors for black background visibility

**Rationale**:
- Spec requirement: "preserve existing functionality"
- Current spinner animation uses --color-border and --color-primary
- These variables will be updated for black theme, spinner inherits changes
- Loading states use existing color system, no structural changes needed

**Alternatives Considered**:
- Redesign animations: Out of scope, violates minimal change principle
- Remove animations: Would degrade user experience

**Implementation**:
- Update color variables only
- Test spinner visibility on black background
- Ensure highlight animations (task-card--highlighted) remain visible

---

## Decision 8: Error and Status Messages

**Decision**: Maintain existing color-coded status system with enhanced contrast

**Rationale**:
- Spec edge case: "color-based status indicators must remain distinguishable on black"
- Current error (#f85149), warning (#d29922), success (#3fb950) colors tested for dark backgrounds
- These colors already meet WCAG AA contrast requirements on dark backgrounds
- Black background provides even better contrast than current dark gray

**Alternatives Considered**:
- Lighten status colors: Unnecessary, current colors already optimal
- Add icons to all statuses: Out of scope, not required for WCAG compliance

**Implementation**:
- Keep existing status color values
- Verify contrast ratios against black background
- Maintain color-coded task status badges

---

## Decision 9: Shadow and Depth Perception

**Decision**: Use subtle shadows with adjusted opacity for black backgrounds

**Rationale**:
- Current --shadow: 0 1px 3px rgba(0, 0, 0, 0.4) designed for dark mode
- Black background requires lighter shadows for visibility
- Shadows help distinguish elevated components (cards, modals)

**Alternatives Considered**:
- No shadows: Would flatten UI, reduce depth perception
- Colored shadows: Non-standard, adds unnecessary complexity
- Border-only approach: Less elegant, more rigid

**Implementation**:
- Update --shadow to use slightly lighter opacity or subtle highlight
- Consider adding subtle glow effect for elevated elements
- Test shadow visibility across all components

---

## Decision 10: Browser Compatibility and High Contrast Mode

**Decision**: Support modern browsers with CSS custom properties, graceful degradation for high contrast mode

**Rationale**:
- Spec edge case: "browser/OS accessibility settings that might conflict"
- CSS custom properties supported in all modern browsers (95%+ coverage)
- High contrast mode (forced-colors: active) should use system colors
- @media (forced-colors: active) query allows detection and override

**Alternatives Considered**:
- Ignore high contrast mode: Would fail accessibility for some users
- Extensive fallbacks for old browsers: Out of scope, project targets modern browsers

**Implementation**:
- Add @media (forced-colors: active) rules to respect system high contrast mode
- Test in Windows high contrast mode and browser reader modes
- Ensure color variables gracefully degrade if not supported

---

## Technology Stack Summary

**Frontend Technologies**:
- CSS Custom Properties (CSS Variables) - Primary theming mechanism
- React 18.3.1 - Component framework (no changes needed)
- Vite - Build tool (no changes needed)
- TypeScript - Type safety (no changes needed)

**Styling Approach**:
- Global CSS variables in frontend/src/index.css
- Component-specific styles in frontend/src/App.css and component CSS files
- Existing useAppTheme hook for theme state management

**No New Dependencies Required**: All changes achievable with existing CSS capabilities

---

## Implementation Risk Assessment

**Low Risk**:
- CSS variable updates (existing pattern, well-understood)
- Color contrast (black provides excellent contrast potential)
- Browser compatibility (CSS custom properties widely supported)

**Medium Risk**:
- Shadow visibility (may need iteration to find right balance)
- Component-specific overrides (need to audit all component styles)

**Mitigation**:
- Visual testing across all screens and components
- Automated contrast checking with browser dev tools
- Manual keyboard navigation testing for focus indicators

---

## Open Questions Resolved

1. **Will existing theme toggle work?** Yes, we'll adapt the existing dark mode toggle to control black theme
2. **Do we need new React components?** No, pure CSS changes to existing components
3. **What about user preferences?** Out of scope per spec, black theme is default
4. **Testing strategy?** Visual verification + automated contrast checks + manual keyboard testing
5. **Performance impact?** None, CSS variable updates are highly performant
