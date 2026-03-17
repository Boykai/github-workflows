# Contract: Shared Instructions File Changes

**Feature**: 051-agent-config-cleanup

This document defines the change contracts for `.github/agents/copilot-instructions.md`.

---

## Contract 1: Add Failure and Degradation Guidance Section

**File**: `.github/agents/copilot-instructions.md`
**Type**: MODIFY — add new section after "Validation Expectations"
**Priority**: P2 (User Story 4)

### New Section Content

Insert after the `## Validation Expectations` section (and its bullet points), before `## Frontend Pattern Notes`:

```markdown
## Failure and Degradation Guidance

When operating in environments where tools or context may be unavailable, follow these guidelines:

### MCP Server Unavailability
- If an MCP server (Context7, CodeGraphContext, Azure MCP) fails to start or respond, continue without it. Use alternative approaches: direct file reading, grep-based search, or official documentation lookup.
- Log a brief warning noting which MCP server was unavailable and what fallback was used.
- Do not block the entire workflow for a single MCP failure.

### Missing Context (PR Diff, Branch Info)
- If PR context is unavailable (e.g., running locally without a PR), switch to Local mode and work from the current branch changes.
- If branch information is unavailable, explicitly ask the user for scope before proceeding.
- Never assume the full repository is in scope when context is missing.

### Repeated Terminal Command Failures
- If a terminal command fails, retry once with the same parameters.
- If it fails again, try with verbose or debug flags to get more diagnostic output.
- After 3 consecutive failures of the same command, stop retrying, report the failure clearly to the user, and continue with other tasks that do not depend on the failing command.
- Do not silently swallow errors or claim success when commands fail.
```

### Position

After `## Validation Expectations` and its content (currently ending at the flaky test note on approximately line 181), before `## Frontend Pattern Notes` (currently approximately line 183).

### Validation

- Section exists with the exact heading `## Failure and Degradation Guidance`
- Three subsections present: MCP Server Unavailability, Missing Context, Repeated Terminal Command Failures
- No existing sections are modified or displaced
- File remains valid markdown

---

## Contract 2: Document $ARGUMENTS Convention

**File**: `.github/agents/copilot-instructions.md`
**Type**: MODIFY — add subsection to `## Custom Agents` section
**Priority**: P3 (User Story 6)

### New Subsection Content

Insert after the `### MCP Configuration` subsection and before `## MCP Presets`:

```markdown
### Agent Input Convention (`$ARGUMENTS`)

Every agent definition includes a `$ARGUMENTS` block near the top of its markdown body:

```text
## User Input

\```text
$ARGUMENTS
\```

You **MUST** consider the user input before proceeding (if not empty).
```

This is a project convention — `$ARGUMENTS` is a placeholder that GitHub replaces with the user's input when invoking the agent. All new agent definitions MUST include this block to ensure user input is processed. The block should appear early in the agent body (after the opening description, before execution phases) so the agent considers user input before starting work.
```

### Position

After the `### MCP Configuration` subsection (currently approximately line 215), before `## MCP Presets` (currently approximately line 217).

### Validation

- Subsection exists with heading `### Agent Input Convention (`$ARGUMENTS`)`
- Contains explanation of what `$ARGUMENTS` is, where to place it, and why it exists
- No existing sections are modified
- File remains valid markdown

---

## Contract 3: Document Invocability Evaluation

**File**: `.github/agents/copilot-instructions.md`
**Type**: MODIFY — add brief note to `## Custom Agents` section
**Priority**: P3 (User Story 5)

### New Content

Insert as a paragraph after the Utility Agents table and before `### MCP Configuration`:

```markdown
> **Invocability**: All utility agents use default settings (both user-invocable and model-invocable). This was evaluated in feature 051-agent-config-cleanup and determined appropriate — every agent serves legitimate direct-invocation and auto-selection use cases. No `user-invocable` or `disable-model-invocation` overrides are needed.
```

### Position

After the Utility Agents table (currently approximately line 213), before `### MCP Configuration` (currently approximately line 214).

### Validation

- Blockquote paragraph exists documenting the invocability decision
- References feature 051 for traceability
- No existing content is modified
- File remains valid markdown
