# Tasks: Recurring Documentation Refresh Playbook

**Input**: Design documents from `/specs/040-doc-refresh-playbook/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not required. This feature introduces no code changes — only documentation process artifacts and a single JSON metadata file. Validation is performed through the existing weekly sweep checklist, automated link checking (`grep`), and scope verification (`git diff --stat`), all built into the playbook itself (Phase 6/US6).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Each user story corresponds to one phase of the bi-weekly documentation refresh playbook.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/` at repository root
- **Docs**: `docs/` at repository root
- **Specs**: `specs/040-doc-refresh-playbook/`
- **Scripts**: `scripts/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the refresh baseline file and verify all prerequisite tools, files, and scripts are in place before the first refresh cycle

- [x] T001 Create initial `docs/.last-refresh` baseline JSON file with fields: `date` (current ISO 8601 timestamp), `sha` (current `git rev-parse HEAD`), `documents_updated` (empty array), `documents_skipped` (empty array), `broken_links_found` (0), `manual_followups` (empty array) — per RefreshBaseline entity in data-model.md and research R1
- [x] T002 [P] Verify prerequisite tools are available: `git` (with full history, not shallow clone), `jq` (for JSON baseline parsing), `grep`, `find`, and confirm `scripts/generate-diagrams.sh` exists and is executable
- [x] T003 [P] Verify all 11 documentation files in the documentation-to-source mapping exist at their expected paths: `docs/api-reference.md`, `docs/architecture.md`, `docs/agent-pipeline.md`, `docs/configuration.md`, `docs/custom-agents-best-practices.md`, `docs/project-structure.md`, `docs/testing.md`, `docs/troubleshooting.md`, `docs/setup.md`, `docs/signal-integration.md`, `frontend/docs/findings-log.md`
- [x] T004 [P] Verify all source-of-truth files referenced in the DocumentationMapping (data-model.md) exist: `backend/src/api/` route files, `backend/src/services/`, `backend/src/config.py`, `docker-compose.yml`, `pyproject.toml`, `package.json`, test directories, pipeline/orchestrator service files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm existing checklists and process infrastructure are functional before executing any refresh phase

**⚠️ CRITICAL**: No user story work can begin until this phase is complete — the baseline file and verified mappings are required inputs for all subsequent phases

- [x] T005 Verify `docs/checklists/weekly-sweep.md` exists and is current — this checklist is used as the final validation pass in US6 (FR-019)
- [x] T006 [P] Verify `docs/decisions/README.md` (ADR index) exists and contains current entries — used by US5 for ADR index updates (FR-015)
- [x] T007 [P] Verify `docs/architectures/` directory contains expected Mermaid diagram files: `high-level.mmd`, `deployment.mmd`, `frontend-components.mmd`, `backend-components.mmd`, `data-flow.mmd` — used by US5 for diagram regeneration (FR-014)
- [x] T008 [P] Confirm `CHANGELOG.md` follows Keep a Changelog format with `## [Unreleased]` or `## YYYY-MM-DD` date headers and `### Added`/`### Changed`/`### Removed`/`### Fixed` category headers — required for reliable parsing in US1 (research R2)

**Checkpoint**: Foundation ready — baseline file created, all prerequisite files verified, user story execution can now begin

---

## Phase 3: User Story 1 — Detect and Catalog Changes Since Last Refresh (Priority: P1) 🎯 MVP

**Goal**: Examine three sources (CHANGELOG, specs, code diffs) and produce a categorized Change Manifest listing all new features, changed behaviors, removed functionality, architectural shifts, and UX shifts since the last refresh

**Independent Test**: Run the change detection process against a known two-week window with the pre-recorded baseline commit SHA from `docs/.last-refresh`, and verify the manifest captures all user-visible changes by cross-checking against `git log --oneline` for the period

### Implementation for User Story 1

