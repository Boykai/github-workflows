# Tasks: Tools Page — Fix MCP Bugs, Broken Link, Repo Name Display, Discover Button & Auto-populate MCP Name

**Input**: Design documents from `/specs/028-mcp-tools-fixes/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested in the feature specification. Existing tests should continue to pass.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project setup needed — all changes are in-place modifications to existing files. This phase covers reading existing code to understand current behavior before making changes.

- [ ] T001 [P] Review current MCP validation logic in `backend/src/services/tools/service.py` (functions `validate_mcp_config()` and `_extract_endpoint_url()`)
- [ ] T002 [P] Review current frontend validation in `frontend/src/components/tools/UploadMcpModal.tsx` (function `validateMcpJson()`)
- [ ] T003 [P] Review current ToolsPage layout in `frontend/src/pages/ToolsPage.tsx` (docs link, repo display, action buttons)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking prerequisites needed — all changes are independent in-place modifications to 3 existing files. No new entities, no new routes, no new migrations.

**⚠️ NOTE**: This feature has no shared foundational tasks. User story phases can begin immediately after review (Phase 1).

**Checkpoint**: Phase 1 review complete — user story implementation can begin.

---

## Phase 3: User Story 1 — Accept Command/Args MCP Definitions Without Validation Error (Priority: P1) 🎯 MVP

**Goal**: Fix the blocking validation bug where MCP definitions using `command`/`args` fields (e.g., Docker-based stdio servers) are incorrectly rejected with a "must have 'type' of 'http' or 'stdio'" error. Implement type inference: `command` → `stdio`, `url` → `http`.

**Independent Test**: Paste an MCP definition JSON with `command`/`args` but no `type` field into the creation form → no validation error appears → server is created successfully.

### Implementation for User Story 1

- [ ] T004 [US1] Update `validate_mcp_config()` type inference in `backend/src/services/tools/service.py` — infer `stdio` from `command`, `http` from `url` when `type` is absent; return clear errors for ambiguous or invalid definitions
- [ ] T005 [US1] Update `_extract_endpoint_url()` in `backend/src/services/tools/service.py` to handle configs without explicit `type` by checking for `url`/`command` fields when `type` is absent, matching the inference logic from T004
- [ ] T006 [P] [US1] Update `validateMcpJson()` in `frontend/src/components/tools/UploadMcpModal.tsx` to mirror backend type inference: infer `stdio` when `command` is present and `type` is absent, infer `http` when `url` is present and `type` is absent, update subsequent field-specific checks to use resolved type, and return clear error messages for ambiguous/invalid definitions

**Checkpoint**: Command/args-style MCP definitions (e.g., Docker-based servers) are accepted without validation errors in both frontend and backend. Explicit `type` configs continue to work. Ambiguous configs produce clear, actionable errors.

---

## Phase 4: User Story 2 — Auto-populate MCP Name From Uploaded Definition (Priority: P1)

**Goal**: When a user uploads or pastes an MCP definition JSON and the name field is empty, automatically populate the MCP Name field with the first key under `mcpServers` (e.g., `context7` from `{"mcpServers": {"context7": {...}}}`). Never overwrite user-entered names.

**Independent Test**: Leave the MCP Name field empty → paste an MCP definition JSON → name field auto-populates with the first server key. Also: enter a custom name → paste JSON → name remains unchanged.

### Implementation for User Story 2

- [ ] T007 [US2] Add `multiServerWarning` state variable in `frontend/src/components/tools/UploadMcpModal.tsx` for informational messaging when multiple servers are detected
- [ ] T008 [US2] Add `useEffect` hook in `frontend/src/components/tools/UploadMcpModal.tsx` that watches `configContent` state, parses JSON, extracts `Object.keys(parsed.mcpServers)[0]`, sets name only when `name.trim() === ''`, and sets multi-server warning when `keys.length > 1`
- [ ] T009 [US2] Render `multiServerWarning` message in `frontend/src/components/tools/UploadMcpModal.tsx` below the name field using amber informational styling consistent with existing `duplicateWarning` display

**Checkpoint**: MCP Name auto-populates from uploaded/pasted JSON when empty. User-entered names are never overwritten. Multi-server definitions show an informational warning.

---

## Phase 5: User Story 3 — Fix Broken MCP Documentation Link (Priority: P2)

**Goal**: Update the MCP docs link on the Tools page to point to the correct GitHub Copilot MCP documentation URL, replacing the current broken/dead link.

**Independent Test**: Click the "MCP docs" button on the Tools page → navigates to a valid, accessible GitHub Copilot MCP documentation page.

### Implementation for User Story 3

- [ ] T010 [P] [US3] Replace the broken MCP docs URL in `frontend/src/pages/ToolsPage.tsx` from `https://docs.github.com/en/copilot/customizing-copilot/extending-the-functionality-of-github-copilot-in-your-organization` to `https://docs.github.com/copilot/customizing-copilot/using-model-context-protocol`

