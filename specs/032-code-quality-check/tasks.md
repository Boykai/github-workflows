# Tasks: Code Quality Check

**Input**: Design documents from `/specs/032-code-quality-check/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Testing is required by the specification, so each user story includes test work that should fail before implementation and pass after the story is complete.

**Organization**: Tasks are grouped by setup, foundational work, then user story so each increment can be implemented and validated independently.

## Phase 1: Setup

**Purpose**: Align repository-level quality workflows and phase verification before refactoring starts.

- [ ] T001 Confirm backend quality-tooling commands in `backend/pyproject.toml` and align them with the verification flow in `specs/032-code-quality-check/quickstart.md`
- [ ] T002 [P] Confirm frontend quality-tooling scripts and dependencies in `frontend/package.json` for lint, type-check, coverage, and build verification
- [ ] T003 [P] Update execution checkpoints in `specs/032-code-quality-check/checklists/requirements.md` and `specs/032-code-quality-check/quickstart.md` for the seven user-story phases

---

## Phase 2: Foundational

**Purpose**: Establish shared primitives that later user stories reuse across backend and frontend work.

**⚠️ CRITICAL**: Complete this phase before starting user-story implementation.

- [x] T004 Implement shared backend exception and caching primitives in `backend/src/logging_utils.py` and `backend/src/utils.py`
- [x] T005 Implement shared selected-project and service access helpers in `backend/src/dependencies.py`
- [ ] T006 [P] Harden shared dialog and class-composition primitives in `frontend/src/components/ui/confirmation-dialog.tsx` and `frontend/src/lib/utils.ts`
- [ ] T007 [P] Extend shared accessibility and render-test helpers in `frontend/src/test/a11y-helpers.ts` and `frontend/src/test/test-utils.tsx`

**Checkpoint**: Shared backend/frontend helpers are ready for story-specific refactors.

---

## Phase 3: User Story 1 - Fix Silent Failures and Security Vulnerabilities (Priority: P1) 🎯 MVP

**Goal**: Make backend failures visible in logs, stop leaking internal exception details externally, and lock CORS down to the explicit HTTP methods in the specification.

**Independent Test**: Trigger representative backend failures and verify every handled exception logs context, Signal replies stay generic, and CORS only allows `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, and `OPTIONS`.

### Tests for User Story 1

- [ ] T008 [P] [US1] Add exception-handling regression coverage in `backend/tests/unit/test_exceptions.py` and `backend/tests/unit/test_logging_utils.py`
- [ ] T009 [P] [US1] Add security regression coverage for sanitized Signal replies and CORS headers in `backend/tests/unit/test_error_responses.py` and `backend/tests/unit/test_main.py`

### Implementation for User Story 1

- [x] T010 [US1] Narrow and log shared backend exception paths in `backend/src/main.py`, `backend/src/dependencies.py`, and `backend/src/logging_utils.py`
- [x] T011 [US1] Narrow and log API-layer exception paths in `backend/src/api/auth.py`, `backend/src/api/board.py`, `backend/src/api/cleanup.py`, `backend/src/api/health.py`, `backend/src/api/projects.py`, `backend/src/api/settings.py`, `backend/src/api/signal.py`, `backend/src/api/tasks.py`, `backend/src/api/tools.py`, `backend/src/api/webhooks.py`, and `backend/src/api/workflow.py`
- [x] T012 [US1] Narrow and log service-layer exception paths in `backend/src/services/agent_creator.py`, `backend/src/services/cleanup_service.py`, `backend/src/services/completion_providers.py`, `backend/src/services/copilot_polling/agent_output.py`, `backend/src/services/copilot_polling/completion.py`, `backend/src/services/copilot_polling/helpers.py`, `backend/src/services/copilot_polling/pipeline.py`, `backend/src/services/copilot_polling/polling_loop.py`, `backend/src/services/copilot_polling/recovery.py`, `backend/src/services/database.py`, `backend/src/services/encryption.py`, `backend/src/services/github_commit_workflow.py`, `backend/src/services/metadata_service.py`, `backend/src/services/model_fetcher.py`, `backend/src/services/signal_bridge.py`, `backend/src/services/signal_delivery.py`, `backend/src/services/tools/service.py`, `backend/src/services/websocket.py`, `backend/src/services/workflow_orchestrator/config.py`, and `backend/src/services/workflow_orchestrator/orchestrator.py`
- [x] T013 [US1] Replace external exception detail leaks with `safe_error_response()` in `backend/src/services/signal_chat.py`
- [x] T014 [US1] Restrict allowed CORS methods and remove the related remediation comment in `backend/src/main.py`

