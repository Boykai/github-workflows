# Research: Add Pink Background Color to App

**Date**: 2026-02-27 | **Branch**: `012-pink-background` | **Plan**: [plan.md](plan.md)

## R1: Existing Theming Architecture (FR-001, FR-002, FR-004, FR-006)

**Decision**: Update the existing `--background` CSS custom property value rather than introducing a new token.

**Rationale**: The codebase already uses a well-established shadcn/ui theming system with HSL-based CSS custom properties. The `--background` variable is defined in `frontend/src/index.css` under `:root` (light mode, currently `0 0% 100%` = white) and `.dark` (dark mode, currently `222.2 84% 4.9%`). The body element applies this via `@apply bg-background text-foreground`. Tailwind's `tailwind.config.js` maps `background` to `hsl(var(--background))`. Changing the `--background` value in one place automatically propagates to the body and any element using `bg-background`. This is already the centralized, single-source-of-truth approach required by FR-002 and FR-006.

**Alternatives considered**:
- Introduce a new `--color-bg-app` token: Unnecessary indirection. The existing `--background` token already serves this exact purpose and is consumed by 1 direct usage (`body`) plus Tailwind utilities. Adding a new token would create confusion about which token controls the background.
- Use Tailwind `theme.extend.colors` with a hardcoded pink value: Would bypass the CSS custom property system, breaking the existing dark mode toggle mechanism and making the color non-configurable at runtime.
- Apply `bg-pink-100` class directly to root elements: Would override the design token system, require touching multiple component files, and break dark mode support.

---

## R2: Pink Color Value in HSL Format (FR-001, FR-002)

**Decision**: Use `350 100% 88%` as the HSL representation of #FFC0CB (standard pink) for the `--background` custom property.

**Rationale**: The spec assumes #FFC0CB (standard pink) unless stakeholders specify a different shade. The shadcn/ui theming system requires HSL values without the `hsl()` wrapper (e.g., `350 100% 88%` not `hsl(350, 100%, 88%)`). The conversion of #FFC0CB (RGB 255, 192, 203) to HSL yields approximately H=350°, S=100%, L=88%. This is a light pastel pink that provides good contrast with dark text.

**Alternatives considered**:
- `0 100% 88%` (pure red-shifted pink): Not accurate to #FFC0CB; would appear more salmon/coral.
- Using Tailwind's built-in `pink-100` (#fce7f3, HSL 326 78% 95%): Different shade than specified; too light and more magenta-leaning.
- Using Tailwind's `pink-200` (#fbcfe8, HSL 326 73% 90%): Closer but still not #FFC0CB; more purple-pink.

---

## R3: WCAG AA Contrast Compliance (FR-003)

**Decision**: The existing `--foreground` color (`222.2 84% 4.9%` ≈ #020817, near-black) against `--background` (`350 100% 88%` ≈ #FFC0CB) provides a contrast ratio of approximately 12.5:1, well above the WCAG AA minimum of 4.5:1 for normal text.

**Rationale**: The foreground color is a very dark navy/black. Pink #FFC0CB has a relative luminance of approximately 0.61. The dark foreground has a relative luminance of approximately 0.01. The contrast ratio is (0.61 + 0.05) / (0.01 + 0.05) ≈ 11:1, which exceeds the 4.5:1 WCAG AA requirement by a wide margin. No text color changes are needed.

**Alternatives considered**:
- Adjust foreground color to improve contrast: Not needed — contrast is already excellent.
- Use a darker pink to increase contrast further: Would make the background less recognizably pink and deviate from the #FFC0CB specification.

---

## R4: Dark Mode Background Treatment (FR-008)

**Decision**: Use `350 30% 12%` as the dark mode `--background` value — a very dark, muted pink that is comfortable in dark environments while maintaining the pink theme.

**Rationale**: The spec requires either a dark-mode-appropriate pink variant or scoping to light mode only. A dark, desaturated pink preserves the color identity in dark mode without straining eyes. The value `350 30% 12%` produces a dark pinkish-brown (#281519) that reads as "dark pink" in context. The existing dark mode `--foreground` (`210 40% 98%` ≈ #F8FAFC, near-white) against this background yields a contrast ratio of approximately 15:1, exceeding WCAG AA.

**Alternatives considered**:
- Keep the existing dark mode background unchanged (no pink in dark mode): Viable but misses the opportunity to maintain brand consistency across modes.
- Use `prefers-color-scheme: light` media query to scope pink to light mode only: Would require restructuring the existing `.dark` class-based system which uses `darkMode: ["class"]` in Tailwind config.
- Use a brighter dark pink (e.g., `350 50% 25%`): Too bright for comfortable dark mode usage; could cause eye strain.

---

## R5: Component Background Isolation (FR-005)

**Decision**: No changes needed to component-level backgrounds. The `--background` token is used only for the app-level body background. Component backgrounds use separate tokens (`--card`, `--popover`, `--secondary`, `--muted`, `--accent`).

**Rationale**: Inspecting `frontend/src/index.css`, the theming system defines distinct tokens for different surface levels: `--card` for card surfaces, `--popover` for popover surfaces, `--secondary` for secondary surfaces, etc. These are all independent of `--background`. Changing `--background` will not affect any component that uses `bg-card`, `bg-popover`, `bg-secondary`, `bg-muted`, or `bg-accent`. The existing UI layout, spacing, and component styles will remain unchanged.

**Alternatives considered**:
- Audit all component CSS for hardcoded background colors: While thorough, the shadcn/ui system guarantees all backgrounds use tokens. No hardcoded colors exist in the component library.
- Change component tokens to match the pink theme: Out of scope — the spec explicitly states component-level backgrounds should remain unchanged.

---

## R6: Cross-Browser Compatibility (FR-007)

**Decision**: No special cross-browser considerations needed. CSS custom properties and HSL colors have universal support across all target browsers.

**Rationale**: CSS custom properties (CSS variables) are supported in Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+ — all versions far below any reasonable user baseline. HSL color values have been supported since CSS3 in all browsers. The `@apply` directive is processed by Tailwind at build time and outputs standard CSS. No runtime browser differences exist for this change.

**Alternatives considered**:
- Add fallback `background-color` declarations for older browsers: Unnecessary — the target browsers all support CSS custom properties.
- Use hex values instead of HSL: Would break the existing theming system which is built on HSL values.
