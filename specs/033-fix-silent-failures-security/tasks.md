# Tasks: Fix Silent Failures & Security

**Input**: Design documents from `/specs/033-fix-silent-failures-security/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/logging-contract.md, quickstart.md

**Tests**: The feature specification does not require new automated tests or a TDD workflow. This task list relies on the existing backend lint, type-check, unit-test, and static verification commands already documented for the feature.

**Organization**: Tasks are grouped by user story so each story can be completed and validated independently. User Story 1 is the MVP because it restores observability for the highest-impact silent failures.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend source**: `backend/src/`
- **Backend tests**: `backend/tests/unit/`
- **Feature docs**: `specs/033-fix-silent-failures-security/`

---

## Phase 1: Setup

**Purpose**: Confirm the feature scope, implementation surface, and verification contract before editing exception handlers.

- [ ] T001 Review the feature requirements and story priorities in `specs/033-fix-silent-failures-security/spec.md` and `specs/033-fix-silent-failures-security/plan.md`
- [ ] T002 [P] Audit the current critical, high, and medium exception handlers in `backend/src/services/github_projects/service.py`, `backend/src/services/github_projects/__init__.py`, `backend/src/services/metadata_service.py`, `backend/src/services/agent_creator.py`, and `backend/src/services/signal_chat.py`
- [ ] T003 [P] Baseline the remaining bare `except Exception:` sweep in `backend/src/` and capture the expected grep-based verification commands from `specs/033-fix-silent-failures-security/quickstart.md`

**Checkpoint**: The team knows which handlers are already fixed, which files still need changes, and how completion will be verified.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared exception-handling rules that all user stories depend on.

**⚠️ CRITICAL**: No user story work should begin until the logging contract, intentional-catch policy, and verification baseline are aligned.

- [ ] T004 Confirm the shared logging and sanitization patterns to reuse from `backend/src/logging_utils.py` against `specs/033-fix-silent-failures-security/contracts/logging-contract.md`
- [ ] T005 [P] Add or verify documentation comments for intentional broad catches in `backend/src/main.py`, `backend/src/services/signal_bridge.py`, `backend/src/api/workflow.py`, `backend/src/api/chat.py`, `backend/src/services/model_fetcher.py`, `backend/src/services/github_projects/service.py`, `backend/src/services/chores/service.py`, `backend/src/services/ai_agent.py`, and `backend/src/services/workflow_orchestrator/models.py`
- [ ] T006 [P] Prepare the static `grep`/`ruff`/`pyright`/`pytest` verification flow described in `specs/033-fix-silent-failures-security/quickstart.md` and `backend/pyproject.toml`

**Checkpoint**: The implementation contract is defined, intentional exceptions are documented, and the validation flow is ready.

---

## Phase 3: User Story 1 - Eliminate Critical Silent Exception Swallowing (Priority: P1) 🎯 MVP

**Goal**: Ensure the highest-impact silent failures in GitHub project services and metadata fallback paths always emit actionable logs without changing recovery behavior.

**Independent Test**: Trigger the workflow config fetch, branch OID update, cleanup, and metadata fallback failure paths and confirm the expected warning/debug logs with `exc_info=True` are emitted while existing fallbacks still run.

### Implementation for User Story 1

- [ ] T007 [US1] Verify and finish the workflow-config and branch-OID handlers in `backend/src/services/github_projects/service.py` with warning logs, bound exceptions, and the targeted `httpx.HTTPStatusError`/`KeyError`/`ValueError` narrowing from the plan
- [ ] T008 [P] [US1] Verify and finish the client-cleanup handler in `backend/src/services/github_projects/__init__.py` so it keeps a broad bound catch and emits the required debug log with traceback details
- [ ] T009 [P] [US1] Verify and finish the SQLite metadata fallback handler in `backend/src/services/metadata_service.py` so it logs warnings with `repo_key` context and narrows to `aiosqlite.Error`/`KeyError` where safe

**Checkpoint**: The four critical silent-failure paths are observable and still degrade gracefully. This is the MVP.

---

## Phase 4: User Story 2 - Log Database Update Failures in Agent Pipeline (Priority: P1)

**Goal**: Ensure agent-creation persistence failures stop disappearing silently and always leave an auditable error trail.

**Independent Test**: Simulate failures in the issue-number, branch-name, PR-number, and owner/repo resolution update paths and confirm the expected error or warning logs include agent/project context and `exc_info=True`.

### Implementation for User Story 2

- [ ] T010 [US2] Update the `github_issue_number`, `branch_name`, and `github_pr_number` persistence handlers in `backend/src/services/agent_creator.py` to log error-level failures with agent identifiers and traceback details
- [ ] T011 [US2] Update the owner/repo resolution handler in `backend/src/services/agent_creator.py` to log warning-level failures with `project_id` context while preserving the existing fallback path

**Checkpoint**: Agent pipeline write failures are visible in logs instead of being silently swallowed.

---

## Phase 5: User Story 3 - Prevent Exception Detail Leaks to End Users (Priority: P1)

**Goal**: Remove all Signal user-message paths that expose raw Python exception details while keeping detailed diagnostics in server-side logs.

**Independent Test**: Trigger each failing Signal command path in `backend/src/services/signal_chat.py` and verify the user receives a hardcoded friendly error message while the server logs the full exception details.

### Implementation for User Story 3

- [ ] T012 [US3] Audit every exception-driven `_reply(...)` path in `backend/src/services/signal_chat.py` and replace any interpolated exception text with generic friendly Signal responses
- [ ] T013 [US3] Route Signal command failures in `backend/src/services/signal_chat.py` through server-side error logging and shared sanitization helpers from `backend/src/logging_utils.py` where applicable

**Checkpoint**: Signal users no longer see internal exception details, but operators still get full diagnostic logs.

---

## Phase 6: User Story 4 - Log Signal Context Resolution Failures (Priority: P2)

**Goal**: Make missing repository context in the Signal flow observable without changing the degraded execution path.

**Independent Test**: Force repository-context resolution to fail in `backend/src/services/signal_chat.py` and confirm the flow continues with a warning log that includes the project identifier and traceback details.

### Implementation for User Story 4

- [ ] T014 [US4] Verify and finish the repository-context resolution handler in `backend/src/services/signal_chat.py` so it emits the required warning log with `project_id` context and `exc_info=True`
- [ ] T015 [US4] Confirm the downstream no-context flow in `backend/src/services/signal_chat.py` keeps its existing behavior after logging is added and does not introduce new user-facing leaks

**Checkpoint**: Signal context-loss events are diagnosable without breaking the existing graceful-degradation path.

---

## Phase 7: User Story 5 - Narrow Exception Types and Add Binding (Priority: P2)

**Goal**: Finish the repository-wide exception-handling hygiene sweep by binding remaining broad catches, tightening specific handlers where safe, and leaving only documented resilience exceptions behind.

**Independent Test**: Run the documented static search across `backend/src/` and confirm that remaining bare `except Exception:` sites are either intentionally documented or part of `backend/src/logging_utils.py`, with the targeted services and APIs updated to use `as e` and improved logging.

### Implementation for User Story 5

- [ ] T016 [P] [US5] Add `as e` bindings and improved logging context to the remaining broad handlers in `backend/src/services/workflow_orchestrator/config.py`, `backend/src/services/chores/template_builder.py`, and `backend/src/services/blocking_queue.py`
- [ ] T017 [P] [US5] Add `as e` bindings and improved logging context to the remaining broad handlers in `backend/src/services/agents/service.py` and `backend/src/services/copilot_polling/pipeline.py`
- [ ] T018 [US5] Add `as e` bindings, improved logging, and intentional-flow comments to the remaining broad handlers in `backend/src/services/chores/service.py`
- [ ] T019 [P] [US5] Add `as e` bindings and include exception context in the API-layer handlers in `backend/src/api/tasks.py`, `backend/src/api/projects.py`, `backend/src/api/signal.py`, `backend/src/api/chores.py`, `backend/src/api/workflow.py`, `backend/src/api/auth.py`, and `backend/src/api/chat.py`
- [ ] T020 [US5] Re-scan `backend/src/` to verify that only the documented resilience blocks in `backend/src/logging_utils.py` remain as bare `except Exception:` catches without `as e`

**Checkpoint**: The exception-handling sweep is complete, precise, and aligned with the documented intentional exceptions.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Run the feature-specific verification flow and make sure the final implementation is safe, observable, and regression-checked.

- [ ] T021 [P] Run the manual and static verification scenarios from `specs/033-fix-silent-failures-security/quickstart.md` against `backend/src/services/github_projects/service.py`, `backend/src/services/agent_creator.py`, `backend/src/services/metadata_service.py`, and `backend/src/services/signal_chat.py`
- [ ] T022 [P] Run `uv run --extra dev ruff check src/`, `uv run --extra dev pyright src/`, and `uv run --extra dev pytest tests/unit/ -x` from `backend/pyproject.toml` after the exception-handling changes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: Depend on Foundational completion
  - **US1**, **US2**, and **US3** are all P1 and should be delivered before P2 cleanup work
  - **US4** depends on the Signal command surface reviewed in **US3**
  - **US5** should follow the focused story fixes so the broad exception sweep incorporates the earlier targeted changes
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - no dependency on other stories
- **User Story 2 (P1)**: Can start after Foundational - independent of US1 except for shared logging conventions
- **User Story 3 (P1)**: Can start after Foundational - independent of US1/US2 except for shared sanitization patterns
- **User Story 4 (P2)**: Depends on US3 because both tasks modify `backend/src/services/signal_chat.py`
- **User Story 5 (P2)**: Depends on US1-US4 so the repository-wide sweep does not overwrite earlier focused fixes

### Within Each User Story

- Review the current handler state before editing
- Preserve existing control flow and fallback behavior while adding logging or narrowing catches
- Apply binding (`as e`) before adjusting log messages
- Finish the static/manual verification for the story before moving to the next priority tier

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel after T001 defines the scope
- **Phase 2**: T005 and T006 can run in parallel once T004 confirms the shared contract
- **US1**: T008 and T009 can run in parallel with T007 because they touch different files
- **US5**: T016, T017, and T019 can run in parallel because they update different file groups
- **Phase 8**: T021 and T022 can run in parallel after implementation stabilizes

---

## Parallel Execution Examples

### User Story 1

```text
Task T007: Finish service-level critical logging and narrowing in backend/src/services/github_projects/service.py
Task T008: Finish cleanup logging in backend/src/services/github_projects/__init__.py
Task T009: Finish metadata fallback logging in backend/src/services/metadata_service.py
```

### User Story 2

```text
Task T010: Update agent DB write failure logging in backend/src/services/agent_creator.py
Task T011: Follow with owner/repo resolution warning logging in backend/src/services/agent_creator.py
# Same file and overlapping flow: execute sequentially, not in parallel.
```

### User Story 3

```text
Task T012: Audit and replace user-facing exception leaks in backend/src/services/signal_chat.py
Task T013: Add server-side logging and helper reuse in backend/src/services/signal_chat.py
# Same file and overlapping handlers: execute sequentially, not in parallel.
```

### User Story 4

```text
Task T014: Finish repository-context warning logging in backend/src/services/signal_chat.py
Task T015: Verify the downstream no-context behavior in backend/src/services/signal_chat.py
# Same file and same flow: execute sequentially, not in parallel.
```

### User Story 5

```text
Task T016: Update backend/src/services/workflow_orchestrator/config.py, backend/src/services/chores/template_builder.py, and backend/src/services/blocking_queue.py
Task T017: Update backend/src/services/agents/service.py and backend/src/services/copilot_polling/pipeline.py
Task T019: Update backend/src/api/tasks.py, backend/src/api/projects.py, backend/src/api/signal.py, backend/src/api/chores.py, backend/src/api/workflow.py, backend/src/api/auth.py, and backend/src/api/chat.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Trigger the four critical failure paths and confirm warning/debug logging is present
5. Demo or merge the observability MVP before expanding to additional handlers if needed

