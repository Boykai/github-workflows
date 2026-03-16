# Implementation Plan: UI Audit Issue Template

**Branch**: `045-ui-audit` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/045-ui-audit/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Review and merge the GitHub issue template for **UI Audit** — a reusable checklist that standardises page-level audits across the Solune frontend. The template (`.github/ISSUE_TEMPLATE/chore-ui-audit.md`) already exists in the repository and provides ten audit categories with 59+ checklist items, a six-phase implementation guide, a relevant-files reference section, and verification commands. The implementation work is a review-and-merge chore: validate the template content against the specification requirements (FR-001 through FR-012), confirm all placeholder mechanics work, and ensure the template is selectable from GitHub's "New Issue" page with the correct title, labels, and body.

## Technical Context

**Language/Version**: Markdown (GitHub-Flavoured Markdown for issue templates)
**Primary Dependencies**: GitHub Issues infrastructure (issue template YAML front matter)
**Storage**: N/A — the template is a static `.md` file in `.github/ISSUE_TEMPLATE/`
**Testing**: Manual validation — create an issue from the template and verify the rendered output
**Target Platform**: GitHub.com issue tracker (browser-based)
**Project Type**: Single (repository configuration file)
**Performance Goals**: N/A — static template file, no runtime performance concerns
**Constraints**: Template must conform to GitHub issue template format (YAML front matter + Markdown body). No external dependencies. Template must be generic enough to apply to any page in the application (FR-007, SC-007)
**Scale/Scope**: 1 file (`.github/ISSUE_TEMPLATE/chore-ui-audit.md`), ~200 lines of Markdown. 10 audit categories, 59+ checklist items, 6 implementation phases, 1 relevant-files section, 1 verification section

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate (Phase 0)

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | `spec.md` exists with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, edge cases, and explicit in/out-of-scope boundaries |
| II | Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III | Agent-Orchestrated Execution | ✅ PASS | Single-responsibility agent (`speckit.plan`) producing well-defined outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md) |
| IV | Test Optionality with Clarity | ✅ PASS | Tests are not explicitly mandated in the spec. This is a static Markdown template — validation is manual (create issue, verify output). No automated tests required |
| V | Simplicity and DRY | ✅ PASS | Single-file deliverable (issue template). No abstraction needed. Placeholder-based design (`[PAGE_NAME]`, `[feature]`) enables reuse without template modification (SC-007) |
| — | Branch & Directory Naming | ✅ PASS | `045-ui-audit` follows `###-short-name` convention |
| — | Phase-Based Execution | ✅ PASS | Specify (complete) → Plan (current) → Tasks → Implement → Analyze |
| — | Independent User Stories | ✅ PASS | US1 (create from template) and US2 (track progress) are independently testable P1 stories. US3–US6 are P2/P3 enhancements |
| — | Constitution Supremacy | ✅ PASS | No conflicts between constitution and templates |
| — | Compliance Review | ✅ PASS | This section fulfils the compliance requirement |

**Gate Result**: ✅ ALL GATES PASS — Proceed to Phase 0.

### Post-Design Gate (Phase 1)

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | Research confirms template content satisfies all 12 FRs. No spec changes needed |
| II | Template-Driven Workflow | ✅ PASS | `research.md`, `data-model.md`, `contracts/`, `quickstart.md` all generated |
| III | Agent-Orchestrated Execution | ✅ PASS | Plan complete and aligned with the generated tasks/review artifacts |
| IV | Test Optionality with Clarity | ✅ PASS | No automated tests mandated. Manual verification steps documented in quickstart.md |
| V | Simplicity and DRY | ✅ PASS | Single Markdown file, no code, no dependencies, no abstraction layers |

**Gate Result**: ✅ ALL GATES PASS — Proceed to Phase 2 (task generation).

## Project Structure

### Documentation (this feature)

```text
specs/045-ui-audit/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/
│   └── template-contract.md  # Issue template format and content contract
├── checklists/
│   └── requirements.md  # Pre-existing checklist from specify phase
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
.github/
└── ISSUE_TEMPLATE/
    └── chore-ui-audit.md    # The UI Audit issue template (single deliverable)
```

**Structure Decision**: This feature is a single static Markdown file in the repository's `.github/ISSUE_TEMPLATE/` directory. No source code, no build artefacts, no runtime components. The entire deliverable is the issue template file itself, which is already present in the repository and requires review and merge.

## Complexity Tracking

> No constitution violations to justify. All gates pass.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | — | — |
