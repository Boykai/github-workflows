# Tasks: Codebase Cleanup — Reduce Technical Debt and Improve Maintainability

**Input**: Design documents from `/specs/002-codebase-cleanup/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not requested — this is a cleanup-only feature. No new tests are added.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each cleanup category.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`, `frontend/src/`

---

## Phase 1: Setup

**Purpose**: Establish clean baseline and verify CI passes before making changes

- [ ] T001 Verify all CI checks pass on current branch by running `cd backend && ruff check src/ && pyright src/ && pytest` and `cd frontend && npm run lint && npm run type-check && npm run test && npm run build`
- [ ] T002 Record baseline test counts and timing for before/after comparison

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Remove test artifacts that are not code changes but block a clean workspace

**⚠️ CRITICAL**: MagicMock file cleanup must happen first so subsequent git operations are clean

- [ ] T003 Delete all MagicMock-generated artifact files from backend/ root by running `cd backend && ls | grep "MagicMock" | xargs rm -f`
- [ ] T004 Verify .gitignore already contains `backend/<MagicMock *` pattern to prevent future accumulation

**Checkpoint**: Workspace root is clean — all subsequent changes are source code edits

---

## Phase 3: User Story 1 — Remove Dead Code and Unused Artifacts (Priority: P1) 🎯 MVP

**Goal**: Remove all confirmed-dead functions, methods, models, components, types, and unused exports from both backend and frontend

**Independent Test**: Run full CI suite (`ruff check`, `pyright`, `pytest`, `eslint`, `tsc`, `vitest`, `vite build`) — all checks pass with zero regressions

### Backend Dead Code Removal

- [ ] T005 [P] [US1] Remove `handle_copilot_pr_ready()` function (~93 lines) from backend/src/api/webhooks.py
- [ ] T006 [P] [US1] Remove `determine_next_action()` function (~74 lines) and `PipelineAction` dataclass (~10 lines) from backend/src/services/agent_tracking.py
- [ ] T007 [P] [US1] Delete entire backend/src/services/housekeeping/counter.py file (dead `is_threshold_met()` function, ~23 lines) and remove its import from backend/src/services/housekeeping/__init__.py if present
- [ ] T008 [P] [US1] Remove `reset_ai_agent_service()` function (~10 lines) from backend/src/services/ai_agent.py
- [ ] T009 [P] [US1] Remove unused `TTLCache` methods `get_entry()`, `refresh_ttl()`, and `clear_expired()` from backend/src/services/cache.py
- [ ] T010 [P] [US1] Remove unused Pydantic models `UserPreferencesRow`, `GlobalSettingsRow`, and `ProjectSettingsRow` from backend/src/models/settings.py
- [ ] T011 [US1] Run backend validation: `cd backend && ruff check src/ && pyright src/ && pytest`

### Frontend Dead Code Removal

- [ ] T012 [P] [US1] Delete entire frontend/src/components/housekeeping/ directory (5 unused component files: HousekeepingTaskForm.tsx, HousekeepingTaskList.tsx, RunNowButton.tsx, TemplateLibrary.tsx, TriggerHistoryLog.tsx)
- [ ] T013 [P] [US1] Delete unused frontend/src/components/settings/AIPreferences.tsx component file
- [ ] T014 [P] [US1] Remove 45 unused type exports from frontend/src/types/index.ts (ProjectType, SenderType, ActionType, ProposalStatus, RecommendationStatus, AuthResponse, TaskCreateActionData, StatusUpdateActionData, ProjectSelectActionData, ActionData, IssuePriority, IssueSize, IssueLabel, IssueMetadata, IssueRecommendation, AgentSource, AgentNotification, PipelineStateInfo, ProjectSpecificSettings, AIPreferencesUpdate, DisplayPreferencesUpdate, WorkflowDefaultsUpdate, NotificationPreferencesUpdate, ModelOption, SignalConnectionStatus, SignalLinkStatus, SignalBanner, TemplateCategory, HousekeepingTriggerType, TriggerEventType, TriggerStatus, TriggerEvent, ContentType, PRState, BoardStatusOption, BoardStatusField, BoardRepository, BoardAssignee, BoardCustomFieldValue, LinkedPR, RefreshErrorType, BranchInfo, PullRequestInfo, CleanupItemResult, CleanupAuditLogEntry)
- [ ] T015 [P] [US1] Remove unused API methods `projectsApi.get()` and `tasksApi.create()` from frontend/src/services/api.ts
- [ ] T016 [P] [US1] Remove unused `statusColorToBg()` function from frontend/src/components/board/colorUtils.ts
- [ ] T017 [P] [US1] Remove unused exports `unregisterCommand()` from frontend/src/lib/commands/registry.ts, and unused types `ParameterSchema` and `CommandHandler` from frontend/src/lib/commands/types.ts
- [ ] T018 [P] [US1] Remove unused constants `BOARD_POLL_INTERVAL_MS` and `WS_RECONNECT_DELAY_MS` from frontend/src/constants.ts
- [ ] T019 [US1] Run frontend validation: `cd frontend && npm run lint && npm run type-check && npm run test && npm run build`

