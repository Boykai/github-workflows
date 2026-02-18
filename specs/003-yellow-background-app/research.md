# Research: Yellow Background Color for App

**Feature**: 003-yellow-background-app | **Date**: 2026-02-18  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires minimal research as it is a straightforward CSS variable value replacement task. The existing CSS custom property architecture (`--color-bg`, `--color-bg-secondary`) in `frontend/src/index.css` is already the correct mechanism for applying background color changes. All technical context is known from codebase exploration and the feature specification. This document satisfies the Phase 0 requirement and documents key decisions.

## Decision Areas

### 1. Yellow Color Selection (Light Mode)

**Decision**: Use #FFFDE7 (Material Yellow 50) for page background and #FFFFF0 (Ivory) for surface background

**Rationale**: 
- #FFFDE7 is a soft, muted yellow that provides warmth without visual fatigue
- Contrast ratio against primary text (#24292f): **14.27:1** — exceeds WCAG AA (4.5:1)
- #FFFFF0 (Ivory) for surfaces is a complementary near-white yellow that maintains the yellow palette while keeping elevated surfaces (cards, headers, modals) visually distinct
- Contrast ratio of #FFFFF0 against primary text (#24292f): **14.52:1** — exceeds WCAG AA (4.5:1)

**Alternatives Considered**:
- **#FFF9C4 (Material Yellow 100)**: Rejected — slightly more saturated, would reduce contrast ratio to ~12:1 and could cause visual fatigue on long reading sessions
- **#FFD700 (Gold)**: Rejected — too bold and saturated for a full-page background; contrast ratio against #24292f drops below comfortable levels for extended use
- **#FFFF00 (Pure Yellow)**: Rejected — extremely high saturation, causes eye strain and fails practical usability despite passing contrast ratio

---

### 2. Yellow Color Selection (Dark Mode)

**Decision**: Use #1A1500 (dark warm-yellow tint) for page background and #0D0A00 (deeper dark yellow) for surface background

**Rationale**:
- #1A1500 subtly carries the yellow identity into dark mode without overwhelming the dark theme
- Contrast ratio against dark-mode text (#e6edf3): **15.44:1** — exceeds WCAG AA (4.5:1)
- #0D0A00 for surfaces provides even darker tones for elevated UI elements, maintaining visual hierarchy
- Contrast ratio of #0D0A00 against dark-mode text (#e6edf3): **16.76:1** — exceeds WCAG AA (4.5:1)

**Alternatives Considered**:
- **#2B2200 (lighter warm tint)**: Rejected — too visible, making dark mode feel more like a sepia mode than a dark theme
- **#000000 (pure black)**: Rejected — loses yellow identity entirely; doesn't fulfill the spec requirement for dark-mode yellow tint
- **Keep default dark colors**: Rejected — spec FR-003 and FR-005 require dark-mode yellow-tinted backgrounds

---

### 3. Implementation Strategy

**Decision**: Direct CSS custom property value replacement in `frontend/src/index.css`

**Rationale**: 
- Application already uses `--color-bg` and `--color-bg-secondary` CSS variables
- `body` background is set to `var(--color-bg-secondary)` (page background)
- `--color-bg` is used by components for elevated surfaces (headers, cards, modals)
- Only 4 values need changing: 2 in `:root` (light mode) and 2 in `html.dark-mode-active` (dark mode)
- No new CSS variables, no component-level changes, no structural modifications

**Alternatives Considered**:
- **Tailwind CSS theme configuration**: Rejected — project does not use Tailwind CSS
- **CSS-in-JS / Styled Components**: Rejected — project uses plain CSS with custom properties
- **New CSS variables**: Rejected — existing variables are purpose-built for this exact use case; adding new ones would violate YAGNI and DRY principles
- **Inline styles on body**: Rejected — less maintainable than CSS variables, would bypass the existing theming system

---

### 4. Browser Compatibility

**Decision**: No special handling required

**Rationale**:
- CSS custom properties (variables) are supported by all target browsers: Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+
- Standard `background` property used by `body` is universally supported
- Hex color values (#FFFDE7, #FFFFF0, #1A1500, #0D0A00) are universally supported
- No vendor prefixes needed for any of the CSS used

**Alternatives Considered**:
- **Fallback background values**: Rejected — all modern browsers support CSS custom properties; no legacy browser support required per spec
- **PostCSS fallbacks**: Rejected — unnecessary complexity for universally supported CSS features

---

### 5. Accessibility Verification

**Decision**: All proposed colors pass WCAG AA with significant margin

**Rationale**:
- Light mode page background (#FFFDE7) vs text (#24292f): **14.27:1** (AA requires 4.5:1)
- Light mode surface background (#FFFFF0) vs text (#24292f): **14.52:1** (AA requires 4.5:1)
- Dark mode page background (#1A1500) vs text (#e6edf3): **15.44:1** (AA requires 4.5:1)
- Dark mode surface background (#0D0A00) vs text (#e6edf3): **16.76:1** (AA requires 4.5:1)
- All ratios exceed WCAG AA by at least 3× margin

**Alternatives Considered**:
- **Additional contrast testing tools**: Optional post-implementation — Lighthouse or axe audit recommended but not blocking
- **Custom contrast override for specific components**: Rejected — all components inherit text colors through CSS variables and maintain their own backgrounds where needed

---

### 6. Testing Strategy

**Decision**: Manual verification only; no new tests required

**Rationale**:
- Feature is a visual CSS change with no programmatic logic
- Constitution Principle IV (Test Optionality): Tests are optional by default
- Spec acceptance criteria are human-verifiable (open app, observe background color)
- Existing component styles are preserved; no component-level changes
- Contrast ratios verified computationally in this research phase

**Alternatives Considered**:
- **Visual regression tests**: Rejected — overkill for CSS variable value changes; no visual regression testing infrastructure exists
- **Unit tests for CSS values**: Rejected — CSS values are not testable through unit test frameworks without additional tooling
- **E2E screenshot comparison**: Rejected — adds infrastructure complexity for a simple color change

---

### 7. Rollback Strategy

**Decision**: Standard git revert

**Rationale**:
- Changes are 4 CSS variable value replacements in 1 file
- No database migrations, API changes, or state management involved
- Git commit revert immediately restores previous colors
- No deployment coordination required

**Alternatives Considered**:
- **Feature flag**: Rejected — massive overkill for CSS variable value change
- **Dual theme support**: Rejected — unnecessary complexity for one-time color update

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None — CSS variable value replacements in well-understood file
- **User Impact**: Positive — adds warm yellow visual identity
- **Accessibility Risk**: None — all color pairs verified to exceed WCAG AA by 3× margin
- **Testing Risk**: Low — manual verification sufficient
- **Rollback Risk**: None — instant git revert available

## Best Practices Applied

1. **YAGNI (You Aren't Gonna Need It)**: No new CSS variables or theming infrastructure
2. **KISS (Keep It Simple)**: Direct value replacement over abstraction
3. **DRY (Don't Repeat Yourself)**: Leverages existing CSS custom property architecture
4. **WCAG Compliance**: All color pairs verified computationally
5. **Atomic Commits**: Single commit for related changes

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved
- [x] Technology choices documented with rationale
- [x] Alternatives evaluated for key decisions
- [x] Implementation approach clear and justified
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered
- [x] Accessibility verified for all color pairs

**Status**: ✅ **PHASE 0 COMPLETE** - Ready for Phase 1 design artifacts
