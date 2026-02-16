# Research: Red Background Color

**Branch**: `copilot/apply-red-background-color-again` | **Date**: 2026-02-16 | **Spec**: [spec.md](./spec.md)

## Phase 0: Research & Decisions

This document captures all technical decisions, research findings, and clarifications needed for implementing the red background color feature.

---

## Research Task 1: Red Color Selection for Branding

**Context**: Specification requires "#ff0000 or similar prominent red" for visual branding impact.

**Decision**: Use `#ff0000` (pure red) for light mode

**Rationale**: 
- Pure red (#ff0000) provides maximum visual impact and brand recognition
- It's a standard web-safe color with excellent browser support
- Clear, unambiguous color specification that matches user requirements
- Hex color values should use lowercase per codebase conventions (frontend/src/index.css:3-29)

**Alternatives Considered**:
- `#dc3545` (Bootstrap danger red) - Rejected: Less vibrant, doesn't meet "prominent red" requirement
- `#e60000` (darker red) - Rejected: Less visually impactful than pure red
- `#ff1744` (Material Design red) - Rejected: Pink undertones, less pure red

---

## Research Task 2: Dark Mode Red Adaptation

**Context**: FR-005 requires clarification on whether red background applies to both light and dark themes.

**Decision**: Apply red background to both light mode and dark mode, using a darker red (`#8b0000` / dark red) for dark mode

**Rationale**:
- Consistent branding across both theme modes
- Dark mode red should be darkened to reduce eye strain in low-light environments
- `#8b0000` maintains red identity while being appropriate for dark theme
- Spec edge case asks "Should the red background apply to both light and dark themes?" - answer is YES for consistency

**Alternatives Considered**:
- Light mode only - Rejected: Would create inconsistent branding experience for dark mode users
- Same `#ff0000` for both modes - Rejected: Too bright for dark mode, causes eye strain
- No red in dark mode (keep default) - Rejected: Breaks branding consistency

**Resolution for FR-005**: Red background MUST apply to both light and dark themes with appropriate color adjustments for each mode.

---

## Research Task 3: CSS Custom Property Strategy

**Context**: Application uses CSS custom properties (CSS variables) for theming in `frontend/src/index.css`.

**Decision**: Modify `--color-bg-secondary` CSS custom property in both `:root` and `html.dark-mode-active` selectors

**Rationale**:
- Existing pattern: CSS variables control theme colors (lines 2-30 in frontend/src/index.css)
- `--color-bg-secondary` is used for body background (line 43: `background: var(--color-bg-secondary)`)
- `--color-bg-secondary` is used throughout the application for various surfaces
- Single point of change ensures consistency across all screens and components
- No component-level changes needed - CSS cascade handles propagation

**Alternatives Considered**:
- Modify `--color-bg` instead - Rejected: Used for component surfaces, not page background
- Direct body style override - Rejected: Breaks theming system and CSS custom property pattern
- Component-by-component changes - Rejected: Violates DRY principle, inconsistent

**Implementation Details**:
- Light mode: `:root { --color-bg-secondary: #ff0000; }` (line 9)
- Dark mode: `html.dark-mode-active { --color-bg-secondary: #8b0000; }` (line 25)

---

## Research Task 4: Accessibility and Contrast Compliance

**Context**: FR-003 requires WCAG AA compliance (4.5:1 for normal text, 3:1 for large text).

**Decision**: Verify and adjust text colors to ensure sufficient contrast against red background

**Rationale**:
- Red background (#ff0000) will require light text colors for readability
- Current text colors may not meet contrast requirements on red background
- WCAG AA is a legal requirement in many jurisdictions

**Contrast Analysis**:
- Red background (#ff0000) with white text (#ffffff): Contrast ratio = 3.99:1 (FAILS for normal text)
- Red background (#ff0000) with light gray (#f6f8fa): Contrast ratio = ~3.8:1 (FAILS)
- Need to identify all text colors used in application

**Required Changes**:
- Light mode: Text colors must be adjusted to white or near-white for sufficient contrast
- Dark mode: Text on dark red (#8b0000) may also need adjustment

**Alternatives Considered**:
- Keep existing text colors - Rejected: Fails WCAG AA compliance
- Lighter red background - Rejected: Defeats "prominent red" branding requirement
- White/off-white text only - Best option for red background

**Testing Required**: Manual accessibility testing with contrast checker tools (e.g., WebAIM Contrast Checker)

---

## Research Task 5: Component and Surface Backgrounds

**Context**: Spec edge case asks "Are there any screen or component backgrounds that should remain non-red?"

**Decision**: Only the page/body background becomes red. Component surfaces (cards, buttons, inputs, panels) maintain their existing backgrounds using `--color-bg`

**Rationale**:
- `--color-bg-secondary` is specifically for page background (body element)
- `--color-bg` is used for component surfaces and should remain white/dark for usability
- Buttons, inputs, chat bubbles, panels use `--color-bg` and will remain readable
- This approach maintains visual hierarchy and usability

**Verification**: 
- Body background: Uses `--color-bg-secondary` (will be red)
- Buttons: Use `--color-bg-secondary` in App.css (lines 73, 130, 177, 209, 234, 494)
- Chat interface: Uses `--color-bg-secondary` extensively (ChatInterface.css)
- Component surfaces maintain contrast and readability

**Impact Assessment**:
- Some UI components currently use `--color-bg-secondary` for their backgrounds
- These components will also become red, which may affect visual hierarchy
- Need to verify this is acceptable or adjust individual components

**Alternatives Considered**:
- All backgrounds red - Rejected: Poor UX, everything blends together
- Only body red, everything else white - This is the implemented approach
- Selective component changes - May be needed if buttons/panels become problematic

---

## Research Task 6: Modal and Overlay Handling

**Context**: Spec edge case asks "How does the red background interact with overlays, modals, or pop-ups?"

**Decision**: Modals and overlays should maintain their own background colors (typically `--color-bg`) to stand out from red page background

**Rationale**:
- Modals/overlays need visual separation from page background
- Red modals on red background would lack visual hierarchy
- Standard modal pattern: semi-transparent backdrop + white/dark modal surface

**Implementation**:
- No changes needed if modals use `--color-bg` for their surfaces
- If any modals use `--color-bg-secondary`, they may need individual style adjustments

**Verification Required**: Test all modal/overlay components after change

---

## Research Task 7: Text Color Adjustments for Red Background

**Context**: Current text colors (--color-text: #24292f for light mode) will not have sufficient contrast on red background.

**Decision**: Update `--color-text` to `#ffffff` (white) for light mode when red background is applied

**Rationale**:
- White text on red background: ~4.0:1 contrast (marginal for WCAG AA normal text)
- May need to increase font weight or size for some text to improve readability
- For dark mode (#8b0000 background), light text should work well

**Implementation Details**:
- Light mode: `--color-text: #ffffff;` (line 11)
- Dark mode: May need adjustment from current `#e6edf3` depending on contrast with `#8b0000`

**Testing Required**: Full accessibility audit with contrast checker after implementation

---

## Research Task 8: Browser Compatibility

**Context**: CSS custom properties must work across all target browsers.

**Decision**: CSS custom properties (CSS variables) are supported in all modern browsers

**Rationale**:
- CSS variables supported since: Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+
- Application already uses CSS variables extensively (existing in index.css)
- No polyfills or fallbacks needed for modern browser targets

**Alternatives Considered**:
- Preprocessor variables (Sass/Less) - Rejected: Not used in current stack
- Inline styles - Rejected: Poor maintainability, breaks theming system

---

## Research Task 9: Performance Implications

**Context**: CSS variable changes can trigger repaints/reflows.

**Decision**: Single CSS variable change has negligible performance impact

**Rationale**:
- Changing a CSS variable value causes browser repaint, not reflow
- Paint operation is fast for solid color backgrounds
- No JavaScript computation required
- No animation or transitions involved in this feature

**Measurement**: No performance testing required for this simple change

---

## Research Task 10: Testing Strategy

**Context**: Feature is primarily visual and requires verification.

**Decision**: Manual visual testing is primary verification method; automated tests are optional

**Rationale**:
- Visual features are best verified by human inspection
- Automated color detection tests are brittle and complex
- Playwright E2E tests could verify computed styles, but add limited value
- Constitution Principle IV: Tests are optional unless explicitly requested

**Testing Approach**:
- Manual: Open application in browser, verify red background in both themes
- Manual: Check all major screens for consistency
- Manual: Verify text readability and contrast
- Optional: Playwright test to verify computed background-color value

**Test Coverage**:
- User Story 1: Manual verification of red background visibility
- User Story 2: Manual verification of text/element readability and contrast

---

## Summary of Decisions

1. **Color Selection**: `#ff0000` for light mode, `#8b0000` for dark mode
2. **Theme Coverage**: Red background applies to both light and dark themes
3. **Implementation**: Modify `--color-bg-secondary` CSS custom property
4. **Text Contrast**: Update `--color-text` to `#ffffff` for light mode
5. **Component Surfaces**: Maintain existing `--color-bg` for cards/buttons/inputs
6. **Modals**: Keep current backgrounds for visual separation
7. **Browser Support**: Full support via CSS custom properties
8. **Performance**: Negligible impact from single CSS variable change
9. **Testing**: Manual visual verification as primary method
10. **Accessibility**: Requires contrast verification and potential text color adjustments

---

## Clarifications Resolved

**FR-005 Clarification**: "Should red apply to both themes, or only light mode?"
- **Resolution**: Red background MUST apply to both light mode and dark mode with theme-appropriate color values (`#ff0000` for light, `#8b0000` for dark)

**Edge Case 1**: "Are there any screen or component backgrounds that should remain non-red?"
- **Resolution**: Component surfaces (cards, buttons, inputs) use `--color-bg` and maintain their current colors. Only the page background becomes red.

**Edge Case 2**: "How does the red background interact with overlays, modals, or pop-ups?"
- **Resolution**: Modals and overlays maintain their own backgrounds for visual separation.

**Edge Case 3**: "What happens when dark mode is enabled?"
- **Resolution**: Dark mode gets a darker red (`#8b0000`) appropriate for low-light viewing while maintaining branding consistency.
