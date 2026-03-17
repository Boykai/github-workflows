# Feature Specification: Non-Speckit Agent Definitions — Improvement Opportunities

**Feature Branch**: `051-agent-config-cleanup`  
**Created**: 2026-03-17  
**Status**: Draft  
**Input**: User description: "Non-Speckit Agent Definitions — Improvement Opportunities"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Agents Have Full Tool Access (Priority: P1)

As a developer invoking a custom agent (Architect, Archivist, Designer, Judge, Linter, Quality Assurance, or Tester), I expect the agent to have access to all built-in tools (read, search, edit, execute, agent, web) so it can perform its work without hitting silent capability gaps.

**Why this priority**: Without explicit tool declarations, agents rely on implicit defaults that may not include all necessary tools. This is the simplest change with the broadest impact — it unblocks every other improvement by ensuring agents can execute commands, read files, and search code.

**Independent Test**: Can be verified by inspecting each of the 7 agent definition files and confirming the YAML frontmatter includes a `tools` field granting full access.

**Acceptance Scenarios**:

1. **Given** any of the 7 non-speckit agent definition files, **When** a reviewer inspects the YAML frontmatter, **Then** a `tools` field is present granting access to all built-in tool aliases.
2. **Given** a developer invokes one of the 7 agents, **When** the agent needs to read files, search code, edit files, or run terminal commands, **Then** it can do so without capability restrictions.

---

### User Story 2 — Dead Handoff Configuration Removed (Priority: P1)

As a maintainer of the agent definitions, I want all unsupported `handoffs` blocks removed from agent frontmatters so the configuration is clean, accurate, and does not mislead contributors into thinking sub-agent handoffs are supported.

**Why this priority**: Five of the 7 agents declare `handoffs` in YAML frontmatter, but custom GitHub agents do not support sub-agent handoffs. This is dead configuration that creates confusion and a false sense of automation. Removing it is a prerequisite for rewriting validation sections (User Story 3).

**Independent Test**: Can be verified by inspecting the YAML frontmatter of all 7 agent files and confirming no `handoffs` key exists in any of them.

**Acceptance Scenarios**:

1. **Given** the Archivist, Designer, Judge, Quality Assurance, or Tester agent definition file, **When** a reviewer inspects the YAML frontmatter, **Then** no `handoffs` block is present.
2. **Given** the Architect or Linter agent definition file (which currently have no handoffs), **When** a reviewer inspects the YAML frontmatter, **Then** no `handoffs` block is present.
3. **Given** the Judge agent definition file, **When** the copy-paste bug in the handoff prompt is checked, **Then** it is moot because the entire handoff block has been removed.

---

### User Story 3 — Validation Sections Rewritten for Direct Execution (Priority: P1)

As a developer relying on agents for code quality, I want the agents' validation instructions to tell the agent to run linting, tests, and type-checks directly (using terminal access) rather than referencing a handoff to the Linter agent, so that validation actually executes.

**Why this priority**: With handoffs removed (User Story 2), any instruction sections that reference handing off to Linter for validation become orphaned. Agents must be told explicitly to run validation commands themselves. Without this, agents will skip validation entirely.

**Independent Test**: Can be verified by reading the markdown body of each affected agent and confirming that validation sections instruct the agent to execute lint, test, and type-check commands directly rather than referencing a Linter handoff.

**Acceptance Scenarios**:

1. **Given** the Archivist, Designer, Judge, Quality Assurance, or Tester agent definition file, **When** a reviewer reads the validation-related sections, **Then** the instructions tell the agent to run validation commands itself (e.g., run linters, tests, type-checks via terminal).
2. **Given** any of the 5 affected agent definition files, **When** a reviewer searches for the word "handoff" or "hand off," **Then** no references to handing off to another agent for validation are found.
3. **Given** an agent executes its workflow, **When** it reaches the validation step, **Then** it runs the validation commands directly rather than attempting to delegate to another agent.

---

### User Story 4 — Failure and Degradation Guidance (Priority: P2)

