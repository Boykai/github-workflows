# Research: Add Green Background Color to App

**Feature**: 007-green-background | **Date**: 2026-02-20
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature is a straightforward CSS change with minimal technical unknowns. The primary research areas are green shade selection (WCAG AA compliance) and the CSS implementation approach within the existing custom property system. All unknowns were resolved through codebase inspection and contrast ratio analysis.

## Decision Areas

### 1. Green Shade Selection

**Decision**: Use `#2D6A4F` (dark forest green) as the primary green background color

**Rationale**:
- **WCAG AA compliance**: `#2D6A4F` against `#24292f` (light mode text) yields a contrast ratio of approximately 2.2:1 for the body background; however, existing UI components (header, sidebar, cards, board columns) all render their own opaque backgrounds (`var(--color-bg)` = `#ffffff` or `var(--color-bg-secondary)` = `#f6f8fa`), so primary text is never rendered directly on the green body background
- The green body background is visible in gaps, edges, and as the base layer behind overlays — areas where no text is rendered directly
- `#2D6A4F` is a mid-range green that complements the existing neutral UI palette without clashing
- Dark mode: `#2D6A4F` works well against the dark mode palette (`--color-bg: #0d1117`, `--color-bg-secondary: #161b22`) as a distinct but non-jarring accent

**Alternatives Considered**:
| Alternative | Why Rejected |
|---|---|
| `#4CAF50` (Material Green) | Too bright/saturated; clashes with the subdued GitHub-style UI palette |
| `#1B4332` (Very dark green) | Too dark; barely distinguishable from dark mode backgrounds |
| `#52B788` (Light green) | Too light; poor contrast with light mode component backgrounds, looks washed out |
| `#388E3C` (Medium green) | Acceptable but more saturated than necessary; `#2D6A4F` is more neutral/professional |

---

### 2. CSS Implementation Approach

**Decision**: Define a `--color-bg-primary` CSS custom property in `:root` and apply it to the `body` element background

**Rationale**:
- The existing codebase already uses CSS custom properties extensively (`:root` block in `index.css` with `--color-bg`, `--color-bg-secondary`, etc.)
- Adding `--color-bg-primary` follows the established naming convention
- Applying to `body` ensures the green is the base layer across all pages/routes
- Existing components already have explicit backgrounds that layer on top (verified: `app-header`, `app-container`, `board-page`, `chat-section`, `task-card`, `modal-content`, etc.)
- Hardcoded fallback before the `var()` declaration provides graceful degradation

**Alternatives Considered**:
| Alternative | Why Rejected |
|---|---|
| Tailwind utility class | Project does not use Tailwind CSS; would require adding a new dependency |
| Inline style on `#root` div | Bypasses CSS custom property system; not maintainable; no fallback mechanism |
| CSS-in-JS / styled-components | Project uses plain CSS files; introducing a new styling paradigm is overkill |
| Separate `green-theme.css` file | Unnecessary file for a single property; violates simplicity principle |

---

### 3. Dark Mode Handling

**Decision**: Use the same green value (`#2D6A4F`) for both light and dark modes

**Rationale**:
- Spec Assumption 6 explicitly states: "No dark mode–specific green variant is required for this initial change; the same green applies in all contexts"
- `#2D6A4F` works visually in both modes — it's mid-range enough to be distinct against both white and dark backgrounds
- Adding the variable to both `:root` and `html.dark-mode-active` ensures it's available in both contexts, even if the value is the same (future-proofing for easy per-mode adjustment)

**Alternatives Considered**:
| Alternative | Why Rejected |
|---|---|
| Lighter green for dark mode | Out of scope per spec assumption 6 |
| Only define in `:root` | Would work but adding to dark mode block future-proofs for theme-specific adjustments |

---

### 4. Fallback Strategy

**Decision**: Use a hardcoded `background` declaration before the `var()` declaration for graceful degradation

**Rationale**:
- CSS custom properties (custom properties) are supported in all modern browsers (Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+)
- For the rare case of unsupported browsers, a preceding `background: #2D6A4F;` ensures the green is still applied
- This is the standard CSS fallback pattern and requires zero JavaScript

**Implementation Pattern**:
```css
body {
  background: #2D6A4F;
  background: var(--color-bg-primary);
}
```

**Alternatives Considered**:
| Alternative | Why Rejected |
|---|---|
| `@supports` query | More complex; overkill for a simple color fallback |
| JavaScript feature detection | Unnecessary complexity for CSS-only change |
| No fallback | Spec FR-007 requires graceful degradation |

---

### 5. Testing Strategy

**Decision**: Manual visual verification only; no new automated tests

**Rationale**:
- Feature is a visual CSS change with no programmatic logic
- Constitution Principle IV (Test Optionality): Tests are optional by default
- Spec acceptance criteria are human-verifiable (open app, observe green background)
- Existing E2E tests do not assert background colors

**Alternatives Considered**:
| Alternative | Why Rejected |
|---|---|
| Visual regression tests | Overkill for single CSS property change; no existing visual testing infrastructure |
| Unit tests for CSS variable | CSS custom properties are not testable via Vitest unit tests |
| E2E screenshot comparison | Would require baseline screenshots and comparison infrastructure |

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None — single CSS property change in established file
- **User Impact**: Positive — adds visual branding as requested
- **Contrast Risk**: Low — green is base layer; text renders on component backgrounds with sufficient contrast
- **Rollback Risk**: None — instant git revert restores previous background

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved
- [x] Green shade selected with contrast analysis
- [x] CSS implementation approach documented
- [x] Dark mode handling clarified
- [x] Fallback strategy defined
- [x] Testing approach documented
- [x] Risks identified and assessed

**Status**: ✅ **PHASE 0 COMPLETE** — Ready for Phase 1 design artifacts
