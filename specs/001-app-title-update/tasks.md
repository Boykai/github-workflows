# Tasks: Update App Title to "GitHub Workflows"

**Input**: Design documents from `/specs/001-app-title-update/`
**Prerequisites**: spec.md (loaded - 2 user stories with priorities P1, P2)

**Tests**: No tests requested in feature specification - focusing on direct implementation and manual validation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app structure**: `frontend/` for React application
- HTML entry point: `frontend/index.html`
- React components: `frontend/src/`

---

## Phase 1: Setup (Project Context)

**Purpose**: Verify project structure and understand current title implementation

- [ ] T001 Verify frontend project structure and locate title configuration files

---

## Phase 2: User Story 1 - Browser Tab Title Update (Priority: P1) 🎯 MVP

**Goal**: Update the browser page title to "GitHub Workflows" so users can identify the application in browser tabs, bookmarks, and tab tooltips.

**Independent Test**: Open the application in a browser and verify:
1. Browser tab displays "GitHub Workflows"
2. Bookmark the page and verify bookmark title shows "GitHub Workflows"
3. Hover over the browser tab to verify tooltip shows "GitHub Workflows"

### Implementation for User Story 1

- [ ] T002 [US1] Update HTML title tag from "Welcome to Tech Connect 2026!" to "GitHub Workflows" in frontend/index.html (line 7)

**Checkpoint**: Browser tab title should now display "GitHub Workflows" - test by opening the application in a browser

---

## Phase 3: User Story 2 - UI Header Title Update (Priority: P2)

**Goal**: Update all visible UI headers to display "GitHub Workflows" for consistent branding throughout the user experience.

**Independent Test**: Navigate through the application and verify:
1. Login page header displays "GitHub Workflows"
2. Authenticated app header displays "GitHub Workflows"
3. Header remains consistent across all pages and routes
4. Header displays appropriately on mobile viewport

### Implementation for User Story 2

- [ ] T003 [P] [US2] Update login page header from "Welcome to Tech Connect 2026!" to "GitHub Workflows" in frontend/src/App.tsx (line 69)
- [ ] T004 [P] [US2] Update authenticated app header from "Welcome to Tech Connect 2026!" to "GitHub Workflows" in frontend/src/App.tsx (line 85)

**Checkpoint**: All UI headers should now display "GitHub Workflows" - test by viewing both unauthenticated and authenticated states

---

## Phase 4: Cross-Browser Validation & Polish

**Purpose**: Verify title updates work correctly across all supported browsers and ensure no regressions

- [ ] T005 [P] Validate title display in Chrome browser (FR-004 compliance)
- [ ] T006 [P] Validate title display in Firefox browser (FR-004 compliance)
- [ ] T007 [P] Validate title display in Safari browser (FR-004 compliance)
- [ ] T008 [P] Validate title display in Edge browser (FR-004 compliance)
- [ ] T009 Verify title consistency across all application routes (FR-003 compliance)
- [ ] T010 Test responsive header display on mobile viewport (User Story 2, Acceptance Scenario 3)
- [ ] T011 Verify no regression in navigation, routing, or other functionality (FR-005 compliance)
- [ ] T012 Confirm title truncation behavior in narrow browser tabs is acceptable (Edge Case handling)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **User Story 1 (Phase 2)**: Depends on Setup - Browser tab title (P1 priority)
- **User Story 2 (Phase 3)**: Independent of US1 - UI header titles (P2 priority)
- **Validation (Phase 4)**: Depends on completion of US1 and US2

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Setup (Phase 1) - Independent of US1, can run in parallel

### Within Each User Story

- User Story 1: Single file update (frontend/index.html)
- User Story 2: Two parallel updates in same file (frontend/src/App.tsx lines 69 and 85)

### Parallel Opportunities

- Phase 1 has only one task (sequential)
- Phase 2 (User Story 1) and Phase 3 (User Story 2) can be worked on in parallel after Phase 1
- Within User Story 2: Tasks T003 and T004 are marked [P] and can be done simultaneously (different line numbers in same file)
- All validation tasks in Phase 4 marked [P] can run in parallel (different browsers, different test scenarios)

---

## Parallel Example: User Story 2

```bash
# Both header updates in User Story 2 can be done together:
Task T003: "Update login page header in frontend/src/App.tsx (line 69)"
Task T004: "Update authenticated app header in frontend/src/App.tsx (line 85)"

# All browser validation tasks can be launched together:
Task T005: "Validate title display in Chrome browser"
Task T006: "Validate title display in Firefox browser"
Task T007: "Validate title display in Safari browser"
Task T008: "Validate title display in Edge browser"
```

---

## Implementation Strategy

### MVP First (Both User Stories - High Priority)

Given the small scope of this feature, the MVP includes both user stories:

1. Complete Phase 1: Setup (verify project structure)
2. Complete Phase 2: User Story 1 (browser tab title) - **P1 priority**
3. Complete Phase 3: User Story 2 (UI header titles) - **P2 priority**
4. **STOP and VALIDATE**: Test both stories independently
5. Complete Phase 4: Cross-browser validation
6. Deploy/demo if ready

**Why both stories in MVP**: 
- User Story 1 and 2 combined deliver complete branding consistency
- Both are simple text replacements (3 lines total)
- Splitting them would create incomplete branding
- Total implementation time is minimal

### Incremental Delivery

1. Complete Setup → Foundation ready
2. Complete User Story 1 → Browser tab displays "GitHub Workflows" (independently testable)
3. Complete User Story 2 → UI headers display "GitHub Workflows" (independently testable)
4. Complete Validation → Cross-browser compatibility confirmed
5. Each story adds value and can be tested independently even though MVP includes both

### Parallel Team Strategy

With multiple developers (if needed):

1. Developer A: Complete Setup, then User Story 1 (browser tab title)
2. Developer B: Complete User Story 2 (UI header titles) after Setup
3. Both developers: Phase 4 validation tasks in parallel (different browsers)

However, given the small scope (3 text replacements), a single developer can complete this efficiently in sequence.

---

## Notes

- Total of 12 tasks across 4 phases
- 3 implementation tasks (T002, T003, T004) - all simple text replacements
- 8 validation tasks (T005-T012) to ensure quality and cross-browser compatibility
- [P] tasks = different files or different test scenarios, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently testable
- No tests requested in specification - relying on manual validation
- Commit after implementing each user story
- Focus on FR-001 through FR-005 compliance
- Verify all Success Criteria (SC-001 through SC-005) after implementation
