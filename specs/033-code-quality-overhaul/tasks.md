---
title: "Tasks: Code Quality & Technical Debt Overhaul"
description: "Executable task list for code quality & technical debt overhaul"
---

# Tasks: Code Quality & Technical Debt Overhaul

**Input**: Design documents from `specs/033-code-quality-overhaul/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Tests are required by this feature. Each user story includes test or verification tasks before implementation tasks, plus story-level verification at the end.

**Organization**: Tasks are grouped by setup, shared foundations, and then by user story so each increment can be implemented and verified independently.

## Format: `[ID] [P?] [Story for US tasks only] Description`

- **[P]**: Can run in parallel with other tasks in the same phase because the work targets different files.
- **[Story]**: Required on every user-story task only (`[US1]` ... `[US6]`); omit it for setup, foundational, and polish tasks.
- Every task below includes explicit repository-relative file paths.

## Path Conventions

- **Backend**: `backend/src/` and `backend/tests/`
- **Frontend**: `frontend/src/`
- **Infrastructure**: `docker-compose.yml`, `backend/pyproject.toml`, `frontend/Dockerfile`, `frontend/package.json`

## Phase 1: Setup (Dead Code & Build Artifact Cleanup)

**Purpose**: Clean the baseline so later refactors start from accurate analysis, valid tests, and current shared helpers.

- [ ] T001 Audit and remove stale cleanup tests in `backend/tests/` that reference commented-out code or the pre-adoption behavior of `handle_service_error()` and `safe_error_response()`
- [x] T002 Update analysis exclusions for coverage artifacts in `backend/pyproject.toml` so `backend/htmlcov/` is outside static-analysis scope
- [x] T003 [P] Remove commented-out code blocks without tracked TODOs from `backend/src/services/copilot_polling/agent_output.py`
- [x] T004 [P] Remove commented-out code blocks without tracked TODOs from `backend/src/services/copilot_polling/pipeline.py`
- [x] T005 [P] Remove commented-out code blocks without tracked TODOs from `backend/src/services/workflow_orchestrator/orchestrator.py`
- [x] T006 Decide whether to adopt or delete `handle_service_error()` and `safe_error_response()` in `backend/src/logging_utils.py` before shared error-handling work begins

**Checkpoint**: Baseline cleanup is complete and the repository is ready for shared infrastructure work.

---

## Phase 2: Foundational (DRY Helpers & Structured Logging Infrastructure)

**Purpose**: Establish shared logging, helper, and error-handling infrastructure that all later stories rely on.

**⚠️ CRITICAL**: Complete this phase before starting any user-story work.

- [ ] T007 Configure root structured JSON logging in `backend/src/main.py` and `backend/src/logging_utils.py` per `specs/033-code-quality-overhaul/contracts/structured-logging.md`
- [ ] T008 [P] Standardize logger acquisition and structured `extra={}` usage across `backend/src/api/` and `backend/src/services/`
- [x] T009 [P] Finalize the canonical repository-resolution contract and `cached_fetch()` helper in `backend/src/utils.py`
- [x] T010 [P] Add `require_selected_project()` and related dependency wiring in `backend/src/dependencies.py`
- [x] T011 Implement the shared GitHub error-handling pattern in `backend/src/logging_utils.py` and `backend/src/exceptions.py`
- [x] T012 Run `pytest -x` and `ruff check` against `backend/src/` and `backend/tests/` to confirm the shared foundation is stable

**Checkpoint**: Shared helpers, logging, and backend error handling are ready; user stories can now proceed.

---

## Phase 3: User Story 1 - Developer Encounters a Bug in the Polling Pipeline (Priority: P1) 🎯 MVP

**Goal**: Break the largest backend complexity hotspots into focused helpers so a developer can isolate a bug in the polling pipeline without reading monolithic functions.

**Independent Test**: `cgc analyze complexity` shows all targeted backend functions under the required threshold, and `pytest -x` passes for the refactored backend modules.

### Tests for User Story 1

- [ ] T013 [P] [US1] Add failing regression tests for helper extraction in `backend/tests/unit/test_agent_output.py` and `backend/tests/unit/test_recovery.py`
- [ ] T014 [P] [US1] Add failing regression tests for orchestration flow changes in `backend/tests/unit/test_workflow_orchestrator.py` and `backend/tests/unit/test_polling_loop.py`
- [ ] T015 [P] [US1] Add failing regression tests for chat persistence and cleanup classification in `backend/tests/unit/test_api_chat.py` and `backend/tests/unit/test_cleanup_service.py`

### Implementation for User Story 1

- [x] T016 [US1] Add `CommentScanResult` and extract `post_agent_outputs_from_pr()` helpers in `backend/src/services/copilot_polling/agent_output.py`
- [x] T017 [US1] Add `AgentResolution` and split `assign_agent_for_status()` into focused resolvers in `backend/src/services/workflow_orchestrator/orchestrator.py`
- [x] T018 [US1] Extend `AgentStepState` in `backend/src/models/agent.py` and replace emoji parsing in `backend/src/services/copilot_polling/recovery.py`
- [x] T019 [US1] Add `PollStep` plus a data-driven step list in `backend/src/services/copilot_polling/polling_loop.py`
- [x] T020 [US1] Create the `chat_messages` SQLite migration in `backend/src/migrations/` for persistent chat storage
- [x] T021 [US1] Move chat message persistence from in-memory storage to SQLite in `backend/src/api/chat.py`
- [ ] T022 [US1] Extract chat command dispatch handlers from `backend/src/api/chat.py` into focused command-processing helpers
- [x] T023 [US1] Add `ItemClassification` and split `preflight()` responsibilities in `backend/src/services/cleanup_service.py`
- [x] T024 [US1] Refactor `_reconstruct_pipeline_state()` in `backend/src/services/copilot_polling/pipeline.py` and `get_board_data()` in `backend/src/services/github_projects/service.py` into explicit helper flows
- [ ] T025 [US1] Run `cgc analyze complexity` and `pytest -x` for `backend/src/services/copilot_polling/`, `backend/src/services/workflow_orchestrator/`, `backend/src/api/chat.py`, and `backend/tests/unit/`

**Checkpoint**: The backend polling and orchestration hotspots are decomposed, testable, and below the complexity threshold.

---

## Phase 4: User Story 2 - Developer Adds a New API Endpoint That Needs Repository Info (Priority: P1)

**Goal**: Eliminate duplicated repository, project-selection, cache, and case-insensitive lookup logic so new API endpoints follow one documented path.

**Independent Test**: All repository-resolution callers use `resolve_repository()`, duplicate helper code is removed, and `pytest -x`, `ruff check`, and frontend tests pass for the touched modules.

### Tests for User Story 2

- [ ] T026 [P] [US2] Add failing regression tests for repository fallback behavior in `backend/tests/unit/test_utils.py`, `backend/tests/unit/test_api_workflow.py`, and `backend/tests/unit/test_api_chat.py`
- [ ] T027 [P] [US2] Add failing helper-adoption tests in `backend/tests/unit/test_error_responses.py` and `frontend/src/hooks/useAgentConfig.test.tsx`

### Implementation for User Story 2

- [x] T028 [US2] Consolidate repository fallback logic on `resolve_repository()` in `backend/src/utils.py` and remove duplicate resolution code from `backend/src/api/chat.py`, `backend/src/api/workflow.py`, and `backend/src/main.py`
- [x] T029 [US2] Adopt `require_selected_project()` in `backend/src/api/chat.py`, `backend/src/api/workflow.py`, `backend/src/api/tasks.py`, and `backend/src/api/chores.py`
- [ ] T030 [US2] Replace inline cache management with `cached_fetch()` in `backend/src/api/projects.py`, `backend/src/api/board.py`, `backend/src/api/chat.py`, and `backend/src/api/workflow.py`
- [x] T031 [US2] Apply the shared GitHub error-handling pattern in `backend/src/api/board.py`, `backend/src/api/projects.py`, `backend/src/api/workflow.py`, and `backend/src/api/tasks.py`
- [x] T032 [P] [US2] Create `case_insensitive_get()` in `frontend/src/lib/case-utils.ts` and replace inline key-matching logic in `frontend/src/hooks/useAgentConfig.ts`
- [ ] T033 [US2] Run `pytest -x`, `ruff check`, and `npx vitest run` for `backend/src/api/`, `backend/src/utils.py`, `frontend/src/hooks/useAgentConfig.ts`, and related tests

**Checkpoint**: Repository and endpoint helper behavior is centralized, consistent, and independently verified.

---

## Phase 5: User Story 3 - Developer Needs to Modify Issue Creation Logic (Priority: P2)

**Goal**: Decompose the GitHub API God class into domain services so issue, PR, branch, and board changes happen in focused files with stable contracts.

**Independent Test**: `backend/src/services/github_projects/service.py` is under 1,500 lines, each extracted domain service stays under 800 lines, and callers compile and pass tests.

### Tests for User Story 3

- [ ] T034 [P] [US3] Add failing extraction-contract tests in `backend/tests/unit/test_github_projects.py` and `backend/tests/unit/test_api_projects.py`
- [ ] T035 [P] [US3] Add failing dependency-injection and typed-return tests in `backend/tests/unit/test_api_board.py` and `backend/tests/unit/test_api_workflow.py`

### Implementation for User Story 3

- [x] T036 [US3] Extract static bot-detection utilities to `backend/src/services/github_projects/identities.py` and update callers in `backend/src/services/github_projects/` and `backend/src/api/`
- [x] T037 [US3] Introduce `RateLimitManager` in `backend/src/services/github_projects/rate_limit.py` and adopt it in `backend/src/services/github_projects/service.py`
- [x] T038 [US3] Implement `GitHubBaseClient` in `backend/src/services/github_projects/base_client.py` and rebase `backend/src/services/github_projects/service.py` on the shared client contract
- [x] T039 [P] [US3] After `backend/src/services/github_projects/base_client.py` lands, extract `GitHubBranchService` in `backend/src/services/github_projects/branches.py` and update branch callers in `backend/src/api/workflow.py` and `backend/src/services/github_commit_workflow.py`
- [x] T040 [P] [US3] After `backend/src/services/github_projects/base_client.py` lands, extract `GitHubPullRequestService` in `backend/src/services/github_projects/pull_requests.py` and update callers in `backend/src/api/cleanup.py` and `backend/src/services/cleanup_service.py`
- [x] T041 [P] [US3] After `backend/src/services/github_projects/base_client.py` lands, extract `GitHubIssuesService` in `backend/src/services/github_projects/issues.py` and update callers in `backend/src/api/chat.py` and `backend/src/services/agent_creator.py`
- [x] T042 [P] [US3] After `backend/src/services/github_projects/base_client.py` lands, extract `GitHubProjectBoardService` in `backend/src/services/github_projects/projects.py` and update callers in `backend/src/api/board.py`, `backend/src/api/projects.py`, and `backend/src/api/tasks.py`
- [ ] T043 [US3] Add new GitHub service dependency getters in `backend/src/dependencies.py` and typed return models in `backend/src/models/project.py`, `backend/src/models/task.py`, and `backend/src/models/workflow.py`
- [ ] T044 [US3] Run `pytest -x`, `pyright`, and `wc -l` checks across `backend/src/services/github_projects/`, `backend/src/dependencies.py`, and `backend/tests/unit/`

**Checkpoint**: GitHub API responsibilities are split by domain, callers use the right service, and service contracts are enforced.

---

## Phase 6: User Story 4 - Developer Modifies the Settings Page Form (Priority: P2)

**Goal**: Break oversized frontend components and hooks into focused units, replace manual form flattening with declarative form handling, and remove type-unsafe data parsing.

**Independent Test**: `npx vitest run`, `npx tsc --noEmit`, and `npx eslint .` pass, and every touched component or hook is within the file-size limits from the plan.

### Tests for User Story 4

- [ ] T045 [P] [US4] Add failing settings-form tests in `frontend/src/components/settings/GlobalSettings.test.tsx` and `frontend/src/components/settings/AISettingsSection.test.tsx`
- [ ] T046 [P] [US4] Add failing hook-and-page regression tests in `frontend/src/hooks/usePipelineConfig.test.tsx`, `frontend/src/hooks/useChat.test.tsx`, and `frontend/src/pages/LoginPage.test.tsx`

### Implementation for User Story 4

- [x] T047 [US4] Split `frontend/src/components/settings/GlobalSettings.tsx` into `frontend/src/components/settings/AISettingsSection.tsx`, `frontend/src/components/settings/DisplaySettings.tsx`, `frontend/src/components/settings/WorkflowSettings.tsx`, and `frontend/src/components/settings/NotificationSettings.tsx`
- [x] T048 [US4] Create `frontend/src/components/settings/globalSettingsSchema.ts` and migrate `frontend/src/components/settings/GlobalSettings.tsx` plus `frontend/package.json` to `react-hook-form`, `zod`, and `@hookform/resolvers`
- [ ] T049 [US4] Decompose `frontend/src/hooks/usePipelineConfig.ts` into `frontend/src/hooks/usePipelineBoard.ts`, `frontend/src/hooks/usePipelineValidation.ts`, `frontend/src/hooks/usePipelineModelOverride.ts`, and `frontend/src/hooks/usePipelineReducer.ts`
- [x] T050 [P] [US4] Extract shared time helpers in `frontend/src/lib/time-utils.ts` and adopt them in `frontend/src/components/chores/FeaturedRitualsPanel.tsx` and `frontend/src/components/chores/ChoreCard.tsx`
- [ ] T051 [P] [US4] Replace unsafe response casts with validated schemas in `frontend/src/hooks/useChat.ts` and `frontend/src/services/api.ts`
- [x] T052 [US4] Extract `frontend/src/components/AnimatedBackground.tsx` from `frontend/src/pages/LoginPage.tsx` and simplify the page structure
- [ ] T053 [US4] Run `npx vitest run`, `npx tsc --noEmit`, and `npx eslint .` for `frontend/src/components/settings/`, `frontend/src/hooks/`, `frontend/src/pages/LoginPage.tsx`, and related tests

**Checkpoint**: The frontend settings and pipeline editing surfaces are split into focused units and validated with tests.

---

## Phase 7: User Story 5 - Operations Verifies Build Reproducibility (Priority: P3)

**Goal**: Pin infrastructure versions and tighten dependency constraints so Docker builds and type-checking behave reproducibly over time.

**Independent Test**: `docker compose build` succeeds, no `latest` tags remain, and `pyright` standard mode passes or has explicit documented exceptions.

### Tests for User Story 5

- [ ] T054 [US5] Capture the failing reproducibility baseline by running `docker compose build` and `pyright` against `docker-compose.yml`, `frontend/Dockerfile`, and `backend/pyproject.toml`

### Implementation for User Story 5

- [ ] T055 [US5] Pin all Docker image tags in `docker-compose.yml` and `frontend/Dockerfile` to explicit semantic versions
- [ ] T056 [US5] Add upper-bound constraints for major Python dependencies and set pyright to standard mode in `backend/pyproject.toml`
- [ ] T057 [US5] Resolve new standard-mode typing findings in `backend/src/` and `backend/tests/unit/`, or document the approved exceptions in `backend/pyproject.toml`
- [ ] T058 [US5] Re-run `docker compose build`, `pytest -x`, and `pyright` for `docker-compose.yml`, `frontend/Dockerfile`, `backend/pyproject.toml`, `backend/src/`, and `backend/tests/unit/`

**Checkpoint**: Build inputs are pinned, dependency bounds are explicit, and reproducibility checks are green.

---

## Phase 8: User Story 6 - Developer Writes Tests for a High-Complexity Function (Priority: P3)

**Goal**: Consolidate mock infrastructure and add durable unit coverage so refactored high-complexity helpers are safe to evolve.

**Independent Test**: Coverage for the refactored backend modules reaches the plan target, and mocks fail fast when callers use invalid signatures.

### Tests for User Story 6

- [ ] T059 [P] [US6] Add failing helper-coverage tests in `backend/tests/unit/test_agent_output.py`, `backend/tests/unit/test_recovery.py`, `backend/tests/unit/test_polling_loop.py`, and `backend/tests/unit/test_cleanup_service.py`
- [ ] T060 [P] [US6] Add failing storage-and-orchestrator coverage tests in `backend/tests/unit/test_api_chat.py`, `backend/tests/unit/test_workflow_orchestrator.py`, and `backend/tests/unit/test_github_projects.py`

### Implementation for User Story 6

- [ ] T061 [US6] Consolidate shared mock factories into `backend/tests/conftest.py` and remove `backend/tests/helpers/mocks.py` imports across `backend/tests/`
- [ ] T062 [US6] Add `spec=` enforcement to async mocks in `backend/tests/conftest.py`, `backend/tests/unit/test_api_workflow.py`, and `backend/tests/unit/test_github_projects.py`
- [ ] T063 [US6] Finish dedicated unit coverage for the refactored helpers in `backend/tests/unit/test_agent_output.py`, `backend/tests/unit/test_recovery.py`, `backend/tests/unit/test_api_chat.py`, `backend/tests/unit/test_cleanup_service.py`, `backend/tests/unit/test_polling_loop.py`, and `backend/tests/unit/test_workflow_orchestrator.py`
- [ ] T064 [US6] Run `pytest --cov` for `backend/src/services/copilot_polling/`, `backend/src/api/chat.py`, `backend/src/services/cleanup_service.py`, and `backend/tests/unit/` to confirm the coverage target

**Checkpoint**: Refactored backend modules have dedicated tests, centralized mocks, and measurable coverage.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Re-run the whole change set against the agreed quality gates and validate the feature documentation workflow.

- [ ] T065 [P] Run the full static-analysis suite against `backend/src/`, `backend/tests/`, `frontend/src/`, and `backend/pyproject.toml`
- [ ] T066 [P] Validate every example in `specs/033-code-quality-overhaul/quickstart.md` against the live code paths in `backend/src/` and `frontend/src/`
- [ ] T067 [P] Verify complexity and file-size targets across `backend/src/services/`, `frontend/src/components/settings/`, and `frontend/src/hooks/`
- [ ] T068 Run the final regression sweep with `pytest -x`, `npx vitest run`, and `docker compose build` for `backend/tests/`, `frontend/src/`, and `docker-compose.yml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** → no dependencies; start immediately.
- **Phase 2: Foundational** → depends on Phase 1; blocks all user stories.
- **Phase 3: US1** → depends on Phase 2; establishes the MVP backend refactor path.
- **Phase 4: US2** → depends on Phase 2; can proceed alongside US1 after shared helpers land.
- **Phase 5: US3** → depends on Phase 2 and benefits from the shared logging/error-handling patterns from Phase 2.
- **Phase 6: US4** → depends on Phase 2; frontend work is otherwise independent of backend refactors.
- **Phase 7: US5** → should start after US1-US4 so pyright standard-mode noise reflects the refactored codebase, matching `research.md` R-007.
- **Phase 8: US6** → depends on US1 and US3 because it adds durable tests around the refactored helpers and domain services.
- **Phase 9: Polish** → depends on all selected user stories being complete.

