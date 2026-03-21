# Tasks: Lint & Type Suppression Audit

**Input**: Design documents from `/specs/001-lint-suppression-audit/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅, contracts/ ✅

**Tests**: Not requested — verification via existing linter and test suites (per spec IV. Test Optionality).

**Organization**: Tasks are grouped by user story (US1–US4) to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- **Backend config**: `solune/backend/pyproject.toml`
- **Backend tests**: `solune/backend/tests/`
- **Frontend tests**: `solune/frontend/src/test/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Linter configuration changes that eliminate the need for inline suppressions globally

- [ ] T001 Add `B008` to global `ignore` list in `solune/backend/pyproject.toml` `[tool.ruff.lint]` section with comment `# function call defaults (FastAPI Depends() pattern)`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add justification comments to all retained suppressions that cannot be removed. These MUST be complete before user story phases begin, because user story phases will modify these same files and need the justified baseline in place.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Add justification comments to 8 file-level `# pyright: reportAttributeAccessIssue=false` directives in `solune/backend/src/services/github_projects/` files (service.py, copilot.py, agents.py, pull_requests.py, projects.py, issues.py, branches.py, board.py): comment `# GitHub API responses use dynamic attribute access; typing all response shapes is out of scope`
- [ ] T003 [P] Add justification comments to 2 inline `# pyright: ignore[reportMissingImports]` directives in `solune/backend/src/services/completion_providers.py` (lines ~66, ~184): comment `# optional copilot SDK; type stubs may not be available`
- [ ] T004 [P] Add justification comments to 5 `# type: ignore[reportMissingImports]` directives in `solune/backend/src/services/completion_providers.py` (lines ~62–63, ~167–168, ~262): comment `# optional SDK; not installed in all environments`
- [ ] T005 [P] Add justification comment to `# noqa: E402` in `solune/backend/src/services/github_projects/__init__.py` (line ~60): comment `# import depends on prior module-level setup`
- [ ] T006 [P] Add justification comments to `# noqa: PTH119` and `# noqa: PTH118` in `solune/backend/src/api/chat.py` (lines ~381, ~387): comment `# CodeQL recognizes os.path.basename/normpath as path-traversal sanitizers; do NOT migrate to pathlib`
- [ ] T007 [P] Add justification comment to `# type: ignore[call-arg]` on `Settings()` in `solune/backend/src/config.py` (line ~217): comment `# pydantic-settings loads config from environment variables`
- [ ] T008 [P] Add justification comments to 2 `# type: ignore[attr-defined]` on `record.request_id` in `solune/backend/src/logging_utils.py` (lines ~198, ~200): comment `# dynamic attribute injection on LogRecord is standard Python logging pattern`
- [ ] T009 [P] Add justification comment to `# type: ignore[misc]` on `BoundedDict.pop` in `solune/backend/src/utils.py` (line ~140): comment `# intentional API widening: pop() accepts optional default for dict-compatible interface`
- [ ] T010 [P] Add justification comments to retained `eslint-disable-next-line jsx-a11y/no-autofocus` in `solune/frontend/src/components/board/AddAgentPopover.tsx` (line ~114) and `solune/frontend/src/components/chores/AddChoreModal.tsx` (line ~276): comment `// autoFocus on modal/popover open is intentional UX for keyboard-first interaction`
- [ ] T011 [P] Add justification comment to retained `eslint-disable-next-line react-hooks/exhaustive-deps` in `solune/frontend/src/components/agents/AgentChatFlow.tsx` (line ~65): comment `// initialization-only effect — runs once on mount, deps intentionally empty`
- [ ] T012 [P] Add justification comment to retained `eslint-disable-next-line react-hooks/exhaustive-deps` in `solune/frontend/src/components/chores/ChoreChatFlow.tsx` (line ~62): comment `// initialization-only effect — runs once on mount, deps intentionally empty`
- [ ] T013 [P] Verify existing justification comment on `eslint-disable-next-line react-hooks/exhaustive-deps` in `solune/frontend/src/hooks/useRealTimeSync.ts` (line ~219); add or improve if missing
- [ ] T014 [P] Add justification comment to retained `eslint-disable-next-line @typescript-eslint/no-explicit-any` in `solune/frontend/src/lib/lazyWithRetry.ts` (line ~13): comment `// ComponentType<any> required — React.lazy() cannot accept unknown props generic`
- [ ] T015 [P] Add justification comments to all 5 `@ts-expect-error` directives in `solune/frontend/src/test/setup.ts`: comment `// intentional override of read-only DOM global for test setup; no typed alternative exists`

