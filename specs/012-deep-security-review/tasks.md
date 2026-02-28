# Tasks: Deep Security Review and Application Hardening

**Input**: Design documents from `/specs/012-deep-security-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification. Existing tests must continue to pass (spec success criteria: all existing auth tests pass, zero functional regressions). No new test tasks are generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Workflows**: `.github/workflows/`
- **Specs**: `specs/012-deep-security-review/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline understanding and audit context before making any changes

- [ ] T001 Review current CI workflow configuration in .github/workflows/ci.yml and document all third-party action references, trigger patterns, and permission state
- [ ] T002 [P] Run backend dependency audit against backend/pyproject.toml and record all findings
- [ ] T003 [P] Run frontend dependency audit against frontend/package.json and frontend/package-lock.json and record all findings
- [ ] T004 [P] Scan entire repository for hardcoded secrets, credentials, API keys, and tokens across all source, config, and workflow files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: There are no new foundational infrastructure tasks for this security hardening feature. The existing project structure, auth framework, and error handling are already in place. All changes are in-place modifications to existing files.

**⚠️ NOTE**: Phase 1 audit tasks must complete before remediation phases begin, so that findings inform the work.

**Checkpoint**: Audit complete — remediation work can now begin in parallel across user stories

---

## Phase 3: User Story 1 — Secure GitHub Workflow Configurations (Priority: P1) 🎯 MVP

**Goal**: Harden all GitHub Workflow files with SHA-pinned actions, least-privilege permissions, and no insecure trigger patterns (FR-001, FR-002, FR-014)

**Independent Test**: Inspect .github/workflows/ci.yml and verify every `uses:` directive has a full 40-character SHA, explicit `permissions` blocks exist at top-level and/or per-job, and no `pull_request_target` with head checkout is present

### Implementation for User Story 1

- [ ] T005 [US1] Pin actions/checkout from @v4 to full commit SHA in .github/workflows/ci.yml (backend, frontend, and docker job steps)
- [ ] T006 [US1] Pin actions/setup-python from @v5 to full commit SHA in .github/workflows/ci.yml
- [ ] T007 [US1] Pin actions/setup-node from @v4 to full commit SHA in .github/workflows/ci.yml
- [ ] T008 [US1] Add top-level `permissions: {}` block (deny-all default) to .github/workflows/ci.yml
- [ ] T009 [US1] Add job-level `permissions: { contents: read }` to the backend job in .github/workflows/ci.yml
- [ ] T010 [US1] Add job-level `permissions: { contents: read }` to the frontend job in .github/workflows/ci.yml
- [ ] T011 [US1] Add job-level `permissions: { contents: read }` to the docker job in .github/workflows/ci.yml
- [ ] T012 [US1] Add inline comments with human-readable version tags next to each SHA-pinned action reference in .github/workflows/ci.yml
- [ ] T013 [US1] Verify no insecure trigger patterns (pull_request_target with head checkout) exist in .github/workflows/ci.yml

**Checkpoint**: CI workflow is fully hardened — all actions SHA-pinned, permissions least-privilege, no insecure triggers

---

## Phase 4: User Story 2 — Secrets and Sensitive Data Protection (Priority: P1)

**Goal**: Confirm zero hardcoded credentials, API keys, tokens, or secrets exist in source code, configuration, or workflow files (FR-003)

**Independent Test**: Run a secrets scan across the entire repository and verify all matches are placeholders, test fixtures, or configuration references — not real credentials

### Implementation for User Story 2

- [ ] T014 [P] [US2] Verify .env and .env.local are excluded via .gitignore
- [ ] T015 [P] [US2] Verify .env.example contains only placeholder values with descriptive comments in .env.example
- [ ] T016 [P] [US2] Verify docker-compose.yml uses ${VAR_NAME} substitution for all sensitive values in docker-compose.yml
- [ ] T017 [P] [US2] Verify backend config loads all secrets from environment variables via pydantic-settings in backend/src/config.py
- [ ] T018 [P] [US2] Verify test fixtures use only dummy/mock values in backend/tests/
- [ ] T019 [US2] Document secrets management audit results as findings in the security findings report

**Checkpoint**: Secrets audit complete — zero real credentials in codebase confirmed and documented

