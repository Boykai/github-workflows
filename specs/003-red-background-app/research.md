# Research: Apply Red Background Color to App

**Feature**: 003-red-background-app | **Date**: 2026-02-18  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires no significant research as it is a straightforward CSS variable value update. The application already uses a centralized CSS custom properties system in `frontend/src/index.css` with light mode (`:root`) and dark mode (`html.dark-mode-active`) selectors. All technical context is known from existing codebase exploration. This document satisfies the Phase 0 requirement from the plan template.

## Decision Areas

### 1. Red Color Values for Light Mode

**Decision**: Use `#fff5f5` for `--color-bg` (primary surfaces) and `#ffebee` (Material Design Red 50) for `--color-bg-secondary` (page background)

**Rationale**:
- Material Design Red 50 (`#ffebee`) is a design-system-aligned value, not an arbitrary color literal
- `#fff5f5` is a very light red tint that works well for surface backgrounds (cards, headers, modals)
- Both values maintain excellent WCAG AA contrast ratios with existing text color `#24292f`:
  - `#fff5f5` with `#24292f`: 13.70:1 ratio (well above 4.5:1 minimum)
  - `#ffebee` with `#24292f`: 12.82:1 ratio (well above 4.5:1 minimum)
- Light tints provide a visible red theme without overwhelming the interface

**Alternatives Considered**:
- **`#ffcdd2` (Material Red 100)**: Rejected for primary surface — too saturated for card/header backgrounds, could cause visual fatigue. Suitable for page background but `#ffebee` provides better contrast.
- **`#FF0000` (pure red)**: Rejected — far too saturated, would make text unreadable and cause visual discomfort. Contrast ratio with dark text would be very low (~4:1).
- **`#F44336` (Material Red 500)**: Rejected — primary brand red is too bold for a background color. Better suited for accent/action elements.

---

### 2. Red Color Values for Dark Mode

**Decision**: Use `#2d0a0a` for `--color-bg` (primary surfaces) and `#1a0505` for `--color-bg-secondary` (page background)

**Rationale**:
- Dark red values maintain the red theme while preserving the dark mode aesthetic
- Both values maintain excellent WCAG AA contrast ratios with existing dark mode text color `#e6edf3`:
  - `#2d0a0a` with `#e6edf3`: 15.33:1 ratio (well above 4.5:1 minimum)
  - `#1a0505` with `#e6edf3`: 16.64:1 ratio (well above 4.5:1 minimum)
- The page background (`#1a0505`) is darker than the surface background (`#2d0a0a`), maintaining the existing dark mode layering pattern where surfaces appear slightly elevated

**Alternatives Considered**:
- **`#1a0000` (near-black red)**: Rejected — contrast ratio is excellent (17.02:1) but the red tint is barely perceptible in dark mode. `#1a0505` provides a slightly more visible red while still maintaining high contrast.
- **`#4a0000` (medium dark red)**: Rejected — too bright for a dark mode background, would reduce the sense of a true dark theme.
- **`#0d1117` with red overlay**: Rejected — complexity of CSS overlay for no benefit over direct color value.

---

### 3. Implementation Approach

**Decision**: Direct CSS custom property value replacement in `frontend/src/index.css`

**Rationale**:
- The application already uses CSS custom properties for theming (`--color-bg`, `--color-bg-secondary`)
- `body` uses `var(--color-bg-secondary)` for page background (confirmed in `index.css` line 43)
- Components reference `var(--color-bg)` for surface backgrounds (headers, cards, modals via `App.css`)
- Changing only the variable values propagates the red theme globally without touching any component files
- This satisfies FR-002 (centralized theme variable) and FR-006 (no component-level overrides)

**Alternatives Considered**:
- **New CSS variables (e.g., `--color-bg-red`)**: Rejected — adds unnecessary variables. The existing `--color-bg` and `--color-bg-secondary` are the correct tokens to update.
- **Inline styles on `<App />` wrapper**: Rejected — violates centralized theming principle, would require component changes.
- **Tailwind CSS utility classes**: Rejected — project uses vanilla CSS custom properties, not Tailwind.
- **CSS-in-JS approach**: Rejected — project uses plain CSS files, no CSS-in-JS libraries.

