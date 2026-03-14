# Feature Specification: Recurring Documentation Update Process

**Feature Branch**: `040-doc-sweep`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "Documentation Sweep — A structured cadence for keeping all project documentation accurate, complete, and helpful across the full stack — backend API, frontend components, architecture, configuration, and developer guides."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — PR-Level Documentation Checks (Priority: P1)

As a **PR author**, I want a clear checklist integrated into the pull request template that reminds me to update documentation whenever I change behavior, configuration, or APIs, so that documentation never silently drifts from the codebase.

As a **PR reviewer**, I want an enforceable gate that prevents merging PRs that change user-facing behavior without corresponding documentation updates, so that I can confidently approve changes knowing the docs remain accurate.

**Why this priority**: PR-level enforcement is the single most effective prevention mechanism. Catching documentation drift at the source — the moment code changes — is orders of magnitude cheaper than discovering stale docs weeks later. Without this, every downstream phase inherits compounding inaccuracies.

**Independent Test**: Submit a PR that adds a new API endpoint without updating `docs/api-reference.md`. Verify the PR checklist surfaces the missing documentation item and the reviewer can identify the gap before approval.

**Acceptance Scenarios**:

1. **Given** a developer opens a new pull request, **When** the PR template loads, **Then** a documentation checklist section is visible containing items for API reference, configuration, setup guide, agent pipeline, and schema changes.
2. **Given** a PR adds a new endpoint in the `api/` directory, **When** a reviewer inspects the checklist, **Then** there is a clear item requiring a corresponding entry in `docs/api-reference.md`.
3. **Given** a PR adds a new environment variable in the configuration module, **When** the reviewer inspects the checklist, **Then** there is a clear item requiring a corresponding entry in `docs/configuration.md`.
4. **Given** a PR changes startup behavior, Docker setup, or prerequisites, **When** the reviewer inspects the checklist, **Then** there is a clear item requiring updates to `docs/setup.md`.
5. **Given** a PR that does not require documentation changes, **When** the author fills the checklist, **Then** there is an option to explicitly state "no doc changes needed" with a brief justification.

---

### User Story 2 — Weekly Staleness Sweep (Priority: P1)

As a **developer on rotation**, I want a structured 30-minute weekly checklist that guides me through verifying the accuracy of the most frequently changing documentation files (API reference, configuration, and setup guide), so that documentation drift is caught within one week of occurrence.

**Why this priority**: Even with PR-level checks, documentation can still drift due to overlooked changes, hotfixes, or multi-PR features. A weekly sweep is the safety net that catches what PR reviews miss. The three files covered (API reference, configuration, setup) are the most volatile and most used by developers.

**Independent Test**: Deliberately introduce a mismatch (e.g., add a route file without updating the API reference doc), then follow the weekly sweep checklist to verify the mismatch is detected within the 30-minute process.

**Acceptance Scenarios**:

1. **Given** a developer begins the weekly sweep, **When** they scan the API route files against `docs/api-reference.md`, **Then** any route file without a matching API table entry is identified.
2. **Given** a developer performs the weekly sweep, **When** they compare documented environment variables against the configuration source, **Then** any missing or deleted variables are flagged.
3. **Given** a developer performs the weekly sweep, **When** they verify the setup guide, **Then** prerequisite versions listed in the guide match those in `pyproject.toml` and `package.json`.
4. **Given** a deprecated endpoint is still listed in the API reference, **When** the sweep is performed, **Then** the stale entry is flagged for removal or deprecation notice.

---

### User Story 3 — Monthly Full Documentation Review (Priority: P2)

As a **tech lead**, I want a comprehensive monthly review process that audits every documentation file for accuracy, completeness, and consistency, including cross-reference validation and readability checks, so that the entire documentation set remains trustworthy and usable.

**Why this priority**: Monthly reviews provide depth that weekly sweeps cannot. They cover less-volatile files (architecture, troubleshooting, testing guides), validate cross-document links, and enforce readability standards. This cadence balances thoroughness with practical time investment (2–3 hours).

**Independent Test**: Follow the monthly review checklist against the current docs directory. Verify that every file in `docs/` is reviewed for accuracy, all internal links resolve correctly, and formatting standards are consistently applied.

**Acceptance Scenarios**:

1. **Given** a tech lead begins the monthly review, **When** they walk every file in `docs/`, **Then** each file is verified as accurate (reflects current code behavior), complete (no undocumented features), and consistent (uniform terminology and formatting).
2. **Given** the monthly review includes a cross-reference check, **When** all internal `docs/` links are tested, **Then** every link resolves to an existing heading or file.
3. **Given** the monthly review includes a readability audit, **When** each documentation page is reviewed, **Then** it has a clear purpose statement at the top, sequential steps use numbered lists, and configuration tables include all required columns (variable name, type, required/optional, default, description).
4. **Given** a code snippet appears in a documentation file, **When** the snippet is tested against the current codebase, **Then** it compiles or runs without error.

