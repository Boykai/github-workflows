# Tasks: Codebase Cleanup — Reduce Technical Debt

**Input**: Design documents from `/specs/018-code-cleanup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No new tests are required — this feature removes code and verifies correctness via existing CI checks (per plan.md and spec.md).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`, `frontend/src/`
- Paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify baseline state before making any changes — all CI checks must pass on the current branch.

- [x] T001 Verify backend CI baseline: run `ruff check src tests && ruff format --check src tests` in `backend/`
- [x] T002 [P] Verify backend tests baseline: run `python -m pytest` per-file for `backend/tests/unit/` (file-by-file for stability)
- [x] T003 [P] Verify frontend CI baseline: run `npx tsc --noEmit && npx eslint . && npx vitest run && npx vite build` in `frontend/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational infrastructure is needed — this is a cleanup-only feature operating within the existing codebase.

**⚠️ CRITICAL**: Phase 1 baseline verification MUST pass before any cleanup work begins.

**Checkpoint**: Baseline verified — cleanup implementation can now begin.

---

## Phase 3: User Story 1 — Remove Dead Code and Unused Artifacts (Priority: P1) 🎯 MVP

**Goal**: Remove all unused package dependencies from both backend and frontend. Research confirmed no unused functions, components, commented-out code, or unused route handlers exist — the actionable dead code is limited to 4 unused dependencies (2 backend, 2 frontend).

**Independent Test**: Run `pip install -e ".[dev]"` and all backend CI checks after backend dependency removal; run `npm install && npx vite build && npx vitest run` and all frontend CI checks after frontend dependency removal. All must pass with zero regressions.

### Implementation for User Story 1

- [x] T004 [P] [US1] Remove `python-jose[cryptography]>=3.3.0` from dependencies list in `backend/pyproject.toml`
- [x] T005 [P] [US1] Remove `agent-framework-core>=1.0.0a1` from dependencies list in `backend/pyproject.toml`
- [x] T006 [US1] Verify backend installs cleanly after dependency removal: run `pip install -e ".[dev]"` in `backend/`
- [x] T007 [US1] Run backend linting after dependency removal: `ruff check src tests && ruff format --check src tests` in `backend/`
- [x] T008 [US1] Run backend tests after dependency removal: `python -m pytest tests/unit/ -q` per-file in `backend/`
- [x] T009 [P] [US1] Remove `socket.io-client` from dependencies in `frontend/package.json` via `npm uninstall socket.io-client`
- [x] T010 [P] [US1] Remove `jsdom` from devDependencies in `frontend/package.json` via `npm uninstall jsdom`
- [x] T011 [US1] Verify frontend builds and tests pass after dependency removal: `npx tsc --noEmit && npx eslint . && npx vitest run && npx vite build` in `frontend/`

**Checkpoint**: All unused dependencies removed. Backend and frontend CI checks pass. US1 is complete and independently verified.

---

## Phase 4: User Story 2 — Remove Backwards-Compatibility Shims (Priority: P1)

**Goal**: Confirm that no actionable backwards-compatibility shims exist. Research identified only one pattern — the legacy plaintext token fallback in `EncryptionService.decrypt()` — which is explicitly RETAINED because active user sessions may still contain pre-encryption tokens.

**Independent Test**: Search the codebase for common shim patterns (`if old_format:`, `if legacy:`, deprecated adapters, migration-period aliases) and confirm zero results. Verify the retained legacy token fallback test still passes.

### Implementation for User Story 2

- [x] T012 [P] [US2] Search entire codebase for `if old_format:` and `if legacy:` patterns and confirm zero actionable results, documenting findings
- [x] T013 [P] [US2] Search for deprecated adapter functions, wrapper modules, and migration-period aliases across `backend/src/` and `frontend/src/` and confirm none exist
- [x] T014 [US2] Verify retained legacy token fallback test passes: `python -m pytest backend/tests/unit/test_token_encryption.py -q`

**Checkpoint**: No backwards-compatibility shims require removal. The retained legacy token fallback is documented and tested. US2 is complete.

---

## Phase 5: User Story 3 — Consolidate Duplicated Logic (Priority: P2)

**Goal**: Extract 3 families of duplicated test fixtures into shared helpers in `backend/tests/helpers/mocks.py` and update all consuming test files. Research confirmed no production code duplication warrants consolidation — service CRUD patterns are domain-specific and consolidation would be a wrong abstraction.

**Independent Test**: Run all affected test files after consolidation and verify identical behavior. Run `ruff check tests && ruff format --check tests` in `backend/` to confirm no lint or formatting issues.

### Implementation for User Story 3

- [x] T015 [US3] Add `make_mock_provider()` factory function to `backend/tests/helpers/mocks.py` returning a configured `MockCompletionProvider` instance matching the pattern in `backend/tests/unit/test_ai_agent.py`
- [x] T016 [US3] Replace 7 inline `mock_provider` fixture definitions in `backend/tests/unit/test_ai_agent.py` with imports from `backend/tests/helpers/mocks.py`
- [x] T017 [US3] Verify `test_ai_agent.py` tests pass after consolidation: `python -m pytest backend/tests/unit/test_ai_agent.py -q`
- [x] T018 [US3] Add `make_mock_ai_service()` factory function to `backend/tests/helpers/mocks.py` returning a configured `AsyncMock` of `AIAgentService` matching the pattern in `backend/tests/unit/test_workflow_orchestrator.py`
- [x] T019 [US3] Replace 4 inline `mock_ai_service` fixture definitions in `backend/tests/unit/test_workflow_orchestrator.py` with imports from `backend/tests/helpers/mocks.py`
- [x] T020 [US3] Replace 7 inline `mock_github_service` fixture definitions in `backend/tests/unit/test_workflow_orchestrator.py` with the existing `make_mock_github_service()` from `backend/tests/helpers/mocks.py`
- [x] T021 [US3] Verify `test_workflow_orchestrator.py` tests pass after consolidation: `python -m pytest backend/tests/unit/test_workflow_orchestrator.py -q`
- [x] T022 [US3] Run linting on updated test files: `ruff check tests && ruff format --check tests` in `backend/`

**Checkpoint**: All duplicated test fixtures consolidated into shared helpers. All affected tests pass with identical behavior. US3 is complete.

---

## Phase 6: User Story 4 — Delete Stale and Irrelevant Tests (Priority: P2)

**Goal**: Confirm that no stale or irrelevant tests exist. Research cross-referenced all test files against production source modules and found all tests exercise current behavior. No orphaned test artifacts were found.

**Independent Test**: Run the full backend and frontend test suites and confirm all tests pass. Verify no orphaned `.db`, `.sqlite`, or `MagicMock` files exist in workspace root or `backend/` root.

### Implementation for User Story 4

- [x] T023 [P] [US4] Search for orphaned test artifacts (`.db`, `.sqlite`, `MagicMock` files) in repository root and `backend/` root and confirm none exist
- [x] T024 [P] [US4] Cross-reference all test files in `backend/tests/unit/` against modules in `backend/src/` to confirm no tests reference deleted modules
- [x] T025 [US4] Run full backend test suite to confirm all tests pass: `python -m pytest tests/unit/ -q` per-file in `backend/`

**Checkpoint**: No stale tests require removal. Test suite is current and healthy. US4 is complete.

---

## Phase 7: User Story 5 — Perform General Hygiene Cleanup (Priority: P3)

**Goal**: Confirm that no additional hygiene items exist beyond the dependency removals already completed in US1. Research found all TODO/FIXME/HACK comments reference genuinely open work items, no orphaned migrations or configs exist, and no unused Docker Compose services are present.

**Independent Test**: Grep for `TODO|FIXME|HACK` and confirm all remaining comments are legitimate. Verify all CI checks pass.

### Implementation for User Story 5

- [x] T026 [P] [US5] Audit all `TODO`, `FIXME`, and `HACK` comments across `backend/src/` and `frontend/src/` and confirm each references genuinely open work (not completed items)
- [x] T027 [P] [US5] Verify no orphaned migration files exist: confirm all migrations in `backend/src/migrations/` (001–010) are referenced by the migration runner in `backend/src/services/database.py`
- [x] T028 [P] [US5] Verify no orphaned Docker Compose services or environment variables exist by checking `docker-compose.yml` and `.env.example` against active source references
- [x] T029 [US5] Run final backend CI verification: `ruff check src tests && ruff format --check src tests && pyright src` in `backend/`
- [x] T030 [US5] Run final frontend CI verification: `npx tsc --noEmit && npx eslint . && npx vitest run && npx vite build` in `frontend/`

**Checkpoint**: No additional hygiene items found. All CI checks pass. US5 is complete.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and PR deliverables

- [x] T031 Run full backend test suite (all 47+ files) to confirm zero regressions across all changes
- [x] T032 [P] Run full frontend test suite and production build to confirm zero regressions
- [x] T033 Create PR description with categorized summary of every change, organized by the 5 cleanup categories, with brief explanations for each removal per spec.md deliverables

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — removes unused dependencies
- **US2 (Phase 4)**: Depends on Foundational — can run in parallel with US1 (verification-only)
- **US3 (Phase 5)**: Depends on Foundational — can run in parallel with US1/US2 (different files)
- **US4 (Phase 6)**: Depends on Foundational — can run in parallel with US1/US2/US3 (verification-only)
- **US5 (Phase 7)**: Depends on US1 completion (dependency removals are part of hygiene verification)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 baseline — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 1 baseline — No dependencies on other stories (verification-only)
- **User Story 3 (P2)**: Can start after Phase 1 baseline — No dependencies on other stories (modifies test files only)
- **User Story 4 (P2)**: Can start after Phase 1 baseline — No dependencies on other stories (verification-only)
- **User Story 5 (P3)**: Depends on US1 completion — hygiene audit includes verifying dependency removals

### Within Each User Story

- Backend changes before frontend changes (within US1)
- Verification after each modification step
- CI check at story completion checkpoint

### Parallel Opportunities

- **Phase 1**: T001, T002, T003 can all run in parallel (independent CI checks)
- **Phase 3 (US1)**: T004+T005 can run in parallel (different dependency lines in same file); T009+T010 can run in parallel (different packages)
- **Phase 4 (US2)**: T012+T013 can run in parallel (different search patterns)
- **Phase 5 (US3)**: T015 → T016 → T017 must be sequential (add helper, update file, verify); T018 → T019 → T020 → T021 must be sequential (add helper, update files, verify)
- **Phase 6 (US4)**: T023+T024 can run in parallel (different verification checks)
- **Phase 7 (US5)**: T026+T027+T028 can run in parallel (independent audits)
- **Cross-story**: US1, US2, US3, US4 can all proceed in parallel (no shared file conflicts)

---

## Parallel Example: User Story 1

```bash
# Launch backend dependency removals together (same file, different lines):
Task T004: "Remove python-jose from backend/pyproject.toml"
Task T005: "Remove agent-framework-core from backend/pyproject.toml"

