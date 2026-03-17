# Implementation Plan: Non-Speckit Agent Definitions — Improvement Opportunities

**Branch**: `051-agent-config-cleanup` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/051-agent-config-cleanup/spec.md`

## Summary

Clean up the 7 non-speckit agent definition files (Architect, Archivist, Designer, Judge, Linter, Quality Assurance, Tester) in `.github/agents/`. The changes are configuration-only — no application code, no database changes, no build artifacts. Specifically: (1) add `tools: ["*"]` to all 7 agent YAML frontmatters to grant explicit full tool access, (2) remove unsupported `handoffs` blocks from the 5 agents that declare them, (3) rewrite validation sections in the 5 affected agents to instruct direct command execution instead of referencing a Linter handoff, (4) add shared failure/degradation guidance to `copilot-instructions.md` covering MCP unavailability, missing context, and repeated command failures, (5) document the evaluation of `user-invocable`/`disable-model-invocation` settings, and (6) document the `$ARGUMENTS` convention in the shared instructions file. Research confirms: `tools` field is the correct mechanism per GitHub's custom agent spec; all 7 agents should remain at default invocability settings; degradation guidance belongs in the shared instructions to avoid duplication.

## Technical Context

**Language/Version**: Markdown + YAML frontmatter (agent definition files); no compiled languages
**Primary Dependencies**: GitHub Custom Agent specification (YAML frontmatter fields: `name`, `description`, `tools`, `mcp-servers`)
**Storage**: N/A — all changes are to static configuration files
**Testing**: Manual verification — inspect YAML frontmatter, grep for removed keywords, validate markdown structure
**Target Platform**: GitHub Custom Agents (remote agent execution environment), VS Code Agent Mode (local)
**Project Type**: Configuration-only (agent definitions + shared instructions)
**Performance Goals**: N/A — no runtime behavior changes
**Constraints**: Must not break existing agent functionality; must preserve all MCP server declarations; must not modify speckit agents (out of scope)
**Scale/Scope**: 7 agent definition files modified, 1 shared instructions file modified, 0 application code files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Specification-First | PASS | `spec.md` created with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, edge cases, and explicit scope boundaries |
| II. Template-Driven | PASS | Using canonical `plan-template.md`; all artifacts in `specs/051-agent-config-cleanup/` |
| III. Agent-Orchestrated | PASS | Plan produced by `/speckit.plan`; tasks will follow via `/speckit.tasks` |
| IV. Test Optionality | PASS | No automated tests required — changes are to static markdown/YAML configuration files. Verification is via grep/inspection |
| V. Simplicity / DRY | PASS | Degradation guidance is shared in `copilot-instructions.md` (DRY) rather than duplicated across 7 agents. All changes are minimal edits to existing files — no new abstractions |
| Branch/Dir Naming | PASS | `051-agent-config-cleanup` follows `###-short-name` pattern |
| Phase-Based Execution | PASS | Specify → Plan (this) → Tasks → Implement |
| Independent User Stories | PASS | US-1 (tools field), US-2 (remove handoffs), US-3 (rewrite validation), US-4 (degradation guidance), US-5 (invocability eval), US-6 ($ARGUMENTS docs) are all independently implementable |

No violations. No complexity-tracking entries required.

### Post-Design Re-evaluation

| Principle | Status | Notes |
|---|---|---|
| I. Specification-First | PASS | Research resolved all items; no spec amendments needed |
| II. Template-Driven | PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | PASS | Phase handoff from plan → tasks is clean |
| IV. Test Optionality | PASS | Configuration-only changes; manual verification sufficient |
| V. Simplicity / DRY | PASS | Shared degradation clause avoids 7× duplication; `tools: ["*"]` is the simplest possible grant; validation rewrites are minimal text changes |

## Project Structure

### Documentation (this feature)

```text
specs/051-agent-config-cleanup/
├── plan.md              # This file
├── research.md          # Phase 0 output — 5 research topics resolved
├── data-model.md        # Phase 1 output — entity descriptions (agent file structure)
├── quickstart.md        # Phase 1 output — step-by-step implementation guide
├── contracts/           # Phase 1 output
│   ├── agent-frontmatter.md   # YAML frontmatter change contracts for all 7 agents
│   └── shared-instructions.md # copilot-instructions.md change contracts
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
.github/
├── agents/
│   ├── architect.agent.md           # MODIFY: Add tools field to frontmatter
│   ├── archivist.agent.md           # MODIFY: Add tools, remove handoffs, rewrite validation
│   ├── designer.agent.md            # MODIFY: Add tools, remove handoffs, rewrite validation
│   ├── judge.agent.md               # MODIFY: Add tools, remove handoffs (no validation section to rewrite)
│   ├── linter.agent.md              # MODIFY: Add tools field to frontmatter
│   ├── quality-assurance.agent.md   # MODIFY: Add tools, remove handoffs, rewrite validation
│   ├── tester.agent.md              # MODIFY: Add tools, remove handoffs, rewrite validation
│   └── copilot-instructions.md      # MODIFY: Add degradation guidance, $ARGUMENTS docs, invocability notes
```

**Structure Decision**: Configuration-only. All changes are edits to existing files in `.github/agents/`. No new files created outside the `specs/` documentation directory. No application code, frontend, or backend changes.

## Complexity Tracking

> No violations. No entries required.

All changes are minimal edits to existing YAML frontmatter and markdown body sections. No new dependencies, no new abstractions, no new files outside documentation.
