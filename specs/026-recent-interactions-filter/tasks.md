# Tasks: Recent Interactions — Filter Deleted Items & Display Only Parent Issues with Project Board Status Colors

**Input**: Design documents from `/specs/026-recent-interactions-filter/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/components.md ✅, quickstart.md ✅

**Tests**: Not explicitly requested in the feature specification. Existing tests must continue to pass. No new test tasks are included.

**Organization**: Tasks are grouped by user story (US1–US4) from spec.md to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (all changes frontend-only, no backend modifications)

---

## Phase 1: Setup

**Purpose**: No new project initialization is needed — this feature modifies 3 existing files and introduces no new dependencies.

- [x] T001 Verify existing source files are accessible and review current implementations: `frontend/src/types/index.ts` (RecentInteraction interface), `frontend/src/hooks/useRecentParentIssues.ts` (hook logic), `frontend/src/layout/Sidebar.tsx` (rendering), `frontend/src/components/board/colorUtils.ts` (color utilities)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend the shared `RecentInteraction` type with status fields required by US3 (status colors). This type change must be in place before any hook or rendering modifications.

**⚠️ CRITICAL**: US3 rendering and hook status-capture tasks depend on this type extension being complete.

- [x] T002 Add `status: string` and `statusColor: StatusColor` fields to the `RecentInteraction` interface in `frontend/src/types/index.ts`. The `status` field holds the project board column name (e.g., "In Progress", "Done") and `statusColor` holds the `StatusColor` enum value from `BoardStatusOption.color`. Import `StatusColor` type if not already imported in the same file.

**Checkpoint**: `RecentInteraction` type updated — hook and rendering changes can now begin.

---

## Phase 3: User Story 1 — Automatic Removal of Deleted Items (Priority: P1) 🎯 MVP

**Goal**: Deleted issues (via Clean Up or any other method) no longer appear in the Recent Interactions panel. The hook derives its list exclusively from live `BoardDataResponse` data, so items removed from the project board are implicitly excluded.

**Independent Test**: Delete an issue via Clean Up or directly on GitHub, wait for board data to refresh (automatic polling via `useBoardRefresh`), then verify the deleted item no longer appears in the Recent Interactions sidebar.

### Implementation for User Story 1

- [x] T003 [US1] Refactor `useRecentParentIssues` hook in `frontend/src/hooks/useRecentParentIssues.ts` to iterate `boardData.columns` with a nested column→items loop (instead of the current `flatMap`) so that each item retains its parent column context. Return `[]` when `boardData` is null. Only items currently present in the `BoardDataResponse` are included in the output — items deleted from the project board or GitHub are automatically excluded. Preserve existing deduplication by `item_id` via `Set<string>` and the `MAX_RECENT = 8` limit.

**Checkpoint**: Deleted items are automatically excluded from Recent Interactions. The panel shows only items that exist in the current board data. Verify by deleting an issue and confirming it disappears after board data refresh.

---

## Phase 4: User Story 2 — Display Only Parent Issues (Priority: P1)

**Goal**: The Recent Interactions panel shows ONLY GitHub Issue Parent Issues. Sub-issues, pull requests, draft issues, and all other non-parent item types are excluded.

**Independent Test**: Interact with a mix of parent issues, sub-issues, pull requests, and draft issues, then verify only parent issues appear in the Recent Interactions panel.

### Implementation for User Story 2

- [x] T004 [US2] Add a `content_type === 'issue'` filter to the item iteration in `useRecentParentIssues` in `frontend/src/hooks/useRecentParentIssues.ts`. Skip any item where `item.content_type` is `'draft_issue'` or `'pull_request'`. This ensures only GitHub Issues (not PRs or drafts) appear in the Recent Interactions list (FR-004).

- [x] T005 [US2] Build a `Set<number>` of all sub-issue numbers by iterating every `BoardItem.sub_issues` array across all columns at the start of the `useMemo` computation in `frontend/src/hooks/useRecentParentIssues.ts`. During the main item iteration, skip any item whose `number` is present in this sub-issue set. This ensures only parent issues (top-level issues that are not sub-issues of another issue) are included (FR-005).

**Checkpoint**: Only parent issues appear in Recent Interactions. Sub-issues, PRs, and draft issues are excluded. Verify by checking that items with `content_type !== 'issue'` or items whose `number` appears in another item's `sub_issues` array do not appear in the sidebar.

---

## Phase 5: User Story 3 — Project Board Status Colors (Priority: P2)

**Goal**: Each Parent Issue in the Recent Interactions panel displays a colored left-border accent that corresponds to its current project board status column. Colors update automatically when an issue moves to a different column.

**Independent Test**: Place parent issues in different project board columns (Todo, In Progress, Done, etc.) and verify each displays the correct corresponding color in the sidebar. Move an issue to a different column and confirm the color updates after board data refresh.

### Implementation for User Story 3

- [x] T006 [US3] During the column→items iteration in `useRecentParentIssues` in `frontend/src/hooks/useRecentParentIssues.ts`, capture `column.status.name` as the `status` field and `column.status.color` (with fallback to `'GRAY'` via nullish coalescing `?? 'GRAY'`) as the `statusColor` field on each `RecentInteraction` object. This populates the new type fields added in T002 (FR-006, FR-007, FR-010).

- [x] T007 [US3] Import `statusColorToCSS` from `@/components/board/colorUtils` in `frontend/src/layout/Sidebar.tsx`. Add a `border-l-2` class and inline `style={{ borderLeftColor: statusColorToCSS(item.statusColor) }}` to each recent interaction `<button>` element, rendering a colored left-border accent that reflects the item's project board status (FR-007, FR-008). Research decision R4 specifies left border accent as the rendering strategy.

- [x] T008 [US3] Update the `title` attribute on each recent interaction button in `frontend/src/layout/Sidebar.tsx` to include the status name, formatted as `"{item.title} — {item.status}"` (e.g., "Fix login bug — In Progress"). This provides additional context on hover (contracts/components.md rendering contract item 4).

**Checkpoint**: Each recent interaction entry displays a colored left border matching its board column status. Hovering shows the status name in the tooltip. Colors update automatically when board data refreshes. Items with no status show a neutral gray border.

---

## Phase 6: User Story 4 — Empty State Messaging (Priority: P3)

**Goal**: When no valid Parent Issues exist in Recent Interactions (all deleted, all sub-issues, or no interactions), a clear empty state message is displayed instead of a blank space.

**Independent Test**: Ensure no valid parent issues exist in Recent Interactions (empty board, all sub-issues, or all deleted) and verify the empty state message "No recent parent issues" appears.

### Implementation for User Story 4

- [x] T009 [US4] Update the empty state text in the Recent Interactions section of `frontend/src/layout/Sidebar.tsx` from `"No recent activity"` to `"No recent parent issues"` to accurately reflect the filtered behavior (FR-009, research decision R5).

**Checkpoint**: When `recentInteractions.length === 0`, the sidebar displays "No recent parent issues" instead of "No recent activity". Verify by selecting a project with no parent issues in the board data.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate that all changes compile, pass linting, and pass existing tests. Run quickstart.md verification steps.

- [x] T010 [P] Verify TypeScript compilation passes with `npx tsc --noEmit` in `frontend/`
- [x] T011 [P] Verify existing linting passes with `npm run lint` in `frontend/`
- [x] T012 [P] Verify existing unit tests pass with `npm run test` in `frontend/`
- [ ] T013 Run quickstart.md verification steps to validate all acceptance scenarios end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — review only
- **Foundational (Phase 2)**: No dependencies — type change blocks US3 hook/rendering tasks
- **US1 (Phase 3)**: Depends on Phase 2 (type fields must exist). Refactors the hook iteration to column-aware loop.
- **US2 (Phase 4)**: Depends on Phase 3 (builds on the refactored iteration loop from T003)
- **US3 (Phase 5)**: Depends on Phase 2 (type fields) and Phase 3 (column-aware iteration). T007, T008 depend on T006 (hook must provide data before Sidebar can render it).
- **US4 (Phase 6)**: No code dependencies — can be done at any point after Phase 1. Text-only change in Sidebar.
- **Polish (Phase 7)**: Depends on all implementation phases being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2). Establishes the column-aware iteration pattern used by US2 and US3.
- **US2 (P1)**: Builds on US1's refactored iteration loop. Can start after US1 is complete.
- **US3 (P2)**: Builds on US1's column-aware iteration (needs column context for status color). Can start after US1. Hook changes (T006) must precede Sidebar changes (T007, T008).
- **US4 (P3)**: Independent of other stories — text-only change. Can be done any time.

### Within Each User Story

- Hook changes before Sidebar rendering changes (data must be available before it can be rendered)
- Type changes (Foundational) before hook changes
- Core filtering before color enhancement

### Parallel Opportunities

- **T010, T011, T012** can all run in parallel (independent validation commands)
- **US2 and US3** hook changes (T004–T006) operate on the same iteration loop but add independent filter/capture logic — they could be implemented in a single pass if desired
- **US4 (T009)** is independent and can run in parallel with any other phase

---

## Parallel Example: User Story 3

```text
# Sequential dependency within US3:
T006: Capture status/statusColor in hook (frontend/src/hooks/useRecentParentIssues.ts)
  ↓ (hook must provide data first)