---

## Phase 5: User Story 3 — Dependency Vulnerability Remediation (Priority: P1)

**Goal**: Identify and remediate all critical and high-severity known vulnerabilities in backend and frontend dependencies (FR-004)

**Independent Test**: Run `pip-audit` against backend and `npm audit` against frontend and verify zero critical or high-severity advisories remain

### Implementation for User Story 3

- [ ] T020 [P] [US3] Run pip-audit or equivalent against backend/pyproject.toml and document all critical/high findings
- [ ] T021 [P] [US3] Run npm audit against frontend/package-lock.json and document all critical/high findings
- [ ] T022 [US3] Update backend dependencies in backend/pyproject.toml to remediate any critical or high-severity CVEs found
- [ ] T023 [US3] Update frontend dependencies in frontend/package.json and regenerate frontend/package-lock.json to remediate any critical or high-severity advisories found
- [ ] T024 [US3] Verify all existing backend tests pass after dependency updates
- [ ] T025 [US3] Verify all existing frontend tests pass after dependency updates
- [ ] T026 [US3] Document all dependency findings and remediations (or accepted risks) in the security findings report

**Checkpoint**: Dependency trees clean — zero critical/high CVEs remain (or accepted risks documented)

---

## Phase 6: User Story 4 — Authentication and Authorization Hardening (Priority: P2)

**Goal**: Harden authentication and authorization flows against session hijacking, privilege escalation, and broken access control (FR-005, FR-006, FR-007, FR-013)

**Independent Test**: Review auth code paths for OAuth state validation, cookie flags, admin endpoint protection, and encryption key warnings; verify each control is properly implemented

### Implementation for User Story 4

- [ ] T027 [P] [US4] Review and verify OAuth state parameter validation (secrets.token_urlsafe, TTL, single-use pop, bounded dict) in backend/src/services/github_auth.py
- [ ] T028 [P] [US4] Review and verify session cookie flags (HttpOnly, SameSite=lax, configurable Secure, max_age) in backend/src/api/auth.py
- [ ] T029 [P] [US4] Review and verify admin authorization enforcement via require_admin() dependency in backend/src/dependencies.py
- [ ] T030 [P] [US4] Review and verify EncryptionService startup warning when ENCRYPTION_KEY is not configured in backend/src/services/encryption.py
- [ ] T031 [US4] Document authentication and authorization audit findings in the security findings report

**Checkpoint**: Auth hardening verified — all controls confirmed operational and documented

---

## Phase 7: User Story 5 — Input Validation and Data Exposure Prevention (Priority: P2)

**Goal**: Ensure all inputs are validated, API error responses do not leak sensitive information, and logs are free of credentials (FR-008, FR-009, FR-010)

**Independent Test**: Submit malicious payloads through API endpoints and verify responses contain generic messages; inspect logs and verify no credentials or tokens appear

### Implementation for User Story 5

- [ ] T032 [US5] Replace `detail=str(e)` with generic "Authentication failed" message in the OAuth callback error handler in backend/src/api/auth.py and log original exception at WARNING level
- [ ] T033 [US5] Replace `detail=f"Invalid GitHub token: {e}"` with generic "Authentication failed" message in the dev-login error handler in backend/src/api/auth.py and log original exception at WARNING level
- [ ] T034 [P] [US5] Review generic exception handler in backend/src/main.py to confirm it returns "Internal server error" without leaking details
- [ ] T035 [P] [US5] Review backend logging patterns to confirm %s formatting is used (no f-strings with user data) and no credentials appear in logs across backend/src/
- [ ] T036 [P] [US5] Verify React frontend does not use dangerouslySetInnerHTML or other XSS vectors across frontend/src/
- [ ] T037 [P] [US5] Verify backend uses parameterized SQL queries (no string concatenation) across backend/src/
- [ ] T038 [US5] Document input validation and data exposure findings in the security findings report

**Checkpoint**: Error responses sanitized, input validation confirmed, no data leakage in logs

---

## Phase 8: User Story 6 — Consolidated Security Utilities (Priority: P3)

**Goal**: Consolidate any duplicated security logic into shared, reusable modules following DRY principles (FR-011)

