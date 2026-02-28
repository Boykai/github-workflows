# Tasks: Deep Security Review of GitHub Workflows App

**Input**: Design documents from `/specs/012-deep-security-review/`
**Prerequisites**: spec.md (required for user stories)

**Tests**: Not requested in feature specification. Test tasks omitted.

**Organization**: Tasks grouped by user story to enable independent implementation and testing. This is a security audit feature — tasks produce audit findings, code fixes, and a review report rather than new application features.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US7)
- All paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish security audit tooling, baseline documentation structure, and inventory of files to review

- [ ] T001 Create security review report skeleton with sections for scope, methodology, findings, fixes, accepted risks, and recommendations in docs/security-review-report.md
- [ ] T002 [P] Run `npm audit` on frontend dependencies and capture output to identify known vulnerabilities in frontend/package-lock.json
- [ ] T003 [P] Run `pip audit` or equivalent on backend dependencies and capture output to identify known vulnerabilities in backend/pyproject.toml
- [ ] T004 [P] Inventory all GitHub Actions workflow files and third-party action references in .github/workflows/ci.yml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create shared security utilities that ALL user stories depend on for consistent validation, sanitization, and security checks

**⚠ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create shared input validation utility with reusable validators (string length, allowed characters, type enforcement) in backend/src/security/__init__.py and backend/src/security/validation.py
- [ ] T006 [P] Create shared output sanitization utility with HTML encoding and error message sanitization functions in backend/src/security/sanitization.py
- [ ] T007 [P] Create security constants module defining allowed origins patterns, security header values, cookie attribute defaults, and input validation limits in backend/src/security/constants.py

**Checkpoint**: Foundation ready — shared security utilities available for all user stories

---

## Phase 3: User Story 1 — Identify and Remediate Critical Vulnerabilities (Priority: P1) 🎯 MVP

**Goal**: All high and critical severity vulnerabilities across the application are identified, documented, and fixed or accepted with justification

**Independent Test**: Run a full security audit of the codebase and verify that zero high or critical vulnerabilities remain unresolved. Check docs/security-review-report.md for complete finding entries.

### Implementation for User Story 1

- [ ] T008 [US1] Audit backend exception handlers for information leakage — ensure stack traces and internal details are not exposed to clients in backend/src/main.py generic_exception_handler and backend/src/api/ endpoint error responses
- [ ] T009 [P] [US1] Audit dev-login endpoint to ensure it is fully disabled in production (not just hidden) and cannot be accessed via direct URL when DEBUG=false in backend/src/api/auth.py
- [ ] T010 [P] [US1] Review OAuth state validation for timing attacks and CSRF protection in backend/src/services/github_auth.py (validate_state, generate_oauth_url)
- [ ] T011 [P] [US1] Audit session management for session fixation, session ID entropy, and proper expiration enforcement in backend/src/services/session_store.py and backend/src/services/github_auth.py
- [ ] T012 [P] [US1] Review encryption service for proper error handling and ensure passthrough mode logs an actionable warning in production in backend/src/services/encryption.py
- [ ] T013 [US1] Document all findings from T008–T012 with severity ratings, affected components, and remediation status in docs/security-review-report.md

**Checkpoint**: User Story 1 complete — all critical vulnerabilities identified and remediated or documented as accepted risks

---

## Phase 4: User Story 2 — Harden GitHub Actions Workflows (Priority: P1)

**Goal**: All GitHub Actions workflows use pinned action versions, least-privilege permissions, and no script injection risks

**Independent Test**: Audit every workflow YAML file and verify each action reference uses a pinned full-length commit SHA, permissions are scoped minimally, and no user-controlled inputs are interpolated into shell commands.

### Implementation for User Story 2

- [ ] T014 [US2] Pin all third-party action references to full-length commit SHAs (actions/checkout@v4 → actions/checkout@<sha>, actions/setup-python@v5 → actions/setup-python@<sha>, actions/setup-node@v4 → actions/setup-node@<sha>) in .github/workflows/ci.yml
- [ ] T015 [US2] Add explicit least-privilege permissions block to each job (backend: contents:read, frontend: contents:read, docker: contents:read packages:read) in .github/workflows/ci.yml
- [ ] T016 [US2] Audit all `run:` steps in .github/workflows/ci.yml for script injection risks — verify no user-controlled expressions (github.event.*, github.head_ref, etc.) are interpolated into shell commands
- [ ] T017 [US2] Document workflow hardening findings and changes in docs/security-review-report.md

