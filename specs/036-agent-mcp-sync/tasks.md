# Tasks: Agent MCP Sync — Propagate Activated & Built-in MCPs to Agent Files

**Input**: Design documents from `/specs/036-agent-mcp-sync/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — the plan.md explicitly calls for backend unit tests and frontend integration tests due to the data-integrity nature of this feature (incorrect sync could corrupt agent files).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new sync module and establish the BUILTIN_MCPS registry constant

- [ ] T001 Create `backend/src/services/agents/agent_mcp_sync.py` module with module docstring, imports (`yaml`, `re`, `logging`, `httpx`, `typing`), and `BUILTIN_MCPS` constant mirroring `frontend/src/lib/buildGitHubMcpConfig.ts` (Context7 HTTP + CodeGraphContext local/uvx)
- [ ] T002 [P] Define `AgentMcpSyncResult` dataclass in `backend/src/services/agents/agent_mcp_sync.py` with fields: `success`, `files_updated`, `files_skipped`, `files_unchanged`, `warnings`, `errors`, `synced_mcps` (matching contracts/agent-sync-api.yaml schema)
- [ ] T003 [P] Add `_FRONTMATTER_RE` regex pattern in `backend/src/services/agents/agent_mcp_sync.py` for splitting YAML frontmatter from Markdown body (reuse pattern from existing `agent_creator.py`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement the core sync logic that all user stories depend on — frontmatter parsing, merge logic, and file read/write via GitHub API

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `_parse_agent_file(content: str) -> tuple[dict, str]` helper in `backend/src/services/agents/agent_mcp_sync.py` — splits file content into (frontmatter dict, markdown body) using `_FRONTMATTER_RE` and `yaml.safe_load()`; returns `(None, content)` for unparseable files
- [ ] T005 [P] Implement `_serialize_agent_file(frontmatter: dict, body: str) -> str` helper in `backend/src/services/agents/agent_mcp_sync.py` — re-serializes updated frontmatter with `yaml.dump(default_flow_style=False, sort_keys=False)` and concatenates with original Markdown body
- [ ] T006 [P] Implement `_build_active_mcp_dict(db, project_id: str) -> dict[str, dict]` helper in `backend/src/services/agents/agent_mcp_sync.py` — queries `mcp_configurations` table for active MCPs (`is_active = 1`), merges with `BUILTIN_MCPS` (built-in takes precedence on key conflict), returns dict keyed by server key
- [ ] T007 Implement `_discover_agent_files(owner, repo, token) -> list[dict]` helper in `backend/src/services/agents/agent_mcp_sync.py` — uses GitHub Contents API (`GET /repos/{owner}/{repo}/contents/.github/agents`) to list all `*.agent.md` files, returns list of `{path, sha, download_url}` dicts
- [ ] T008 Implement `_merge_mcps_into_frontmatter(frontmatter: dict, active_mcps: dict[str, dict]) -> tuple[dict, list[str]]` helper in `backend/src/services/agents/agent_mcp_sync.py` — merges active MCPs into frontmatter `mcp-servers` field (initializing as empty dict if missing), deduplicates by server key (built-in precedence), enforces `tools: ["*"]`, returns (updated frontmatter, warnings list)

**Checkpoint**: Core sync primitives ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Enforce Full Tool Access Across All Agent Definitions (Priority: P1) 🎯 MVP

**Goal**: Whenever agent files are synced, `tools: ["*"]` is unconditionally set on every agent definition. Restrictive or missing `tools` fields are replaced, and overrides are logged as warnings.

**Independent Test**: Run sync on agent files with varying `tools` states (missing, restrictive, already `["*"]`). Verify all end up with `tools: ["*"]` and overrides are warned.

### Tests for User Story 1

- [ ] T009 [P] [US1] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `_merge_mcps_into_frontmatter` sets `tools: ["*"]` when `tools` field is missing from frontmatter
- [ ] T010 [P] [US1] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `_merge_mcps_into_frontmatter` replaces `tools: ["search", "edit"]` with `tools: ["*"]` and returns a warning string containing the original value
- [ ] T011 [P] [US1] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `_merge_mcps_into_frontmatter` leaves `tools: ["*"]` unchanged and produces no warning (idempotent)

### Implementation for User Story 1

- [ ] T012 [US1] Add `tools: ["*"]` enforcement logic in `_merge_mcps_into_frontmatter()` in `backend/src/services/agents/agent_mcp_sync.py` — check current `tools` value, replace if not `["*"]`, append warning with file path and original value to warnings list
- [ ] T013 [US1] Add structured logging in `_merge_mcps_into_frontmatter()` in `backend/src/services/agents/agent_mcp_sync.py` — use `logging.warning()` when a non-`["*"]` tools value is overridden, include agent file path and original value (FR-010)

**Checkpoint**: User Story 1 complete — all agent files get `tools: ["*"]` enforced, overrides are logged

---

## Phase 4: User Story 2 — Propagate Activated MCPs to Agent Files on Toggle (Priority: P1)

**Goal**: When MCPs are activated/deactivated on the Tools page, all agent files' `mcp-servers` fields are updated to reflect the current activation state. No duplicates, clean removal on deactivation.

**Independent Test**: Activate an MCP, run sync, verify all agent files list it. Deactivate, run sync, verify it's removed. Verify no duplicates on repeated sync.

### Tests for User Story 2

- [ ] T014 [P] [US2] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `_merge_mcps_into_frontmatter` adds 3 active MCPs to an empty `mcp-servers` field
- [ ] T015 [P] [US2] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `_merge_mcps_into_frontmatter` does not create duplicate entries when an MCP is already present in `mcp-servers`
- [ ] T016 [P] [US2] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `_merge_mcps_into_frontmatter` removes a deactivated MCP (not in active dict) from `mcp-servers` while keeping remaining MCPs intact
- [ ] T017 [P] [US2] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `_merge_mcps_into_frontmatter` with no active MCPs results in `mcp-servers` containing only built-in MCPs

### Implementation for User Story 2

- [ ] T018 [US2] Implement MCP merge logic in `_merge_mcps_into_frontmatter()` in `backend/src/services/agents/agent_mcp_sync.py` — replace `mcp-servers` with exact set from `active_mcps` dict (built-in + user-activated), ensuring no extra keys remain from previously deactivated MCPs (FR-002, FR-004, FR-005)
- [ ] T019 [US2] Implement the main `sync_agent_mcps(owner, repo, project_id, access_token, trigger, db) -> AgentMcpSyncResult` function in `backend/src/services/agents/agent_mcp_sync.py` — orchestrates: build active MCP dict → discover agent files → for each file: fetch content → parse → merge → compare → write if changed → return result summary
- [ ] T020 [US2] Wire sync trigger in `backend/src/services/tools/service.py` — call `sync_agent_mcps()` after `sync_tool_to_github()` completes for tool activation/deactivation operations (FR-007)
- [ ] T021 [US2] Add `POST /agents/{project_id}/sync-mcps` endpoint in `backend/src/api/agents.py` — accepts optional `trigger` body param, calls `sync_agent_mcps()`, returns `AgentMcpSyncResult` JSON (per contracts/agent-sync-api.yaml)
- [ ] T022 [US2] Add `syncAgentMcps(projectId: string, trigger?: string)` API function in `frontend/src/services/api.ts` — POST to `/agents/{project_id}/sync-mcps`
- [ ] T023 [US2] Update `frontend/src/hooks/useTools.ts` — after tool toggle mutation succeeds, call `syncAgentMcps()` and invalidate agent query cache with `queryClient.invalidateQueries({ queryKey: agentKeys.list(projectId) })`

**Checkpoint**: User Story 2 complete — MCP activation/deactivation on Tools page propagates to all agent files

---

## Phase 5: User Story 3 — Include Built-in MCPs in All Agent Files (Priority: P2)

**Goal**: Built-in MCPs (Context7, Code Graph Context) are always present in every agent file's `mcp-servers` field. They cannot be removed by user action and are re-added on every sync.

**Independent Test**: Create a new agent file, verify built-in MCPs appear. Remove a built-in MCP from a file, run sync, verify it's re-added.

### Tests for User Story 3

- [ ] T024 [P] [US3] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `BUILTIN_MCPS` constant contains entries for `context7` and `CodeGraphContext` with correct types (`http` and `local`/`stdio` respectively)
- [ ] T025 [P] [US3] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `_merge_mcps_into_frontmatter` always includes built-in MCPs even when agent file had them manually removed
- [ ] T026 [P] [US3] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `_build_active_mcp_dict` gives built-in MCPs precedence over user-activated MCPs with the same server key (FR-014)

### Implementation for User Story 3

- [ ] T027 [US3] Ensure `_build_active_mcp_dict()` in `backend/src/services/agents/agent_mcp_sync.py` merges `BUILTIN_MCPS` after user MCPs so built-in entries take precedence on key conflicts (FR-013, FR-014), and log warning on conflict
- [ ] T028 [US3] Wire sync trigger in `backend/src/services/agents/service.py` — call `sync_agent_mcps()` after `create_agent()` completes to ensure new agent files include built-in MCPs from creation (FR-003, FR-008)
- [ ] T029 [US3] Wire sync trigger in `backend/src/services/agents/service.py` — call `sync_agent_mcps()` after `update_agent()` completes to re-enforce built-in MCPs on any agent update (FR-003)

**Checkpoint**: User Story 3 complete — built-in MCPs are guaranteed present in all agent files

---

## Phase 6: User Story 4 — Real-Time Sync on MCP Activation Changes (Priority: P2)

**Goal**: Agent files are updated immediately when MCP activation state changes on the Tools page, without requiring manual sync or app restart. Frontend reflects changes in agent previews.

**Independent Test**: Toggle an MCP on the Tools page, immediately check agent file contents to verify the MCP appears/disappears.

### Tests for User Story 4

- [ ] T030 [P] [US4] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test full `sync_agent_mcps()` function with mocked GitHub API — verify correct number of files_updated, files_unchanged, files_skipped in result
- [ ] T031 [P] [US4] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `sync_agent_mcps()` idempotency — running sync twice with same state produces `files_updated=0` on second run (SC-004)

### Implementation for User Story 4

- [ ] T032 [US4] Add idempotency check in `sync_agent_mcps()` in `backend/src/services/agents/agent_mcp_sync.py` — compare serialized new content with fetched current content; only PUT if content differs (SC-004, SC-007)
- [ ] T033 [US4] Wire startup sync trigger in `backend/src/startup.py` — call `sync_agent_mcps()` as a background task during application initialization to reconcile any drift (FR-009)
- [ ] T034 [US4] Ensure `frontend/src/hooks/useTools.ts` invalidates agent-related queries after sync mutation completes, so agent preview/editor views reflect updated `mcp-servers` and `tools` fields immediately

**Checkpoint**: User Story 4 complete — real-time sync works across all trigger points (toggle, create, update, startup)

---

## Phase 7: User Story 5 — Agent File Schema Validation After Sync (Priority: P3)

**Goal**: After sync updates agent files, each file is validated against lightweight schema rules before being persisted. Invalid files are skipped with error reporting.

**Independent Test**: Corrupt an agent file's structure, run sync, verify the system reports the error and does not persist invalid content.

### Tests for User Story 5

- [ ] T035 [P] [US5] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `_validate_agent_frontmatter()` returns success for valid frontmatter with `tools: ["*"]` and well-formed `mcp-servers` dict
- [ ] T036 [P] [US5] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `_validate_agent_frontmatter()` returns error for frontmatter with invalid `mcp-servers` entry (missing `type` field)
- [ ] T037 [P] [US5] Unit test in `backend/tests/unit/test_agent_mcp_sync.py`: test `sync_agent_mcps()` skips files with unparseable frontmatter and includes file path in `errors` list (FR-012)

### Implementation for User Story 5

- [ ] T038 [US5] Implement `_validate_agent_frontmatter(frontmatter: dict, file_path: str) -> list[str]` helper in `backend/src/services/agents/agent_mcp_sync.py` — validates: YAML parses, `tools` is `["*"]`, `mcp-servers` is dict, each server has `type` and either `url` or `command`; returns list of error strings (R7)
- [ ] T039 [US5] Integrate `_validate_agent_frontmatter()` call in `sync_agent_mcps()` in `backend/src/services/agents/agent_mcp_sync.py` — validate after merge, before write; skip write and append errors to result if validation fails (FR-011)
- [ ] T040 [US5] Handle edge case in `sync_agent_mcps()` in `backend/src/services/agents/agent_mcp_sync.py` — files without parseable frontmatter are skipped, logged as warning with file path, and counted in `files_skipped` (FR-012, R8)

**Checkpoint**: User Story 5 complete — all synced files pass validation before persisting

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Add comprehensive docstrings to all public functions in `backend/src/services/agents/agent_mcp_sync.py`
- [ ] T042 [P] Add type hints to all functions in `backend/src/services/agents/agent_mcp_sync.py` for mypy compliance
- [ ] T043 [P] Verify `BUILTIN_MCPS` constant in `backend/src/services/agents/agent_mcp_sync.py` matches `frontend/src/lib/buildGitHubMcpConfig.ts` `BUILTIN_MCPS` — add inline comment referencing the frontend constant for future maintainers
- [ ] T044 Run `backend/tests/unit/test_agent_mcp_sync.py` full test suite and ensure all tests pass
- [ ] T045 Run `specs/036-agent-mcp-sync/quickstart.md` validation scenarios manually — verify end-to-end sync for each trigger point
- [ ] T046 Review all agent files in `.github/agents/` to confirm `tools: ["*"]` and `mcp-servers` fields are correctly populated after a full sync

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — `tools: ["*"]` enforcement
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — MCP propagation on toggle
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — Built-in MCP inclusion
- **User Story 4 (Phase 6)**: Depends on User Stories 1–3 (Phases 3–5) — Real-time sync ties together all triggers
- **User Story 5 (Phase 7)**: Depends on Foundational (Phase 2) — Validation is independent of other stories
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — no dependencies on other stories
- **US2 (P1)**: Can start after Foundational — no dependencies on other stories
- **US3 (P2)**: Can start after Foundational — integrates with US2 merge logic but independently testable
- **US4 (P2)**: Depends on US1 + US2 + US3 — ties all trigger points together
- **US5 (P3)**: Can start after Foundational — independent validation layer

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Helper functions before orchestrator functions
- Backend before frontend
- Core logic before trigger wiring
- Story complete before moving to next priority

### Parallel Opportunities

- T002 + T003 can run in parallel (different concerns in same file)
- T004 + T005 + T006 + T007 can have T005, T006, T007 in parallel after T004
- T009 + T010 + T011 (US1 tests) can all run in parallel
- T014 + T015 + T016 + T017 (US2 tests) can all run in parallel
- T024 + T025 + T026 (US3 tests) can all run in parallel
- T030 + T031 (US4 tests) can run in parallel
- T035 + T036 + T037 (US5 tests) can all run in parallel
- US1 (Phase 3) and US5 (Phase 7) can run in parallel once Foundational completes
- T041 + T042 + T043 (polish) can all run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task: T014 "test _merge_mcps_into_frontmatter adds 3 active MCPs to empty mcp-servers"
Task: T015 "test _merge_mcps_into_frontmatter no duplicates"
Task: T016 "test _merge_mcps_into_frontmatter removes deactivated MCP"
Task: T017 "test _merge_mcps_into_frontmatter with no active MCPs → only built-ins"

# After tests written and failing, launch implementation:
Task: T018 "MCP merge logic in _merge_mcps_into_frontmatter()"
Task: T019 "Main sync_agent_mcps() orchestrator function"

# Then wire triggers (sequential — depends on T019):
Task: T020 "Wire sync in tools/service.py"
Task: T021 "Add POST /agents/{project_id}/sync-mcps endpoint"
Task: T022 "Add syncAgentMcps() API function in frontend"
Task: T023 "Update useTools.ts with cache invalidation"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T008)
3. Complete Phase 3: User Story 1 — `tools: ["*"]` enforcement (T009–T013)
4. Complete Phase 4: User Story 2 — MCP propagation on toggle (T014–T023)
5. **STOP and VALIDATE**: Test US1 + US2 independently — agents get full tool access and MCPs sync on toggle
6. Deploy/demo if ready — this covers the two P1 stories

### Incremental Delivery

1. Setup + Foundational → Core sync primitives ready
2. Add US1 → `tools: ["*"]` enforced → Test independently (MVP foundation)
3. Add US2 → MCP propagation works → Test independently (MVP complete!)
4. Add US3 → Built-in MCPs always present → Test independently
5. Add US4 → Real-time sync across all triggers → Test independently
6. Add US5 → Schema validation safety net → Test independently
7. Polish → Documentation, type hints, cross-story verification

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (tools enforcement) + User Story 2 (MCP propagation)
   - Developer B: User Story 3 (built-in MCPs) + User Story 5 (validation)
3. After A + B complete: User Story 4 (real-time sync) ties everything together
4. Polish phase as team effort

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 46 |
| **Setup Tasks** | 3 (T001–T003) |
| **Foundational Tasks** | 5 (T004–T008) |
| **US1 Tasks (P1)** | 5 (T009–T013) |
| **US2 Tasks (P1)** | 10 (T014–T023) |
| **US3 Tasks (P2)** | 6 (T024–T029) |
| **US4 Tasks (P2)** | 5 (T030–T034) |
| **US5 Tasks (P3)** | 6 (T035–T040) |
| **Polish Tasks** | 6 (T041–T046) |
| **Parallel Opportunities** | 28 tasks marked [P] |
| **Suggested MVP** | US1 + US2 (Phases 1–4, 23 tasks) |

### Independent Test Criteria Per Story

- **US1**: Sync agent files with mixed `tools` states → all end up `["*"]`, overrides warned
- **US2**: Activate/deactivate MCP → all agent files updated, no duplicates
- **US3**: New agent file → built-in MCPs present; remove built-in → re-added on sync
- **US4**: Toggle MCP on Tools page → immediate agent file update, idempotent
- **US5**: Corrupt agent file → error reported, valid files still updated

### Format Validation

✅ All 46 tasks follow the checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
✅ Setup/Foundational tasks have NO story labels
✅ User Story phase tasks have [US#] labels
✅ Polish phase tasks have NO story labels
✅ All tasks include specific file paths
✅ All parallelizable tasks marked with [P]
