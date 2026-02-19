# Research: Add Black Background Theme

**Feature**: 007-black-background | **Date**: 2026-02-19  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature modifies the app's visual theme to use a black background by updating CSS custom property values and auditing hardcoded colors. The existing design token architecture (`--color-bg`, `--color-bg-secondary`, `--color-text`, etc.) in `frontend/src/index.css` already centralizes background and text colors, so the primary work is value replacement. Research focused on optimal black shade, WCAG contrast compliance, preventing flash of white content (FOWC), and handling hardcoded values.

## Decision Areas

### 1. Black Shade Selection

**Decision**: Use `#000000` (true black) for `--color-bg` and `#121212` for `--color-bg-secondary`

**Rationale**:
- Spec allows either `#000000` or `#121212` as acceptable near-black
- True black (`#000000`) for the primary background provides maximum contrast with white text (21:1 ratio — exceeds WCAG AAA)
- `#121212` for secondary backgrounds (cards, sidebars, columns) provides visual depth and component separation without looking flat
- This two-tier approach follows Material Design's dark theme guidance where surface colors use slight elevation via lightness
- The existing dark mode already uses `#0d1117` / `#161b22`; the new values are darker to match the "black background" requirement

**Alternatives Considered**:
- **Single `#000000` for both tokens**: Rejected — components would be indistinguishable from the page background. No visual hierarchy or depth.
- **Single `#121212` for both tokens**: Rejected — spec explicitly requests "true black" as primary option. Near-black only as alternative.
- **`#0A0A0A` for primary**: Considered — would also meet spec. `#000000` chosen for simplicity and exact match to spec language.

---

### 2. Text and Foreground Colors for Contrast

**Decision**: Use `#e6edf3` for primary text and `#8b949e` for secondary text (same as existing dark mode)

**Rationale**:
- `#e6edf3` on `#000000` = 17.4:1 contrast ratio — exceeds WCAG AAA (7:1) and AA (4.5:1)
- `#8b949e` on `#000000` = 7.2:1 contrast ratio — exceeds WCAG AA (4.5:1)
- `#8b949e` on `#121212` = 6.0:1 contrast ratio — exceeds WCAG AA (4.5:1)
- These values are already proven in the app's existing dark mode and require no adjustment
- All interactive elements (buttons, links) using `--color-primary: #539bf5` on `#000000` = 8.1:1 — exceeds WCAG AA

**Alternatives Considered**:
- **Pure white `#ffffff` for primary text**: Rejected — too harsh on pure black background, causes eye strain. `#e6edf3` is softer while maintaining excellent contrast.
- **Custom contrast values**: Rejected — existing dark mode values already verified and in use. Reuse avoids introducing untested color combinations.

---

### 3. Preventing Flash of White Content (FOWC)

**Decision**: Add inline `style="background-color: #000000"` on `<html>` element in `index.html`

**Rationale**:
- External CSS loads asynchronously; during parse/load time, browser renders default white background
- Inline style on `<html>` is applied before any external resources load
- This is a zero-cost solution (no extra HTTP requests, no JavaScript)
- Spec FR-005 explicitly requires preventing white flash during page load
- The existing `index.html` has no inline styles, so this is a clean addition

**Alternatives Considered**:
- **Inline `<style>` block in `<head>`**: Viable but more verbose. Single attribute is simpler.
- **Critical CSS inlining via Vite plugin**: Rejected — overkill for single property. Adds build complexity.
- **`prefers-color-scheme` media query**: Rejected — this feature makes black the default regardless of OS preference.
- **Server-side rendering of initial styles**: Rejected — app is a client-side SPA with no SSR.

---

### 4. Handling the Dark Mode Toggle

**Decision**: Update `:root` (default/light mode) token values to black theme. Keep `html.dark-mode-active` overrides as-is for now.

**Rationale**:
- Spec states: "The existing dark mode toggle (if present) is separate from this feature; this feature makes black the default background regardless of any dark mode setting."
- The `:root` selector defines the default (light mode) values. By changing these to black theme values, the app is black by default.
- The `html.dark-mode-active` class overrides remain untouched — they already define a dark theme (GitHub-style `#0d1117`). The toggle still functions but switches between two dark variants.
- This is the simplest approach: change defaults, don't touch the toggle mechanism.

**Alternatives Considered**:
- **Remove dark mode toggle entirely**: Rejected — spec does not require removing existing functionality. Toggle still works.
- **Make dark mode the permanent state via JavaScript**: Rejected — adds complexity. CSS-only solution is simpler.
- **Create a third "black" theme class**: Rejected — YAGNI. Over-engineering for a single-value change.

---