**Checkpoint**: User Story 2 complete — all workflow files follow GitHub Actions security best practices

---

## Phase 5: User Story 3 — Secure Secrets and Credentials Management (Priority: P1)

**Goal**: No secrets or sensitive values are hardcoded anywhere in the codebase; all credentials use secure secret stores

**Independent Test**: Scan the entire repository for patterns resembling secrets (API keys, tokens, passwords, private keys) and verify all sensitive values come from environment variables or secret management systems.

### Implementation for User Story 3

- [ ] T018 [US3] Scan all source files for hardcoded secrets, API keys, tokens, or passwords using pattern matching (grep for common secret patterns: api_key, password, secret, token, private_key with literal string values) across backend/src/, frontend/src/, and root config files
- [ ] T019 [P] [US3] Verify .env.example contains only placeholder values and no real credentials; confirm .env is in .gitignore in .env.example and .gitignore
- [ ] T020 [P] [US3] Audit that sensitive values (access_token, refresh_token, client_secret, encryption_key) are never logged or included in error messages in backend/src/services/github_auth.py, backend/src/services/encryption.py, and backend/src/api/auth.py
- [ ] T021 [P] [US3] Verify git history does not contain committed secrets by checking .gitignore covers .env, *.pem, *.key patterns in .gitignore
- [ ] T022 [US3] Document secrets management findings and changes in docs/security-review-report.md

**Checkpoint**: User Story 3 complete — zero hardcoded secrets in codebase, all credentials use secure stores

---

## Phase 6: User Story 4 — Audit Input Validation and Output Encoding (Priority: P2)

**Goal**: All user inputs are properly validated and all outputs are correctly encoded to prevent injection attacks

**Independent Test**: Review all user-facing input endpoints for validation rules and confirm all dynamic content in UI responses is properly encoded or sanitized.

### Implementation for User Story 4

- [ ] T023 [US4] Audit all API endpoint input parameters for proper validation (type, length, format, allowed characters) in backend/src/api/auth.py, backend/src/api/chat.py, backend/src/api/board.py, backend/src/api/tasks.py, backend/src/api/projects.py, backend/src/api/settings.py, backend/src/api/workflow.py, and backend/src/api/signal.py
- [ ] T024 [P] [US4] Add input validation using shared validation utility (T005) to endpoints that accept free-text user input (chat messages, task descriptions, project names) in backend/src/api/chat.py and backend/src/api/tasks.py
- [ ] T025 [P] [US4] Audit backend for SQL injection risks — verify all database queries use parameterized statements in backend/src/services/database.py and backend/src/services/session_store.py and backend/src/services/settings_store.py
- [ ] T026 [P] [US4] Audit frontend for XSS risks — verify all user-provided content rendered in React components uses safe patterns (no dangerouslySetInnerHTML with unsanitized input) in frontend/src/components/ and frontend/src/pages/
- [ ] T027 [P] [US4] Audit backend for command injection risks — verify no user input is interpolated into shell commands or file paths without sanitization in backend/src/services/
- [ ] T028 [US4] Document input validation and output encoding findings and changes in docs/security-review-report.md

**Checkpoint**: User Story 4 complete — all inputs validated, all outputs encoded, no injection vulnerabilities

---

## Phase 7: User Story 5 — Consolidate Security Logic and Produce Review Report (Priority: P2)

**Goal**: Duplicated security logic is consolidated into shared utilities and a comprehensive security review report is produced

**Independent Test**: Verify that security-related patterns (validation, sanitization, auth checks) use shared utilities and that the security review report covers all audit areas.

### Implementation for User Story 5

- [ ] T029 [US5] Identify duplicated security patterns across backend/src/api/ endpoints (repeated cookie-setting logic, repeated session validation, repeated error sanitization) and refactor to use shared utilities from backend/src/security/
- [ ] T030 [P] [US5] Consolidate duplicated cookie-setting logic (set_cookie calls with httponly, secure, samesite, max_age) into a shared helper function in backend/src/security/cookies.py and update backend/src/api/auth.py to use it
- [ ] T031 [P] [US5] Consolidate repeated authentication check patterns into the existing dependency injection in backend/src/dependencies.py — ensure all protected endpoints use Depends() consistently
- [ ] T032 [US5] Finalize security review report with executive summary, categorized findings (critical/high/medium/low), fixes applied with file references, accepted risks with justification, and ongoing recommendations in docs/security-review-report.md

