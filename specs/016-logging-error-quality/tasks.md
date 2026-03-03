# Tasks: Improve Logging, Error Message Handling & Code Quality

**Input**: Design documents from `/specs/016-logging-error-quality/`
**Prerequisites**: spec.md (required for user stories)

**Tests**: Tests are OPTIONAL — the specification uses SHOULD (not MUST) for test additions (FR-010). Test tasks are not included below; add them if TDD is desired.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5, US6)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Scope is limited to backend only per spec assumptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the centralized logging utility module and sensitive-data pattern configuration that all user stories depend on

- [x] T001 Create centralized logging utility module with redact function stub, structured formatter stub, and request-ID logging filter stub in backend/src/logging_utils.py
- [x] T002 [P] Define sensitive-data redaction patterns (tokens, API keys, PII, credentials, internal paths) as a configurable list in backend/src/logging_utils.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement core sanitization, structured formatting, and request-ID injection infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Implement the redact function that scrubs sensitive data from arbitrary strings using the pattern list defined in T002 in backend/src/logging_utils.py
- [x] T004 [P] Implement a SanitizingFormatter (logging.Formatter subclass) that applies the redact function to every log record message before emission in backend/src/logging_utils.py
- [x] T005 [P] Implement a StructuredJsonFormatter (logging.Formatter subclass) that emits log records as JSON objects with fields: timestamp, level, message, logger, and context metadata in backend/src/logging_utils.py
- [x] T006 [P] Implement a RequestIDFilter (logging.Filter subclass) that injects the current request ID from the ContextVar in backend/src/middleware/request_id.py into every log record in backend/src/logging_utils.py
- [x] T007 Update setup_logging() in backend/src/config.py to accept a structured mode flag, attach the SanitizingFormatter (always), attach StructuredJsonFormatter (when structured=True), and attach RequestIDFilter to the root logger
- [x] T008 Update the lifespan handler in backend/src/main.py to pass the structured flag (based on debug setting) when calling setup_logging()

**Checkpoint**: Foundation ready — centralized logging utility installed, all log output passes through sanitization and includes request ID

---

## Phase 3: User Story 1 — Sensitive Data Never Appears in Logs (Priority: P1) 🎯 MVP

**Goal**: All log output is automatically sanitized so that credentials, tokens, API keys, PII, and internal file paths are never written to any log destination.

**Independent Test**: Trigger log-emitting operations (requests, errors, auth flows) and verify that no sensitive data appears in log output. Search logs for known test tokens, API keys, or email addresses — zero matches expected.

### Implementation for User Story 1

- [x] T009 [US1] Expand redaction patterns to cover GitHub token formats (ghp_, gho_, ghs_, github_pat_), Bearer tokens, Basic auth, and common API key formats in backend/src/logging_utils.py
- [x] T010 [P] [US1] Add PII redaction patterns for email addresses, and configurable maximum log message length (truncation for oversized payloads) in backend/src/logging_utils.py
- [x] T011 [P] [US1] Add internal file path sanitization pattern that strips system-specific directory prefixes from production log output in backend/src/logging_utils.py
- [x] T012 [US1] Audit and update the OAuth token exchange error log at backend/src/api/auth.py line ~110 to ensure the exception object does not leak token values
- [x] T013 [US1] Add resilience to the logging utility so that failures in the sanitization or formatting layer fall back to stderr and do not crash the application in backend/src/logging_utils.py

**Checkpoint**: User Story 1 complete — all log output passes through sanitization; sensitive patterns are redacted automatically

---

## Phase 4: User Story 2 — Consistent Structured Logging Across All Modules (Priority: P1)

**Goal**: All modules emit logs in a consistent, structured format with standard severity levels, machine-parseable in production and human-readable in development.

**Independent Test**: Examine log output from multiple modules; verify every entry contains timestamp, severity level, message, module name, and request ID. Verify no caught-and-handled errors are logged as FATAL.

### Implementation for User Story 2

