# Tasks: Add MCP Configuration Support for GitHub Agents in Settings Page

**Input**: Design documents from `/specs/012-mcp-settings-config/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/mcp-api.md

**Tests**: Tests are OPTIONAL — not explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and shared backend models/services needed by all user stories

- [ ] T001 Create MCP database migration in backend/src/migrations/006_add_mcp_configurations.sql
- [ ] T002 [P] Create MCP Pydantic models (request/response/row) in backend/src/models/mcp.py
- [ ] T003 [P] Add MCP TypeScript interfaces to frontend/src/types/index.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend service layer and API routing that MUST be complete before ANY user story UI can function

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement MCP CRUD service (list, create, delete with per-user scoping and 25-MCP limit) in backend/src/services/mcp_store.py
- [ ] T005 Implement SSRF URL validation helper (reject private/reserved IPs, enforce HTTP(S) scheme) in backend/src/services/mcp_store.py
- [ ] T006 Create MCP API router with GET /settings/mcps, POST /settings/mcps, DELETE /settings/mcps/{mcp_id} endpoints in backend/src/api/mcp.py
- [ ] T007 Register MCP API router in backend/src/api/__init__.py
- [ ] T008 [P] Add MCP API client methods (listMcps, createMcp, deleteMcp) to frontend/src/services/api.ts

**Checkpoint**: Backend API fully functional — all three MCP endpoints (GET, POST, DELETE) respond correctly with auth

---

## Phase 3: User Story 1 — View MCP Configuration List (Priority: P1) 🎯 MVP

**Goal**: Authenticated users see an MCP management section on the Settings page listing all configured MCPs with name and active status, or an empty state message when none exist

**Independent Test**: Navigate to Settings page as an authenticated user → MCP section renders with either a populated list or empty state message ("No MCPs configured yet. Add one to get started.")

### Implementation for User Story 1

- [ ] T009 [US1] Create useMcpSettings React hook with list query (GET /settings/mcps) and loading/error state in frontend/src/hooks/useMcpSettings.ts
- [ ] T010 [US1] Create McpSettings component with MCP list display (name, active status), empty state, and loading indicator in frontend/src/components/settings/McpSettings.tsx
- [ ] T011 [US1] Add McpSettings section to Settings page (visible only to authenticated users) in frontend/src/pages/SettingsPage.tsx

**Checkpoint**: User Story 1 complete — authenticated users can view their MCP list or see the empty state on the Settings page

---

## Phase 4: User Story 2 — Add a New MCP Configuration (Priority: P1)

**Goal**: Authenticated users can add a new MCP by providing a name and endpoint URL, with client-side validation and inline success/error feedback

**Independent Test**: Fill in "Test MCP" name + "https://example.com/mcp" URL → submit → new MCP appears in list with success message. Submit with empty name → inline validation error. Submit with invalid URL → inline validation error.

### Implementation for User Story 2

- [ ] T012 [US2] Add createMcp mutation to useMcpSettings hook (POST /settings/mcps, optimistic list refresh, success/error state) in frontend/src/hooks/useMcpSettings.ts
- [ ] T013 [US2] Add MCP creation form to McpSettings component (name input max 100 chars, endpoint URL input max 2048 chars, client-side validation, submit button, inline feedback) in frontend/src/components/settings/McpSettings.tsx

**Checkpoint**: User Stories 1 AND 2 complete — users can view their MCP list and add new MCPs with inline validation and feedback

---

## Phase 5: User Story 3 — Remove an MCP Configuration (Priority: P2)

**Goal**: Authenticated users can remove an existing MCP with a confirmation prompt and see inline feedback confirming removal

**Independent Test**: Click remove on an MCP → confirmation prompt appears → confirm → MCP disappears from list with success message. Cancel → MCP remains.

### Implementation for User Story 3

- [ ] T014 [US3] Add deleteMcp mutation to useMcpSettings hook (DELETE /settings/mcps/{id}, optimistic list refresh, success/error state) in frontend/src/hooks/useMcpSettings.ts
- [ ] T015 [US3] Add remove button with confirmation dialog and inline delete feedback to McpSettings component in frontend/src/components/settings/McpSettings.tsx

**Checkpoint**: User Stories 1, 2, AND 3 complete — full CRUD lifecycle (view, add, remove) functional

---

## Phase 6: User Story 4 — Handle Authentication Errors Gracefully (Priority: P2)

**Goal**: When OAuth token expires or permissions change during any MCP operation, the system shows a clear re-authentication prompt instead of a generic error

**Independent Test**: Simulate expired session (clear session cookie) → attempt add or remove MCP → see "Your session has expired. Please sign in again." message with re-authentication link

### Implementation for User Story 4

- [ ] T016 [US4] Add 401 response detection and re-authentication prompt to useMcpSettings hook (catch 401 from any MCP API call, display session expired message with login link) in frontend/src/hooks/useMcpSettings.ts
- [ ] T017 [US4] Add authentication error state UI (session expired banner with re-login button) to McpSettings component in frontend/src/components/settings/McpSettings.tsx

**Checkpoint**: All user stories complete — full feature with graceful auth error handling

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T018 [P] Verify SSRF validation rejects private IPs (127.0.0.1, 10.x, 172.16.x, 192.168.x, 169.254.x, ::1) and allows valid public URLs in backend/src/services/mcp_store.py
- [ ] T019 [P] Verify 25 MCP per-user limit is enforced and returns 409 Conflict in backend/src/api/mcp.py
- [ ] T020 Run quickstart.md manual validation (start app, add MCP, view list, remove MCP, verify empty state, test validation errors)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (migration + models) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — View MCP list
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) — Add MCP builds on list view
- **User Story 3 (Phase 5)**: Depends on User Story 2 (Phase 4) — Remove MCP requires items in list
- **User Story 4 (Phase 6)**: Depends on User Story 2 (Phase 4) — Auth error handling requires CRUD operations
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Builds on US1 (McpSettings component + useMcpSettings hook already created)
- **User Story 3 (P2)**: Builds on US2 (adds delete to existing component + hook)
- **User Story 4 (P2)**: Builds on US2 (adds auth error handling to existing hook + component)

### Within Each User Story

- Hook logic before component UI
- Component rendering before page integration
- Core functionality before error handling

### Parallel Opportunities

- T002 (backend models) and T003 (frontend types) can run in parallel — different files
- T008 (frontend API client) can run in parallel with T004–T007 (backend service/API) — different directories
- T018 and T019 (polish verification tasks) can run in parallel — independent validation
- US3 and US4 could run in parallel once US2 is complete (both add to the same component but at different sections)

---

## Parallel Example: Setup Phase

```bash
# Launch setup tasks in parallel (different files):
Task: T002 "Create MCP Pydantic models in backend/src/models/mcp.py"
Task: T003 "Add MCP TypeScript interfaces to frontend/src/types/index.ts"
```

## Parallel Example: Foundational Phase

```bash
# Launch backend API client in parallel with backend service:
Task: T004-T007 "Backend service + API endpoints"
Task: T008 "Frontend API client methods in frontend/src/services/api.ts"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (migration, models, types)
2. Complete Phase 2: Foundational (service, API, frontend client)
3. Complete Phase 3: User Story 1 (view MCP list with empty state)
4. Complete Phase 4: User Story 2 (add MCP with validation)
5. **STOP and VALIDATE**: Test MVP — add an MCP and see it in the list
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Backend API ready
2. Add User Story 1 → MCP list renders → Deploy/Demo (read-only MVP)
3. Add User Story 2 → Add MCP works → Deploy/Demo (write MVP!)
4. Add User Story 3 → Remove MCP works → Deploy/Demo
5. Add User Story 4 → Auth errors handled → Deploy/Demo
6. Polish → SSRF/limit verification → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 → User Story 2 (sequential, same files)
   - Developer B: Can prep US3/US4 logic once US2 merges
3. Stories complete and integrate independently

---

## Summary

- **Total tasks**: 20
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 5 tasks
- **Phase 3 (US1 — View List)**: 3 tasks
- **Phase 4 (US2 — Add MCP)**: 2 tasks
- **Phase 5 (US3 — Remove MCP)**: 2 tasks
- **Phase 6 (US4 — Auth Errors)**: 2 tasks
- **Phase 7 (Polish)**: 3 tasks
- **Parallel opportunities**: 4 identified (Setup, Foundational, Polish, US3/US4)
- **Suggested MVP scope**: User Stories 1 + 2 (View + Add MCP — Phases 1–4, 13 tasks)
- **Format validation**: ✅ All 20 tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Backend follows existing FastAPI + aiosqlite + Pydantic patterns
- Frontend follows existing React + TanStack Query + shadcn/ui patterns
- No test tasks included (tests not explicitly requested in specification)
