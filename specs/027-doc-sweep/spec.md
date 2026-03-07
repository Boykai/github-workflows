# Feature Specification: Recurring Documentation Update Process

**Feature Branch**: `027-doc-sweep`  
**Created**: 2026-03-07  
**Status**: Implemented  
**Input**: User description: "Documentation Sweep — A structured cadence for keeping all project documentation accurate, complete, and helpful across the full stack. Includes PR-level checks, weekly staleness sweeps, monthly full reviews, quarterly architecture audits, and standards/tooling enforcement."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — PR Author Verifies Documentation Before Merge (Priority: P1)

A developer completes a code change that adds a new endpoint, environment variable, or modifies startup behavior. Before submitting their pull request, they see a documentation checklist in the PR template. The checklist prompts them to confirm that corresponding documentation files have been updated (or explicitly state no doc changes are needed). The reviewer can see at a glance whether documentation was addressed and can reject the PR if the checklist items are unmet.

**Why this priority**: PR-level checks are the first line of defense against documentation drift. Every code change that affects behavior, configuration, or APIs must be caught at the PR level — before it reaches the main branch. Without this gate, all downstream review processes inherit stale documentation.

**Independent Test**: Can be fully tested by creating a pull request with a code change that adds a new endpoint, verifying the PR template includes the documentation checklist, and confirming the reviewer can see the checklist status.

**Acceptance Scenarios**:

1. **Given** a developer creates a new pull request, **When** the PR description is populated from the template, **Then** a documentation checklist section is included with items covering endpoint docs, configuration docs, setup docs, agent pipeline docs, schema/data model docs, and a summary of which doc files were updated.
2. **Given** a developer has added a new endpoint in the codebase, **When** the reviewer inspects the PR, **Then** the reviewer can verify whether the corresponding documentation file has been updated by checking the documentation checklist item.
3. **Given** a developer has made a code change that does not affect documentation, **When** they fill out the PR checklist, **Then** they can explicitly mark "no doc changes needed" and provide a brief rationale.
4. **Given** a reviewer is evaluating a PR that changes a configuration variable, **When** the documentation checklist shows the configuration docs item is unchecked, **Then** the reviewer knows to request documentation updates before approving.

---

### User Story 2 — Weekly Staleness Sweep Catches Documentation Drift (Priority: P1)

A developer on rotation performs a weekly staleness sweep that takes approximately 30 minutes. They follow a structured checklist to compare the current codebase against key documentation files: API reference, configuration guide, and setup guide. They identify any discrepancies — missing endpoints, outdated environment variables, changed prerequisite versions — and either fix them immediately or file issues to track the corrections.

**Why this priority**: Even with PR-level checks, documentation can drift due to incomplete reviews, emergency fixes, or cross-cutting changes. The weekly sweep is a lightweight safety net that catches drift before it compounds. It is the most cost-effective recurring review activity.

**Independent Test**: Can be fully tested by intentionally introducing a discrepancy between the codebase and a documentation file, performing the weekly sweep using the checklist, and confirming the discrepancy is identified.

**Acceptance Scenarios**:

1. **Given** the codebase has a route file that does not have a matching entry in the API reference documentation, **When** the developer performs the weekly sweep checklist for the API reference, **Then** the missing entry is identified and flagged for addition.
2. **Given** a configuration variable has been removed from the codebase, **When** the developer performs the weekly sweep checklist for the configuration documentation, **Then** the stale variable entry is identified and flagged for removal.
3. **Given** the prerequisite version for a runtime has been updated in the project manifest, **When** the developer performs the weekly sweep checklist for the setup guide, **Then** the version mismatch is identified and flagged for correction.
4. **Given** an endpoint has been deprecated but is still listed in the API reference, **When** the developer performs the weekly sweep, **Then** the deprecated endpoint is identified and flagged for removal or deprecation notice.

---

### User Story 3 — Monthly Full Review Ensures Coverage and Consistency (Priority: P2)

The tech lead conducts a monthly full documentation review as a sprint planning item, taking approximately 2–3 hours. They walk through every documentation file to verify accuracy (reflects current code behavior), completeness (no major features are undocumented), and consistency (uniform terminology, naming, and formatting). They also perform a cross-reference check to validate internal links, code snippet correctness, and external link validity. Readability and usability standards are assessed: each page has a purpose statement, step-by-step guides use numbered lists, and standard table formats are used for configuration and API documentation.

