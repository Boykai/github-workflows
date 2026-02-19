# Tasks: Add Black Background Theme

**Input**: Design documents from `/specs/007-black-background/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/css-changes.md ✅, quickstart.md ✅

**Tests**: Not explicitly requested in feature specification. Test tasks are omitted per Test Optionality principle.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify current baseline and confirm file structure — no new dependencies required

- [X] T001 Verify current design token values in frontend/src/index.css and audit hardcoded light color values in frontend/src/App.css per contracts/css-changes.md

---

## Phase 2: User Story 1 + User Story 2 — Black Background Across All Pages + Readable Text and Icons (Priority: P1+P2) 🎯 MVP

**Goal**: Apply black background globally via centralized design tokens and prevent white flash on page load. All text and icon colors updated to WCAG AA-compliant values against the black background.

**Independent Test**: Load the app → background is black (#000000) from first paint → no white flash → navigate all routes → all pages have black background → all text is readable with light colors on black → all icons and interactive elements are clearly visible.

**Note**: US1 (global black background) and US2 (readable text/icons) are delivered together because both are achieved by the same `:root` token update in `frontend/src/index.css`. The new text tokens (`--color-text: #e6edf3`, `--color-text-secondary: #8b949e`) pass WCAG AA contrast (17.4:1 and 7.2:1 respectively) against `#000000` as verified in data-model.md.

### Implementation

- [X] T002 [US1] Update :root design tokens to black theme values in frontend/src/index.css — change --color-primary to #539bf5, --color-secondary to #8b949e, --color-success to #3fb950, --color-warning to #d29922, --color-danger to #f85149, --color-bg to #000000, --color-bg-secondary to #121212, --color-border to #30363d, --color-text to #e6edf3, --color-text-secondary to #8b949e, --shadow to 0 1px 3px rgba(0, 0, 0, 0.4)
- [X] T003 [P] [US1] Add inline style="background-color: #000000" to the <html> element in frontend/index.html to prevent white flash before CSS loads (FR-005)

**Checkpoint**: MVP complete — all pages display black background, all text passes WCAG AA contrast, no white flash on load. The centralized token architecture ensures all components using `var(--color-*)` inherit the new values automatically (FR-006, SC-005).

---

## Phase 3: User Story 3 — Consistent Component Theming (Priority: P3)

**Goal**: Replace hardcoded light background and text color values that bypass the token system so error states, animations, and component-specific styles are visually consistent with the black theme.

**Independent Test**: Trigger error states (error toast, error banner) → backgrounds are dark red-tinted (not light pink) → error text is readable → trigger highlight-pulse animation → green tint is visible on black background.

### Implementation

- [X] T004 [US3] Replace hardcoded light background and text colors in frontend/src/App.css — update highlight-pulse animation background from #dafbe1 to rgba(45, 164, 78, 0.2) at line ~388, error-toast background from #fff1f0 to rgba(207, 34, 46, 0.15) at line ~407, error-banner background from #fff1f0 to rgba(207, 34, 46, 0.15) at line ~446, error-banner-message color from #82071e to #ff6b6b at line ~471, and board-error-content color from #82071e to #ff6b6b at line ~1476

**Checkpoint**: All component-level backgrounds consistent with black theme. No remaining hardcoded light backgrounds in the codebase (FR-007).

---

## Phase 4: User Story 4 — Third-Party and Embedded Content Blending (Priority: P4)

**Goal**: Ensure any third-party embedded content or iframes blend visually with the black background.

**Independent Test**: Inspect all app routes for embedded third-party content and confirm visual integration with the black theme.

**Note**: No third-party embeds or iframes currently exist in the application (confirmed in research.md, Decision Area 8). No implementation tasks are required. If third-party content is added in the future, it should be wrapped in a dark-bordered container with a matching background to visually contain it.

**Checkpoint**: US4 satisfied — no third-party content exists to address. Approach documented for future use.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and visual regression check across all routes

- [X] T005 [P] Verify no remaining hardcoded light background values (#fff, #ffffff, #f6f8fa, #f5f5f5) in background properties across frontend/src/index.css, frontend/src/App.css, and frontend/src/components/chat/ChatInterface.css
- [X] T006 Run quickstart.md validation checklist from specs/007-black-background/quickstart.md — verify all pages display black background, no white flash on load, text contrast passes, all components themed, error states visible

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **US1+US2 (Phase 2)**: Depends on Phase 1 — MVP delivery target
- **US3 (Phase 3)**: Can start after Phase 1 — independent of Phase 2 (different file: App.css vs index.css)
- **US4 (Phase 4)**: No implementation needed — documentation only
- **Polish (Phase 5)**: Depends on Phase 2 and Phase 3 being complete

### User Story Dependencies

- **US1+US2 (P1+P2)**: Can start after Setup — no dependencies on other stories
- **US3 (P3)**: Can start after Setup — independent of US1+US2 (different file)
- **US4 (P4)**: No dependencies — no implementation required

### Within Each Phase

- Token updates (index.css) before inline style (index.html) within Phase 2
- All hardcoded color replacements within the same file (App.css) are sequential in Phase 3
- Verification tasks (Phase 5) run after all implementation phases

### Parallel Opportunities

- T003 (index.html inline style) can run in parallel with T002 (index.css tokens) — different files
- Phase 2 (US1+US2, index.css + index.html) and Phase 3 (US3, App.css) can run in parallel — different files, no dependencies
- T005 and T006 (Polish) can run in parallel with each other

---

## Parallel Example: Phase 2 + Phase 3

```
# These can run in parallel (different files, no dependencies):
Phase 2: T002 (index.css tokens) + T003 (index.html inline style)
Phase 3: T004 (App.css hardcoded color replacements)

# All three files are independent — maximum parallelism possible
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (verify current state)
2. Complete Phase 2: US1+US2 (update :root tokens + prevent white flash)
3. **STOP and VALIDATE**: All pages have black background, text is readable, no white flash
4. Deploy/demo — delivers the primary user value (black background + readable text)

### Incremental Delivery

1. Setup → Baseline verified
2. Add US1+US2 → Black background + readable text → **MVP!**
3. Add US3 → Hardcoded colors fixed → Component consistency complete
4. US4 → No changes needed (documented)
5. Polish → Final verification → Production-ready

### Key Optimization

Phase 2 (US1+US2) and Phase 3 (US3) can run in parallel since they modify different files (index.css/index.html vs App.css), reducing total wall-clock time to that of the slower phase.

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| Setup | T001 | (verification only) |
| US1+US2 (MVP) | T002–T003 | frontend/src/index.css, frontend/index.html |
| US3 | T004 | frontend/src/App.css |
| US4 | (none) | (no third-party embeds exist) |
| Polish | T005–T006 | (verification only) |

**Total Tasks**: 6
**Tasks per User Story**: US1+US2: 2, US3: 1, US4: 0
**Parallel Opportunities**: T002+T003 (different files), Phase 2+Phase 3 (different files), T005+T006
**Suggested MVP Scope**: Phase 1 + Phase 2 (US1+US2 only — delivers black background + readable text)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- No backend changes — this is a frontend CSS-only feature
- No new dependencies required
- ChatInterface.css already uses `var(--color-*)` tokens — inherits black theme automatically from T002
- Dark mode toggle (`html.dark-mode-active`) remains unchanged — both modes are now dark variants
- Rollback is instant via `git revert` — all changes are CSS value replacements
- All WCAG AA contrast ratios verified mathematically in data-model.md
