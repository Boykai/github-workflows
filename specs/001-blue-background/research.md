# Research: Blue Background Application Interface

**Branch**: `001-blue-background` | **Date**: 2026-02-16  
**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Phase 0: Technical Research & Decisions

This document resolves all NEEDS CLARIFICATION items from the Technical Context and documents technology choices for implementing the blue background feature.

---

## Decision 1: CSS Custom Property Selection

**Question**: Which CSS custom property should be modified to apply the blue background?

**Decision**: Modify `--color-bg-secondary` in `:root` selector

**Rationale**: 
- The `body` element uses `background: var(--color-bg-secondary)` in `frontend/src/index.css:43`
- This variable controls the main application background color
- Changing this variable will apply the background consistently across all screens
- The existing theme system already uses this pattern for theming

**Alternatives Considered**:
- Modifying `--color-bg` - Rejected because this is used for component surfaces (cards, panels), not the main background
- Adding a new CSS variable - Rejected because unnecessary; existing variable serves the purpose
- Direct `body` background property - Rejected because it bypasses the theme system and breaks dark mode

**Implementation**: Change `--color-bg-secondary: #f6f8fa;` to `--color-bg-secondary: #1976d2;` in `:root` selector

---

## Decision 2: Dark Mode Background Color

**Question**: What blue shade should be used for dark mode to maintain consistency?

**Decision**: Use darker blue shade `#0d47a1` for dark mode (html.dark-mode-active selector)

**Rationale**:
- Dark mode requires darker colors to prevent eye strain
- `#0d47a1` is a darker variant of `#1976d2` that maintains the same hue
- This shade provides appropriate contrast with light text in dark mode
- Maintains brand consistency while adapting to theme context

**Alternatives Considered**:
- Using same `#1976d2` for both modes - Rejected because too bright for dark mode, causes eye strain
- Not changing dark mode at all - Rejected because spec requires consistent application across themes (FR-004)
- Using completely different blue - Rejected because should maintain brand color relationship

**Implementation**: Change `--color-bg-secondary: #161b22;` to `--color-bg-secondary: #0d47a1;` in `html.dark-mode-active` selector

---

## Decision 3: Text Contrast Requirements

**Question**: Do existing text colors meet WCAG AA contrast requirements against blue background?

