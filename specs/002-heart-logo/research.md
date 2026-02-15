# Research: Heart Logo on Homepage

**Feature**: 002-heart-logo | **Date**: 2026-02-15 | **Spec**: [spec.md](./spec.md)

## Phase 0: Research & Decision Log

This document captures technical decisions made during the planning phase.

---

## Decision 1: Logo Asset Format

**Context**: Need to choose between SVG, PNG, or other image formats for the heart logo.

**Options Considered**:
1. **SVG (Scalable Vector Graphics)** - Vector format, infinitely scalable, small file size
2. **PNG** - Raster format, good quality but fixed resolution, larger file size
3. **WebP** - Modern format, better compression but limited browser support in older browsers

**Decision**: Use **SVG**

**Rationale**:
- SVG is infinitely scalable without quality loss (FR-004: maintain visual quality at all resolutions)
- Small file size ensures fast loading (SC-001: visible within 1 second)
- Perfect for responsive design (FR-003: scales appropriately on all screen sizes)
- Can be styled with CSS for brand colors (FR-006: use brand colors)
- Excellent browser support across all modern browsers (SC-003)
- No pixelation at any zoom level (edge case: 200% zoom)

**Alternatives Rejected**:
- PNG: Would need multiple resolutions (1x, 2x, 3x) for different screen densities, increasing complexity
- WebP: Better compression but potential compatibility issues with older browsers

---

## Decision 2: Asset Storage Location

**Context**: Need to determine where to store the logo asset in the project structure.