# Then verify backend sequentially:
Task T006: "Verify backend installs cleanly"
Task T007: "Run backend linting"
Task T008: "Run backend tests"

# Launch frontend dependency removals together (different packages):
Task T009: "Remove socket.io-client from frontend/package.json"
Task T010: "Remove jsdom from frontend/package.json"

# Then verify frontend:
Task T011: "Verify frontend builds and tests pass"
```

## Parallel Example: User Story 3

```bash
# Fixture consolidation must be sequential within each fixture family:
# Family 1: mock_provider
Task T015: "Add make_mock_provider() to mocks.py"
Task T016: "Update test_ai_agent.py to use shared helper"
Task T017: "Verify test_ai_agent.py passes"

# Family 2: mock_ai_service + mock_github_service (same file)
Task T018: "Add make_mock_ai_service() to mocks.py"
Task T019: "Replace mock_ai_service in test_workflow_orchestrator.py"
Task T020: "Replace mock_github_service in test_workflow_orchestrator.py"
Task T021: "Verify test_workflow_orchestrator.py passes"

# Family 1 and Family 2 can run in parallel (different files)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify baseline)
2. Complete Phase 3: User Story 1 (remove unused dependencies)
3. **STOP and VALIDATE**: All CI checks pass, dependency manifests are lean
4. This alone delivers the highest-value, lowest-risk improvement

### Incremental Delivery

1. US1 (unused dependencies) → Immediate value, very low risk
2. US2 (shims verification) → Confirms no action needed, documents rationale
3. US3 (test fixture consolidation) → Reduces test maintenance burden
4. US4 (stale tests verification) → Confirms test suite health
5. US5 (hygiene verification) → Final sweep, confirms clean state
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. All developers verify baseline (Phase 1)
2. Once baseline verified:
   - Developer A: US1 (dependency removal — `pyproject.toml`, `package.json`)
   - Developer B: US3 (test fixture consolidation — `tests/helpers/mocks.py`, test files)
   - Developer C: US2 + US4 + US5 (verification tasks — read-only analysis)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on other tasks in the same phase
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and verifiable
- Commit after each task or logical group using conventional commits: `chore:` for removals, `refactor:` for consolidation
- US2, US4, and US5 are primarily verification/audit tasks — research found no actionable items beyond US1 and US3
- Items explicitly RETAINED (do not remove): legacy token fallback in `backend/src/services/encryption.py`, all migration files (001–010), `github-copilot-sdk` dependency, all TODO comments, service CRUD patterns, Signal API docker service
