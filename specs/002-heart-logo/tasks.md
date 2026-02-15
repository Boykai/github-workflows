# Tasks: Heart Logo on Homepage

**Input**: Design documents from `/specs/002-heart-logo/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - not explicitly requested in the feature specification, so test tasks are not included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Paths shown below reflect the actual project structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and asset preparation

- [ ] T001 Verify frontend development environment is functional (can run `npm run dev`)
- [ ] T002 Create frontend/public/ directory if it doesn't exist
- [ ] T003 Create heart-logo.svg file in frontend/public/heart-logo.svg (SVG format, <10KB, with viewBox attribute)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Verify existing App.tsx login section structure (lines 68-71 in frontend/src/App.tsx)
- [ ] T005 Verify existing App.css contains .app-login styles (frontend/src/App.css)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Brand Recognition on Homepage (Priority: P1) 🎯 MVP

**Goal**: Display heart logo at top center of homepage above main content, establishing visual brand identity

**Independent Test**: Load the homepage (login page) and verify the heart logo is visible at the top center, delivering immediate brand recognition

### Implementation for User Story 1

- [ ] T006 [US1] Add img element for heart logo to login section in frontend/src/App.tsx (insert as first child in .app-login div before h1)
- [ ] T007 [US1] Add src attribute pointing to /heart-logo.svg in frontend/src/App.tsx
- [ ] T008 [US1] Add alt attribute with descriptive text "Heart logo - Tech Connect 2026" in frontend/src/App.tsx
- [ ] T009 [US1] Add className="logo" attribute to img element in frontend/src/App.tsx
- [ ] T010 [P] [US1] Create .logo CSS class in frontend/src/App.css with basic positioning (display: block, margin: 0 auto)
- [ ] T011 [US1] Verify logo displays at top center on homepage by running dev server and visually inspecting
- [ ] T012 [US1] Verify logo appears above "Welcome to Tech Connect 2026!" heading

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - logo visible at top center of homepage

---

## Phase 4: User Story 2 - Responsive Logo Display (Priority: P2)

**Goal**: Ensure logo displays correctly and maintains visual quality on all screen sizes (mobile, tablet, desktop)

**Independent Test**: Load homepage on different viewport sizes (mobile 320px-767px, tablet 768px-1023px, desktop 1024px+) and verify logo scales appropriately and maintains visual quality

### Implementation for User Story 2

- [ ] T013 [P] [US2] Add responsive width sizing using clamp(60px, 10vw, 120px) to .logo class in frontend/src/App.css
- [ ] T014 [P] [US2] Add height: auto to .logo class in frontend/src/App.css to maintain aspect ratio
- [ ] T015 [P] [US2] Add bottom margin (1.5rem) to .logo class in frontend/src/App.css for spacing
- [ ] T016 [US2] Add mobile media query (@media max-width: 768px) with adjusted logo sizing to frontend/src/App.css
- [ ] T017 [US2] Test mobile viewport (375px) and verify logo scales appropriately without distortion
- [ ] T018 [US2] Test tablet viewport (768px) and verify logo scales appropriately
- [ ] T019 [US2] Test desktop viewport (1920px) and verify logo not overly large
- [ ] T020 [US2] Test browser window resize and verify logo adapts smoothly

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - logo visible and responsive across all screen sizes

---

## Phase 5: User Story 3 - Accessible Logo (Priority: P3)

**Goal**: Provide descriptive alternative text for logo so assistive technology users can understand the branding element

**Independent Test**: Inspect logo element with screen reader tools and verify appropriate alt text is present and announced

### Implementation for User Story 3

- [ ] T021 [US3] Verify alt attribute is present and descriptive (already added in T008, confirm it meets accessibility standards)
- [ ] T022 [P] [US3] Add high contrast mode support with media query (@media prefers-contrast: high) in frontend/src/App.css
- [ ] T023 [US3] Test with screen reader (VoiceOver/Narrator) and verify alt text is announced correctly
- [ ] T024 [US3] Test image load failure by temporarily renaming logo file and verify alt text displays gracefully
- [ ] T025 [US3] Test with 200% page zoom and verify logo scales without pixelation

**Checkpoint**: All user stories should now be independently functional - logo is visible, responsive, and accessible

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T026 [P] Test logo in Chrome browser and verify correct display
- [ ] T027 [P] Test logo in Firefox browser and verify correct display
- [ ] T028 [P] Test logo in Safari browser and verify correct display (if available)
- [ ] T029 [P] Test logo in Edge browser and verify correct display (if available)
- [ ] T030 [P] Test edge case: extremely small screen (<320px) and verify logo still visible
- [ ] T031 [P] Verify logo is non-interactive (clicking does nothing, no cursor: pointer)
- [ ] T032 Run quickstart.md final validation checklist
- [ ] T033 Verify no TypeScript or linting errors in frontend code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1 but independently testable (US1 should be complete first for incremental delivery)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Builds on US1 (verifies US1 implementation) but independently testable

### Within Each User Story

- **User Story 1**: T006-T009 (JSX changes) should be done together, T010 (CSS) can be parallel, T011-T012 (verification) must be sequential after implementation
- **User Story 2**: T013-T015 (CSS styling) can be done in parallel, T016 (media query) sequential after base styles, T017-T020 (testing) sequential after CSS complete
- **User Story 3**: T021 (verification) first, T022 (CSS) can be parallel, T023-T025 (testing) sequential after implementation

### Parallel Opportunities

- All Setup tasks (T001-T003) can potentially run in parallel if environment is ready
- All Foundational tasks (T004-T005) are verification tasks and can run in parallel
- Within User Story 1: T010 (CSS) can be done in parallel with T006-T009 (JSX) since they're in different files
- Within User Story 2: T013-T015 (CSS properties) can be done in parallel (same file but non-conflicting properties)
- Within User Story 3: T022 (CSS) can be done in parallel with T021 (verification)
- All Polish tasks (T026-T031) are independent browser tests and can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch JSX modifications and CSS creation together:
Task T006-T009: "Modify App.tsx to add img element with all required attributes"
Task T010: "Create .logo CSS class in App.css"

# After both complete, run verification:
Task T011: "Verify logo displays at top center"
Task T012: "Verify logo appears above heading"
```

