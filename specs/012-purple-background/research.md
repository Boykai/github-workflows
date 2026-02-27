# Research: Add Purple Background Color to Application

**Date**: 2026-02-27 | **Branch**: `012-purple-background` | **Plan**: [plan.md](plan.md)

## R1: Purple HSL Value Selection for Light Mode (FR-001, FR-002, FR-004)

**Decision**: Use `270 50% 40%` (equivalent to `hsl(270, 50%, 40%)` → approximately `#663399`, known as "Rebeccapurple") as the light-mode `--background` value.

**Rationale**: This shade of purple is a well-known web color (CSS named color `rebeccapurple`), has strong recognition, and provides a rich purple appearance. At HSL `270 50% 40%`, the color has sufficient depth to read as distinctly purple while being dark enough to provide excellent contrast with light-colored text. The contrast ratio of white text (`#FFFFFF` / `210 40% 98%`) against this background exceeds 7:1, far surpassing the WCAG AA minimum of 4.5:1. The existing `--foreground` value in `:root` is `222.2 84% 4.9%` (near-black), which also passes at >10:1 contrast. However, since the background is now dark in light mode, the `--foreground` must be updated to a light color for readability.

**Alternatives considered**:
- `hsl(270, 100%, 80%)` (light pastel purple): Too light — would have poor contrast with light text and look washed out. Would require dark foreground text, but secondary tokens (cards, popovers) also use the same `--background` value, creating a confusing all-pastel UI.
- `hsl(280, 60%, 50%)` (vivid purple): Overly saturated — can cause eye strain on large surfaces. Medium lightness makes contrast borderline with both light and dark text.
- Tailwind `purple-600` (`hsl(271, 91%, 65%)`): Good option but very high saturation for a full-page background surface. Slightly too bright for extended viewing.

**Implementation approach**:
- In `frontend/src/index.css`, update `:root { --background: 270 50% 40%; }`.
- Update `:root { --foreground: 210 40% 98%; }` to ensure light text on dark purple background.

---

## R2: Purple HSL Value Selection for Dark Mode (FR-007)

**Decision**: Use `270 50% 20%` as the dark-mode `--background` value.

**Rationale**: Dark mode should use a deeper, less luminous variant of the same purple hue. At lightness 20% (compared to 40% in light mode), the color remains recognizably purple but is dark enough for comfortable dark-mode viewing. The existing dark-mode `--foreground` value of `210 40% 98%` (near-white) achieves a contrast ratio exceeding 10:1 against this background. Using the same hue (270°) and saturation (50%) ensures visual continuity between modes — only the lightness changes.

**Alternatives considered**:
- `hsl(270, 50%, 10%)`: Too dark — barely distinguishable from pure black, losing the purple identity.
- `hsl(270, 30%, 15%)`: Desaturated — reads as dark gray rather than purple. Doesn't fulfill the "purple background" requirement.
- Same value as light mode (`270 50% 40%`): Too bright for dark mode, causes eye strain in low-light environments.

**Implementation approach**:
- In `frontend/src/index.css`, update `.dark { --background: 270 50% 20%; }`.

---

## R3: Foreground and Secondary Token Adjustments (FR-002, FR-005, FR-008)

**Decision**: Update `--foreground` and review `--card`, `--popover`, `--secondary`, `--muted`, and `--border` tokens to ensure contrast and visual coherence with the new purple background.

**Rationale**: The current light-mode `--foreground` is near-black (`222.2 84% 4.9%`), which was designed for a white background. With a dark purple background, near-black text would be illegible. The foreground must be switched to a light color. Similarly, `--card` and `--popover` currently match `--background` (white in light mode, dark blue in dark mode). These should be updated to complement the purple background — either matching it or providing intentional contrast.

**Alternatives considered**:
- Only change `--background` and leave all other tokens: Would break text readability (dark text on dark background) and create visual inconsistencies with cards/popovers.
- Introduce a new `--color-bg-app` token: Adds unnecessary complexity. The existing `--background` token is the standard shadcn/ui approach and is already consumed by `bg-background` across all components. Changing it at the source is the simplest approach.