**Checkpoint**: User Story 1 is independently releasable once backend failures are logged, Signal replies are sanitized, and CORS is explicit.

---

## Phase 4: User Story 2 - Eliminate Duplicated Patterns (Priority: P1)

**Goal**: Consolidate repeated backend and frontend patterns onto shared repository-resolution, error-handling, cache, validation, dialog, and class-name utilities.

**Independent Test**: Verify all targeted call sites use canonical helpers, ad-hoc implementations are removed, dialogs preserve accessibility/overflow behavior, and dynamic class names route through `cn()`.

### Tests for User Story 2

- [ ] T015 [P] [US2] Add repository-resolution and cache-helper regression tests in `backend/tests/unit/test_utils.py`, `backend/tests/unit/test_api_workflow.py`, and `backend/tests/unit/test_api_chat.py`
- [ ] T016 [P] [US2] Add modal composition and responsive overflow tests in `frontend/src/components/board/IssueDetailModal.test.tsx`, `frontend/src/components/board/AgentPresetSelector.test.tsx`, and `frontend/src/components/pipeline/UnsavedChangesDialog.test.tsx`

### Implementation for User Story 2

- [x] T017 [US2] Remove ad-hoc repository resolution in `backend/src/api/workflow.py`, `backend/src/api/chat.py`, and `backend/src/main.py`
- [ ] T018 [US2] Adopt `handle_service_error()` across route handlers in `backend/src/api/agents.py`, `backend/src/api/chores.py`, `backend/src/api/cleanup.py`, `backend/src/api/projects.py`, `backend/src/api/tasks.py`, `backend/src/api/tools.py`, and `backend/src/api/workflow.py`
- [ ] T019 [US2] Extract and apply `cached_fetch()` in `backend/src/utils.py`, `backend/src/api/projects.py`, `backend/src/api/board.py`, and `backend/src/api/chat.py`
- [x] T020 [US2] Add `require_selected_project()` and replace inline guards in `backend/src/dependencies.py`, `backend/src/api/chat.py`, `backend/src/api/tasks.py`, `backend/src/api/chores.py`, and `backend/src/api/workflow.py`
- [ ] T021 [P] [US2] Recompose modal workflows on `ConfirmationDialog` in `frontend/src/components/board/AgentPresetSelector.tsx`, `frontend/src/components/board/IssueDetailModal.tsx`, `frontend/src/components/pipeline/UnsavedChangesDialog.tsx`, `frontend/src/components/agents/BulkModelUpdateDialog.tsx`, and `frontend/src/components/tools/ToolSelectorModal.tsx`
- [x] T022 [P] [US2] Replace template-literal class composition with `cn()` in `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/layout/ProjectSelector.tsx`, `frontend/src/layout/Sidebar.tsx`, `frontend/src/layout/NotificationBell.tsx`, `frontend/src/layout/RateLimitBar.tsx`, `frontend/src/components/chat/ChatPopup.tsx`, `frontend/src/components/chat/ChatToolbar.tsx`, and `frontend/src/components/chat/CommandAutocomplete.tsx`
- [x] T023 [US2] Replace remaining dynamic class string construction with `cn()` in `frontend/src/components/chat/FilePreviewChips.tsx`, `frontend/src/components/chat/IssueRecommendationPreview.tsx`, `frontend/src/components/chat/MentionAutocomplete.tsx`, `frontend/src/components/chat/MessageBubble.tsx`, `frontend/src/components/chat/VoiceInputButton.tsx`, `frontend/src/components/chores/ChoreCard.tsx`, `frontend/src/components/chores/ChoreChatFlow.tsx`, `frontend/src/components/tools/RepoConfigPanel.tsx`, `frontend/src/components/tools/GitHubToolsetSelector.tsx`, `frontend/src/components/tools/ToolCard.tsx`, `frontend/src/components/settings/AdvancedSettings.tsx`, `frontend/src/components/settings/McpSettings.tsx`, `frontend/src/components/settings/SettingsSection.tsx`, `frontend/src/components/settings/SignalConnection.tsx`, `frontend/src/components/pipeline/PipelineBoard.tsx`, `frontend/src/components/pipeline/ModelSelector.tsx`, `frontend/src/components/pipeline/PipelineModelDropdown.tsx`, `frontend/src/components/pipeline/PresetBadge.tsx`, `frontend/src/components/pipeline/SavedWorkflowsList.tsx`, `frontend/src/components/pipeline/AgentNode.tsx`, `frontend/src/components/board/BlockingChainPanel.tsx`, `frontend/src/components/board/AgentConfigRow.tsx`, `frontend/src/components/board/AddAgentPopover.tsx`, `frontend/src/components/board/AgentTile.tsx`, `frontend/src/components/board/IssueCard.tsx`, `frontend/src/components/board/AgentColumnCell.tsx`, `frontend/src/components/board/BlockingIssuePill.tsx`, `frontend/src/components/board/BoardToolbar.tsx`, `frontend/src/components/board/RefreshButton.tsx`, `frontend/src/components/board/CleanUpAuditHistory.tsx`, `frontend/src/components/agents/AgentAvatar.tsx`, `frontend/src/components/agents/AgentCard.tsx`, `frontend/src/components/agents/AgentChatFlow.tsx`, and `frontend/src/components/agents/AddAgentModal.tsx`

