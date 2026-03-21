# Tasks: Breadcrumb Deep Route Support

**Input**: Design documents from `/specs/055-breadcrumb-deep-routes/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Existing Vitest suite validates no regressions. Tests can be added separately if desired.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` — frontend-only changes; no backend modifications needed

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new files and foundational types required by all subsequent phases

- [ ] T001 Create `solune/frontend/src/lib/breadcrumb-utils.ts` with `BreadcrumbSegment` interface (`label: string`, `path: string`) and `toTitleCase(slug: string): string` utility that splits on hyphens/underscores, capitalizes each word, and joins with spaces
- [ ] T002 [P] Create `solune/frontend/src/hooks/useBreadcrumb.ts` with `BreadcrumbContext` (React Context holding `Map<string, string>`), `BreadcrumbProvider` component (manages labels state via `useState`), `useBreadcrumb()` hook (returns `{ setLabel, removeLabel }` with stable `useCallback` references), and `useBreadcrumbLabels()` hook (returns the labels `Map` for read-only consumption)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire the BreadcrumbProvider into the component tree so all user story implementations have access to the shared context

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Wrap `<TopBar />` and `<Outlet />` (main content area) with `<BreadcrumbProvider>` in `solune/frontend/src/layout/AppLayout.tsx` — import `BreadcrumbProvider` from `@/hooks/useBreadcrumb` and ensure both the Breadcrumb consumer (inside TopBar) and page producers (inside Outlet) share the same context instance

**Checkpoint**: Foundation ready — BreadcrumbProvider is in the component tree; user story implementation can now begin

---

## Phase 3: User Story 1 — Multi-Segment Breadcrumb Trail (Priority: P1) 🎯 MVP

**Goal**: Parse the current URL pathname into individual path segments and render a breadcrumb item for each segment, preceded by "Home," with clickable intermediate links and a non-clickable final segment

**Independent Test**: Navigate to any route deeper than one segment (e.g., `/apps/my-cool-app`) and verify the breadcrumb renders all intermediate segments as clickable links, with the final segment displayed as plain text

### Implementation for User Story 1

- [ ] T004 [US1] Implement `buildBreadcrumbSegments(pathname, navRoutes, labelOverrides)` in `solune/frontend/src/lib/breadcrumb-utils.ts` — always starts with `{ label: 'Home', path: '/' }`, strips trailing slashes, splits pathname on `/`, filters empty segments, builds cumulative paths, resolves labels via three-tier resolution (context overrides → NAV_ROUTES match → toTitleCase fallback), returns `BreadcrumbSegment[]`
- [ ] T005 [US1] Rewrite `solune/frontend/src/layout/Breadcrumb.tsx` to use `buildBreadcrumbSegments()` and `useBreadcrumbLabels()` — import `buildBreadcrumbSegments` from `@/lib/breadcrumb-utils`, import `useBreadcrumbLabels` from `@/hooks/useBreadcrumb`, call `buildBreadcrumbSegments(pathname, NAV_ROUTES, labelOverrides)`, render all segments with `ChevronRight` separators, non-final segments as `<Link>` components, final segment as plain `<span>` with `font-medium` styling

**Checkpoint**: At this point, navigating to `/apps` shows "Home > Apps" (preserved behavior), and navigating to `/apps/my-cool-app` shows "Home > Apps > My Cool App" (title-case fallback). User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 — Dynamic Labels via Breadcrumb Context (Priority: P1)

**Goal**: Allow page components to register human-readable breadcrumb labels for dynamic path segments so the breadcrumb shows entity names (e.g., "My Cool App") instead of raw URL slugs

**Independent Test**: Navigate to a detail page whose component sets a breadcrumb label via the context. Verify the breadcrumb displays the human-readable label rather than the raw URL segment. Navigate away and verify the label is cleaned up.

### Implementation for User Story 2

