# Feature Specification: Recurring Documentation Refresh Playbook

**Feature Branch**: `040-doc-refresh-playbook`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "Plan: Recurring Documentation Refresh Playbook"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect and Catalog Changes Since Last Refresh (Priority: P1)

A documentation maintainer initiates a bi-weekly documentation refresh cycle. The process examines three sources — the CHANGELOG, recently modified spec directories, and code diffs since the last recorded refresh — and produces a categorized Change Manifest listing all new features, changed behaviors, removed functionality, architectural shifts, and UX shifts. The maintainer reviews this manifest to understand what has changed in the application since the last documentation cycle.

**Why this priority**: Without an accurate, comprehensive Change Manifest, no subsequent documentation updates can happen. This is the foundational input that drives every other phase of the playbook. If only this story is delivered, the team already gains visibility into documentation drift.

**Independent Test**: Can be fully tested by running the change detection process against a known two-week window with a pre-recorded baseline commit SHA, and verifying the manifest captures all user-visible changes (cross-checked against `git log --oneline` for the period).

**Acceptance Scenarios**:

1. **Given** a last-refresh baseline exists with a date and commit SHA, **When** the change detection process runs, **Then** it extracts all Added/Changed/Removed/Fixed entries from CHANGELOG since that date.
2. **Given** two spec directories have been modified since the last refresh date, **When** the spec scan runs, **Then** both specs appear in the manifest with their title and summary.
3. **Given** new files were added to backend API routes and a frontend page was renamed since the last refresh SHA, **When** the code diff analysis runs, **Then** both changes appear in the manifest even if they are absent from the CHANGELOG.
4. **Given** all three sources have been analyzed, **When** the Change Manifest is compiled, **Then** items are categorized into: New features, Changed behavior, Removed functionality, Architectural shifts, and UX shifts — with no duplicates across categories.

---

### User Story 2 - Prioritize Documentation Updates by Focus Shift (Priority: P1)

After the Change Manifest is produced, the maintainer classifies changes by domain area (e.g., pipeline, agents, chat, auth, infra) and identifies narrative shifts — such as a new top-level capability being added, a prominent feature being removed, or the application's primary workflow changing. The result is a prioritized list of documentation updates (P0 through P3) that tells the maintainer exactly which files to update and in what order.

**Why this priority**: Prioritization prevents the maintainer from spending effort on low-impact docs while critical files like README are stale. This story turns a raw change list into an actionable update plan. Together with Story 1, it forms a complete "what to do" guide even before any writing begins.

**Independent Test**: Can be fully tested by providing a sample Change Manifest and verifying the output correctly classifies changes by domain, identifies narrative shifts, and produces a priority-ordered list of documents to update.

**Acceptance Scenarios**:

1. **Given** a Change Manifest with changes concentrated in the pipeline and agents domains, **When** focus shift analysis runs, **Then** pipeline and agents are identified as current development focus areas.
2. **Given** the manifest indicates the application's primary workflow has changed (e.g., new landing page, reorganized navigation), **When** narrative shifts are evaluated, **Then** README is flagged as P0 priority for update.
3. **Given** the manifest shows new endpoints were added but no architectural changes, **When** prioritization runs, **Then** `api-reference.md` is P1, `architecture.md` is not flagged, and `project-structure.md` is not flagged.
4. **Given** no changes affect the application's pitch or primary workflow, **When** prioritization runs, **Then** README is not flagged as P0.

---

### User Story 3 - Update README to Reflect Current State (Priority: P2)

When the prioritization phase flags README as needing updates (P0), the maintainer updates the README's feature list, architecture overview, quickstart instructions, and workflow descriptions to accurately reflect the current state of the application. Each section is validated against its source of truth (current codebase, configuration files, and UX).

**Why this priority**: README is the first document new users and contributors encounter. An outdated README causes confusion and erodes trust. However, it only needs updating when the app's pitch or primary workflow has actually changed, making it dependent on the prioritization phase.

**Independent Test**: Can be fully tested by comparing the updated README sections against current configuration files (docker-compose.yml, pyproject.toml, package.json) and verifying that the feature list matches the Change Manifest's "New features" and "Removed functionality" categories.

**Acceptance Scenarios**:

1. **Given** the Change Manifest lists two new capabilities and one removed feature, **When** the README feature list is updated, **Then** the new capabilities are added, the removed feature is deleted, and features are reordered by current prominence.
2. **Given** the system topology has changed (new service added to docker-compose.yml), **When** the README architecture overview is updated, **Then** the overview reflects the new service and its role.
3. **Given** a prerequisite version has changed in pyproject.toml, **When** the quickstart instructions are validated, **Then** the README shows the updated version requirement.
4. **Given** the application's primary UX flow has changed, **When** workflow descriptions are updated, **Then** page names, navigation paths, and terminology match the current application.

---

### User Story 4 - Update Individual Documentation Files Against Source of Truth (Priority: P2)

For each documentation file flagged by the prioritization phase, the maintainer diffs the current doc content against its designated source-of-truth (e.g., `api-reference.md` against backend route files, `configuration.md` against config.py). Inaccuracies are corrected, new sections are added for new functionality, and stale content is removed.

**Why this priority**: Individual docs are the detailed reference materials that users rely on daily. Keeping them accurate prevents support burden and user frustration. This story covers the bulk of the refresh work and directly depends on the prioritization from Story 2.

**Independent Test**: Can be fully tested by selecting any single doc (e.g., `configuration.md`), comparing it against its source-of-truth file (`config.py`), and verifying every documented item still exists in the source and every source item is documented.

**Acceptance Scenarios**:

1. **Given** a new API endpoint was added to `backend/src/api/`, **When** `api-reference.md` is updated, **Then** the new endpoint is documented with its purpose, parameters, and responses.
2. **Given** an environment variable was removed from `config.py`, **When** `configuration.md` is updated, **Then** the removed variable is deleted from the documentation.
3. **Given** a new service was added to `docker-compose.yml`, **When** `architecture.md` is updated, **Then** the new service appears in the architecture description with its role and relationships.
4. **Given** a test category was added to the test suite, **When** `testing.md` is updated, **Then** the new test category is documented with its run command and purpose.
5. **Given** the filesystem structure has changed (new directories, renamed modules), **When** `project-structure.md` is updated, **Then** the documented tree matches the actual filesystem.

---

### User Story 5 - Validate Cross-References, Diagrams, and Indexes (Priority: P3)

After all individual documents are updated, the maintainer validates that all internal links between documents resolve correctly, Mermaid diagrams are regenerated if architecture changed, the ADR index includes any new architectural decisions, and document ownership is updated if new files were created.

**Why this priority**: Cross-reference integrity and diagram accuracy are important for a polished documentation set, but they represent finishing touches that depend on all content updates being complete first.

**Independent Test**: Can be fully tested by running a link validation check across all documentation files and verifying zero broken internal links, then confirming any changed architecture diagrams render correctly.

**Acceptance Scenarios**:

1. **Given** all documentation files have been updated, **When** internal link validation runs, **Then** every `[text](docs/...)` link in README and docs/ resolves to an existing file.
2. **Given** the architecture has changed during this refresh cycle, **When** Mermaid diagrams are regenerated, **Then** the diagrams in `docs/architectures/` reflect the current system topology.
3. **Given** a new architectural decision was made during the refresh period, **When** the ADR index is checked, **Then** the new ADR appears in `docs/decisions/README.md`.
4. **Given** a new documentation file was created during this refresh, **When** ownership is reviewed, **Then** `OWNERS.md` includes the new file.

---

### User Story 6 - Verify Accuracy and Record the Refresh Baseline (Priority: P3)

After all updates and validations are complete, the maintainer runs the weekly sweep checklist as a final validation pass, spot-checks key user flows in the running application against documentation, records the refresh in the CHANGELOG, and stores the current date and commit SHA as the new baseline for the next refresh cycle.

**Why this priority**: Verification and baseline recording ensure the refresh cycle is self-sustaining. Without recording the baseline, the next cycle cannot determine its diff window. This story closes the loop and makes the process repeatable.

**Independent Test**: Can be fully tested by completing a full refresh cycle, verifying the weekly sweep checklist passes, confirming a CHANGELOG entry was added, and verifying the baseline file contains the current date and commit SHA.

**Acceptance Scenarios**:

