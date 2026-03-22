# Tasks: Startup Config Validation for AI Provider, Azure OpenAI, and Database Path

**Input**: Design documents from `/specs/001-startup-config-validation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Explicitly requested in FR-010 — 3 test classes with 11 total tests are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/backend/tests/`
- Scope: 2 files — `solune/backend/src/config.py` and `solune/backend/tests/unit/test_config_validation.py`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the `pathlib.Path` import required by database path validation and define the valid AI providers constant.

- [ ] T001 Add `from pathlib import Path` import to `solune/backend/src/config.py`
- [ ] T002 Define `_VALID_AI_PROVIDERS` constant (`{"copilot", "azure_openai"}`) at module level or inline in `_validate_production_secrets()` in `solune/backend/src/config.py`

---

## Phase 2: User Story 1 — Reject Unknown AI Provider at Startup (Priority: P1) 🎯 MVP

**Goal**: The system immediately rejects any unrecognized `ai_provider` value at boot time with a clear, actionable `ValueError` — fatal in both debug and production modes.

**Independent Test**: Provide an invalid `ai_provider` value (e.g., `"openai"`) and verify the application refuses to start with an error message that names the invalid value and lists the valid options (`"copilot"`, `"azure_openai"`).

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T003 [P] [US1] Add `TestAiProviderValidation.test_unknown_provider_raises` in `solune/backend/tests/unit/test_config_validation.py` — call `_make_production(ai_provider="openai")` and assert `pytest.raises(ValueError, match="Unknown AI_PROVIDER")`
- [ ] T004 [P] [US1] Add `TestAiProviderValidation.test_copilot_passes` in `solune/backend/tests/unit/test_config_validation.py` — call `_make_production(ai_provider="copilot")` and assert no error
- [ ] T005 [P] [US1] Add `TestAiProviderValidation.test_azure_openai_passes` in `solune/backend/tests/unit/test_config_validation.py` — call `_make_production(ai_provider="azure_openai", azure_openai_endpoint="https://x.openai.azure.com", azure_openai_key="key123")` and assert no error

### Implementation for User Story 1

- [ ] T006 [US1] Add `ai_provider` enum validation in `_validate_production_secrets()` in `solune/backend/src/config.py` — insert **before** the `if not self.debug:` branch (after `errors: list[str] = []`, around line 112) so it is fatal in both debug and production modes. Raise `ValueError(f"Unknown AI_PROVIDER '{self.ai_provider}'. Accepted values are: 'azure_openai', 'copilot'.")` when `self.ai_provider not in _VALID_AI_PROVIDERS`

**Checkpoint**: `pytest solune/backend/tests/unit/test_config_validation.py::TestAiProviderValidation -v` — all 3 tests pass

---

## Phase 3: User Story 2 — Validate Azure OpenAI Credential Completeness (Priority: P2)

**Goal**: When `ai_provider` is `"azure_openai"`, verify that both `azure_openai_endpoint` and `azure_openai_key` are provided. Accumulate errors in production; emit a warning in debug.

**Independent Test**: Set `ai_provider="azure_openai"` with one or both credentials missing and verify the appropriate error (production) or warning (debug) is produced.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T007 [P] [US2] Add `TestAzureOpenAIConfigRequired.test_missing_endpoint_raises` in `solune/backend/tests/unit/test_config_validation.py` — call `_make_production(ai_provider="azure_openai", azure_openai_endpoint=None, azure_openai_key="key123")` and assert `pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT is required")`
- [ ] T008 [P] [US2] Add `TestAzureOpenAIConfigRequired.test_missing_key_raises` in `solune/backend/tests/unit/test_config_validation.py` — call `_make_production(ai_provider="azure_openai", azure_openai_endpoint="https://x.openai.azure.com", azure_openai_key=None)` and assert `pytest.raises(ValueError, match="AZURE_OPENAI_KEY is required")`
- [ ] T009 [P] [US2] Add `TestAzureOpenAIConfigRequired.test_complete_config_passes` in `solune/backend/tests/unit/test_config_validation.py` — call `_make_production(ai_provider="azure_openai", azure_openai_endpoint="https://x.openai.azure.com", azure_openai_key="key123")` and assert no error
- [ ] T010 [P] [US2] Add `TestAzureOpenAIConfigRequired.test_missing_config_warns_in_debug` in `solune/backend/tests/unit/test_config_validation.py` — call `_make_debug(ai_provider="azure_openai")` with `caplog` fixture and assert `"Azure OpenAI credentials incomplete"` appears in `caplog.text`