- [x] T009 [US1] Read the refresh baseline from `docs/.last-refresh` using `jq` to extract `.date` and `.sha` fields — handle fallback per FR-020: if file is missing or malformed, use `--since="2 weeks ago"` for date-based operations and `HEAD~100` for SHA-based operations, and log a warning (per change-detection.md contract)
- [x] T010 [US1] Extract CHANGELOG delta by parsing `CHANGELOG.md`: scan for section headers matching `## YYYY-MM-DD` or `## [Unreleased]`, include all entries from sections dated after the baseline date AND the `[Unreleased]` section, extract bullet items under `### Added`, `### Changed`, `### Removed`, `### Fixed` sub-headers — each item becomes a ManifestItem with `source: "CHANGELOG"` (FR-002, research R2, change-detection.md contract)
- [x] T011 [P] [US1] Scan `specs/` for recently modified directories using `find specs/ -mindepth 1 -maxdepth 1 -type d -newer docs/.last-refresh` — for each modified directory, read `spec.md` to extract the feature title (first `# ` heading) and first paragraph as summary, creating ManifestItems with `source: "specs"` and deduplicating against CHANGELOG entries (FR-003, change-detection.md contract)
- [x] T012 [P] [US1] Run code diff analysis using `git diff --stat <baseline-sha>..HEAD`, `git diff --name-status <baseline-sha>..HEAD`, and `git log --oneline --since="<baseline-date>"` — flag new files (`A` status), deleted files (`D` status), renamed files (`R` status), and high-churn files (>5 commits or >100 lines changed) in monitored directories: `backend/src/api/`, `backend/src/services/`, `backend/src/config.py`, `backend/src/migrations/`, `frontend/src/pages/`, `frontend/src/components/`, `docker-compose.yml`, `pyproject.toml`, `package.json` (FR-004, research R3, change-detection.md contract)
- [x] T013 [US1] Compile the Change Manifest by merging findings from T010, T011, and T012 into five categories: **New features** (pages, endpoints, services, UX flows), **Changed behavior** (renamed concepts, altered workflows, config changes), **Removed functionality** (deleted routes, deprecated features, removed UI), **Architectural shifts** (new services, refactored modules, changed dependencies), **UX shifts** (new pages, removed pages, changed navigation) — ensure no duplicates across categories, each item has description, source, source_detail, domain, and affected_docs fields per ChangeManifest entity in data-model.md (FR-005)
- [x] T014 [US1] Cross-check the compiled Change Manifest against `git log --oneline --since="<baseline-date>"` to verify completeness — every user-visible commit should map to at least one manifest item (SC-002); flag any uncovered commits for manual review

**Checkpoint**: User Story 1 complete — Change Manifest produced with categorized changes from all three sources, cross-checked for completeness

---

## Phase 4: User Story 2 — Prioritize Documentation Updates by Focus Shift (Priority: P1)

**Goal**: Classify changes by domain area, identify narrative shifts, and produce a priority-ordered list (P0–P3) of documentation files to update

**Independent Test**: Provide the Change Manifest from US1 and verify the output correctly classifies changes by domain, identifies narrative shifts, and produces a priority-ordered list of documents to update matching the rules in FR-008

### Implementation for User Story 2

- [x] T015 [US2] Classify Change Manifest items in `docs/.change-manifest.md` by domain area: group each item into one of the predefined domains — pipeline, agents, chat, projects, tools, settings, auth, signal, analytics, infra — and identify domains with the most changes as current development focus areas (FR-006)
- [x] T016 [US2] Evaluate narrative shifts from the classified `docs/.change-manifest.md` by answering four questions: (1) Has a new top-level capability been added? (2) Has a prominent feature been reduced or removed? (3) Has the app's pitch changed? (4) Has the UX flow changed significantly (new landing page, reorganized nav, new primary workflow)? — document answers and evidence from manifest items (FR-007)
- [x] T017 [US2] Assign priority levels to each documentation file using the rule-based prioritization from FR-008 and research R6: **P0** → `README.md` if pitch/workflow changed; **P1** → `docs/api-reference.md`, `docs/agent-pipeline.md`, `docs/custom-agents-best-practices.md`, `docs/signal-integration.md` if directly affected by new/changed features; **P2** → `docs/project-structure.md`, `docs/architecture.md` if modules added/removed/reorganized; **P3** → `docs/troubleshooting.md`, `docs/configuration.md`, `docs/testing.md`, `docs/setup.md` if config/errors/tests changed — a document inherits its highest applicable priority (PriorityAssignment entity in data-model.md)
- [x] T018 [US2] Produce the final priority-ordered update plan in `docs/.change-manifest.md` listing each flagged document with its priority level (P0–P3), trigger reason, and source-of-truth file(s) to diff against — documents with no applicable triggers are marked as skipped (FR-008, documentation-update.md contract)