**Why this priority**: The monthly review provides a comprehensive quality gate that catches issues the weekly sweep may miss — such as undocumented features, broken cross-references, inconsistent terminology, and readability problems. It ensures the documentation suite remains a reliable resource.

**Independent Test**: Can be fully tested by performing the full documentation review using the coverage audit checklist, cross-reference check, and readability assessment, then confirming all identified issues are logged with clear remediation paths.

**Acceptance Scenarios**:

1. **Given** a new feature was shipped last month without corresponding documentation, **When** the tech lead performs the monthly coverage audit, **Then** the missing documentation is identified and an issue is created to address it.
2. **Given** an internal documentation link points to a heading that was renamed, **When** the cross-reference check is performed, **Then** the broken link is identified and flagged for correction.
3. **Given** a configuration table in the documentation is missing the "required/optional" column, **When** the readability assessment is performed, **Then** the incomplete table format is identified as a readability issue.
4. **Given** two documentation files use different terms for the same concept, **When** the consistency check is performed, **Then** the terminology mismatch is identified and one canonical term is selected.

---

### User Story 4 — Quarterly Architecture Audit After Major Milestones (Priority: P2)

After a major feature milestone (new integrations, significant refactors, new agent types), the tech lead conducts a quarterly architecture audit taking approximately half a day. They verify the architecture document reflects the current service topology, data flow, and provider integrations. They ensure any significant architectural decisions are captured as Architecture Decision Records. A developer experience audit is performed — a team member follows the setup guide from scratch and documents any friction. A documentation gaps analysis identifies features shipped in the quarter without adequate documentation.

**Why this priority**: Quarterly audits address deep structural documentation that weekly and monthly reviews do not cover — architecture diagrams, decision records, and developer onboarding experience. These issues accumulate slowly but significantly impact new team member productivity and architectural understanding.

**Independent Test**: Can be fully tested by comparing the architecture document against the current service topology, verifying ADRs exist for significant decisions, having a team member complete the setup guide from scratch, and checking that all features shipped in the quarter have documentation.

**Acceptance Scenarios**:

1. **Given** a new service was added to the application since the last audit, **When** the architecture document is reviewed, **Then** the missing service is identified as a gap in the architecture diagram.
2. **Given** a significant architectural decision was made during the quarter, **When** the decision records are reviewed, **Then** the decision is captured (or flagged as missing) in an Architecture Decision Record with Context, Decision, and Consequences sections.
3. **Given** a new team member follows the setup guide from scratch, **When** they encounter friction or missing steps, **Then** the friction points are documented and the setup guide is updated to address them.
4. **Given** features were shipped in the quarter, **When** the documentation gaps analysis is performed, **Then** any features lacking adequate documentation are identified and issues are created to address the gaps.

---

### User Story 5 — Automated Formatting and Link Validation (Priority: P2)

When a contributor submits a pull request that modifies any markdown file in the `docs/` directory or any `*.md` file in the repository, an automated check runs in the continuous integration pipeline. The check validates that the markdown conforms to consistent formatting standards (ATX-style headings, language-tagged code blocks, proper table formatting) and that all internal and external links resolve correctly. If violations are found, the CI check fails with clear error messages identifying the specific files and issues, allowing the contributor to fix them before merge.

**Why this priority**: Automated linting and link checking remove the burden of manual formatting reviews and prevent broken links from accumulating. This is the most scalable way to enforce documentation standards across all contributors.

**Independent Test**: Can be fully tested by submitting a markdown file with intentional formatting violations and a broken link, then confirming the CI pipeline catches both issues and reports them clearly.

**Acceptance Scenarios**:

1. **Given** a contributor submits a PR with a markdown file using setext-style headings instead of ATX-style, **When** the CI markdown linting check runs, **Then** the check fails and reports the specific heading format violation.
2. **Given** a contributor submits a PR with a markdown file containing a broken internal link, **When** the CI link check runs, **Then** the check fails and identifies the specific broken link and the file it appears in.
3. **Given** a contributor submits a PR with a properly formatted markdown file and all valid links, **When** the CI checks run, **Then** both checks pass and the PR is not blocked.
4. **Given** a code block in a documentation file lacks a language specifier, **When** the CI markdown linting check runs, **Then** the check reports the missing language tag with the file and line number.

---

### User Story 6 — Documentation Ownership Is Clear and Discoverable (Priority: P3)

