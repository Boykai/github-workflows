# Tasks: Refactor Codebase for Quality, Best Practices, and UX Improvements

**Input**: Design documents from `/specs/014-codebase-quality-refactor/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested — test tasks are omitted. Existing tests should be updated only where assertions change due to implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. US6 (BoundedDict) is already complete per research.md and requires no code changes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Docker config**: repository root (`docker-compose.yml`, `backend/Dockerfile`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project structure needed — all changes target existing files. This phase validates the current codebase state.

- [ ] T001 Verify existing backend tests pass: `cd backend && pytest -v`
- [ ] T002 Verify existing frontend tests pass: `cd frontend && npm test`
- [ ] T003 Verify backend linting passes: `cd backend && ruff check src tests && ruff format --check src tests`

---

## Phase 2: Foundational (No Blocking Prerequisites)

**Purpose**: No foundational/blocking prerequisites — all 10 user stories are independent edits to existing files with no shared new infrastructure.

**⚠️ NOTE**: This refactor has no blocking prerequisites. Each user story modifies different files (or different sections of shared files) and can proceed directly after Phase 1 validation.

**Checkpoint**: Baseline validated — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Correct Default Status Column Values (Priority: P1) 🎯 MVP

**Goal**: Replace the invalid `"Todo"` string in `DEFAULT_STATUS_COLUMNS` with `StatusNames.BACKLOG` so all default status columns reference canonical `StatusNames` values.

**Independent Test**: Create a new project with default settings and confirm all default status columns correspond to valid `StatusNames` values — no `"Todo"` appears.

### Implementation for User Story 1

- [ ] T004 [US1] Replace hardcoded strings in `DEFAULT_STATUS_COLUMNS` with `StatusNames` enum references in `backend/src/constants.py` — change `["Todo", "In Progress", "Done"]` to `[StatusNames.BACKLOG, StatusNames.IN_PROGRESS, StatusNames.DONE]` (note: `StatusNames.BACKLOG` resolves to the string `"Backlog"` at runtime)
- [ ] T005 [US1] Update test assertion for default status columns in `backend/tests/unit/test_config.py` to expect `["Backlog", "In Progress", "Done"]` instead of `["Todo", "In Progress", "Done"]`

**Checkpoint**: `DEFAULT_STATUS_COLUMNS` uses only canonical `StatusNames` values. Verify: `cd backend && pytest tests/unit/test_config.py -v`

---

## Phase 4: User Story 2 — Prevent Duplicate Admin Promotion (Priority: P1)

**Goal**: Eliminate the TOCTOU race condition in admin auto-promotion by replacing the SELECT-then-UPDATE pattern with an atomic `UPDATE ... WHERE admin_github_user_id IS NULL`.

**Independent Test**: Simulate two concurrent admin-promotion requests against a database with no admin set and confirm only one succeeds.

### Implementation for User Story 2

- [ ] T006 [US2] Refactor `require_admin` in `backend/src/dependencies.py` — replace the two-step SELECT + UPDATE with an atomic `UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1 AND admin_github_user_id IS NULL`, check `cursor.rowcount` to determine success, re-read on `rowcount == 0` for idempotent handling, and raise 403 if another user was promoted

**Checkpoint**: Admin promotion is atomic — only one user can be promoted. Verify: `cd backend && pytest tests/unit/test_admin_authorization.py -v`

---

## Phase 5: User Story 3 — Resilient Application Startup (Priority: P2)

**Goal**: Wrap the lifespan startup logic in `try/finally` so that background tasks and signal listeners are always cleaned up on startup failure.

**Independent Test**: Simulate a startup failure (e.g., database connection error) and confirm no background tasks or listeners remain running.

### Implementation for User Story 3

- [ ] T007 [US3] Refactor `lifespan()` in `backend/src/main.py` — initialize `cleanup_task = None` before a `try` block, move `yield` inside the `try`, move all cleanup (stop signal listener, cancel cleanup task, close database) into a `finally` block with None-guards for each resource

**Checkpoint**: Startup failures trigger proper cleanup. Verify: `cd backend && pytest tests/unit/test_main.py -v`

---

## Phase 6: User Story 4 — Lightweight Docker Health Checks (Priority: P2)

**Goal**: Replace the heavyweight `httpx`-based Docker healthcheck with a stdlib `urllib.request` call to reduce resource overhead.

**Independent Test**: Build the Docker image and confirm the healthcheck command runs successfully using `urllib.request` instead of `httpx`.

### Implementation for User Story 4

- [ ] T008 [P] [US4] Update `HEALTHCHECK CMD` in `backend/Dockerfile` — replace `python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health')"` with `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"`
- [ ] T009 [P] [US4] Update backend healthcheck in `docker-compose.yml` — replace the `httpx` import in the test command with `urllib.request.urlopen`

**Checkpoint**: Docker healthcheck uses stdlib only. Verify: Inspect `Dockerfile` and `docker-compose.yml` for `urllib.request`.

---

## Phase 7: User Story 5 — Auto-Detect Secure Cookie Flag (Priority: P2)

