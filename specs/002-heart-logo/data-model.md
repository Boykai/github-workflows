# Data Model: Heart Logo on Homepage

**Feature**: 002-heart-logo | **Date**: 2026-02-15  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature adds a visual presentation element (heart logo) to the user interface. The "data model" represents the SVG graphic structure, CSS styling properties, and DOM relationships rather than traditional backend data entities. This is a frontend-only feature with no database, API, or state management requirements.

## Entities

### Entity: HeartLogoElement

**Type**: DOM Element (SVG) + CSS Styles  
**Purpose**: Visual branding element displayed in application header  
**Lifecycle**: Static element rendered on component mount, persists for page lifetime

**Attributes**:

| Attribute | Type | Constraints | Value/Range |
|-----------|------|-------------|-------------|
| `elementType` | `string` | Fixed | `"svg"` |
| `role` | `string` | Fixed | `"img"` |
| `ariaLabel` | `string` | Non-empty, descriptive | `"Heart logo"` or `"Application heart logo"` |
| `viewBox` | `string` | Valid SVG viewBox | `"0 0 24 24"` (standard icon size) |
| `width` | `CSS length` | Responsive range | `clamp(40px, 8vw, 120px)` |
| `height` | `CSS length` | Aspect-preserving | `auto` |
| `fill` | `CSS color` | Brand color or fallback | `var(--color-primary)` or `currentColor` |
| `display` | `CSS display` | Block-level | `block` |
| `margin` | `CSS spacing` | Center alignment | `0 auto` (horizontal center) |

**Locations**:
- Login page: Inside `.app-login` header section before `<h1>` (line ~69 of App.tsx)
- Authenticated page: Inside `.app-header` before `<h1>` (line ~85 of App.tsx)

**Validation Rules**:
1. **Semantic correctness**: Must have `role="img"` for screen reader compatibility
2. **Descriptive label**: `aria-label` must be non-empty and describe the logo purpose
3. **Size constraints**: Width must be between 40px (minimum visibility) and 120px (maximum size)
4. **Aspect ratio**: Height must maintain 1:1 ratio with width (square icon)
5. **Color accessibility**: Must meet WCAG AA contrast ratio (3:1 for graphics) against background

**State Transitions**: None - static element with no runtime changes

**Relationships**: 
- **Parent**: Header container (`<div className="app-login">` or `<header className="app-header">`)
- **Sibling**: Application title `<h1>` element (logo appears before title)
- **Theme system**: Inherits color from CSS custom property `--color-primary` (updates on theme toggle)

---

### Entity: LogoSVGPath

**Type**: SVG Path Data  
**Purpose**: Defines heart shape geometry  
**Lifecycle**: Static data embedded in SVG element

**Attributes**:

| Attribute | Type | Constraints | Value |
|-----------|------|-------------|-------|
| `d` | `string` | Valid SVG path commands | Heart shape path (M/C/Z commands) |
| `fill` | `CSS color` | Inherited from parent SVG | `inherit` |
| `fillRule` | `string` | Optional | `"evenodd"` (if needed for complex paths) |

**Example Path Data**:
```
M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z
```

**Validation Rules**:
1. **Path validity**: Must be valid SVG path syntax (parseable by browser)
2. **Closed path**: Should end with Z command for filled shapes
3. **Coordinate system**: Must fit within viewBox bounds (0 0 24 24)

**Relationships**: 
- **Parent**: HeartLogoElement SVG container

---

### Entity: LogoStyles

**Type**: CSS Style Declarations  
**Purpose**: Control responsive sizing, positioning, and theme compatibility  
**Lifecycle**: Defined in App.css, applied to logo element

**Attributes**:

| Property | Value | Purpose |
|----------|-------|---------|
| `width` | `clamp(40px, 8vw, 120px)` | Responsive sizing (320px to 2560px screens) |
| `height` | `auto` | Maintain aspect ratio |
| `display` | `block` | Enable margin centering |
| `margin` | `0 auto 16px auto` | Horizontal center + bottom spacing |
| `fill` | `var(--color-primary)` | Brand color integration |
| `transition` | `fill 0.2s ease` | Smooth theme transitions |

**Forced Colors Mode Override**:
```css
@media (forced-colors: active) {
  fill: CanvasText;
}
```

**Validation Rules**:
1. **Size bounds**: Width clamp values must ensure visibility (min ≥ 40px, max ≤ 120px)
2. **Color accessibility**: Fill color must meet contrast requirements in both light/dark modes
3. **Responsive behavior**: Must scale smoothly across all viewport sizes