- [x] T014 [US2] Create a get_logger(name) helper in backend/src/logging_utils.py that returns a logger pre-configured with the operation context and is the standard way for all modules to obtain a logger
- [x] T015 [P] [US2] Update log format in backend/src/config.py to include request_id field in the format string for the human-readable formatter (development mode)
- [x] T016 [P] [US2] Audit severity levels in backend/src/api/chat.py — ensure caught-and-handled errors use WARNING or ERROR (not FATAL/CRITICAL) and informational events use INFO
- [x] T017 [P] [US2] Audit severity levels in backend/src/api/board.py — ensure caught-and-handled errors use WARNING or ERROR and informational events use INFO
- [x] T018 [P] [US2] Audit severity levels in backend/src/api/workflow.py — ensure caught-and-handled errors use WARNING or ERROR and informational events use INFO
- [x] T019 [P] [US2] Audit severity levels in backend/src/api/webhooks.py — ensure caught-and-handled errors use WARNING or ERROR and informational events use INFO
- [x] T020 [P] [US2] Audit severity levels in backend/src/services/github_projects/service.py — ensure caught-and-handled errors use WARNING or ERROR and informational events use INFO
- [x] T021 [US2] Verify that the StructuredJsonFormatter output is valid JSON and parseable by standard log aggregation tools (manual check of sample output)

**Checkpoint**: User Story 2 complete — all log entries follow consistent format with correct severity levels and contextual metadata

---

## Phase 5: User Story 3 — Safe Error Messages Returned to Callers (Priority: P1)

**Goal**: Error responses never expose internal implementation details, raw exceptions, stack traces, or database errors. Detailed error info is logged server-side only.

**Independent Test**: Trigger various error conditions (invalid input, server errors, DB failures, third-party failures) and verify returned error messages are generic and safe. Verify detailed info appears only in server logs.

### Implementation for User Story 3

- [x] T022 [US3] Create a safe_error_response() helper in backend/src/logging_utils.py that logs detailed error info server-side and returns a generic user-safe message string
- [x] T023 [US3] Replace str(e) in HTTPException detail at backend/src/api/housekeeping.py lines ~79, ~204, ~218 with safe static error messages and log the original exception server-side
- [x] T024 [P] [US3] Replace str(e) in GitHubAPIError details at backend/src/api/board.py lines ~63, ~118 with safe static error messages and log the original exception server-side
- [x] T025 [P] [US3] Replace str(e) in error response content at backend/src/api/chat.py lines ~299, ~421 with safe static error messages and log the original exception server-side
- [x] T026 [P] [US3] Replace str(e) in GitHubAPIError details at backend/src/api/cleanup.py lines ~52, ~104, ~125 with safe static error messages and log the original exception server-side
- [x] T027 [P] [US3] Replace str(e) in error response at backend/src/api/webhooks.py lines ~188, ~543 with safe static error messages and log the original exception server-side
- [x] T028 [P] [US3] Replace str(e) in GitHubAPIError message at backend/src/api/workflow.py line ~253 with a safe static error message and log the original exception server-side
- [x] T029 [US3] Verify the generic exception handler in backend/src/main.py lines ~253-259 returns only "Internal server error" and logs full context (request ID, operation) server-side

**Checkpoint**: User Story 3 complete — zero API error responses contain raw exception text, stack traces, or internal details

---

## Phase 6: User Story 4 — DRY Logging and Error-Handling Logic (Priority: P2)

**Goal**: Logging setup, formatting, and error-handling patterns are centralized so that changes only need to be made in one place.

**Independent Test**: Modify the centralized logging configuration (e.g., change format or add a redaction pattern) and verify the change applies to log output from all modules without modifying individual files.

### Implementation for User Story 4

- [x] T030 [US4] Extract the repeated "log exception + raise safe AppException" pattern into a shared handle_service_error() helper in backend/src/logging_utils.py
- [x] T031 [US4] Refactor duplicate error handling blocks in backend/src/api/board.py to use the shared handle_service_error() helper
- [x] T032 [P] [US4] Refactor duplicate error handling blocks in backend/src/api/cleanup.py to use the shared handle_service_error() helper
- [x] T033 [P] [US4] Refactor duplicate error handling blocks in backend/src/api/chat.py to use the shared handle_service_error() helper
- [x] T034 [P] [US4] Refactor duplicate error handling blocks in backend/src/api/workflow.py to use the shared handle_service_error() helper
- [x] T035 [US4] Verify that all modules obtain loggers via get_logger() from backend/src/logging_utils.py — no ad-hoc logging.getLogger() with custom configuration outside config.py

**Checkpoint**: User Story 4 complete — logging and error-handling logic lives in one place; modules use shared utilities

---