**Checkpoint**: User Story 2 complete — prioritized update plan produced; maintainer knows exactly which files to update and in what order

---

## Phase 5: User Story 3 — Update README to Reflect Current State (Priority: P2)

**Goal**: When README is flagged P0, update its feature list, architecture overview, quickstart instructions, and workflow descriptions to accurately reflect the current application state

**Independent Test**: Compare updated README sections against current configuration files (`docker-compose.yml`, `pyproject.toml`, `package.json`) and verify the feature list matches the Change Manifest's "New features" and "Removed functionality" categories

### Implementation for User Story 3

- [x] T019 [US3] Update the feature list / capabilities section in `README.md`: add new capabilities from the Change Manifest "New features" category, remove deprecated ones from the "Removed functionality" category, and reorder by current prominence (FR-009, documentation-update.md contract README-specific rules)
- [x] T020 [P] [US3] Update the architecture overview section in `README.md` if system topology changed: compare described services against `docker-compose.yml` service definitions and `backend/src/services/` directory, add new services, remove decommissioned ones (documentation-update.md contract)
- [x] T021 [P] [US3] Validate quickstart instructions in `README.md` against current prerequisite versions: check Python version in `backend/pyproject.toml` (`python_requires`), Node.js version in `frontend/package.json`, Docker Compose configuration in `docker-compose.yml`, and update any stale version numbers or setup commands (FR-010)
- [x] T022 [US3] Update workflow descriptions and screenshots in `README.md` if UX changed: verify page names, navigation paths, and terminology match the current application — update descriptions of primary user flows to reflect current state (documentation-update.md contract README-specific rules)

**Checkpoint**: User Story 3 complete — README accurately reflects current application state (feature list, architecture, quickstart, workflows)

---

## Phase 6: User Story 4 — Update Individual Documentation Files Against Source of Truth (Priority: P2)

**Goal**: For each documentation file flagged by the prioritization phase, diff its content against the designated source-of-truth, correct inaccuracies, add new sections for new functionality, and remove stale content

**Independent Test**: Select any single doc (e.g., `docs/configuration.md`), compare it against its source-of-truth file (`backend/src/config.py`), and verify every documented item still exists in the source and every source item is documented

### Implementation for User Story 4