### Implementation for User Story 2

- [ ] T011 [US2] Add Azure OpenAI completeness check in the **production block** of `_validate_production_secrets()` in `solune/backend/src/config.py` — if `self.ai_provider == "azure_openai"`, append errors for missing `azure_openai_endpoint` (`"AZURE_OPENAI_ENDPOINT is required when AI_PROVIDER='azure_openai'. Set it to your Azure OpenAI resource URL."`) and/or missing `azure_openai_key` (`"AZURE_OPENAI_KEY is required when AI_PROVIDER='azure_openai'. Set it to your Azure OpenAI API key."`)
- [ ] T012 [US2] Add Azure OpenAI completeness warning in the **debug block** of `_validate_production_secrets()` in `solune/backend/src/config.py` — if `self.ai_provider == "azure_openai"` and either credential is missing, emit `_logger.warning("Azure OpenAI credentials incomplete — AI features will not work (debug mode)")`

**Checkpoint**: `pytest solune/backend/tests/unit/test_config_validation.py::TestAzureOpenAIConfigRequired -v` — all 4 tests pass

---

## Phase 4: User Story 3 — Validate Database Path in Production (Priority: P3)

**Goal**: Reject empty or non-absolute `database_path` values in production mode. Allow `:memory:` and relative paths in debug mode. Never perform directory existence checks.

**Independent Test**: Provide an empty or relative `database_path` in production mode and verify an error is produced, or provide a valid absolute path and verify acceptance.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US3] Add `TestDatabasePathValidation.test_empty_path_raises` in `solune/backend/tests/unit/test_config_validation.py` — call `_make_production(database_path="")` and assert `pytest.raises(ValueError, match="DATABASE_PATH must not be empty")`
- [ ] T014 [P] [US3] Add `TestDatabasePathValidation.test_relative_path_raises_in_production` in `solune/backend/tests/unit/test_config_validation.py` — call `_make_production(database_path="data/settings.db")` and assert `pytest.raises(ValueError, match="DATABASE_PATH must be an absolute path")`
- [ ] T015 [P] [US3] Add `TestDatabasePathValidation.test_absolute_path_passes` in `solune/backend/tests/unit/test_config_validation.py` — call `_make_production(database_path="/var/lib/solune/data/settings.db")` and assert no error
- [ ] T016 [P] [US3] Add `TestDatabasePathValidation.test_relative_path_allowed_in_debug` in `solune/backend/tests/unit/test_config_validation.py` — call `_make_debug(database_path="data/settings.db")` and assert no error

### Implementation for User Story 3

- [ ] T017 [US3] Add database path validation in the **production block only** of `_validate_production_secrets()` in `solune/backend/src/config.py` — after Azure OpenAI checks, strip `database_path` and: (a) if empty, append `"DATABASE_PATH must not be empty in production mode. Set it to an absolute path (e.g., /var/lib/solune/data/settings.db)."`, (b) elif not `":memory:"` and not `Path(db).is_absolute()`, append `"DATABASE_PATH must be an absolute path in production mode (got '{self.database_path}'). Use a full path starting with /."`

**Checkpoint**: `pytest solune/backend/tests/unit/test_config_validation.py::TestDatabasePathValidation -v` — all 4 tests pass

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Verify all tests pass and no regressions exist in existing configuration tests.