**Checkpoint**: All retained suppressions now have justification comments. User story implementation can begin.

---

## Phase 3: User Story 1 — Audit and Resolve Backend Type Suppressions (Priority: P1) 🎯 MVP

**Goal**: Remove at least 60% of the 49 backend type suppressions (`type: ignore` + `pyright:`) by fixing underlying type issues.

**Independent Test**: Run `python -m pyright src/` and `ruff check src/` in `solune/backend/` — zero new errors. Run `python -m pytest tests/unit/ -x -q --timeout=30` — all tests pass.

### Category: return-value — Cast fixes (12 instances)

- [ ] T016 [P] [US1] Add `from typing import cast` and replace `# type: ignore[return-value]` with `cast()` in `solune/backend/src/services/cache.py` (lines ~220, ~229, ~234)
- [ ] T017 [P] [US1] Replace `# type: ignore[return-value]` with `cast()` in `solune/backend/src/services/github_projects/copilot.py` (lines ~233, ~816)
- [ ] T018 [P] [US1] Replace `# type: ignore[return-value]` with `cast()` in `solune/backend/src/services/github_projects/pull_requests.py` (lines ~289, ~369, ~712)
- [ ] T019 [P] [US1] Replace `# type: ignore[return-value]` with `cast()` in `solune/backend/src/services/github_projects/projects.py` (line ~357)
- [ ] T020 [P] [US1] Replace `# type: ignore[return-value]` with `cast()` in `solune/backend/src/services/github_projects/issues.py` (line ~435)
- [ ] T021 [P] [US1] Replace `# type: ignore[return-value]` with `cast()` in `solune/backend/src/utils.py` (line ~297)

### Category: type-arg — asyncio.Task generics (6 instances)

- [ ] T022 [P] [US1] Change `asyncio.Task` to `asyncio.Task[None]` and remove `# type: ignore[type-arg]` in `solune/backend/src/services/task_registry.py` (lines ~33, ~44, ~55, ~101)
- [ ] T023 [P] [US1] Change `asyncio.Task` to `asyncio.Task[Any]` and remove `# type: ignore[type-arg]` in `solune/backend/src/services/github_projects/service.py` (line ~89)
- [ ] T024 [P] [US1] Change `asyncio.Task` to `asyncio.Task[Any]` and remove `# type: ignore[type-arg]` in `solune/backend/src/services/model_fetcher.py` (line ~28)

### Category: arg-type — Argument type mismatches (7 instances)

- [ ] T025 [P] [US1] Add `assert`/`if` guard for `settings.azure_openai_endpoint` (str | None → str) and remove `# type: ignore[arg-type]` in `solune/backend/src/services/completion_providers.py` (lines ~280–281)
- [ ] T026 [P] [US1] Fix `name` parameter type annotation and remove `# type: ignore[arg-type]` in `solune/backend/src/services/task_registry.py` (line ~50)
- [ ] T027 [P] [US1] Fix `min()` key function to use dict subscript instead of `.get()` and remove `# type: ignore[arg-type]` in `solune/backend/src/services/agents/service.py` (line ~1143)
- [ ] T028 [P] [US1] Fix `self._data.pop(key, *args)` variadic args type and remove `# type: ignore` in `solune/backend/src/utils.py` (line ~141)
- [ ] T029 [P] [US1] Fix `_rate_limit_exceeded_handler` callable type annotation and remove `# type: ignore[arg-type]` in `solune/backend/src/main.py` (line ~482)
- [ ] T030 [P] [US1] Fix `dict(next(iter(...)))` arg-type and remove `# type: ignore[arg-type]` in `solune/backend/src/services/tools/service.py` (line ~710)

### Category: Miscellaneous type fixes (4 removable instances)

- [ ] T031 [P] [US1] Fix decorator return type with `cast()` or `@overload` and remove `# type: ignore[return-value]` in `solune/backend/src/logging_utils.py` (line ~301)
- [ ] T032 [P] [US1] Fix `row[0]`, `row[1]`, `row[2]` indexing with proper tuple unpacking or type annotation and remove `# type: ignore[index]` in `solune/backend/src/services/metadata_service.py` (lines ~371–373)
- [ ] T033 [P] [US1] Fix `config.agent_mappings = deduped` assignment type and remove `# type: ignore[assignment]` in `solune/backend/src/services/workflow_orchestrator/config.py` (line ~283)
- [ ] T034 [P] [US1] Fix assignment type and remove `# type: ignore[assignment]` in `solune/backend/src/api/workflow.py` (line ~578)

