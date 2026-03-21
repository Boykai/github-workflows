# Tasks: Breadcrumb Deep Route Support

**Input**: Design documents from `/specs/054-breadcrumb-deep-routes/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT included — they were not explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` (frontend within monorepo)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project initialization needed — this feature is within the existing `solune/frontend/` web application.

*(No setup tasks — the project, build tooling, and dependency management already exist.)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the BreadcrumbContext infrastructure that MUST be complete before ANY user story can be implemented. The context provider and hook enable both the Breadcrumb component (reads labels) and page components (inject labels) to share state.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T001 Create BreadcrumbContextValue interface, BreadcrumbContext, BreadcrumbProvider component, and useBreadcrumb hook in `solune/frontend/src/hooks/useBreadcrumb.ts`
- [ ] T002 Import BreadcrumbProvider and wrap layout content (TopBar + Outlet) with it in `solune/frontend/src/layout/AppLayout.tsx`

**Checkpoint**: Foundation ready — BreadcrumbProvider is in the component tree and useBreadcrumb hook is available for both the Breadcrumb component and page components.

---

## Phase 3: User Story 1 — Full-Depth Breadcrumb Trail for Nested Routes (Priority: P1) 🎯 MVP

**Goal**: Parse every segment of the URL path and render a complete breadcrumb trail (e.g., "Home > Apps > my-cool-app" for `/apps/my-cool-app`) with clickable ancestor links.

**Independent Test**: Navigate to any route with 3+ path segments and verify the breadcrumb displays a segment for each level, with each ancestor segment being a clickable link and the last segment being plain text.

### Implementation for User Story 1

- [ ] T003 [P] [US1] Define BreadcrumbSegment interface (label, path, isCurrent) in `solune/frontend/src/layout/Breadcrumb.tsx`
- [ ] T004 [P] [US1] Implement toTitleCase(segment) helper that replaces hyphens with spaces and capitalizes each word in `solune/frontend/src/layout/Breadcrumb.tsx`
- [ ] T005 [US1] Implement buildSegments(pathname, routeLabels, dynamicLabels) pure function that splits pathname on "/", filters empties, strips trailing slashes, decodes URI components, builds cumulative paths, prepends Home segment, and marks last as isCurrent in `solune/frontend/src/layout/Breadcrumb.tsx`
- [ ] T006 [US1] Rewrite Breadcrumb component render to call buildSegments with current pathname and render full-depth trail — ancestor segments as clickable Link components, last segment as plain text in `solune/frontend/src/layout/Breadcrumb.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional — navigating to `/apps/my-cool-app` shows "Home > Apps > My Cool App" with clickable ancestors. Labels use title-cased fallback for all segments.

---

## Phase 4: User Story 2 — Dynamic Labels via Breadcrumb Context (Priority: P1)

**Goal**: Allow pages to inject human-readable labels into the breadcrumb via the BreadcrumbContext (e.g., showing "My Cool App" instead of the raw URL slug "my-cool-app").

**Independent Test**: Navigate to a page that resolves a dynamic parameter (e.g., app detail), verify the breadcrumb initially shows the raw segment, then updates to the friendly name once the page data loads and injects the label.

### Implementation for User Story 2

- [ ] T007 [US2] Wire Breadcrumb component to read dynamic labels Map from useBreadcrumb() context and pass it to buildSegments for label resolution in `solune/frontend/src/layout/Breadcrumb.tsx`
- [ ] T008 [US2] Add dynamic breadcrumb label injection in app detail page — call setLabel with app path and display name in useEffect, return removeLabel in cleanup in `solune/frontend/src/pages/AppsPage.tsx`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — deep routes show full trails, and pages can inject friendly labels that auto-clean on navigation.

---

## Phase 5: User Story 3 — Route Metadata Labels for Known Routes (Priority: P2)

**Goal**: Use labels from the NAV_ROUTES configuration for known route segments (e.g., `/apps` → "Apps") to ensure consistency between the sidebar navigation and breadcrumb trail, rather than relying solely on title-casing.

**Independent Test**: Navigate to any route whose path matches a known route in NAV_ROUTES (e.g., `/apps/some-app`) and verify the breadcrumb uses the configured label (e.g., "Apps") matching the sidebar.

### Implementation for User Story 3

- [ ] T009 [US3] Build static routeLabels Map from NAV_ROUTES (path → label) at module level in `solune/frontend/src/layout/Breadcrumb.tsx`
- [ ] T010 [US3] Add routeLabels lookup to buildSegments label resolution priority (dynamic labels → route metadata → title-case fallback) in `solune/frontend/src/layout/Breadcrumb.tsx`

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently — known route segments show configured labels, dynamic labels override when set, and unknown segments fall back to title-casing.

---

## Phase 6: User Story 4 — Accessible Breadcrumb Navigation (Priority: P2)

**Goal**: Make the breadcrumb fully accessible with semantic HTML structure, screen reader support, and keyboard navigation compliance per WAI-ARIA breadcrumb best practices.

**Independent Test**: Navigate to a deep route, use a screen reader to verify the breadcrumb announces as a navigation landmark, reads each segment in order, identifies the current page, and does not announce decorative separators.

### Implementation for User Story 4

- [ ] T011 [P] [US4] Change breadcrumb inner container from span-based layout to semantic `<ol>` with `<li>` children for proper list hierarchy in `solune/frontend/src/layout/Breadcrumb.tsx`
- [ ] T012 [US4] Add aria-current="page" attribute to the last breadcrumb segment and aria-hidden="true" to all separator icons in `solune/frontend/src/layout/Breadcrumb.tsx`

**Checkpoint**: All user stories should now be independently functional — full-depth trails, dynamic labels, route metadata labels, and full accessibility support.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling and final validation across all user stories

- [ ] T013 [P] Verify edge cases — trailing slashes, URI-encoded characters, UUID segments, empty segments, 404 routes — produce correct breadcrumb output in `solune/frontend/src/layout/Breadcrumb.tsx`
- [ ] T014 Run type-check (`npx tsc --noEmit`) and test suite (`npx vitest run`) per quickstart.md verification steps in `solune/frontend/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Skipped — existing project
- **Foundational (Phase 2)**: No dependencies — can start immediately. BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) and User Story 1 (Phase 3) — reads context in same component
- **User Story 3 (Phase 5)**: Depends on User Story 1 (Phase 3) — extends buildSegments label resolution
- **User Story 4 (Phase 6)**: Depends on User Story 1 (Phase 3) — restructures the rendered output
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — core path parsing, no other story dependencies
- **User Story 2 (P1)**: Depends on US1 (buildSegments must exist to wire dynamic labels into) — independently testable once wired
- **User Story 3 (P2)**: Depends on US1 (extends buildSegments with route lookup) — independently testable
- **User Story 4 (P2)**: Depends on US1 (restructures rendered output) — can proceed in parallel with US2/US3