- [x] T023 [P] [US4] Update `docs/api-reference.md` against `backend/src/api/` route files: extract all route decorators (`@app.` / `@router.`) from API files, compare documented endpoints against code routes, add new endpoints, remove deleted ones, correct changed parameters or response types (FR-011, documentation-update.md contract)
- [x] T024 [P] [US4] Update `docs/architecture.md` against `backend/src/services/` directory and `docker-compose.yml`: compare documented services against actual service files and compose definitions, update service descriptions, add new services, remove decommissioned ones, update relationship descriptions (FR-011)
- [x] T025 [P] [US4] Update `docs/agent-pipeline.md` against pipeline/orchestrator service code (PipelineService, WorkflowOrchestrator): compare documented stages, execution groups, and status flow against current code logic, update any changed pipeline behavior (FR-011)
- [x] T026 [P] [US4] Update `docs/configuration.md` against `backend/src/config.py`: extract all environment variable references (`os.environ`, `getenv`, `Field(`) from config, compare against documented env vars, add new variables with types and defaults, remove deleted variables, correct changed defaults (FR-011)
- [x] T027 [P] [US4] Update `docs/custom-agents-best-practices.md` against AgentMcpSync service code and `.agent.md` files: compare documented frontmatter properties and MCP sync behavior against current implementation (FR-011)
- [x] T028 [P] [US4] Update `docs/project-structure.md` against current filesystem: run `tree -I node_modules -I __pycache__ -I .git -L 3` (or equivalent `find`) and compare output against the documented directory tree, update for new directories, renamed modules, and removed paths (FR-011)
- [x] T029 [P] [US4] Update `docs/testing.md` against test directories, `backend/pyproject.toml` (`[tool.pytest]` section), and `frontend/vitest.config.ts`: compare documented test categories and run commands against current configuration, add new test categories, update changed commands (FR-011)
- [x] T030 [P] [US4] Update `docs/troubleshooting.md` against recent bug fixes from the Change Manifest "Changed behavior" / "Fixed" items: add new error patterns and resolutions, remove entries for issues that have been fixed (FR-011)
- [x] T031 [P] [US4] Update `docs/setup.md` against `pyproject.toml`, `package.json`, and `docker-compose.yml`: compare documented prerequisites, versions, and setup steps against current files, update changed version requirements and installation commands (FR-011)
- [x] T032 [P] [US4] Update `docs/signal-integration.md` against Signal-related backend code — only if the Change Manifest contains Signal-domain items; skip this task if no Signal code changes detected (FR-011, conditional per DocumentationMapping in data-model.md)
- [x] T033 [P] [US4] Append to `frontend/docs/findings-log.md` — only if the Change Manifest contains frontend UX audit findings; skip this task if no frontend audit results are available (FR-011, conditional per DocumentationMapping in data-model.md)

**Checkpoint**: User Story 4 complete — all flagged documentation files updated against their source-of-truth with zero stale claims

---

## Phase 7: User Story 5 — Validate Cross-References, Diagrams, and Indexes (Priority: P3)

**Goal**: Validate all internal links resolve correctly, regenerate Mermaid diagrams if architecture changed, update the ADR index for new decisions, and update document ownership if new files were created

**Independent Test**: Run link validation (`grep -rn` for internal doc links) across all documentation files and verify zero broken internal links; confirm any changed architecture diagrams render correctly

### Implementation for User Story 5

- [x] T034 [US5] Validate all internal documentation links by running `grep -rn '\[.*\](docs/' README.md docs/` and verifying each target path resolves to an existing file — for links with anchors (`#section-name`), verify the target file contains a matching heading; report all broken links with source file, line number, and target path (FR-013, verification-baseline.md contract, research R7)
- [x] T035 [P] [US5] Regenerate Mermaid diagrams by running `scripts/generate-diagrams.sh` — only if the Change Manifest contains items in the "Architectural shifts" category; verify all `.mmd` files in `docs/architectures/` (`high-level.mmd`, `deployment.mmd`, `frontend-components.mmd`, `backend-components.mmd`, `data-flow.mmd`) are valid after regeneration (FR-014, research R8, verification-baseline.md contract)
- [x] T036 [P] [US5] Check for new ADRs by running `git diff --name-status <baseline-sha>..HEAD -- docs/decisions/` and update `docs/decisions/README.md` with entries for any new architectural decision records found (ADR number, title, date, status) (FR-015, verification-baseline.md contract)
- [x] T037 [P] [US5] Review `docs/OWNERS.md` and update if new documentation files were created during this refresh cycle — add ownership entries for any new files (verification-baseline.md contract)

**Checkpoint**: User Story 5 complete — zero broken internal links, diagrams regenerated (if needed), ADR index current, ownership up to date

---

## Phase 8: User Story 6 — Verify Accuracy and Record the Refresh Baseline (Priority: P3)

**Goal**: Run the weekly sweep checklist as a final validation, spot-check user flows against documentation, record the refresh in the CHANGELOG, and store the new baseline for the next refresh cycle

