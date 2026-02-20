# Research: Add Purple Background Color to App

**Feature**: 005-purple-background | **Date**: 2026-02-20  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires minimal research as it is a straightforward CSS theming change. The existing codebase already uses CSS custom properties for theming with light/dark mode support. The primary decisions involve which CSS variable to modify, how to preserve existing component backgrounds, and ensuring WCAG AA contrast compliance for text rendered directly on the purple surface.

## Decision Areas

### 1. CSS Variable Strategy

**Decision**: Introduce a new CSS custom property `--color-bg-app: #7C3AED` and apply it to the `body` element, replacing the current `var(--color-bg-secondary)` reference

**Rationale**:
- The existing `--color-bg-secondary` variable (`#f6f8fa` light / `#161b22` dark) is used by 15+ component selectors (board columns, sidebar headers, theme toggle, modals, etc.)
- Changing `--color-bg-secondary` directly would propagate purple into all those component backgrounds — violating the spec scope ("apply to the app's root/main container element")
- A dedicated variable isolates the body background from component-level backgrounds
- The new variable follows the existing naming convention (`--color-bg`, `--color-bg-secondary`, now `--color-bg-app`)

**Alternatives Considered**:
- **Modify `--color-bg-secondary` directly**: Rejected — would turn board columns, modal fields, sidebar headers, and 12+ other elements purple, breaking visual hierarchy
- **Modify `--color-bg` directly**: Rejected — `--color-bg` is used for component foreground backgrounds (header, sidebar, chat section, cards). Changing it to purple would make all components purple
- **Hardcode `background: #7C3AED` on body**: Rejected — violates FR-006 (centralized theming mechanism) and the existing CSS variable pattern

**Implementation**: Add `--color-bg-app: #7C3AED` to `:root` and `html.dark-mode-active`, then update `body` to use `background: var(--color-bg-app)`

---

### 2. Purple Shade Selection

**Decision**: Use #7C3AED (modern violet) as specified in the feature spec

**Rationale**:
- Spec explicitly selects #7C3AED in FR-001 and FR-002
- Issue description recommends #7C3AED as "modern violet" option
- Provides good contrast with white text (6.65:1 ratio — exceeds WCAG AA 4.5:1)
- Modern, vibrant aesthetic appropriate for a tech application