A contributor wants to know who is responsible for a specific documentation file — either to request a review, report an issue, or coordinate an update. They check the documentation ownership file and find a clear mapping of each documentation file to its designated owner (by role, not by individual name). When documentation falls behind, the responsible role is accountable for bringing it up to date.

**Why this priority**: Clear ownership prevents the "tragedy of the commons" where no one feels responsible for documentation quality. It provides accountability and makes it easy to route documentation questions to the right person.

**Independent Test**: Can be fully tested by verifying the ownership file exists, contains an entry for each documentation file, and that each entry maps to a role.

**Acceptance Scenarios**:

1. **Given** a contributor checks the documentation ownership file, **When** they look up a specific documentation file, **Then** they find a clear mapping to the responsible role.
2. **Given** a new documentation file is added to the project, **When** the ownership file is reviewed, **Then** a corresponding entry for the new file is expected (caught during monthly review if missing).
3. **Given** the ownership file exists, **When** a contributor reads it, **Then** every documentation file in the `docs/` directory has a corresponding ownership entry.

---

### Edge Cases

- What happens when a PR changes behavior that spans multiple documentation files? The PR author must update all affected files and list each updated file in the PR description.
- What happens when the weekly sweep identifies a discrepancy that requires significant rewriting? The developer files an issue rather than attempting to fix it during the 30-minute sweep, and the issue is addressed in the next sprint.
- What happens when an external link in the documentation is temporarily unreachable during CI checks? The link checker should distinguish between permanent failures (404) and temporary failures (timeout, 5xx), and only fail the build on permanent failures. Temporary failures are logged as warnings.
- What happens when a documentation file has no clear owner due to a team restructure? The tech lead acts as the default owner until the ownership file is updated during the next monthly review.
- What happens when the monthly review identifies that a documentation file is no longer needed? The file is marked for deprecation, and if no one objects within one review cycle, it is removed and its references are updated.
- What happens when the quarterly architecture audit reveals the architecture diagram tooling is unavailable? The audit documents the discrepancies in text form and creates an issue to update the diagram when tooling is available.
- What happens when a contributor is unsure whether their code change requires documentation updates? They default to checking the documentation checklist item as "confirmed not needed" with a rationale, and the reviewer makes the final call.
- What happens when CI markdown linting rules conflict with the content of an existing documentation file? The contributor can use inline disable comments for specific rules if justified, and the exception is documented in the PR description.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The PR template MUST include a documentation checklist section with items for endpoint documentation, configuration documentation, setup documentation, agent pipeline documentation, schema/data model documentation, and a field for listing updated doc files or confirming no changes are needed.
- **FR-002**: The documentation checklist MUST be visible to both the PR author and reviewers, allowing reviewers to verify documentation coverage before approving.
- **FR-003**: A weekly staleness sweep checklist MUST exist that covers API reference accuracy (route-to-documentation mapping), configuration documentation accuracy (environment variable parity), and setup guide accuracy (version and step verification).
- **FR-004**: The weekly sweep checklist MUST be completable within approximately 30 minutes by a single developer.
- **FR-005**: A monthly full documentation review checklist MUST exist covering accuracy (reflects current behavior), completeness (all features documented), and consistency (uniform terminology and formatting).
- **FR-006**: The monthly review MUST include a cross-reference check validating all internal documentation links, code snippet correctness, top-level README links, and external link validity.
- **FR-007**: The monthly review MUST include a readability assessment verifying each page has a purpose statement, step-by-step guides use numbered lists, configuration tables include variable name/type/required status/default/description columns, API tables include method/path/auth/description columns, and troubleshooting entries follow the Symptom-Cause-Fix format.
- **FR-008**: A quarterly architecture audit checklist MUST exist covering architecture document accuracy (service diagram, data flow, provider list), Architecture Decision Records completeness, developer experience audit (setup from scratch), and documentation gaps analysis.
- **FR-009**: Architecture Decision Records MUST follow the Context-Decision-Consequences format.
- **FR-010**: The CI pipeline MUST run markdown formatting validation on all markdown files in the `docs/` directory and all `*.md` files in the repository when they are modified in a pull request.
- **FR-011**: The CI pipeline MUST run link validation on documentation files, checking both internal links and external links.
- **FR-012**: CI formatting and link checks MUST produce clear, actionable error messages identifying the specific file, line, and violation when checks fail.
- **FR-013**: A documentation ownership file MUST exist that maps each documentation file to a responsible role.
- **FR-014**: All documentation MUST use ATX-style headings, language-tagged code blocks, tables for structured data (environment variables, API endpoints, configuration options), numbered lists for sequential steps, and bullet lists for non-ordered items.
- **FR-015**: Filenames referenced in documentation MUST use inline code formatting.
- **FR-016**: The cadence of documentation reviews MUST follow the defined schedule: PR-level checks on every PR, weekly staleness sweeps, monthly full reviews, and quarterly architecture audits.
- **FR-017**: Roles and responsibilities for documentation maintenance MUST be defined: PR authors update docs for behavior changes, PR reviewers reject PRs without documentation updates, rotating developers perform weekly sweeps, and the tech lead signs off on monthly reviews and leads quarterly audits.
- **FR-018**: Each documentation page MUST meet the project's definition of "good documentation": accurate, minimal, actionable, discoverable, and maintained (last-reviewed date within the current quarter).