**Checkpoint**: User Story 2 is independently testable once shared utilities own the duplicated behaviors on both backend and frontend.

---

## Phase 5: User Story 3 - Break Apart Oversized Files (Priority: P2)

**Goal**: Split the largest backend service, frontend API layer, and pipeline hook into focused modules without breaking existing imports or behavior.

**Independent Test**: Inspect the resulting module structure, confirm public imports remain compatible, and run the relevant backend/frontend tests to prove the split preserved behavior.

### Tests for User Story 3

- [ ] T024 [P] [US3] Add backend service-split regression coverage in `backend/tests/unit/test_github_projects.py` and `backend/tests/unit/test_module_boundaries.py`
- [ ] T025 [P] [US3] Add frontend API and hook compatibility tests in `frontend/src/hooks/usePipelineConfig.test.tsx`, `frontend/src/hooks/useWorkflow.test.tsx`, and `frontend/src/services/api/index.test.ts`

### Implementation for User Story 3

- [ ] T026 [US3] Extract backend issue and pull-request modules in `backend/src/services/github_projects/issues.py`, `backend/src/services/github_projects/pull_requests.py`, and `backend/src/services/github_projects/__init__.py`
- [ ] T027 [US3] Extract backend Copilot and board modules in `backend/src/services/github_projects/copilot.py`, `backend/src/services/github_projects/board.py`, and `backend/src/services/github_projects/__init__.py`
- [ ] T028 [US3] Reduce `backend/src/services/github_projects/service.py` to an orchestration façade and preserve backward-compatible exports in `backend/src/services/github_projects/__init__.py`
- [ ] T029 [P] [US3] Split the frontend API layer into `frontend/src/services/api/client.ts`, `frontend/src/services/api/projects.ts`, `frontend/src/services/api/chat.ts`, `frontend/src/services/api/agents.ts`, `frontend/src/services/api/tools.ts`, `frontend/src/services/api/board.ts`, and `frontend/src/services/api/index.ts`
- [ ] T030 [US3] Migrate API consumers to the new module structure in `frontend/src/hooks/useProjects.ts`, `frontend/src/hooks/useAgents.ts`, `frontend/src/hooks/useTools.ts`, `frontend/src/hooks/useWorkflow.ts`, `frontend/src/hooks/useChat.ts`, `frontend/src/hooks/useProjectBoard.ts`, and remove `frontend/src/services/api.ts`
- [ ] T031 [US3] Decompose pipeline configuration logic into `frontend/src/hooks/usePipelineState.ts`, `frontend/src/hooks/usePipelineMutations.ts`, `frontend/src/hooks/usePipelineValidation.ts`, and `frontend/src/hooks/usePipelineConfig.ts`

