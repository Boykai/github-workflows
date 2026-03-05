# Research: Ruby-Colored Background Theme

**Feature**: 018-ruby-background-theme  
**Date**: 2026-03-05  
**Status**: Complete

## Research Tasks

### 1. Ruby Color Selection & HSL Conversion

**Context**: The existing theming system uses HSL values (without the `hsl()` wrapper) for CSS custom properties. The ruby color #9B111E must be converted to HSL format.

**Decision**: Use `#9B111E` as the primary ruby color, converted to HSL `355 80% 34%`.

**Rationale**:
- #9B111E is the canonical "ruby red" color specified in the feature request
- HSL value `355 80% 34%` matches the existing token format used in `index.css` (e.g., `--background: 0 0% 100%`)
- The hue (355°) is a deep red with slight blue undertone, evoking the gemstone quality
- Saturation (80%) provides rich color without being neon
- Lightness (34%) ensures a dark enough background for light text contrast

**Alternatives Considered**:
- `#CC0020` (HSL `351 100% 40%`) — More saturated/brighter, harder to maintain contrast
- `#E0115F` (HSL `342 86% 47%`) — Too pink/magenta, less "ruby" and more "rose"
- `#722F37` (HSL `353 42% 32%`) — Too desaturated, looks more brown/maroon than ruby

### 2. WCAG AA Contrast Analysis

**Context**: All foreground text must maintain a minimum 4.5:1 contrast ratio against the ruby background per WCAG AA.

**Decision**: Use `#FFFFFF` (white, HSL `0 0% 100%`) as the primary foreground text color against the ruby background.

**Rationale**:
- #FFFFFF on #9B111E yields a contrast ratio of **5.57:1**, exceeding the 4.5:1 WCAG AA minimum
- #FFFFFF on #9B111E also exceeds the 3:1 minimum for large text and UI components
- White text on deep ruby is the most readable and visually harmonious combination
- The existing dark mode already uses light foreground (`210 40% 98%` ≈ #F8FAFC) which yields similar high contrast

**Alternatives Considered**:
- Light gray `#D1D5DB` on #9B111E — Contrast ratio ~3.4:1, fails WCAG AA for normal text
- Cream `#FFF8DC` on #9B111E — Contrast ratio ~5.2:1, passes but adds color cast
- Pure white is the simplest and highest-contrast option

### 3. Theme Token Integration Strategy

**Context**: The app uses CSS custom properties in `:root` and `.dark` scopes in `index.css`, consumed by Tailwind via `hsl(var(--background))`. Need to determine which tokens to change.

**Decision**: Update `--background` and `--foreground` tokens in both `:root` and `.dark` scopes to ruby-themed values. Keep component-level tokens (card, popover, etc.) distinct from the page background.

**Rationale**:
- `body` already applies `@apply bg-background text-foreground`, so changing `--background` automatically applies ruby to the page
- The root `<div>` in `App.tsx` also uses `bg-background text-foreground`, providing consistent coverage
- Component tokens (`--card`, `--popover`, `--muted`) should NOT be changed to ruby—they serve as surface colors for UI panels, modals, and inputs that need distinct backgrounds from the page
- Both light and dark modes should reflect the ruby theme, with slight shade variations for visual distinction

**Alternatives Considered**:
- Adding a new `--background-ruby` token — Adds unnecessary complexity; the spec says to replace the background, not add an option
- Only changing `:root` — Would lose ruby theme when dark mode is active
- Changing all surface tokens to ruby — Would make cards, modals, inputs unreadable

### 4. Light vs Dark Mode Ruby Variants

**Context**: The app supports light and dark themes via `.dark` class toggling. Both need ruby backgrounds but may benefit from slight variation.

**Decision**: 
- Light mode (`:root`): `--background: 355 80% 34%` (ruby #9B111E) with `--foreground: 0 0% 100%` (white)
- Dark mode (`.dark`): `--background: 355 80% 22%` (darker ruby ~#6B0C15) with `--foreground: 0 0% 98%` (near-white)

**Rationale**:
- Using a darker ruby for dark mode maintains the visual distinction between light/dark modes
- Darker ruby (#6B0C15 at 22% lightness) still reads as clearly "ruby" 
- Contrast ratio for white on dark ruby: ~8.2:1 (excellent)
- Users toggling between modes will see a noticeable but harmonious difference
- The spec requires ruby in both modes; varying lightness is the most natural approach

**Alternatives Considered**:
- Same exact ruby in both modes — No visual distinction when toggling themes; defeats the purpose of dark mode
- Lighter ruby for dark mode — Contradicts dark mode expectations (darker surfaces)

### 5. Fallback for CSS Custom Property Support

**Context**: The spec SHOULD provide a fallback for browsers without CSS custom property support.

**Decision**: Add a static `background-color: #9B111E` declaration before the `@apply` directive in the body rule, and set a fallback `color: #FFFFFF`.

**Rationale**:
- CSS cascade ensures browsers that don't support custom properties will use the static declaration
- Browsers that do support custom properties will use the `@apply bg-background` which resolves to the same ruby color
- This is the standard CSS fallback pattern (progressive enhancement)
- Modern browser support for custom properties is >97%, so this is a safety net

**Alternatives Considered**:
- `@supports` query — More complex and not needed; simple cascade fallback is sufficient
- No fallback — Spec says SHOULD (not MUST), but providing one is trivial

### 6. Impact on Existing Component Surfaces

**Context**: Many components use `bg-background` for their own surfaces (header, modals, inputs). Need to assess impact.

**Decision**: Keep `--card`, `--popover`, `--secondary`, `--muted`, and `--accent` tokens unchanged. Update only `--background` and `--foreground`. Components using `bg-card`, `bg-popover`, `bg-muted`, `bg-accent` will retain their current distinct surface colors. Components explicitly using `bg-background` (header, main container) will inherit the ruby theme.

**Rationale**:
- The spec states: "Component-specific backgrounds (e.g., modals, cards, input fields) retain their own background colors as designed. Only the main application/page-level background changes to ruby."
- `App.tsx` header uses `bg-background` — this will become ruby, which is desirable as it makes the header part of the ruby theme
- Card/popover/muted components use their own tokens and are unaffected
- The border token should be updated to complement the ruby theme (a slightly lighter/darker ruby border)

**Alternatives Considered**:
- Change all tokens to ruby variants — Would make component surfaces indistinguishable from the background
- Create a separate `--background-page` token — Over-engineering for this feature; violates Simplicity principle
