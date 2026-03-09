# Implementation Plan: Recurring Documentation Update Process

**Branch**: `032-doc-sweep` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/032-doc-sweep/spec.md`

## Summary

Establish a comprehensive, recurring documentation update process that keeps all project documentation accurate, complete, and helpful across the full stack. The implementation delivers PR-level documentation checklists, structured review checklists for weekly/monthly/quarterly cadences, CI-enforced formatting and link validation, clear documentation ownership, and defined roles and responsibilities. This is the third iteration of the documentation sweep feature (succeeding `027-doc-sweep` and `030-doc-sweep`), with all six user stories: PR checks (P1), weekly sweeps (P1), monthly reviews (P2), quarterly architecture audits (P2), formatting standards enforcement (P3), and documentation ownership assignment (P3).

**Key finding**: The `027-doc-sweep` and `030-doc-sweep` features have already been implemented and merged. The existing repository includes a complete PR template with documentation checklist, three review checklists (`docs/checklists/`), CI markdown linting and link checking, `docs/OWNERS.md` with ownership mappings, and 6 ADRs in `docs/decisions/`. This `032-doc-sweep` plan builds upon that foundation, focusing on the new FR-021 requirement (formalizing the "good documentation" definition as an acceptance bar) and validating continued completeness against FR-001 through FR-021 and SC-001 through SC-010.

## Technical Context

**Language/Version**: Markdown (documentation), YAML (GitHub Actions CI), Node.js 20 (CI tooling runtime)
**Primary Dependencies**: markdownlint-cli 0.48.0 (already in CI), markdown-link-check 3.14.2 (already in CI)
**Storage**: N/A — all artifacts are markdown files committed to the repository
**Testing**: CI-based markdown linting and link checking (already configured in `.github/workflows/ci.yml`); pre-commit hooks (`.pre-commit-config.yaml`)
**Target Platform**: GitHub repository (PR templates, CI workflows, markdown documentation)
**Project Type**: Web application (frontend/ + backend/) — but this feature affects only documentation, CI configuration, and process artifacts; no application code changes
**Performance Goals**: Weekly sweep completable in ≤30 minutes (SC-002); monthly review in 2–3 hours; quarterly audit in ~half day; CI lint/link checks within existing CI budget
**Constraints**: No new CI dependencies beyond what is already installed; no changes to application code; PR template must be compatible with GitHub's native PR template system; no disruption to existing CI pipeline timing
**Scale/Scope**: 21 functional requirements (FR-001–FR-021), 10 success criteria (SC-001–SC-010), 6 user stories (P1–P3), ~15 documentation files in scope for review cadence, 3 review checklists, 1 PR template, 1 ownership file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios for each, 21 functional requirements (FR-001–FR-021), 10 success criteria (SC-001–SC-010), edge cases, and assumptions |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution: specify → plan → tasks → implement. Plan hands off to `/speckit.tasks` for Phase 2. |
| **IV. Test Optionality** | ✅ PASS | Tests not mandated in spec; this feature is process/documentation-oriented with CI checks serving as the validation mechanism. Existing CI tests are unaffected. No TDD approach needed. |
| **V. Simplicity/DRY** | ✅ PASS | Leverages existing CI infrastructure (markdownlint, markdown-link-check already in ci.yml), existing OWNERS.md, existing ADR directory, existing PR template, existing checklists. New work focuses on FR-021 gap and incremental validation. |

**Gate result**: PASS — no violations. Proceeding to Phase 0.

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-021). Research decisions reference specific requirements. |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 task generation |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing CI checks serve as validation. CI linting is the "test" for documentation quality. |
| **V. Simplicity/DRY** | ✅ PASS | Reuses all existing infrastructure. The only new content is the "good documentation" definition (FR-021) added to the governance location. Checklists remain standalone markdown — the simplest possible format. |

**Gate result**: PASS — no violations post-design.

## Project Structure

### Documentation (this feature)

```text
specs/032-doc-sweep/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0: Research decisions (R1–R6)
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Developer onboarding guide for documentation process
├── contracts/
│   ├── pr-template.md   # Phase 1: PR template contract with documentation checklist
│   ├── checklists.md    # Phase 1: Weekly/monthly/quarterly checklist contracts
│   └── ci-config.md     # Phase 1: CI workflow configuration contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (from speckit.specify)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
.github/
├── pull_request_template.md       # EXISTS: PR template with documentation checklist (FR-001, FR-002) — no changes needed
└── workflows/
    └── ci.yml                     # EXISTS: Docs lint job with markdownlint + markdown-link-check (FR-015, FR-016) — no changes needed

docs/
├── OWNERS.md                      # EXISTS: Documentation ownership mapping (FR-017, FR-018, FR-019) — add FR-021 good documentation definition
├── checklists/
│   ├── weekly-sweep.md            # EXISTS: Weekly staleness sweep (FR-003–FR-006) — no changes needed
│   ├── monthly-review.md          # EXISTS: Monthly full review (FR-007–FR-010, FR-020) — verify FR-021 reference
│   └── quarterly-audit.md         # EXISTS: Quarterly audit (FR-011–FR-013) — no changes needed
├── decisions/                     # EXISTS: ADR directory with 6 records + README — no changes needed
│   └── README.md
├── setup.md                       # EXISTS: Subject to review cadence
├── configuration.md               # EXISTS: Subject to review cadence
├── api-reference.md               # EXISTS: Subject to review cadence
├── architecture.md                # EXISTS: Subject to review cadence
├── agent-pipeline.md              # EXISTS: Subject to review cadence
├── custom-agents-best-practices.md # EXISTS: Subject to review cadence
├── signal-integration.md          # EXISTS: Subject to review cadence
├── testing.md                     # EXISTS: Subject to review cadence
├── troubleshooting.md             # EXISTS: Subject to review cadence
└── project-structure.md           # EXISTS: Subject to review cadence

.markdownlint.json                 # EXISTS: Markdown formatting rules (FR-014) — no changes needed
.markdown-link-check.json          # EXISTS: Link validation config (FR-016) — no changes needed
.pre-commit-config.yaml            # EXISTS: Pre-commit hooks with markdownlint — no changes needed
```

**Structure Decision**: This feature is process/documentation-oriented and does not modify application source code. All deliverables are markdown files (checklists, PR template) and the "good documentation" definition addition to `docs/OWNERS.md`. The existing web application structure (frontend/ + backend/) is unaffected. The `027-doc-sweep` and `030-doc-sweep` implementations have created the foundational infrastructure; this iteration validates completeness against the 032 requirements and addresses the FR-021 gap.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Build on 027/030-doc-sweep foundation | Existing infrastructure covers FR-001–FR-020; incremental gap-fill is simpler than rebuilding | Full rewrite of all documentation artifacts (rejected: violates DRY) |
| Add good documentation definition to OWNERS.md | Central governance file already contains ownership + cadence; keeps all doc governance in one place | Standalone STANDARDS.md (rejected: another file to maintain; definition is short) |
| No new CI tooling (vale deferred) | markdownlint + markdown-link-check cover FR-015 and FR-016; vale is a P3 "consider" item | Adding vale immediately (rejected: YAGNI — spec says "consider", not "must") |