**Checkpoint**: User Story 3 is complete when large files are replaced by focused modules with preserved import compatibility.

---

## Phase 6: User Story 4 - Strengthen Type Safety (Priority: P2)

**Goal**: Add explicit backend return types, replace loosely typed structured data, enable stricter TypeScript checks, and eliminate unsafe response casts.

**Independent Test**: Run backend type-checking and frontend compilation with strict unused checks enabled, and confirm all targeted API response paths use proper types or type guards.

### Tests for User Story 4

- [ ] T032 [P] [US4] Add backend typing regression tests for structured service responses in `backend/tests/unit/test_utils.py`, `backend/tests/unit/test_api_board.py`, and `backend/tests/unit/test_github_projects.py`
- [ ] T033 [P] [US4] Add frontend strict-typing regression coverage in `frontend/src/hooks/useProjects.test.tsx`, `frontend/src/hooks/useChat.test.tsx`, and `frontend/src/hooks/usePipelineConfig.test.tsx`

### Implementation for User Story 4

- [ ] T034 [US4] Add explicit return types to backend shared utilities and API entrypoints in `backend/src/utils.py`, `backend/src/dependencies.py`, `backend/src/api/board.py`, `backend/src/api/chat.py`, `backend/src/api/tasks.py`, and `backend/src/api/workflow.py`
- [ ] T035 [US4] Replace generic structured returns with `TypedDict` models in `backend/src/services/github_projects/service.py`, `backend/src/services/agents/service.py`, `backend/src/services/tools/service.py`, and `backend/src/services/metadata_service.py`
- [x] T036 [US4] Enable `noUnusedLocals` and `noUnusedParameters` and resolve resulting compile errors in `frontend/tsconfig.json`, `frontend/src/hooks/useBoardControls.ts`, `frontend/src/hooks/useChat.ts`, `frontend/src/hooks/usePipelineConfig.ts`, `frontend/src/pages/AgentsPage.tsx`, and `frontend/src/pages/ProjectsPage.tsx`
- [ ] T037 [US4] Replace unsafe response casts with type guards in `frontend/src/services/api/client.ts`, `frontend/src/components/settings/McpSettings.tsx`, `frontend/src/components/board/AgentColumnCell.tsx`, and `frontend/src/hooks/useChat.ts`

**Checkpoint**: User Story 4 is independently complete when backend and frontend static analysis both pass with the new type-safety requirements.

---

## Phase 7: User Story 5 - Remove Technical Debt and Legacy Patterns (Priority: P3)

**Goal**: Remove singleton patterns and legacy anti-patterns, harden migration handling, persist chat state, and clean up unused frontend test infrastructure.

**Independent Test**: Verify services are resolved through DI, dynamic imports are gone, migration-prefix handling is explicit, chat state survives restart through SQLite, and the frontend has one active test directory without `jsdom`.

### Tests for User Story 5

- [ ] T038 [P] [US5] Add dependency-injection and persistence regression tests in `backend/tests/unit/test_ai_agent.py`, `backend/tests/unit/test_workflow_orchestrator.py`, `backend/tests/unit/test_database.py`, and `backend/tests/unit/test_api_chat.py`
- [ ] T039 [P] [US5] Add frontend cleanup regression coverage for consolidated test utilities in `frontend/src/test/setup.ts`, `frontend/src/test/test-utils.tsx`, and `frontend/src/test/utils/formatAgentName.test.ts`