- [ ] T006 [US2] Add dynamic breadcrumb label registration in `solune/frontend/src/pages/AppsPage.tsx` — import `useBreadcrumb` from `@/hooks/useBreadcrumb`, call `setLabel('/apps/<appName>', displayName)` inside a `useEffect` when the app detail view renders, use `app?.display_name ?? toTitleCase(appName)` as the label, return `() => removeLabel(path)` from the useEffect cleanup to prevent label leakage across routes

**Checkpoint**: At this point, navigating to `/apps/my-cool-app` shows "Home > Apps > My Cool App" using the app's actual display name from the API response. Navigating away cleans up the label. User Story 2 is fully functional and independently testable.

---

## Phase 5: User Story 3 — Three-or-More-Level Routes (Priority: P2)

**Goal**: Support breadcrumb trails for routes with three or more path segments (e.g., `/apps/my-cool-app/settings` → "Home > Apps > My Cool App > Settings")

**Independent Test**: Navigate to a route with three or more segments and verify all intermediate segments appear as clickable links in the correct order

**Note**: This user story is inherently satisfied by the `buildBreadcrumbSegments` implementation in Phase 3 (T004), which iterates over all path parts without a depth limit. This phase validates depth support and handles any depth-specific edge cases.

### Implementation for User Story 3

- [ ] T007 [US3] Verify that `buildBreadcrumbSegments` in `solune/frontend/src/lib/breadcrumb-utils.ts` correctly handles paths with 3, 4, and 5 segments — confirm the `for` loop iterates over `parts.length` without a hard-coded limit, cumulative paths build correctly at each depth level, and label resolution applies at every segment

**Checkpoint**: Breadcrumb renders correctly for arbitrary-depth routes. All segments except the last are clickable. User Story 3 is satisfied by the Phase 3 implementation.

---

## Phase 6: User Story 4 — Static Route Label Resolution (Priority: P2)

**Goal**: Ensure the breadcrumb uses human-readable labels from the application's route configuration (NAV_ROUTES) for known static routes, keeping breadcrumb labels consistent with the sidebar navigation menu

**Independent Test**: Navigate to a static route (e.g., `/apps`, `/settings`, `/tools`) and verify the breadcrumb uses the label from NAV_ROUTES rather than a title-cased slug

**Note**: This user story is inherently satisfied by the three-tier resolution in `buildBreadcrumbSegments` (Phase 3, T004), which checks NAV_ROUTES as the second-tier label source. This phase validates label consistency.

### Implementation for User Story 4

- [ ] T008 [US4] Verify that `buildBreadcrumbSegments` in `solune/frontend/src/lib/breadcrumb-utils.ts` resolves all 9 NAV_ROUTES entries (`/`, `/projects`, `/pipeline`, `/agents`, `/tools`, `/chores`, `/apps`, `/activity`, `/settings`) using exact path matching (`r.path === cumulativePath`) and confirm labels match sidebar navigation labels

**Checkpoint**: All known static routes display breadcrumb labels consistent with the sidebar navigation. Unknown segments fall back to title-casing. User Story 4 is satisfied by the Phase 3 implementation.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling and validation across all user stories

- [ ] T009 [P] Ensure trailing slash normalization in `buildBreadcrumbSegments` in `solune/frontend/src/lib/breadcrumb-utils.ts` — `/apps/` and `/apps` must produce identical output per FR-011; multiple trailing slashes must also be normalized
- [ ] T010 [P] Verify query parameter and hash fragment handling — `useLocation().pathname` in `solune/frontend/src/layout/Breadcrumb.tsx` excludes query strings and hash fragments by default per FR-010; confirm no additional stripping is needed
- [ ] T011 [P] Validate label cleanup lifecycle in `solune/frontend/src/hooks/useBreadcrumb.ts` — ensure `removeLabel` deletes the Map entry, `useEffect` cleanup fires on unmount, and no stale labels leak across route navigations per FR-008
- [ ] T012 Run quickstart.md validation: `cd solune/frontend && npm run lint && npm run type-check && npx vitest run`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T002 creates the provider that T003 wires in)
- **User Story 1 (Phase 3)**: Depends on Phase 1 (T001 for toTitleCase) and Phase 2 (T003 for provider in tree)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (T003 for provider) and Phase 3 (T005 for breadcrumb rendering)
- **User Story 3 (Phase 5)**: Satisfied by Phase 3 implementation — validation only
- **User Story 4 (Phase 6)**: Satisfied by Phase 3 implementation — validation only
- **Polish (Phase 7)**: Depends on Phase 3 completion; can overlap with Phases 5–6

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 3 — requires Breadcrumb.tsx rewrite to consume context labels
- **User Story 3 (P2)**: No new implementation — validated against Phase 3 output
- **User Story 4 (P2)**: No new implementation — validated against Phase 3 output