**Checkpoint**: All dead code removed from both backend and frontend. CI passes. This is the MVP — the single highest-impact cleanup category.

---

## Phase 4: User Story 2 — Eliminate Stale and Meaningless Tests (Priority: P2)

**Goal**: Remove test classes and methods that test dead functions, and delete the entirely-unused test helpers directory

**Independent Test**: Run `cd backend && pytest` — all remaining tests pass. Confirm removed tests only targeted dead code.

- [ ] T020 [P] [US2] Remove `TestDetermineNextAction` test class (7 methods) from backend/tests/unit/test_agent_tracking.py
- [ ] T021 [P] [US2] Remove `TestHandleCopilotPrReady` test class (3+ methods) from backend/tests/unit/test_webhooks.py
- [ ] T022 [P] [US2] Remove tests for `UserPreferencesRow`, `GlobalSettingsRow`, `ProjectSettingsRow` from backend/tests/unit/test_settings_store.py (if present — these models are being removed in US1)
- [ ] T023 [US2] Delete entire backend/tests/helpers/ directory (factories.py, mocks.py, assertions.py, __init__.py — never imported by any test file)
- [ ] T024 [US2] Run backend test validation: `cd backend && pytest`

**Checkpoint**: Test suite is clean — all remaining tests target live code. No stale coverage signals.

---

## Phase 5: User Story 3 — Consolidate Duplicated Logic (Priority: P3)

**Goal**: Merge duplicate implementations into single canonical versions and update all call sites

**Independent Test**: Run full CI suite — all checks pass. Diff review confirms each duplicate is replaced by the canonical version.

- [ ] T025 [US3] Consolidate duplicate `formatTimeAgo()` in frontend/src/components/settings/DynamicDropdown.tsx by replacing the local inline implementation with an import from the canonical frontend/src/utils/formatTime.ts (extend canonical to accept both Date and ISO string if needed)
- [ ] T026 [US3] Consolidate or differentiate `STALE_TIME_MEDIUM` and `STALE_TIME_SHORT` constants in frontend/src/constants.ts (both currently set to identical value `60 * 1000` — either merge into one constant or set distinct values per their documented intent)
- [ ] T027 [US3] Run frontend validation: `cd frontend && npm run lint && npm run type-check && npm run test && npm run build`

**Checkpoint**: No duplicate logic remains. Each concept has a single canonical implementation.

---

## Phase 6: User Story 4 — Remove Backwards-Compatibility Shims (Priority: P4)

**Goal**: Remove backward-compatibility re-exports and aliases that only exist to support old import paths, and update all consumers to use canonical imports

**Independent Test**: Run full CI suite. Grep for old import paths confirms zero remaining references.

- [ ] T028 [US4] Remove 19 backward-compatibility re-exports from backend/src/models/chat.py (lines 16-44: DEFAULT_AGENT_MAPPINGS, AgentAssignment, AgentAssignmentInput, AgentSource, AvailableAgent, AvailableAgentsResponse, AITaskProposal, IssueLabel, IssueMetadata, IssuePriority, IssueRecommendation, IssueSize, ProposalConfirmRequest, ProposalStatus, RecommendationStatus, AVAILABLE_LABELS, TriggeredBy, WorkflowConfiguration, WorkflowResult, WorkflowTransition, utcnow) and remove their `# noqa: F401` suppression comments
- [ ] T029 [US4] Update all test files that import via `from src.models.chat import ...` to use canonical module imports instead: update backend/tests/unit/test_models.py, backend/tests/unit/test_workflow_orchestrator.py, backend/tests/unit/test_ai_agent.py, backend/tests/unit/test_api_workflow.py, backend/tests/unit/test_api_tasks.py, backend/tests/unit/test_api_chat.py, backend/tests/integration/test_custom_agent_assignment.py
- [ ] T030 [US4] Remove `PREDEFINED_LABELS = LABELS` alias from backend/src/prompts/issue_generation.py and update backend/tests/unit/test_prompts.py to import `LABELS` directly instead of `PREDEFINED_LABELS`
- [ ] T031 [US4] Run backend validation: `cd backend && ruff check src/ && pyright src/ && pytest`

**Checkpoint**: All backward-compatibility shims removed. Tests import from canonical module paths.

---

## Phase 7: User Story 5 — General Hygiene and Dependency Cleanup (Priority: P5)

**Goal**: Remove unused dependencies from project manifests and clean up stale metadata

**Independent Test**: Clean install of all dependencies followed by full CI suite passes.

- [ ] T032 [P] [US5] Remove `python-jose[cryptography]` and `agent-framework-core` from dependencies list in backend/pyproject.toml
- [ ] T033 [P] [US5] Remove `socket.io-client` dependency from frontend/package.json by running `cd frontend && npm uninstall socket.io-client`
- [ ] T034 [US5] Run full validation after dependency removal: `cd backend && pip install -e . && pytest` and `cd frontend && npm install && npm run build && npm run test`