**Checkpoint**: User Story 5 complete — security logic consolidated, comprehensive report delivered

---

## Phase 8: User Story 6 — Verify Dependency Supply Chain Security (Priority: P2)

**Goal**: All third-party dependencies are audited for known vulnerabilities and supply chain risks

**Independent Test**: Run dependency audit tools on both backend and frontend packages and verify no known high or critical vulnerabilities exist in the resolved dependency tree.

### Implementation for User Story 6

- [ ] T033 [US6] Resolve or document all high and critical vulnerabilities found in frontend npm audit (T002) by upgrading affected packages in frontend/package.json and frontend/package-lock.json
- [ ] T034 [P] [US6] Resolve or document all high and critical vulnerabilities found in backend pip audit (T003) by upgrading affected packages in backend/pyproject.toml
- [ ] T035 [P] [US6] Verify Dependabot or equivalent automated vulnerability scanning is enabled for the repository in .github/dependabot.yml (create if missing)
- [ ] T036 [US6] Re-run dependency audits to confirm all high and critical vulnerabilities are resolved and document final status in docs/security-review-report.md

**Checkpoint**: User Story 6 complete — all dependency vulnerabilities resolved or documented

---

## Phase 9: User Story 7 — Evaluate Transport Security and Security Headers (Priority: P3)

**Goal**: HTTPS enforcement, CORS policies, and security headers are properly configured

**Independent Test**: Inspect the application's HTTP responses for appropriate security headers and verify CORS policies only allow expected origins.

### Implementation for User Story 7

- [ ] T037 [US7] Audit CORS configuration for overly permissive wildcards and verify allowed origins are restricted to trusted domains in backend/src/config.py (cors_origins) and backend/src/main.py (CORSMiddleware)
- [ ] T038 [P] [US7] Add security headers middleware (X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Strict-Transport-Security, Content-Security-Policy, X-XSS-Protection) in backend/src/middleware/security_headers.py and register in backend/src/main.py
- [ ] T039 [P] [US7] Audit cookie attributes — verify session cookies use Secure=True, HttpOnly=True, SameSite=Lax in production and that cookie_secure defaults are safe in backend/src/config.py and backend/src/api/auth.py
- [ ] T040 [P] [US7] Add security headers to frontend nginx configuration for production static file serving in frontend/nginx.conf
- [ ] T041 [US7] Document transport security and headers findings and changes in docs/security-review-report.md

**Checkpoint**: User Story 7 complete — transport security hardened, all security headers in place

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories and documentation updates

- [ ] T042 [P] Update root README.md with security practices section covering how to configure secrets, security headers, and cookie settings
- [ ] T043 [P] Verify .env.example documents all security-related environment variables (ENCRYPTION_KEY, COOKIE_SECURE, GITHUB_WEBHOOK_SECRET, SESSION_SECRET_KEY) with generation instructions in .env.example
- [ ] T044 Run full validation across backend/src/, frontend/src/, and .github/workflows/: re-scan for hardcoded secrets, re-audit dependency vulnerabilities, verify all workflow actions are pinned, confirm security headers are present
- [ ] T045 Final review and sign-off of docs/security-review-report.md — ensure all findings are categorized, all fixes referenced, and all accepted risks justified

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends On | Blocks |
|-------|-----------|--------|
| **Phase 1: Setup** | None — start immediately | Phase 2, all user stories |
| **Phase 2: Foundational** | Phase 1 complete | All user stories |
| **Phase 3: US1 (Vulnerabilities)** | Phase 2 | Phase 10 (report finalization) |
| **Phase 4: US2 (Workflows)** | Phase 1 (T004 inventory) | Phase 10 |
| **Phase 5: US3 (Secrets)** | Phase 1 | Phase 10 |
| **Phase 6: US4 (Input/Output)** | Phase 2 (shared validators) | US5 (consolidation) |
| **Phase 7: US5 (Consolidate)** | US1–US4 findings complete | Phase 10 |
| **Phase 8: US6 (Dependencies)** | Phase 1 (T002, T003 audits) | Phase 10 |
| **Phase 9: US7 (Transport)** | Phase 2 | Phase 10 |
| **Phase 10: Polish** | All user stories complete | None |

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 1 — No dependencies on other stories
- **US3 (P1)**: Can start after Phase 1 — No dependencies on other stories
- **US4 (P2)**: Can start after Phase 2 — Uses shared validation utilities
- **US5 (P2)**: Depends on US1–US4 findings — Consolidates patterns found during audit
- **US6 (P2)**: Can start after Phase 1 audit outputs (T002, T003) — Independent of code audit stories
- **US7 (P3)**: Can start after Phase 2 — No dependencies on other stories