---

### User Story 4 — Quarterly Architecture Audit (Priority: P2)

As a **tech lead**, I want a quarterly deep-dive that verifies architecture documentation, captures major design decisions as Architecture Decision Records, and audits the developer onboarding experience, so that strategic documentation stays aligned with the system's actual state after major milestones.

**Why this priority**: Architecture documentation changes less frequently but has higher impact when it drifts. Quarterly audits timed after major feature milestones catch structural changes that weekly and monthly reviews may not surface, and the ADR process preserves institutional knowledge that would otherwise be lost.

**Independent Test**: After a major feature milestone, follow the quarterly audit checklist. Verify the architecture diagram reflects the current Docker Compose topology and all backend service modules are represented.

**Acceptance Scenarios**:

1. **Given** a quarterly audit is triggered after a major feature milestone, **When** the architecture document is reviewed, **Then** the service diagram reflects the current Docker Compose topology and all backend service modules are represented.
2. **Given** a significant architectural decision was made during the quarter, **When** the audit is performed, **Then** the decision is captured as an ADR in `docs/decisions/` following the Context → Decision → Consequences format.
3. **Given** the quarterly audit includes a developer experience check, **When** a team member follows `docs/setup.md` from scratch, **Then** they can complete the full local setup end-to-end and any friction points are documented.
4. **Given** the quarterly audit includes a docs gaps analysis, **When** all features shipped in the quarter are listed, **Then** each feature has adequate documentation coverage.

---

### User Story 5 — Documentation Standards and Automation (Priority: P3)

As a **contributor**, I want clearly defined formatting standards and automated linting in CI that enforces consistent formatting and catches broken links, so that documentation quality is maintained automatically without relying solely on manual review.

**Why this priority**: Standards and automation create a self-sustaining quality baseline. While they don't replace human review, they eliminate entire categories of errors (broken links, inconsistent formatting) automatically, reducing the manual review burden at every other phase.

**Independent Test**: Submit a PR with a markdown file that violates formatting standards (e.g., inconsistent heading style, broken internal link). Verify the CI pipeline flags the violations before the PR can be merged.

**Acceptance Scenarios**:

1. **Given** a PR modifies a markdown file in `docs/`, **When** CI runs, **Then** a markdown linter checks the file against project formatting standards and reports any violations.
2. **Given** a PR introduces a broken internal or external link in a documentation file, **When** CI runs, **Then** a link checker identifies the broken link and reports it as a CI failure.
3. **Given** a new contributor reads the formatting standards, **When** they write documentation, **Then** they can follow clear rules for heading styles (ATX), code block language specifications, table usage, and list formatting.

---

### User Story 6 — Documentation Ownership and Accountability (Priority: P3)

As a **project maintainer**, I want each documentation file to have a designated owner listed in a central ownership file, and clear role definitions for documentation responsibilities, so that accountability is explicit and no documentation file is orphaned.

**Why this priority**: Without clear ownership, documentation maintenance defaults to "everyone's responsibility" which in practice means no one's responsibility. Explicit ownership ensures every file has someone accountable for its accuracy and timeliness.

**Independent Test**: Check that a `docs/OWNERS.md` file exists and maps every file in `docs/` to a designated owner role.

**Acceptance Scenarios**:

1. **Given** the documentation ownership file exists, **When** a developer checks `docs/OWNERS.md`, **Then** every file in `docs/` is listed with a designated owner role.
2. **Given** documented roles and responsibilities exist, **When** a PR author, reviewer, or rotating developer consults them, **Then** their specific documentation responsibilities are clearly defined.
3. **Given** a new documentation file is added to `docs/`, **When** the ownership file is reviewed during the next sweep, **Then** the new file is flagged as needing an assigned owner.

---

### Edge Cases