**Independent Test**: Complete a full refresh cycle, verify the weekly sweep checklist passes, confirm a CHANGELOG entry was added, and verify the baseline file contains the current date and commit SHA

### Implementation for User Story 6

- [x] T038 [US6] Run the `docs/checklists/weekly-sweep.md` checklist as a final validation pass — all checklist items should pass after the refresh; investigate any failures and fix if caused by the refresh, record pre-existing failures as manual followups (FR-019, verification-baseline.md contract)
- [x] T039 [US6] Spot-check 3 key user flows in the running application: select representative P0/P1 user flows, walk through each in the application, compare page names, navigation paths, and terminology against documentation, flag and fix any discrepancies (SC-006, verification-baseline.md contract)
- [x] T040 [US6] Verify refresh scope by running `git diff --stat` and confirming changes are limited to `docs/`, `README.md`, `CHANGELOG.md`, and `docs/.last-refresh` — revert any accidental code edits before committing (SC-005, verification-baseline.md contract)
- [x] T041 [US6] Add a dated CHANGELOG entry under the appropriate `## YYYY-MM-DD` section with `### Changed` listing which documents were updated during this refresh cycle (e.g., "Documentation refresh: updated [list of documents] to match current codebase state") in `CHANGELOG.md` (FR-016, verification-baseline.md contract)
- [x] T042 [US6] Commit all documentation changes (from T019–T041) with message format: `docs: bi-weekly documentation refresh YYYY-MM-DD` — this commit captures all doc updates, CHANGELOG entry, and cross-reference fixes (FR-017, verification-baseline.md contract)
- [x] T043 [US6] Update `docs/.last-refresh` baseline with current cycle data: set `date` to current ISO 8601 timestamp, `sha` to the commit SHA from T042 (`git rev-parse HEAD`), `documents_updated` to the list of modified doc paths, `documents_skipped` to reviewed-but-unchanged docs, `broken_links_found` to count from T034, and `manual_followups` to any deferred items — then amend the refresh commit (`git commit --amend --no-edit`) so the baseline is included in the final committed state (FR-017, FR-021, RefreshBaseline entity in data-model.md, quickstart.md)

**Checkpoint**: User Story 6 complete — refresh cycle closed, baseline recorded, next cycle can start with a clean diff window

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Process improvements and documentation of lessons learned that span multiple user stories

- [x] T044 [P] Review refresh cycle efficiency against the 4-hour time budget (SC-001) and document any bottlenecks or process improvements discovered during execution in `specs/040-doc-refresh-playbook/quickstart.md`
- [x] T045 [P] Verify the complete end-to-end process is documented in `specs/040-doc-refresh-playbook/quickstart.md` with accurate commands and time estimates per phase
- [x] T046 Confirm the refresh playbook complements (does not replace) existing `docs/checklists/weekly-sweep.md`, `docs/checklists/monthly-review.md`, and `docs/checklists/quarterly-audit.md` checklists — verify no overlap or conflict in responsibilities (FR-019)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 – Change Detection (Phase 3)**: Depends on Foundational; produces the Change Manifest consumed by all subsequent stories
- **US2 – Prioritization (Phase 4)**: Depends on US1 (requires the Change Manifest as input)
- **US3 – README Update (Phase 5)**: Depends on US2 (requires priority assignments); only executes if README is flagged P0
- **US4 – Individual Doc Updates (Phase 6)**: Depends on US2 (requires priority assignments); can run in parallel with US3
- **US5 – Cross-References (Phase 7)**: Depends on US3 and US4 (all content updates must be complete before link validation)
- **US6 – Verify & Record (Phase 8)**: Depends on US5 (all updates and validations must be complete)
- **Polish (Phase 9)**: Depends on US6 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories; produces the Change Manifest
- **User Story 2 (P1)**: Depends on US1 — requires the Change Manifest as input; produces the priority-ordered update plan
- **User Story 3 (P2)**: Depends on US2 — requires priority assignments; conditional execution (only if README flagged P0); can run in parallel with US4
- **User Story 4 (P2)**: Depends on US2 — requires priority assignments; each doc update (T023–T033) is independent and can run in parallel
- **User Story 5 (P3)**: Depends on US3 + US4 — all content updates must be complete; cross-reference validation must run after all changes are made
- **User Story 6 (P3)**: Depends on US5 — all updates and validations must be complete before recording the baseline