**Relationships**:
- **CSS Variables**: References `--color-primary` from theme system (index.css)
- **Media Queries**: Overridden by `forced-colors` media query for high contrast mode

---

## Entity Relationships

```
ThemeSystem (index.css)
    ↓ provides --color-primary
HeaderContainer (App.tsx)
    ↓ contains
HeartLogoElement (SVG)
    ↓ styles from
LogoStyles (App.css)
    ↓ contains
LogoSVGPath (path element)
```

**Key Relationships**:
1. **Theme Dependency**: Logo color inherits from theme system via CSS custom property
2. **Layout Hierarchy**: Logo is child of header, sibling of title
3. **Style Application**: CSS rules target logo class for responsive behavior
4. **Accessibility Tree**: Logo exposed to assistive technology via ARIA attributes

**No Dependencies On**:
- User data or session state
- Backend API models
- Database records
- Component props or state (static rendering)
- External asset files

---

## Data Validation

### Compile-Time Validation

- **TypeScript/JSX**: SVG elements and attributes are type-checked by React types
- **ESLint**: Accessibility plugin checks for `role` and `aria-label` presence
- **CSS**: Build-time validation of property syntax by Vite/PostCSS

### Runtime Validation

None required. Logo is static presentation element with no user input or dynamic generation.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. **FR-001**: Logo visible at top center of homepage (visual inspection)
2. **FR-003**: Logo responsive on mobile/tablet/desktop (DevTools responsive mode)
3. **FR-004**: Logo maintains quality 320px-2560px (resize browser window)
4. **FR-005**: Screen reader announces "Heart logo" (NVDA/JAWS/VoiceOver test)
5. **FR-007**: Logo non-interactive (verify no hover cursor, no click handler)
6. **Edge case**: Logo visible in high contrast mode (Windows High Contrast)
7. **Edge case**: Logo scales with page zoom (browser zoom to 200%)

---

## Data Storage

**Storage Mechanism**: Git repository source code  
**Format**: 
- JSX (SVG inline in App.tsx)
- CSS (styles in App.css)
**Persistence**: Version controlled via git  
**Backup**: GitHub remote repository  
**Build Output**: Compiled into React bundle (vite build)

---

## Data Flow

```
Developer writes JSX (App.tsx) + CSS (App.css)
        ↓
Git commit with logo code
        ↓
Vite build process (transpile TSX → JS)
        ↓
Bundled JavaScript + CSS
        ↓
Browser loads bundle
        ↓
React renders SVG to DOM
        ↓
CSS applies styles (responsive sizing, colors)
        ↓
User sees heart logo in header
```

**Flow Characteristics**:
- **Unidirectional**: Source → Build → Deploy → Render → Display
- **No user input**: Logo is static display element
- **No persistence layer**: No localStorage, cookies, or server state
- **No network requests**: Inline SVG has no external dependencies
- **Theme reactivity**: CSS variables update on theme toggle (automatic re-color)

---

## Data Constraints

### Technical Constraints

- **SVG browser support**: Universal support in Chrome, Firefox, Safari, Edge (target browsers)
- **viewBox coordinate system**: Must use consistent coordinate space (0 0 24 24)
- **CSS clamp() support**: Supported in all modern browsers (Chrome 79+, Firefox 75+, Safari 13.1+)
- **ARIA attributes**: `role="img"` and `aria-label` must be present for accessibility

### Business Constraints

From spec.md requirements:
- **FR-001**: MUST display heart logo at top center of homepage
- **FR-002**: MUST position logo above main content area (before `<h1>`)
- **FR-003**: MUST ensure responsive scaling on all screen sizes
- **FR-004**: MUST maintain visual quality without pixelation (SVG satisfies this)
- **FR-005**: MUST provide descriptive alt text (`aria-label`)
- **FR-006**: SHOULD use brand colors (`--color-primary`)
- **FR-007**: MUST be non-interactive (no onClick, no href)
- **FR-008**: MUST handle load failures gracefully (inline SVG satisfies this)

### Accessibility Constraints

- **WCAG 2.4.4**: Logo must have accessible name via `aria-label`
- **WCAG 1.4.11**: Graphics contrast ratio ≥ 3:1 against adjacent colors
- **WCAG 1.4.3**: Logo color must have sufficient contrast in both light/dark themes
- **Screen reader compatibility**: Must announce as image with descriptive label

### Responsive Constraints

