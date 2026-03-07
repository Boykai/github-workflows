# Implementation Plan: Recurring Documentation Update Process

**Branch**: `027-doc-sweep` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/027-doc-sweep/spec.md`

## Summary

Establish a recurring documentation update process that keeps all project documentation accurate, complete, and helpful. The implementation adds a PR-level documentation checklist to the GitHub PR template (currently missing), creates structured checklists for weekly staleness sweeps, monthly full reviews, and quarterly architecture audits, and ensures the existing CI markdown linting and link validation pipeline covers all required files. Documentation ownership is already tracked in `docs/OWNERS.md`. The feature is primarily process-oriented — delivering markdown checklists, a PR template, and minor CI configuration refinements — with no backend/frontend code changes required.

## Technical Context

**Language/Version**: Markdown (documentation), YAML (GitHub Actions CI), Node.js 20 (CI tooling runtime)
**Primary Dependencies**: markdownlint-cli 0.48.0 (already in CI), markdown-link-check 3.14.2 (already in CI)
**Storage**: N/A — all artifacts are markdown files committed to the repository
**Testing**: CI-based markdown linting and link checking (already configured in `.github/workflows/ci.yml`)
**Target Platform**: GitHub repository (PR templates, CI workflows, markdown documentation)
**Project Type**: Web application (frontend/ + backend/) — but this feature affects only documentation and CI configuration, not application code
**Performance Goals**: Weekly sweep completable in ≤30 minutes (SC-002); monthly review completable in 2–3 hours; CI lint/link checks complete within existing CI budget
**Constraints**: No new CI dependencies beyond what is already installed; no changes to application code; PR template must be compatible with GitHub's native PR template system
**Scale/Scope**: 1 new PR template, 4 review checklists (weekly/monthly/quarterly/PR-level), minor CI config updates, ~10 documentation files in scope for review cadence

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 18 functional requirements (FR-001–FR-018), 10 success criteria, and 8 edge cases |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not mandated in spec; this feature is process/documentation-oriented with CI checks serving as the validation mechanism. Existing CI tests unaffected. |
| **V. Simplicity/DRY** | ✅ PASS | Leverages existing CI infrastructure (markdownlint, markdown-link-check already in ci.yml), existing OWNERS.md, existing ADR directory. No new abstractions or tooling. |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-018) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing CI checks serve as validation |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing markdownlint config, link-check config, OWNERS.md, ADR directory. No unnecessary tooling or abstractions. Checklists are standalone markdown — the simplest possible format. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/027-doc-sweep/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R5)
├── data-model.md        # Phase 1: Entity definitions (Documentation File, Checklist, ADR, Ownership)
├── quickstart.md        # Phase 1: Developer onboarding guide for documentation process
├── contracts/
│   ├── pr-template.md   # Phase 1: PR template contract with documentation checklist
│   ├── checklists.md    # Phase 1: Weekly/monthly/quarterly checklist contracts
│   └── ci-config.md     # Phase 1: CI workflow configuration contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
.github/
├── pull_request_template.md       # NEW: PR template with documentation checklist (FR-001, FR-002)
└── workflows/
    └── ci.yml                     # MODIFIED: Expand docs lint scope to cover all *.md files (FR-010)

docs/
├── OWNERS.md                      # EXISTS: Documentation ownership mapping (FR-013) — may need minor updates
├── checklists/                    # NEW directory
│   ├── weekly-sweep.md            # NEW: Weekly staleness sweep checklist (FR-003, FR-004)
│   ├── monthly-review.md          # NEW: Monthly full documentation review checklist (FR-005–FR-007)
│   └── quarterly-audit.md         # NEW: Quarterly architecture audit checklist (FR-008, FR-009)
├── decisions/                     # EXISTS: ADR directory with 6 records — no changes needed
│   └── README.md                  # EXISTS: ADR template and index
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

.markdownlint.json                 # EXISTS: May need minor rule additions
.markdown-link-check.json          # EXISTS: No changes expected
.pre-commit-config.yaml            # EXISTS: No changes for this feature (CI handles linting)
```

**Structure Decision**: This feature is process/documentation-oriented and does not modify application source code. All deliverables are markdown files (checklists, PR template) and minor CI configuration changes. The existing web application structure (frontend/ + backend/) is unaffected. New checklist files are placed in `docs/checklists/` to keep them discoverable alongside the documentation they govern.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Checklists as standalone markdown in `docs/checklists/` | Simple, discoverable, version-controlled; no tooling required to use them | GitHub Issues templates (rejected: checklists are internal process docs, not issue templates) |
| PR template at `.github/pull_request_template.md` | GitHub's native single-file PR template — simplest approach | Multiple PR templates in `.github/PULL_REQUEST_TEMPLATE/` (rejected: YAGNI — one template sufficient for documentation checklist) |
| CI scope expansion via glob patterns | Extends existing `docs` job to cover `*.md` at repo root (currently only `docs/**/*.md` + `README.md`) | Separate workflow for markdown linting (rejected: DRY — existing `docs` job already runs the same tools) |