**Checkpoint**: MCP docs link navigates to the correct GitHub Copilot MCP documentation page.

---

## Phase 6: User Story 4 — Display Repository Name Instead of Owner (Priority: P2)

**Goal**: Change the Repository field/bubble on the Tools page to display the repository name (e.g., `github-workflows`) instead of the owner or `owner/name` format. Existing CSS handles dynamic sizing via `truncate` class.

**Independent Test**: View the Tools page → Repository bubble shows `github-workflows` (not `Boykai` or `Boykai/github-workflows`).

### Implementation for User Story 4

- [ ] T011 [P] [US4] Update both the `badge` prop and the Repository stats `value` in `frontend/src/pages/ToolsPage.tsx` from `` `${repo.owner}/${repo.name}` `` to `repo.name`

**Checkpoint**: Repository bubble and stats display show the repository name (not the owner or full path) and resize dynamically.

---

## Phase 7: User Story 5 — Add Discover Button for MCP Registry (Priority: P3)

**Goal**: Add a "Discover" button in the MCP section of the Tools page that opens the GitHub MCP Registry (`https://github.com/mcp`) in a new tab. The button must be accessible, keyboard-navigable, and styled consistently with existing page buttons.

**Independent Test**: The Discover button renders on the Tools page, is keyboard-navigable, and clicking it opens `https://github.com/mcp` in a new tab.

### Implementation for User Story 5

- [ ] T012 [US5] Add a "Discover" `<Button>` element with `variant="outline"` and `size="lg"` in the actions slot of `CelestialCatalogHero` in `frontend/src/pages/ToolsPage.tsx`, after the existing "MCP docs" button, wrapping an `<a>` tag with `href="https://github.com/mcp"`, `target="_blank"`, `rel="noopener noreferrer"`, and `aria-label="Discover MCP integrations on GitHub"`

**Checkpoint**: Discover button renders, is keyboard-accessible, opens the GitHub MCP Registry in a new tab, and is visually consistent with existing buttons.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories to ensure no regressions.

- [ ] T013 Run frontend type check (`npx tsc --noEmit` in `frontend/`) to verify no TypeScript errors
- [ ] T014 [P] Run frontend lint (`npx eslint src/` in `frontend/`) to verify no lint violations
- [ ] T015 [P] Run frontend tests (`npx vitest run` in `frontend/`) to verify no regressions
- [ ] T016 [P] Run backend lint (`ruff check src/` in `backend/`) to verify no lint violations
- [ ] T017 [P] Run backend tests (`pytest` in `backend/`) to verify no regressions
- [ ] T018 Validate all 5 fixes end-to-end per `quickstart.md` verification steps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately (code review only)
- **Foundational (Phase 2)**: N/A — no foundational tasks needed
- **User Story 1 — Validation Fix (Phase 3)**: Can start immediately after Phase 1
- **User Story 2 — Auto-populate Name (Phase 4)**: Can start immediately after Phase 1 (independent of US1, different code area in same file)
- **User Story 3 — Docs Link Fix (Phase 5)**: Can start immediately (independent — different file area)
- **User Story 4 — Repo Display Fix (Phase 6)**: Can start immediately (independent — different file area)
- **User Story 5 — Discover Button (Phase 7)**: Can start immediately (independent — different file area)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Backend (T004–T005) and frontend (T006) changes can run in parallel — they modify different files
- **User Story 2 (P1)**: Modifies `UploadMcpModal.tsx` (same file as T006 in US1) — T007–T009 should run after T006
- **User Story 3 (P2)**: Fully independent — modifies a different area of `ToolsPage.tsx`
- **User Story 4 (P2)**: Fully independent — modifies a different area of `ToolsPage.tsx`
- **User Story 5 (P3)**: Fully independent — adds a new element to `ToolsPage.tsx`