**Goal**: Add an `effective_cookie_secure` computed property to `Settings` that auto-detects HTTPS from `frontend_url`, and update cookie-setting code to use it.

**Independent Test**: Configure `frontend_url` with an HTTPS URL and confirm the effective cookie secure flag is `True` even when `cookie_secure` is not explicitly set.

### Implementation for User Story 5

- [ ] T010 [P] [US5] Add `effective_cookie_secure` property to `Settings` class in `backend/src/config.py` — returns `True` if `self.cookie_secure is True` OR `self.frontend_url.startswith("https://")`
- [ ] T011 [US5] Update `_set_session_cookie()` in `backend/src/api/auth.py` — change `secure=settings.cookie_secure` to `secure=settings.effective_cookie_secure`

**Checkpoint**: Cookie secure flag auto-detects HTTPS. Verify: `cd backend && pytest tests/unit/test_config.py -v`

---

## Phase 8: User Story 6 — Complete Dictionary Interface for BoundedDict (Priority: P3)

**Goal**: Verify `BoundedDict` already implements the full dict-like interface.

**Independent Test**: Run existing `BoundedDict` tests to confirm all methods work correctly.

### Implementation for User Story 6

- [ ] T012 [US6] Verify `BoundedDict` in `backend/src/utils.py` already implements `get()`, `pop()`, `keys()`, `values()`, `items()`, `__iter__()`, `clear()`, and `__repr__()` — no code changes needed per research.md R6. Run: `cd backend && pytest tests/unit/test_utils.py -v`

**Checkpoint**: BoundedDict is confirmed complete. No changes required.

---

## Phase 9: User Story 7 — Remove Unused DOM Testing Library (Priority: P3)

**Goal**: Remove `jsdom` from frontend `devDependencies` since `vitest.config.ts` uses `happy-dom`.

**Independent Test**: Remove `jsdom`, run `npm install`, and confirm all frontend tests pass.

### Implementation for User Story 7

- [ ] T013 [US7] Remove `jsdom` from `devDependencies` in `frontend/package.json` and run `cd frontend && npm install` to update `package-lock.json`

**Checkpoint**: Only `happy-dom` remains as DOM testing library. Verify: `cd frontend && npm test`

---

## Phase 10: User Story 8 — Settings Cache Clearing Utility (Priority: P3)

**Goal**: Add a `clear_settings_cache()` utility function to `config.py` for explicit cache clearing in test teardown.

**Independent Test**: Call `clear_settings_cache()` between tests and confirm mock settings do not leak.

### Implementation for User Story 8

- [ ] T014 [US8] Add `clear_settings_cache()` function to `backend/src/config.py` — delegates to `get_settings.cache_clear()`, placed immediately after the `get_settings()` function definition

**Checkpoint**: Cache clearing utility is available. Verify: `cd backend && python -c "from src.config import clear_settings_cache; clear_settings_cache(); print('OK')"`

---

## Phase 11: User Story 9 — Exponential Backoff for Session Cleanup Errors (Priority: P3)

**Goal**: Add exponential backoff (capped at 5 minutes) to `_session_cleanup_loop` to reduce log spam on repeated failures.

**Independent Test**: Simulate repeated cleanup failures and confirm the retry interval increases exponentially up to the cap, then resets on success.

### Implementation for User Story 9

- [ ] T015 [US9] Add exponential backoff to `_session_cleanup_loop` in `backend/src/main.py` — add `consecutive_failures = 0` counter, compute sleep as `min(interval * (2 ** consecutive_failures), 300)`, increment on failure, reset to 0 on success

**Checkpoint**: Cleanup loop backs off on errors. Verify: `cd backend && pytest tests/unit/test_main.py -v`

---

## Phase 12: User Story 10 — Flexible Environment File Resolution (Priority: P3)

**Goal**: Update `Settings.model_config` to check both `../.env` and `.env` for environment file resolution, supporting both local dev and Docker contexts.

**Independent Test**: Place a `.env` file in the expected location for each context and confirm Settings loads values correctly.

### Implementation for User Story 10

- [ ] T016 [US10] Update `env_file` in `Settings.model_config` in `backend/src/config.py` — change from `env_file="../.env"` to `env_file=("../.env", ".env")`

**Checkpoint**: Env file resolves in both local and Docker contexts. Verify: `cd backend && pytest tests/unit/test_config.py -v`

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories.

- [ ] T017 Run full backend test suite: `cd backend && pytest -v`
- [ ] T018 Run full frontend test suite: `cd frontend && npm test`
- [ ] T019 Run backend linting: `cd backend && ruff check src tests && ruff format --check src tests`
- [ ] T020 Run frontend linting: `cd frontend && npm run lint`
- [ ] T021 Run quickstart.md validation — confirm all file paths and commands are accurate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — no new infrastructure needed
- **User Stories (Phases 3–12)**: All depend on Phase 1 validation passing
  - All user stories are independent and can proceed in parallel
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 13)**: Depends on all user story phases being complete

### User Story Dependencies

