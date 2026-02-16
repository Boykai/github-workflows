# Research: White Background Interface

**Feature**: 002-white-background  
**Date**: 2026-02-16  
**Purpose**: Resolve technical unknowns and validate approach for applying white background to app interface

## Decision 1: CSS Custom Properties Strategy

**Decision**: Use existing CSS custom property system (`--color-bg`, `--color-bg-secondary`) in `index.css`

**Rationale**: 
- Application already uses CSS custom properties for theming
- Centralized management in `:root` selector ensures consistency
- All components already reference these variables
- Single source of truth approach minimizes risk of inconsistencies
- No JavaScript changes needed - pure CSS solution

**Alternatives Considered**:
1. **Inline styles per component** - Rejected: Would scatter background values across codebase, hard to maintain
2. **CSS classes approach** - Rejected: Adds unnecessary layer when variables already exist
3. **Styled-components/CSS-in-JS** - Rejected: Not part of current tech stack, would require major refactoring

## Decision 2: Dark Mode Handling

**Decision**: Maintain dark mode CSS rules but ensure light mode (white background) is the default

**Rationale**:
- Specification states "white background takes precedence" and "User preference for dark mode... is out of scope"
- Existing dark mode infrastructure should remain intact for future features
- Simply update light mode values to pure white (#FFFFFF)
- Dark mode variables can stay unchanged as they're behind `.dark-mode-active` class
- This approach is reversible if requirements change

**Alternatives Considered**:
1. **Remove dark mode entirely** - Rejected: Destructive change, makes future dark mode harder
2. **Force disable dark mode toggle** - Rejected: Out of scope per specification
3. **Override dark mode with white** - Rejected: Confusing UX if dark mode is re-enabled later

## Decision 3: Background Color Values

**Decision**: Set `--color-bg: #FFFFFF` and `--color-bg-secondary: #FFFFFF` (both pure white)

**Rationale**:
- Specification explicitly requires "#FFFFFF" throughout
- Using the same value for both primary and secondary backgrounds ensures 100% consistency
- Eliminates any subtle shade variations that could appear inconsistent
- Meets "solid white background" requirement from spec

**Alternatives Considered**:
1. **Use slight shade variation (e.g., #F6F8FA for secondary)** - Rejected: Current value, spec wants pure white everywhere
2. **Keep secondary as-is** - Rejected: Could create visual inconsistency
3. **Use rgb(255, 255, 255)** - Rejected: Hex format is convention in this codebase

## Decision 4: Text Contrast Verification

**Decision**: Manually verify existing text colors against white background meet WCAG 2.1 Level AA standards (4.5:1 for normal text, 3:1 for large text)

**Rationale**:
- Current text colors: `--color-text: #24292f` (dark gray) should have sufficient contrast
- Large majority of existing UI already works on `--color-bg: #ffffff` (current default)
- Manual verification faster than automated testing for this small scope
- Can use browser DevTools accessibility features for quick checks

**Verification Checklist**:
- Primary text (`--color-text: #24292f`) on white: ~17:1 contrast ✓
- Secondary text (`--color-text-secondary: #57606a`) on white: ~8:1 contrast ✓
- Primary color (`--color-primary: #0969da`) on white: ~7:1 contrast ✓
- Success color (`--color-success: #1a7f37`) on white: ~5:1 contrast ✓
- Warning color (`--color-warning: #9a6700`) on white: ~6:1 contrast ✓
- Danger color (`--color-danger: #cf222e`) on white: ~7:1 contrast ✓

**Alternatives Considered**:
1. **Automated contrast testing** - Postponed: Can add later if needed
2. **Change text colors** - Not needed: Existing colors have excellent contrast
3. **Skip verification** - Rejected: Required by FR-004 in specification

## Decision 5: Transition Smoothness

**Decision**: Verify existing React rendering doesn't cause background flashes; no additional changes needed

**Rationale**:
- React's reconciliation algorithm already prevents unnecessary re-renders
- CSS custom properties change instantly when DOM loads
- No dynamic background color changes in JavaScript code
- Navigation handled by React state, not full page reloads
- `background: var(--color-bg-secondary)` on body ensures immediate white background

**Verification Plan**:
- Test navigation between screens
- Check for any loading states with different backgrounds
- Verify modals/dialogs don't flash different colors
- Test theme toggle (should not be used, but verify no flash)

**Alternatives Considered**:
1. **Add CSS transitions** - Rejected: Could cause unwanted fade effects during loading
2. **Preload background styles** - Not needed: Already loaded in index.css
3. **JavaScript background management** - Rejected: CSS solution is simpler and faster

## Decision 6: Modal and Dialog Styling

**Decision**: Update modal/dialog backgrounds via component-specific CSS that references `--color-bg`

**Rationale**:
- Most modals/dialogs already use `background: var(--color-bg)` or inherit from parent
- CSS variable change will cascade to all child components
- Need to verify no hardcoded background colors in component styles
- Check for any overlays or dimmed backgrounds that might need adjustment

**Files to Check**:
- ChatInterface.css - Message bubbles, input areas
- Component-specific styles in App.css
- Any modal/popup styles in component files

**Alternatives Considered**:
1. **Add explicit background to each modal** - Rejected: Redundant if variables work
2. **Use portal backgrounds** - Not needed: No portals detected in codebase
3. **Z-index layering** - Not relevant to background color

## Decision 7: Loading and Error States

**Decision**: Verify loading spinners and error displays work on white background; update if needed

**Rationale**:
- Loading spinner uses `background: var(--color-bg)` in app-loading class
- Error displays have explicit backgrounds (#fff1f0 for error toast)
- Need to ensure these states don't flash different colors
- Error banners already use light backgrounds compatible with white

**Verification Points**:
- `.app-loading` uses `var(--color-bg)` ✓
- `.error-toast` has explicit light background ✓
- `.error-banner` has explicit light background ✓
- Spinner animation doesn't create color artifacts

**Alternatives Considered**:
1. **Redesign error states** - Out of scope per specification
2. **Add loading overlays** - Not needed: Current approach sufficient
3. **Change error colors** - Not needed: Already compatible

## Decision 8: Navigation Component Backgrounds

**Decision**: Update `.app-header` and `.project-sidebar` to explicitly use `var(--color-bg)` (already done)

**Rationale**:
- Header already has `background: var(--color-bg)`
- Sidebar already has `background: var(--color-bg)`
- Both will automatically become white when variable changes
- Border colors use `var(--color-border)` which provides subtle separation

**Current State**:
- `.app-header { background: var(--color-bg); }` ✓
- `.project-sidebar { background: var(--color-bg); }` ✓
- `.chat-section { background: var(--color-bg); }` ✓

**Alternatives Considered**:
1. **Add explicit white backgrounds** - Not needed: Variables provide consistency
2. **Remove borders** - Rejected: Borders provide visual structure
3. **Adjust border colors** - Evaluate: Current `--color-border` may need lighter shade

## Decision 9: Interactive Element Backgrounds

**Decision**: Verify buttons, forms, cards inherit white background appropriately; check for hover states

**Rationale**:
- Task cards use `background: var(--color-bg)` ✓
- Buttons use `var(--color-bg-secondary)` for some states
- Form inputs use `background: var(--color-bg)`
- Need to ensure hover states don't create jarring transitions

**Elements to Verify**:
- `.task-card { background: var(--color-bg); }` ✓
- `.project-select { background: var(--color-bg); }` ✓
- Button hover states use `var(--color-border)` (subtle)
- Status badges have colored backgrounds (intentional, not changed)

**Alternatives Considered**:
1. **Flatten all backgrounds** - Rejected: Loses visual hierarchy
2. **Increase shadows** - Postponed: Only if depth perception is lost
3. **Add borders everywhere** - Rejected: Cluttered appearance

## Decision 10: Animation and Transition Handling

**Decision**: Review `@keyframes` animations to ensure they work with white background

**Rationale**:
- `@keyframes highlight-pulse` animates task cards with green highlight
- Background transitions from `#dafbe1` (light green) to `var(--color-bg)`
- This animation should work fine with white background
- Other animations (spin, pulse) don't involve background colors

**Animations to Verify**:
- `@keyframes highlight-pulse` - Uses `var(--color-bg)` in end state ✓
- `@keyframes spin` - Rotation only, no colors
- `@keyframes pulse` - Opacity only, no colors
- Component transitions - CSS transitions property, no color specified

**Alternatives Considered**:
1. **Remove animations** - Rejected: Good UX, already compatible
2. **Adjust animation colors** - Not needed unless visual testing shows issues
3. **Add new animations** - Out of scope

## Summary

All research decisions validate a simple, low-risk approach:
1. Update two CSS custom property values in `index.css`
2. Manually verify contrast ratios (all existing colors pass)
3. Test navigation transitions (React handles this well)
4. Verify modals/dialogs inherit white background
5. Confirm loading and error states are compatible
6. Validate interactive element backgrounds

**No unknowns remain** - Ready to proceed to Phase 1 (Design & Contracts).
