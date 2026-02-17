# Research: Green Background for Tech Connect App

**Feature**: 003-green-background-app | **Date**: 2026-02-17
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

The primary research area is selecting WCAG 2.1 AA-compliant green shades for both light and dark mode. The application uses CSS custom properties for theming, so the implementation requires updating 4 variable values in a single file (`frontend/src/index.css`). No architectural research is needed.

## Decision Areas

### 1. Green Color Selection for Light Mode

**Decision**: Use `#E8F5E9` (mint green) for `--color-bg` and `#C8E6C9` (light green) for `--color-bg-secondary`

**Rationale**:
- `#E8F5E9` with app text color `#24292f`: **13.03:1** contrast ratio (exceeds WCAG AA 4.5:1 requirement by 2.9×)
- `#C8E6C9` with app text color `#24292f`: **10.90:1** contrast ratio (exceeds WCAG AA 4.5:1 requirement by 2.4×)
- These are clearly green (not white-passing) while being light enough for comfortable reading
- The two shades provide visual hierarchy (primary vs secondary backgrounds) consistent with the existing design pattern
- Both work well with the existing `--color-border` (#d0d7de), `--color-text-secondary` (#57606a), and all status colors

**WCAG Contrast Verification** (calculated using relative luminance formula per WCAG 2.1):
| Background | Text Color | Ratio | AA Normal (4.5:1) | AA Large (3:1) |
|-----------|-----------|-------|-------------------|----------------|
| #E8F5E9 (bg) | #24292f (text) | 13.03:1 | ✅ PASS | ✅ PASS |
| #E8F5E9 (bg) | #57606a (text-secondary) | 5.77:1 | ✅ PASS | ✅ PASS |
| #C8E6C9 (bg-secondary) | #24292f (text) | 10.90:1 | ✅ PASS | ✅ PASS |
| #C8E6C9 (bg-secondary) | #57606a (text-secondary) | 4.83:1 | ✅ PASS | ✅ PASS |

**Alternatives Considered**:
- **#00FF00 (bright green)**: Rejected — fails WCAG AA with white text (1.37:1). Causes eye strain. Spec explicitly notes this is not ideal.
- **#4CAF50 (Material green)**: Rejected — mid-tone green fails WCAG AA with both black (5.27:1 pass) and white (2.78:1 fail) text simultaneously, limiting UI flexibility.
- **#228B22 (forest green)**: Rejected — dark mid-tone fails contrast with both dark text (3.34:1 fail) and white text (4.39:1 fail for normal text).
- **#D4E6D4 (sage green)**: Viable alternative — 11.21:1 with dark text. Slightly less saturated green. Would also work but #E8F5E9 is more visually distinct as green.

---

### 2. Green Color Selection for Dark Mode

**Decision**: Use `#0D2818` for `--color-bg` and `#1A3A2A` for `--color-bg-secondary`

**Rationale**:
- `#0D2818` with dark mode text `#e6edf3`: **13.32:1** contrast ratio (exceeds WCAG AA by 2.96×)
- `#1A3A2A` with dark mode text `#e6edf3`: **10.56:1** contrast ratio (exceeds WCAG AA by 2.35×)
- These dark greens replace the current near-black (`#0d1117` / `#161b22`) with a green tint
- The visual difference is subtle but clearly green, maintaining the dark mode's purpose (reduced eye strain)
- Both work well with existing dark mode colors (`--color-border: #30363d`, `--color-text-secondary: #8b949e`)

**WCAG Contrast Verification**:
| Background | Text Color | Ratio | AA Normal (4.5:1) | AA Large (3:1) |
|-----------|-----------|-------|-------------------|----------------|
| #0D2818 (bg) | #e6edf3 (text) | 13.32:1 | ✅ PASS | ✅ PASS |
| #0D2818 (bg) | #8b949e (text-secondary) | 6.81:1 | ✅ PASS | ✅ PASS |
| #1A3A2A (bg-secondary) | #e6edf3 (text) | 10.56:1 | ✅ PASS | ✅ PASS |
| #1A3A2A (bg-secondary) | #8b949e (text-secondary) | 5.40:1 | ✅ PASS | ✅ PASS |

**Alternatives Considered**:
- **#006400 (CSS dark green)**: Rejected — too bright for dark mode, defeats purpose of reduced eye strain
- **#132B1C**: Viable alternative — 12.79:1 ratio. Nearly identical to #0D2818 but slightly warmer. Either would work.
- **#0F2D1A**: Viable alternative — 12.60:1 ratio. Slightly lighter than chosen option. Also acceptable.

---

### 3. Implementation Approach

**Decision**: Update CSS custom property values in `:root` and `html.dark-mode-active` selectors

**Rationale**:
- Application already uses CSS custom properties (`--color-bg`, `--color-bg-secondary`) for theming
- All components reference these variables (verified: `App.css` uses `var(--color-bg)` 6 times, `var(--color-bg-secondary)` 5 times)
- The `useAppTheme.ts` hook toggles dark mode via `dark-mode-active` CSS class on `<html>`
- Changing variable values propagates to all components automatically — no per-component updates needed
- This is the simplest possible approach: change 4 hex values in 1 file

**Alternatives Considered**:
- **New CSS variables (--color-bg-green)**: Rejected — YAGNI. Adding new variables when existing ones serve the same purpose adds unnecessary complexity.
- **Theme provider in React**: Rejected — app already uses CSS variables, not JS-based theming. Would require architectural change.
- **Separate green theme CSS file**: Rejected — adds file management complexity. Existing variable system is sufficient.
- **CSS-in-JS (styled-components, etc.)**: Rejected — app doesn't use CSS-in-JS. Would require new dependency and migration.

---

### 4. Component Impact Analysis

**Decision**: No component-level CSS changes required

**Rationale**:
- All component backgrounds use `var(--color-bg)` or `var(--color-bg-secondary)` — automatically updated
- Text colors use `var(--color-text)` and `var(--color-text-secondary)` — unchanged, contrast verified
- Login button (`background: var(--color-text)`, `color: white`) — unchanged, no impact
- Error toast/banner use hardcoded `#fff1f0` background — these are overlays with own backgrounds, unaffected by page background
- Status badges use `rgba()` overlays on their parent backgrounds — will harmonize with green
- Border colors (`--color-border`) remain unchanged — sufficient contrast with both green backgrounds

**Components Verified**:
| Component | Background Source | Impact |
|-----------|------------------|--------|
| `.app-header` | `var(--color-bg)` | ✅ Auto-updated to green |
| `.project-sidebar` | `var(--color-bg)` | ✅ Auto-updated to green |
| `.task-card` | `var(--color-bg)` | ✅ Auto-updated to green |
| `.chat-section` | `var(--color-bg)` | ✅ Auto-updated to green |
| `.status-column` | `var(--color-bg-secondary)` | ✅ Auto-updated to green |
| `.theme-toggle-btn` | `var(--color-bg-secondary)` | ✅ Auto-updated to green |
| `.logout-button` | `var(--color-bg-secondary)` | ✅ Auto-updated to green |
| `.project-select` | `var(--color-bg)` | ✅ Auto-updated to green |
| `body` | `var(--color-bg-secondary)` | ✅ Auto-updated to green |
| `.error-toast` | `#fff1f0` (hardcoded) | ✅ No change needed |
| `.error-banner` | `#fff1f0` (hardcoded) | ✅ No change needed |
| `.login-button` | `var(--color-text)` | ✅ No change needed |

---

### 5. Fallback Strategy

**Decision**: CSS custom properties with standard fallback syntax

**Rationale**:
- CSS custom properties are supported in all modern browsers (Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+)
- The application already relies on CSS custom properties without fallbacks — adding them just for green would be inconsistent
- If CSS variables fail to load, the browser's default white background appears — this satisfies FR-009 (neutral fallback)

**Alternatives Considered**:
- **Explicit fallback values**: `background: #E8F5E9; background: var(--color-bg);` — Rejected. Would add complexity for a scenario that doesn't occur in target browsers. The app already relies on CSS variables without fallbacks.
- **JavaScript fallback**: Rejected — overengineered for a CSS-only change.

---

### 6. Print Stylesheet

**Decision**: No print stylesheet changes needed

**Rationale**:
- Edge case from spec: "Print stylesheets may use white/neutral backgrounds to save ink"
- Application does not currently have print styles
- Adding print styles is out of scope per YAGNI principle
- Browsers typically ignore background colors in print by default unless user opts in

---

### 7. Transition Handling

**Decision**: No additional CSS transitions needed

**Rationale**:
- FR-005 requires no flicker during screen transitions
- The green background is set via CSS custom properties on `:root` and `body` — these are present from initial page load
- React SPA navigation doesn't cause full page reloads, so background persists automatically
- Theme toggle already has smooth transition because it only changes CSS variable values

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None — CSS variable value changes in a single file
- **User Impact**: Positive — adds green visual identity as requested
- **Accessibility Risk**: None — all contrast ratios verified above exceed WCAG AA minimums
- **Testing Risk**: Low — visual verification sufficient; existing tests unaffected
- **Rollback Risk**: None — instant git revert of 4 hex value changes

## Best Practices Applied

1. **YAGNI**: No new CSS variables, no new files, no new abstractions
2. **KISS**: Change 4 hex values in 1 file to achieve the entire feature
3. **WCAG 2.1 AA**: All contrast ratios mathematically verified (not estimated)
4. **Existing Patterns**: Using the app's established CSS custom property theming system
5. **Atomic Change**: Single file modification enables clean rollback

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved (none existed)
- [x] Technology choices documented with rationale
- [x] Alternatives evaluated for key decisions
- [x] WCAG contrast ratios calculated and verified
- [x] Implementation approach clear and justified
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered

**Status**: ✅ **PHASE 0 COMPLETE** - Ready for Phase 1 design artifacts