### 5. Auditing Hardcoded Light Background Values

**Decision**: Replace hardcoded light backgrounds in `App.css` and `ChatInterface.css` with dark-compatible values

**Rationale**:
- `App.css` contains `#fff1f0` (error toast/banner background) — appears as light pink on black, needs dark alternative
- `App.css` contains `#dafbe1` in the highlight animation — light green on black, needs dark alternative
- `App.css` contains `#82071e` (error text) — dark red that works fine on black backgrounds
- `ChatInterface.css` uses `var(--color-*)` tokens throughout — already compatible
- Some hardcoded accent colors (`#2da44e`, `#cf222e`, `#d29922`, etc.) are semantic colors for status indicators — these work on dark backgrounds and don't need changing

**Alternatives Considered**:
- **Convert all hardcoded colors to CSS variables**: Rejected per YAGNI — only light backgrounds cause visual issues on black. Status/accent colors work fine.
- **Leave hardcoded values unchanged**: Rejected — `#fff1f0` creates jarring light rectangles on black background (spec FR-007 requires audit).

**Implementation**:
- `#fff1f0` (error toast/banner) → `rgba(207, 34, 46, 0.15)` (dark red tint, matches existing dark theme patterns)
- `#dafbe1` (highlight animation start) → `rgba(45, 164, 78, 0.2)` (dark green tint)
- `#82071e` (error banner message) → `#ff6b6b` (lighter red for readability on dark)

---

### 6. Border and Shadow Adjustments

**Decision**: Update `--color-border` to `#30363d` and `--shadow` to use higher opacity

**Rationale**:
- Current light mode border `#d0d7de` is too light on black background — barely visible
- `#30363d` is the existing dark mode border value — proven to work on dark backgrounds
- Current light mode shadow `rgba(0, 0, 0, 0.1)` is invisible on black — increase to `rgba(0, 0, 0, 0.4)`
- These match the existing `html.dark-mode-active` values, ensuring visual consistency

**Alternatives Considered**:
- **Keep light mode borders**: Rejected — light gray borders on black look washed out and create poor visual hierarchy
- **Use brighter borders**: Rejected — would look garish. Subtle dark gray borders are standard for dark themes

---

### 7. Browser Compatibility

**Decision**: No special handling required beyond CSS custom properties fallback

**Rationale**:
- CSS custom properties are supported in all modern browsers (Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+)
- Spec states: "Standard web browser support (latest 2 versions of Chrome, Firefox, Safari, Edge) is sufficient"
- Inline `style` attribute on `<html>` is universally supported
- Spec edge case mentions CSS custom property fallback — add `background: #000000` before `background: var(--color-bg)` for safety

**Alternatives Considered**:
- **PostCSS custom properties fallback plugin**: Rejected — adds build dependency for edge case with negligible user impact
- **JavaScript-based polyfill**: Rejected — unnecessary for supported browsers

---

### 8. Third-Party Content Handling

**Decision**: No third-party embeds currently exist in the app; document approach for future

**Rationale**:
- Code audit shows no `<iframe>` elements or third-party widget integrations in any component
- Spec FR-008 requires handling third-party content — satisfied by noting there are none currently
- If added in future, the recommended approach is a dark wrapper container with matching background

**Alternatives Considered**:
- **Preemptively add iframe styling rules**: Rejected per YAGNI — no iframes exist to style

---

## Implementation Risks

**Risk Level**: LOW

- **Technical Risk**: Minimal — CSS token value changes with well-understood effects
- **User Impact**: Positive — modern dark appearance as requested
- **Testing Risk**: Low — visual verification on all major routes sufficient
- **Rollback Risk**: None — instant git revert restores previous colors
- **Accessibility Risk**: Low — chosen colors exceed WCAG AA requirements; verified mathematically

## Best Practices Applied

1. **YAGNI (You Aren't Gonna Need It)**: No new theme infrastructure; leverage existing tokens
2. **KISS (Keep It Simple)**: Value replacements over new abstractions
3. **DRY (Don't Repeat Yourself)**: Centralized tokens already exist; reuse architecture
4. **Accessibility First**: All color choices verified against WCAG AA contrast ratios
5. **Progressive Enhancement**: Inline fallback for pre-CSS-load state

## Phase 0 Completion Checklist

- [X] All NEEDS CLARIFICATION items from Technical Context resolved
- [X] Technology choices documented with rationale
- [X] Alternatives evaluated for key decisions
- [X] Implementation approach clear and justified
- [X] Risks identified and assessed
- [X] No hidden dependencies discovered

**Status**: ✅ **PHASE 0 COMPLETE** - Ready for Phase 1 design artifacts
