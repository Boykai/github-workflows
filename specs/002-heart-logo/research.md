# Research: Heart Logo on Homepage

**Feature**: 002-heart-logo | **Date**: 2026-02-15  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature adds a visual branding element (heart logo) to the homepage. Research focuses on logo format, positioning strategy, responsive design approach, and accessibility implementation to meet all functional requirements while maintaining code simplicity.

## Decision Areas

### 1. Logo Format and Asset Type

**Decision**: Inline SVG heart icon

**Rationale**: 
- SVG provides perfect scalability for responsive requirements (320px to 2560px)
- No external file dependency eliminates load failure scenarios
- Can use CSS custom properties for brand colors (maintains theme compatibility)
- Inline SVG is immediately available (no HTTP request = faster load time)
- Full accessibility control via SVG attributes (aria-label, role, title)
- Small heart icon has minimal SVG code (~10-20 lines)

**Alternatives Considered**:
- **External SVG file** (`<img src="/heart.svg">`): Rejected - requires asset management, introduces HTTP request latency, complicates alt text implementation, creates file-missing failure scenario
- **PNG/JPG image file**: Rejected - raster format causes pixelation at large sizes (fails FR-004), larger file size, no color theming capability
- **Icon font (e.g., Font Awesome)**: Rejected - adds external dependency (70KB+ for one icon), increases bundle size, semantic accessibility is harder (icon fonts are presentational)
- **Unicode heart character** (❤️): Rejected - limited styling control, inconsistent rendering across browsers/OS, cannot guarantee brand colors

**Implementation**: Create inline SVG element in React component with proper semantic structure and ARIA attributes

---

### 2. Logo Positioning Strategy

**Decision**: Dedicated logo container in app header above title

**Rationale**:
- Current header structure (`app-header` class) has title and actions in flex layout
- Adding logo container before title maintains semantic hierarchy
- CSS flexbox with center alignment achieves "top center" requirement
- Works on both login page and authenticated view (both have headers)
- No layout disruption to existing header actions (theme toggle, login button)

**Alternatives Considered**:
- **Absolute positioning**: Rejected - fragile on responsive layouts, risks overlapping with other header elements, difficult to maintain vertical rhythm
- **Separate header row**: Rejected - adds unnecessary DOM depth, complicates existing flex layout, wastes vertical space
- **Logo as background image**: Rejected - not semantically correct, accessibility is difficult, cannot be inspected/copied

**Implementation**: 
1. Add logo container before `<h1>` in header
2. Use CSS flexbox column direction for logo stacking above title
3. Apply `text-align: center` or `align-items: center` for centering

---

### 3. Responsive Sizing Strategy

**Decision**: CSS viewport-based sizing with min/max constraints

**Rationale**:
- `width: clamp(40px, 8vw, 120px)` provides responsive scaling
- Minimum 40px ensures visibility on small screens (320px width)
- Maximum 120px prevents oversized logo on ultra-wide displays
- `height: auto` maintains aspect ratio (prevents distortion)
- Scales smoothly across all breakpoints without media queries
- SVG inherent scalability ensures crisp rendering at all sizes

**Alternatives Considered**:
- **Fixed pixel sizes with media queries**: Rejected - requires multiple breakpoints, harder to maintain, step changes rather than smooth scaling
- **Percentage-based sizing**: Rejected - size depends on parent width which varies by content, unpredictable results
- **rem/em units**: Rejected - scales with font size not viewport, may become too large/small if user adjusts browser font settings

**Implementation**: CSS rule with `clamp()` function for width, `height: auto` for aspect preservation

---

### 4. Brand Color Integration

**Decision**: Use existing CSS custom properties from design system

