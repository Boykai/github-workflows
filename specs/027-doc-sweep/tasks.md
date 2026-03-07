# Tasks: Recurring Documentation Update Process

**Input**: Design documents from `/specs/027-doc-sweep/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested — this feature is process/documentation-oriented. CI markdown linting and link checking serve as the validation mechanism (already configured).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Repository root**: `.github/`, `docs/`, `.markdownlint.json`, `.markdown-link-check.json`
- **CI workflows**: `.github/workflows/ci.yml`
- **Documentation**: `docs/` (existing files), `docs/checklists/` (new directory)
- **Spec artifacts**: `specs/027-doc-sweep/` (reference only — not modified by implementation tasks)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the directory structure and foundational files needed by all user stories

- [x] T001 Create `docs/checklists/` directory for review checklist files
- [x] T002 [P] Verify existing `docs/OWNERS.md` is accessible and follows the expected ownership mapping format
- [x] T003 [P] Verify existing `docs/decisions/` directory contains the ADR template (`docs/decisions/README.md`) and existing ADRs (001–006)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No blocking foundational tasks — this feature's deliverables are independent markdown files and a minor CI config change. All user stories can begin immediately after Setup.

**⚠️ NOTE**: Unlike application features, this process-oriented feature has no shared infrastructure that blocks user stories. Each story produces independent markdown artifacts. The only dependency is the `docs/checklists/` directory created in Phase 1 (needed by US2, US3, US4).

**Checkpoint**: Setup complete — user story implementation can begin in parallel

---

## Phase 3: User Story 1 — PR Author Verifies Documentation Before Merge (Priority: P1) 🎯 MVP

**Goal**: Create a GitHub PR template with a documentation checklist so every new PR includes documentation verification prompts for the author and reviewer.

**Independent Test**: Create a new pull request in the repository and confirm the PR description is auto-populated with the documentation checklist section, including all 6 required checklist items and the "Doc files updated" field.

### Implementation for User Story 1

- [x] T004 [US1] Create PR template at `.github/pull_request_template.md` with Description, Type of Change, Documentation checklist (6 items per FR-001), and Testing sections — per contract `specs/027-doc-sweep/contracts/pr-template.md`
- [x] T005 [US1] Validate PR template uses GitHub-flavored markdown checkbox syntax (`- [ ]`) and includes the "Doc files updated" free-text field for FR-002 reviewer visibility

**Checkpoint**: User Story 1 complete — new PRs will auto-populate with the documentation checklist

---

## Phase 4: User Story 2 — Weekly Staleness Sweep Catches Documentation Drift (Priority: P1)

**Goal**: Create a structured weekly sweep checklist that a rotating developer can complete in ~30 minutes to identify documentation-to-code discrepancies in the API reference, configuration, and setup guides.

**Independent Test**: Open `docs/checklists/weekly-sweep.md`, walk through each section against the current codebase, and confirm the checklist is completable within 30 minutes and covers API reference, configuration, and setup guide accuracy.

### Implementation for User Story 2

- [x] T006 [US2] Create weekly sweep checklist at `docs/checklists/weekly-sweep.md` with header (~30 min estimate), API Reference check, Configuration check, Setup Guide check, and Completion Record sections — per contract `specs/027-doc-sweep/contracts/checklists.md`
- [x] T007 [US2] Validate weekly sweep checklist uses ATX-style headings (FR-014), inline code formatting for filenames (FR-015), and GitHub-flavored checkbox syntax

**Checkpoint**: User Story 2 complete — weekly staleness sweep checklist is ready for use by the dev rotation

---

## Phase 5: User Story 3 — Monthly Full Review Ensures Coverage and Consistency (Priority: P2)

**Goal**: Create a comprehensive monthly review checklist covering accuracy, completeness, consistency, cross-references, and readability for the tech lead to use during sprint planning.

**Independent Test**: Open `docs/checklists/monthly-review.md`, confirm it includes the coverage audit table (per-file verification), cross-reference check items, readability assessment items, and a completion record. Verify the checklist is structured to be completable in 2–3 hours.

### Implementation for User Story 3

- [x] T008 [US3] Create monthly review checklist at `docs/checklists/monthly-review.md` with header (2–3 hours estimate), Coverage Audit with per-file verification table (FR-005), Cross-Reference Check (FR-006), Readability Assessment (FR-007), and Completion Record sections — per contract `specs/027-doc-sweep/contracts/checklists.md`
- [x] T009 [US3] Validate monthly review checklist includes all 11 documentation files from plan.md project structure (`docs/setup.md`, `docs/configuration.md`, `docs/api-reference.md`, `docs/architecture.md`, `docs/agent-pipeline.md`, `docs/custom-agents-best-practices.md`, `docs/signal-integration.md`, `docs/testing.md`, `docs/troubleshooting.md`, `docs/project-structure.md`, `frontend/docs/`)

**Checkpoint**: User Story 3 complete — monthly full documentation review checklist is ready for use by the tech lead

---

## Phase 6: User Story 4 — Quarterly Architecture Audit After Major Milestones (Priority: P2)

**Goal**: Create a quarterly audit checklist covering architecture document review, ADR completeness, developer experience audit, and documentation gaps analysis for the tech lead to conduct after major milestones.

**Independent Test**: Open `docs/checklists/quarterly-audit.md`, confirm it includes architecture document review items, ADR check items (Context-Decision-Consequences format per FR-009), developer experience audit items (setup from scratch), documentation gaps analysis items, and a completion record.

### Implementation for User Story 4

- [x] T010 [US4] Create quarterly audit checklist at `docs/checklists/quarterly-audit.md` with header (~half day estimate), Architecture Document Review (FR-008), Architecture Decision Records (FR-009), Developer Experience Audit, Documentation Gaps Analysis, and Completion Record sections — per contract `specs/027-doc-sweep/contracts/checklists.md`
- [x] T011 [US4] Validate quarterly audit checklist references existing `docs/decisions/` directory and its README.md template

**Checkpoint**: User Story 4 complete — quarterly architecture audit checklist is ready for use

---

## Phase 7: User Story 5 — Automated Formatting and Link Validation (Priority: P2)

**Goal**: Expand the CI pipeline's markdown linting scope to cover all `*.md` files at the repository root (beyond just `README.md`), ensuring automated formatting and link validation catches issues before merge.

**Independent Test**: Run `markdownlint "docs/**/*.md" "*.md" --config .markdownlint.json` locally and confirm it lints both `docs/` files and root-level `*.md` files. Submit a PR with an intentional markdown formatting violation and confirm the CI check fails with a clear error message.

### Implementation for User Story 5

- [x] T012 [US5] Update the markdownlint command in `.github/workflows/ci.yml` to expand the glob from `"docs/**/*.md" "README.md"` to `"docs/**/*.md" "*.md"` — per contract `specs/027-doc-sweep/contracts/ci-config.md`
- [x] T013 [US5] Verify the link-check step in `.github/workflows/ci.yml` covers `README.md` in addition to `docs/**/*.md` files — per contract `specs/027-doc-sweep/contracts/ci-config.md`
- [x] T014 [US5] Validate that the existing `.markdownlint.json` configuration does not need changes (confirm `MD013: false`, `MD033: false`, `MD041: false` are appropriate per ci-config contract)
- [x] T015 [US5] Validate that the existing `.markdown-link-check.json` configuration handles transient failures correctly (`retryOn429`, `retryCount`, `timeout` settings) per spec edge case on temporary link unreachability

**Checkpoint**: User Story 5 complete — CI pipeline validates markdown formatting and links across all documentation and root-level `*.md` files

---

## Phase 8: User Story 6 — Documentation Ownership Is Clear and Discoverable (Priority: P3)

**Goal**: Update the existing `docs/OWNERS.md` to include entries for the newly created `docs/checklists/` files, ensuring every documentation file has a designated owner role.

**Independent Test**: Open `docs/OWNERS.md` and confirm every file in the `docs/` directory (including the new `docs/checklists/` files) has a corresponding ownership entry mapping to a responsible role.

### Implementation for User Story 6

- [x] T016 [US6] Update `docs/OWNERS.md` to add ownership entries for new files: `docs/checklists/weekly-sweep.md`, `docs/checklists/monthly-review.md`, `docs/checklists/quarterly-audit.md` — assign to appropriate roles per data-model.md ownership mapping
- [x] T017 [US6] Validate that every file in `docs/` (including subdirectories) has a corresponding entry in `docs/OWNERS.md` per FR-013

**Checkpoint**: User Story 6 complete — all documentation files have designated owners

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories to ensure consistency and completeness

- [x] T018 [P] Validate all new markdown files pass `markdownlint` locally: run `markdownlint "docs/checklists/*.md" ".github/pull_request_template.md" --config .markdownlint.json`
- [x] T019 [P] Validate all internal links in new checklist files resolve correctly: run `markdown-link-check` on each new file
- [x] T020 Verify all new files use ATX-style headings, language-tagged code blocks, tables for structured data, numbered lists for sequential steps, and bullet lists for non-ordered items (FR-014, FR-015)
- [x] T021 Run `specs/027-doc-sweep/quickstart.md` verification steps end-to-end to confirm all deliverables are in place

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — but no blocking tasks for this feature
- **User Story 1 (Phase 3)**: Can start immediately — no dependency on `docs/checklists/` directory
- **User Story 2 (Phase 4)**: Depends on Phase 1 (T001 creates `docs/checklists/` directory)
- **User Story 3 (Phase 5)**: Depends on Phase 1 (T001 creates `docs/checklists/` directory)
- **User Story 4 (Phase 6)**: Depends on Phase 1 (T001 creates `docs/checklists/` directory)
- **User Story 5 (Phase 7)**: Can start immediately — modifies existing CI config, no dependency on new directories
- **User Story 6 (Phase 8)**: Depends on Phases 4–6 (needs to know final list of new files to add to OWNERS.md)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent — creates `.github/pull_request_template.md`
- **User Story 2 (P1)**: Independent after Phase 1 — creates `docs/checklists/weekly-sweep.md`
- **User Story 3 (P2)**: Independent after Phase 1 — creates `docs/checklists/monthly-review.md`
- **User Story 4 (P2)**: Independent after Phase 1 — creates `docs/checklists/quarterly-audit.md`
- **User Story 5 (P2)**: Independent — modifies `.github/workflows/ci.yml`
- **User Story 6 (P3)**: Depends on US2/US3/US4 completion (needs final file list for ownership update)

### Within Each User Story

- Create the markdown file with all required sections per contract
- Validate formatting and structure against FR-014/FR-015
- Story complete when file exists and passes linting

### Parallel Opportunities

- **User Stories 1, 2, 3, 4, 5** can all proceed in parallel (different files, no shared dependencies beyond Phase 1 directory creation)
- Within each story: T006/T007 (US2), T008/T009 (US3), T010/T011 (US4) — creation then validation is sequential
- **User Story 6** must wait for US2–US4 to know the final file list
- **Polish tasks** T018 and T019 can run in parallel (different tools, same files)

---

## Parallel Example: User Stories 1–5

```text
# After Phase 1 (T001 directory creation), launch all stories in parallel:
Task: T004 [US1] Create PR template at .github/pull_request_template.md
Task: T006 [US2] Create weekly sweep checklist at docs/checklists/weekly-sweep.md
Task: T008 [US3] Create monthly review checklist at docs/checklists/monthly-review.md
Task: T010 [US4] Create quarterly audit checklist at docs/checklists/quarterly-audit.md
Task: T012 [US5] Update markdownlint command in .github/workflows/ci.yml

