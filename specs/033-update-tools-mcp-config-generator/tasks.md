# Tasks: Update Tools Page — GitHub.com MCP Configuration Generator

**Input**: Design documents from `/specs/033-update-tools-mcp-config-generator/` plus the parent issue-backed user story in Boykai/github-workflows#3039  
**Prerequisites**: `plan.md`, `research.md`, `data-model.md`, `contracts/api.md`, `contracts/components.md`, `quickstart.md`

**Tests**: Tests are explicitly requested in the design artifacts for the config builder utility and the Tools page generator UI, so targeted frontend test tasks are included below.

**Organization**: Tasks are grouped by the single P1 user story from the issue so the GitHub.com MCP configuration generator can be implemented and validated independently as the MVP.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., `US1`)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React/TypeScript), `backend/src/` (FastAPI/Python)
- **Frontend tools UI**: `frontend/src/components/tools/`
- **Frontend shared utilities**: `frontend/src/lib/`
- **Frontend hooks/types**: `frontend/src/hooks/`, `frontend/src/types/`
- This feature is frontend-only; no backend implementation changes are planned

---

## Phase 1: Setup

**Purpose**: Establish the replacement surface for the Tools page section and confirm the shared contracts the generator reuses.

- [ ] T001 Update the section mount point and replacement copy for the GitHub.com MCP generator in `frontend/src/components/tools/ToolsPanel.tsx`
- [ ] T002 [P] Verify the existing MCP tool query/state contract reused by the generator in `frontend/src/hooks/useTools.ts` and `frontend/src/types/index.ts`

**Checkpoint**: The Tools page replacement point and reused frontend contracts are confirmed before core generator work begins.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared config-generation foundation that every Tools page behavior depends on.

**⚠️ CRITICAL**: No user story work should begin until the GitHub.com config builder and its output contract are in place.

- [ ] T003 Implement `BUILTIN_MCPS`, server extraction, deduplication, GitHub.com `mcpServers` serialization, and built-in metadata in `frontend/src/lib/buildGitHubMcpConfig.ts`
- [ ] T004 [P] Add unit coverage for built-in inclusion, malformed tool configs, duplicate server keys, and valid GitHub.com JSON output in `frontend/src/lib/buildGitHubMcpConfig.test.ts`
- [ ] T005 Define the generator props, derived state, and rendered sections contract in `frontend/src/components/tools/GitHubMcpConfigGenerator.tsx`

**Checkpoint**: The reusable config builder and component contract are ready for the MVP user story.

---

## Phase 3: User Story 1 — Generate a Copy/Paste-Ready GitHub.com MCP Configuration (Priority: P1) 🎯 MVP

**Goal**: Let a Solune user open the Tools page and immediately get a GitHub.com MCP configuration built from active MCPs plus always-included Built-In MCPs, with clear guidance and one-click copy support.

**Independent Test**: On the Tools page, activate at least one MCP and verify the generator shows a read-only syntax-highlighted config that updates immediately, includes Built-In MCPs with labels, and copies to the clipboard for GitHub.com; then deactivate all user MCPs and verify the empty-state guidance appears.

### Tests for User Story 1

- [ ] T006 [P] [US1] Add component integration coverage for active-only filtering, Built-In badges, empty-state guidance, and copy controls in `frontend/src/components/tools/ToolsEnhancements.test.tsx`

### Implementation for User Story 1

- [ ] T007 [US1] Render the GitHub.com MCP generator header, contextual help copy, and active/built-in MCP summary list in `frontend/src/components/tools/GitHubMcpConfigGenerator.tsx`
- [ ] T008 [US1] Render the read-only syntax-highlighted configuration block and Built-In-aware MCP entry presentation in `frontend/src/components/tools/GitHubMcpConfigGenerator.tsx`
- [ ] T009 [US1] Implement Clipboard API copying with insecure-context fallback and transient success feedback in `frontend/src/components/tools/GitHubMcpConfigGenerator.tsx`
- [ ] T010 [US1] Recompute the displayed configuration from active tools plus Built-In MCPs in real time and surface the no-active-tools empty state in `frontend/src/components/tools/GitHubMcpConfigGenerator.tsx`
- [ ] T011 [US1] Replace the legacy “Configure GitHub Toolset” section with `GitHubMcpConfigGenerator` in `frontend/src/components/tools/ToolsPanel.tsx`