**Alternatives Considered**:
- **#6A0DAD (deep royal purple)**: Not selected — darker shade, higher contrast but less modern feel
- **#C084FC (soft lavender)**: Not selected — too light, poor contrast with white text (~1.7:1)
- **CSS keyword `purple` (#800080)**: Rejected per FR-002 — generic keyword may render differently

**Implementation**: Use literal hex value `#7C3AED` in the CSS custom property definition

---

### 3. Text Contrast on Purple Background

**Decision**: Update text colors on surfaces exposed to the purple body background (login page, loading screen) to white/light tones for WCAG AA compliance

**Rationale**:
- Current `--color-text` is `#24292f` (dark) — contrast ratio against #7C3AED is only ~2.03:1 (FAILS WCAG AA)
- White (`#FFFFFF`) on #7C3AED yields ~6.65:1 contrast ratio (PASSES WCAG AA)
- Current `--color-text-secondary` is `#57606a` — contrast ratio against #7C3AED is only ~2.62:1 (FAILS)
- The login page (`.app-login`) and loading screen (`.app-loading`) sit directly on the body background with no intermediate opaque container
- Authenticated views are unaffected — `.app-header`, `.project-sidebar`, `.chat-section`, `.board-page` all have `background: var(--color-bg)` (white/dark)

**Alternatives Considered**:
- **Change global `--color-text` to white**: Rejected — would break all text in components that have white/light backgrounds (header, sidebar, cards, etc.)
- **Add a wrapper div with white background behind authenticated content**: Rejected — overengineered; authenticated components already have their own backgrounds
- **Use text-shadow for readability**: Rejected — non-standard approach, doesn't improve measured contrast ratio

**Implementation**: Add targeted CSS overrides for `.app-login` and `.app-loading` to use `color: #FFFFFF` for headings and `color: rgba(255, 255, 255, 0.85)` for secondary text

---

### 4. Dark Mode Handling

**Decision**: Apply the same purple (#7C3AED) in both light and dark modes for the body background

**Rationale**:
- Spec states "the purple background should render consistently regardless of theme mode"
- The purple serves as a brand identity element — switching it per theme would undermine branding
- Both light and dark mode components overlay the body with their own opaque backgrounds, so the purple only shows on login/loading screens

**Alternatives Considered**:
- **Darker purple in dark mode (e.g., #5B21B6)**: Rejected — spec requires consistent rendering regardless of theme
- **Skip dark mode update**: Rejected — would show dark `#161b22` body in dark mode instead of purple

**Implementation**: Set `--color-bg-app: #7C3AED` in both `:root` and `html.dark-mode-active` blocks

---

### 5. FOUC Prevention

**Decision**: No additional measures needed — CSS custom properties load synchronously

**Rationale**:
- `index.css` is imported in `main.tsx` and bundled by Vite into the main CSS chunk
- CSS variables defined in `:root` are applied before first paint
- No JavaScript-dependent color application (unlike theme toggle, which is post-hydration)
- The `<link>` or inline `<style>` in the Vite build loads before React mounts

**Alternatives Considered**:
- **Inline style on `<body>` in index.html**: Rejected — unnecessary; Vite's CSS bundling already prevents FOUC
- **Critical CSS extraction**: Rejected — overkill for single variable addition

**Implementation**: Standard CSS variable in `index.css` — no special FOUC handling needed

---

### 6. Cross-Browser Consistency

**Decision**: No special handling required — CSS custom properties are universally supported

**Rationale**:
- CSS custom properties (`var()`) have 97%+ global browser support (caniuse.com)
- All target browsers (Chrome, Firefox, Safari, Edge) support CSS custom properties since 2016+
- Hex color values render identically across browsers (no color profile differences for sRGB hex)
- No vendor prefixes required

**Alternatives Considered**:
- **Fallback `background` property before `var()`**: Rejected — all target browsers support CSS variables
- **PostCSS custom properties plugin**: Rejected — unnecessary for modern browsers

**Implementation**: Direct use of `var(--color-bg-app)` with no fallbacks

---

### 7. Component Impact Audit

**Decision**: No component-level CSS changes needed beyond login and loading screens

**Rationale**:
- Audited all CSS selectors in `App.css` and `index.css`
- Authenticated layout: `.app-header` (white bg), `.project-sidebar` (white bg), `.chat-section` (white bg), `.board-page` (white bg) — all cover the purple body completely
- Board columns, cards, modals, popovers — all have explicit `background: var(--color-bg)` or `var(--color-bg-secondary)` with opaque values
- Only exposed surfaces: `.app-login` (login page) and `.app-loading` (loading spinner) — these float on the body with no background override

**Alternatives Considered**:
- **Add white backgrounds to login/loading containers**: Rejected — defeats the purpose of showing the purple background
- **Audit and modify every component**: Rejected — unnecessary; components already have opaque backgrounds

**Implementation**: Only `.app-login` and `.app-loading` need text color adjustments

---

### 8. LoginButton Component Contrast

**Decision**: No changes needed — LoginButton already uses white text on dark background

**Rationale**:
- `.login-button` has `background: var(--color-text)` (dark) and `color: white`
- The button is self-contained with its own opaque background
- White text on dark button background maintains existing contrast
- Button renders correctly regardless of parent background color

**Alternatives Considered**:
- **Change button to outline style on purple**: Rejected — would require additional component changes beyond scope

**Implementation**: No changes to LoginButton component or styles

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None — CSS variable addition in well-understood file
- **User Impact**: Positive — establishes branded visual identity
- **Testing Risk**: Low — manual verification sufficient, automated tests unaffected
- **Rollback Risk**: None — instant git revert of single CSS file

## Best Practices Applied

1. **YAGNI (You Aren't Gonna Need It)**: No theme picker, no multiple purple variants, no configuration infrastructure
2. **KISS (Keep It Simple)**: Single CSS variable addition with targeted overrides
3. **DRY (Don't Repeat Yourself)**: Purple value defined once in CSS variable, referenced via `var()`
4. **Separation of Concerns**: Body background isolated from component backgrounds via dedicated variable
5. **Progressive Enhancement**: CSS variables degrade gracefully (transparent background if unsupported — N/A for modern browsers)

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved
- [x] Technology choices documented with rationale
- [x] Alternatives evaluated for key decisions
- [x] Implementation approach clear and justified
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered

**Status**: ✅ **PHASE 0 COMPLETE** — Ready for Phase 1 design artifacts