### User Story Dependencies

- **US1**: Independent after Foundational; recommended MVP story because it attacks the highest-risk backend complexity.
- **US2**: Independent after Foundational; shares only the helper contracts introduced in Phase 2.
- **US3**: Independent after Foundational for extraction sequencing, but it should follow the incremental split order from `research.md` R-002 and only parallelize T039-T042 after T038 is complete.
- **US4**: Independent after Foundational; no required dependency on backend stories.
- **US5**: Depends on earlier refactors being stable before raising pyright strictness and pinning reproducibility inputs.
- **US6**: Depends on the US1/US3 refactors being in place so coverage and `spec=` enforcement target the final interfaces.

### Within Each User Story

- Add or update the listed tests first and confirm they fail for the intended gap.
- Introduce new enums, dataclasses, or helpers before rewiring callers.
- Update call sites only after the destination abstraction is present.
- Finish each story with the listed verification task before moving to a lower-priority story.

### Parallel Opportunities

- **Setup**: T003-T005 can run in parallel because they touch different backend files.
- **Foundational**: T008-T010 can run in parallel after T007 starts the logging baseline.
- **US1**: T013-T015 can run in parallel; T020-T024 can also be split by file ownership once the migration shape is agreed.
- **US2**: T026-T027 and T029-T032 can run in parallel because backend helper adoption and frontend key-matching are isolated.
- **US3**: T034-T035 can run in parallel, and T039-T042 can run in parallel once T036-T038 establish the shared base client and rate-limit infrastructure.
- **US4**: T045-T046 and T050-T052 can run in parallel once the form and hook decomposition plan is agreed.
- **US5**: T055 and T056 can run in parallel because Docker pinning and Python dependency bounds touch different files.
- **US6**: T059-T060 can run in parallel, and T061-T062 can also proceed together once the mock migration plan is clear.
- **Polish**: T065-T067 can run in parallel before the final regression sweep in T068.