### Within Each User Story

- Audit/scan before remediation
- Remediation before documentation
- Individual findings before report sections
- Backend before frontend (when both are affected)
- Shared utilities before endpoint-specific fixes

### Parallel Opportunities

**Phase 1** — All 4 tasks touch different files/tools:
```
T001 (report skeleton) ‖ T002 (npm audit) ‖ T003 (pip audit) ‖ T004 (workflow inventory)
```

**Phase 2** — All 3 tasks are independent:
```
T005 (validation.py) ‖ T006 (sanitization.py) ‖ T007 (constants.py)
```

**Phase 3 (US1)** — Parallel audit tasks:
```
T008 (exception handlers) → T013 (document)
T009 (dev-login) ────────↗
T010 (OAuth state) ──────↗
T011 (session mgmt) ─────↗
T012 (encryption) ────────↗
```

**P1 stories after Phase 2** — All three can run in parallel:
```
US1 (T008–T013)  ‖  US2 (T014–T017)  ‖  US3 (T018–T022)
```

**P2 stories** — US4, US6, US7 can run in parallel:
```
US4 (T023–T028)  ‖  US6 (T033–T036)  ‖  US7 (T037–T041)
→ then US5 (T029–T032) after US4 completes
```

---

## Parallel Example: User Story 1

```bash
# Launch all audit tasks for User Story 1 together:
Task: "Audit backend exception handlers in backend/src/main.py"
Task: "Audit dev-login endpoint in backend/src/api/auth.py"
Task: "Review OAuth state validation in backend/src/services/github_auth.py"
Task: "Audit session management in backend/src/services/session_store.py"
Task: "Review encryption service in backend/src/services/encryption.py"

# Then document all findings:
Task: "Document all findings in docs/security-review-report.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (4 tasks)
2. Complete Phase 2: Foundational (3 tasks)
3. Complete Phase 3: User Story 1 — Identify and Remediate Critical Vulnerabilities (6 tasks)
4. **STOP AND VALIDATE**: Verify all critical/high vulnerabilities are documented and remediated
5. Deploy/demo if ready — **13 tasks to MVP**

### Incremental Delivery

1. Setup + Foundational → Foundation ready (7 tasks)
2. **Add US1** → Critical vulnerabilities identified and fixed → Validate (**MVP!**)
3. **Add US2** → Workflows hardened with pinned SHAs and least-privilege → Validate
4. **Add US3** → Secrets management verified → Validate
5. **Add US4** → Input validation and output encoding hardened → Validate
6. **Add US5** → Security logic consolidated, report finalized → Validate
7. **Add US6** → Dependencies audited and upgraded → Validate
8. **Add US7** → Transport security and headers hardened → Validate
9. Polish → Final validation and report sign-off → Release
10. Each story adds security hardening without breaking previous work

### Parallel Team Strategy

With multiple developers after Phase 2 completes:
- **Developer A**: US1 (critical vulns) → US5 (consolidation + report)
- **Developer B**: US2 (workflows) → US4 (input validation)
- **Developer C**: US3 (secrets) → US6 (dependencies) → US7 (transport)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [USn] label maps task to user story for traceability
- No test tasks included — tests were not requested in the feature specification
- This is a security audit feature — tasks produce findings, code fixes, and a review report
- OWASP Top 10 (2021) is the reference framework for categorizing vulnerabilities
- docs/security-review-report.md is the central artifact tracking all findings across stories
- Each story adds to the security report; US5 produces the final consolidated version
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