- **US1 (P1)**: Independent — modifies `backend/src/constants.py`, `backend/tests/unit/test_config.py`
- **US2 (P1)**: Independent — modifies `backend/src/dependencies.py`
- **US3 (P2)**: Independent — modifies `backend/src/main.py` (lifespan function)
- **US4 (P2)**: Independent — modifies `backend/Dockerfile`, `docker-compose.yml`
- **US5 (P2)**: Independent — modifies `backend/src/config.py`, `backend/src/api/auth.py`
- **US6 (P3)**: No changes needed — verification only
- **US7 (P3)**: Independent — modifies `frontend/package.json`, `frontend/package-lock.json`
- **US8 (P3)**: Independent — modifies `backend/src/config.py` (new function, no overlap with US5 property)
- **US9 (P3)**: Independent — modifies `backend/src/main.py` (cleanup loop function, no overlap with US3 lifespan)
- **US10 (P3)**: Independent — modifies `backend/src/config.py` (model_config, no overlap with US5 or US8)

### Shared File Considerations

Three files are modified by multiple user stories but at non-overlapping locations:

| File | User Stories | Sections |
|------|-------------|----------|
| `backend/src/config.py` | US5, US8, US10 | US5: new property on Settings class · US8: new function after get_settings() · US10: model_config env_file field |
| `backend/src/main.py` | US3, US9 | US3: lifespan() function · US9: _session_cleanup_loop() function |
| `backend/tests/unit/test_config.py` | US1, US5, US10 | US1: update assertion for default status columns · US5/US10: existing tests may need assertion updates if coverage exists |

**Recommended order for shared files**: US10 → US5 → US8 (config.py), US3 → US9 (main.py)

### Within Each User Story

- Core implementation before integration
- Verify with targeted tests after each story
- Commit after each task or logical group

### Parallel Opportunities

- **Full parallel**: US1, US2, US3, US4, US6, US7 — all modify different files
- **Sequential within config.py**: US5, US8, US10 — different sections but same file
- **Sequential within main.py**: US3, US9 — different functions but same file
- **US4 tasks T008 + T009**: Parallel (Dockerfile and docker-compose.yml are separate files)
- **US5 tasks T010 + T011**: T010 first (add property), then T011 (use property)

---

## Parallel Example: All P1 Stories

```bash
# US1 and US2 can run simultaneously (different files):
Task T004: "Replace DEFAULT_STATUS_COLUMNS in backend/src/constants.py"
Task T006: "Refactor require_admin in backend/src/dependencies.py"

# US1 test update can run after T004:
Task T005: "Update test assertion in backend/tests/unit/test_config.py"
```

## Parallel Example: All P2 Stories

```bash
# US3, US4, US5 can all start simultaneously:
Task T007: "Refactor lifespan() in backend/src/main.py"
Task T008: "Update HEALTHCHECK in backend/Dockerfile"
Task T009: "Update healthcheck in docker-compose.yml"
Task T010: "Add effective_cookie_secure to backend/src/config.py"

# After T010 completes:
Task T011: "Update _set_session_cookie() in backend/src/api/auth.py"
```

## Parallel Example: All P3 Stories

```bash
# US7, US8, US9, US10 can start in parallel (US6 is verification only):
Task T012: "Verify BoundedDict in backend/src/utils.py"
Task T013: "Remove jsdom from frontend/package.json"
Task T014: "Add clear_settings_cache() to backend/src/config.py"
Task T015: "Add backoff to _session_cleanup_loop in backend/src/main.py"
Task T016: "Update env_file in backend/src/config.py"
```

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Validate baseline
2. Complete Phase 3: US1 — Fix DEFAULT_STATUS_COLUMNS (T004, T005)
3. Complete Phase 4: US2 — Atomic admin promotion (T006)
4. **STOP and VALIDATE**: Run `cd backend && pytest -v` — both P1 bugs are fixed
5. Deploy/demo if ready — critical bugs resolved

### Incremental Delivery

1. P1 stories (US1, US2) → Critical bug fixes → Validate
2. P2 stories (US3, US4, US5) → Reliability + security improvements → Validate
3. P3 stories (US6–US10) → Quality-of-life improvements → Validate
4. Polish (Phase 13) → Full suite validation → Done
5. Each priority tier adds value without breaking previous fixes

### Parallel Team Strategy

With multiple developers:

1. All start on different user stories immediately (no blocking prerequisites)
2. Developer A: US1 + US2 (P1 — critical bugs)
3. Developer B: US3 + US4 (P2 — reliability)
4. Developer C: US5 + US10 + US8 (P2/P3 — config.py changes)
5. Developer D: US7 + US9 (P3 — frontend + main.py)
6. All stories merge independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 21 (T001–T021) |
| **Setup tasks** | 3 (T001–T003) |
| **User story tasks** | 13 (T004–T016) |
| **Polish tasks** | 5 (T017–T021) |
| **User stories** | 10 (US1–US10) |
| **Stories requiring code changes** | 9 (US6 is already complete) |
| **Parallel opportunities** | 6 groups identified |
| **Suggested MVP scope** | US1 + US2 (P1 — 3 tasks) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- US6 requires no code changes — BoundedDict is already complete
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