---

## Parallel Example: User Story 1

```bash
# Parallelize the up-front regression tests
T013 backend/tests/unit/test_agent_output.py + backend/tests/unit/test_recovery.py
T014 backend/tests/unit/test_workflow_orchestrator.py + backend/tests/unit/test_polling_loop.py
T015 backend/tests/unit/test_api_chat.py + backend/tests/unit/test_cleanup_service.py

# Parallelize implementation once the helper boundaries are agreed
T020 backend/src/migrations/
T021 backend/src/api/chat.py
T023 backend/src/services/cleanup_service.py
T024 backend/src/services/copilot_polling/pipeline.py + backend/src/services/github_projects/service.py
```

## Parallel Example: User Story 2

```bash
# Parallelize helper regression coverage
T026 backend/tests/unit/test_utils.py + backend/tests/unit/test_api_workflow.py + backend/tests/unit/test_api_chat.py
T027 backend/tests/unit/test_error_responses.py + frontend/src/hooks/useAgentConfig.test.tsx

# Parallelize backend and frontend adoption work
T029 backend/src/api/chat.py + backend/src/api/workflow.py + backend/src/api/tasks.py + backend/src/api/chores.py
T032 frontend/src/lib/case-utils.ts + frontend/src/hooks/useAgentConfig.ts
```