- **Minimum size**: 40px width at 320px viewport (ensures visibility on small phones)
- **Maximum size**: 120px width at 2560px viewport (prevents oversized logo on large monitors)
- **Aspect ratio**: Must maintain 1:1 ratio (square icon) across all sizes
- **Zoom support**: Must remain crisp at 200% browser zoom (SVG vector format)

---

## Data Migration

**Migration Type**: Additive change (no existing logo to replace)  
**Rollback**: Git revert to previous commit  
**Data Loss Risk**: None - no user data, no stored state  
**Backward Compatibility**: N/A - purely additive feature

**Implementation Steps**:
1. Add inline SVG to `frontend/src/App.tsx` (2 locations)
2. Add logo styles to `frontend/src/App.css`
3. Commit changes
4. Build frontend (`npm run build`)
5. Deploy updated frontend

**No database migrations required** - frontend-only change

---

## Security Considerations

**Threat Model**: None - static SVG with no user input or dynamic generation

**Security Properties**:
- **No XSS risk**: Hardcoded SVG path, not user-generated content
- **No injection risk**: No dynamic attributes or event handlers
- **No CSRF risk**: Logo is presentational, no state-changing actions
- **No authentication impact**: Logo display is public (visible before/after login)
- **No authorization impact**: No access control decisions
- **No data leakage**: Logo contains no sensitive information

**SVG Security Notes**:
- Inline SVG avoids external resource loading (no `<use xlink:href>` with remote URLs)
- No embedded JavaScript in SVG (`<script>` tags)
- No external entity references

---

## Performance Characteristics

**Size Impact**:
- SVG path data: ~150-200 bytes (compressed)
- CSS styles: ~150 bytes
- ARIA attributes: ~30 bytes
- **Total addition**: ~400 bytes to bundle (negligible)

**Runtime Impact**:
- SVG rendering: O(1) - single DOM element creation
- CSS clamp() calculation: Computed once on layout, cached by browser
- Theme transition: CSS variable update triggers repaint (< 16ms)
- **No performance degradation expected**

**Memory Impact**: 
- One SVG DOM node per page view: ~100 bytes RAM
- CSS styles in CSSOM: ~50 bytes RAM
- Negligible overall

**Network Impact**:
- Inline SVG: 0 additional HTTP requests
- No external asset loading
- **Improves performance** compared to external image

---

## Alternative Data Models Considered

### Alternative 1: External SVG File

```typescript
<img src="/assets/heart-logo.svg" alt="Heart logo" />
```

**Rejected Rationale**: 
- Requires additional HTTP request (slower load)
- Needs asset management in public directory
- Harder to apply CSS custom properties for theming
- Creates failure scenario if file missing (violates FR-008)
- Cannot use `fill` styling on `<img>` tag (must be inline or background)

### Alternative 2: React Component with Props

```typescript
<HeartLogo size="large" color="primary" ariaLabel="Heart logo" />
```

**Rejected Rationale**: 
- Premature abstraction (YAGNI violation - Constitution V)
- Adds unnecessary files, imports, prop definitions
- Logo is static with no dynamic behavior
- Two instances don't justify component extraction
- Constitution V: "Duplication is preferable to wrong abstraction"

### Alternative 3: CSS Background Image

```css
.logo::before {
  content: "";
  background: url('data:image/svg+xml,...');
}
```

**Rejected Rationale**:
- Not semantically correct for meaningful image
- Accessibility is difficult (cannot add `aria-label` to pseudo-element)
- Cannot use CSS custom properties in data URI reliably
- More complex syntax than inline SVG

### Alternative 4: Icon Font

```html
<i className="icon-heart" aria-label="Heart logo"></i>
```

**Rejected Rationale**:
- Requires external dependency (Font Awesome, Material Icons)
- Adds 70KB+ to bundle for single icon
- Icon fonts are presentational, not semantic
- Cannot guarantee brand color styling
- Modern best practice favors inline SVG over icon fonts

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (HeartLogoElement, LogoSVGPath, LogoStyles)
- [x] Entity attributes documented with types and constraints
- [x] Validation rules defined (semantic, accessibility, responsive)
- [x] Relationships documented (DOM hierarchy, theme system, CSS cascade)
- [x] Data flow described (source → build → render → display)
- [x] Storage mechanism identified (git source code, compiled bundle)
- [x] Security considerations addressed (no risks - static content)
- [x] Performance impact assessed (negligible - ~400 bytes addition)
- [x] Accessibility constraints documented (WCAG compliance)
- [x] Responsive constraints defined (40px-120px range, viewport units)
- [x] Migration approach defined (additive change, git commit)
- [x] Alternative models evaluated and rejected

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
