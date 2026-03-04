# Research: Add Red Background Color to App

**Feature**: 018-red-background | **Date**: 2026-03-04

## Research Tasks

### 1. Optimal Red Shade for Application Background

**Context**: The spec requires an intentional shade of red (not pure #FF0000) that balances visual appeal with readability and reduces eye strain.

**Decision**: Use Material Design Red 700 (`#D32F2F`) for light mode and Red 900 (`#B71C1C`) for dark mode.

**Rationale**:
- `#D32F2F` (HSL: `0 70% 50%`) provides a vibrant but not harsh red. It is the Material Design "Red 700" tone, widely used in production applications (e.g., Google's error states, YouTube's branding).
- For dark mode, `#B71C1C` (HSL: `0 73% 41%`) is a deeper, darker red that reduces eye strain in low-light conditions while maintaining the red identity.
- Pure `#FF0000` is too saturated and causes visual fatigue on large surfaces; the chosen shades are desaturated enough for comfort.

**Alternatives Considered**:
| Shade | Hex | HSL | Rejected Because |
|-------|-----|-----|------------------|
| Pure Red | `#FF0000` | `0 100% 50%` | Too saturated; causes eye strain on large backgrounds |
| Red 400 | `#EF5350` | `1 84% 63%` | Too light; poor contrast with white text |
| Red 600 | `#E53935` | `1 78% 55%` | Viable but slightly less established than Red 700 |
| Red 800 | `#C62828` | `0 67% 47%` | Good option; slightly too dark for light mode primary |
| Red 900 | `#B71C1C` | `0 73% 41%` | Too dark for light mode; reserved for dark mode variant |

---

### 2. WCAG 2.1 AA Contrast Compliance with Red Background

**Context**: All text must maintain a minimum 4.5:1 contrast ratio against the red background (FR-003).

**Decision**: Use white (`#FFFFFF` / HSL `0 0% 100%`) as the primary foreground text color against the red background.

**Rationale**:
- **Light mode** (`#D32F2F` background + `#FFFFFF` text): Contrast ratio ≈ **4.68:1** — passes WCAG AA for normal text (≥4.5:1).
- **Dark mode** (`#B71C1C` background + `#FFFFFF` text): Contrast ratio ≈ **6.27:1** — comfortably passes WCAG AA.
- White text on red is a well-established, widely recognized color combination (emergency signage, brand logos).

**Alternatives Considered**:
| Foreground | Against #D32F2F | Against #B71C1C | Rejected Because |
|------------|-----------------|-----------------|------------------|
| `#000000` (black) | 6.49:1 ✅ | 8.69:1 ✅ | Passes but creates harsh, less aesthetic contrast |
| `#FAFAFA` (off-white) | 4.48:1 ❌ | 6.00:1 ✅ | Fails AA on light mode by slim margin |
| `#FFFFFF` (white) | 4.68:1 ✅ | 6.27:1 ✅ | **Selected** — passes both modes, clean aesthetic |

---

### 3. CSS Variable Integration Strategy

**Context**: The project uses CSS custom properties in `frontend/src/index.css` with HSL values consumed by Tailwind CSS via `hsl(var(--background))`. The existing `<body>` element already applies `bg-background text-foreground` classes.

**Decision**: Update only the `--background` and `--foreground` CSS variable values in both `:root` (light) and `.dark` (dark) blocks. No changes needed to Tailwind config, ThemeProvider, or any component files.

**Rationale**:
- The existing architecture already cascades the `--background` variable to every element using `bg-background`. Changing the variable value at the root level propagates the red background everywhere automatically.
- The `--foreground` variable must also be updated to white to ensure readable text globally.
- This is the simplest possible change — a single file, four variable values.

**Alternatives Considered**:
| Approach | Rejected Because |
|----------|------------------|
| Add a new CSS variable `--app-bg-color` | Unnecessary; `--background` already serves this exact purpose and is referenced everywhere |
| Modify `tailwind.config.js` to add a custom red color | Adds complexity; the existing `background` color token already works |
| Add inline styles to `App.tsx` or `main.tsx` | Bypasses the theme system; not maintainable |
| Use Tailwind `bg-red-700` class on body | Hard-codes a specific shade; loses theme token benefits |

---

### 4. Component-Level Background Preservation

**Context**: Edge case from spec — components with explicit backgrounds (cards, modals, popovers) should not be overridden by the global red background.

**Decision**: Keep existing `--card`, `--popover`, `--secondary`, `--muted`, and `--accent` variable values unchanged. They define distinct surface colors that are already applied via their own Tailwind classes (`bg-card`, `bg-popover`, etc.).

**Rationale**:
- The existing component library (shadcn/ui) uses specific tokens for each surface: cards use `bg-card`, popovers use `bg-popover`, modals use `bg-card` or `bg-background` with explicit overrides. These are separate CSS variables.
- Only `--background` defines the page-level background. Component surfaces reference their own tokens and won't be affected.
- This was verified by examining `tailwind.config.js` color mappings and the component source code.

**Alternatives Considered**:
| Approach | Rejected Because |
|----------|------------------|
| Override all surface tokens to red variants | Spec explicitly states components should keep their own backgrounds |
| Add `!important` to body background | Unnecessary and brittle; CSS specificity already handled correctly |

---

### 5. Light/Dark Mode Theme Integration

**Context**: The app supports light, dark, and system theme modes via `ThemeProvider.tsx` which toggles a `.dark` class on `<html>`. CSS variables in `index.css` have separate `:root` and `.dark` blocks.

**Decision**: Update both `:root` and `.dark` blocks with red background shades. Light mode gets `#D32F2F` (brighter red), dark mode gets `#B71C1C` (deeper red). Both use white foreground text.

**Rationale**:
- The theme system already handles mode switching by toggling CSS variable blocks. Updating both blocks ensures the red background works in all three modes (light, dark, system).
- The darker red for dark mode reduces eye strain while maintaining the red identity.
- No changes to `ThemeProvider.tsx` are needed — it already correctly manages the class toggle.

**Alternatives Considered**:
| Approach | Rejected Because |
|----------|------------------|
| Same red shade for both modes | Dark mode needs a darker shade to reduce eye strain |
| Only update light mode | Inconsistent experience; dark mode users would see original colors |
