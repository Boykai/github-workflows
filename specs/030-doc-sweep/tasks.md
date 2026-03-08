# Tasks: Recurring Documentation Update Process

**Input**: Design documents from `/specs/030-doc-sweep/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested. CI-based markdown linting and link checking serve as validation (Test Optionality: PASS per constitution check).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This feature builds on the existing `027-doc-sweep` foundation — most artifacts exist and require verification/gap-filling rather than creation from scratch.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline by auditing existing `027-doc-sweep` artifacts against `030-doc-sweep` requirements (FR-001–FR-020)

- [x] T001 Run full gap analysis of existing documentation artifacts against FR-001–FR-020 requirements table in specs/030-doc-sweep/research.md
- [x] T002 [P] Verify all files referenced in specs/030-doc-sweep/plan.md Project Structure exist in the repository (docs/checklists/, docs/decisions/, docs/OWNERS.md, .github/pull_request_template.md, .markdownlint.json, .markdown-link-check.json)
- [x] T003 [P] Run `markdownlint "docs/**/*.md" "*.md" --config .markdownlint.json` locally and capture any existing lint errors as baseline

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Ensure all shared documentation infrastructure is complete and correct before verifying individual user stories

**⚠️ CRITICAL**: No user story verification can begin until this phase confirms the foundational artifacts are in place

- [x] T004 Verify docs/ directory contains all 10 documentation files listed in data-model.md Current Instances table (docs/setup.md, docs/configuration.md, docs/api-reference.md, docs/architecture.md, docs/agent-pipeline.md, docs/custom-agents-best-practices.md, docs/signal-integration.md, docs/testing.md, docs/troubleshooting.md, docs/project-structure.md)
- [x] T005 [P] Verify docs/checklists/ directory contains all 3 checklist files (weekly-sweep.md, monthly-review.md, quarterly-audit.md)
- [x] T006 [P] Verify docs/decisions/ directory contains README.md with ADR template and existing ADRs (001–006)
- [x] T007 [P] Verify frontend/docs/findings-log.md exists as listed in data-model.md

**Checkpoint**: All foundational documentation artifacts confirmed present — user story verification can begin

---

## Phase 3: User Story 1 — PR Author Completes Documentation Checklist (Priority: P1) 🎯 MVP

**Goal**: Verify the PR template includes a complete documentation checklist that prompts authors to update relevant docs or explicitly state no changes needed (FR-001, FR-002)

**Independent Test**: Open a pull request and confirm the PR description auto-populates with the 6-item documentation checklist and a rationale field for "no doc changes needed"

### Implementation for User Story 1

- [x] T008 [US1] Verify .github/pull_request_template.md contains all 6 documentation checklist items per contracts/pr-template.md: endpoint docs, config docs, setup docs, agent pipeline docs, schema/data model docs, and doc update confirmation
- [x] T009 [US1] Verify .github/pull_request_template.md includes rationale field matching format from contracts/pr-template.md: `**Doc files updated**: <!-- List files or write "None — no doc changes needed" with rationale -->`
- [x] T010 [US1] If any checklist items are missing or the rationale field format differs from the contract, update .github/pull_request_template.md to match the contract specification exactly
- [x] T011 [US1] Verify the PR template Documentation section is positioned after Type of Change and before Testing sections per contracts/pr-template.md Required Sections order

**Checkpoint**: PR template is fully compliant with FR-001 and FR-002. Any PR opened will auto-populate with the documentation checklist.

---

## Phase 4: User Story 2 — Developer Performs Weekly Staleness Sweep (Priority: P1)

**Goal**: Verify the weekly sweep checklist covers API reference validation (FR-004), configuration documentation validation (FR-005), and setup guide validation (FR-006), completable in ~30 minutes (SC-002)

**Independent Test**: Introduce a deliberate discrepancy (e.g., an undocumented route) and walk through the checklist to confirm it catches the issue

### Implementation for User Story 2

- [x] T012 [US2] Verify docs/checklists/weekly-sweep.md contains API Reference Validation section with items: scan backend/src/api/ against docs/api-reference.md, confirm path prefixes/methods/params accuracy, flag removed/deprecated endpoints (FR-004 per contracts/checklists.md)
- [x] T013 [US2] Verify docs/checklists/weekly-sweep.md contains Configuration Documentation Validation section with items: compare env vars against backend/src/config.py, confirm default values and required/optional status (FR-005 per contracts/checklists.md)
- [x] T014 [US2] Verify docs/checklists/weekly-sweep.md contains Setup Guide Validation section with items: confirm Docker Compose steps match project state, confirm prerequisite versions match pyproject.toml and package.json, confirm Codespaces badge works (FR-006 per contracts/checklists.md)
- [x] T015 [US2] If any required checklist items are missing from docs/checklists/weekly-sweep.md, add them following the exact wording from contracts/checklists.md Weekly Sweep Checklist section
- [x] T016 [US2] Verify docs/checklists/weekly-sweep.md uses GitHub-flavored markdown checkbox syntax (`- [ ]`) for all actionable items

**Checkpoint**: Weekly sweep checklist is fully compliant with FR-003–FR-006. A developer on rotation can complete it in ~30 minutes with clear, specific instructions.

---

## Phase 5: User Story 3 — Tech Lead Conducts Monthly Full Documentation Review (Priority: P2)

**Goal**: Verify the monthly review checklist covers accuracy/completeness/consistency audit (FR-007), cross-reference validation (FR-008), code snippet correctness (FR-009), readability standards (FR-010), and troubleshooting format enforcement (FR-020)

**Independent Test**: Walk through the monthly checklist against the current docs/ directory and confirm every verification item is actionable and maps to a specific documentation file

### Implementation for User Story 3

- [x] T017 [US3] Verify docs/checklists/monthly-review.md contains Coverage Audit section with accuracy, completeness, and consistency checklist items for every docs/ file (FR-007 per contracts/checklists.md)
- [x] T018 [P] [US3] Verify docs/checklists/monthly-review.md contains file-by-file verification table listing each doc file, its ownership, and key things to verify (matching docs/OWNERS.md entries per contracts/checklists.md)
- [x] T019 [US3] Verify docs/checklists/monthly-review.md contains Cross-Reference Check section with items: internal link validation (FR-008), code snippet correctness (FR-009), README.md links, external link validity (per contracts/checklists.md)
- [x] T020 [US3] Verify docs/checklists/monthly-review.md contains Readability & Usability section with items: purpose statements, numbered lists for steps, config table format, API table format, and troubleshooting Symptom → Cause → Fix format (FR-010, FR-020 per contracts/checklists.md)
- [x] T021 [US3] If any required sections or items are missing from docs/checklists/monthly-review.md, add them following the exact structure from contracts/checklists.md Monthly Review Checklist section
- [x] T022 [US3] Verify docs/troubleshooting.md entries follow the Symptom → Cause → Fix format (FR-020); if any entries deviate, restructure them to match

**Checkpoint**: Monthly review checklist is fully compliant with FR-007–FR-010 and FR-020. Tech lead can conduct a 2–3 hour review with clear, actionable items covering every docs/ file.

---

## Phase 6: User Story 4 — Tech Lead Performs Quarterly Architecture Audit (Priority: P2)

**Goal**: Verify the quarterly audit checklist covers service topology accuracy (FR-011), ADR completeness with Context → Decision → Consequences format (FR-012), developer experience testing (FR-013), and documentation gaps analysis

**Independent Test**: Walk through the quarterly audit checklist and confirm it covers architecture document verification, ADR review, developer experience testing, and gaps analysis with specific, actionable items

### Implementation for User Story 4

- [x] T023 [US4] Verify docs/checklists/quarterly-audit.md contains Architecture Document Verification section with items: Docker Compose topology match, backend service module coverage, data flow accuracy, AI provider list currency (FR-011 per contracts/checklists.md)
- [x] T024 [US4] Verify docs/checklists/quarterly-audit.md contains Decision Records section with items: ADR completeness for quarter, ADR format follows Context → Decision → Consequences, ADR index in docs/decisions/README.md is current (FR-012 per contracts/checklists.md)
- [x] T025 [US4] Verify docs/checklists/quarterly-audit.md contains Developer Experience Audit section with items: fresh setup walkthrough, end-to-end setup timing, troubleshooting doc update for friction points (FR-013 per contracts/checklists.md)
- [x] T026 [US4] Verify docs/checklists/quarterly-audit.md contains Docs Gaps Analysis section with items: feature-to-doc coverage for quarter, unreferenced docs identification, CHANGELOG.md assessment (per contracts/checklists.md)
- [x] T027 [US4] If any required sections or items are missing from docs/checklists/quarterly-audit.md, add them following the exact structure from contracts/checklists.md Quarterly Audit Checklist section
- [x] T028 [P] [US4] Verify docs/decisions/README.md contains ADR template with Context → Decision → Consequences format and index of existing ADRs (001–006)

**Checkpoint**: Quarterly audit checklist is fully compliant with FR-011–FR-013. Tech lead can conduct a half-day audit with clear items covering architecture accuracy, decision records, DX testing, and gap analysis.

---

## Phase 7: User Story 5 — All Contributors Follow Formatting Standards (Priority: P3)

**Goal**: Verify CI pipeline enforces documentation formatting standards (FR-014, FR-015) and link validation (FR-016) with automated linting on all markdown files

**Independent Test**: Submit a documentation change with a formatting violation (e.g., setext-style heading) and confirm CI rejects it; submit a doc with a broken link and confirm CI catches it

### Implementation for User Story 5

- [x] T029 [US5] Verify .markdownlint.json enforces ATX-style headings (MD003 default), dash-style lists (MD004), and language-specified code blocks (MD040 default) per contracts/ci-config.md Required Rules table
- [x] T030 [US5] Verify .github/workflows/ci.yml docs job runs `markdownlint "docs/**/*.md" "*.md" --config .markdownlint.json` matching the scope in contracts/ci-config.md Step 1 (FR-015)
- [x] T031 [US5] Verify .github/workflows/ci.yml docs job runs `markdown-link-check` on all docs/**/*.md files and README.md matching contracts/ci-config.md Step 2 (FR-016)
- [x] T032 [P] [US5] Verify .markdown-link-check.json includes retry config for 429 status, timeout handling, and ignore patterns for Codespaces/localhost URLs per contracts/ci-config.md
- [x] T033 [P] [US5] Verify .pre-commit-config.yaml includes markdownlint hook targeting `docs/**/*.md` and root-level `*.md` files with `--config .markdownlint.json` per contracts/ci-config.md
- [x] T034 [US5] If any CI configuration gaps are found, update the relevant config file (.markdownlint.json, .github/workflows/ci.yml, .pre-commit-config.yaml) to match contracts/ci-config.md exactly

**Checkpoint**: CI pipeline fully enforces formatting standards (FR-014–FR-016). All markdown violations and broken links are caught before merge (SC-006, SC-007).

---

## Phase 8: User Story 6 — Documentation Ownership Is Clearly Assigned (Priority: P3)

**Goal**: Verify every documentation file has a designated owner in docs/OWNERS.md (FR-017, FR-018) and a review cadence schedule is defined (FR-019)

**Independent Test**: Cross-reference docs/OWNERS.md against the actual docs/ directory listing and confirm every file has exactly one owner; verify the review cadence table covers all 4 cadence types

### Implementation for User Story 6

- [x] T035 [US6] Verify docs/OWNERS.md contains ownership entries for all 15 files listed in data-model.md Current Instances table (FR-017) — cross-reference actual docs/ directory listing
- [x] T036 [US6] Verify each file in docs/OWNERS.md has exactly one designated owner or an explicitly marked rotation scheme (FR-018) — confirm troubleshooting.md and weekly-sweep.md show rotating ownership
- [x] T037 [US6] Verify docs/OWNERS.md contains Review Cadence table with entries for Every PR, Weekly, Monthly, and Quarterly review types including scope and responsible role (FR-019)
- [x] T038 [US6] If any documentation files exist in docs/ that are not listed in docs/OWNERS.md, add ownership entries for them following the format in data-model.md
- [x] T039 [US6] If any new documentation files were added by this feature, add corresponding ownership entries to docs/OWNERS.md

**Checkpoint**: Documentation ownership is fully compliant with FR-017–FR-019. Every documentation file has a clear owner and the review cadence is defined (SC-005).

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories, cross-reference checks, and quickstart verification

- [x] T040 [P] Run `markdownlint "docs/**/*.md" "*.md" --config .markdownlint.json` to confirm all documentation passes formatting standards
- [x] T041 [P] Run `find docs -name "*.md" -print0 | xargs -0 -I {} markdown-link-check {} --config .markdown-link-check.json --quiet` to confirm all links resolve
- [x] T042 Verify all internal cross-references between docs/ files are valid (README.md links to docs/, docs/ files link to each other)
- [x] T043 Walk through specs/030-doc-sweep/quickstart.md Quick Verification steps (sections 1–4) and confirm each passes
- [x] T044 Validate FR-001–FR-020 requirements traceability: confirm each functional requirement maps to at least one completed task
- [x] T045 Validate SC-001–SC-010 success criteria: confirm each measurable outcome is achievable with the delivered artifacts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — confirms all base artifacts exist
- **User Stories (Phases 3–8)**: All depend on Foundational phase completion
  - US1 (Phase 3) and US2 (Phase 4) are P1 — implement first
  - US3 (Phase 5) and US4 (Phase 6) are P2 — implement after P1 stories
  - US5 (Phase 7) and US6 (Phase 8) are P3 — implement after P2 stories
  - User stories can proceed in parallel within the same priority level
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. Only touches .github/pull_request_template.md
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. Only touches docs/checklists/weekly-sweep.md
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Independent of US1/US2 but benefits from US2 weekly sweep being validated first. Touches docs/checklists/monthly-review.md and docs/troubleshooting.md
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Independent of US1–US3. Touches docs/checklists/quarterly-audit.md and docs/decisions/README.md
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) — Independent but CI config validation benefits from all docs being finalized. Touches .markdownlint.json, .github/workflows/ci.yml, .pre-commit-config.yaml
- **User Story 6 (P3)**: Can start after Foundational (Phase 2) — Should be last to capture any new files added by other stories. Touches docs/OWNERS.md

### Within Each User Story

- Verify existing content first (read-only assessment)
- Identify gaps against contracts/
- Apply fixes for any gaps found
- Confirm compliance with relevant FRs

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003)
- All Foundational tasks marked [P] can run in parallel (T005, T006, T007)
- US1 and US2 are fully independent and can run in parallel (different files)
- US3 and US4 are fully independent and can run in parallel (different files)
- US5 and US6 are mostly independent and can run in parallel (different files)
- Within each story, tasks marked [P] can run in parallel
- Polish tasks T040 and T041 can run in parallel

---

## Parallel Example: User Story 1 + User Story 2

```bash
# These two P1 stories operate on completely different files and can run in parallel:

# Developer A: User Story 1 (PR Template)
Task: "Verify .github/pull_request_template.md contains all 6 documentation checklist items"
Task: "Verify rationale field format"
Task: "Fix any gaps"

# Developer B: User Story 2 (Weekly Sweep)
Task: "Verify docs/checklists/weekly-sweep.md API Reference section"
Task: "Verify Configuration Documentation section"
Task: "Verify Setup Guide section"
Task: "Fix any gaps"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup — audit existing artifacts
2. Complete Phase 2: Foundational — confirm all base files exist
3. Complete Phase 3: User Story 1 — PR template verified/updated
4. Complete Phase 4: User Story 2 — Weekly sweep checklist verified/updated
5. **STOP and VALIDATE**: Both P1 stories independently verified
6. Run CI to confirm lint and link checks pass

### Incremental Delivery

1. Setup + Foundational → Base artifacts confirmed ✓
2. US1 + US2 (P1) → PR checks and weekly sweeps operational → Validate (MVP!)
3. US3 + US4 (P2) → Monthly reviews and quarterly audits operational → Validate
4. US5 + US6 (P3) → CI enforcement and ownership finalized → Validate
5. Polish → Full cross-cutting validation → Feature complete

### Parallel Team Strategy

With multiple developers:

1. Team confirms Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (PR template) + US5 (CI formatting) — both touch CI/template files
   - Developer B: US2 (Weekly sweep) + US3 (Monthly review) — both touch checklists
   - Developer C: US4 (Quarterly audit) + US6 (Ownership) — both touch review processes
3. Stories complete and integrate independently — no file conflicts between parallel tracks

---

## Notes

- This feature is process/documentation-oriented — no application code changes
- Most artifacts already exist from `027-doc-sweep` — focus is verification and gap-filling
- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story touches distinct files, enabling safe parallel execution
- CI lint and link checks serve as the automated validation mechanism (no additional tests)
- Contracts in specs/030-doc-sweep/contracts/ define the authoritative specification for each artifact
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