**Independent Test**: Search the codebase for duplicated auth checks, validation routines, and secrets-handling patterns; verify each security concern has at most one canonical implementation

### Implementation for User Story 6

- [ ] T039 [US6] Extract duplicated cookie-setting logic from OAuth login and dev-login endpoints into a shared helper function in backend/src/api/auth.py
- [ ] T040 [US6] Update the OAuth login endpoint to use the shared cookie-setting helper in backend/src/api/auth.py (depends on T039)
- [ ] T041 [US6] Update the dev-login endpoint to use the shared cookie-setting helper in backend/src/api/auth.py (depends on T039)
- [ ] T042 [US6] Verify all existing tests pass after cookie helper refactor
- [ ] T043 [US6] Document security logic consolidation findings in the security findings report

**Checkpoint**: Duplicated security logic consolidated — each security concern has one canonical implementation

---

## Phase 9: User Story 7 — Security Findings Documentation (Priority: P3)

**Goal**: Produce a comprehensive security findings report documenting all issues found, fixes applied, severity ratings, and accepted risks (FR-012)

**Independent Test**: Verify the report exists, contains categorized findings with SEC-### IDs, severity ratings, affected components, remediation status, and justification for any accepted risks

### Implementation for User Story 7

- [ ] T044 [US7] Create security findings report at specs/012-deep-security-review/security-findings-report.md with header, methodology section, and severity classification system
- [ ] T045 [US7] Document all GitHub Actions workflow findings (SHA pinning, permissions, triggers) with SEC-### IDs and severity ratings in specs/012-deep-security-review/security-findings-report.md
- [ ] T046 [P] [US7] Document all secrets management findings in specs/012-deep-security-review/security-findings-report.md
- [ ] T047 [P] [US7] Document all dependency vulnerability findings in specs/012-deep-security-review/security-findings-report.md
- [ ] T048 [P] [US7] Document all authentication and authorization findings in specs/012-deep-security-review/security-findings-report.md
- [ ] T049 [P] [US7] Document all input validation and data exposure findings in specs/012-deep-security-review/security-findings-report.md
- [ ] T050 [US7] Add summary table with total counts by severity, remediation status breakdown, and accepted risk justifications in specs/012-deep-security-review/security-findings-report.md
- [ ] T051 [US7] Add recommendations section for future enhancements (rate limiting, git secrets scanning in CI, Dependabot for SHA updates) in specs/012-deep-security-review/security-findings-report.md

**Checkpoint**: Security findings report complete — all findings documented, categorized, and actionable

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories and cleanup

- [ ] T052 Run all existing backend tests (pytest) to confirm zero regressions after all security changes
- [ ] T053 Run all existing frontend tests (npm test) to confirm zero regressions after all security changes
- [ ] T054 Run backend linting (ruff check, ruff format --check, pyright) to confirm code quality after changes
- [ ] T055 Run frontend linting (npm run lint, npm run type-check) to confirm code quality after changes
- [ ] T056 Run frontend build (npm run build) to confirm build succeeds after changes
- [ ] T057 Run quickstart.md validation steps to confirm all verification commands pass
- [ ] T058 Final review of security findings report for completeness and accuracy

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: N/A — no new infrastructure needed; audit from Phase 1 informs all remediation
- **User Story 1 — Workflow Hardening (Phase 3)**: Depends on T001 audit findings
- **User Story 2 — Secrets Protection (Phase 4)**: Depends on T004 secrets scan findings
- **User Story 3 — Dependency Remediation (Phase 5)**: Depends on T002, T003 dependency audit findings
- **User Story 4 — Auth Hardening (Phase 6)**: Independent — review-based, can start after Phase 1
- **User Story 5 — Input/Data Exposure (Phase 7)**: Independent — T032, T033 are the primary code changes
- **User Story 6 — DRY Consolidation (Phase 8)**: Depends on US5 (T032, T033) being complete since both modify backend/src/api/auth.py
- **User Story 7 — Findings Report (Phase 9)**: Depends on all other user stories — aggregates findings from US1-US6
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after T001 — no dependencies on other stories
- **US2 (P1)**: Can start after T004 — no dependencies on other stories
- **US3 (P1)**: Can start after T002, T003 — no dependencies on other stories
- **US4 (P2)**: Can start after Phase 1 — no dependencies on other stories
- **US5 (P2)**: Can start after Phase 1 — no dependencies on other stories
- **US6 (P3)**: Should start after US5 (shared file: backend/src/api/auth.py)
- **US7 (P3)**: Should start after US1-US6 (aggregates all findings)