### Incremental Delivery

1. Complete Setup + Foundational to lock the exception-handling contract
2. Deliver US1 for the critical silent-failure paths (**MVP**)
3. Deliver US2 so agent persistence failures are observable
4. Deliver US3 to close user-facing exception leaks
5. Deliver US4 to capture Signal context-loss warnings
6. Deliver US5 to finish the broader exception-binding/narrowing sweep
7. Finish with Phase 8 verification

### Parallel Team Strategy

With multiple developers:

1. One developer completes Setup + Foundational alignment
2. Then split the focused P1 work:
   - Developer A: US1 in `backend/src/services/github_projects/` and `backend/src/services/metadata_service.py`
   - Developer B: US2 in `backend/src/services/agent_creator.py`
   - Developer C: US3 in `backend/src/services/signal_chat.py`
3. After the P1 stories merge, split the P2 cleanup sweep:
   - Developer A: US4 follow-up in `backend/src/services/signal_chat.py`
   - Developer B: US5 service-layer sweep in `backend/src/services/`
   - Developer C: US5 API-layer sweep in `backend/src/api/`

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 22 |
| **Setup tasks** | 3 (T001-T003) |
| **Foundational tasks** | 3 (T004-T006) |
| **US1 tasks** | 3 (T007-T009) |
| **US2 tasks** | 2 (T010-T011) |
| **US3 tasks** | 2 (T012-T013) |
| **US4 tasks** | 2 (T014-T015) |
| **US5 tasks** | 5 (T016-T020) |
| **Polish tasks** | 2 (T021-T022) |
| **Parallel tasks marked [P]** | 11 |
| **MVP scope** | Phases 1-3 (T001-T009) |

---

## Notes

- All checklist items follow the required `- [ ] T### [P?] [US?] Description with file path` format
- No new automated test tasks are included because the feature spec and plan did not request TDD or new coverage
- The task list assumes the existing `backend/src/logging_utils.py` helpers and Python logging infrastructure are reused rather than replaced
- User Story 5 intentionally leaves `backend/src/logging_utils.py` resilience catches unchanged except for verification that they remain documented