**Checkpoint**: All dependencies in manifests are actively used. Clean installs succeed.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, commit organization, and PR creation

- [ ] T035 Run complete CI validation across both projects: backend (ruff check, pyright, pytest) and frontend (lint, type-check, vitest, vite build)
- [ ] T036 Organize commits using conventional commit format: `chore:` for dead code/test removal, `refactor:` for code consolidation
- [ ] T037 Push branch and open (or update) PR with categorized summary of all changes organized by the 5 cleanup categories, including rationale for each removal
- [ ] T038 Run quickstart.md validation checklist to confirm all items pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify baseline
- **Foundational (Phase 2)**: No code dependencies — clean workspace artifacts
- **US1: Dead Code (Phase 3)**: Depends on Phase 2 — remove dead source code
- **US2: Stale Tests (Phase 4)**: Depends on Phase 3 — dead code must be removed first so we know which tests target removed code
- **US3: Consolidation (Phase 5)**: Independent of Phase 4 — can start after Phase 3
- **US4: Shims (Phase 6)**: Independent of Phase 5 — can start after Phase 3 (but test import updates in T029 must account for any test changes from Phase 4)
- **US5: Hygiene (Phase 7)**: Independent of Phase 5/6 — can start after Phase 3
- **Polish (Phase 8)**: Depends on all previous phases

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US2 (P2)**: Depends on US1 — must know which functions were removed to identify stale tests
- **US3 (P3)**: Can start after US1 — consolidation is independent of test/shim cleanup
- **US4 (P4)**: Can start after US1 — shim removal is independent of consolidation
- **US5 (P5)**: Can start after US1 — dependency cleanup is independent

### Within Each User Story

- Backend changes before frontend changes (within US1)
- Source code changes before test changes (US1 before US2)
- Validate after each phase before proceeding

### Parallel Opportunities

Within US1 (Phase 3):
- All backend dead code tasks T005–T010 can run in parallel (different files)
- All frontend dead code tasks T012–T018 can run in parallel (different files)
- Backend and frontend blocks can run in parallel after Phase 2

Within US2 (Phase 4):
- T020, T021, T022 can run in parallel (different test files)

After US1 completes:
- US3 (Phase 5), US4 (Phase 6), and US5 (Phase 7) can all start in parallel

---

## Parallel Example: User Story 1 (Phase 3)

```bash
# Launch all backend dead code removals together:
Task T005: Remove handle_copilot_pr_ready() from backend/src/api/webhooks.py
Task T006: Remove determine_next_action() + PipelineAction from backend/src/services/agent_tracking.py
Task T007: Delete backend/src/services/housekeeping/counter.py
Task T008: Remove reset_ai_agent_service() from backend/src/services/ai_agent.py
Task T009: Remove unused TTLCache methods from backend/src/services/cache.py
Task T010: Remove unused *Row models from backend/src/models/settings.py

# Then validate backend (T011)

# Launch all frontend dead code removals together:
Task T012: Delete frontend/src/components/housekeeping/ directory
Task T013: Delete frontend/src/components/settings/AIPreferences.tsx
Task T014: Remove 45 unused types from frontend/src/types/index.ts
Task T015: Remove unused API methods from frontend/src/services/api.ts
Task T016: Remove statusColorToBg() from frontend/src/components/board/colorUtils.ts
Task T017: Remove unused exports from frontend/src/lib/commands/
Task T018: Remove unused constants from frontend/src/constants.ts

# Then validate frontend (T019)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify baseline)
2. Complete Phase 2: Foundational (clean MagicMock files)
3. Complete Phase 3: User Story 1 (remove all dead code)
4. **STOP and VALIDATE**: Full CI suite passes, dead code is gone
5. This alone delivers the highest-impact cleanup

### Incremental Delivery

1. Complete Setup + Foundational → Clean workspace
2. Add US1: Dead Code Removal → Validate → Commit (MVP!)
3. Add US2: Stale Test Removal → Validate → Commit
4. Add US3: Consolidation → Validate → Commit
5. Add US4: Shim Removal → Validate → Commit
6. Add US5: Dependency Cleanup → Validate → Commit
7. Polish: PR with categorized summary
8. Each commit is independently valid — CI passes at every step

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + US1 together (most impactful)
2. Once US1 is done:
   - Developer A: US2 (Stale Tests)
   - Developer B: US3 (Consolidation)
   - Developer C: US4 (Shims) + US5 (Deps)
3. All stories complete independently and merge cleanly

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Commit after each phase with appropriate conventional commit prefix
- Validate CI after every phase — never proceed with failing checks
- The total of 38 tasks covers all 5 user stories across 8 phases
- No new tests or features are added — this is strictly removal and consolidation
- Deferred items (hasattr patterns, legacy pipeline path, test_api_e2e fixture duplication) are documented in research.md and excluded from tasks