T007: Render border-l-2 with statusColorToCSS in Sidebar (frontend/src/layout/Sidebar.tsx)
T008: Update title attribute with status name in Sidebar (frontend/src/layout/Sidebar.tsx)

# T007 and T008 modify the same Sidebar file but different attributes of the same element.
# They should be done sequentially to avoid merge conflicts.
```

---

## Parallel Example: Polish Phase

```text
# All three validation tasks can run simultaneously:
T010: npx tsc --noEmit (TypeScript check)
T011: npm run lint (ESLint check)
T012: npm run test (Vitest unit tests)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (type extension — T002)
2. Complete Phase 3: US1 — Deleted item filtering (T003)
3. **STOP and VALIDATE**: Board data is source of truth; deleted items don't appear
4. This alone delivers the most critical data-integrity fix

### Incremental Delivery

1. **T002** → Type extension ready
2. **T003** → US1 complete: Deleted items filtered ✅ (MVP!)
3. **T004, T005** → US2 complete: Parent issues only ✅
4. **T006, T007, T008** → US3 complete: Status colors rendered ✅
5. **T009** → US4 complete: Empty state updated ✅
6. **T010–T013** → Polish: All validations pass ✅
7. Each story adds value without breaking previous stories

### Single Developer Strategy

Since all changes touch only 3 files (~150 LOC), a single developer should:

1. Complete T002 (types) first
2. Implement T003–T005 in one pass through the hook file
3. Implement T006–T009 in one pass through the Sidebar file
4. Run T010–T012 validation in parallel
5. Total estimated time: ~4–6 hours of focused work

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 13 |
| **Foundational** | 1 task (T002) |
| **US1 tasks** | 1 task (T003) |
| **US2 tasks** | 2 tasks (T004–T005) |
| **US3 tasks** | 3 tasks (T006–T008) |
| **US4 tasks** | 1 task (T009) |
| **Polish tasks** | 4 tasks (T010–T013) |
| **Files modified** | 3 (`types/index.ts`, `useRecentParentIssues.ts`, `Sidebar.tsx`) |
| **Net LOC change** | ~150 |
| **Parallel opportunities** | T010+T011+T012 (validation), T009 (independent of other stories) |
| **Suggested MVP scope** | US1 only (T002 + T003) — deleted item filtering |

---

## Notes

- [P] tasks = different files, no dependencies — can run in parallel
- [Story] label maps each task to a specific user story for traceability
- Each user story is independently testable per spec.md acceptance scenarios
- No new npm dependencies required — all existing utilities reused
- No backend changes — all data comes from existing `BoardDataResponse`
- `statusColorToCSS()` and `statusColorToBg()` from `colorUtils.ts` handle all color mapping including GRAY fallback
- Commit after each task or logical group (e.g., all hook changes, all Sidebar changes)
- Stop at any checkpoint to validate the story independently