# Then validate all stories in parallel:
Task: T005 [US1] Validate PR template format
Task: T007 [US2] Validate weekly sweep format
Task: T009 [US3] Validate monthly review file list
Task: T011 [US4] Validate quarterly audit ADR references
Task: T013–T015 [US5] Validate CI config and tool configs
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 3: User Story 1 — PR template (T004–T005)
3. Complete Phase 4: User Story 2 — Weekly sweep checklist (T006–T007)
4. **STOP and VALIDATE**: Test by creating a PR (US1) and performing a mini sweep (US2)
5. The two P1 stories deliver the highest-impact documentation process improvements

### Incremental Delivery

1. Complete Setup → Directory structure ready
2. Add User Story 1 (PR template) → Every new PR includes doc checklist (MVP!)
3. Add User Story 2 (Weekly sweep) → Weekly safety net catches drift
4. Add User Story 3 (Monthly review) → Comprehensive quality gate
5. Add User Story 4 (Quarterly audit) → Deep structural review
6. Add User Story 5 (CI validation) → Automated enforcement
7. Add User Story 6 (Ownership update) → Clear accountability for new files
8. Polish → Final validation and linting
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup (Phase 1) together
2. Once directory exists:
   - Developer A: User Story 1 (PR template) + User Story 5 (CI config)
   - Developer B: User Story 2 (Weekly sweep) + User Story 3 (Monthly review)
   - Developer C: User Story 4 (Quarterly audit) + User Story 6 (Ownership)
3. Stories complete and integrate independently — no merge conflicts expected (all different files)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story produces independent markdown artifacts — minimal cross-story dependencies
- No application code changes required — all deliverables are markdown files and CI config
- Existing `docs/OWNERS.md`, `docs/decisions/`, `.markdownlint.json`, and `.markdown-link-check.json` are leveraged as-is (per research decisions R2–R5)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