### Within Each User Story

- Backend validation (T004–T005) and frontend validation (T006) modify different files — they can run in parallel
- State setup before effect hook before UI rendering (US2: T007→T008→T009)
- All ToolsPage changes (US3, US4, US5) can be applied in any order

### Parallel Opportunities

- T001, T002, T003 (Phase 1 review) can all run in parallel
- T004/T005 (backend) and T010, T011, T012 (frontend ToolsPage) can run in parallel
- T006 can run in parallel with T004/T005 (different files)
- T013, T014, T015, T016, T017 (Phase 8 checks) can largely run in parallel

---

## Parallel Example: Cross-Story Parallelism

```bash
# All ToolsPage fixes can run in parallel (different sections of same file):
Task T010: "Fix MCP docs URL in frontend/src/pages/ToolsPage.tsx"
Task T011: "Update badge and stats to repo.name in frontend/src/pages/ToolsPage.tsx"
Task T012: "Add Discover button in frontend/src/pages/ToolsPage.tsx"

# Backend and frontend validation fixes can run in parallel (different files):
Task T004: "Update validate_mcp_config() in backend/src/services/tools/service.py"
Task T006: "Update validateMcpJson() in frontend/src/components/tools/UploadMcpModal.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Review existing code
2. Complete Phase 3: User Story 1 — Fix validation bug (P1, blocking bug)
3. **STOP and VALIDATE**: Test with command/args MCP definition → no error
4. Deploy/demo if ready — the critical bug is fixed

### Incremental Delivery

1. User Story 1 (P1 Bug Fix) → Test → Validation bug resolved (MVP!)
2. User Story 2 (P1 Usability) → Test → Auto-populate works
3. User Story 3 (P2 Link Fix) → Test → Docs link works
4. User Story 4 (P2 Display Fix) → Test → Repo name displayed correctly
5. User Story 5 (P3 Enhancement) → Test → Discover button works
6. Polish → All checks pass → Ready for review
7. Each story adds value without breaking previous stories

### Single Developer Strategy

Given this is a small, focused fix feature (~3 files):
1. Apply all backend changes first (T004–T005)
2. Apply all frontend changes in sequence (T006–T013)
3. Run all checks (T013–T018)
4. Estimated total time: ~4–6 hours

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 18 |
| **US1 tasks (Validation Fix)** | 3 (T004–T006) |
| **US2 tasks (Auto-populate)** | 3 (T007–T009) |
| **US3 tasks (Docs Link)** | 1 (T010) |
| **US4 tasks (Repo Display)** | 1 (T011) |
| **US5 tasks (Discover Button)** | 1 (T012) |
| **Setup/Review tasks** | 3 (T001–T003) |
| **Polish/Validation tasks** | 6 (T013–T018) |
| **Parallel opportunities** | 8 tasks can run in parallel across stories |
| **Files modified** | 3 (service.py, UploadMcpModal.tsx, ToolsPage.tsx) |
| **New files** | 0 |
| **MVP scope** | User Story 1 (T004–T006) — fixes the blocking validation bug |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No tests are explicitly mandated in the spec — existing tests must continue to pass
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