## Parallel Example: User Story 3

```bash
# Parallelize contract tests first
T034 backend/tests/unit/test_github_projects.py + backend/tests/unit/test_api_projects.py
T035 backend/tests/unit/test_api_board.py + backend/tests/unit/test_api_workflow.py

# Parallelize domain extraction after the base client lands
T039 backend/src/services/github_projects/branches.py + backend/src/api/workflow.py
T040 backend/src/services/github_projects/pull_requests.py + backend/src/api/cleanup.py
T041 backend/src/services/github_projects/issues.py + backend/src/api/chat.py
T042 backend/src/services/github_projects/projects.py + backend/src/api/board.py + backend/src/api/projects.py + backend/src/api/tasks.py
```

## Parallel Example: User Story 4

```bash
# Parallelize frontend regression tests
T045 frontend/src/components/settings/GlobalSettings.test.tsx + frontend/src/components/settings/AISettingsSection.test.tsx
T046 frontend/src/hooks/usePipelineConfig.test.tsx + frontend/src/hooks/useChat.test.tsx + frontend/src/pages/LoginPage.test.tsx

# Parallelize decompositions by surface area
T050 frontend/src/lib/time-utils.ts + frontend/src/components/chores/FeaturedRitualsPanel.tsx + frontend/src/components/chores/ChoreCard.tsx
T052 frontend/src/components/AnimatedBackground.tsx + frontend/src/pages/LoginPage.tsx
```

