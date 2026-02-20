# Research: Apply Tan Background Color to App

**Feature**: 001-tan-background  
**Date**: 2026-02-20  
**Status**: Complete

## R1: Tan Color Selection

**Task**: Determine the correct tan hex value for the global background.

**Decision**: Use `#D2B48C` (CSS named color "tan") as the default light-mode background.

**Rationale**: #D2B48C is the standard CSS named color "tan" and matches the issue request. It provides a warm, inviting aesthetic while maintaining sufficient contrast with the existing primary text color (#24292f). The spec allows for project-owner override but establishes #D2B48C as the reasonable default.

**Alternatives considered**:
- `#C9A97A` — Slightly darker/warmer gold-tan. Passes contrast but departs from standard "tan" naming.
- `#E8D5B7` — Lighter beige-tan. Lower contrast with text (closer to WCAG threshold), less visually distinct.
- `#DEB887` — CSS "burlywood". Similar warmth but less commonly identified as "tan".

## R2: WCAG AA Contrast Analysis

**Task**: Verify that the chosen tan background meets WCAG AA contrast requirements with existing text colors.

**Decision**: #D2B48C passes WCAG AA for primary text but requires secondary text darkening.

**Rationale**: Computed contrast ratios against current CSS variables:

| Background | Foreground | Contrast | WCAG AA (4.5:1) |
|-----------|-----------|---------|-----------------|
| #D2B48C | #24292f (`--color-text`) | 7.43:1 | ✅ Pass |
| #D2B48C | #57606a (`--color-text-secondary`) | 3.24:1 | ❌ Fail |

The primary text color passes comfortably. The secondary text color (#57606a) fails and must be darkened to approximately #3D4451 or similar (luminance ≤ 0.068) to achieve ≥ 4.5:1 contrast on the tan background.

**Note**: Secondary text may also appear on component surfaces (cards, modals) that use `--color-bg: #ffffff`. A darkened secondary text (#3D4451) against white yields ~10.2:1 contrast, which is safe.

**Alternatives considered**:
- Lighten the tan to reduce contrast gap — rejected because it weakens the visual tan identity.
- Only darken text on tan surfaces via scoped CSS — rejected as overly complex; a single darker secondary text works on both white and tan.

## R3: Dark Mode Tan Equivalent

**Task**: Determine an appropriate dark-mode equivalent of the tan background.

**Decision**: Use `#2C1E12` as the dark-mode tan background.

**Rationale**: #2C1E12 is a dark warm brown that preserves the tan color family's warmth. Contrast analysis:

| Background | Foreground | Contrast | WCAG AA (4.5:1) |
|-----------|-----------|---------|-----------------|
| #2C1E12 | #e6edf3 (`--color-text` dark) | 13.65:1 | ✅ Pass |
| #2C1E12 | #8b949e (`--color-text-secondary` dark) | 5.25:1 | ✅ Pass |

Both dark-mode text colors pass WCAG AA against #2C1E12.

**Alternatives considered**:
- `#3B2A1A` — Slightly lighter dark-tan. Primary text passes (11.6:1) but secondary text fails (4.46:1).
- `#4A3728` — Too light for dark mode. Secondary text fails (3.65:1).
- Keep `#0d1117` (current dark bg) — Breaks dark-mode tan consistency; loses warm aesthetic.

## R4: CSS Architecture Approach

**Task**: Determine how to apply the tan background in the existing CSS architecture.

**Decision**: Update CSS custom properties in `frontend/src/index.css` `:root` and `html.dark-mode-active` selectors.

**Rationale**: The project uses CSS custom properties (not Tailwind CSS, not CSS-in-JS). The body element uses `var(--color-bg-secondary)` as its background. The cleanest change is to:
1. Update `--color-bg-secondary` to `#D2B48C` in `:root` (light mode)
2. Update `--color-bg-secondary` to `#2C1E12` in `html.dark-mode-active` (dark mode)
3. Darken `--color-text-secondary` to pass WCAG AA on the new background

This approach uses the existing design token system, requires no new tokens, and ensures all pages inherit the change through the existing `body { background: var(--color-bg-secondary) }` rule.

**Alternatives considered**:
- Add a new `--color-bg-tan` variable — rejected per Simplicity/DRY (YAGNI); an extra variable adds complexity with no benefit since `--color-bg-secondary` already serves as the body background token.
- Apply `background-color: #D2B48C` directly to `body` — rejected as a one-off override; violates FR-002 (must be a reusable design token).

## R5: Component Impact Assessment

**Task**: Identify components that may need surface-level background adjustments.

**Decision**: Components using `--color-bg` (#ffffff light / #0d1117 dark) for surface backgrounds will maintain visual distinction against the tan body background. No additional component overrides are expected.

**Rationale**: The current architecture separates body background (`--color-bg-secondary`) from component surface background (`--color-bg`). Cards, modals, and sidebars typically use `--color-bg` (white in light mode), which has clear visual separation from #D2B48C tan. A visual review during implementation should confirm this.

**Alternatives considered**:
- Pre-emptively adjust all component backgrounds — rejected as premature; components already use `--color-bg` which is visually distinct from tan.
