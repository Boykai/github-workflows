# Tasks: Add Golden Background to App

**Input**: Design documents from `/specs/018-golden-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested in the feature specification. No automated test tasks included. Visual regression review is manual per spec assumptions.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Changes scoped entirely to `frontend/src/index.css` per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing project structure and theming system before making changes

- [x] T001 Verify existing CSS custom property structure in `frontend/src/index.css` (confirm `:root` and `.dark` selectors with `--background` token)
- [x] T002 Verify Tailwind config consumes `hsl(var(--background))` in `frontend/tailwind.config.js` (read-only confirmation, no changes needed)
- [x] T003 Verify `body` applies `@apply bg-background` in `frontend/src/index.css` (read-only confirmation, no changes needed)

**Checkpoint**: Existing theming infrastructure confirmed — token update can proceed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational blocking tasks required. This feature modifies existing CSS tokens only — no new infrastructure, dependencies, or schema changes are needed.

**⚠️ NOTE**: Phase 2 is empty because the existing theming system (CSS variables + Tailwind config + ThemeProvider) already provides all required infrastructure. Proceed directly to user story phases.

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 — Golden Background Visible Across App (Priority: P1) 🎯 MVP

**Goal**: Apply a golden background color (#FFD700) to the top-level app container globally across all pages via the existing `--background` CSS custom property.

**Independent Test**: Open the application in a browser and verify the background color across all pages is golden (#FFD700), with no layout breakage, consistent across mobile/tablet/desktop widths, and rendering identically in Chrome, Firefox, Safari, and Edge.

### Implementation for User Story 1

- [x] T004 [US1] Update `:root` `--background` value from `0 0% 100%` to `51 100% 50%` in `frontend/src/index.css`

**Checkpoint**: Light-mode golden background is now visible across the entire app. Verify by opening `http://localhost:5173` — the page background should be gold (#FFD700). Resize to mobile/tablet/desktop widths to confirm no layout breakage.

---

## Phase 4: User Story 2 — Text and UI Elements Remain Readable (Priority: P1)

**Goal**: Ensure all foreground text and UI elements maintain a minimum 4.5:1 contrast ratio against the golden background per WCAG AA standards.

**Independent Test**: Run an accessibility contrast checker (browser DevTools or external tool) with background #FFD700 and foreground #020817. Verify contrast ratio ≥4.5:1 (expected: ~13.6:1). Visually confirm all text, buttons, links, icons, and form inputs remain clearly readable.

### Implementation for User Story 2