## Parallel Example: User Story 5

```bash
# Parallelize reproducibility changes by artifact type
T055 docker-compose.yml + frontend/Dockerfile
T056 backend/pyproject.toml

# Run verification after both land
T058 docker-compose.yml + frontend/Dockerfile + backend/pyproject.toml + backend/src/ + backend/tests/unit/
```

## Parallel Example: User Story 6

```bash
# Parallelize new coverage work
T059 backend/tests/unit/test_agent_output.py + backend/tests/unit/test_recovery.py + backend/tests/unit/test_polling_loop.py + backend/tests/unit/test_cleanup_service.py
T060 backend/tests/unit/test_api_chat.py + backend/tests/unit/test_workflow_orchestrator.py + backend/tests/unit/test_github_projects.py

# Parallelize mock migration and spec enforcement
T061 backend/tests/conftest.py + backend/tests/
T062 backend/tests/conftest.py + backend/tests/unit/test_api_workflow.py + backend/tests/unit/test_github_projects.py
```

---

## Implementation Strategy

### MVP First

1. Complete **Phase 1: Setup**.
2. Complete **Phase 2: Foundational**.
3. Complete **Phase 3: US1**.
4. Validate the MVP with **T025** before moving on.

### Incremental Delivery

1. Deliver **US1** first to remove the riskiest backend complexity hotspots.
2. Deliver **US2** next so all new endpoint work uses one canonical helper set.
3. Deliver **US3** once backend helpers are stable, following the incremental extraction order in `research.md`.
4. Deliver **US4** as the frontend modernization increment.
5. Deliver **US5** after refactors settle, then close with **US6** for coverage hardening.
6. Finish with **Phase 9** for global verification.

### Recommended Execution Order for the Team

1. One engineer drives **Setup + Foundational**.
2. After Phase 2, split work across:
   - Engineer A: **US1**
   - Engineer B: **US2**, then **US3** once the shared GitHub base-client groundwork is in place
   - Engineer C: **US4**
3. Reserve **US5** for the point where the repository is otherwise stable.
4. Use **US6** as the final backend hardening pass before polish.

### Suggested MVP Scope

- **Primary MVP**: **US1** only.
- **Practical MVP extension**: **US1 + US2** if the team wants the main backend complexity win plus the canonical helper cleanup in the same release.

---

## Notes

- All task lines use the required checklist format: checkbox, task ID, optional `[P]`, required user-story label for story tasks, and explicit file paths.
- Story tasks intentionally avoid cross-story labels so progress can be tracked per user story.
- Verification tasks are kept inside each story so every increment is independently testable and shippable.