**Checkpoint**: Backend type suppressions reduced from 49 → ~20 (29 removed, 20 retained with justification). Run `pyright src/`, `ruff check src/`, `pytest tests/unit/` to verify.

---

## Phase 4: User Story 2 — Audit and Resolve Frontend Accessibility and React Hook Suppressions (Priority: P2)

**Goal**: Remove at least 8 of 14 `eslint-disable` directives by fixing accessibility patterns and React hook dependency arrays.

**Independent Test**: Run `npx eslint .` and `npx tsc --noEmit` in `solune/frontend/` — zero new errors. Run `npx vitest run` — all tests pass.

### Category: jsx-a11y — Backdrop dismiss patterns (3 removable instances)

- [ ] T035 [P] [US2] Replace raw `<div onClick={stopPropagation}>` with semantic interactive element (add `onKeyDown` handler or use `<dialog>`) and remove `eslint-disable-next-line` jsx-a11y directive in `solune/frontend/src/components/agents/AgentIconPickerModal.tsx` (line ~59)
- [ ] T036 [P] [US2] Replace raw `<div onClick>` backdrop-dismiss with semantic interactive element and remove `eslint-disable-next-line` jsx-a11y directives in `solune/frontend/src/components/board/AgentPresetSelector.tsx` (lines ~424, ~472)

### Category: react-hooks/exhaustive-deps — Dependency array fixes (4 removable instances)

- [ ] T037 [P] [US2] Fix missing dependency or simplify conditional in `useEffect` and remove `eslint-disable-next-line react-hooks/exhaustive-deps` in `solune/frontend/src/components/chat/ChatInterface.tsx` (line ~389)
- [ ] T038 [P] [US2] Add missing `isOpen` dependency to `useEffect` and remove `eslint-disable-next-line react-hooks/exhaustive-deps` in `solune/frontend/src/components/pipeline/ModelSelector.tsx` (line ~86)
- [ ] T039 [P] [US2] Add missing `name` dependency to `useEffect` and remove `eslint-disable-next-line react-hooks/exhaustive-deps` in `solune/frontend/src/components/tools/UploadMcpModal.tsx` (line ~201)
- [ ] T040 [P] [US2] Add missing `resetAndClose` dependency (stabilize with `useCallback` if needed) and remove `eslint-disable-next-line react-hooks/exhaustive-deps` in `solune/frontend/src/components/chores/AddChoreModal.tsx` (line ~90)

### Category: @typescript-eslint/no-explicit-any — Type replacement (1 removable instance)

- [ ] T041 [P] [US2] Create a typed `WindowWithSpeechRecognition` interface and replace `window as any` cast; remove `eslint-disable-next-line @typescript-eslint/no-explicit-any` in `solune/frontend/src/hooks/useVoiceInput.ts` (line ~42)

**Checkpoint**: Frontend eslint-disable count reduced from 14 → 6 (8 removed, 6 retained with justification). Run `eslint .`, `tsc --noEmit`, `vitest run` to verify.

---

## Phase 5: User Story 3 — Audit and Resolve Backend Linter Suppressions (Priority: P3)

**Goal**: Remove 18 of 21 `# noqa` directives by leveraging the B008 global config (Phase 1) and adding `__all__` declarations.

**Independent Test**: Run `ruff check src/` in `solune/backend/` — zero new errors. Run `python -m pytest tests/unit/ -x -q --timeout=30` — all tests pass.

### Category: B008 — FastAPI Depends() (12 instances, all removed by T001 config)

- [ ] T042 [P] [US3] Remove all `# noqa: B008` comments from `solune/backend/src/api/cleanup.py`
- [ ] T043 [P] [US3] Remove all `# noqa: B008` comments from `solune/backend/src/api/activity.py`
- [ ] T044 [P] [US3] Remove all `# noqa: B008` comments from `solune/backend/src/api/chat.py`
- [ ] T045 [P] [US3] Remove all `# noqa: B008` comments from `solune/backend/src/dependencies.py`

### Category: F401 — Re-exports with __all__ (6 instances)

- [ ] T046 [P] [US3] Add `__all__` list declaring all re-exported names and remove `# noqa: F401` from imports in `solune/backend/src/models/chat.py`
- [ ] T047 [P] [US3] Remove `# noqa: F401` from imports in `solune/backend/src/services/copilot_polling/__init__.py` (already has `__all__` list at lines ~150–242)