1. **Given** all documentation updates are complete, **When** the weekly sweep checklist is run, **Then** all checklist items pass.
2. **Given** the refresh is complete, **When** the maintainer spot-checks three key user flows in the running application, **Then** page names, navigation, and terminology in the docs match the live application.
3. **Given** all verification passes, **When** the refresh is recorded, **Then** a dated CHANGELOG entry lists which documents were updated.
4. **Given** the refresh commit is made, **When** the baseline is updated, **Then** the baseline file contains the current date and the commit SHA of the refresh commit.
5. **Given** the next refresh cycle begins, **When** it reads the baseline, **Then** it uses the stored date and SHA as the starting point for change detection.

---

### Edge Cases

- What happens when no changes are detected since the last refresh? The process completes with an empty Change Manifest and no documentation updates are needed. The baseline is still updated to record the check.
- What happens when the baseline file is missing or corrupted? The process falls back to using a reasonable default window (e.g., the last 2 weeks based on date, or the last tagged docs-refresh commit). A warning is surfaced to the maintainer.
- What happens when a source-of-truth file for a doc has been deleted? The corresponding documentation file is flagged for review — the maintainer decides whether to archive or remove the doc.
- What happens when CHANGELOG entries are ambiguous or missing for significant code changes? The code diff analysis (source 3) catches undocumented changes and surfaces them in the manifest so they are not overlooked.
- What happens when multiple documentation files reference the same changed component? Each file is updated independently against its own source of truth; the cross-reference validation in Phase 5 ensures consistency.
- What happens when the refresh process is interrupted midway? Partial progress is preserved because each doc update is an independent commit-able unit. The baseline is only updated upon full completion, so an interrupted refresh can be resumed.
- What happens when internal links point to a document section (anchor) that was renamed or removed during the refresh? Link validation detects the broken anchor and flags it for manual correction.
- What happens when diagram generation fails (e.g., malformed Mermaid syntax)? The failure is reported to the maintainer. The refresh continues for all other tasks; diagram issues are tracked as an open item.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The process MUST read a stored baseline (date and commit SHA) to determine the diff window for change detection.
- **FR-002**: The process MUST extract all Added, Changed, Removed, and Fixed entries from CHANGELOG.md that were added since the last refresh date.
- **FR-003**: The process MUST scan the `specs/` directory for directories modified since the last refresh and extract each spec's title and summary.
- **FR-004**: The process MUST run a code diff analysis comparing the last refresh commit SHA to the current HEAD, surfacing high-churn files, new files, deleted files, and renamed modules.
- **FR-005**: The process MUST compile a Change Manifest that merges findings from CHANGELOG, specs, and code diffs into five categories: New features, Changed behavior, Removed functionality, Architectural shifts, and UX shifts.
- **FR-006**: The process MUST classify Change Manifest items by domain area (e.g., pipeline, agents, chat, projects, tools, settings, auth, signal, analytics, infra) to identify current development focus.
- **FR-007**: The process MUST evaluate narrative shifts by determining whether a new top-level capability was added, a prominent feature was removed, the application's pitch changed, or the UX flow changed significantly.
- **FR-008**: The process MUST assign a priority level (P0–P3) to each documentation file based on the nature of changes detected, following the prioritization rules: P0 for README when pitch/workflow changed, P1 for docs directly affected by new/changed features, P2 for structural docs when modules changed, P3 for support docs when config/errors/tests changed.
- **FR-009**: The process MUST update the README feature list by adding new capabilities, removing deprecated ones, and reordering by current prominence when README is flagged P0.
- **FR-010**: The process MUST validate README quickstart instructions against current prerequisite versions in configuration files (docker-compose.yml, pyproject.toml, package.json) when README is flagged P0.
- **FR-011**: The process MUST update each flagged documentation file by diffing its content against its designated source-of-truth file, correcting inaccuracies, adding new sections, and removing stale content.
- **FR-012**: The process MUST maintain a mapping of each documentation file to its source-of-truth (e.g., `api-reference.md` ↔ backend route files, `configuration.md` ↔ config.py, `architecture.md` ↔ services + docker-compose.yml).
- **FR-013**: The process MUST validate all internal documentation links (markdown links referencing `docs/` paths) and report any that do not resolve to existing files.
- **FR-014**: The process MUST trigger Mermaid diagram regeneration when architectural changes are detected in the Change Manifest.
- **FR-015**: The process MUST update the ADR index in `docs/decisions/README.md` when new architectural decision records are identified.
- **FR-016**: The process MUST add a dated entry to CHANGELOG.md listing which documents were updated during the refresh.
- **FR-017**: The process MUST store the current date and commit SHA as the new refresh baseline upon successful completion, using a persistent baseline file (e.g., `docs/.last-refresh`).
- **FR-018**: The process MUST run on a bi-weekly cadence, decoupled from release cycles.
- **FR-019**: The process MUST complement (not replace) existing weekly, monthly, and quarterly documentation checklists.
- **FR-020**: The process MUST handle the case where no baseline exists by falling back to a reasonable default diff window (e.g., 2 weeks by date or last docs-refresh tag).
- **FR-021**: The process MUST produce a summary report at the end of each refresh cycle listing: documents updated, documents skipped (no changes needed), broken links found, and any items requiring manual follow-up.

