# Tasks: Codebase Cleanup — Reduce Technical Debt

**Input**: Design documents from `/specs/018-code-cleanup/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: No new tests are required — the spec explicitly does not mandate writing new tests. Existing CI checks (ruff, pyright, pytest, eslint, tsc, vitest, vite build) serve as the validation mechanism. Only genuinely stale tests are removed.

**Organization**: Tasks are grouped by user story (5 stories from spec.md) to enable independent implementation. User stories map to cleanup categories: US1 = Dead Code Removal (P1), US2 = Backwards-Compatibility Shims (P1), US3 = Consolidate Duplicated Logic (P2), US4 = Delete Stale Tests (P2), US5 = General Hygiene (P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`, `backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline CI state and detection analysis before any code changes

- [x] T001 Run full backend CI baseline: `cd backend && ruff check src/ tests/ && ruff format --check src/ tests/ && pyright src/ && pytest --tb=short`
- [x] T002 Run full frontend CI baseline: `cd frontend && npx eslint src/ && npx tsc --noEmit && npx vitest run && npm run build`
- [x] T003 [P] Run backend dead code detection: `cd backend && ruff check --select F401,F811,F841 src/ tests/`
- [x] T004 [P] Run frontend dead code detection: `cd frontend && npx tsc --noUnusedLocals --noUnusedParameters --noEmit`
- [x] T005 [P] Grep for backwards-compatibility patterns: `grep -rn "legacy\|compat\|old_format\|deprecated\|shim\|polyfill\|hasattr" backend/src/ frontend/src/`
- [x] T006 [P] Grep for stale TODO/FIXME/HACK comments: `grep -rn "TODO\|FIXME\|HACK" backend/src/ frontend/src/`
- [x] T007 [P] Grep for commented-out code in Python: `grep -rn "^[[:space:]]*#.*def \|^[[:space:]]*#.*class \|^[[:space:]]*#.*import " backend/src/`
- [x] T008 [P] Grep for commented-out code in TypeScript: `grep -rn "^[[:space:]]*//.*function \|^[[:space:]]*//.*const \|^[[:space:]]*//.*import " frontend/src/`

**Checkpoint**: Baseline CI passes, detection results documented. All subsequent phases use these results as input.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Review dynamic loading patterns and confirm safe-to-remove boundaries before any deletions

**⚠️ CRITICAL**: No removal work can begin until dynamic loading patterns are confirmed

- [x] T009 Audit dynamic imports in backend — search for `importlib`, `__import__`, `getattr` on modules, string-based plugin loading in `backend/src/` to build a "do not remove" list per FR-021
- [x] T010 [P] Audit migration discovery patterns — verify all migration files in `backend/src/migrations/` (001–010) are loaded by `backend/src/services/database.py` and confirm none are orphaned per FR-015
- [x] T011 [P] Audit frontend dynamic imports — search for `React.lazy`, dynamic `import()`, and string-based component loading in `frontend/src/` to build a "do not remove" list per FR-021
- [x] T012 Create a tracking document (in PR description) listing every removal/consolidation with rationale per FR-023

**Checkpoint**: "Do not remove" lists established. Safe removal boundaries confirmed. All user story phases can now proceed.

---

## Phase 3: User Story 1 — Remove Dead Code and Unreachable Paths (Priority: P1) 🎯 MVP

**Goal**: Remove all dead code — unused functions, unreachable branches, commented-out logic, unused imports, unused variables, unused type definitions, and unused models — so the codebase only contains actively used code.

**Independent Test**: Run all existing CI checks (ruff, pyright, pytest, eslint, tsc, vitest, vite build) after removals. Verify no test failures or build errors. Verify no remaining code references removed symbols.

### Backend Dead Code Removal

- [x] T013 [P] [US1] Remove unused imports flagged by ruff (F401) across all files in `backend/src/`
- [x] T014 [P] [US1] Remove unused variables flagged by ruff (F841) across all files in `backend/src/`
- [x] T015 [P] [US1] Remove unused imports and variables flagged by ruff in `backend/tests/`
- [x] T016 [US1] Audit and remove unused functions/methods in `backend/src/utils.py` — cross-reference all callers before removal
- [x] T017 [P] [US1] Audit and remove unused exception classes in `backend/src/exceptions.py` — cross-reference all callers before removal
- [x] T018 [P] [US1] Audit and remove unused constants in `backend/src/constants.py` — cross-reference all callers before removal
- [x] T019 [P] [US1] Audit and remove unused dependency injection functions in `backend/src/dependencies.py` — cross-reference all callers before removal
- [x] T020 [P] [US1] Audit and remove unused config entries in `backend/src/config.py` — cross-reference all callers before removal
- [x] T021 [US1] Audit and remove unused Pydantic models across `backend/src/models/*.py` — cross-reference all imports and API responses per FR-005
- [x] T022 [US1] Audit and remove unused route handlers in `backend/src/api/*.py` — verify no frontend calls, no test coverage, not part of public API per FR-006
- [x] T023 [P] [US1] Audit and remove dead middleware in `backend/src/middleware/` — cross-reference all registrations in app startup
- [x] T024 [P] [US1] Audit and remove unused logging helpers in `backend/src/logging_utils.py` — cross-reference all callers
- [x] T025 [US1] Remove any commented-out code blocks (not documentation comments) found in `backend/src/` per FR-004

### Frontend Dead Code Removal

- [x] T026 [P] [US1] Remove unused imports and variables flagged by eslint/tsc across all files in `frontend/src/`
- [x] T027 [US1] Audit and remove unused React components in `frontend/src/components/` — cross-reference all imports and route references per FR-007
- [x] T028 [US1] Audit and remove unused custom hooks in `frontend/src/hooks/` — cross-reference all imports per FR-007
- [x] T029 [P] [US1] Audit and remove unused utility functions in `frontend/src/utils/` — cross-reference all imports per FR-007
- [x] T030 [P] [US1] Audit and remove unused TypeScript type definitions in `frontend/src/types/` — cross-reference all imports per FR-005
- [x] T031 [P] [US1] Audit and remove unused constants in `frontend/src/constants.ts` — cross-reference all imports
- [x] T032 [US1] Remove any commented-out code blocks found in `frontend/src/` per FR-004
- [x] T033 [US1] Run full CI validation after all US1 removals: backend (ruff, pyright, pytest) and frontend (eslint, tsc, vitest, vite build)

**Checkpoint**: All dead code removed. CI passes. No remaining code references removed symbols. Commit with `chore: remove dead code and unused symbols`.

---

## Phase 4: User Story 2 — Remove Backwards-Compatibility Shims (Priority: P1)

**Goal**: Remove all obsolete compatibility layers, polyfills, and adapter code — including conditional branches for old API shapes, deprecated config formats, and migration-period aliases — so the codebase reflects only the current architecture.

**Independent Test**: Remove each shim, run all CI checks, confirm no test failures or runtime errors — proving the old code path is no longer exercised.

### Shim Removal Tasks (from research.md findings)

- [x] T034 [US2] Verify and remove legacy plaintext token fallback in `backend/src/services/encryption.py:62-88` — confirm `_is_plaintext_token()` and fallback logic in `decrypt_token()` are no longer needed (all tokens encrypted). Remove the dead branch per FR-001, FR-002
- [x] T035 [US2] Verify and remove model re-exports for import compatibility in `backend/src/models/chat.py:18-40` — audit all `from src.models.chat import Agent/Recommendation/Workflow` imports; if all callers use new paths, remove re-exports and `# noqa: F401` comments per FR-001
- [x] T036 [P] [US2] Verify and remove service module re-exports in `backend/src/services/workflow_orchestrator/__init__.py:10-11` — audit all callers; if all use direct submodule imports, remove re-exports per FR-001
- [x] T037 [P] [US2] Verify and remove service module re-exports in `backend/src/services/copilot_polling/__init__.py:193` — audit all callers; if all use direct submodule imports, remove re-exports per FR-001
- [x] T038 [US2] Verify and remove dynamic agent slug extraction `hasattr` fallbacks in `backend/src/services/agent_tracking.py:105`, `backend/src/services/workflow_orchestrator/config.py:268`, `backend/src/services/workflow_orchestrator/orchestrator.py:711`, `backend/src/services/workflow_orchestrator/models.py:25` — confirm all agents are now objects, remove string-based fallbacks per FR-001, FR-002
- [x] T039 [US2] Verify and remove "Done!" marker fallback in `backend/src/services/copilot_polling/helpers.py:63-67` — confirm no pre-policy issues exist, remove backward-compatibility branch per FR-001, FR-002
- [x] T040 [US2] Grep for any additional backwards-compatibility patterns (`if old_format:`, `if legacy:`, `# compat`, `# backwards`, `# deprecated`) across `backend/src/` and `frontend/src/` and remove confirmed dead branches per FR-001, FR-002
- [x] T041 [US2] Run full CI validation after all US2 removals: backend (ruff, pyright, pytest) and frontend (eslint, tsc, vitest, vite build)

**Checkpoint**: All confirmed backwards-compatibility shims removed. CI passes. Only current code paths remain. Commit with `chore: remove backwards-compatibility shims`.

---

## Phase 5: User Story 3 — Consolidate Duplicated Logic (Priority: P2)

**Goal**: Consolidate near-duplicate functions, utility helpers, service methods, model definitions, and copy-pasted test patterns into single shared implementations so that bug fixes only need to be made in one place.

**Independent Test**: Run all CI checks after each consolidation. Verify all callers of consolidated functions produce identical results to original implementations.

### Backend Consolidation

- [x] T042 [US3] Extract shared `TokenClientCache` utility from duplicated token caching logic in `backend/src/services/completion_providers.py:67-80` and `backend/src/services/model_fetcher.py:75-80` — create shared class in `backend/src/services/token_client_cache.py`, update both callers per FR-008
- [x] T043 [US3] Evaluate chat response model alignment across `backend/src/models/chat.py` (ChatMessagesResponse), `backend/src/models/chores.py` (ChoreChatResponse), and `backend/src/models/agents.py` (AgentChatResponse) — compare fields and determine if shared base is justified per FR-011
- [x] T044 [US3] If T043 confirms alignment: extract shared `BaseChatFlowResponse` model from the three chat response models into `backend/src/models/chat.py` and update all callers — skip if fields differ meaningfully (duplication is preferable to wrong abstraction)
- [x] T045 [US3] Audit and consolidate `is_admin_user()` in `backend/src/services/agent_creator.py` — check if equivalent exists in `backend/src/services/settings_store.py` or similar; consolidate into single shared function per FR-008
- [x] T046 [US3] Consolidate duplicated test mock patterns in `backend/tests/` — identify most-duplicated inline mock setups and migrate to shared helpers in `backend/tests/helpers/factories.py` and `backend/tests/helpers/mocks.py` per FR-009

### Frontend Consolidation

- [x] T047 [US3] Evaluate and extract shared `GenericChatFlow` base component from `frontend/src/components/agents/AgentChatFlow.tsx` and `frontend/src/components/chores/ChoreChatFlow.tsx` — extract shared chat message state, rendering, and session management; keep resource-specific logic in wrapper components per FR-008
- [x] T048 [US3] Evaluate and create `createResourceHooks<T>()` factory from duplicated CRUD hook patterns in `frontend/src/hooks/useAgents.ts:15-63` and `frontend/src/hooks/useChores.ts:21-80+` — only consolidate if patterns are stable and abstraction is justified per FR-008 (duplication is preferable to wrong abstraction)
- [x] T049 [P] [US3] Audit and consolidate duplicated API client logic in `frontend/src/services/` — identify repeated fetch/error-handling patterns and extract shared utility functions per FR-010
- [x] T050 [P] [US3] Audit and consolidate overlapping TypeScript type definitions in `frontend/src/types/` — merge duplicated or overlapping type definitions into canonical types per FR-011
- [x] T051 [US3] Run full CI validation after all US3 consolidations: backend (ruff, pyright, pytest) and frontend (eslint, tsc, vitest, vite build)

**Checkpoint**: All high-value duplication consolidated. CI passes. Each consolidation documented with rationale. Commit with `refactor: consolidate duplicated logic`.

---

## Phase 6: User Story 4 — Delete Stale and Irrelevant Tests (Priority: P2)

**Goal**: Remove test files and test cases that test deleted or refactored functionality, mock internals so heavily they don't test real behavior, or test code paths that no longer exist — so the test suite accurately reflects the current codebase.

**Independent Test**: Run the full test suite after removals. Confirm all remaining tests pass and meaningful coverage for active code paths is preserved.

### Backend Test Cleanup

- [x] T052 [US4] Run full backend test suite (`cd backend && pytest -v`) and identify any tests that fail due to testing nonexistent functionality
- [x] T053 [US4] Audit `backend/tests/unit/` for test cases targeting deleted or refactored functions/classes — cross-reference test targets with current `backend/src/` codebase; remove stale tests per FR-012
- [x] T054 [P] [US4] Audit `backend/tests/integration/` for test cases targeting deleted or refactored functionality — cross-reference test targets with current `backend/src/` codebase; remove stale tests per FR-012
- [x] T055 [US4] Audit `backend/tests/` for tests that mock internals so heavily they don't validate real behavior — identify tests where the majority of the test is mock setup rather than behavior validation per FR-013
- [x] T056 [P] [US4] Search for and remove test artifacts (leftover `.db` files, `MagicMock` files, temporary test output) at repository root and in `backend/` per FR-014

### Frontend Test Cleanup

- [x] T057 [US4] Run full frontend test suite (`cd frontend && npx vitest run`) and identify any tests that fail due to testing nonexistent functionality
- [x] T058 [US4] Audit frontend test files in `frontend/src/` for test cases targeting deleted or refactored components/hooks — remove stale tests per FR-012
- [x] T059 [P] [US4] Audit `frontend/e2e/` for stale end-to-end tests targeting deleted features or workflows — remove stale tests per FR-012
- [x] T060 [US4] Run full CI validation after all US4 removals: backend (pytest) and frontend (vitest)

**Checkpoint**: All stale tests removed. Full test suite passes. Meaningful coverage preserved for active code. Commit with `chore: remove stale and irrelevant tests`.

---

## Phase 7: User Story 5 — General Hygiene Cleanup (Priority: P3)

**Goal**: Clean up orphaned configuration files, stale TODO/FIXME/HACK comments referencing completed work, unused dependencies, and unused environment variables — so the project's configuration and metadata accurately reflect the current state.

**Independent Test**: Run all CI checks and builds after removals. Confirm dependency resolution still succeeds and no functionality is broken.

### Dependency Cleanup

- [x] T061 [US5] Verify and remove unused npm dependency `socket.io-client` from `frontend/package.json` — confirm no imports of `socket.io-client` exist in `frontend/src/` and it is not dynamically loaded per FR-017
- [x] T062 [P] [US5] Verify and remove unused npm dev dependency `jsdom` from `frontend/package.json` — confirm project uses `happy-dom` (configured in `frontend/src/test/setup.ts`) and `jsdom` is not referenced in vitest config per FR-017
- [x] T063 [US5] Run `cd frontend && npm install` after dependency removal to confirm `package-lock.json` updates and no resolution errors
- [x] T064 [US5] Audit `backend/pyproject.toml` for unused Python dependencies — cross-reference each dependency with imports in `backend/src/`; remove any confirmed unused per FR-017

### Configuration Cleanup

- [x] T065 [P] [US5] ~~Remove unused environment variable `SESSION_EXPIRE_HOURS` from `.env.example`~~ — **CORRECTED**: `SESSION_EXPIRE_HOURS` IS actively used by `backend/src/config.py:37` (as `session_expire_hours`) and referenced by `backend/src/services/session_store.py`. NOT removed.
- [x] T066 [P] [US5] Audit `docker-compose.yml` for unused services or environment variables — cross-reference with current application needs per FR-018
- [x] T067 [P] [US5] Audit `.env.example` for any additional unused environment variables — cross-reference each variable with `backend/src/config.py` and `backend/src/` per FR-018

### Comment and Config Cleanup

- [x] T068 [US5] Review and selectively remove stale TODO/FIXME/HACK comments in `backend/src/` — only remove comments referencing completed work; keep `backend/src/api/projects.py:23` (future work) and `backend/src/services/signal_chat.py:155,159,165` (active security issue) per FR-016
- [x] T069 [P] [US5] Review and selectively remove stale TODO/FIXME/HACK comments in `frontend/src/` — only remove comments referencing completed work per FR-016
- [x] T070 [US5] Audit for orphaned migration files or configs referencing deleted features in `backend/src/migrations/` and project config files per FR-015
- [x] T071 [US5] Run full CI validation after all US5 changes: backend (ruff, pyright, pytest) and frontend (eslint, tsc, vitest, vite build) plus `npm install` and `pip install`

**Checkpoint**: All general hygiene items addressed. CI passes. Dependencies resolve cleanly. Commit with `chore: general hygiene cleanup`.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cross-story integration

- [x] T072 Run complete CI suite across entire repository — backend: `ruff check`, `ruff format --check`, `pyright`, `pytest`; frontend: `eslint`, `tsc --noEmit`, `vitest run`, `npm run build`
- [x] T073 Verify no public API contracts changed — diff all files in `backend/src/api/` and confirm no route paths, request/response shapes, or status codes were modified per FR-020
- [x] T074 Compile categorized PR description summary — organize every removal/consolidation by the 5 cleanup categories with brief rationale for each change per FR-023
- [x] T075 Measure and report total lines removed, functions consolidated, dependencies removed, and stale tests removed per SC-002, SC-004, SC-006
- [x] T076 Run quickstart.md validation checklist to confirm all items pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) — BLOCKS all user stories
- **US1 Dead Code (Phase 3)**: Depends on Foundational (Phase 2) — recommended first (largest impact)
- **US2 Shims (Phase 4)**: Depends on Foundational (Phase 2) — can run in parallel with US1 (different code targets)
- **US3 Consolidation (Phase 5)**: Depends on US1 and US2 completion (consolidation targets may overlap with dead code/shim removals)
- **US4 Stale Tests (Phase 6)**: Depends on US1 and US2 completion (need to know which code was removed to identify stale tests)
- **US5 Hygiene (Phase 7)**: Depends on Foundational (Phase 2) — can run in parallel with US1/US2 (different targets: deps, configs, comments)
- **Polish (Phase 8)**: Depends on ALL user stories complete

### User Story Dependencies

- **US1 (P1) — Dead Code**: Can start after Foundational. No dependencies on other stories.
- **US2 (P1) — Shims**: Can start after Foundational. No dependencies on other stories. Can run in parallel with US1.
- **US3 (P2) — Consolidation**: Should follow US1 and US2 to avoid consolidating code that will be removed.
- **US4 (P2) — Stale Tests**: Should follow US1 and US2 to accurately identify tests for removed code.
- **US5 (P3) — Hygiene**: Can start after Foundational. Independent of other stories (targets different files: configs, deps, comments).

### Within Each User Story

- Audit/analysis tasks before removal tasks
- Backend and frontend tasks marked [P] within a story can run in parallel (different codebases)
- CI validation is the final task in each story phase
- Each story completes with a conventional commit

### Parallel Opportunities

- **Phase 1**: T003, T004, T005, T006, T007, T008 can all run in parallel (read-only analysis)
- **Phase 2**: T010, T011 can run in parallel with T009
- **Phase 3 (US1)**: Backend tasks (T013–T025) and frontend tasks (T026–T032) can run in parallel
- **Phase 4 (US2)**: T036 and T037 can run in parallel (different files)
- **Phase 5 (US3)**: T049 and T050 can run in parallel; backend and frontend consolidation can be parallelized
- **Phase 6 (US4)**: T054, T056, T059 can run in parallel
- **Phase 7 (US5)**: T062, T065, T066, T067, T069 can all run in parallel

---

## Parallel Example: User Story 1 (Dead Code Removal)

```bash
# Launch backend and frontend dead code removal in parallel:
Task: "Remove unused imports flagged by ruff (F401) across backend/src/"        # T013
Task: "Remove unused imports and variables flagged by eslint/tsc in frontend/"   # T026

# Within backend, these target different files and can run in parallel:
Task: "Audit and remove unused exception classes in backend/src/exceptions.py"   # T017
Task: "Audit and remove unused constants in backend/src/constants.py"            # T018
Task: "Audit and remove unused dependency functions in backend/src/dependencies.py" # T019
Task: "Audit and remove unused config entries in backend/src/config.py"          # T020

# Within frontend, these target different files and can run in parallel:
Task: "Audit and remove unused utility functions in frontend/src/utils/"         # T029
Task: "Audit and remove unused TypeScript types in frontend/src/types/"          # T030
Task: "Audit and remove unused constants in frontend/src/constants.ts"           # T031
```

---

## Parallel Example: User Story 2 (Shim Removal)

```bash
# These target different service modules and can run in parallel:
Task: "Verify and remove service re-exports in workflow_orchestrator/__init__.py" # T036
Task: "Verify and remove service re-exports in copilot_polling/__init__.py"      # T037
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 — Dead Code & Shims)

1. Complete Phase 1: Setup — establish baseline CI
2. Complete Phase 2: Foundational — confirm safe removal boundaries
3. Complete Phase 3: US1 Dead Code Removal — largest immediate impact
4. **STOP and VALIDATE**: Run full CI, verify no regressions
5. Complete Phase 4: US2 Shim Removal — co-equal priority with US1
6. **STOP and VALIDATE**: Run full CI, verify no regressions
7. At this point, the highest-priority cleanup is complete and can be reviewed/merged

### Incremental Delivery

1. Setup + Foundational → Safe removal boundaries confirmed
2. Add US1 Dead Code → CI passes → Commit (`chore: remove dead code`) — MVP Part 1
3. Add US2 Shims → CI passes → Commit (`chore: remove backwards-compatibility shims`) — MVP Part 2
4. Add US3 Consolidation → CI passes → Commit (`refactor: consolidate duplicated logic`)
5. Add US4 Stale Tests → CI passes → Commit (`chore: remove stale tests`)
6. Add US5 Hygiene → CI passes → Commit (`chore: general hygiene cleanup`)
7. Polish → Final CI validation, PR description, metrics → Ready for review

### Single-Agent Strategy

Since this is a cleanup task executed by a single agent:

1. Complete all phases sequentially in priority order
2. Run CI validation after each phase (not just at the end)
3. Commit after each user story with appropriate conventional commit prefix
4. If any CI check fails after a removal, revert that specific removal and continue
5. Document every removal in the PR description as changes are made

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable via existing CI checks
- No new tests are written — existing CI checks serve as validation
- Conventional commits: `refactor:` for consolidation (US3), `chore:` for removal (US1, US2, US4, US5)
- **Do not remove**: crypto polyfill in `frontend/src/test/setup.ts:11` (legitimate test environment polyfill per R1)
- **Do not remove**: TODOs in `backend/src/api/projects.py:23` (future work) and `backend/src/services/signal_chat.py:155,159,165` (active security issue per R5)
- **Caution**: Duplication is preferable to wrong abstraction — applies to all US3 consolidation tasks. Do not force abstractions that don't genuinely simplify maintenance.
- Total tasks: 76