As an agent operating in an environment where external services or tools may be unavailable, I need clear guidance on what to do when things fail (MCP servers down, context unavailable, terminal commands failing repeatedly) so that I degrade gracefully rather than producing errors or incomplete results.

**Why this priority**: Currently only the Architect agent has degradation guidance (for Azure MCP unavailability). The other 6 agents have no instructions for common failure modes. This gap means agents may hang, produce errors, or silently skip critical steps when infrastructure issues occur.

**Independent Test**: Can be verified by reading each agent's definition (or the shared instructions file) and confirming failure/degradation guidance exists for the most likely failure modes.

**Acceptance Scenarios**:

1. **Given** any of the 7 agent definition files or the shared instructions file, **When** a reviewer looks for failure-handling guidance, **Then** guidance is present for at least these scenarios: MCP server unavailability, missing context (PR diff, branch info), and repeated terminal command failures.
2. **Given** an agent encounters an MCP server that fails to start, **When** it checks its instructions, **Then** it finds clear guidance on how to proceed (e.g., skip MCP-dependent steps, warn the user, use alternative approaches).
3. **Given** an agent's terminal command (lint, test, build) fails repeatedly, **When** it checks its instructions, **Then** it finds guidance on maximum retry attempts and how to report the failure to the user.

---

### User Story 5 — Invocability Controls Evaluated (Priority: P3)

As a project maintainer, I want to evaluate whether each agent should be restricted via `user-invocable` and `disable-model-invocation` settings, so that agents intended only for pipeline use are not accidentally triggered by users or auto-selected by the model.

**Why this priority**: All 7 agents currently default to being both user-invocable and model-invocable. While this is acceptable for most agents, some may benefit from restrictions. This is a low-risk evaluation with clear documentation outcomes.

**Independent Test**: Can be verified by confirming that a documented decision exists for each agent regarding its invocability settings, and that any decided restrictions are reflected in the agent frontmatter.

**Acceptance Scenarios**:

1. **Given** the project's agent documentation, **When** a reviewer looks for invocability decisions, **Then** a documented rationale exists for each of the 7 agents explaining whether it should be user-invocable, model-invocable, both, or neither.
2. **Given** an agent determined to need restricted invocability, **When** a reviewer inspects its YAML frontmatter, **Then** the appropriate `user-invocable` or `disable-model-invocation` field is set.
3. **Given** an agent determined to remain at default settings, **When** a reviewer inspects its YAML frontmatter, **Then** no unnecessary invocability fields clutter the configuration.

---

### User Story 6 — $ARGUMENTS Convention Documented (Priority: P3)

As a new contributor creating or modifying agents, I need the `$ARGUMENTS` pattern documented in the shared instructions so I understand this project-specific convention and can follow it consistently.

**Why this priority**: Every agent body includes a `$ARGUMENTS` block, but this convention is not documented anywhere. New contributors will not know to include it when creating agents, leading to inconsistency.

**Independent Test**: Can be verified by checking the shared instructions file for a section explaining the `$ARGUMENTS` convention, its purpose, and usage guidance.

**Acceptance Scenarios**:

1. **Given** the shared instructions file (e.g., `copilot-instructions.md`), **When** a new contributor reads the custom agents section, **Then** they find documentation explaining the `$ARGUMENTS` convention.
2. **Given** the `$ARGUMENTS` documentation, **When** a contributor reads it, **Then** they understand: what `$ARGUMENTS` represents, where to place it in agent definitions, and why it exists.

---

### Edge Cases