---

### 4. Component Background Preservation

**Decision**: No changes to component-level CSS needed

**Rationale**:
- Components like cards, modals, and input fields reference `var(--color-bg)` for their backgrounds
- When `--color-bg` changes to `#fff5f5` (light) or `#2d0a0a` (dark), these components will inherit the red-tinted surface color
- This is the intended behavior: surfaces should have a consistent red tint
- Components with explicitly different backgrounds (e.g., dropdown menus, tooltips) already use their own color values and are not affected
- FR-006 is satisfied: no component-level backgrounds are overridden beyond the intended theme change

**Alternatives Considered**:
- **Add `background-color: white` overrides to specific components**: Rejected — would break the theming system and create maintenance burden. The red tint on surfaces is part of the intended design.
- **Create separate `--color-bg-component` variable**: Rejected — unnecessary abstraction, violates YAGNI principle.

---

### 5. Testing Strategy

**Decision**: Manual visual verification; no new automated tests

**Rationale**:
- Feature is a visual CSS change with no programmatic logic
- Constitution Principle IV (Test Optionality): Tests are optional by default
- Spec acceptance criteria are human-verifiable (open app, observe background color)
- Existing E2E and unit tests should not be affected since no component behavior changes
- A contrast audit can be done by inspecting computed styles in browser DevTools

**Alternatives Considered**:
- **Visual regression tests**: Rejected — project does not have visual regression infrastructure. Setting it up would be disproportionate to the change scope.
- **Automated contrast ratio tests**: Rejected — contrast ratios are pre-calculated and documented. Runtime verification not needed for static CSS values.
- **New unit tests for CSS variables**: Rejected — testing CSS variable values in unit tests adds no value beyond the existing manual verification.

---

### 6. Accessibility Validation

**Decision**: Pre-calculated contrast ratios documented in spec; manual DevTools verification post-implementation

**Rationale**:
- All contrast ratios have been calculated and verified:
  - Light mode `#fff5f5` surface with `#24292f` text: 13.70:1 ✅
  - Light mode `#ffebee` page with `#24292f` text: 12.82:1 ✅
  - Dark mode `#2d0a0a` surface with `#e6edf3` text: 15.33:1 ✅
  - Dark mode `#1a0505` page with `#e6edf3` text: 16.64:1 ✅
- All ratios exceed WCAG AA minimum (4.5:1) by a significant margin
- Secondary text colors also maintain sufficient contrast

**Alternatives Considered**:
- **axe-core automated scan**: Optional post-implementation step but not required for this feature given pre-calculated ratios
- **Lighthouse audit**: Optional post-implementation step; useful for general audit but not a prerequisite

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None — CSS variable value replacements in well-understood file
- **User Impact**: Positive — delivers requested visual change
- **Accessibility Risk**: Very low — all contrast ratios pre-verified and exceed minimums
- **Testing Risk**: Low — manual verification sufficient, existing tests unaffected
- **Rollback Risk**: None — instant git revert available

## Best Practices Applied

1. **YAGNI (You Aren't Gonna Need It)**: No new variables, files, or abstractions
2. **KISS (Keep It Simple)**: Direct value replacement over any abstraction layer
3. **DRY (Don't Repeat Yourself)**: Using existing centralized theme variables — single update point
4. **Design System Alignment**: Material Design Red palette values used for light mode
5. **WCAG Compliance**: All contrast ratios pre-calculated and verified

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved
- [x] Technology choices documented with rationale
- [x] Alternatives evaluated for key decisions
- [x] Color values verified for WCAG AA compliance
- [x] Implementation approach clear and justified
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered

**Status**: ✅ **PHASE 0 COMPLETE** - Ready for Phase 1 design artifacts
