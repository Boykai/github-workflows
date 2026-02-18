# Tasks: Red Background Color for App

**Input**: Design documents from `/specs/003-red-background-app/`
**Prerequisites**: spec.md ✅ (plan.md not generated — spec.md contains full implementation context)

**Tests**: Tests are NOT included (not explicitly requested in spec).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No setup required — the project already uses CSS custom properties for theming in `frontend/src/index.css`. No new files, dependencies, or infrastructure needed.

*(No tasks in this phase)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational changes required — the existing CSS custom property architecture (`--color-bg`, `--color-bg-secondary`) and dark mode toggle (`html.dark-mode-active`) already support this change.

*(No tasks in this phase)*

---

## Phase 3: User Story 1 - Red Background Visible Across All Screens (Priority: P1) 🎯 MVP

**Goal**: Apply red-tinted background colors to the light mode theme so all screens display a red background

**Independent Test**: Open the application in light mode and navigate through all primary views — every screen should display a red-tinted background (#ffcdd2 page background, #ffebee surface background). Component-level backgrounds (cards, modals, input fields) should retain their own colors.

### Implementation for User Story 1

- [ ] T001 [US1] Update `--color-bg` from `#ffffff` to `#ffebee` (Material Red 50) in `:root` selector in frontend/src/index.css
- [ ] T002 [US1] Update `--color-bg-secondary` from `#f6f8fa` to `#ffcdd2` (Material Red 100) in `:root` selector in frontend/src/index.css

**Checkpoint**: Light mode now displays red-tinted backgrounds across all screens. Text contrast ratio with #24292f is 12.82:1 (--color-bg) and 10.41:1 (--color-bg-secondary), both exceeding WCAG AA 4.5:1 minimum.

---

## Phase 4: User Story 2 - Accessible Text on Red Background (Priority: P2)

**Goal**: Ensure all text and UI elements maintain WCAG AA-compliant contrast ratios against the red backgrounds

**Independent Test**: Inspect all text elements on the red background and verify contrast ratios meet WCAG AA (minimum 4.5:1). Primary text (#24292f) on #ffebee = 12.82:1 ✅. Primary text (#24292f) on #ffcdd2 = 10.41:1 ✅. Secondary text (#57606a) on both backgrounds also exceeds 4.5:1.

### Implementation for User Story 2

- [ ] T003 [US2] Verify existing foreground text color `--color-text: #24292f` achieves ≥4.5:1 contrast against new `--color-bg` (#ffebee) and `--color-bg-secondary` (#ffcdd2) in frontend/src/index.css
- [ ] T004 [US2] Verify existing secondary text color `--color-text-secondary: #57606a` achieves ≥4.5:1 contrast against new background values in frontend/src/index.css

**Checkpoint**: All text and UI elements are confirmed readable on the red backgrounds with WCAG AA compliance. No code changes needed — existing text colors already provide sufficient contrast.

---

## Phase 5: User Story 3 - Red Background in Dark Mode (Priority: P2)

**Goal**: Apply dark red background colors to the dark mode theme so the red aesthetic is maintained when dark mode is active

**Independent Test**: Toggle dark mode on and verify the background changes to dark red variants (#1a0000 page background, #2a0a0a surface background). Text should remain clearly readable.

### Implementation for User Story 3

- [ ] T005 [US3] Update `--color-bg` from `#0d1117` to `#2a0a0a` (dark red) in `html.dark-mode-active` selector in frontend/src/index.css
- [ ] T006 [US3] Update `--color-bg-secondary` from `#161b22` to `#1a0000` (very dark red) in `html.dark-mode-active` selector in frontend/src/index.css

**Checkpoint**: Dark mode now displays dark red-tinted backgrounds. Text contrast ratio with #e6edf3 is 15.50:1 (--color-bg) and 17.02:1 (--color-bg-secondary), both exceeding WCAG AA 4.5:1 minimum.

---

## Phase 6: User Story 4 - Centralized Theme Change (Priority: P3)

**Goal**: Confirm the red background is defined through centralized theme variables so future changes require only a single update

**Independent Test**: Verify that background color values are defined as CSS custom properties in `frontend/src/index.css` and are referenced (not hardcoded) throughout the application via `var(--color-bg)` and `var(--color-bg-secondary)`.

### Implementation for User Story 4

- [ ] T007 [US4] Verify all background color references use `var(--color-bg)` or `var(--color-bg-secondary)` and no hardcoded background color values exist in frontend/src/App.css
- [ ] T008 [US4] Verify body background uses `var(--color-bg-secondary)` in frontend/src/index.css (already the case — no changes needed)

**Checkpoint**: The red background is fully centralized — changing the 4 CSS custom property values in `frontend/src/index.css` is the only modification required, with zero component-level changes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all responsive breakpoints and modes

- [ ] T009 Verify red background renders consistently across mobile, tablet, and desktop viewport widths in frontend/src/index.css
- [ ] T010 Verify no component-level background overrides are broken by the global red background change in frontend/src/App.css

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup — skipped (no setup needed)
    ↓
Phase 2: Foundational — skipped (no foundational changes needed)
    ↓
Phase 3: User Story 1 (T001-T002, sequential — same file, same selector)
    ↓
Phase 4: User Story 2 (T003-T004, verification only — no code changes)
    ↓
Phase 5: User Story 3 (T005-T006, sequential — same file, same selector)
    ↓
Phase 6: User Story 4 (T007-T008, verification only — no code changes)
    ↓
Phase 7: Polish (T009-T010, parallel — different verification scopes)
```

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies — can start immediately. This is the MVP.
- **User Story 2 (P2)**: Depends on US1 (need red backgrounds applied to verify contrast). Verification only — no code changes.
- **User Story 3 (P2)**: No dependency on US1 (dark mode variables are independent). Can run in parallel with US1 if desired.
- **User Story 4 (P3)**: Depends on US1 and US3 (need all changes applied to verify centralization). Verification only — no code changes.

### Within Each User Story

- T001 before T002 (same `:root` selector in same file)
- T005 before T006 (same `html.dark-mode-active` selector in same file)
- Verification tasks (T003-T004, T007-T008) require no specific ordering

### Parallel Opportunities

- US1 (T001-T002) and US3 (T005-T006) modify different selectors in the same file and could be done together
- All verification tasks (T003-T004, T007-T008) can run in parallel after implementation
- Polish tasks (T009-T010) can run in parallel

---

## Parallel Example: User Story 1 + User Story 3

```bash
# These modify different selectors in the same file and can be batched:
Task T001: Update --color-bg in :root to #ffebee in frontend/src/index.css
Task T002: Update --color-bg-secondary in :root to #ffcdd2 in frontend/src/index.css
Task T005: Update --color-bg in html.dark-mode-active to #2a0a0a in frontend/src/index.css
Task T006: Update --color-bg-secondary in html.dark-mode-active to #1a0000 in frontend/src/index.css
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 3: User Story 1 (T001-T002) — apply red backgrounds in light mode
2. **STOP and VALIDATE**: Open app, confirm red background on all screens
3. Deploy/demo if ready — the core visual change is delivered

### Incremental Delivery

1. Add User Story 1 (T001-T002) → Light mode red background → Validate
2. Add User Story 3 (T005-T006) → Dark mode red background → Validate
3. Verify User Story 2 (T003-T004) → Accessibility confirmed
4. Verify User Story 4 (T007-T008) → Centralization confirmed
5. Polish (T009-T010) → Cross-device and cross-component validation

### Single Developer Strategy

Given this is an XS feature (0.5h estimate) with only 4 actual code changes in a single file:

1. Apply all 4 CSS variable changes (T001, T002, T005, T006) in one edit
2. Run all verifications (T003-T004, T007-T008, T009-T010) together
3. Total: ~10 minutes implementation, ~20 minutes verification

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| US1: Light Mode | T001-T002 | frontend/src/index.css |
| US2: Accessibility | T003-T004 | *(verification only)* |
| US3: Dark Mode | T005-T006 | frontend/src/index.css |
| US4: Centralization | T007-T008 | *(verification only)* |
| Polish | T009-T010 | *(verification only)* |

**Total Tasks**: 10
- Tasks per user story: US1=2, US2=2, US3=2, US4=2, Polish=2
- Code change tasks: 4 (T001, T002, T005, T006)
- Verification tasks: 6 (T003, T004, T007, T008, T009, T010)
- Parallel opportunities: US1+US3 can be batched; all verification tasks can run in parallel
- Independent test criteria: Each user story has its own independent test defined above
- Suggested MVP scope: User Story 1 only (T001-T002, light mode red background)
- Format validation: ✅ ALL tasks follow checklist format (checkbox, ID, labels, file paths)
