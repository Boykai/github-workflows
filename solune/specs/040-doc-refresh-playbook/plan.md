# Implementation Plan: Recurring Documentation Refresh Playbook

**Branch**: `040-doc-refresh-playbook` | **Date**: 2026-03-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/040-doc-refresh-playbook/spec.md`

## Summary

A bi-weekly documentation refresh process that detects what changed in the application (via CHANGELOG, specs, and code diffs), determines how the app's focus has shifted, and rewrites README + `docs/` to stay accurate. The playbook is organized into six phases: change detection, focus shift prioritization, README update, individual docs update, cross-reference validation, and verification with baseline recording. Research confirms the approach is viable using standard git CLI tools, line-based CHANGELOG parsing, and a JSON baseline file at `docs/.last-refresh`. The process is initially manual (~3–4 hours per cycle) with a clear automation path for change manifest generation and link validation after 2–3 manual cycles. This feature introduces no code changes — only documentation process artifacts and a single JSON metadata file.

## Technical Context

**Language/Version**: Bash (shell scripts for git commands, `grep`, `find`), Markdown (all documentation)
**Primary Dependencies**: Git CLI, `jq` (for JSON baseline parsing), `grep`/`find` (POSIX utilities), `scripts/generate-diagrams.sh` (existing Mermaid diagram generator)
**Storage**: `docs/.last-refresh` (JSON file committed to repository) — stores refresh baseline (date, SHA, update history)
**Testing**: Manual verification via `docs/checklists/weekly-sweep.md` checklist; automated internal link validation via `grep`; scope verification via `git diff --stat`
**Target Platform**: Any Unix-like environment with Git (developer workstation, CI runner)
**Project Type**: Web application (frontend + backend) — this feature modifies only documentation, not source code
**Performance Goals**: Full refresh cycle completable within 4 hours (SC-001)
**Constraints**: Zero code changes — `git diff --stat` must show only `docs/`, `README.md`, `CHANGELOG.md` modifications (SC-005); must complement (not replace) existing weekly/monthly/quarterly checklists (FR-019)
**Scale/Scope**: 11 documentation files + README, each mapped to specific source-of-truth files; 5 Mermaid diagram files; 3 checklist files; bi-weekly cadence

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅

Feature spec (`spec.md`) includes 6 prioritized user stories (P1–P3) with independent testing criteria and Given-When-Then acceptance scenarios. Scope boundaries are explicit — code changes are out of scope, automation is deferred to post-manual-validation cycles, and this complements rather than replaces existing checklists.

### II. Template-Driven Workflow ✅

All artifacts follow canonical templates: `plan.md` (this file), `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`. No custom sections added beyond what the template prescribes.

### III. Agent-Orchestrated Execution ✅

Plan phase produces well-defined outputs (research, data model, contracts, quickstart) that feed into the tasks phase. The six-phase playbook structure has clear inputs (previous phase outputs) and produces specific outputs (Change Manifest, Priority Assignments, updated docs, baseline record).

### IV. Test Optionality with Clarity ✅

This feature is a documentation process — no code is written, so no unit/integration tests are applicable. Validation is performed through the existing weekly sweep checklist (manual), automated link checking (`grep`), and scope verification (`git diff --stat`). These validation steps are built into the playbook itself (Phase 6).

### V. Simplicity and DRY ✅

The playbook uses standard Unix tools (`git`, `grep`, `find`, `jq`) and existing repository scripts (`generate-diagrams.sh`). No new abstractions, frameworks, or dependencies are introduced. The JSON baseline format is the simplest viable approach for storing cycle metadata. The documentation-to-source mapping is a static 11-row table, not an over-engineered registry.

**Gate Result**: PASS — all constitution principles satisfied. No violations requiring justification.

### Post-Design Re-evaluation ✅

After completing Phase 1 design artifacts:

- **I. Specification-First**: Research resolved all unknowns (8 research tasks). Data model defines 5 entities matching the spec's key entities.
- **II. Template-Driven**: All artifacts follow canonical templates. Contracts cover the three main process phases (detection, update, verification).
- **III. Agent-Orchestrated**: Clear handoff chain: research → data model → contracts → quickstart → tasks (next phase).
- **IV. Test Optionality**: Confirmed — no tests needed. Validation is process-internal.
- **V. Simplicity**: No complexity violations. All decisions favor the simplest viable approach.

**Post-Design Gate Result**: PASS — no new violations introduced during design.

## Project Structure

### Documentation (this feature)

```text
specs/040-doc-refresh-playbook/
├── plan.md                          # This file
├── research.md                      # Phase 0 output — resolved unknowns and best practices
├── data-model.md                    # Phase 1 output — entity definitions for refresh workflow
├── quickstart.md                    # Phase 1 output — step-by-step refresh guide
├── contracts/                       # Phase 1 output — process contracts
│   ├── change-detection.md          # Three-source change detection contract
│   ├── documentation-update.md      # Per-document update process contract
│   └── verification-baseline.md     # Verification steps and baseline recording contract
├── checklists/
│   └── requirements.md              # Spec quality checklist (pre-existing)
└── tasks.md                         # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
docs/
├── .last-refresh                    # NEW: Refresh baseline JSON file (FR-017)
├── api-reference.md                 # Updated per refresh cycle
├── architecture.md                  # Updated per refresh cycle
├── agent-pipeline.md                # Updated per refresh cycle
├── configuration.md                 # Updated per refresh cycle
├── custom-agents-best-practices.md  # Updated per refresh cycle
├── project-structure.md             # Updated per refresh cycle
├── testing.md                       # Updated per refresh cycle
├── troubleshooting.md               # Updated per refresh cycle
├── setup.md                         # Updated per refresh cycle
├── signal-integration.md            # Updated per refresh cycle (conditional)
├── OWNERS.md                        # Updated if new docs created
├── architectures/                   # Mermaid diagrams (regenerated if architecture changed)
│   ├── high-level.mmd
│   ├── deployment.mmd
│   ├── frontend-components.mmd
│   ├── backend-components.mmd
│   └── data-flow.mmd
├── checklists/
│   ├── weekly-sweep.md              # Used as final validation pass
│   ├── monthly-review.md
│   └── quarterly-audit.md
└── decisions/
    └── README.md                    # ADR index (updated if new ADRs found)

README.md                            # Updated per refresh cycle (when P0)
CHANGELOG.md                         # Refresh entry added per cycle
scripts/generate-diagrams.sh         # Existing script invoked for diagram regeneration
```

**Structure Decision**: This feature operates on existing documentation files — no new source code directories or modules are created. The only new file introduced is `docs/.last-refresh` (a JSON metadata file). All other files listed above already exist in the repository and are updated in-place during each refresh cycle.

## Complexity Tracking

> No constitution violations detected. This section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