## Phase 7: User Story 5 — Unhandled Exceptions Are Caught with Context (Priority: P2)

**Goal**: All unhandled exceptions and async rejections are caught by a global handler and logged with request ID, operation name, and safe user identifier.

**Independent Test**: Deliberately trigger unhandled exceptions in various request handlers and verify each produces a log entry with request ID, operation name, and safe context. Verify the response is always a generic safe error.

### Implementation for User Story 5

- [x] T036 [US5] Enhance the generic exception handler in backend/src/main.py to include the request ID (from ContextVar), request method, and request path in the logged error context
- [x] T037 [US5] Add a global unhandled-async-exception hook (asyncio exception handler) in backend/src/main.py lifespan to catch and log unhandled async errors with context
- [x] T038 [US5] Verify that every globally caught error returns the safe generic "Internal server error" response per User Story 3 in backend/src/main.py

**Checkpoint**: User Story 5 complete — no exception goes silently unnoticed; all unhandled errors logged with context and return safe responses

---

## Phase 8: User Story 6 — Code Quality Cleanup via Full Review (Priority: P3)

**Goal**: Full code review pass to remove dead code, simplify overly complex logic, and standardize inconsistent patterns in logging and error handling.

**Independent Test**: Compare codebase metrics (linting warnings, dead code instances) before and after. Run full test suite to confirm no behavioral regressions.

### Implementation for User Story 6

- [x] T039 [P] [US6] Remove dead or unreachable code related to logging and error handling identified during review across backend/src/api/ files
- [x] T040 [P] [US6] Simplify overly complex try/except blocks in backend/src/services/github_projects/service.py where error handling is nested or redundant
- [x] T041 [P] [US6] Standardize all remaining inconsistent logging patterns (e.g., mixed logger.error vs logger.exception usage, inconsistent message formatting) across backend/src/api/ and backend/src/services/ files
- [x] T042 [US6] Run ruff check and ruff format on backend/src/ and backend/tests/ to verify code quality after all changes (ruff check src tests && ruff format --check src tests)

**Checkpoint**: User Story 6 complete — codebase is cleaner with no dead code, simplified logic, and consistent patterns

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cross-cutting improvements

- [x] T043 [P] Add docstrings and inline documentation to backend/src/logging_utils.py explaining the sanitization patterns, formatter modes, and usage guidelines
- [x] T044 [P] Verify log truncation works for oversized payloads (manually test with a >10KB log message) in backend/src/logging_utils.py
- [x] T045 [P] Verify the logging utility self-resilience (manually trigger a formatter error and confirm fallback to stderr) in backend/src/logging_utils.py
- [x] T046 Run full backend linting (ruff check src tests && ruff format --check src tests) and test suite to verify no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — Sanitization patterns + formatter
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — Structured formatter + request ID filter
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — Can start in parallel with US1/US2
- **User Story 4 (Phase 6)**: Depends on US1 + US2 + US3 — DRY refactor requires centralized utilities to exist
- **User Story 5 (Phase 7)**: Depends on Foundational (Phase 2) + US3 — Global handler uses safe error responses
- **User Story 6 (Phase 8)**: Depends on US1–US5 — Cleanup pass runs after all patterns are established
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories; can run in parallel with US1
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories; can run in parallel with US1 and US2
- **User Story 4 (P2)**: Depends on US1, US2, US3 — Refactors patterns established in those stories
- **User Story 5 (P2)**: Depends on Foundational + US3 — Uses safe error responses
- **User Story 6 (P3)**: Depends on all previous stories — Final cleanup pass

### Within Each User Story

- Utility/helper functions before consumers
- Core implementation before integration
- Audit/review tasks before verification tasks

### Parallel Opportunities

- T001 and T002 can run in parallel within Setup — independent aspects of logging_utils.py initialization
- T004, T005, and T006 can run in parallel within Foundational — independent formatter/filter implementations
- US1, US2, and US3 can all start in parallel once Foundational is complete — different concerns (sanitization, format, error responses)
- T010 and T011 can run in parallel within US1 — independent pattern additions
- T016, T017, T018, T019, and T020 can run in parallel within US2 — auditing different files
- T024, T025, T026, T027, and T028 can run in parallel within US3 — fixing different API files
- T032, T033, and T034 can run in parallel within US4 — refactoring different API files
- T039, T040, and T041 can run in parallel within US6 — independent cleanup targets
- T043, T044, and T045 can run in parallel within Polish — independent verification tasks