### Key Entities

- **Change Manifest**: A categorized inventory of all changes detected since the last refresh. Contains items grouped by: New features, Changed behavior, Removed functionality, Architectural shifts, and UX shifts. Each item has a description, source (CHANGELOG/spec/code diff), and affected domain area.
- **Refresh Baseline**: A record of the last completed refresh cycle. Contains: date of last refresh, commit SHA at time of last refresh, and list of documents updated. Stored persistently so the next cycle can determine its diff window.
- **Documentation Mapping**: A registry that associates each documentation file with its source-of-truth file(s) in the codebase. Used to determine what to diff each doc against and when a doc needs updating.
- **Priority Assignment**: A classification applied to each documentation file based on the Change Manifest. Levels range from P0 (README when pitch/workflow changed) through P3 (support docs for minor config/test changes).
- **Refresh Summary Report**: An output produced at the end of each cycle listing all actions taken, documents updated, issues found, and items deferred to the next cycle.

## Assumptions

- The CHANGELOG follows a consistent format with Added/Changed/Removed/Fixed sections that can be parsed reliably.
- The `specs/` directory structure uses a numbered naming convention (e.g., `039-feature-name/`) and each spec has a title and summary that can be extracted.
- Git history is available for diff analysis — the repository is not shallow-cloned for refresh purposes.
- The existing weekly sweep checklist (`docs/checklists/weekly-sweep.md`) is maintained and can serve as a final validation pass.
- The `scripts/generate-diagrams.sh` script exists and can regenerate Mermaid diagrams on demand.
- The documentation-to-source-of-truth mapping (doc ↔ code file) is stable and does not change frequently; when it does, the mapping is updated as part of the refresh.
- The process is initially manual (performed by a maintainer) with the intent to automate change manifest generation and link validation after 2–3 manual cycles.
- The baseline storage format is a JSON file at `docs/.last-refresh` containing `{"date": "...", "sha": "..."}`, chosen for queryability over a git tag approach.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A documentation maintainer can complete the full refresh cycle (detection through verification) within 4 hours for a typical bi-weekly window.
- **SC-002**: The Change Manifest captures 100% of user-visible changes — verified by cross-checking against `git log --oneline` for the refresh period with zero missed items.
- **SC-003**: After a refresh cycle, all internal documentation links resolve correctly — zero broken links detected by link validation.
- **SC-004**: After a refresh cycle, each updated documentation file matches its source-of-truth — no stale endpoints, environment variables, module names, or configuration values remain.
- **SC-005**: After a refresh cycle, `git diff --stat` shows changes only in `docs/`, `README.md`, and `CHANGELOG.md` — no accidental code edits.
- **SC-006**: Three key user flows spot-checked in the running application match the documentation (page names, navigation paths, and terminology are accurate).
- **SC-007**: The refresh baseline is recorded after every completed cycle, enabling the next cycle to start with a clean diff window — zero "unknown starting point" situations after the first cycle.
- **SC-008**: Documentation staleness (measured by the number of inaccuracies found during weekly sweep checklists) decreases by at least 50% after three consecutive bi-weekly refresh cycles.
