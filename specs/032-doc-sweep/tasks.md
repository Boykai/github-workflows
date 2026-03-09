# Tasks: Recurring Documentation Update Process

**Input**: Design documents from `/specs/032-doc-sweep/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested. CI-based markdown linting and link checking serve as validation (Test Optionality: PASS per constitution check). No TDD approach needed.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This is the third iteration of the documentation sweep feature (succeeding `027-doc-sweep` and `030-doc-sweep`). Most artifacts already exist and have been validated; the primary new work is formalizing the FR-021 "good documentation" definition and performing completeness verification against all 21 functional requirements.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline by auditing existing `027-doc-sweep` and `030-doc-sweep` artifacts against `032-doc-sweep` requirements (FR-001–FR-021)

- [x] T001 Run full gap analysis of existing documentation artifacts against FR-001–FR-021 requirements table in specs/032-doc-sweep/research.md, confirming FR-001–FR-020 are implemented and FR-021 is the only gap
- [x] T002 [P] Verify all files referenced in specs/032-doc-sweep/plan.md Project Structure section exist in the repository: docs/checklists/, docs/decisions/, docs/OWNERS.md, .github/pull_request_template.md, .markdownlint.json, .markdown-link-check.json, .pre-commit-config.yaml
- [x] T003 [P] Run `markdownlint "docs/**/*.md" "*.md" --config .markdownlint.json` locally and confirm zero lint errors as baseline

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Ensure all shared documentation infrastructure is present and structurally correct before verifying individual user stories

**⚠️ CRITICAL**: No user story verification can begin until this phase confirms the foundational artifacts are in place

- [x] T004 Verify docs/ directory contains all 10 documentation files listed in specs/032-doc-sweep/data-model.md Current Instances table: docs/setup.md, docs/configuration.md, docs/api-reference.md, docs/architecture.md, docs/agent-pipeline.md, docs/custom-agents-best-practices.md, docs/signal-integration.md, docs/testing.md, docs/troubleshooting.md, docs/project-structure.md
- [x] T005 [P] Verify docs/checklists/ directory contains all 3 checklist files: weekly-sweep.md, monthly-review.md, quarterly-audit.md
- [x] T006 [P] Verify docs/decisions/ directory contains README.md with ADR template and existing ADRs (001–006)
- [x] T007 [P] Verify frontend/docs/findings-log.md exists as listed in specs/032-doc-sweep/data-model.md Current Instances table

**Checkpoint**: All foundational documentation artifacts confirmed present — user story verification can begin

---

## Phase 3: User Story 1 — PR Author Completes Documentation Checklist (Priority: P1) 🎯 MVP

**Goal**: Verify the PR template includes a complete documentation checklist that prompts authors to update relevant docs or explicitly state no changes needed (FR-001, FR-002)

**Independent Test**: Open a pull request and confirm the PR description auto-populates with the 6-item documentation checklist and a rationale field for "no doc changes needed"

### Implementation for User Story 1

- [x] T008 [US1] Verify .github/pull_request_template.md contains all 6 documentation checklist items per specs/032-doc-sweep/contracts/pr-template.md: endpoint docs, config docs, setup docs, agent pipeline docs, schema/data model docs, and doc update confirmation
- [x] T009 [US1] Verify .github/pull_request_template.md includes rationale field matching format from specs/032-doc-sweep/contracts/pr-template.md: `**Doc files updated**: <!-- List files or write "None — no doc changes needed" with rationale -->`
- [x] T010 [US1] If any checklist items are missing or the rationale field format differs from the contract, update .github/pull_request_template.md to match the contract specification exactly
- [x] T011 [P] [US1] Verify the PR template Documentation section is positioned after Type of Change and before Testing sections per specs/032-doc-sweep/contracts/pr-template.md Required Sections order

**Checkpoint**: PR template is fully compliant with FR-001 and FR-002. Any PR opened will auto-populate with the documentation checklist (SC-001).

---

## Phase 4: User Story 2 — Developer Performs Weekly Staleness Sweep (Priority: P1)

**Goal**: Verify the weekly sweep checklist covers API reference validation (FR-004), configuration documentation validation (FR-005), and setup guide validation (FR-006), completable in ~30 minutes (SC-002)

**Independent Test**: Introduce a deliberate discrepancy (e.g., an undocumented route) and walk through the checklist to confirm it catches the issue

### Implementation for User Story 2

- [x] T012 [US2] Verify docs/checklists/weekly-sweep.md contains API Reference Validation section with items: scan backend/src/api/ against docs/api-reference.md, confirm path prefixes/methods/params accuracy, flag removed/deprecated endpoints (FR-004 per specs/032-doc-sweep/contracts/checklists.md)
- [x] T013 [US2] Verify docs/checklists/weekly-sweep.md contains Configuration Documentation Validation section with items: compare env vars against backend/src/config.py, confirm default values and required/optional status (FR-005 per specs/032-doc-sweep/contracts/checklists.md)
- [x] T014 [US2] Verify docs/checklists/weekly-sweep.md contains Setup Guide Validation section with items: confirm Docker Compose steps match project state, confirm prerequisite versions match pyproject.toml and package.json, confirm Codespaces badge works (FR-006 per specs/032-doc-sweep/contracts/checklists.md)
- [x] T015 [US2] If any required checklist items are missing from docs/checklists/weekly-sweep.md, add them following the exact wording from specs/032-doc-sweep/contracts/checklists.md Weekly Sweep Checklist section
- [x] T016 [P] [US2] Verify docs/checklists/weekly-sweep.md uses GitHub-flavored markdown checkbox syntax (`- [ ]`) for all actionable items and passes markdownlint

**Checkpoint**: Weekly sweep checklist is fully compliant with FR-003–FR-006. A developer on rotation can complete it in ~30 minutes with clear, specific instructions (SC-002).

---

## Phase 5: User Story 3 — Tech Lead Conducts Monthly Full Documentation Review (Priority: P2)

**Goal**: Verify the monthly review checklist covers accuracy/completeness/consistency audit (FR-007), cross-reference validation (FR-008), code snippet correctness (FR-009), readability standards (FR-010), troubleshooting format enforcement (FR-020), and the "good documentation" acceptance bar (FR-021)

**Independent Test**: Walk through the monthly checklist against the current docs/ directory and confirm every verification item is actionable and maps to a specific documentation file

### Implementation for User Story 3

- [x] T017 [US3] Verify docs/checklists/monthly-review.md contains Coverage Audit section with accuracy, completeness, and consistency checkboxes per specs/032-doc-sweep/contracts/checklists.md (FR-007)
- [x] T018 [P] [US3] Verify docs/checklists/monthly-review.md contains file-by-file verification table covering all documentation areas from specs/032-doc-sweep/data-model.md (12 rows — individual checklist files and the decisions directory are grouped) with ownership and key verification items
- [x] T019 [US3] Verify docs/checklists/monthly-review.md contains Cross-Reference Check section with items: internal links validity, code snippet correctness, README links, external links (FR-008, FR-009 per specs/032-doc-sweep/contracts/checklists.md)
- [x] T020 [US3] Verify docs/checklists/monthly-review.md contains Readability & Usability section with items: purpose statements, numbered lists, configuration table format, API table format, troubleshooting Symptom → Cause → Fix format (FR-010, FR-020 per specs/032-doc-sweep/contracts/checklists.md)
- [x] T021 [US3] Verify docs/checklists/monthly-review.md contains Good Documentation Acceptance Bar section referencing the five criteria from FR-021: accurate, minimal, actionable, discoverable, maintained — add if missing
- [x] T022 [US3] If the FR-021 acceptance bar is missing from docs/checklists/monthly-review.md, add a checkbox item: `- [ ] All reviewed files meet the "good documentation" definition (see docs/OWNERS.md): accurate, minimal, actionable, discoverable, maintained`

**Checkpoint**: Monthly review checklist is fully compliant with FR-007–FR-010, FR-020, and FR-021. The tech lead can complete it in 2–3 hours with all verification items explicitly stated (SC-003).

---

## Phase 6: User Story 4 — Tech Lead Performs Quarterly Architecture Audit (Priority: P2)

**Goal**: Verify the quarterly audit checklist covers service topology accuracy (FR-011), ADR completeness with Context → Decision → Consequences format (FR-012), developer experience testing (FR-013), and docs gaps analysis

**Independent Test**: Walk through the quarterly audit checklist and confirm each section is actionable with clear instructions for verifying architecture docs, decision records, DX testing, and gap analysis

### Implementation for User Story 4

- [x] T023 [US4] Verify docs/checklists/quarterly-audit.md contains Architecture Document Verification section with items: service diagram topology, backend service modules, data flow accuracy, AI provider list (FR-011 per specs/032-doc-sweep/contracts/checklists.md)
- [x] T024 [US4] Verify docs/checklists/quarterly-audit.md contains Decision Records section with items: ADR completeness, Context → Decision → Consequences format, ADR index in docs/decisions/README.md (FR-012 per specs/032-doc-sweep/contracts/checklists.md)
- [x] T025 [US4] Verify docs/checklists/quarterly-audit.md contains Developer Experience Audit section with items: fresh setup walkthrough, time-to-setup measurement, troubleshooting additions (FR-013 per specs/032-doc-sweep/contracts/checklists.md)
- [x] T026 [P] [US4] Verify docs/checklists/quarterly-audit.md contains Docs Gaps Analysis section with items: quarter feature-to-doc mapping, unused docs identification, CHANGELOG.md assessment
- [x] T027 [US4] If any required sections or items are missing from docs/checklists/quarterly-audit.md, add them following the exact wording from specs/032-doc-sweep/contracts/checklists.md Quarterly Audit Checklist section

**Checkpoint**: Quarterly audit checklist is fully compliant with FR-011–FR-013. The tech lead can complete it in ~half a day with structured sections for architecture verification, decision records, DX testing, and gap analysis (SC-004).

---

## Phase 7: User Story 5 — Formatting Standards and Automated Enforcement (Priority: P3)

**Goal**: Verify CI-enforced formatting standards are in place via markdownlint (FR-014, FR-015) and markdown-link-check (FR-016), ensuring all documentation contributions are automatically validated before merge

**Independent Test**: Submit a documentation change that violates formatting standards (e.g., setext-style headings or unspecified code blocks) and confirm the CI pipeline rejects it with clear error messages (SC-006, SC-007)

### Implementation for User Story 5

- [x] T028 [US5] Verify .markdownlint.json enforces required formatting rules per specs/032-doc-sweep/contracts/ci-config.md: ATX headings (MD003 via default), dash lists (MD004), code block language tags (MD040 via default), with appropriate exceptions (MD013 false, MD033 false, MD041 false)
- [x] T029 [P] [US5] Verify .github/workflows/ci.yml contains a docs job that runs markdownlint on `docs/**/*.md` and `*.md` with --config .markdownlint.json (FR-015 per specs/032-doc-sweep/contracts/ci-config.md)
- [x] T030 [P] [US5] Verify .github/workflows/ci.yml docs job runs markdown-link-check on all docs/**/*.md files and README.md with --config .markdown-link-check.json (FR-016 per specs/032-doc-sweep/contracts/ci-config.md)
- [x] T031 [P] [US5] Verify .markdown-link-check.json includes retry configuration for rate limiting (429), timeout settings, ignore patterns for Codespaces/localhost URLs, and accepts 200/206 status codes per specs/032-doc-sweep/contracts/ci-config.md
- [x] T032 [P] [US5] Verify .pre-commit-config.yaml includes markdownlint hook matching CI scope: files pattern `(^docs/.*\.md$|^[^/]*\.md$)` with --config .markdownlint.json per specs/032-doc-sweep/contracts/ci-config.md

**Checkpoint**: CI enforcement is fully compliant with FR-014–FR-016. Formatting violations are caught before merge (SC-006) and broken links are detected automatically (SC-007).

---

## Phase 8: User Story 6 — Documentation Ownership Is Clearly Assigned (Priority: P3)

**Goal**: Verify docs/OWNERS.md maps every documentation file to a designated owner (FR-017, FR-018), includes a review cadence schedule (FR-019), and formalizes the "good documentation" definition as the acceptance bar for all review phases (FR-021)

**Independent Test**: Confirm that every file in docs/ has a corresponding entry in docs/OWNERS.md, that each entry has exactly one owner or a rotation scheme, that the cadence table is complete, and that the "good documentation" definition is present

### Implementation for User Story 6

- [x] T033 [US6] Verify docs/OWNERS.md contains ownership entries for all 15 documentation files listed in specs/032-doc-sweep/data-model.md Current Instances table with file path, owner role, and key verification items (FR-017, FR-018)
- [x] T034 [US6] Verify docs/OWNERS.md includes Review Cadence table with entries for every-PR, weekly, monthly, and quarterly review types with scope and responsible role (FR-019)
- [x] T035 [US6] Verify docs/OWNERS.md explicitly marks rotating ownership for docs/troubleshooting.md and docs/checklists/weekly-sweep.md (FR-018 rotation indicator per specs/032-doc-sweep/data-model.md)
- [x] T036 [US6] Add "Definition of Good Documentation" section to docs/OWNERS.md with the five criteria from FR-021: accurate, minimal, actionable, discoverable, maintained — per specs/032-doc-sweep/research.md R2 decision
- [x] T037 [US6] Verify the "Definition of Good Documentation" section in docs/OWNERS.md matches the exact wording from specs/032-doc-sweep/spec.md FR-021: (1) Accurate — every step, command, variable, and path matches the current codebase; (2) Minimal — no redundant content, each fact appears in exactly one place; (3) Actionable — readers can accomplish the documented task without reading source code; (4) Discoverable — the correct doc is easy to find from the README or table of contents; (5) Maintained — last-reviewed date is within the current quarter

**Checkpoint**: Documentation ownership is fully compliant with FR-017–FR-019 and FR-021. Every doc file has a named owner, the cadence is documented, and the "good documentation" definition is formalized as the acceptance bar (SC-005).

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories, CI compliance verification, and quickstart guide validation

- [x] T038 [P] Run `markdownlint "docs/**/*.md" "*.md" --config .markdownlint.json` and confirm zero lint errors after all changes
- [x] T039 [P] Run `find docs -name "*.md" -print0 | xargs -0 -I {} markdown-link-check {} --config .markdown-link-check.json --quiet` and confirm zero broken links after all changes
- [x] T040 [P] Run `markdown-link-check README.md --config .markdown-link-check.json --quiet` and confirm README links are valid
- [x] T041 Verify all internal cross-references between docs/OWNERS.md, docs/checklists/*.md, and docs/decisions/README.md resolve correctly
- [x] T042 Walk through specs/032-doc-sweep/quickstart.md verification steps to confirm all deliverables are accessible and functional
- [x] T043 Perform final FR-001–FR-021 traceability check: confirm every functional requirement maps to at least one verified artifact per specs/032-doc-sweep/research.md R1 gap analysis table

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–8)**: All depend on Foundational phase completion
  - US1 (Phase 3) and US2 (Phase 4) are P1 priority — implement first
  - US3 (Phase 5) and US4 (Phase 6) are P2 priority — implement after P1 stories
  - US5 (Phase 7) and US6 (Phase 8) are P3 priority — implement after P2 stories
  - US6 (Phase 8, T036) creates the FR-021 definition; US3 (Phase 5, T021–T022) references it — US6/T036 should complete before US3/T021
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US3 (P2)**: Can start after Foundational (Phase 2) — T021–T022 depend on US6/T036 (FR-021 definition must exist before referencing it)
- **US4 (P2)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US5 (P3)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US6 (P3)**: Can start after Foundational (Phase 2) — T036 should be completed early since US3 references it

### Within Each User Story

- Verification tasks before modification tasks (verify → identify gaps → fix gaps)
- Each story can be completed and validated independently
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003)
- All Foundational tasks marked [P] can run in parallel (T005, T006, T007)
- Once Foundational phase completes, US1 and US2 (both P1) can start in parallel
- US3 and US4 (both P2) can run in parallel, except T021–T022 depends on T036
- US5 and US6 (both P3) can run in parallel, except US6/T036 should complete before US3/T021
- Within US5: T029, T030, T031, T032 are all [P] (different files)
- Within each phase: All tasks marked [P] can run in parallel

---

## Parallel Example: User Story 5

```text
# Launch all verification tasks for User Story 5 together:
Task: T028 — Verify .markdownlint.json formatting rules
Task: T029 — Verify ci.yml markdownlint step
Task: T030 — Verify ci.yml markdown-link-check step
Task: T031 — Verify .markdown-link-check.json configuration
Task: T032 — Verify .pre-commit-config.yaml markdownlint hook
```

## Parallel Example: User Story 1 + User Story 2

```text
# P1 stories can run in parallel after Foundational phase:
Developer A: T008–T011 (US1: PR template verification)
Developer B: T012–T016 (US2: Weekly sweep verification)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (gap analysis and baseline)
2. Complete Phase 2: Foundational (all docs present)
3. Complete Phase 3: User Story 1 (PR template compliance)
4. **STOP and VALIDATE**: Open a test PR and verify the documentation checklist appears correctly
5. Deploy if ready — PR-level checks are the earliest and most cost-effective documentation gate

### Incremental Delivery

1. Complete Setup + Foundational → Foundation verified
2. Add US1 (PR template) + US2 (weekly sweep) → P1 stories complete → Core documentation cadence operational
3. Add US3 (monthly review) + US4 (quarterly audit) → P2 stories complete → Full review cadence established
4. Add US5 (formatting standards) + US6 (ownership + FR-021) → P3 stories complete → Governance formalized
5. Complete Polish → All 21 functional requirements verified end-to-end
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (PR template) + US3 (monthly review)
   - Developer B: US2 (weekly sweep) + US4 (quarterly audit)
   - Developer C: US5 (formatting) + US6 (ownership)
3. Note: Developer C should complete T036 (FR-021 definition) before Developer A reaches T021–T022 (FR-021 reference in monthly checklist)
4. All developers join for Phase 9 Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- This feature is process/documentation-oriented — no application code changes
- Most artifacts exist from 027-doc-sweep and 030-doc-sweep; primary new work is FR-021 (T036, T037) and completeness verification
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- CI checks (markdownlint, markdown-link-check) serve as automated tests for documentation quality
