# Research: Recurring Documentation Update Process

**Feature**: 032-doc-sweep | **Date**: 2026-03-09

## R1: Gap Analysis — Existing Infrastructure vs 032-doc-sweep Requirements

**Task**: Determine what is already implemented in the repository and what gaps remain against the 032-doc-sweep requirements (FR-001 through FR-021).

**Decision**: The repository has a mature documentation infrastructure established by previous iterations (`027-doc-sweep`, `030-doc-sweep`). FR-001 through FR-020 are fully covered by existing artifacts. FR-021 (definition of "good documentation") requires a new section in the documentation or checklists to formalize the acceptance bar.

**Rationale**: A systematic comparison of the 21 functional requirements against the current repository state:

| Requirement | Status | Gap |
|-------------|--------|-----|
| FR-001 (PR template checklist) | ✅ Implemented | None — `.github/pull_request_template.md` has all 6 checklist items |
| FR-002 (No doc changes option) | ✅ Implemented | None — template includes "confirmed not needed — explain below" with rationale field |
| FR-003 (Weekly sweep checklist) | ✅ Implemented | None — `docs/checklists/weekly-sweep.md` exists |
| FR-004 (Weekly: API endpoint comparison) | ✅ Implemented | Checklist explicitly requires comparing route files to API reference entries |
| FR-005 (Weekly: env var comparison) | ✅ Implemented | Checklist explicitly requires comparing config source to docs |
| FR-006 (Weekly: prerequisite version check) | ✅ Implemented | Checklist explicitly requires matching manifest versions |
| FR-007 (Monthly review checklist) | ✅ Implemented | None — `docs/checklists/monthly-review.md` exists |
| FR-008 (Monthly: cross-reference check) | ✅ Implemented | Checklist includes internal link validation |
| FR-009 (Monthly: code snippet validation) | ✅ Implemented | Checklist includes code snippet correctness check |
| FR-010 (Monthly: readability standards) | ✅ Implemented | Checklist includes purpose statements, numbered lists, table formats |
| FR-011 (Quarterly audit checklist) | ✅ Implemented | None — `docs/checklists/quarterly-audit.md` exists |
| FR-012 (Quarterly: ADR completeness) | ✅ Implemented | Checklist includes ADR review with Context → Decision → Consequences format |
| FR-013 (Quarterly: DX test) | ✅ Implemented | Checklist includes developer experience test (fresh setup walkthrough) |
| FR-014 (Formatting standards) | ✅ Implemented | `.markdownlint.json` enforces ATX headings, code block formatting |
| FR-015 (CI formatting enforcement) | ✅ Implemented | `ci.yml` docs job runs markdownlint on `docs/**/*.md` and `*.md` |
| FR-016 (CI link checking) | ✅ Implemented | `ci.yml` docs job runs markdown-link-check on all `docs/**/*.md` and `README.md` |
| FR-017 (Ownership file exists) | ✅ Implemented | `docs/OWNERS.md` exists with comprehensive mapping |
| FR-018 (Single owner per file) | ✅ Implemented | Each file has exactly one owner; rotation explicitly marked |
| FR-019 (Cadence schedule) | ✅ Implemented | `docs/OWNERS.md` includes Review Cadence table |
| FR-020 (Troubleshooting format) | ✅ Implemented | `docs/troubleshooting.md` follows Symptom → Cause → Fix format |
| FR-021 (Good documentation definition) | ⚠️ Gap | Definition exists in issue description but is not yet formalized in the repository documentation or checklists |

**Conclusion**: The existing infrastructure is comprehensive. The primary gap is FR-021 — formalizing the definition of "good documentation" (accurate, minimal, actionable, discoverable, maintained) as an explicit acceptance bar applied during all review phases.

**Alternatives Considered**:

- **Full reimplementation**: Rejected — would duplicate existing work and violate DRY principle
- **Skip 032 entirely**: Rejected — the expanded spec adds FR-021 and refines success criteria wording; the plan provides incremental value by validating completeness and addressing the remaining gap

---

## R2: FR-021 — Good Documentation Definition Placement

**Task**: Determine the best location to formalize the "good documentation" definition so it is applied as the acceptance bar for all review phases.

**Decision**: Add a "Definition of Good Documentation" section to `docs/OWNERS.md` (which already serves as the central documentation governance file) and reference it from each review checklist.