### Implementation for User Story 5

- [ ] T040 [US5] Replace module-level singletons with app-state factories in `backend/src/services/ai_agent.py`, `backend/src/services/workflow_orchestrator/orchestrator.py`, `backend/src/services/cache.py`, `backend/src/services/github_projects/service.py`, `backend/src/dependencies.py`, and `backend/src/main.py`
- [x] T041 [US5] Replace the dynamic import anti-pattern with standard imports in `backend/src/services/chores/template_builder.py` and adjust coverage in `backend/tests/unit/test_chores_service.py`
- [x] T042 [US5] Implement duplicate-migration prefix detection and reconciliation logging in `backend/src/services/database.py`, `backend/src/migrations/013_agent_config_lifecycle_status.sql`, `backend/src/migrations/013_pipeline_configs.sql`, `backend/src/migrations/014_agent_default_models.sql`, `backend/src/migrations/014_extend_mcp_tools.sql`, `backend/src/migrations/015_agent_icon_name.sql`, and `backend/src/migrations/015_pipeline_mcp_presets.sql`
- [ ] T043 [US5] Persist chat history with bounded retention using existing schema in `backend/src/api/chat.py`, `backend/src/services/database.py`, and `backend/src/migrations/012_chat_persistence.sql`
- [x] T044 [US5] Remove `jsdom` and consolidate test directories in `frontend/package.json`, `frontend/package-lock.json`, `frontend/src/test/utils/formatAgentName.test.ts`, and delete `frontend/src/tests/utils/formatAgentName.test.ts`
- [ ] T045 [US5] Resolve remaining tracked remediation comments in `backend/src/main.py`, `backend/src/api/chat.py`, `backend/src/services/database.py`, and `backend/src/services/github_projects/service.py`

**Checkpoint**: User Story 5 is independently complete when legacy global state and cleanup TODOs are replaced with explicit, testable implementations.

---

## Phase 8: User Story 6 - Improve Performance and Observability (Priority: P3)

**Goal**: Reduce unnecessary frontend recomputation, cancel stale requests, and cap backend in-memory growth.

**Independent Test**: Verify memoized computations stop re-running needlessly, aborted requests do not update stale UI state, and backend caches/stores evict old entries once size limits are reached.

### Tests for User Story 6

- [ ] T046 [P] [US6] Add backend cache-boundary regression tests in `backend/tests/unit/test_cache.py`, `backend/tests/unit/test_database.py`, and `backend/tests/unit/test_chat_block.py`
- [ ] T047 [P] [US6] Add frontend memoization and request-cancellation regression tests in `frontend/src/hooks/useProjects.test.tsx`, `frontend/src/hooks/useWorkflow.test.tsx`, and `frontend/src/hooks/useChat.test.tsx`

### Implementation for User Story 6

- [ ] T048 [US6] Memoize expensive page and board computations in `frontend/src/pages/AgentsPage.tsx`, `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/pages/AppPage.tsx`, `frontend/src/components/board/ProjectBoard.tsx`, and `frontend/src/components/pipeline/PipelineBoard.tsx`
- [ ] T049 [US6] Propagate `AbortSignal` through the frontend data layer in `frontend/src/services/api/client.ts`, `frontend/src/services/api/chat.ts`, `frontend/src/services/api/projects.ts`, `frontend/src/hooks/useChat.ts`, `frontend/src/hooks/useProjects.ts`, and `frontend/src/hooks/useWorkflow.ts`
- [ ] T050 [US6] Enforce bounded-size eviction across in-memory stores in `backend/src/services/cache.py`, `backend/src/services/metadata_service.py`, `backend/src/api/chat.py`, `backend/src/services/session_store.py`, and `backend/src/services/blocking_queue.py`

**Checkpoint**: User Story 6 is independently complete when renders are stable, aborted requests are harmless, and in-memory data structures stay within configured bounds.

---

## Phase 9: User Story 7 - Close Testing and Linting Gaps (Priority: P4)

**Goal**: Fill backend/frontend coverage gaps, improve accessibility assertions, and enforce stronger lint/build quality checks.

**Independent Test**: Run backend and frontend test suites plus lint/type-check/build to confirm the new coverage, accessibility assertions, lint rules, and bundle-analysis output all work together.

### Tests for User Story 7

- [ ] T051 [P] [US7] Add backend exception-path coverage for narrowed handlers in `backend/tests/unit/test_exceptions.py`, `backend/tests/unit/test_api_workflow.py`, and `backend/tests/unit/test_error_responses.py`
- [ ] T052 [P] [US7] Add render and accessibility coverage for core pages in `frontend/src/pages/AgentsPage.test.tsx`, `frontend/src/pages/ProjectsPage.test.tsx`, `frontend/src/pages/AppPage.test.tsx`, and `frontend/src/test/a11y-helpers.ts`
- [ ] T053 [P] [US7] Add chat live-region accessibility tests in `frontend/src/components/chat/ChatInterface.test.tsx` and `frontend/src/components/chat/MessageBubble.test.tsx`

### Implementation for User Story 7

- [ ] T054 [US7] Expand frontend page and component coverage in `frontend/src/pages/AgentsPage.test.tsx`, `frontend/src/pages/ProjectsPage.test.tsx`, `frontend/src/pages/AppPage.test.tsx`, `frontend/src/components/agents/__tests__/AgentsPanel.test.tsx`, and `frontend/src/components/board/ProjectBoard.test.tsx`
- [ ] T055 [US7] Add ARIA live-region support for chat updates in `frontend/src/components/chat/ChatInterface.tsx`, `frontend/src/components/chat/MessageBubble.tsx`, and `frontend/src/components/chat/SystemMessage.tsx`
- [ ] T056 [US7] Add import-order and React lint rules in `frontend/eslint.config.js` and `frontend/package.json`
- [ ] T057 [US7] Add bundle-analysis reporting to the build in `frontend/vite.config.ts` and `frontend/package.json`

**Checkpoint**: User Story 7 is independently complete when coverage, accessibility checks, linting, and build analysis all run cleanly.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Execute the full verification flow and capture any final cross-story cleanup.

