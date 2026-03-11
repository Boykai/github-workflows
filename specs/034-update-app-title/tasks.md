# Tasks: Update App Title to "Hello World"

**Input**: Design documents from `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/`
**Prerequisites**: `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/plan.md` (required), `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/spec.md` (required), `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/research.md`, `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/data-model.md`, `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/contracts/`, `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/quickstart.md`

**Tests**: The feature specification does not request a TDD workflow, so no dedicated test-authoring tasks are included. Existing frontend validation commands and the quickstart checklist must pass after implementation.

**Organization**: Tasks are grouped by user story so each story can be implemented, validated, and delivered independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: Which user story this task belongs to (for example, `US1`, `US2`, `US3`)
- Every task below includes exact repository file paths

## Path Conventions

- **Repository root**: `/home/runner/work/github-workflows/github-workflows`
- **Frontend app**: `/home/runner/work/github-workflows/github-workflows/frontend/`
- **Feature docs**: `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/`

---

## Phase 1: Setup

**Purpose**: Confirm the exact user-facing branding surfaces and guardrails before editing files.

- [ ] T001 Confirm the in-scope branding replacements and preserved taglines in `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/research.md` and `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/quickstart.md`

**Checkpoint**: The implementation scope is limited to the approved user-facing title surfaces and excludes comments, test fixtures, and internal identifiers.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared search baseline that all user stories depend on before changing visible copy.

**⚠️ CRITICAL**: No user story work should begin until the approved replacement list is confirmed across the known frontend files.

- [ ] T002 Search `/home/runner/work/github-workflows/github-workflows/frontend/index.html`, `/home/runner/work/github-workflows/github-workflows/frontend/src/layout/Sidebar.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/LoginPage.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/SettingsPage.tsx` for in-scope `Solune` branding and preserve the out-of-scope references documented in `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/research.md`

**Checkpoint**: The exact set of user-facing strings to replace is frozen and can be implemented without touching unrelated branding references.

---

## Phase 3: User Story 1 - Browser Tab Shows Updated Title (Priority: P1) 🎯 MVP

**Goal**: Update the browser tab title so every page loads with `Hello World` in the document title.

**Independent Test**: Open the application in a browser, load any route, and verify the browser tab displays `Hello World`.

### Implementation for User Story 1

- [ ] T003 [US1] Replace `<title>Solune</title>` with `<title>Hello World</title>` in `/home/runner/work/github-workflows/github-workflows/frontend/index.html`

**Checkpoint**: The browser tab shows the new title without requiring any backend or environment-specific changes.

---

## Phase 4: User Story 2 - In-App Branding Displays Updated Title (Priority: P1)

**Goal**: Update the visible in-app branding surfaces so sidebar and page copy match the browser tab title while preserving existing taglines.

**Independent Test**: Load the app in logged-out and logged-in states and verify the sidebar, login page, and settings page all display `Hello World` in place of the old title.

### Implementation for User Story 2

- [ ] T004 [P] [US2] Update the sidebar brand label to `Hello World` in `/home/runner/work/github-workflows/github-workflows/frontend/src/layout/Sidebar.tsx` while keeping the `Sun & Moon` and `Guided solar orbit` taglines unchanged
- [ ] T005 [US2] Update the login page heading and opening branding sentence to `Hello World` in `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/LoginPage.tsx` while preserving the existing workspace badge and supporting copy
- [ ] T006 [P] [US2] Update the settings subtitle to `Configure your preferences for Hello World.` in `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/SettingsPage.tsx`

**Checkpoint**: All primary in-app branding surfaces display `Hello World` consistently without changing unrelated copy.

---

## Phase 5: User Story 3 - No Residual Old Branding (Priority: P2)

**Goal**: Eliminate any remaining in-scope user-facing `Solune` title references so the rebrand is complete.

**Independent Test**: Search the approved frontend surfaces and confirm no user-facing `Solune` strings remain after the edits land.

### Implementation for User Story 3

- [ ] T007 [US3] Re-scan `/home/runner/work/github-workflows/github-workflows/frontend/index.html`, `/home/runner/work/github-workflows/github-workflows/frontend/src/layout/Sidebar.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/LoginPage.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/SettingsPage.tsx` for residual user-facing `Solune` strings and clear any missed replacements before merge
- [ ] T008 [US3] Search `/home/runner/work/github-workflows/github-workflows/frontend/` for alternate user-facing title definitions or environment-specific overrides beyond the approved files and resolve any in-scope leftovers called out by `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/research.md`

**Checkpoint**: No user-facing title references to the old name remain in the frontend code paths covered by the specification.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Run the existing quality gates and manual acceptance checks for the completed title update.