**Implementation approach**:
- Light mode (`:root`):
  - `--background: 270 50% 40%` (purple)
  - `--foreground: 210 40% 98%` (near-white for readable text)
  - `--card: 270 50% 45%` (slightly lighter purple for card surfaces)
  - `--card-foreground: 210 40% 98%` (light text on purple cards)
  - `--popover: 270 50% 45%` (match card)
  - `--popover-foreground: 210 40% 98%`
  - `--primary: 210 40% 98%` (light primary buttons on purple)
  - `--primary-foreground: 270 50% 40%` (purple text on light buttons)
  - `--secondary: 270 40% 50%` (lighter purple for secondary surfaces)
  - `--secondary-foreground: 210 40% 98%`
  - `--muted: 270 30% 50%` (desaturated purple for muted areas)
  - `--muted-foreground: 270 20% 80%` (light muted text)
  - `--accent: 270 40% 50%` (purple accent)
  - `--accent-foreground: 210 40% 98%`
  - `--destructive: 0 84.2% 60.2%` (keep red for destructive actions)
  - `--destructive-foreground: 210 40% 98%`
  - `--border: 270 30% 55%` (visible border on purple)
  - `--input: 270 30% 55%` (match border for inputs)
  - `--ring: 210 40% 98%` (light ring for focus states)
- Dark mode (`.dark`):
  - `--background: 270 50% 20%` (deep purple)
  - `--foreground: 210 40% 98%` (near-white, unchanged)
  - `--card: 270 50% 25%` (slightly lighter purple)
  - `--card-foreground: 210 40% 98%`
  - `--popover: 270 50% 25%`
  - `--popover-foreground: 210 40% 98%`
  - `--primary: 210 40% 98%`
  - `--primary-foreground: 270 50% 20%`
  - `--secondary: 270 40% 30%`
  - `--secondary-foreground: 210 40% 98%`
  - `--muted: 270 30% 30%`
  - `--muted-foreground: 270 20% 70%`
  - `--accent: 270 40% 30%`
  - `--accent-foreground: 210 40% 98%`
  - `--destructive: 0 62.8% 30.6%` (keep existing dark-mode destructive)
  - `--destructive-foreground: 210 40% 98%`
  - `--border: 270 30% 35%`
  - `--input: 270 30% 35%`
  - `--ring: 270 30% 70%`

---

## R4: Cross-Browser Compatibility (FR-006)

**Decision**: Use standard HSL notation for CSS custom properties, which is universally supported across all modern browsers.

**Rationale**: The existing codebase already uses HSL values in CSS custom properties (e.g., `--background: 0 0% 100%`) consumed via Tailwind's `hsl(var(--background))` wrapper. This pattern is supported in Chrome 49+, Firefox 31+, Safari 9.1+, and Edge 15+. Since the change only modifies the numeric HSL values (not the format or consumption pattern), cross-browser compatibility is inherently maintained.

**Alternatives considered**:
- Switch to hex values: Would require changing Tailwind config's `hsl()` wrapper to `var()` direct — unnecessary and breaking change.
- Add vendor prefixes: Not needed — CSS custom properties and HSL colors don't require prefixes in any modern browser.
- Add fallback values: Unnecessary — all target browsers (latest Chrome, Firefox, Safari, Edge) support CSS custom properties.

**Implementation approach**:
- No special cross-browser handling needed. Use the same HSL format already in use throughout `index.css`.

---

## R5: Impact on Existing Components (FR-005, FR-008)

**Decision**: Audit all components using `bg-background` and other token-based classes to verify they remain visually coherent with the purple background.

**Rationale**: The `bg-background` class (mapped to `--background`) is used on `body` (via `index.css`), the main app container in `App.tsx`, the header, and various component surfaces. Changing `--background` affects all of these simultaneously. Components using `bg-card`, `bg-popover`, `bg-secondary` etc. will be updated to purple-family variants (see R3), ensuring visual harmony. Components using `bg-primary` for buttons will switch to light-on-purple, maintaining interaction clarity.

**Alternatives considered**:
- Change only the body background while keeping component tokens unchanged: Would create a visual disconnect — purple body with white cards and popovers. Incoherent design.
- Introduce a separate `--body-background` token: Adds complexity without benefit. The shadcn/ui system is designed for `--background` to serve as the base surface color.

**Implementation approach**:
- After updating all tokens in `index.css`, visually inspect each page and component type.
- Key components to verify: header, buttons (all variants), cards, modals/popovers, inputs, sidebar, board columns, chat interface.
- Confirm no component becomes illegible or loses visual boundaries.
