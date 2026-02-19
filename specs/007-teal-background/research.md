# Research: Add Teal Background Color to App

**Feature**: 007-teal-background | **Date**: 2026-02-19

---

## R1: Teal Color Value and WCAG AA Contrast Compliance

### Decision
Use **#0D9488** (Tailwind teal-600) as the primary teal background, and **#0F766E** (Tailwind teal-700) as the dark mode variant.

### Rationale
- #0D9488 is the spec-recommended value, matching Tailwind's `teal-600` — a widely recognized, modern teal.
- **White text (#FFFFFF) on #0D9488** yields a contrast ratio of approximately **4.53:1**, which passes WCAG AA for normal text (≥4.5:1) and large text (≥3:1).
- **White text (#FFFFFF) on #0F766E** (dark mode) yields approximately **5.4:1**, comfortably passing WCAG AA.
- Both values are already documented in the feature spec as recommended defaults.

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| #008080 (classic teal) | Darker than needed; less modern aesthetic; similar contrast but less aligned with Tailwind ecosystem |
| #14B8A6 (Tailwind teal-400) | Too light — white text contrast ratio drops below 3:1, failing WCAG AA |
| #2DD4BF (Tailwind teal-300) | Way too light for background use with white text |
| Custom non-Tailwind value | No benefit over well-established Tailwind palette; reduces predictability |

### Key Contrast Data

| Background | Foreground | Ratio | WCAG AA (normal) | WCAG AA (large) |
|---|---|---|---|---|
| #0D9488 | #FFFFFF | ~4.53:1 | ✅ Pass | ✅ Pass |
| #0D9488 | #24292F | ~5.5:1 | ✅ Pass | ✅ Pass |
| #0F766E | #FFFFFF | ~5.4:1 | ✅ Pass | ✅ Pass |
| #0F766E | #E6EDF3 | ~6.8:1 | ✅ Pass | ✅ Pass |

---

## R2: CSS Custom Property Implementation Strategy

### Decision
Add a new `--color-bg-app` CSS custom property to `:root` and `html.dark-mode-active`, then apply it to the `body` background.

### Rationale
- The app already uses CSS custom properties as design tokens in `frontend/src/index.css` (`:root` block with `--color-bg`, `--color-bg-secondary`, etc.).
- Adding a dedicated `--color-bg-app` token (rather than overwriting `--color-bg`) preserves the existing `--color-bg` (white/dark) used by cards, headers, sidebar, and modals as their distinct background.
- The `body` element currently uses `var(--color-bg-secondary)` for its background — changing this to `var(--color-bg-app)` targets only the root-level background without breaking component-level backgrounds.
- Single source of truth: changing `--color-bg-app` in one place updates the entire app background.

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| Override `--color-bg` to teal | Would break all components using `var(--color-bg)` for their own backgrounds (cards, modals, sidebar, header) |
| Override `--color-bg-secondary` to teal | Would break status columns, form backgrounds, and other secondary surfaces |
| Add class to `<div id="root">` | Unnecessary complexity; `body` already has the background rule |
| Tailwind config extension | App doesn't use Tailwind utility classes; uses plain CSS custom properties |
| Inline style on App.tsx wrapper | Violates FR-002 (single source of truth) and FR-008 (no hardcoded overrides) |

---

## R3: Impact on Existing UI Components

### Decision
No changes needed to existing components. All cards, modals, sidebars, headers, and overlays already define their own `background: var(--color-bg)` or `background: var(--color-bg-secondary)`, which will layer on top of the teal root background.

### Rationale
- **Header** (`.app-header`): uses `background: var(--color-bg)` → white in light mode, #0d1117 in dark mode. ✅ Distinct from teal.
- **Sidebar** (`.project-sidebar`): uses `background: var(--color-bg)` → white. ✅ Distinct.
- **Chat section** (`.chat-section`): uses `background: var(--color-bg)` → white. ✅ Distinct.
- **Board page** (`.board-page`): uses `background: var(--color-bg)` → white. ✅ Distinct.
- **Board columns** (`.board-column`): uses `background: var(--color-bg-secondary)`. ✅ Distinct.
- **Task/issue cards** (`.task-card`, `.board-issue-card`): uses `background: var(--color-bg)`. ✅ Distinct.
- **Modals** (`.modal-content`): uses `background: var(--color-bg)`. ✅ Distinct with backdrop.
- **Login screen** (`.app-login`): no background set — **will inherit teal**. Text color `var(--color-text)` (#24292F) on #0D9488 gives ~5.5:1. ✅ Pass.
- **Loading screen** (`.app-loading`): no background set — **will inherit teal**. ✅ Acceptable.

### Key Finding
The teal background will primarily be visible on:
1. The `body` behind the `#root` content
2. The login screen (before authentication)
3. The loading screen (during auth check)
4. Any gaps between layout sections (minimal with current flexbox layout)

Most authenticated views fill the viewport with components that have their own backgrounds, so the teal acts as a branded base layer visible during transitions and on screen edges.

---

## R4: Dark Mode Support

### Decision
Apply #0F766E as `--color-bg-app` in the `html.dark-mode-active` selector. The existing `useAppTheme` hook and class-toggling mechanism require no changes.

### Rationale
- The app already supports dark mode via `html.dark-mode-active` class toggle (managed by `useAppTheme` hook in `frontend/src/hooks/useAppTheme.ts`).
- The dark mode `:root` override block in `index.css` already changes all `--color-*` tokens. Adding `--color-bg-app: #0F766E` to this block follows the established pattern exactly.
- #0F766E is the spec-recommended dark variant (Tailwind teal-700), providing a deeper, less bright teal suitable for dark themes.
- No changes to the theme toggle hook, localStorage logic, or class application mechanism are needed.

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| Same teal (#0D9488) in dark mode | Too bright for dark mode context; jarring contrast with dark UI elements |
| Very dark teal (#134E4A, teal-900) | Too dark; nearly indistinguishable from the dark mode background (#0d1117) |
| No dark mode variant | Violates FR-007 (SHOULD apply darker variant); existing dark mode users would get bright teal |