- [ ] T009 [P] Run `npm run lint`, `npm run type-check`, `npm run test`, and `npm run build` in `/home/runner/work/github-workflows/github-workflows/frontend/` and resolve any failures caused by the branding edits
- [ ] T010 [P] Execute the verification checklist in `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/quickstart.md` against `/home/runner/work/github-workflows/github-workflows/frontend/index.html`, `/home/runner/work/github-workflows/github-workflows/frontend/src/layout/Sidebar.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/LoginPage.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/SettingsPage.tsx`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — blocks all user story work
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational completion and can proceed independently of US1 once the shared search baseline is set
- **User Story 3 (Phase 5)**: Depends on US1 and US2 completion because it verifies the combined branding surfaces
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependency Graph

```text
Setup -> Foundational -> {US1, US2}
US1 -> US3
US2 -> US3
US3 -> Polish
```

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational; it only changes `/home/runner/work/github-workflows/github-workflows/frontend/index.html`
- **US2 (P1)**: Independent after Foundational; it updates visible UI copy in `/home/runner/work/github-workflows/github-workflows/frontend/src/layout/Sidebar.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/LoginPage.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/SettingsPage.tsx`
- **US3 (P2)**: Depends on US1 and US2 so the final search and cleanup cover the full set of updated title surfaces

### Within Each User Story

- Confirm the approved replacement scope before editing strings
- Apply direct string replacements in the targeted file paths only
- Finish each story's independent validation before moving to the next dependent story
- Run the existing frontend quality checks and quickstart verification after all edits are complete

### Parallel Opportunities

- **US2**: T004 and T006 can run in parallel because they edit different files; T005 proceeds separately in `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/LoginPage.tsx`
- **Polish**: T009 and T010 can run in parallel once all file edits and residual-branding checks are complete

---

## Parallel Execution Examples

### User Story 1

```text
No safe same-story parallel split is recommended.
T003 is the only implementation task and should land on its own.
```

### User Story 2

```text
Task T004: Update sidebar branding in /home/runner/work/github-workflows/github-workflows/frontend/src/layout/Sidebar.tsx
Task T005: Update login branding copy in /home/runner/work/github-workflows/github-workflows/frontend/src/pages/LoginPage.tsx
Task T006: Update settings subtitle in /home/runner/work/github-workflows/github-workflows/frontend/src/pages/SettingsPage.tsx
```

### User Story 3

```text
No safe same-story parallel split is recommended.
T007 should confirm the approved files are clean before T008 broadens the frontend search for unexpected user-facing title overrides.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm the browser tab displays `Hello World`
5. Demo the renamed browser title before expanding to the rest of the UI

### Incremental Delivery

1. Complete Setup + Foundational to freeze the approved replacement scope
2. Add User Story 1 to update the browser tab title
3. Add User Story 2 to align in-app branding surfaces with the new title
4. Add User Story 3 to prove no residual in-scope old branding remains
5. Finish with Phase 6 quality checks and manual quickstart verification

### Parallel Team Strategy

With multiple developers:

1. One developer completes Setup + Foundational to lock the approved scope
2. Then split by file ownership:
   - Developer A: US1 in `/home/runner/work/github-workflows/github-workflows/frontend/index.html`
   - Developer B: US2 sidebar and settings updates in `/home/runner/work/github-workflows/github-workflows/frontend/src/layout/Sidebar.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/SettingsPage.tsx`
   - Developer C: US2 login copy update in `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/LoginPage.tsx`
3. Rejoin for US3 residual-branding search and Phase 6 validation

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 10 |
| **Setup tasks** | 1 (T001) |
| **Foundational tasks** | 1 (T002) |
| **US1 tasks** | 1 (T003) |
| **US2 tasks** | 3 (T004-T006) |
| **US3 tasks** | 2 (T007-T008) |
| **Polish tasks** | 2 (T009-T010) |
| **Parallel opportunities** | 4 tasks marked `[P]` across the US2 file splits and final validation |
| **Suggested MVP scope** | Phases 1-3 (T001-T003) for the browser-tab rename; add Phase 4 (T004-T006) for product-ready branding consistency |
| **Independent test criteria** | Each user story phase includes a standalone browser/search validation scenario derived from `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/spec.md` |
| **Format validation** | Every task uses the required `- [ ] T### [P?] [US?] Description with file path` checklist structure |

---

## Notes

- No dedicated automated test-writing tasks are included because the specification requests implementation work, not a TDD workflow
- The data model and API contract documents are intentionally unaffected; the work stays within static frontend copy in `/home/runner/work/github-workflows/github-workflows/frontend/`
- User Story 3 focuses on removing residual **user-facing** branding only; out-of-scope comments, fixtures, and internal identifiers remain unchanged per `/home/runner/work/github-workflows/github-workflows/specs/034-update-app-title/research.md`