- [ ] T058 [P] Run backend verification commands from `specs/032-code-quality-check/quickstart.md` against `backend/pyproject.toml` and `backend/tests/unit/test_module_boundaries.py`
- [ ] T059 [P] Run frontend verification commands from `specs/032-code-quality-check/quickstart.md` against `frontend/package.json`, `frontend/tsconfig.json`, `frontend/eslint.config.js`, and `frontend/vite.config.ts`
- [ ] T060 Complete the final acceptance checklist and document any follow-up deltas in `specs/032-code-quality-check/checklists/requirements.md` and `specs/032-code-quality-check/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** → no dependencies.
- **Phase 2: Foundational** → depends on Setup and blocks all user stories.
- **Phase 3 / US1** → starts after Foundational; recommended MVP start because it removes active reliability and security risk.
- **Phase 4 / US2** → starts after Foundational; can overlap with late US1 verification, but backend file overlap makes sequential execution safer for one implementer.
- **Phase 5 / US3** → depends on US2 because the decomposition should preserve the shared helpers introduced earlier.
- **Phase 6 / US4** → depends on US3 so type work lands on stable module boundaries.
- **Phase 7 / US5** → depends on US3 and should follow US4 for fewer moving type signatures during DI/persistence work.
- **Phase 8 / US6** → depends on US3 because AbortSignal wiring and memoization rely on the split frontend API/hook structure.
- **Phase 9 / US7** → depends on US1-US6 so tests and lint rules target the final architecture.
- **Phase 10: Polish** → depends on all desired user stories being complete.

### User Story Completion Order

1. **US1** - Fix Silent Failures and Security Vulnerabilities
2. **US2** - Eliminate Duplicated Patterns
3. **US3** - Break Apart Oversized Files
4. **US4** - Strengthen Type Safety
5. **US5** - Remove Technical Debt and Legacy Patterns
6. **US6** - Improve Performance and Observability
7. **US7** - Close Testing and Linting Gaps

### Within Each User Story

- Write the listed tests first and confirm they fail for the targeted behavior.
- Complete shared or structural implementation tasks before cleanup tasks in the same story.
- Re-run the story's independent verification before moving to the next priority.

---

## Parallel Opportunities

### User Story 1

- `T008` and `T009` can run in parallel because they touch separate backend test files.
- After tests exist, `T011` and `T013` can be split between API-layer and Signal-service workstreams.

```text
Parallel example (US1): T008 + T009, then T011 + T013
```

### User Story 2

- `T015` and `T016` can run in parallel because backend and frontend regression tests are isolated.
- `T021` and `T022` can run in parallel because the dialog refactor and the first `cn()` migration touch different frontend files.

```text
Parallel example (US2): T015 + T016, then T021 + T022
```

### User Story 3

- `T024` and `T025` can run in parallel as backend/frontend compatibility tests.
- `T029` can proceed in parallel with backend extraction work in `T026`-`T028` because the file sets are separate.

```text
Parallel example (US3): T024 + T025, then T026/T027/T028 alongside T029
```

### User Story 4

- `T032` and `T033` can run in parallel.
- Backend typing work (`T034`-`T035`) can be staffed separately from frontend strictness work (`T036`-`T037`).

```text
Parallel example (US4): T032 + T033, then T034/T035 alongside T036/T037
```

### User Story 5

- `T038` and `T039` can run in parallel because backend DI coverage and frontend test cleanup are isolated.
- `T041` and `T044` can run in parallel after `T040` starts because they touch separate backend/frontend concerns.

```text
Parallel example (US5): T038 + T039, then T041 + T044
```

### User Story 6

- `T046` and `T047` can run in parallel as backend/frontend regression tests.
- `T048` and `T050` can be split across frontend and backend implementers.

```text
Parallel example (US6): T046 + T047, then T048 + T050
```

### User Story 7

- `T051`, `T052`, and `T053` can run in parallel because they target separate test surfaces.
- `T056` and `T057` can run in parallel after accessibility work begins because lint config and Vite config are separate files.

```text
Parallel example (US7): T051 + T052 + T053, then T056 + T057
```

---

## Implementation Strategy

### MVP First

1. Complete **Phase 1: Setup**.
2. Complete **Phase 2: Foundational**.
3. Complete **Phase 3: User Story 1**.
4. Run the Phase 1 quickstart verification commands in `specs/032-code-quality-check/quickstart.md`.
5. Demo or ship the MVP once logging, sanitized external errors, and explicit CORS behavior are verified.

### Incremental Delivery

1. Deliver **US1** to remove active security/reliability risk.
2. Deliver **US2** to normalize helpers before deeper refactors.
3. Deliver **US3** and **US4** to stabilize structure and typing.
4. Deliver **US5** and **US6** as maintenance/performance hardening.
5. Finish with **US7** and **Phase 10** to lock in automated quality gates.

### Suggested Team Split

- **Developer A**: backend refactors (`US1`, backend half of `US2`, backend half of `US5`, backend half of `US6`)
- **Developer B**: frontend refactors (`US2` frontend half, `US3` frontend half, `US4` frontend half, `US7`)
- **Developer C**: structural cross-cutting work (`US3` backend split, `US5` DI/persistence, final verification)

### Suggested MVP Scope

- **Recommended MVP**: Setup + Foundational + **User Story 1** only.
- **Reason**: US1 removes the highest-risk silent failure and security issues while remaining independently testable.

---

## Notes

- All tasks use the required checklist format with sequential IDs.
- `[P]` is applied only where the file sets are independent enough to execute concurrently.
- `[US#]` labels appear only on user-story tasks.
- Every task description includes exact repository-relative file paths.