### Within Each User Story

- Models/types before utility functions
- Utility functions before component integration
- Context infrastructure before consumers
- Core implementation before page integration
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 can run in parallel (different files: `breadcrumb-utils.ts` vs `useBreadcrumb.ts`)
- T009, T010, T011 can run in parallel (different files, independent edge cases)
- Once Phase 2 completes, US1 and US2 setup work can overlap if US2 doesn't depend on the rewritten Breadcrumb
- US3 and US4 validation can run in parallel

---

## Parallel Example: Phase 1

```bash
# Launch both setup tasks together (different files, no dependencies):
Task T001: "Create BreadcrumbSegment interface and toTitleCase in solune/frontend/src/lib/breadcrumb-utils.ts"
Task T002: "Create BreadcrumbContext, BreadcrumbProvider, hooks in solune/frontend/src/hooks/useBreadcrumb.ts"
```

## Parallel Example: Phase 7

```bash
# Launch all polish tasks together (different files, independent concerns):
Task T009: "Trailing slash normalization in solune/frontend/src/lib/breadcrumb-utils.ts"
Task T010: "Query/hash handling verification in solune/frontend/src/layout/Breadcrumb.tsx"
Task T011: "Label cleanup lifecycle validation in solune/frontend/src/hooks/useBreadcrumb.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001, T002)
2. Complete Phase 2: Foundational (T003)
3. Complete Phase 3: User Story 1 (T004, T005)
4. **STOP and VALIDATE**: Navigate to `/apps/my-cool-app` — should show "Home > Apps > My Cool App"
5. Deploy/demo if ready — basic multi-segment breadcrumb is functional

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (T004–T005) → Multi-segment breadcrumbs work → Deploy/Demo (MVP!)
3. Add User Story 2 (T006) → Dynamic labels from API data → Deploy/Demo
4. Validate User Story 3 (T007) → Arbitrary depth confirmed
5. Validate User Story 4 (T008) → NAV_ROUTES label consistency confirmed
6. Polish (T009–T012) → Edge cases handled, full validation complete

### File Change Summary

| File | Change | Phase |
|------|--------|-------|
| `solune/frontend/src/lib/breadcrumb-utils.ts` | **NEW** | Phase 1 (T001) + Phase 3 (T004) |
| `solune/frontend/src/hooks/useBreadcrumb.ts` | **NEW** | Phase 1 (T002) |
| `solune/frontend/src/layout/AppLayout.tsx` | **MODIFY** | Phase 2 (T003) |
| `solune/frontend/src/layout/Breadcrumb.tsx` | **MODIFY** | Phase 3 (T005) |
| `solune/frontend/src/pages/AppsPage.tsx` | **MODIFY** | Phase 4 (T006) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No new npm dependencies — uses built-in React Context, existing React Router hooks, existing NAV_ROUTES constant
- Frontend-only feature — no backend changes, no API endpoints, no database changes
- US3 and US4 are satisfied by US1's core implementation (`buildBreadcrumbSegments` handles arbitrary depth and NAV_ROUTES lookup inherently) — their phases are validation checkpoints