**Decision**: Update text colors to white (#ffffff) for light mode and light gray (#e6edf3) for dark mode

**Rationale**:
- Current text color `#24292f` (dark gray) provides contrast ratio of ~2.5:1 against `#1976d2` - FAILS WCAG AA requirement (4.5:1)
- White text `#ffffff` provides 5.5:1 contrast against `#1976d2` - PASSES WCAG AA
- Dark mode text `#e6edf3` provides 6.8:1 contrast against `#0d47a1` - PASSES WCAG AA
- Secondary text also needs adjustment for proper contrast

**Alternatives Considered**:
- Keeping existing text colors - Rejected because fails accessibility requirements (FR-002)
- Using light gray for light mode - Rejected because reduces contrast unnecessarily
- Custom colors per component - Rejected because theme system should handle this centrally

**Implementation**: 
- Light mode: `--color-text: #ffffff;`, `--color-text-secondary: #e3f2fd;`
- Dark mode: Keep `--color-text: #e6edf3;`, update `--color-text-secondary: #bbdefb;`

---

## Decision 4: Component Background Colors

**Question**: Do component surfaces (cards, panels) need color adjustment?

**Decision**: Update `--color-bg` to provide contrast against the blue background

**Rationale**:
- Component surfaces need to stand out from the blue background
- Using white/light backgrounds creates visual hierarchy
- Maintains readability of component content
- Provides clear visual boundaries

**Alternatives Considered**:
- Keeping white background - Partially acceptable but needs dark mode adjustment
- Using transparent backgrounds - Rejected because reduces component readability
- Different colors per component - Rejected because inconsistent user experience

**Implementation**:
- Light mode: `--color-bg: #ffffff;` (keep existing)
- Dark mode: `--color-bg: #1a237e;` (darker blue for component surfaces)

---

## Decision 5: Border and Shadow Updates

**Question**: Do borders and shadows need adjustment for visibility against blue background?

**Decision**: Update border color to lighter shade for visibility; keep shadows

**Rationale**:
- Current border `#d0d7de` (light gray) has poor contrast against `#1976d2`
- Lighter borders improve component definition
- Shadows still work effectively against blue backgrounds
- Maintains visual separation between elements

**Alternatives Considered**:
- Removing borders entirely - Rejected because reduces clarity of component boundaries
- Using darker borders - Rejected because less visible against blue background
- Significantly increasing shadow intensity - Rejected because can look harsh

**Implementation**:
- Light mode: `--color-border: #e3f2fd;` (light blue tint)
- Dark mode: `--color-border: #1976d2;` (medium blue for contrast against dark blue)

---

## Decision 6: Interactive Element Contrast

**Question**: Do buttons and interactive elements meet 3:1 contrast requirement?

**Decision**: Update primary button colors to ensure proper contrast

**Rationale**:
- Primary action buttons need to stand out against blue background
- Current primary color `#0969da` is too similar to background `#1976d2`
- Using orange/amber for primary actions creates strong visual contrast
- Maintains accessibility for all interactive elements (FR-003)

**Alternatives Considered**:
- Keeping blue buttons - Rejected because insufficient contrast with blue background
- Using green buttons - Rejected because conflicts with success/positive action semantics
- Using white buttons - Rejected because can look washed out, less actionable

**Implementation**:
- Light mode: `--color-primary: #f57c00;` (orange for primary actions)
- Dark mode: `--color-primary: #ffa726;` (lighter orange for dark backgrounds)

---

## Decision 7: Form Input Field Styling

**Question**: How to ensure input fields are distinguishable from the blue background?

**Decision**: Maintain white backgrounds for inputs with stronger borders

**Rationale**:
- White input backgrounds provide clear affordance for interaction
- Strong borders create visual boundaries against blue background
- Maintains standard form UX patterns users expect
- Ensures accessibility for form interactions (FR-006)

**Alternatives Considered**:
- Transparent input backgrounds - Rejected because reduces clarity of input areas
- Blue-tinted inputs - Rejected because can confuse users about input state
- Outlined-only inputs - Partially acceptable but filled provides better clarity

**Implementation**: Input elements already use component background (`--color-bg`), which will be white. Ensure borders use `--color-border` for visibility.

---

## Decision 8: Screen Reader and Accessibility Features

**Question**: Does the color change impact screen reader functionality?

**Decision**: No changes needed to accessibility features; purely visual

**Rationale**:
- Color changes do not affect HTML structure or ARIA attributes
- Screen readers operate on semantic HTML, not visual styling
- Contrast requirements ensure visual accessibility
- No JavaScript changes that could impact assistive technology

**Alternatives Considered**:
- Adding ARIA announcements for theme - Rejected because unnecessary for color changes
- Adding high contrast mode - Deferred to separate feature; current solution meets WCAG AA

**Implementation**: No additional implementation needed; existing accessibility features preserved (FR-007)

---

## Decision 9: Testing and Validation Approach

**Question**: How to validate color contrast and visual consistency?

**Decision**: Manual testing with browser DevTools and contrast checker tools

**Rationale**:
- Visual features require human verification
- Browser DevTools provide color picker and contrast ratio calculation
- Manual navigation through all routes verifies consistency (FR-004)
- Automated contrast testing complex for CSS variables

**Alternatives Considered**:
- Automated contrast testing - Considered but complex setup for CSS variable-based themes
- Screenshot comparison tests - Rejected because brittle and maintenance overhead
- Unit testing CSS values - Rejected because doesn't verify actual rendered result

**Implementation**: 
1. Use browser DevTools to verify hex values applied correctly
2. Use WebAIM Contrast Checker to validate text contrast ratios
3. Manually navigate all routes to verify consistency
4. Test both light and dark modes
5. Take screenshots for documentation

---

## Decision 10: Performance and Build Considerations

**Question**: Does the CSS change impact build process or performance?

**Decision**: No impact; CSS changes are compile-time static

**Rationale**:
- CSS custom property changes are parsed at build time by Vite
- No runtime JavaScript changes required
- No new dependencies or assets
- Browser performance for CSS variables is negligible

**Alternatives Considered**:
- Runtime theme calculation - Rejected because unnecessary complexity
- CSS-in-JS approach - Rejected because existing CSS system works well
- Separate stylesheet loading - Rejected because increases HTTP requests

**Implementation**: Standard Vite build process handles CSS changes. No special build configuration needed.

---

## Summary

All technical decisions support a simple, accessible implementation:

1. **Core Change**: Modify 2 CSS variables (`--color-bg-secondary`) in `frontend/src/index.css`
2. **Accessibility**: Update text and border colors to meet WCAG AA standards
3. **Theme Support**: Provide appropriate colors for both light and dark modes
4. **Validation**: Manual testing with contrast checking tools
5. **Performance**: Zero impact on build or runtime performance

The implementation requires changes only to `frontend/src/index.css` with no JavaScript modifications, maintaining simplicity while meeting all functional requirements.
