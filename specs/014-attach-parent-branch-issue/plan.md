# Implementation Plan: Attach Parent Branch to GitHub Issue Upon Branch Creation

**Branch**: `014-attach-parent-branch-issue` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-attach-parent-branch-issue/spec.md`

## Summary

Add a GitHub Actions workflow (`.github/workflows/branch-issue-link.yml`) that listens for branch `create` events, parses the branch name to extract a GitHub Issue number, and automatically posts a comment on that issue linking the branch. The workflow handles idempotency (no duplicate comments), graceful degradation (warnings for unrecognized branches, non-existent/closed issues), and transient failure retries with exponential backoff.

## Technical Context

**Language/Version**: YAML (GitHub Actions workflow), Bash (inline shell scripts)
**Primary Dependencies**: GitHub Actions, `gh` CLI (pre-installed on GitHub-hosted runners)
**Storage**: N/A
**Testing**: Manual testing via branch creation; `actionlint` for workflow syntax validation
**Target Platform**: GitHub Actions (ubuntu-latest runners)
**Project Type**: single (one workflow file, no application code changes)
**Performance Goals**: Branch-to-issue link posted within 2 minutes of branch creation (SC-001)
**Constraints**: Must use `GITHUB_TOKEN` (no PATs or GitHub Apps); must work on all GitHub plan tiers
**Scale/Scope**: Single workflow file (~80-120 lines of YAML); single repository scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md exists with 4 prioritized user stories (P1–P3), acceptance scenarios, and scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase follows single-responsibility agent model; outputs are well-defined markdown documents |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are not explicitly requested in the spec; manual testing via branch creation is sufficient. `actionlint` can validate workflow syntax. No automated test infrastructure needed. |
| V. Simplicity and DRY | ✅ PASS | Single workflow file with inline bash; no external dependencies beyond `gh` CLI; no abstractions or shared libraries. YAGNI applied — no configurable patterns, no cross-repo support. |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/014-attach-parent-branch-issue/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Workflow data model
├── quickstart.md        # Phase 1: Developer quickstart
├── contracts/           # Phase 1: Workflow contract
│   └── branch-issue-link-workflow.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT this phase)
```

### Source Code (repository root)

```text
.github/
└── workflows/
    ├── ci.yml                    # Existing CI pipeline
    └── branch-issue-link.yml    # NEW: Branch-to-issue linking workflow
```

**Structure Decision**: This feature adds a single GitHub Actions workflow file. No application code (backend/frontend) is modified. The workflow lives alongside the existing `ci.yml` in `.github/workflows/`.

## Complexity Tracking

> No constitution violations to justify. All principles are satisfied.

## Constitution Re-Check (Post Phase 1 Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All design artifacts trace back to spec.md requirements; every FR is addressed in the workflow contract |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow canonical structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produced well-defined outputs for handoff to tasks phase |
| IV. Test Optionality with Clarity | ✅ PASS | No automated tests required; manual testing guide provided in quickstart.md; `actionlint` recommended for syntax validation |
| V. Simplicity and DRY | ✅ PASS | Single workflow file with no external dependencies; regex parsing in bash; `gh` CLI for GitHub API interaction; no unnecessary abstractions |

**Post-Design Gate Result**: ✅ ALL PASS — ready for Phase 2 (tasks generation via `/speckit.tasks`).