- [ ] T018 Run full validation test suite: `pytest solune/backend/tests/unit/test_config_validation.py -v` — all existing + new tests pass (11 new tests across 3 classes)
- [ ] T019 Run config property regression tests: `pytest solune/backend/tests/unit/test_config.py -v` — no regressions
- [ ] T020 Verify validation order in `_validate_production_secrets()`: (1) ai_provider enum check (universal), (2) Azure OpenAI completeness (branched), (3) DB path (production only)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (Phase 2)**: Depends on Phase 1 (needs `_VALID_AI_PROVIDERS` constant)
- **User Story 2 (Phase 3)**: Depends on Phase 1; independent of US1 (but logically after)
- **User Story 3 (Phase 4)**: Depends on Phase 1 (`pathlib.Path` import); independent of US1/US2
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Setup — independent of US1 (but US1's enum check ensures valid `ai_provider` before Azure check runs)
- **User Story 3 (P3)**: Can start after Setup — fully independent of US1 and US2

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Implementation modifies `solune/backend/src/config.py` (same function — sequential within story)
- Story tests should pass after implementation

### Parallel Opportunities

- **T001 + T002**: Setup tasks can be done together (same file, but non-overlapping changes)
- **T003 + T004 + T005**: All US1 tests can be written in parallel (same file, different test methods)
- **T007 + T008 + T009 + T010**: All US2 tests can be written in parallel
- **T013 + T014 + T015 + T016**: All US3 tests can be written in parallel
- **US1 tests + US2 tests + US3 tests**: All test classes can be written in a single batch since they are in the same file but different classes

---

## Parallel Example: All Test Classes

```bash
# All test tasks across stories can be batched (same file, independent classes):
Task: T003-T005 "TestAiProviderValidation class in tests/unit/test_config_validation.py"
Task: T007-T010 "TestAzureOpenAIConfigRequired class in tests/unit/test_config_validation.py"
Task: T013-T016 "TestDatabasePathValidation class in tests/unit/test_config_validation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: User Story 1 tests + implementation (T003–T006)
3. **STOP and VALIDATE**: `pytest tests/unit/test_config_validation.py::TestAiProviderValidation -v`
4. Unknown AI providers are now rejected at startup — MVP complete

### Incremental Delivery

1. Complete Setup → pathlib import + constant ready
2. Add User Story 1 → AI provider enum validation → Test independently (MVP!)
3. Add User Story 2 → Azure OpenAI completeness checks → Test independently
4. Add User Story 3 → Database path validation → Test independently
5. Each story adds validation without breaking previous stories or existing tests

### Parallel Team Strategy

With multiple developers:

1. Developer A: All test classes (T003–T016) — single file, no conflicts
2. Developer B: All implementation tasks (T001, T002, T006, T011, T012, T017) — single file, sequential in validator
3. Alternatively, each developer takes one user story end-to-end

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 20 |
| Setup tasks | 2 (T001–T002) |
| US1 tasks (P1 — AI Provider) | 4 (T003–T006: 3 tests + 1 impl) |
| US2 tasks (P2 — Azure OpenAI) | 6 (T007–T012: 4 tests + 2 impl) |
| US3 tasks (P3 — Database Path) | 5 (T013–T017: 4 tests + 1 impl) |
| Polish tasks | 3 (T018–T020) |
| Parallel opportunities | Test classes can be batched; all [P] tasks within a phase |
| Files modified | 2 (`config.py`, `test_config_validation.py`) |
| Suggested MVP scope | Setup + User Story 1 (T001–T006) |
| Format validation | ✅ ALL tasks follow checklist format (checkbox, ID, labels, file paths) |

## Notes

- [P] tasks = different files or independent test methods, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after implementation
- Tests are written FIRST and verified to FAIL before implementation (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing `_make_production()` and `_make_debug()` helpers require no changes