### Within Each User Story

- Change detection sources (T010, T011, T012) can run in parallel, then merge in T013
- Doc updates (T023–T033) are fully independent and can all run in parallel
- Cross-reference tasks (T034–T037) can run in parallel
- Verification and recording (T038–T043) must run sequentially: sweep → spot-check → scope verify → CHANGELOG → commit → baseline (amend)

### Parallel Opportunities

- All Setup tasks T002–T004 marked [P] can run in parallel
- All Foundational tasks T006–T008 marked [P] can run in parallel
- US1: Spec scan (T011) and code diff (T012) can run in parallel after baseline read (T009)
- US3: Architecture (T020) and quickstart validation (T021) can run in parallel
- US4: All 11 doc update tasks (T023–T033) can run in parallel — each targets a different file with a different source-of-truth
- US5: Diagram regeneration (T035), ADR index (T036), and OWNERS (T037) can run in parallel after link validation (T034)
- US3 and US4 can run in parallel after US2 completes (different target files)

---

## Parallel Example: User Story 4

```bash
# Launch all doc update tasks together (each targets a different file):
Task T023: "Update docs/api-reference.md against backend/src/api/ route files"
Task T024: "Update docs/architecture.md against backend/src/services/ + docker-compose.yml"
Task T025: "Update docs/agent-pipeline.md against pipeline/orchestrator code"
Task T026: "Update docs/configuration.md against backend/src/config.py"
Task T027: "Update docs/custom-agents-best-practices.md against agent MCP sync code"
Task T028: "Update docs/project-structure.md against filesystem tree output"
Task T029: "Update docs/testing.md against test dirs + config files"
Task T030: "Update docs/troubleshooting.md against Change Manifest bug fixes"
Task T031: "Update docs/setup.md against pyproject.toml + package.json + docker-compose.yml"
Task T032: "Update docs/signal-integration.md against Signal backend code (conditional)"
Task T033: "Append to frontend/docs/findings-log.md (conditional)"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup — create baseline file, verify prerequisites
2. Complete Phase 2: Foundational — verify checklists and mappings
3. Complete Phase 3: User Story 1 — produce the Change Manifest
4. Complete Phase 4: User Story 2 — produce the priority-ordered update plan
5. **STOP and VALIDATE**: The team now has full visibility into documentation drift and knows exactly which files to update and in what order
6. Even without executing the updates, the Change Manifest + priority plan delivers value

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (Change Detection) → Change Manifest produced (visibility into drift)
3. Add US2 (Prioritization) → Actionable update plan produced (MVP!)
4. Add US3 (README) + US4 (Docs) → All documentation updated against source-of-truth
5. Add US5 (Cross-References) → Links validated, diagrams current
6. Add US6 (Verify & Record) → Cycle closed, baseline recorded for next cycle
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple contributors after US2 completes:

1. Team completes Setup + Foundational + US1 + US2 together (sequential dependency chain)
2. Once US2 produces the priority plan:
   - Contributor A: US3 (README updates)
   - Contributors B–E: US4 tasks in parallel (each person takes 2–3 doc files)
3. After all US3 + US4 tasks complete:
   - Contributor A: US5 (cross-reference validation)
   - Contributor B: US6 (verification and baseline recording)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- This feature introduces no code changes — `git diff --stat` must show only `docs/`, `README.md`, `CHANGELOG.md` modifications (SC-005)
- The process is initially manual (~3–4 hours per cycle) with automation path for change manifest generation and link validation after 2–3 manual cycles (spec Assumption 7)
- Conditional tasks (T032, T033) are skipped when their trigger condition is not met — this is expected behavior, not a failure
- Commit after each phase or logical group of tasks
- Stop at any checkpoint to validate the story independently