### Key Entities

- **Documentation File**: A markdown file within the `docs/` directory or at the repository root that describes a specific aspect of the project (setup, configuration, API reference, architecture, etc.). Key attributes: file path, designated owner role, last-reviewed date, review status.
- **Documentation Checklist**: A structured list of verification items used at different review cadences (PR-level, weekly, monthly, quarterly). Key attributes: checklist type, items, pass/fail status, reviewer, completion date.
- **Architecture Decision Record (ADR)**: A document capturing a significant architectural decision. Key attributes: title, context, decision, consequences, date, status.
- **Documentation Ownership Mapping**: A file that maps each documentation file to a responsible role. Key attributes: documentation file path, owner role.

## Assumptions

- The project uses GitHub pull requests as the standard workflow for code changes, and PR templates are supported and already in use (or can be adopted without significant overhead).
- The CI/CD pipeline is already in place and supports adding new check steps for markdown linting and link validation.
- The team has at least one developer available for the weekly rotation and the tech lead has capacity for monthly and quarterly reviews.
- The existing `docs/` directory structure is the canonical location for project documentation and does not require reorganization as part of this feature.
- The documentation formatting standards described (ATX headings, language-tagged code blocks, etc.) do not conflict with any existing enforced formatting rules.
- Architecture Decision Records will be stored in a `docs/decisions/` directory, created if it does not already exist.
- The new contributor review is triggered on demand and does not require a recurring schedule or automation.

## Scope Exclusions

- **Content migration**: This specification does not include migrating or rewriting existing documentation to meet the new standards. Existing documentation will be brought into compliance incrementally through the defined review cadences.
- **Documentation generation tooling**: This specification does not include automated documentation generation from code (e.g., auto-generating API reference from code annotations). It focuses on the human review and maintenance process.
- **Documentation hosting or publishing**: This specification does not cover hosting documentation on an external site (e.g., GitHub Pages, ReadTheDocs). Documentation remains as markdown files in the repository.
- **Prose style linting**: While mentioned as a consideration in the parent issue, prose style linting (e.g., `vale`) is excluded from scope. It can be evaluated separately after markdown formatting and link linting are established.
- **Automated documentation drift detection**: Automated comparison of code changes against documentation content (beyond what CI linting provides) is not in scope. Drift detection is handled by the human review cadences.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of new pull requests include the documentation checklist in their description, as verified by the PR template.
- **SC-002**: Weekly staleness sweeps are completed within 30 minutes and identify at least 90% of documentation-to-code discrepancies introduced since the last sweep.
- **SC-003**: After the first monthly review cycle, zero documentation files have broken internal links.
- **SC-004**: After CI linting is enabled, 100% of merged pull requests that modify markdown files pass the formatting and link validation checks.
- **SC-005**: Every documentation file in the `docs/` directory has a designated owner role listed in the ownership file.
- **SC-006**: After the first quarterly audit, the setup guide can be followed from scratch by a new contributor to achieve a working local environment without requiring unwritten steps or tribal knowledge.
- **SC-007**: 100% of significant architectural decisions made after the process is adopted have a corresponding Architecture Decision Record.
- **SC-008**: Documentation staleness (time since last review) for any file does not exceed one quarter (approximately 90 days).
- **SC-009**: The monthly review identifies and resolves all terminology inconsistencies across documentation files, achieving uniform naming within two review cycles.
- **SC-010**: New team members can locate the correct documentation for any project aspect within 2 minutes using the README and table of contents structure.
