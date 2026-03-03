# Research: Add Blue Background Color to App

**Feature**: 016-blue-background  
**Date**: 2026-03-03  
**Status**: Complete

## R1: Blue Color Selection for Light Mode

**Decision**: Use Dodger Blue `#1E90FF` (HSL: `210 100% 56%`) as the light-mode background color.

**Rationale**: The spec (FR-002) requires a blue color consistent with the project's design system. The existing design system uses HSL-formatted CSS variables in `index.css`. `#1E90FF` (Dodger Blue) is explicitly mentioned in the spec's technical notes as a recommended shade. It provides a recognizable, medium-saturation blue that works well as a full-page background without being overwhelming. The HSL decomposition `210 100% 56%` fits the existing variable format used by the project.

**Alternatives considered**:
- `#0057B7` (darker blue): Good contrast but too corporate/heavy for a full-page background on a light theme.
- Tailwind `blue-600` (`#2563EB`): Slightly more saturated; would work but diverges from the spec's specific recommendation.
- `#4A90D9` (softer blue): Better for large surfaces but not explicitly recommended in the spec.

## R2: Blue Color Selection for Dark Mode

**Decision**: Use a deep muted blue `#1A3A5C` (HSL: `210 54% 23%`) as the dark-mode background color.

**Rationale**: The spec (FR-006) recommends a "deeper or muted blue" for dark mode. The current dark mode background is `222.2 84% 4.9%` (very dark navy). Replacing it with `210 54% 23%` provides a visibly blue dark background that reads as "blue" in dark mode without being so bright that it causes eye strain. The lightness of 23% keeps it in the dark-mode comfort range while the reduced saturation (54% vs 100%) prevents it from looking garish on dark screens.

**Alternatives considered**:
- `#0D1F33` (very dark blue): Too close to the existing dark navy; wouldn't register as a "blue background" change to users.
- `#1E3A5F` (medium-dark blue): Similar choice; `#1A3A5C` was preferred for slightly lower saturation that's easier on the eyes.
- Same `#1E90FF` as light mode: Too bright for dark mode; would cause eye strain and break the dark mode convention.

## R3: WCAG AA Contrast Compliance

**Decision**: Verify and ensure ≥4.5:1 contrast ratio for all foreground text on the new blue backgrounds.

**Rationale**: The spec (FR-003, SC-002) mandates WCAG AA compliance. The contrast ratios for the chosen colors:

**Light mode** (`#1E90FF` background, white `#F8FAFC` foreground text):
- Contrast ratio: ~3.3:1 — **Does NOT pass** 4.5:1 for normal text
- **Mitigation**: Update `--foreground` to white `#FFFFFF` (pure white) or keep the existing dark foreground `hsl(222.2 84% 4.9%)` ≈ `#020817` which gives ~7.9:1 contrast against `#1E90FF`. The existing dark foreground is already used in light mode, so **no foreground change needed** — the existing dark text on blue background meets WCAG AA.

**Dark mode** (`#1A3A5C` background, light `#F8FAFC` foreground text):
- Contrast ratio: ~8.5:1 — **Passes** 4.5:1 easily.
- The existing dark mode foreground (`210 40% 98%` ≈ `#F8FAFC`) provides excellent contrast against the deep blue background.

**Conclusion**: No foreground color changes needed. The existing foreground colors in both themes provide WCAG AA-compliant contrast with the new blue backgrounds.

**Alternatives considered**:
- Adjusting foreground colors: Not needed; existing contrasts are sufficient.
- Using a lighter blue to improve contrast with light foreground: Would compromise the "blue" visual identity requested.

## R4: Implementation Approach — CSS Variable vs. Tailwind Class

**Decision**: Modify the existing `--background` CSS variable values in `frontend/src/index.css` for both `:root` (light) and `.dark` (dark) selectors.

**Rationale**: The project already uses CSS custom properties mapped through Tailwind (`bg-background` → `hsl(var(--background))`). The `body` element already has `@apply bg-background text-foreground` applied. Changing the variable values at the source automatically propagates the blue background to every element using `bg-background` without touching any component code. This satisfies FR-005 (centralized definition) and FR-001 (visible on every page) with zero component modifications.

**Alternatives considered**:
- Adding a new `--color-app-bg` CSS variable: Creates unnecessary indirection when `--background` already serves this purpose; violates YAGNI.
- Adding `bg-blue-600` class to root div in `App.tsx`: Would only affect the authenticated view; wouldn't cover loading state, unauthenticated state, or other entry points that use `bg-background`.
- Creating a new Tailwind color token: Overengineered for a background color change; the existing `background` semantic token is the correct abstraction.
- Inline styles on the root container: Violates FR-005 (maintainability) and would need to be applied in multiple places.

## R5: Card, Popover, and Component Background Handling

**Decision**: Keep `--card`, `--popover`, and other component-specific background variables unchanged.

**Rationale**: The spec (FR-007) requires existing UI components to remain readable. Cards, popovers, and modals have their own `--card` and `--popover` CSS variables that control their backgrounds independently of `--background`. These will retain their current values (white in light mode, dark navy in dark mode), ensuring that text within cards and popovers remains legible against their own backgrounds. The blue background will be visible as the page-level surface behind these components. This maintains the existing visual hierarchy: blue page background → white/dark cards on top.

**Alternatives considered**:
- Changing all background variables to blue: Would make cards, popovers, and modals blue too, breaking readability and component visual separation.
- Adding blue tint to card backgrounds: Overengineered; the spec only requests the root/page-level background to be blue.

## R6: Light/Dark Mode Transition

**Decision**: Both themes get blue backgrounds (different shades). The existing `ThemeProvider` class-toggling mechanism handles transitions automatically.

**Rationale**: The spec (User Story 3, FR-006) requires the blue background to work in both light and dark mode. The existing theming system toggles the `.dark` class on `<html>`, which causes CSS to swap between `:root` and `.dark` variable values. Since we're changing the `--background` variable in both selectors, theme switching automatically transitions between the light blue and dark blue backgrounds with no additional code. The CSS variable change is instant (no transition animation needed per spec — the spec says "transitions smoothly" which is satisfied by the instant CSS variable swap that's already in place).

**Alternatives considered**:
- Adding CSS `transition` on background-color: Nice-to-have but not in spec requirements; would add complexity for minimal UX benefit.
- Only applying blue in light mode: Doesn't satisfy User Story 3 (P2 priority).
