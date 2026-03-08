# Research: Recurring Documentation Update Process

**Feature**: 030-doc-sweep | **Date**: 2026-03-08

## R1: Gap Analysis — 027-doc-sweep vs 030-doc-sweep Requirements

**Task**: Determine what was already implemented by `027-doc-sweep` and what gaps remain against the expanded `030-doc-sweep` requirements (FR-001 through FR-020).

**Decision**: The `027-doc-sweep` implementation covers the majority of requirements. Specific gaps exist in FR-019 (cadence schedule documentation), FR-020 (troubleshooting format enforcement), and completeness of the quarterly audit checklist (FR-011–FR-013).

**Rationale**: A systematic comparison of the 20 functional requirements against the current repository state reveals:

| Requirement | Status | Gap |
|-------------|--------|-----|
| FR-001 (PR template checklist) | ✅ Implemented | None — `.github/pull_request_template.md` has all 6 checklist items |
| FR-002 (No doc changes option) | ✅ Implemented | None — template includes "confirmed not needed — explain below" with rationale field |
| FR-003 (Weekly sweep checklist) | ✅ Implemented | None — `docs/checklists/weekly-sweep.md` exists |
| FR-004 (Weekly: API endpoint comparison) | ✅ Implemented | Verify checklist explicitly requires comparing route files to API reference entries |
| FR-005 (Weekly: env var comparison) | ✅ Implemented | Verify checklist explicitly requires comparing config source to docs |
| FR-006 (Weekly: prerequisite version check) | ✅ Implemented | Verify checklist explicitly requires matching manifest versions |
| FR-007 (Monthly review checklist) | ✅ Implemented | None — `docs/checklists/monthly-review.md` exists |
| FR-008 (Monthly: cross-reference check) | ✅ Implemented | Verify checklist includes internal link validation |
| FR-009 (Monthly: code snippet validation) | ✅ Implemented | Verify checklist includes code snippet correctness check |
| FR-010 (Monthly: readability standards) | ✅ Implemented | Verify checklist includes purpose statements, numbered lists, table formats |
| FR-011 (Quarterly audit checklist) | ✅ Implemented | None — `docs/checklists/quarterly-audit.md` exists |
| FR-012 (Quarterly: ADR completeness) | ✅ Implemented | Verify checklist includes ADR review with Context → Decision → Consequences format |
| FR-013 (Quarterly: DX test) | ⚠️ Verify | Verify checklist includes developer experience test (fresh setup walkthrough) |
| FR-014 (Formatting standards) | ✅ Implemented | `.markdownlint.json` enforces ATX headings, code block formatting |
| FR-015 (CI formatting enforcement) | ✅ Implemented | `ci.yml` docs job runs markdownlint on `docs/**/*.md` and `*.md` |
| FR-016 (CI link checking) | ✅ Implemented | `ci.yml` docs job runs markdown-link-check on all `docs/**/*.md` and `README.md` |
| FR-017 (Ownership file exists) | ✅ Implemented | `docs/OWNERS.md` exists with comprehensive mapping |
| FR-018 (Single owner per file) | ✅ Implemented | Each file has exactly one owner; rotation explicitly marked |
| FR-019 (Cadence schedule) | ✅ Implemented | `docs/OWNERS.md` includes Review Cadence table |
| FR-020 (Troubleshooting format) | ⚠️ Verify | Verify `docs/troubleshooting.md` follows Symptom → Cause → Fix format |

**Conclusion**: The 027-doc-sweep implementation is comprehensive. The 030 plan should focus on verification and any incremental refinements needed to fully satisfy FR-001–FR-020, particularly validating the quarterly audit checklist (FR-013) and troubleshooting format (FR-020).

**Alternatives Considered**:

- **Full reimplementation**: Rejected — would duplicate existing work and violate DRY principle.
- **Skip 030 entirely**: Rejected — the expanded spec adds valuable structure (6 user stories, 10 success criteria) that the 027 implementation didn't explicitly validate against.

---

## R2: PR Template Completeness

**Task**: Verify the existing PR template at `.github/pull_request_template.md` fully satisfies FR-001 and FR-002.

**Decision**: The existing PR template is fully compliant. No changes needed.

**Rationale**: The current template includes:

- ✅ Endpoint documentation checklist item (FR-001)
- ✅ Environment variable documentation checklist item (FR-001)
- ✅ Startup/Docker/prerequisites checklist item (FR-001)
- ✅ Agent/workflow/AI provider checklist item (FR-001)
- ✅ Schema/data model checklist item (FR-001)
- ✅ "Documentation updated (or confirmed not needed — explain below)" (FR-002)
- ✅ "Doc files updated" field with rationale prompt (FR-002)

The template also includes Type of Change and Testing sections, providing a comprehensive PR workflow.

**Alternatives Considered**:

- **Add more granular checklist items**: Rejected — the current 6-item checklist covers all major documentation categories without being overly prescriptive.