---

## Parallel Example: User Story 2

```bash
# Launch all CSS property additions together (different properties, same file):
Task T013: "Add width: clamp() to .logo"
Task T014: "Add height: auto to .logo"
Task T015: "Add margin-bottom to .logo"

# After base styles complete:
Task T016: "Add mobile media query"

# After CSS complete, launch all viewport tests together:
Task T017: "Test mobile 375px"
Task T018: "Test tablet 768px"
Task T019: "Test desktop 1920px"
Task T020: "Test window resize"
```

---

## Parallel Example: Polish Phase

```bash
# Launch all browser tests together (independent):
Task T026: "Test Chrome"
Task T027: "Test Firefox"
Task T028: "Test Safari"
Task T029: "Test Edge"
Task T030: "Test edge case <320px"
Task T031: "Verify non-interactive"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (logo visible at top center)
5. Demo/review if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (MVP!)
3. Add User Story 2 → Test independently → Demo (Responsive!)
4. Add User Story 3 → Test independently → Demo (Accessible!)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (T006-T012)
   - Developer B: Prepare for User Story 2 (research responsive patterns)
   - Developer C: Prepare accessibility testing tools
3. After US1 complete:
   - Developer A: User Story 2 (T013-T020)
   - Developer B: User Story 3 (T021-T025)
   - Developer C: Polish tasks (T026-T033)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files or non-conflicting properties, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each phase or logical group
- Stop at any checkpoint to validate story independently
- Total estimated time: ~1 hour (matches spec metadata: 2.0h estimate including testing and documentation)
- No automated tests required (tests not explicitly requested in spec)
- Focus on manual visual verification and browser testing