- What happens when a PR changes behavior but the author claims "no doc changes needed" — is there a verification mechanism beyond trust?
- How is documentation handled for features that span multiple PRs before the full documentation picture is clear?
- What happens when the weekly sweep reveals a large number of stale entries that cannot be fixed within 30 minutes?
- How are conflicts resolved when two contributors update the same documentation file simultaneously?
- What happens when an external link referenced in documentation goes permanently offline?
- How is documentation handled during emergency hotfixes where the standard PR process may be abbreviated?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The PR template MUST include a documentation checklist section with items covering API reference, configuration, setup guide, agent pipeline, and schema changes.
- **FR-002**: The PR template checklist MUST include an explicit "Documentation updated (or confirmed not needed)" item.
- **FR-003**: The weekly staleness sweep MUST include verification steps for `docs/api-reference.md` against route files in the API source directory.
- **FR-004**: The weekly staleness sweep MUST include verification steps for `docs/configuration.md` against environment variables in the configuration source.
- **FR-005**: The weekly staleness sweep MUST include verification steps for `docs/setup.md` against prerequisite versions in `pyproject.toml` and `package.json`.
- **FR-006**: The monthly review MUST audit every file in `docs/` for accuracy, completeness, and consistency.
- **FR-007**: The monthly review MUST validate all internal documentation links resolve to existing headings or files.
- **FR-008**: The monthly review MUST verify that each documentation page has a clear purpose statement, uses numbered lists for sequential steps, and follows table formatting standards.
- **FR-009**: The quarterly audit MUST verify the architecture diagram reflects the current service topology.
- **FR-010**: The quarterly audit MUST capture any significant architectural decisions as ADRs following the Context → Decision → Consequences format.
- **FR-011**: The quarterly audit MUST include a developer experience test where a team member follows the setup guide from scratch.
- **FR-012**: CI MUST run a markdown linter on all files in `docs/` and root-level `*.md` files to enforce formatting standards.
- **FR-013**: CI MUST run a link checker on documentation files to catch broken internal and external links.
- **FR-014**: A `docs/OWNERS.md` file MUST exist mapping each documentation file to a designated owner role.
- **FR-015**: Formatting standards MUST require ATX-style headings, language-specified code blocks, tables for structured data (env vars, API endpoints, config options), numbered lists for sequential steps, and inline code formatting for file names.
- **FR-016**: The weekly sweep MUST be completable within 30 minutes by a single developer.
- **FR-017**: The monthly review MUST be completable within 2–3 hours.
- **FR-018**: Each documentation file MUST have a last-reviewed date within the current quarter to be considered "maintained."

### Assumptions

- The project uses a pull request-based workflow where all code changes go through review before merging.
- The `docs/` directory is the canonical location for project documentation.
- The team has enough developers to sustain a weekly rotation for staleness sweeps without overburdening any single person.
- Existing CI infrastructure supports adding new linting and link-checking steps.
- The `markdownlint` tool is suitable for enforcing the project's formatting standards.
- The `markdown-link-check` tool is suitable for validating internal and external links.
- Architecture Decision Records are a new practice — the `docs/decisions/` directory may not yet exist and will need to be created.
- The "New contributor review" cadence (on demand, before onboarding) is handled ad hoc and does not require formal process definition beyond ensuring `docs/setup.md` is accurate.

### Key Entities

- **Documentation File**: A markdown file in `docs/` or `frontend/docs/` that describes a specific aspect of the project (setup, API reference, architecture, etc.). Key attributes: file path, designated owner, last-reviewed date, purpose.
- **Review Cadence**: A scheduled documentation review activity with a defined frequency (per-PR, weekly, monthly, quarterly), scope, responsible role, and expected duration.
- **PR Documentation Checklist**: A set of verification items embedded in the PR template that authors must complete before requesting review. Covers API, configuration, setup, agent pipeline, and schema documentation.
- **Architecture Decision Record (ADR)**: A structured document capturing a significant design decision using the Context → Decision → Consequences format, stored in `docs/decisions/`.
- **Documentation Owner**: A role designation linking a documentation file to the person or team responsible for its accuracy and maintenance, recorded in `docs/OWNERS.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of pull requests that change user-facing behavior, configuration, or APIs include documentation updates or an explicit "no doc changes needed" justification within 30 days of process adoption.
- **SC-002**: Weekly staleness sweeps detect documentation drift within 7 days of the code change that caused it.
- **SC-003**: Every file in `docs/` has a last-reviewed date within the current quarter at all times after the first full quarterly cycle.
- **SC-004**: Zero broken internal documentation links detected during monthly reviews after the first full monthly cycle.
- **SC-005**: A new contributor can complete the full local development setup by following `docs/setup.md` without needing to consult source code or ask for help, within 30 minutes.
- **SC-006**: 100% of documentation files in `docs/` have a designated owner listed in `docs/OWNERS.md`.
- **SC-007**: CI catches 100% of markdown formatting violations and broken links in documentation files before merge.
- **SC-008**: Every significant architectural decision made during a quarter is captured as an ADR before the next quarterly audit.
- **SC-009**: The weekly staleness sweep is completed by the assigned developer within the 30-minute time budget at least 90% of the time.
- **SC-010**: Documentation accuracy, as measured by the monthly review audit (percentage of files passing all accuracy checks), reaches and sustains 95% or higher.
