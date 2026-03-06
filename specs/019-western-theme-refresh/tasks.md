# Tasks: Western/Cowboy UI Theme Refresh

**Input**: Design documents from `/specs/019-western-theme-refresh/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No new tests requested. Existing Vitest, jest-axe, and Playwright tests serve as regression guards (SC-004).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/` at repository root (no backend changes)
- Config files: `frontend/index.html`, `frontend/tailwind.config.js`
- Styles: `frontend/src/index.css`
- Components: `frontend/src/components/`
- Pages: `frontend/src/pages/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No structural changes needed — this is a re-skin of an existing project. The only setup is verifying the dev environment works.

- [x] T001 Verify frontend dev server starts cleanly with `cd frontend && npm install && npm run dev`
- [x] T002 Run existing test suite to capture baseline with `cd frontend && npm test`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core design system changes that MUST be complete before any user story-specific work. These 3 config/style files define the entire visual foundation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete — all component styling derives from these tokens.

- [x] T003 Replace all CSS custom property values in the `:root` block of `frontend/src/index.css` with western light-mode HSL tokens per data-model.md Light Mode entity (19 color tokens + radius)
- [x] T004 Replace all CSS custom property values in the `.dark` block of `frontend/src/index.css` with western dark-mode HSL tokens per data-model.md Dark Mode entity (18 color tokens)
- [x] T005 Add `h1, h2, h3 { font-family: theme('fontFamily.display'); }` rule to the `@layer base` block in `frontend/src/index.css`
- [x] T006 Update the Google Fonts `<link>` tag in `frontend/index.html` to include Rye font: `family=Rye&family=Inter:wght@400;500;600;700&display=swap`
- [x] T007 Add `display: ['Rye', 'Georgia', 'serif']` to `fontFamily` and update `sans` fallbacks to `['Inter', 'system-ui', 'sans-serif']` in `frontend/tailwind.config.js`
- [x] T008 Add warm `boxShadow` entries (`warm-sm`, `warm`, `warm-md`, `warm-lg`) to `theme.extend` in `frontend/tailwind.config.js` per research.md RT-3
- [x] T009 Update `--radius` value from `0.5rem` to `0.375rem` in the `:root` block of `frontend/src/index.css`

**Checkpoint**: Load app in browser — cream backgrounds, brown text, gold accents, and Rye headings should be visible across all views. Dark mode toggle should show espresso-brown backgrounds with gold accents.

---

## Phase 3: User Story 1 — Western Design System & Global Theming (Priority: P1) 🎯 MVP

**Goal**: Deliver the complete western visual identity in light mode — all pages display warm cream backgrounds, dark brown text, sunset-gold accents, and western-style headings.

**Independent Test**: Load the app in light mode and visually confirm: cream/parchment backgrounds, dark brown text, gold/orange accent elements, and western slab-serif headings on login, board, and settings views.

### Implementation for User Story 1

> Note: The foundational phase (T003–T009) delivers ~80% of US1 via CSS variable propagation. These tasks handle the remaining ~20% that requires manual verification and adjustment.

- [x] T010 [US1] Verify light-mode visual rendering on the login/unauthenticated view in `frontend/src/App.tsx` — confirm cream background, brown text, gold accents on LoginButton, Rye font on "Agent Projects" heading
- [x] T011 [US1] Verify light-mode visual rendering on the board view in `frontend/src/pages/ProjectBoardPage.tsx` — confirm board columns, issue cards, and panels all reflect the western palette
- [x] T012 [US1] Verify light-mode visual rendering on the settings view in `frontend/src/pages/SettingsPage.tsx` — confirm settings sections, inputs, buttons, and labels reflect the western palette
- [x] T013 [US1] Run existing test suite (`cd frontend && npm test`) to confirm all tests pass with the new palette — no modifications to tests allowed (SC-004)

**Checkpoint**: All views display the western color palette in light mode. Existing tests pass. US1 is independently verified.

---

## Phase 4: User Story 2 — Dark Mode Western Theme (Priority: P1)

**Goal**: Deliver the complete western dark mode — espresso-brown backgrounds, warm off-white text, gold accents, consistent aesthetic with light mode.

**Independent Test**: Toggle to dark mode via the existing theme switch and verify: deep brown backgrounds (not black), warm off-white text, gold accents, and legible contrast across all views.

### Implementation for User Story 2

> Note: The foundational phase (T004) already defines all dark-mode CSS variables. These tasks verify and refine the dark mode rendering.

- [x] T014 [US2] Verify dark-mode visual rendering across all views (login, board, settings) — confirm espresso-brown backgrounds, warm off-white text, gold accents, Rye headings
- [x] T015 [US2] Verify the `select` element `color-scheme` rules in `frontend/src/index.css` still work correctly for native dropdowns in both light and dark modes
- [x] T016 [US2] Run existing test suite in dark-mode context to confirm no regressions — existing tests pass unchanged

**Checkpoint**: Both light and dark modes display a consistent western aesthetic. Theme toggle works seamlessly.

---

## Phase 5: User Story 3 — Updated UI Primitives & Interactive States (Priority: P2)

**Goal**: Refine buttons, cards, and inputs with tactile interactions — press animation, warm shadows, gold focus highlights — to complete the themed interactive experience.

**Independent Test**: Tab through all interactive elements to verify gold focus rings; hover over cards/buttons to verify warm shadow/border transitions; click buttons to verify press scale effect.

### Implementation for User Story 3

- [x] T017 [P] [US3] Add `transition-transform duration-150 active:scale-[0.97]` to the button base className in `frontend/src/components/ui/button.tsx` (FR-007)
- [x] T018 [P] [US3] Replace `shadow-sm` with `shadow-warm-sm` and add `hover:shadow-warm-md` as the default card shadow in `frontend/src/components/ui/card.tsx` (FR-012)
- [x] T019 [P] [US3] Add `focus:border-accent` to the input className in `frontend/src/components/ui/input.tsx` for gold focus border highlight (FR-006)
- [x] T020 [US3] Verify gold focus rings appear on all interactive elements (buttons, inputs, links) by tabbing through the UI — the `--ring` CSS variable (now gold) handles this via Tailwind's `ring-ring` class
- [x] T021 [US3] Run existing test suite to confirm button, card, and input test files still pass after class changes

**Checkpoint**: All interactive elements exhibit updated hover, focus, and active states. Press animation works on buttons. Warm shadows on cards. Gold focus borders on inputs.

---

## Phase 6: User Story 4 — Hardcoded Color Harmonization (Priority: P2)

**Goal**: Audit and update all hardcoded Tailwind color classes across ~20 component files to harmonize with the western palette while preserving semantic meaning for functional indicators.

**Independent Test**: Navigate to views containing status badges (agent cards), warning banners (rate limit, signal conflict), and sync indicators. Confirm they visually harmonize with surrounding western-themed elements. Functional status dots (green/yellow/red) retain standard colors.

### Implementation for User Story 4 — REPLACE disposition

- [x] T022 [P] [US4] Replace hardcoded `amber-*` classes in the SignalBannerBar section of `frontend/src/App.tsx` with `accent/*` theme tokens per research.md RT-4 REPLACE table
- [x] T023 [P] [US4] Replace hardcoded status badge colors in `frontend/src/components/agents/AgentCard.tsx` — active badge: soften green, pending PR badge: use `accent` tokens, pending deletion badge: use `destructive` tokens per research.md RT-4
- [x] T024 [P] [US4] Replace hardcoded `green-500/600` confirm button colors with `bg-primary text-primary-foreground` in `frontend/src/components/chat/TaskPreview.tsx`
- [x] T025 [P] [US4] Replace hardcoded `green-500/600` confirm button colors with `bg-primary text-primary-foreground` in `frontend/src/components/chat/StatusChangePreview.tsx`
- [x] T026 [P] [US4] Replace hardcoded multi-color button and badge classes with theme tokens where possible in `frontend/src/components/chat/IssueRecommendationPreview.tsx`
- [x] T027 [P] [US4] Replace hardcoded `amber-*` warning classes with `accent/*` theme tokens in `frontend/src/components/settings/DynamicDropdown.tsx`
- [x] T028 [P] [US4] Replace hardcoded `green-*` success indicator colors in `frontend/src/components/board/CleanUpSummary.tsx` with softened `green-100/80 text-green-800` variants
- [x] T029 [P] [US4] Replace hardcoded `green-*` success indicator colors in `frontend/src/components/board/CleanUpConfirmModal.tsx` with softened variants
- [x] T030 [P] [US4] Replace hardcoded `green-*` and `yellow-*` status colors in `frontend/src/components/board/CleanUpAuditHistory.tsx` with softened or token-based variants

### Implementation for User Story 4 — SOFTEN disposition

- [x] T031 [P] [US4] Soften `amber-500` to `amber-600` or replace with `accent` token in `frontend/src/components/board/AgentTile.tsx`
- [x] T032 [P] [US4] Soften `amber-500` to `amber-600` or replace with `accent` token in `frontend/src/components/board/AgentColumnCell.tsx`
- [x] T033 [P] [US4] Soften status colors (`amber-500`→`amber-600`, `green-500`→`green-600`, `blue-500`→`blue-600`) in `frontend/src/components/board/AddAgentPopover.tsx`
- [x] T034 [P] [US4] Soften `green-500`→`green-600` and `yellow-500`→`yellow-600` in `frontend/src/components/chores/ChoreCard.tsx`
- [x] T035 [P] [US4] Replace `yellow-500/10`/`yellow-700` warning banner colors with `accent/10`/`accent-foreground` tokens in `frontend/src/pages/ProjectBoardPage.tsx`
- [x] T036 [P] [US4] Adjust `green-500` success text to `text-green-700 dark:text-green-400` in `frontend/src/components/settings/SettingsSection.tsx`
- [x] T037 [P] [US4] Adjust `green-500` success indicator to `text-green-700 dark:text-green-400` in `frontend/src/components/chat/MessageBubble.tsx`

### Verification for User Story 4 — KEEP disposition (no changes, just verify)

- [x] T038 [US4] Verify sync status dots in `frontend/src/pages/ProjectBoardPage.tsx` retain `green-500`/`yellow-500`/`red-500` semantic colors (FR-009)
- [x] T039 [US4] Verify connection status indicators in `frontend/src/components/settings/SignalConnection.tsx` retain standard `green-*`/`yellow-*`/`red-*` semantic colors (FR-009)
- [x] T040 [US4] Verify MCP status indicators in `frontend/src/components/settings/McpSettings.tsx` retain standard semantic colors (FR-009)
- [x] T041 [US4] Verify sub-issue state icons in `frontend/src/components/board/IssueCard.tsx` retain `green-500`/`purple-500` GitHub state colors (FR-009)
- [x] T042 [US4] Verify state indicators in `frontend/src/components/board/IssueDetailModal.tsx` retain `green-500`/`purple-500`/`red-500` semantic colors (FR-009)
- [x] T043 [US4] Run existing test suite to confirm all tests pass after hardcoded color updates

**Checkpoint**: All hardcoded colors have been intentionally categorized — replaced, softened, or confirmed as kept. No clashing colors remain. Functional status indicators preserved.

---

## Phase 7: User Story 5 — Layout & Structural Enhancements (Priority: P3)

**Goal**: Add structural polish to elevate the theme from a color swap to a cohesive branded experience — header branding, favicon, navigation transitions.

**Independent Test**: Load the app and inspect: the header for western branding elements (display font on app name, gold accent border), the browser tab for a themed favicon, and navigation buttons for smooth transition effects.

### Implementation for User Story 5

- [x] T044 [P] [US5] Add `font-display` class to the "Agent Projects" application name in the header section of `frontend/src/App.tsx` and add a subtle `border-b-2 border-accent` gold accent border to the header (FR-003)
- [x] T045 [P] [US5] Create a western-themed SVG favicon at `frontend/public/favicon.svg` using gold (#D4A017) and brown (#55351A) colors (horseshoe or cowboy hat silhouette) per research.md RT-7 (FR-013)
- [x] T046 [US5] Update the `<link rel="icon">` tag in `frontend/index.html` to reference the new `favicon.svg` instead of `/vite.svg` (FR-013)
- [x] T047 [P] [US5] Add `font-display` class to page headings in `frontend/src/pages/ProjectBoardPage.tsx` ("Project Board" heading) and `frontend/src/pages/SettingsPage.tsx` ("Settings" heading)
- [x] T048 [US5] Add `transition-all duration-150` to navigation buttons in the header of `frontend/src/App.tsx` for smooth active/inactive state transitions
- [x] T049 [US5] Run existing test suite to confirm no regressions after layout enhancements

**Checkpoint**: Header displays western branding with display font and gold accent. Favicon is western-themed. Navigation transitions are smooth.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [x] T050 Visual regression check across all views (login, board, settings) in both light and dark modes — verify no remnant slate/blue theme colors (SC-001)
- [x] T051 WCAG AA contrast audit — verify all text-to-background combinations meet 4.5:1 (normal) or 3:1 (large text) requirements using browser dev tools or jest-axe output (SC-003, FR-010)
- [x] T052 Responsive layout check — resize browser from desktop to mobile widths, verify no layout breaks, font scaling, card stacking (SC-008)
- [x] T053 Interactive state audit — tab through all elements for gold focus rings, hover cards/buttons for warm shadows, click buttons for press effect (SC-007)
- [x] T054 Run full existing test suite (`cd frontend && npm test`) for final regression confirmation (SC-004)
- [x] T055 Run Playwright e2e tests (`cd frontend && npx playwright test`) if available, to confirm no end-to-end regressions
- [x] T056 Run quickstart.md validation checklist from `specs/019-western-theme-refresh/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001, T002) — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Foundational (T003–T009) — verification pass
- **US2 (Phase 4)**: Depends on Foundational (T003–T009) — can run in parallel with US1
- **US3 (Phase 5)**: Depends on Foundational (T007, T008 for warm shadows) — can run in parallel with US1/US2
- **US4 (Phase 6)**: Depends on Foundational (T003, T004 for palette context) — can run in parallel with US3
- **US5 (Phase 7)**: Depends on Foundational (T006, T007 for display font) — can run in parallel with US3/US4
- **Polish (Phase 8)**: Depends on ALL user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational phase — no dependencies on other stories
- **US2 (P1)**: Depends only on Foundational phase — independent of US1 (different CSS block)
- **US3 (P2)**: Depends only on Foundational phase (warm shadow tokens) — independent of US1/US2
- **US4 (P2)**: Depends only on Foundational phase (palette context for color decisions) — independent of US3
- **US5 (P3)**: Depends only on Foundational phase (display font availability) — independent of US3/US4

### Within Each User Story

- REPLACE tasks before SOFTEN tasks (more impactful first)
- Implementation before verification
- All [P] tasks within a story can run in parallel
- Story complete before final verification task

### Parallel Opportunities

- T003 and T004 edit the same file (`index.css`) — run sequentially
- T005 edits `index.css` — run after T003/T004
- T006 and T007/T008 edit different files — can run in parallel
- T017, T018, T019 edit different files — can run in parallel
- T022–T037 all edit different files — can ALL run in parallel
- T044, T045, T047 edit different files — can run in parallel

---

## Parallel Example: User Story 4 (Maximum Parallelism)

```bash
# All REPLACE tasks target different files — run simultaneously:
T022: App.tsx SignalBannerBar
T023: AgentCard.tsx status badges
T024: TaskPreview.tsx confirm button
T025: StatusChangePreview.tsx confirm button
T026: IssueRecommendationPreview.tsx badges
T027: DynamicDropdown.tsx warnings
T028: CleanUpSummary.tsx success indicators
T029: CleanUpConfirmModal.tsx success indicators
T030: CleanUpAuditHistory.tsx status indicators

# All SOFTEN tasks target different files — also can run simultaneously:
T031: AgentTile.tsx
T032: AgentColumnCell.tsx
T033: AddAgentPopover.tsx
T034: ChoreCard.tsx
T035: ProjectBoardPage.tsx banners
T036: SettingsSection.tsx
T037: MessageBubble.tsx
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T009) — **this delivers ~80% of the visual transformation**
3. Complete Phase 3: User Story 1 verification (T010–T013)
4. **STOP and VALIDATE**: App displays western theme in light mode. Tests pass.
5. This is a shippable MVP — the app is fully themed in light mode.

### Incremental Delivery

1. Setup + Foundational → Foundation ready (both light and dark tokens defined)
2. Add US1 verification → Light mode confirmed → MVP shippable
3. Add US2 verification → Dark mode confirmed → Both modes themed
4. Add US3 → Primitives refined (press, shadows, focus) → Polished interactions
5. Add US4 → Hardcoded colors harmonized → No visual outliers
6. Add US5 → Header branding, favicon, transitions → Complete branded experience
7. Polish → Final cross-cutting validation → Feature complete

### Critical Path

```
T001 → T002 → T003 → T004 → T005 → T009 (index.css sequential edits)
                  ↘ T006 (index.html — parallel with T005)
                  ↘ T007 → T008 (tailwind.config.js — parallel with T005)
```

After Foundational phase, all user stories can proceed in parallel.