**Checkpoint**: Backend noqa count reduced from 21 → 3 (18 removed, 3 retained — E402 + 2×PTH with justification). Run `ruff check src/`, `pytest tests/unit/` to verify.

---

## Phase 6: User Story 4 — Audit and Resolve Test File Suppressions (Priority: P4)

**Goal**: Remove at least 50% of test `# type: ignore` directives (17 of 26) by improving mock typing and test patterns.

**Independent Test**: Run `python -m pyright src/` and `python -m pytest tests/unit/ -x -q --timeout=30` in `solune/backend/`. Run `npx tsc --noEmit` and `npx vitest run` in `solune/frontend/`.

### Category: Backend test spy typing (8 instances in test_metadata_service.py)

- [ ] T048 [US4] Add explicit type annotations to spy cache class (e.g., `data`, `set_calls`, `deleted` attributes) and remove `# type: ignore` directives in `solune/backend/tests/unit/test_metadata_service.py`

### Category: Backend test production mode (6 instances in test_production_mode.py)

- [ ] T049 [US4] Fix `Settings()` call-arg suppressions by adding `_env_file=None` parameter or using typed construction and remove `# type: ignore[call-arg]` in `solune/backend/tests/integration/test_production_mode.py`

### Category: Backend test transaction safety (2 instances)

- [ ] T050 [P] [US4] Replace direct attribute access with `unittest.mock.patch.object()` or `MagicMock()` and remove `# type: ignore` in `solune/backend/tests/concurrency/test_transaction_safety.py`

### Category: Backend test miscellaneous fixes (1 instance each)

- [ ] T051 [P] [US4] Fix generator return type annotation and remove `# type: ignore` in `solune/backend/tests/unit/test_template_files.py`
- [ ] T052 [P] [US4] Use `{**defaults, **overrides}` dict merge instead of `.update()` and remove `# type: ignore` in `solune/backend/tests/unit/test_pipeline_state_store.py`

### Category: Backend test retained suppressions (9 instances — justification only)

- [ ] T053 [P] [US4] Add justification comments to 5 retained `# type: ignore[attr-defined]` for `record.request_id` dynamic attribute in `solune/backend/tests/unit/test_logging_utils.py`: comment `# dynamic attribute injection on LogRecord is standard Python logging pattern`
- [ ] T054 [P] [US4] Add justification comment to retained `# type: ignore` for frozen dataclass mutation test in `solune/backend/tests/unit/test_polling_loop.py`
- [ ] T055 [P] [US4] Add justification comment to retained `# type: ignore` for frozen dataclass mutation test in `solune/backend/tests/unit/test_transcript_detector.py`
- [ ] T056 [P] [US4] Add justification comment to retained `# type: ignore` for frozen dataclass mutation test in `solune/backend/tests/unit/test_agent_output.py`

**Checkpoint**: Backend test suppression count reduced from 26 → 9 (17 removed, 9 retained with justification). Frontend test `@ts-expect-error` count remains at 5 (all justified in Phase 2). Run all test suites to verify.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cross-cutting verification across all user stories

- [ ] T057 Run full backend verification: `cd solune/backend && ruff check src/ && python -m pyright src/ && python -m pytest tests/unit/ -x -q --timeout=30`
- [ ] T058 Run full frontend verification: `cd solune/frontend && npx eslint . && npx tsc --noEmit && npx vitest run`
- [ ] T059 Count total remaining suppressions across entire codebase and verify ≤58 (50% reduction from 115 baseline): `grep -rn "# type: ignore\|# noqa\|# pyright:" solune/backend/src/ solune/backend/tests/ | wc -l` and `grep -rn "eslint-disable\|@ts-expect-error" solune/frontend/src/ | wc -l`
- [ ] T060 Verify 100% of retained suppressions have inline justification comments: scan all remaining suppression lines for accompanying comments
- [ ] T061 Run quickstart.md validation commands to confirm all verification steps pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: No strict dependency on Phase 1, but should complete first to establish the justified baseline
- **User Stories (Phases 3–6)**: All depend on Foundational (Phase 2) completion
  - US1 (Phase 3), US2 (Phase 4), US3 (Phase 5), US4 (Phase 6) can proceed in parallel
  - Or sequentially in priority order: P1 → P2 → P3 → P4