- What happens if an agent definition file has other undocumented YAML frontmatter fields beyond `handoffs`? Only `handoffs` should be removed; other fields should be left untouched unless explicitly addressed.
- What happens if the shared instructions file (`copilot-instructions.md`) does not exist or has a different structure? The degradation guidance and `$ARGUMENTS` documentation should be added in a way that fits the existing file structure, or a new section should be created.
- What happens if an agent's validation section is deeply intertwined with other instructions? The rewrite should preserve non-validation instructions and only modify the validation-related content.
- What happens if a future GitHub update adds support for agent handoffs? The specification documents the current state. If handoffs become supported, the decision should be revisited, but the dead configuration should still be removed now to prevent confusion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each of the 7 non-speckit agent definition files (Architect, Archivist, Designer, Judge, Linter, Quality Assurance, Tester) MUST include a `tools` field in its YAML frontmatter granting access to all built-in tool aliases.
- **FR-002**: All `handoffs` blocks MUST be removed from the YAML frontmatter of every agent definition file that currently contains one (Archivist, Designer, Judge, Quality Assurance, Tester).
- **FR-003**: Markdown body sections in agent definition files that reference handing off to the Linter agent for validation MUST be rewritten to instruct the agent to perform validation directly (run lint, tests, type-checks via terminal).
- **FR-004**: The rewritten validation sections MUST contain no references to "handoff," "hand off," or delegating validation to another agent.
- **FR-005**: Failure and degradation guidance MUST be added for all 7 agents, covering at minimum: MCP server unavailability, missing context (PR diff, branch info), and repeated terminal command failures.
- **FR-006**: The degradation guidance SHOULD be implemented as a shared clause in the common instructions file to avoid duplication, with per-agent overrides only where agent-specific failure modes exist.
- **FR-007**: A documented decision MUST exist for each of the 7 agents regarding `user-invocable` and `disable-model-invocation` settings, with rationale for each.
- **FR-008**: The `$ARGUMENTS` convention MUST be documented in the shared instructions file, explaining its purpose, placement, and usage in agent definitions.
- **FR-009**: All changes MUST preserve existing agent functionality — agents must continue to perform their defined roles correctly after modifications.
- **FR-010**: The Judge agent's copy-paste bug (handoff prompt referencing "quality-assurance changes" instead of "judge changes") MUST be resolved by removing the entire handoff block.

### Key Entities

- **Agent Definition File**: A markdown file in `.github/agents/` with YAML frontmatter and markdown body instructions. Contains the agent's name, description, tool access, and behavioral instructions.
- **YAML Frontmatter**: The metadata block at the top of each agent definition file, enclosed in `---` delimiters. Controls agent configuration such as name, description, tools, and (currently unsupported) handoffs.
- **Shared Instructions File**: The project-wide instructions file (`copilot-instructions.md`) that provides common guidance to all agents.
- **Validation Section**: The portion of an agent's markdown body that instructs it on how to verify its work (run linting, tests, type-checks).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the 7 non-speckit agent definition files include a `tools` field in YAML frontmatter granting full tool access.
- **SC-002**: 0 agent definition files contain a `handoffs` block in their YAML frontmatter.
- **SC-003**: 0 agent definition files contain references to handing off validation to another agent in their markdown body.
- **SC-004**: 100% of the 5 affected agents (Archivist, Designer, Judge, QA, Tester) have validation sections that explicitly instruct the agent to run lint, tests, and type-checks directly.
- **SC-005**: Failure/degradation guidance is present and covers at least 3 failure modes (MCP unavailability, missing context, repeated command failures) for all 7 agents.
- **SC-006**: A documented invocability decision exists for each of the 7 agents.
- **SC-007**: The `$ARGUMENTS` convention is documented in the shared instructions file.
- **SC-008**: All 7 agents continue to perform their defined roles correctly after modifications — no functional regressions.

## Assumptions

- The 7 agents analyzed are the complete set of non-speckit agents in the repository. If additional agents exist, they are out of scope for this specification.
- `tools: ["*"]` is the correct syntax for granting full tool access per GitHub's custom agent spec. If the syntax differs, the implementation should use the correct format.
- The shared instructions file is `copilot-instructions.md` (or equivalent). If it is located elsewhere or named differently, the implementation should target the correct file.
- The Architect agent's existing degradation guidance is a good model for the pattern to follow across other agents.
- Speckit agents (e.g., `speckit.implement`, `speckit.specify`) are explicitly out of scope for this feature, including the `name` field inconsistency noted in the parent issue.
- All 7 agents should remain both user-invocable and model-invocable at default settings unless the evaluation (FR-007) identifies a specific reason to restrict any agent. The default assumption is no restrictions needed.