**Rationale**:
- Application already defines `--color-primary` (#0969da light, #539bf5 dark)
- Heart logo traditionally red, but spec says "SHOULD use brand colors" (not MUST)
- Primary blue aligns with GitHub branding (application context)
- Automatic dark mode support (CSS variable updates on theme toggle)
- No additional color definitions needed
- Fallback to currentColor if variables undefined (graceful degradation)

**Alternatives Considered**:
- **Hardcoded red color** (#cf222e): Rejected - ignores brand color requirement, no dark mode adaptation, less cohesive with UI
- **New CSS variable for logo**: Rejected - YAGNI violation, single-use variable adds complexity
- **Gradient or multi-color**: Rejected - complicates implementation, no requirement for complex styling

**Implementation**: SVG `fill` attribute uses `var(--color-primary)` with `currentColor` fallback

---

### 5. Accessibility Implementation

**Decision**: Semantic SVG with proper ARIA attributes

**Rationale**:
- SVG with `role="img"` announces as image to screen readers
- `aria-label="Heart logo"` provides descriptive text (satisfies FR-005)
- Decorative nature means `aria-hidden="false"` to ensure announcement
- No interactive elements needed (satisfies FR-007: non-interactive)
- Works across all major screen readers (NVDA, JAWS, VoiceOver)

**Alternatives Considered**:
- **`<title>` element inside SVG**: Rejected - inconsistent screen reader support, `aria-label` is more reliable
- **Empty alt text** (`aria-hidden="true"`): Rejected - spec requires descriptive text (FR-005)
- **Visually hidden text span**: Rejected - unnecessary with proper SVG attributes

**Implementation**: 
```jsx
<svg role="img" aria-label="Heart logo" ...>
  <path d="..." />
</svg>
```

---

### 6. Component Structure

**Decision**: Inline SVG directly in App.tsx header sections

**Rationale**:
- Logo appears in 2 locations (login page header, authenticated header)
- Both are in same component (App.tsx)
- Small SVG code doesn't justify separate component
- DRY violation (2 instances) is acceptable per Constitution V (duplication preferable to wrong abstraction)
- No props or state needed - static presentation

**Alternatives Considered**:
- **Dedicated Logo component**: Rejected - premature abstraction for simple static SVG, adds file overhead, imports, and complexity for no benefit
- **Shared constant**: Rejected - JSX cannot be easily shared as constant without React.createElement or Fragment, increases complexity

**Implementation**: Copy inline SVG into both header sections (login and authenticated)

---

### 7. Logo Failure Handling

**Decision**: No special handling needed for inline SVG

**Rationale**:
- Inline SVG cannot "fail to load" (no HTTP request)
- SVG rendering failure is catastrophic browser issue (not application concern)
- Aria-label already provides text alternative if visual fails
- Spec's FR-008 (handle load failures gracefully) is satisfied by inline approach

**Alternatives Considered**:
- **Fallback image element**: Not applicable - inline SVG has no load failure mode
- **Error boundary**: Rejected - overkill for static presentation, SVG errors are non-recoverable anyway

**Implementation**: No error handling code required

---

### 8. Testing Strategy

**Decision**: Manual verification + optional E2E test update

**Rationale**:
- Constitution Principle IV: Tests are optional by default
- Feature is visual presentation with no business logic
- Acceptance criteria are human-verifiable (see logo, check responsiveness)
- E2E tests in `frontend/e2e/` may need logo assertion updates
- Playwright can screenshot for visual regression if desired

**Alternatives Considered**:
- **Visual regression testing**: Rejected - no existing infrastructure, overkill for single addition
- **Unit tests for Logo component**: Rejected - no separate component exists, testing inline SVG presence is low value
- **Automated responsive testing**: Rejected - manual browser DevTools verification is sufficient

**Implementation**: 
1. Manual verification in browser (multiple screen sizes)
2. Check with screen reader for accessibility
3. Optionally update E2E tests if they assert header content

---

### 9. High Contrast Mode Support

**Decision**: Use CSS `forced-colors` media query with `CanvasText` color

**Rationale**:
- Windows High Contrast Mode and browser reader modes override custom colors
- `forced-colors: active` media query detects high contrast
- `CanvasText` system color ensures logo visible in user's chosen scheme
- Maintains accessibility for users with contrast sensitivity
- Addresses edge case in spec (high contrast mode visibility)

**Alternatives Considered**:
- **No high contrast handling**: Rejected - spec explicitly mentions this edge case
- **Fixed high contrast color**: Rejected - may not match user's chosen theme

**Implementation**:
```css
@media (forced-colors: active) {
  .heart-logo {
    fill: CanvasText;
  }
}
```

---

### 10. Page Zoom Support

**Decision**: SVG with viewport units handles zoom automatically

**Rationale**:
- Browser zoom scales all content including SVG proportionally
- Viewport units (vw) scale with zoom level
- SVG vector format ensures crisp rendering at 200%+ zoom
- No special code needed - browser handles this natively
- Addresses edge case in spec (zoom behavior)

**Alternatives Considered**:
- **JavaScript zoom detection**: Rejected - unnecessary, browser zoom is transparent to code
- **Fixed pixel sizes**: Rejected - would scale but less smoothly than viewport units

**Implementation**: No special code needed - existing SVG + viewport sizing handles zoom

---

## Implementation Risks

**Risk Level**: LOW

- **Technical Risk**: Minimal - inline SVG is well-supported technology
- **User Impact**: Positive - enhances branding with no functionality changes
- **Testing Risk**: Low - visual feature with straightforward acceptance criteria
- **Rollback Risk**: None - additive change, no breaking modifications
- **Performance Risk**: Negligible - small inline SVG adds ~1KB to bundle

## Best Practices Applied

1. **KISS (Keep It Simple)**: Inline SVG over asset management infrastructure
2. **YAGNI (You Aren't Gonna Need It)**: No separate component for static icon
3. **Semantic HTML/SVG**: Proper ARIA attributes for accessibility
4. **Progressive Enhancement**: Logo is additive, app works without it
5. **Responsive Design**: Mobile-first approach with viewport units
6. **Accessibility First**: Screen reader support built in from start

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved
- [x] Logo format decision (inline SVG) with rationale
- [x] Positioning strategy (header container) documented
- [x] Responsive approach (viewport units with clamp) defined
- [x] Brand color integration (CSS variables) specified
- [x] Accessibility implementation (ARIA attributes) planned
- [x] Edge cases (high contrast, zoom) addressed
- [x] Component structure (inline in App.tsx) decided
- [x] Testing approach (manual + optional E2E) confirmed
- [x] Alternatives evaluated for all key decisions
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered

**Status**: ✅ **PHASE 0 COMPLETE** - Ready for Phase 1 design artifacts