- **Phase 5 (US3)**: Depends on Phase 1 (T001 — B008 global ignore must be configured before removing inline B008 noqa comments)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2 — Fully independent of backend stories
- **User Story 3 (P3)**: Can start after Phase 1 + Phase 2 — Depends on T001 (B008 config) for T042–T045
- **User Story 4 (P4)**: Can start after Phase 2 — Fully independent of production code stories

### Within Each User Story

- Tasks marked [P] within the same story can run in parallel (different files)
- Non-[P] tasks should be completed in order listed
- Verify at each checkpoint before proceeding to next story

### Parallel Opportunities

- All Phase 2 tasks (T002–T015) can run in parallel — different files
- All US1 tasks (T016–T034) can run in parallel — different files
- All US2 tasks (T035–T041) can run in parallel — different files
- All US3 tasks (T042–T047) can run in parallel — different files
- US4 tasks T050–T056 can run in parallel — different files
- **Cross-story**: US1, US2, US3, US4 can all be worked on in parallel by different developers

---

## Parallel Example: User Story 1

```bash
# Launch all return-value cast fixes in parallel:
Task T016: "Cast fixes in solune/backend/src/services/cache.py"
Task T017: "Cast fixes in solune/backend/src/services/github_projects/copilot.py"
Task T018: "Cast fixes in solune/backend/src/services/github_projects/pull_requests.py"
Task T019: "Cast fixes in solune/backend/src/services/github_projects/projects.py"
Task T020: "Cast fixes in solune/backend/src/services/github_projects/issues.py"
Task T021: "Cast fixes in solune/backend/src/utils.py"

# Launch all type-arg fixes in parallel:
Task T022: "asyncio.Task[None] in solune/backend/src/services/task_registry.py"
Task T023: "asyncio.Task[Any] in solune/backend/src/services/github_projects/service.py"
Task T024: "asyncio.Task[Any] in solune/backend/src/services/model_fetcher.py"
```

## Parallel Example: User Story 3

```bash
# After T001 (B008 config) is complete, launch all noqa removal in parallel:
Task T042: "Remove B008 noqa from solune/backend/src/api/cleanup.py"
Task T043: "Remove B008 noqa from solune/backend/src/api/activity.py"
Task T044: "Remove B008 noqa from solune/backend/src/api/chat.py"
Task T045: "Remove B008 noqa from solune/backend/src/dependencies.py"
Task T046: "Add __all__ + remove F401 noqa from solune/backend/src/models/chat.py"
Task T047: "Remove F401 noqa from solune/backend/src/services/copilot_polling/__init__.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001 — B008 config)
2. Complete Phase 2: Foundational (T002–T015 — justification comments)
3. Complete Phase 3: User Story 1 (T016–T034 — backend type fixes)
4. **STOP and VALIDATE**: Run `pyright src/`, `ruff check src/`, `pytest tests/unit/`
5. This alone removes ~29 suppressions (25% reduction from baseline)

### Incremental Delivery

1. Setup + Foundational → Justified baseline established
2. Add US1 (backend type) → ~29 removals → Validate backend type safety
3. Add US3 (backend lint) → +18 removals → Validate backend lint compliance
4. Add US2 (frontend a11y/hooks) → +8 removals → Validate frontend lint/a11y compliance
5. Add US4 (test files) → +17 removals → Validate test type safety
6. Polish → Final count verification (target: ≤43 remaining, 63% reduction)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (backend type suppressions)
   - Developer B: User Story 2 (frontend a11y/hooks)
   - Developer C: User Story 3 (backend lint) — after T001 is done
   - Developer D: User Story 4 (test files)
3. All stories integrate independently — no cross-story conflicts

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 61 |
| **Phase 1 (Setup)** | 1 task |
| **Phase 2 (Foundational)** | 14 tasks |
| **Phase 3 (US1 — Backend type)** | 19 tasks |
| **Phase 4 (US2 — Frontend a11y/hooks)** | 7 tasks |
| **Phase 5 (US3 — Backend lint)** | 6 tasks |
| **Phase 6 (US4 — Test files)** | 9 tasks |
| **Phase 7 (Polish)** | 5 tasks |
| **Parallel opportunities** | 54 of 61 tasks are parallelizable within their phase |
| **Projected removals** | 72 of 115 (63% reduction) |
| **Projected retained** | 43 (all with justification comments) |
| **MVP scope** | US1 only — removes 29 suppressions (25% of baseline) |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No new tests required — verification via existing linters and test suites
- All line numbers are approximate — verify against current source before implementation
