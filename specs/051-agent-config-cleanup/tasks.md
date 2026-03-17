# Tasks: Non-Speckit Agent Definitions — Improvement Opportunities

**Input**: Design documents from `/specs/051-agent-config-cleanup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No automated tests required — all changes are to static markdown/YAML configuration files. Verification is via grep/inspection per the quickstart checklist.

**Organization**: Tasks are grouped by user story to enable independent implementation and verification of each story. All changes target `.github/agents/` files only.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project type**: Configuration-only (agent definitions + shared instructions)
- **Agent files**: `.github/agents/<name>.agent.md`
- **Shared instructions**: `.github/agents/copilot-instructions.md`

## Phase 1: Setup

**Purpose**: No project initialization needed — all changes are edits to existing files in `.github/agents/`. This phase is a no-op.

- [ ] T001 Verify all 7 agent definition files exist in `.github/agents/` (architect, archivist, designer, judge, linter, quality-assurance, tester)
- [ ] T002 [P] Verify `copilot-instructions.md` exists at `.github/agents/copilot-instructions.md` and note current section structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No blocking infrastructure is needed. All user stories operate on independent files or independent sections within files. Proceed directly to user story implementation.

**⚠️ NOTE**: User Story 3 (validation rewrites) depends on User Story 2 (handoff removal) being complete first. All other stories are fully independent.

**Checkpoint**: No foundational work required — user story implementation can begin immediately.

---

## Phase 3: User Story 1 — Agents Have Full Tool Access (Priority: P1) 🎯 MVP

**Goal**: Add `tools: ["*"]` to the YAML frontmatter of all 7 non-speckit agent definition files so agents have explicit, deterministic access to all built-in tools (read, search, edit, execute, agent, web).

**Independent Test**: Run `grep -c "^tools:" .github/agents/*.agent.md` and confirm all 7 agent files return a match. Verify the `tools:` block contains `- '*'` in each file.

### Implementation for User Story 1

- [ ] T003 [P] [US1] Add `tools:` block with `- '*'` after `description:` field in `.github/agents/architect.agent.md`
- [ ] T004 [P] [US1] Add `tools:` block with `- '*'` after `description:` field in `.github/agents/archivist.agent.md`
- [ ] T005 [P] [US1] Add `tools:` block with `- '*'` after `description:` field in `.github/agents/designer.agent.md`
- [ ] T006 [P] [US1] Add `tools:` block with `- '*'` after `description:` field in `.github/agents/judge.agent.md`
- [ ] T007 [P] [US1] Add `tools:` block with `- '*'` after `description:` field in `.github/agents/linter.agent.md`
- [ ] T008 [P] [US1] Add `tools:` block with `- '*'` after `description:` field in `.github/agents/quality-assurance.agent.md`
- [ ] T009 [P] [US1] Add `tools:` block with `- '*'` after `description:` field in `.github/agents/tester.agent.md`
- [ ] T010 [US1] Verify: each of the 7 `.github/agents/*.agent.md` files contains a top-level `tools:` field with `- '*'` in the YAML frontmatter (between `description:` and `mcp-servers:`)

**Checkpoint**: All 7 agents now declare explicit full tool access. YAML frontmatter is valid. No other fields modified.

---

## Phase 4: User Story 2 — Dead Handoff Configuration Removed (Priority: P1)

**Goal**: Remove all unsupported `handoffs:` blocks from the YAML frontmatter of the 5 agents that declare them. This eliminates dead configuration and resolves the Judge agent's copy-paste bug.

**Independent Test**: Run `grep -r "handoffs:" .github/agents/*.agent.md` and confirm zero results. Verify all other frontmatter fields (name, description, tools, mcp-servers) remain intact.

### Implementation for User Story 2

- [ ] T011 [P] [US2] Remove entire `handoffs:` block (label, agent, prompt, send) from YAML frontmatter in `.github/agents/archivist.agent.md`
- [ ] T012 [P] [US2] Remove entire `handoffs:` block from YAML frontmatter in `.github/agents/designer.agent.md`
- [ ] T013 [P] [US2] Remove entire `handoffs:` block (includes copy-paste bug) from YAML frontmatter in `.github/agents/judge.agent.md`
- [ ] T014 [P] [US2] Remove entire `handoffs:` block from YAML frontmatter in `.github/agents/quality-assurance.agent.md`
- [ ] T015 [P] [US2] Remove entire `handoffs:` block from YAML frontmatter in `.github/agents/tester.agent.md`
- [ ] T016 [US2] Verify: `grep -r "handoffs:" .github/agents/*.agent.md` returns 0 results
- [ ] T017 [US2] Verify: all 5 modified files retain correct `name`, `description`, `tools`, and `mcp-servers` fields in frontmatter

**Checkpoint**: Zero agent files contain handoff declarations. Judge copy-paste bug is moot. All other configuration preserved.

---

## Phase 5: User Story 3 — Validation Sections Rewritten for Direct Execution (Priority: P1)

**Goal**: Rewrite validation sections in the 5 affected agents so they instruct the agent to run linting, tests, and type-checks directly via terminal access, rather than referencing a Linter handoff. The Judge agent requires no body change (no validation section exists).

**Independent Test**: Run `grep -ri "handoff\|hand off" .github/agents/archivist.agent.md .github/agents/designer.agent.md .github/agents/judge.agent.md .github/agents/quality-assurance.agent.md .github/agents/tester.agent.md` and confirm zero results. Read each validation section and confirm it contains explicit shell commands.

**Dependency**: Requires Phase 4 (US2) complete — handoff blocks must be removed before validation sections are rewritten to avoid conflicting references.

### Implementation for User Story 3

- [ ] T018 [P] [US3] Rewrite `## Validation` section in `.github/agents/archivist.agent.md` — replace passive "run the most relevant validation" with explicit documentation and backend/frontend terminal commands per Contract 3
- [ ] T019 [P] [US3] Rewrite `## Validation` section in `.github/agents/designer.agent.md` — replace passive validation text with explicit frontend terminal commands and visual validation checklist per Contract 4
- [ ] T020 [P] [US3] Rewrite `### 6. Validate the Changes` section in `.github/agents/tester.agent.md` — replace passive validation text with explicit backend/frontend terminal commands per Contract 5
- [ ] T021 [P] [US3] Add new `## Validation` section before `## Output Requirements` in `.github/agents/quality-assurance.agent.md` with explicit backend/frontend terminal commands per Contract 7
- [ ] T022 [US3] Verify: `grep -ri "handoff\|hand off" .github/agents/archivist.agent.md .github/agents/designer.agent.md .github/agents/judge.agent.md .github/agents/quality-assurance.agent.md .github/agents/tester.agent.md` returns 0 results
- [ ] T023 [US3] Verify: each rewritten section contains actual shell commands (ruff, pyright, pytest, npm run lint, etc.)

**Checkpoint**: All 5 affected agents instruct direct validation. No references to handoffs remain in any agent body. Judge agent unchanged (no validation section needed per Contract 6).

---

## Phase 6: User Story 4 — Failure and Degradation Guidance (Priority: P2)

**Goal**: Add shared failure/degradation guidance to `copilot-instructions.md` covering the 3 most common failure modes: MCP server unavailability, missing context (PR diff, branch info), and repeated terminal command failures. All 7 agents inherit this guidance via the shared instructions file.

**Independent Test**: Run `grep "Failure and Degradation" .github/agents/copilot-instructions.md` and confirm 1 match. Verify the section contains 3 subsections (MCP, Missing Context, Terminal Failures).

### Implementation for User Story 4

- [ ] T024 [US4] Add `## Failure and Degradation Guidance` section to `.github/agents/copilot-instructions.md` after `## Validation Expectations` and before `## Frontend Pattern Notes`, with 3 subsections per Contract 1: MCP Server Unavailability, Missing Context (PR Diff, Branch Info), Repeated Terminal Command Failures
- [ ] T025 [US4] Verify: section exists with 3 subsections and no existing sections are displaced or modified

**Checkpoint**: All 7 agents now have shared degradation guidance. The Architect's existing Azure MCP-specific guidance remains as an agent-level override.

---

## Phase 7: User Story 5 — Invocability Controls Evaluated (Priority: P3)

**Goal**: Document the evaluation of `user-invocable` and `disable-model-invocation` settings for all 7 agents. Per research (Topic 5), all agents should remain at defaults — no frontmatter changes needed, only documentation of the decision.

**Independent Test**: Confirm a blockquote in `copilot-instructions.md` documents the invocability decision with rationale referencing feature 051.

### Implementation for User Story 5

- [ ] T026 [US5] Add invocability evaluation blockquote after the Utility Agents table and before `### MCP Configuration` in `.github/agents/copilot-instructions.md` per Contract 3
- [ ] T027 [US5] Verify: blockquote exists documenting that all 7 agents remain at default invocability settings with rationale

**Checkpoint**: Invocability decision is documented. No frontmatter changes needed. Decision is traceable to feature 051.

---

## Phase 8: User Story 6 — $ARGUMENTS Convention Documented (Priority: P3)

**Goal**: Document the `$ARGUMENTS` convention in the shared instructions file so new contributors understand this project-specific pattern and can follow it when creating agents.

**Independent Test**: Run `grep "ARGUMENTS" .github/agents/copilot-instructions.md` and confirm matches showing the documented convention with explanation of purpose, placement, and usage.

### Implementation for User Story 6

- [ ] T028 [US6] Add `### Agent Input Convention ($ARGUMENTS)` subsection after `### MCP Configuration` and before `## MCP Presets` in `.github/agents/copilot-instructions.md` per Contract 2 — include explanation of what `$ARGUMENTS` is, where to place it, and why it exists
- [ ] T029 [US6] Verify: subsection exists with heading, explanation, and code example showing the `$ARGUMENTS` block pattern

**Checkpoint**: `$ARGUMENTS` convention is documented. New contributors can find and follow the pattern.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories

- [ ] T030 Validate all 7 agent YAML frontmatters parse correctly (no YAML syntax errors)
- [ ] T031 Validate `copilot-instructions.md` markdown structure is intact (no broken headings or displaced sections)
- [ ] T032 Run full verification checklist from quickstart.md: all grep checks pass, all sections present, no regressions
- [ ] T033 Confirm no speckit agents (out of scope) were modified

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verification only
- **Foundational (Phase 2)**: No blocking prerequisites for this config-only feature
- **US1 — Tools (Phase 3)**: Independent — can start immediately
- **US2 — Handoffs (Phase 4)**: Independent — can start immediately, can run in parallel with US1
- **US3 — Validation Rewrites (Phase 5)**: **Depends on US2 (Phase 4)** — handoff blocks must be removed before validation sections are rewritten
- **US4 — Degradation (Phase 6)**: Independent — can start immediately, can run in parallel with US1/US2/US3
- **US5 — Invocability (Phase 7)**: Independent — can start immediately
- **US6 — $ARGUMENTS (Phase 8)**: Independent — can start immediately, can run in parallel with US5
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories — purely additive YAML field
- **US2 (P1)**: No dependencies on other stories — purely subtractive YAML removal
- **US3 (P1)**: **Depends on US2** — cannot rewrite validation sections while handoff blocks still exist (would create conflicting guidance)
- **US4 (P2)**: No dependencies — shared instructions file is independent of agent frontmatter changes
- **US5 (P3)**: No dependencies — documentation-only addition to shared instructions
- **US6 (P3)**: No dependencies — documentation-only addition to shared instructions

### Within Each User Story

- All agent file modifications within a story are independent (different files) and marked [P]
- Verification tasks run after all modifications in the story are complete
- Each story can be independently validated after completion

### Parallel Opportunities

- **US1 + US2**: Can run fully in parallel (different YAML fields, no conflicts)
- **US4 + US5 + US6**: Can run fully in parallel (different sections in copilot-instructions.md)
- **Within US1**: All 7 agent modifications are independent [P] tasks
- **Within US2**: All 5 agent modifications are independent [P] tasks
- **Within US3**: All 4 validation rewrites are independent [P] tasks (different files)
- **US3 must wait for US2** (the only serial dependency between stories)

---

## Parallel Example: User Story 1

```bash
# Launch all 7 agent tools additions together (all [P]):
Task T003: "Add tools block in .github/agents/architect.agent.md"
Task T004: "Add tools block in .github/agents/archivist.agent.md"
Task T005: "Add tools block in .github/agents/designer.agent.md"
Task T006: "Add tools block in .github/agents/judge.agent.md"
Task T007: "Add tools block in .github/agents/linter.agent.md"
Task T008: "Add tools block in .github/agents/quality-assurance.agent.md"
Task T009: "Add tools block in .github/agents/tester.agent.md"
```

## Parallel Example: User Story 2

```bash
# Launch all 5 handoff removals together (all [P]):
Task T011: "Remove handoffs from .github/agents/archivist.agent.md"
Task T012: "Remove handoffs from .github/agents/designer.agent.md"
Task T013: "Remove handoffs from .github/agents/judge.agent.md"
Task T014: "Remove handoffs from .github/agents/quality-assurance.agent.md"
Task T015: "Remove handoffs from .github/agents/tester.agent.md"
```

## Parallel Example: Shared Instructions (US4 + US5 + US6)

```bash
# These target different sections of copilot-instructions.md and can be batched:
Task T024: "Add Failure and Degradation section"
Task T026: "Add invocability evaluation note"
Task T028: "Add $ARGUMENTS convention docs"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup verification
2. Complete Phase 3: US1 — Add `tools: ["*"]` to all 7 agents
3. Complete Phase 4: US2 — Remove handoffs from 5 agents
4. **STOP and VALIDATE**: All agents have explicit tool access, no dead configuration
5. This alone resolves the 2 highest-impact issues

### Incremental Delivery

1. US1 + US2 → Frontmatter is clean (MVP!)
2. Add US3 → Validation sections are actionable → Agents can self-validate
3. Add US4 → Degradation guidance → Agents handle failures gracefully
4. Add US5 + US6 → Documentation complete → Contributor onboarding improved
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. **Developer A**: US1 (tools field — 7 agents) + US3 (validation rewrites — 4 agents, after US2 merges)
2. **Developer B**: US2 (handoff removal — 5 agents) + US4 (degradation guidance — 1 file)
3. **Developer C**: US5 + US6 (documentation — both in copilot-instructions.md)
4. Stories complete and integrate independently

---

## Summary

| Metric | Count |
|---|---|
| **Total tasks** | 33 |
| **US1 tasks** (tools field) | 8 (7 parallel + 1 verify) |
| **US2 tasks** (handoff removal) | 7 (5 parallel + 2 verify) |
| **US3 tasks** (validation rewrites) | 6 (4 parallel + 2 verify) |
| **US4 tasks** (degradation guidance) | 2 |
| **US5 tasks** (invocability eval) | 2 |
| **US6 tasks** ($ARGUMENTS docs) | 2 |
| **Setup tasks** | 2 |
| **Polish tasks** | 4 |
| **Parallel opportunities** | 23 of 33 tasks are parallelizable |
| **Files modified** | 8 (7 agent files + 1 shared instructions) |
| **MVP scope** | US1 + US2 (Phases 3–4, 15 tasks) |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently verifiable via grep/inspection
- No automated tests needed — all changes are static configuration
- Commit after each phase or logical group
- Stop at any checkpoint to validate story independently
- The only cross-story dependency is US3 → US2 (validation rewrites require handoff removal first)
- Avoid: modifying speckit agents (out of scope), adding unnecessary YAML fields, removing non-handoff frontmatter