**Checkpoint**: The Tools page now delivers the full GitHub.com MCP configuration generator workflow as an independently testable MVP.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Remove leftover legacy surface area and verify the final behavior using the existing validation flow.

- [ ] T012 [P] Remove the unused legacy selector implementation in `frontend/src/components/tools/GitHubToolsetSelector.tsx`
- [ ] T013 [P] Run the manual scenarios from `specs/033-update-tools-mcp-config-generator/quickstart.md` and the existing frontend validation commands listed in `frontend/package.json`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS the user story
- **User Story 1 (Phase 3)**: Depends on Foundational completion and delivers the MVP
- **Polish (Phase 4)**: Depends on User Story 1 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational completion — no dependency on any other story

### Within User Story 1

- Add the component test coverage before or alongside UI implementation
- Complete the generator layout before wiring copy and empty-state interactions
- Finish real-time data wiring before replacing the legacy section in `ToolsPanel`
- Validate the story end-to-end before cleanup/polish

### Parallel Opportunities

- **Phase 1**: T002 can run in parallel with T001 once the replacement scope is clear
- **Phase 2**: T004 can run in parallel with T005 after T003 establishes the builder contract
- **Phase 3**: T006 can run in parallel with T007 because the test file and component file are independent
- **Phase 4**: T012 and T013 can run in parallel after the MVP implementation is stable

---

## Parallel Example: User Story 1

```text
# Track A — Generator component behavior
Task T007: Render generator header/help/summary list in frontend/src/components/tools/GitHubMcpConfigGenerator.tsx
Task T008: Render syntax-highlighted config block in frontend/src/components/tools/GitHubMcpConfigGenerator.tsx

# Track B — User-story validation
Task T006: Add component integration coverage in frontend/src/components/tools/ToolsEnhancements.test.tsx
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Verify generated config output, Built-In labeling, copy flow, and empty-state behavior on the Tools page
5. Ship/demo the MVP

### Incremental Delivery

1. Complete Setup + Foundational → reusable builder + component contract are ready
2. Add User Story 1 → validate the full GitHub.com MCP generator workflow (**MVP**)
3. Finish Polish → remove legacy surface area and run quickstart/frontend validation commands

### Parallel Team Strategy

With multiple developers:

1. Complete Setup + Foundational together
2. Then split the MVP work:
   - Developer A: `frontend/src/components/tools/GitHubMcpConfigGenerator.tsx`
   - Developer B: `frontend/src/components/tools/ToolsEnhancements.test.tsx`
   - Developer C: final `frontend/src/components/tools/ToolsPanel.tsx` replacement and cleanup

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 13 |
| **Setup tasks** | 2 (T001–T002) |
| **Foundational tasks** | 3 (T003–T005) |
| **US1 tasks** | 6 (T006–T011) |
| **Polish tasks** | 2 (T012–T013) |
| **Parallel opportunities** | 5 tasks marked `[P]` across setup, testing, cleanup, and validation |
| **Independent test criteria** | Tools page config updates from active MCPs, includes Built-In MCPs, supports copy, and shows empty-state guidance when no user MCPs are active |
| **Suggested MVP scope** | Phases 1–3 (T001–T011) |

---

## Notes

- Every task above follows the required checklist format: checkbox, task ID, optional `[P]`, required `[US1]` label for story work, and an exact file path
- The feature design artifacts describe a single P1 user story, so only one user-story phase is included
- Built-In MCP support is modeled as shared foundational work because the UI and tests both depend on the builder output contract
- No backend endpoints or schema changes are required for this feature per `contracts/api.md` and `plan.md`