**Rationale**: The definition of "good documentation" is a governance concept — it defines the acceptance bar for review outcomes. `docs/OWNERS.md` already contains ownership mappings and the review cadence table, making it the natural home for documentation quality standards. Adding the definition there keeps all governance in one place (DRY principle). Each checklist can then reference it with a link rather than duplicating the criteria.

The five criteria from the spec are:

1. **Accurate** — Every step, command, variable, and path matches the current codebase
2. **Minimal** — No redundant content; each fact appears in exactly one place
3. **Actionable** — Readers can accomplish the documented task without needing to read source code
4. **Discoverable** — The correct doc is easy to find from the README or table of contents
5. **Maintained** — Last-reviewed date is within the current quarter

**Alternatives Considered**:

- **Standalone `docs/STANDARDS.md` file**: Rejected — creates another file to maintain; the standards are short enough to live in OWNERS.md alongside governance rules
- **Embed in each checklist**: Rejected — violates DRY; the definition would need updating in 3+ places when amended
- **Add to README.md**: Rejected — README focuses on project overview and getting started; governance belongs in OWNERS.md

---

## R3: PR Template Completeness Verification

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

**Alternatives Considered**:

- **Add more granular checklist items**: Rejected — the current 6-item checklist covers all major documentation categories without being overly prescriptive

---

## R4: CI Enforcement Verification

**Task**: Verify that existing CI configuration adequately enforces FR-014 (formatting standards), FR-015 (CI linting), and FR-016 (link checking).

**Decision**: The existing CI configuration is fully compliant. No changes needed.

**Rationale**: The `.markdownlint.json` config enforces ATX-style headings (MD003 via `"default": true`), language-specified code blocks (MD040 via `"default": true`), and dash-style lists (MD004 explicitly). The CI `docs` job runs markdownlint on `docs/**/*.md` + `*.md` and markdown-link-check on `docs/**/*.md` + `README.md`. Pre-commit hooks mirror CI scope.

**Alternatives Considered**:

- **Add vale for prose linting**: Spec says "consider vale" (P3). Deferred — markdownlint covers formatting; vale adds prose style checks that are lower priority
- **Stricter markdownlint rules**: Rejected — current permissive config (no line length, allow inline HTML) is appropriate for the project's documentation style

---

## R5: Review Checklist Completeness Verification

**Task**: Verify all three review checklists cover their respective functional requirements.

**Decision**: All three checklists are compliant with their requirements. The quarterly audit checklist includes the developer experience test (FR-013) and ADR format check (FR-012).

**Rationale**: Cross-referencing each checklist against its requirements:

- **Weekly sweep** (`docs/checklists/weekly-sweep.md`): Covers FR-003 through FR-006 — API reference comparison, configuration comparison, setup guide version check
- **Monthly review** (`docs/checklists/monthly-review.md`): Covers FR-007 through FR-010 plus FR-020 — accuracy/completeness/consistency audit, cross-reference validation, code snippet correctness, readability standards, troubleshooting format
- **Quarterly audit** (`docs/checklists/quarterly-audit.md`): Covers FR-011 through FR-013 — architecture verification, ADR completeness with Context → Decision → Consequences format, developer experience test, docs gaps analysis

**Alternatives Considered**:

- **Automated weekly sweep script**: Rejected — YAGNI for this iteration. A script comparing route files to API docs would be valuable but is out of scope for a process-focused feature

---

## R6: Documentation Ownership Verification

**Task**: Verify `docs/OWNERS.md` satisfies FR-017 through FR-019.

**Decision**: The existing `docs/OWNERS.md` is fully compliant. It maps every documentation file to a designated owner role, indicates rotating ownership where applicable, and includes a review cadence table.

**Rationale**: FR-017 requires a documentation ownership file listing every documentation file and its designated owner. FR-018 requires each file to have exactly one designated owner or a clearly defined rotation scheme. FR-019 requires a cadence schedule specifying frequency and trigger for each review type. The current `docs/OWNERS.md` satisfies all three with 15 file-to-owner mappings and a review cadence table covering PR-level, weekly, monthly, and quarterly cadences.

**Alternatives Considered**:

- **GitHub CODEOWNERS file**: Rejected — CODEOWNERS is for automated PR review assignment, not documentation ownership tracking. Different purpose and audience
- **Inline ownership headers in each doc**: Rejected — not centrally discoverable, harder to maintain, duplicates information
