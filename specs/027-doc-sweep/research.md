# Research: Recurring Documentation Update Process

**Feature**: 027-doc-sweep | **Date**: 2026-03-07

## R1: PR Template Strategy

**Task**: Determine the best approach for adding a documentation checklist to the GitHub PR template, given that no PR template currently exists.

**Decision**: Create a single `.github/pull_request_template.md` file with the documentation checklist embedded as a section alongside standard PR description fields.

**Rationale**: GitHub supports both single-file templates (`.github/pull_request_template.md`) and multi-template directories (`.github/PULL_REQUEST_TEMPLATE/`). The single-file approach is the simplest — it automatically populates every new PR without requiring the author to choose a template. The documentation checklist items map directly to FR-001: endpoint docs, configuration docs, setup docs, agent pipeline docs, schema/data model docs, and a summary field. Since the project does not currently use PR templates at all, adopting the single-file pattern introduces the least friction.

**Alternatives Considered**:
- **Multi-template directory**: Rejected — YAGNI. Only one template is needed; multiple templates add choice overhead for contributors.
- **GitHub Actions bot comment**: Rejected — adds CI complexity, delays visibility (author sees checklist only after bot runs), and requires additional GitHub token permissions.

---

## R2: Checklist Storage and Format

**Task**: Determine where and how to store the weekly/monthly/quarterly review checklists so they are discoverable, version-controlled, and usable.

**Decision**: Store checklists as standalone markdown files in `docs/checklists/` with GitHub-flavored markdown checkbox syntax (`- [ ]`).

**Rationale**: Markdown checklists in the `docs/` directory are:
- **Discoverable**: Located alongside the documentation they govern
- **Version-controlled**: Changes are tracked in git history
- **Usable**: Developers can copy the checklist into an issue or use it directly from the file
- **CI-compatible**: Subject to existing markdownlint and link-check CI jobs

The `docs/checklists/` subdirectory keeps process documentation separate from project documentation (setup, API reference, etc.) while remaining within the CI linting scope (`docs/**/*.md`).

**Alternatives Considered**:
- **GitHub Issue templates**: Rejected — checklists are internal process guides, not issue creation templates. They need to be read and followed, not filed as issues.
- **Wiki pages**: Rejected — not version-controlled with the codebase, not subject to CI linting, harder to keep in sync.
- **Single combined checklist file**: Rejected — weekly, monthly, and quarterly checklists serve different audiences and cadences; separate files are clearer.

---

## R3: CI Markdown Linting Scope

**Task**: Determine whether the existing CI docs lint job needs modification to meet FR-010 (validate all markdown files modified in a PR).

**Decision**: The existing CI job scope is sufficient for core documentation but should be expanded to cover `*.md` files at the repository root beyond just `README.md`.

**Rationale**: The current `ci.yml` docs job lints `docs/**/*.md` and `README.md`. FR-010 requires validation of "all markdown files in the `docs/` directory and all `*.md` files in the repository." The current scope covers `docs/` completely but misses root-level files like `CHANGELOG.md` (if created), `CONTRIBUTING.md`, or `CODE_OF_CONDUCT.md`. Adding `"*.md"` as a glob target to the markdownlint command extends coverage to these files. The `specs/` directory markdown files are not in scope for documentation linting (they are planning artifacts, not project documentation) and should be excluded to avoid false positives on template syntax.

**Alternatives Considered**:
- **No change to CI**: Rejected — misses FR-010 requirement for "all `*.md` files in the repository" (though the gap is minor since few root-level markdown files exist beyond README).
- **Lint all `**/*.md` recursively**: Rejected — would include `specs/` planning artifacts, `node_modules/`, and other non-documentation markdown that shouldn't be held to docs formatting standards.

---

## R4: Documentation Ownership Model

**Task**: Evaluate whether the existing `docs/OWNERS.md` meets FR-013 requirements or needs modifications.

**Decision**: The existing `docs/OWNERS.md` structure satisfies FR-013, but it must be updated to include entries for any new documentation files introduced by this feature (such as `docs/checklists/*.md`).

**Rationale**: The current `docs/OWNERS.md` maps each documentation file to a responsible role (Backend lead, Tech lead, QA/full-stack lead, Infra/DX lead, rotating owner). It also documents the review cadence (PR-level, weekly, monthly, quarterly). This directly fulfills FR-013 ("A documentation ownership file MUST exist that maps each documentation file to a responsible role"). The file uses role-based ownership (not individual names), which is more resilient to team changes — matching the edge case in the spec about ownership during team restructures.

**Alternatives Considered**:
- **CODEOWNERS file**: Rejected — GitHub CODEOWNERS is for automated review assignment, not documentation ownership tracking. Different purpose.
- **Inline ownership comments in each doc file**: Rejected — harder to maintain, not centrally discoverable, duplicates information.

---

## R5: Architecture Decision Record Process

**Task**: Evaluate whether the existing ADR infrastructure meets FR-008 and FR-009 requirements.

**Decision**: The existing `docs/decisions/` directory with its README.md template and 6 existing ADRs fully satisfies FR-008 and FR-009. The quarterly audit checklist will reference this directory.

**Rationale**: FR-009 requires ADRs to follow the Context-Decision-Consequences format. The existing ADR directory already has a README.md that establishes the template, and 6 ADRs (001–006) that follow consistent formatting. FR-008 requires the quarterly audit to verify ADR completeness — this is a process check implemented via the quarterly audit checklist, not a tooling change. No new infrastructure is needed; the quarterly checklist will include a step to review whether architectural decisions from the quarter have corresponding ADRs.

**Alternatives Considered**:
- **ADR tooling (adr-tools, log4brains)**: Rejected — YAGNI. The existing manual markdown ADR process works well for the project's scale. Tooling adds dependency complexity without proportional benefit.
- **ADR format migration**: Rejected — existing ADRs already follow a consistent format. Mandating a specific template would require retroactive changes without adding value.