---

## R3: Weekly Sweep Checklist Completeness

**Task**: Verify the weekly sweep checklist covers FR-003 through FR-006.

**Decision**: The existing `docs/checklists/weekly-sweep.md` covers all weekly sweep requirements. Verify during implementation that each specific comparison (route files vs API reference, config source vs docs, manifest versions vs setup guide) is explicitly called out.

**Rationale**: FR-004 requires comparison of "documented API endpoints against actual codebase route files." FR-005 requires comparison of "documented environment variables against actual configuration source." FR-006 requires verification of "prerequisite versions in setup guide match actual project manifests." The weekly sweep checklist must be specific enough that a developer on rotation can complete it in ~30 minutes without needing to interpret vague instructions.

**Alternatives Considered**:

- **Automated weekly sweep script**: Rejected — YAGNI for this iteration. A script that compares route files to API docs would be valuable but is out of scope for a process-focused feature. Could be a future enhancement.

---

## R4: Quarterly Audit Checklist and ADR Process

**Task**: Verify the quarterly audit checklist meets FR-011 through FR-013, particularly the developer experience test and ADR completeness requirements.

**Decision**: The existing `docs/checklists/quarterly-audit.md` should be verified to include: (1) service topology verification against Docker Compose, (2) ADR review with explicit Context → Decision → Consequences format check, (3) developer experience test where a team member follows setup from scratch, and (4) documentation gaps analysis for features shipped in the quarter.

**Rationale**: FR-012 specifically requires ADRs to follow the "Context → Decision → Consequences format." The existing `docs/decisions/` directory has 6 ADRs and a README template. FR-013 requires a "developer experience test where a team member follows the setup guide from scratch and documents friction points." This is a process step in the checklist, not a tooling change. The quarterly audit is the most comprehensive review and must cover architecture accuracy, decision records, developer onboarding, and coverage gaps.

**Alternatives Considered**:

- **Automated architecture diagram generation**: Rejected — requires tooling beyond scope; manual verification against Docker Compose is sufficient.
- **ADR tooling (adr-tools, log4brains)**: Rejected — YAGNI. Manual markdown ADRs are working well at current scale (6 decisions).

---

## R5: Formatting Standards and CI Enforcement

**Task**: Verify that existing CI configuration and `.markdownlint.json` adequately enforce FR-014 (formatting standards) and FR-015/FR-016 (CI enforcement).

**Decision**: The existing CI configuration is sufficient. The `.markdownlint.json` config enforces dash-style lists, and the CI docs job runs markdownlint on `docs/**/*.md` and `*.md`. The `markdown-link-check` config handles link validation with retry logic and timeout handling.

**Rationale**: FR-014 requires: ATX-style headings (enforced by markdownlint MD003 default), language-specified code blocks (can be enforced by MD040 rule), tables for structured data (process convention, not machine-enforceable), numbered lists for sequential steps (process convention), and inline code for filenames (process convention). FR-015 requires CI enforcement, which is already in place via `ci.yml`. FR-016 requires broken link detection, which is handled by `markdown-link-check` in CI.

The `.markdownlint.json` currently has permissive settings (MD013 line length disabled, MD033 inline HTML allowed, MD041 first-line heading not required). These are appropriate for the project's documentation style. One potential enhancement: enable MD040 (fenced-code-language) to enforce language tags on code blocks, but this should be verified against existing docs first to avoid breaking CI.

**Alternatives Considered**:

- **Add vale for prose linting**: Spec says "consider vale" (P3). Deferred — markdownlint covers formatting; vale adds prose style checks (passive voice, tone) that are lower priority.
- **Stricter markdownlint rules**: Rejected — current permissive config is appropriate for the project's documentation style and avoids false positives.

---

## R6: Documentation Ownership and Cadence

**Task**: Verify `docs/OWNERS.md` satisfies FR-017 through FR-019 and the documentation ownership user story.

**Decision**: The existing `docs/OWNERS.md` is fully compliant. It maps every documentation file to a designated owner role, indicates rotating ownership where applicable, and includes a review cadence table.

**Rationale**: FR-017 requires a documentation ownership file listing every documentation file and its designated owner. FR-018 requires each file to have exactly one designated owner or a clearly defined rotation scheme. FR-019 requires a cadence schedule specifying frequency and trigger for each review type. The current `docs/OWNERS.md` satisfies all three:

- 15 file-to-owner mappings covering all `docs/` files, checklists, decisions, and frontend docs
- Rotation explicitly marked for `troubleshooting.md` and `weekly-sweep.md`
- Review cadence table with 4 entries (Every PR, Weekly, Monthly, Quarterly)

**Alternatives Considered**:

- **GitHub CODEOWNERS file**: Rejected — CODEOWNERS is for automated PR review assignment, not documentation ownership tracking. Different purpose and audience.
- **Inline ownership headers in each doc**: Rejected — not centrally discoverable, harder to maintain, duplicates information.