**Options Considered**:
1. **frontend/public/** - Vite's default for static assets (copied as-is to dist/)
2. **frontend/src/assets/** - For assets imported via JS modules
3. **Root public/** - Less conventional for Vite projects

**Decision**: Use **frontend/public/**

**Rationale**:
- Vite's recommended location for static assets that don't need processing
- Assets in public/ are served at root path (e.g., `/heart-logo.svg`)
- Simple reference path from HTML/React: `<img src="/heart-logo.svg" />`
- No webpack/vite processing overhead
- Consistent with Vite best practices (existing `/vite.svg` favicon is in this location)

**Alternatives Rejected**:
- src/assets/: Requires import statements, adds build complexity, unnecessary for simple static logo
- Root public/: Would mix backend and frontend concerns, violates project structure convention

---

## Decision 3: Component Modification Strategy

**Context**: Need to determine where in the App.tsx component to place the logo.

**Options Considered**:
1. **Login section (lines 68-71)** - Top of the login page
2. **App header (lines 84-85)** - Visible for authenticated users
3. **Both locations** - Show logo everywhere

**Decision**: Add logo to **login section** (homepage = login page for unauthenticated visitors)

**Rationale**:
- Spec explicitly states "homepage" and login page is the first page visitors see (User Story 1)
- Aligns with acceptance scenario: "visitor accessing the homepage for the first time"
- Login page is the primary branding touchpoint for new users
- Can be extended later if needed for authenticated header
- Keeps change minimal and focused per constitution principle V

**Alternatives Rejected**:
- Authenticated header: Would serve existing users, but spec focuses on "visitors" and "homepage"
- Both: Would expand scope beyond spec requirements

---

## Decision 4: Styling Approach

**Context**: Need to determine how to style the logo for positioning, sizing, and responsiveness.

**Options Considered**:
1. **CSS class in App.css** - Component-specific styling
2. **Inline styles in React** - JS-based styling
3. **Global CSS in index.css** - Theme-level styling

**Decision**: Add **CSS class in App.css**

**Rationale**:
- Consistent with existing project pattern (App.css exists with component-specific styles)
- Allows use of responsive CSS (media queries for mobile/tablet/desktop)
- Keeps presentation logic in CSS, not JS (separation of concerns)
- Easy to maintain and modify
- Can leverage existing CSS variables from index.css for colors

**Alternatives Rejected**:
- Inline styles: Less maintainable, no media query support, violates separation of concerns
- Global CSS: Logo styling is component-specific, not a global concern

---

## Decision 5: Responsive Design Strategy

**Context**: Logo must adapt to different screen sizes (FR-003, User Story 2).

**Options Considered**:
1. **Fixed pixel size** - Same size on all devices
2. **Percentage-based sizing** - Relative to container
3. **CSS clamp() with media queries** - Responsive scaling with min/max bounds

**Decision**: Use **CSS clamp() with media queries**

**Rationale**:
- Provides fluid scaling between minimum and maximum sizes
- `clamp(min, preferred, max)` prevents logo from being too small or too large
- Media queries can override for specific breakpoints if needed
- Handles edge case: extremely small screens (<320px) with graceful min size
- Handles edge case: page zoom with proportional scaling

**Example**:
```css
.logo {
  width: clamp(60px, 10vw, 120px);
  height: auto;
}
```

**Alternatives Rejected**:
- Fixed size: Doesn't adapt to mobile vs desktop, violates FR-003
- Pure percentage: Could become too large on large screens or too small on mobile

---

## Decision 6: Accessibility Implementation

**Context**: Must provide descriptive alt text for screen readers (FR-005, User Story 3).

**Options Considered**:
1. **Alt attribute** - Standard HTML approach
2. **ARIA label** - Accessible rich internet application approach
3. **Both** - Redundant but comprehensive

**Decision**: Use **alt attribute**

**Rationale**:
- Standard HTML5 approach for images
- Universally supported by screen readers (SC-004: 100% coverage)
- Gracefully falls back if image fails to load (edge case: missing file)
- Simple and semantic
- Meets WCAG 2.1 Level AA guidelines (assumption in spec)

**Alt text value**: "Heart logo - [App Name]" (e.g., "Heart logo - Tech Connect 2026")

**Alternatives Rejected**:
- ARIA label: More complex, usually for interactive elements, unnecessary for static logo
- Both: Redundant and could cause screen readers to announce twice

---

## Decision 7: Logo Positioning

**Context**: Logo must be "at the top center of the homepage, above the main content" (FR-001, FR-002).

**Options Considered**:
1. **Flexbox centering** - Modern, simple, well-supported
2. **CSS Grid** - Modern but overkill for single element
3. **Absolute positioning** - Precise but fragile

**Decision**: Use **Flexbox** within existing login container

**Rationale**:
- Login section already uses flexbox layout (App.css)
- Adding logo as first child naturally places it at top
- `align-items: center` and `justify-content: center` handle centering
- Responsive and maintains flow with other elements
- No risk of overlapping content

**Alternatives Rejected**:
- CSS Grid: Overkill for adding single element to existing layout
- Absolute positioning: Brittle, could break on different screen sizes

---

## Decision 8: Logo Interactivity

**Context**: Spec states logo must be non-interactive (FR-007: clicking does not trigger any action).

**Options Considered**:
1. **Plain img element** - No click handler
2. **Disabled button/link** - Interactive but disabled
3. **Div with background image** - Alternative approach

**Decision**: Use **plain img element**

**Rationale**:
- Simplest implementation
- No click events by default
- Semantic HTML (img is for images)
- No need for `pointer-events: none` since there's no click handler
- Clear and explicit implementation of FR-007

**Alternatives Rejected**:
- Disabled button/link: Adds unnecessary complexity, confusing for users/screen readers
- Div with background: Less semantic, harder for accessibility

---

## Decision 9: Brand Colors Implementation

**Context**: FR-006 states logo "SHOULD use the app's brand colors."

**Options Considered**:
1. **Use existing CSS variables** - `--color-primary`, `--color-accent`
2. **Hardcode colors in SVG** - Fixed colors
3. **CSS fill property** - Style SVG with CSS

**Decision**: Create SVG with **CSS fill property** using existing CSS variables

**Rationale**:
- SVG fill can be styled with CSS `fill` property
- Leverages existing theme colors from index.css (lines 2-30)
- Supports light/dark mode automatically (if theme system uses CSS variables)
- Consistent with existing project styling approach

**Example**:
```css
.logo {
  fill: var(--color-primary);
}
```

**Alternatives Rejected**:
- Hardcoded colors: Doesn't adapt to theme changes, harder to maintain
- Inline SVG: More complex than external file reference

---

## Decision 10: Error Handling for Missing Logo

**Context**: FR-008 requires graceful handling of logo load failures (edge case: missing image file).

**Options Considered**:
1. **Alt text only** - Browser default behavior
2. **Onerror handler** - JS-based fallback
3. **Picture element with fallback** - Multiple sources

**Decision**: Use **alt text only** (browser default)

**Rationale**:
- Browser naturally displays alt text if image fails to load
- No additional JS required
- Meets FR-008 requirement
- Graceful degradation with zero code
- WCAG 2.1 compliant

**Alternatives Rejected**:
- Onerror handler: Adds complexity, unnecessary for this use case
- Picture element: Overkill, intended for multiple formats/resolutions

---

## Summary

All technical decisions align with:
- Specification requirements (8 functional requirements)
- Constitution principle V (Simplicity & DRY)
- Existing project conventions (React + TypeScript + CSS)
- Web accessibility standards (WCAG 2.1 Level AA)
- Modern browser best practices

No dependencies to add. No database changes. No API changes. Pure frontend presentation layer addition.