### Within Each User Story

- Types/interfaces before implementation functions
- Pure functions before component integration
- Core implementation before integration with other stories
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 2**: T001 and T002 are sequential (T002 imports from T001)
- **Phase 3**: T003 and T004 can run in parallel (independent type + helper in same file, different code sections)
- **Phase 4**: T007 and T008 are sequential (T008 uses the wiring from T007)
- **Phase 5**: T009 and T010 are sequential (T010 uses the Map from T009)
- **Phase 6**: T011 can run in parallel with Phase 4 or Phase 5 (independent structural change)
- **Cross-phase**: US3 (Phase 5) and US4 (Phase 6) can proceed in parallel after US1 is complete

---

## Parallel Example: User Story 1

```bash
# Launch type + helper in parallel (different code sections, no dependencies):
Task T003: "Define BreadcrumbSegment interface in solune/frontend/src/layout/Breadcrumb.tsx"
Task T004: "Implement toTitleCase helper in solune/frontend/src/layout/Breadcrumb.tsx"

# Then sequentially:
Task T005: "Implement buildSegments() (depends on T003 type + T004 helper)"
Task T006: "Rewrite Breadcrumb render (depends on T005)"
```

## Parallel Example: Cross-Phase

```bash
# After US1 (Phase 3) is complete, these phases can proceed in parallel:
Phase 5 (US3): "Route metadata labels — extends buildSegments"
Phase 6 (US4): "Accessibility — restructures rendered HTML"
# US2 (Phase 4) should be done first since it's P1 priority
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (BreadcrumbProvider + hook)
2. Complete Phase 3: User Story 1 (full-depth path parsing + rendering)
3. **STOP and VALIDATE**: Navigate to `/apps/my-cool-app` — should see "Home > Apps > My Cool App"
4. Deploy/demo if ready — basic deep breadcrumb is functional

### Incremental Delivery

1. Complete Foundational → Context infrastructure ready
2. Add User Story 1 → Full-depth trails work → Deploy/Demo (MVP!)
3. Add User Story 2 → Pages can inject friendly labels → Deploy/Demo
4. Add User Story 3 → Known routes use configured labels → Deploy/Demo
5. Add User Story 4 → Full accessibility compliance → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (must complete first — other stories extend it)
3. Once US1 is done:
   - Developer A: User Story 2 (P1 priority)
   - Developer B: User Story 3 + User Story 4 in parallel (both P2, independent)
4. Stories integrate cleanly since they modify different aspects of the same component

---

## Notes

- [P] tasks = different files or independent code sections, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests were NOT requested in the feature specification — omitted per Test Optionality principle
- All changes are frontend-only (no backend/API changes)
- Only 3 source files affected: 1 new (`useBreadcrumb.ts`), 2 modified (`Breadcrumb.tsx`, `AppLayout.tsx`), plus 1 example integration (`AppsPage.tsx`)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