- [x] T005 [US2] Verify existing `--foreground` value (`222.2 84% 4.9%` ≈ #020817) provides ≥4.5:1 contrast against gold background in `frontend/src/index.css` (no change expected — research confirms 13.6:1 ratio)
- [x] T006 [US2] Visual review of all pages to confirm images, icons, and components that previously assumed a white/neutral background remain legible against gold in `frontend/src/index.css`
- [x] T007 [US2] Confirm `--card` (`0 0% 100%`), `--popover` (`0 0% 100%`), and `--secondary` tokens remain unchanged so overlay surfaces maintain their own backgrounds in `frontend/src/index.css`

**Checkpoint**: All text and UI elements confirmed readable against golden background. No foreground color changes needed. Cards, popovers, and overlays retain their own backgrounds.

---

## Phase 5: User Story 3 — Golden Color Registered as Reusable Theme Token (Priority: P2)

**Goal**: Ensure the golden background color is defined as a reusable design token (CSS variable) within the existing theming system, changeable in one place.

**Independent Test**: Open `frontend/src/index.css`, confirm `--background: 51 100% 50%;` exists in `:root`. Change the value to a different shade (e.g., `51 100% 60%`), rebuild, and verify the background updates globally without modifying any other file.

### Implementation for User Story 3

- [x] T008 [US3] Confirm `--background` CSS variable in `:root` of `frontend/src/index.css` serves as the single source of truth for the golden color (already satisfied by T004 — this is a validation task)
- [x] T009 [P] [US3] Add inline comment documenting the gold color choice (`/* Gold #FFD700 — see specs/018-golden-background */`) next to the `--background` token in `frontend/src/index.css`

**Checkpoint**: Golden color is registered as a reusable CSS variable. Changing `--background` in `:root` updates the background globally.

---

## Phase 6: User Story 4 — Dark Mode Compatibility (Priority: P2)

**Goal**: Define explicit golden background behavior for dark mode — a deepened dark-gold variant that maintains the golden identity while being comfortable for dark mode viewing.

**Independent Test**: Toggle to dark mode and verify the background displays a deepened dark-gold tone (~#3D2E0A). Confirm text remains readable (expected ~12.5:1 contrast ratio). Toggle between light and dark mode to verify smooth transition.

### Implementation for User Story 4

- [x] T010 [US4] Update `.dark` `--background` value from `222.2 84% 4.9%` to `43 74% 15%` in `frontend/src/index.css`
- [x] T011 [US4] Verify dark-mode `--foreground` value (`210 40% 98%` ≈ #F8FAFC) provides ≥4.5:1 contrast against dark gold background in `frontend/src/index.css` (no change expected — research confirms ~12.5:1 ratio)
- [x] T012 [US4] Verify dark-mode `--card`, `--popover`, and `--secondary` tokens remain unchanged in `frontend/src/index.css`

**Checkpoint**: Dark mode displays deepened dark-gold background. Light/dark mode toggle transitions smoothly. All text readable in both modes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [x] T013 Cross-browser verification: Open app in Chrome, Firefox, Safari, and Edge — confirm golden background renders identically in all browsers
- [x] T014 Responsive verification: Test at mobile (375px), tablet (768px), and desktop (1440px) widths — confirm no layout breakage
- [x] T015 Visual regression review: Navigate through all major pages (board, settings, chat) — confirm no components are unexpectedly affected by the golden background
- [x] T016 Run `frontend/src/index.css` quickstart validation per `specs/018-golden-background/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — read-only verification, can start immediately
- **Foundational (Phase 2)**: Empty — no blocking prerequisites needed
- **User Story 1 (Phase 3)**: Depends on Setup verification — the core CSS token change
- **User Story 2 (Phase 4)**: Depends on User Story 1 (T004) — validates contrast after gold is applied
- **User Story 3 (Phase 5)**: Depends on User Story 1 (T004) — validates token reusability after gold is applied
- **User Story 4 (Phase 6)**: Depends on Setup verification — dark mode change is independent of light mode
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup — No dependencies on other stories
- **User Story 2 (P1)**: Depends on User Story 1 — contrast validation requires gold background to be applied first
- **User Story 3 (P2)**: Depends on User Story 1 — token validation requires the token to have the gold value
- **User Story 4 (P2)**: Can start after Setup — dark mode token is independent of light mode token (can run in parallel with US1)

### Within Each User Story

- Verify existing values before modifying
- Modify CSS token value
- Validate contrast compliance
- Visual review of affected components

### Parallel Opportunities

- **T001, T002, T003** (Setup): All verification tasks can run in parallel
- **US1 and US4**: Light mode (T004) and dark mode (T010) modify different CSS selectors (`:root` vs `.dark`) in the same file — can be done sequentially in one edit but are logically independent
- **T005, T006, T007** (US2 validation): Can run in parallel after T004
- **T008, T009** (US3): T009 can run in parallel with other tasks (different section of file)
- **T013, T014, T015** (Polish): All verification tasks can run in parallel

---

## Parallel Example: User Stories 1 & 4

```bash
# These modify different selectors in the same file, so execute sequentially but can be planned together:
Task T004: "Update :root --background to 51 100% 50% in frontend/src/index.css"
Task T010: "Update .dark --background to 43 74% 15% in frontend/src/index.css"

# After both are done, validation tasks can run in parallel:
Task T005: "Verify light-mode contrast ratio"
Task T011: "Verify dark-mode contrast ratio"
Task T006: "Visual review of pages in light mode"
Task T012: "Verify dark-mode card/popover tokens unchanged"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup verification (T001–T003)
2. Phase 2: No blocking tasks needed
3. Complete Phase 3: User Story 1 (T004) — single CSS variable change
4. **STOP and VALIDATE**: Open app, verify golden background is visible globally
5. Deploy/demo if ready — this single change delivers the core feature

### Incremental Delivery

1. Complete Setup → Confirm theming infrastructure
2. Add User Story 1 (T004) → Golden background visible → **MVP!**
3. Add User Story 2 (T005–T007) → Contrast compliance validated
4. Add User Story 3 (T008–T009) → Token documented as reusable
5. Add User Story 4 (T010–T012) → Dark mode golden variant applied
6. Polish (T013–T016) → Cross-browser and responsive validation complete
7. Each story adds value without breaking previous stories

### Single Developer Strategy

Since this is an XS feature (~1 hour estimate) modifying a single file:

1. Complete all Setup verifications (5 minutes)
2. Apply both light-mode and dark-mode token changes together (T004 + T010) — 5 minutes
3. Run all validation tasks (T005–T009, T011–T012) — 15 minutes
4. Complete Polish phase (T013–T016) — 15 minutes
5. Total: ~40 minutes including visual reviews

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 16 |
| **Setup tasks** | 3 (T001–T003) |
| **User Story 1 tasks** | 1 (T004) |
| **User Story 2 tasks** | 3 (T005–T007) |
| **User Story 3 tasks** | 2 (T008–T009) |
| **User Story 4 tasks** | 3 (T010–T012) |
| **Polish tasks** | 4 (T013–T016) |
| **Parallel opportunities** | Setup (3), US2 validation (3), Polish (3) |
| **Files modified** | 1 (`frontend/src/index.css`) |
| **Suggested MVP scope** | User Story 1 only (T004 — single CSS variable change) |
| **Format validated** | ✅ All tasks follow checkbox + ID + labels + file path format |

---

## Notes

- This feature modifies exactly **one file** (`frontend/src/index.css`) with **two CSS variable value changes**
- No new dependencies, files, API changes, or structural changes required
- Most tasks are validation/verification tasks since the actual code change is minimal
- The golden color uses the existing `hsl(var(--background))` Tailwind pattern — zero config changes needed
- Tests are not included as they were not requested in the specification
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