---

## Parallel Example: Setup Phase

```bash
# Launch setup tasks in parallel (independent aspects):
Task: T001 "Create centralized logging utility module in backend/src/logging_utils.py"
Task: T002 "Define sensitive-data redaction patterns in backend/src/logging_utils.py"
```

## Parallel Example: Foundational Phase

```bash
# Launch formatter and filter implementations in parallel (independent classes):
Task: T004 "Implement SanitizingFormatter in backend/src/logging_utils.py"
Task: T005 "Implement StructuredJsonFormatter in backend/src/logging_utils.py"
Task: T006 "Implement RequestIDFilter in backend/src/logging_utils.py"
```

## Parallel Example: User Stories 1, 2, and 3 (after Foundational)

```bash
# All three P1 stories can start in parallel (different concerns):
Phase 3 (US1): "Sanitization patterns + auditing log calls"
Phase 4 (US2): "Severity audits + structured format verification"
Phase 5 (US3): "Replace str(e) in API error responses across all files"
```

## Parallel Example: User Story 3 (fixing API files)

```bash
# Launch all API file fixes in parallel (different files):
Task: T024 "Fix board.py error responses"
Task: T025 "Fix chat.py error responses"
Task: T026 "Fix cleanup.py error responses"
Task: T027 "Fix webhooks.py error responses"
Task: T028 "Fix workflow.py error responses"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 + 3 Only)

1. Complete Phase 1: Setup (logging utility module)
2. Complete Phase 2: Foundational (sanitization + formatters + request ID filter)
3. Complete Phase 3: User Story 1 (sensitive data never in logs)
4. Complete Phase 4: User Story 2 (consistent structured logging)
5. Complete Phase 5: User Story 3 (safe error messages)
6. **STOP and VALIDATE**: All P1 stories deliver immediate security + operational value
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Logging infrastructure ready
2. Add User Story 1 → Log sanitization active → Deploy/Demo (security MVP!)
3. Add User Story 2 → Structured logging active → Deploy/Demo
4. Add User Story 3 → Safe error responses → Deploy/Demo (full P1 complete!)
5. Add User Story 4 → DRY refactor → Deploy/Demo
6. Add User Story 5 → Global exception context → Deploy/Demo
7. Add User Story 6 → Code quality cleanup → Deploy/Demo
8. Polish → Final validation → Release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (sanitization)
   - Developer B: User Story 2 (structured logging)
   - Developer C: User Story 3 (safe error messages)
3. After P1 stories complete:
   - Developer A: User Story 4 (DRY refactor)
   - Developer B: User Story 5 (global exception handler)
4. Final pass:
   - Any developer: User Story 6 (code quality cleanup)
5. Stories complete and integrate independently

---

## Summary

- **Total tasks**: 46
- **Phase 1 (Setup)**: 2 tasks
- **Phase 2 (Foundational)**: 6 tasks
- **Phase 3 (US1 — Sensitive Data Sanitization)**: 5 tasks
- **Phase 4 (US2 — Structured Logging)**: 8 tasks
- **Phase 5 (US3 — Safe Error Messages)**: 8 tasks
- **Phase 6 (US4 — DRY Logging/Error Handling)**: 6 tasks
- **Phase 7 (US5 — Unhandled Exceptions with Context)**: 3 tasks
- **Phase 8 (US6 — Code Quality Cleanup)**: 4 tasks
- **Phase 9 (Polish)**: 4 tasks
- **Parallel opportunities**: 9 identified (Setup, Foundational, US1, US2, US3, US4, US6, Polish, cross-story P1 parallelism)
- **Independent test criteria**: Each user story has a clear independent test defined
- **Suggested MVP scope**: User Stories 1 + 2 + 3 (all P1 — Phases 1–5, 29 tasks)
- **Format validation**: ✅ All 46 tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Backend follows existing FastAPI + Python logging patterns
- Scope is backend only per spec assumptions (frontend logging excluded)
- No test tasks included (FR-010 uses SHOULD, not MUST; tests not explicitly requested)
- Existing custom exception hierarchy (AppException, etc.) is preserved and integrated
- New centralized utility complements existing setup_logging() in config.py
- Request ID middleware already exists; tasks add it to log records via filter
