# Tasks: UI Audit Issue Template

**Input**: Design documents from `/specs/045-ui-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/template-contract.md, quickstart.md

**Tests**: Not requested — this is a static Markdown template with no runtime components. Validation is manual per plan.md and quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent validation of each story's acceptance criteria against the template file `.github/ISSUE_TEMPLATE/chore-ui-audit.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (independent validation, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single deliverable**: `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- **Spec artifacts**: `specs/045-ui-audit/`

---

## Phase 1: Setup (Review Preparation)

**Purpose**: Establish the review baseline — confirm the template file exists, is well-formed, and meets structural prerequisites before validating content.

- [ ] T001 Verify template file exists at `.github/ISSUE_TEMPLATE/chore-ui-audit.md` and is non-empty
- [ ] T002 Validate YAML front matter contains all required fields (`name`, `about`, `title`, `labels`, `assignees`) per contracts/template-contract.md
- [ ] T003 [P] Confirm YAML front matter `name` field is set to `UI Audit` (FR-001) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T004 [P] Confirm YAML front matter `title` field follows `[CHORE] UI Audit` format (FR-010) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T005 [P] Confirm YAML front matter `labels` field includes `chore` (FR-009) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T006 [P] Confirm YAML front matter `assignees` field is present (empty string allowed) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`

---

## Phase 2: Foundational (Template Structure Validation)

**Purpose**: Validate the overall template structure — section presence, heading hierarchy, and Markdown formatting. MUST complete before per-story content validation.

**⚠️ CRITICAL**: No user story validation can begin until the structural integrity of the template is confirmed.

- [ ] T007 Verify the template body contains exactly 10 audit category sections with `### N.` headings matching the names defined in data-model.md and contracts/template-contract.md in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T008 [P] Count total checklist items (lines matching `- [ ]`) and confirm ≥59 items (FR-012) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T009 [P] Verify all checklist items use GitHub-compatible checkbox format `- [ ]` (FR-003) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T010 [P] Verify the template contains an "Implementation Steps" section with exactly 6 phases (FR-006) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T011 [P] Verify the template contains a "Relevant Files" section with placeholder paths (FR-007) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T012 [P] Verify the template contains a "Verification" section with lint, type-check, test, and manual browser validation commands (FR-008) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T013 Verify all three placeholder tokens (`[PAGE_NAME]`, `[PageName]`, `[feature]`) appear in the template body (FR-005) per contracts/template-contract.md placeholder contract in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`

**Checkpoint**: Template structure confirmed — per-story content validation can now begin in parallel.

---

## Phase 3: User Story 1 — Create a Page Audit from the Template (Priority: P1) 🎯 MVP

**Goal**: Validate that a developer can select the UI Audit template from the "New Issue" page, receive a fully structured checklist pre-populated with all ten audit categories, fill in the page name, and create the issue with the correct label and title format.

**Independent Test**: Navigate to the repository's "New Issue" page, select the UI Audit template, verify the issue body contains all ten audit sections with checkbox items, and confirm the issue can be created successfully.

### Implementation for User Story 1

- [ ] T014 [US1] Verify the template is selectable from GitHub's "New Issue" page by confirming it resides in `.github/ISSUE_TEMPLATE/` with valid YAML front matter (FR-001) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T015 [P] [US1] Verify the issue form is pre-filled with the full audit checklist containing all 10 categories when the template is selected (US1-AC1) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T016 [P] [US1] Verify every `[PAGE_NAME]` placeholder is replaceable with an actual page name and the resulting issue clearly identifies the audited page (US1-AC2) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T017 [P] [US1] Verify the `labels: chore` front matter ensures the "chore" label is applied automatically on issue creation (US1-AC3, FR-009) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T018 [US1] Verify the default title `[CHORE] UI Audit` is filterable in the issue list and follows the expected format (US1-AC4, FR-010) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`

**Checkpoint**: User Story 1 validated — the template is selectable, pre-filled, and produces correctly labelled and titled issues.

---

## Phase 4: User Story 2 — Track Audit Progress Across All Categories (Priority: P1)

**Goal**: Validate that every checklist item across all 10 audit categories describes a clear, single pass/fail condition that a developer can evaluate against a real page, and that GitHub's checkbox counters reflect progress.

**Independent Test**: Open an issue created from the template, work through each checklist category, and verify that every item describes a clear, pass/fail condition that can be evaluated against a real page.

### Implementation for User Story 2

- [ ] T019 [P] [US2] Review all items in "1. Component Architecture & Modularity" (7 items) — confirm each describes a single, observable pass/fail condition (FR-004, US2-AC1) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T020 [P] [US2] Review all items in "2. Data Fetching & State Management" (6 items) — confirm each references a specific pattern to verify (FR-004, US2-AC2) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T021 [P] [US2] Review all items in "3. Loading, Error & Empty States" (5 items) — confirm each describes a concrete, testable condition (FR-004) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T022 [P] [US2] Review all items in "4. Type Safety" (5 items) — confirm each describes a concrete, testable condition (FR-004) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T023 [P] [US2] Review all items in "5. Accessibility (a11y)" (7 items) — confirm each maps to a verifiable keyboard-navigation or assistive-technology criterion (FR-004, US2-AC3) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T024 [P] [US2] Review all items in "6. Text, Copy & UX Polish" (8 items) — confirm each describes a concrete, testable condition (FR-004) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T025 [P] [US2] Review all items in "7. Styling & Layout" (6 items) — confirm each describes a concrete, testable condition (FR-004) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T026 [P] [US2] Review all items in "8. Performance" (5 items) — confirm each describes a concrete, testable condition (FR-004) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T027 [P] [US2] Review all items in "9. Test Coverage" (5 items) — confirm each describes a concrete, testable condition (FR-004) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T028 [P] [US2] Review all items in "10. Code Hygiene" (6 items) — confirm each describes a concrete, testable condition (FR-004) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T029 [US2] Verify all checklist items use clear, unambiguous language that does not require external documentation to understand (FR-011, SC-004) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T030 [US2] Verify no category has fewer than 4 items (SC-003) and total items ≥59 (FR-012) — cross-reference with research.md item distribution table in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T031 [US2] Confirm that checking/unchecking items in a created issue from `.github/ISSUE_TEMPLATE/chore-ui-audit.md` updates GitHub's checkbox progress counter per section (US2-AC4, US2-AC5) — manual verification after issue creation

**Checkpoint**: User Story 2 validated — all 60 checklist items are clear, pass/fail, and progress-trackable.

---

## Phase 5: User Story 3 — Follow the Phased Implementation Guide (Priority: P2)

**Goal**: Validate that the six-phase implementation guide is logically sequenced, each phase references specific actionable steps, and phases build on each other without circular dependencies.

**Independent Test**: Read through the implementation steps section and verify that each phase references specific, actionable steps and that phases build on each other in a logical sequence.

### Implementation for User Story 3

- [ ] T032 [P] [US3] Verify Phase 1 (Discovery & Assessment) contains 9 actionable steps that enable producing a complete findings table (US3-AC1) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T033 [P] [US3] Verify Phase 2 (Structural Fixes) contains 4 steps explaining when and how to extract sub-components, hooks, and replace raw data-fetching patterns (US3-AC2) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T034 [P] [US3] Verify Phase 3 (States & Error Handling) contains 4 steps for loading, error, empty states, and confirmation dialogs in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T035 [P] [US3] Verify Phase 4 (a11y & UX Polish) contains 5 steps for ARIA attributes, keyboard navigation, text/copy, tooltips, and dark mode in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T036 [P] [US3] Verify Phase 5 (Testing) contains 3 steps for hook tests, component tests, and edge case verification in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T037 [P] [US3] Verify Phase 6 (Validation) contains 4 verification commands (lint, type-check, tests, manual browser check) matching the Verification section (US3-AC3) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T038 [US3] Verify all 6 phases have sequential dependencies — each phase depends only on preceding phases, with no circular dependencies (US3-AC4, FR-006) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`

**Checkpoint**: User Story 3 validated — the six-phase guide is logically ordered and actionable.

---

## Phase 6: User Story 4 — Identify Relevant Files for a Specific Page (Priority: P2)

**Goal**: Validate that the "Relevant Files" section contains placeholder paths that map to the repository's frontend directory structure and reference actual shared components.

**Independent Test**: Open the template's "Relevant Files" section, replace placeholders with a real page name, and verify the resulting file paths align with the repository's actual directory structure.

### Implementation for User Story 4

- [ ] T039 [P] [US4] Verify "Page & Components" paths use `[PageName]` and `[feature]` placeholders that resolve to valid `solune/frontend/src/` locations (US4-AC1, FR-007) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T040 [P] [US4] Verify "Hooks & API" paths reference `src/hooks/use[Feature].ts` and `src/services/api.ts` with correct placeholder usage in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T041 [P] [US4] Verify "Types" paths reference `src/types/index.ts` or `src/types/[feature].ts` in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T042 [P] [US4] Verify "Shared" section references actual UI primitives (Button, Card, Input, Tooltip, ConfirmationDialog) and common components (CelestialLoader, ErrorBoundary, ProjectSelectionEmptyState) from contracts/template-contract.md (US4-AC2) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T043 [P] [US4] Verify "Tests" paths reference `src/hooks/use[Feature].test.ts` and `src/components/[feature]/*.test.tsx` in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T044 [US4] Substitute placeholders with a real page (e.g., `[PageName]=ProjectsPage`, `[feature]=board`) and confirm all resulting paths point to valid `solune/frontend/src/` directories (US4-AC1, US4-AC3) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`

**Checkpoint**: User Story 4 validated — the Relevant Files section produces a complete file inventory when placeholders are substituted.

---

## Phase 7: User Story 5 — Run Verification Commands After Remediation (Priority: P2)

**Goal**: Validate that the verification section lists specific, runnable commands for linting, type-checking, testing, and manual browser validation that produce clear pass/fail results.

**Independent Test**: Run each verification command listed in the template against a sample page and confirm they produce pass/fail results.

### Implementation for User Story 5

- [ ] T045 [P] [US5] Verify the lint command (`npx eslint src/pages/[PageName].tsx src/components/[feature]/`) is present and produces pass/fail output (US5-AC1, FR-008) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T046 [P] [US5] Verify the type-check command (`npx tsc --noEmit`) is present and produces pass/fail output (US5-AC2, FR-008) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T047 [P] [US5] Verify the test command (`npx vitest run`) is present and produces pass/fail output (US5-AC3, FR-008) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T048 [P] [US5] Verify manual browser checks are listed: light mode, dark mode, responsive viewport, keyboard-only navigation (US5-AC4, FR-008) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T049 [US5] Verify the Verification section contains at least 6 verification items matching the contract (contracts/template-contract.md) — lint, type-check, tests, visual light, visual dark, keyboard (SC-006) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`

**Checkpoint**: User Story 5 validated — all verification commands produce clear pass/fail results.

---

## Phase 8: User Story 6 — Reuse the Template Across Multiple Pages (Priority: P3)

**Goal**: Validate that the template is generic enough to apply to any page in the application via placeholder substitution, without requiring template modifications.

**Independent Test**: Create two audit issues for different pages (e.g., Projects page and Agents page), fill in the page-specific placeholders, and verify both issues are complete and make sense for their respective pages.

### Implementation for User Story 6

- [ ] T050 [P] [US6] Substitute all placeholders for the Projects page (`[PAGE_NAME]=Projects`, `[PageName]=ProjectsPage`, `[feature]=board`) and verify all checklist items, file paths, and commands are applicable (US6-AC1) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T051 [P] [US6] Substitute all placeholders for the Agents page (`[PAGE_NAME]=Agents`, `[PageName]=AgentsPanel`, `[feature]=agents`) and verify all checklist items, file paths, and commands are applicable (US6-AC2) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- [ ] T052 [US6] Confirm that the two audit instances are distinguishable by page name in the title and body (US6-AC3) and that no template modification was required (SC-007) in `.github/ISSUE_TEMPLATE/chore-ui-audit.md`

**Checkpoint**: User Story 6 validated — the template is reusable across different pages without modification.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final review across all stories — edge case handling, consistency checks, and documentation.

- [ ] T053 [P] Verify edge case: template handles pages with no data-fetching hooks (developer skips N/A items and notes them) per spec.md edge cases
- [ ] T054 [P] Verify edge case: template handles new pages with no existing tests (Test Coverage section still applies) per spec.md edge cases
- [ ] T055 [P] Verify edge case: template handles non-applicable checklist items (developer checks and notes N/A) per spec.md edge cases
- [x] T056 The "aduit" typo in the template filename and YAML front matter (RT-005 in research.md) has been corrected — file renamed to `chore-ui-audit.md` with "UI Audit" in all front matter fields
- [ ] T057 Verify template consistency with other chore templates in `.github/ISSUE_TEMPLATE/` — confirm YAML front matter follows the same pattern (RT-006 in research.md)
- [ ] T058 Run quickstart.md verification steps (sections 1–6) against the template file to confirm all structural checks pass
- [ ] T059 Final review: confirm all 12 functional requirements (FR-001 through FR-012) and all 8 success criteria (SC-001 through SC-008) are satisfied per specs/045-ui-audit/spec.md against `.github/ISSUE_TEMPLATE/chore-ui-audit.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — validates template selectability and issue creation
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — validates checklist content quality
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — validates implementation guide
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — validates relevant files section
- **User Story 5 (Phase 7)**: Depends on Foundational (Phase 2) — validates verification commands
- **User Story 6 (Phase 8)**: Depends on User Stories 1–5 (Phases 3–7) — validates reusability using insights from prior stories
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 6 (P3)**: Depends on US1–US5 for context — validates the template works across multiple pages using knowledge from prior validations

### Within Each User Story

- Structural/format checks before content quality checks
- Individual category reviews before cross-category consistency checks
- Placeholder mechanics before placeholder substitution testing

### Parallel Opportunities

- All Setup tasks T003–T006 marked [P] can run in parallel
- All Foundational tasks T008–T012 marked [P] can run in parallel
- User Stories 1–5 (Phases 3–7) can all run in parallel after Foundational phase
- All per-category reviews in US2 (T019–T028) can run in parallel
- All phase reviews in US3 (T032–T037) can run in parallel
- All file section reviews in US4 (T039–T043) can run in parallel
- All verification command reviews in US5 (T045–T048) can run in parallel
- Both page substitution tests in US6 (T050–T051) can run in parallel
- All edge case checks in Polish (T053–T055) can run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch all category reviews in parallel (all different sections, no dependencies):
Task: T019 "Review Component Architecture & Modularity items in .github/ISSUE_TEMPLATE/chore-ui-audit.md"
Task: T020 "Review Data Fetching & State Management items in .github/ISSUE_TEMPLATE/chore-ui-audit.md"
Task: T021 "Review Loading, Error & Empty States items in .github/ISSUE_TEMPLATE/chore-ui-audit.md"
Task: T022 "Review Type Safety items in .github/ISSUE_TEMPLATE/chore-ui-audit.md"
Task: T023 "Review Accessibility items in .github/ISSUE_TEMPLATE/chore-ui-audit.md"
Task: T024 "Review Text, Copy & UX Polish items in .github/ISSUE_TEMPLATE/chore-ui-audit.md"
Task: T025 "Review Styling & Layout items in .github/ISSUE_TEMPLATE/chore-ui-audit.md"
Task: T026 "Review Performance items in .github/ISSUE_TEMPLATE/chore-ui-audit.md"
Task: T027 "Review Test Coverage items in .github/ISSUE_TEMPLATE/chore-ui-audit.md"
Task: T028 "Review Code Hygiene items in .github/ISSUE_TEMPLATE/chore-ui-audit.md"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (verify file exists, YAML front matter valid)
2. Complete Phase 2: Foundational (confirm 10 categories, ≥59 items, 6 phases, all sections present)
3. Complete Phase 3: User Story 1 (template selectable, issue creatable with correct label/title)
4. Complete Phase 4: User Story 2 (all 60 checklist items are clear, pass/fail, progress-trackable)
5. **STOP and VALIDATE**: Both P1 stories confirmed — template is usable for page audits

### Incremental Delivery

1. Complete Setup + Foundational → Template structure confirmed
2. Add User Story 1 → Template is selectable and creates valid issues (MVP!)
3. Add User Story 2 → All checklist content validated → Deploy/Demo
4. Add User Story 3 → Implementation guide validated
5. Add User Story 4 → Relevant files section validated
6. Add User Story 5 → Verification commands validated
7. Add User Story 6 → Reusability confirmed across multiple pages
8. Polish → Edge cases, consistency, final requirements sign-off

### Parallel Team Strategy

With multiple reviewers:

1. Team confirms Setup + Foundational together
2. Once Foundational is confirmed:
   - Reviewer A: User Story 1 (selectability) + User Story 2 (checklist content)
   - Reviewer B: User Story 3 (implementation guide) + User Story 4 (relevant files)
   - Reviewer C: User Story 5 (verification) + User Story 6 (reusability)
3. All stories validated independently, then Polish phase as a group

---

## Notes

- [P] tasks = independent validation steps, no dependencies on each other
- [Story] label maps task to specific user story for traceability
- This is a review-and-merge chore — tasks validate existing content, not create new code
- No automated tests — all validation is manual (create issue, inspect template, run quickstart checks)
- The "aduit" typo (RT-005) has been corrected — template file renamed and front matter updated
- Total: 59 tasks across 9 phases covering 6 user stories and 12 functional requirements