### Within Each User Story

- Audit/review tasks before modification tasks
- Modification tasks before verification tasks
- All tasks complete before documenting findings

### Parallel Opportunities

- **Phase 1**: T002, T003, T004 can all run in parallel (different tools, different files)
- **Phase 3 (US1)**: T005-T007 (SHA pinning) can run in parallel with each other; T009-T011 (permissions) can run in parallel
- **Phase 4 (US2)**: T014-T018 can all run in parallel (different files, read-only verification)
- **Phase 5 (US3)**: T020, T021 can run in parallel (different ecosystems)
- **Phase 6 (US4)**: T027-T030 can all run in parallel (different files, read-only review)
- **Phase 7 (US5)**: T034-T037 can run in parallel (different files, read-only review); T032, T033 are sequential (same file)
- **Phase 9 (US7)**: T046-T049 can run in parallel (different report sections)
- **Cross-story**: US1, US2, US3, US4, US5 can all proceed in parallel (different files)

---

## Parallel Example: User Story 1

```bash
# Launch all SHA-pinning tasks together (same file but different action references):
Task T005: "Pin actions/checkout to full SHA in .github/workflows/ci.yml"
Task T006: "Pin actions/setup-python to full SHA in .github/workflows/ci.yml"
Task T007: "Pin actions/setup-node to full SHA in .github/workflows/ci.yml"

# Launch all permission tasks together:
Task T009: "Add permissions to backend job in .github/workflows/ci.yml"
Task T010: "Add permissions to frontend job in .github/workflows/ci.yml"
Task T011: "Add permissions to docker job in .github/workflows/ci.yml"
```

## Parallel Example: User Story 2

```bash
# Launch all verification tasks together (different files, read-only):
Task T014: "Verify .gitignore excludes .env files"
Task T015: "Verify .env.example has only placeholders"
Task T016: "Verify docker-compose.yml uses env var substitution"
Task T017: "Verify backend config uses pydantic-settings"
Task T018: "Verify test fixtures use dummy values"
```

## Parallel Example: Cross-Story

```bash
# After Phase 1, launch P1 stories in parallel:
US1: "Harden GitHub Workflow files" (modifies .github/workflows/ci.yml)
US2: "Verify secrets management" (read-only across repository)
US3: "Remediate dependency vulnerabilities" (modifies pyproject.toml, package.json)

# Also launch P2 stories in parallel with P1:
US4: "Review auth patterns" (read-only in backend/src/)
US5: "Fix error message leakage" (modifies backend/src/api/auth.py)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Audit (T001-T004)
2. Complete Phase 3: User Story 1 — GitHub Workflow Hardening (T005-T013)
3. **STOP and VALIDATE**: Verify all actions are SHA-pinned, permissions are set, CI still passes
4. This alone addresses the highest-impact security improvement (supply-chain attack prevention)

### Incremental Delivery

1. Complete Phase 1 → Audit findings recorded
2. Add US1 (Workflow Hardening) → Validate independently → CI hardened (MVP!)
3. Add US2 (Secrets) + US3 (Dependencies) → Validate independently → Supply chain secured
4. Add US4 (Auth) + US5 (Error Messages) → Validate independently → App-level hardening done
5. Add US6 (DRY) → Validate independently → Code quality improved
6. Add US7 (Report) → Validate independently → Full documentation delivered
7. Complete Phase 10 → Final regression testing
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team reviews Phase 1 audit results together
2. Once audit is complete:
   - Developer A: US1 (Workflow Hardening) + US2 (Secrets)
   - Developer B: US3 (Dependencies) + US4 (Auth Review)
   - Developer C: US5 (Error Messages) → then US6 (DRY Consolidation)
3. All developers contribute findings to Developer D: US7 (Report)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US5 and US6 both modify backend/src/api/auth.py — execute US5 first, then US6
- The security findings report (US7) is an aggregation task — best done last
- Existing tests serve as the regression gate — no new tests required by the spec
