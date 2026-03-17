# Research: Non-Speckit Agent Definitions — Improvement Opportunities

> Researched 2026-03-17 against the live Solune codebase and GitHub Custom Agent documentation.

---

## Topic 1: GitHub Custom Agent `tools` Field — Syntax and Behavior

### Decision

Use `tools: ["*"]` in the YAML frontmatter of every agent definition file. This grants access to all built-in tool aliases (read, search, edit, execute, agent, web).

### Rationale

- Per GitHub's custom agent specification, the `tools` field controls which built-in tool aliases an agent can access. Without an explicit `tools` field, agents rely on platform-determined implicit defaults that may change.
- The wildcard `["*"]` syntax grants access to all available tools, which is appropriate for all 7 utility agents since they each require broad capabilities: reading files, searching code, editing files, executing terminal commands, and web access.
- None of the 7 agents currently declare `tools`, creating a gap where agents may silently lack capabilities. Making this explicit ensures deterministic behavior.
- The `tools` field is distinct from the `mcp-servers.*.tools` field (which controls per-MCP-server tool filtering). The top-level `tools` controls built-in agent tool access.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Per-agent selective tool lists (e.g., `["read", "execute"]`) | Over-constraining; all 7 agents need broad access. Adds maintenance burden without security benefit since agents are trusted internal tools |
| Omit `tools` entirely (rely on defaults) | Implicit defaults may change. Explicit declaration is defensive and self-documenting |
| Add `tools` only to agents that have gaps | Inconsistent; all agents should declare their capabilities for clarity |

### Implementation Details

Insert `tools: ["*"]` immediately after the `description` field (before any `handoffs` or `mcp-servers` block) in all 7 agent files. Example:

```yaml
---
name: Architect
description: Generates Azure IaC (Bicep)...
tools:
- '*'
mcp-servers:
  ...
---
```

Note: In YAML, `["*"]` is equivalent to the block sequence `- '*'`. Use the block sequence form to match the existing style of `mcp-servers.*.tools` entries.

---

## Topic 2: Handoffs — Unsupported by Custom GitHub Agents

### Decision

Remove all `handoffs` blocks from the YAML frontmatter of the 5 agents that declare them (Archivist, Designer, Judge, Quality Assurance, Tester). Replace the intended validation behavior with explicit instructions to run commands directly.

### Rationale

- Custom GitHub Agents do not support sub-agent handoffs. The `handoffs` field is dead configuration — it is parsed by the YAML parser but has no effect on agent behavior.
- All 5 handoffs target the Linter agent with prompts like "Run the relevant lint, type-check, test, and build validation for the {agent} changes." Since these never execute, validation is effectively skipped.
- The Judge agent's handoff contains a copy-paste bug: its prompt says "for the quality-assurance changes" instead of "for the judge changes." This confirms the handoffs were never tested or validated.
- Removing dead configuration reduces confusion and prevents new contributors from copying the pattern.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Keep handoffs for future compatibility | Dead config creates confusion now; re-adding is trivial if/when support arrives |
| Replace handoffs with a different delegation mechanism | No delegation mechanism exists for custom agents; direct execution is the only option |
| Only remove the Judge's buggy handoff | Inconsistent; all handoffs are equally dead |

### Implementation Details

Remove the entire `handoffs` block from each affected file's YAML frontmatter:

```yaml
# REMOVE THIS BLOCK (exact text varies slightly per agent)
handoffs:
- label: Run Validation
  agent: Linter
  prompt: Run the relevant lint, type-check, test, and build validation
    for the {agent} changes
  send: true
```

**Affected files**: `archivist.agent.md`, `designer.agent.md`, `judge.agent.md`, `quality-assurance.agent.md`, `tester.agent.md`

---

## Topic 3: Validation Section Rewrite Strategy

### Decision

Rewrite the validation sections in the 5 affected agents to explicitly instruct the agent to run validation commands itself using terminal access. The instructions should reference the project's actual validation commands from `copilot-instructions.md` and tell the agent to execute them directly.

### Rationale

- With `tools: ["*"]`, agents have full terminal access via the `execute` tool. They can run linters, tests, type-checks, and builds directly.
- The existing validation sections in Archivist, Designer, and Tester already describe *what* to validate (lint, type-check, test, build) but don't explicitly say "run these commands yourself." The language is passive: "Run the most relevant validation" without stating who runs it.
- The quality-assurance agent has validation mentioned in its output requirements but no dedicated validation section.
- The judge agent has no explicit validation section in its body.
- The rewritten sections should be concrete: reference the actual commands from the project's validation stack (ruff, pyright, pytest for backend; eslint, tsc, vitest for frontend) and tell the agent to execute them.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Remove validation sections entirely | Agents still need guidance on what to validate; removing would reduce quality |
| Add a shared validation script agents can call | Over-engineering; the commands are already documented in `copilot-instructions.md` |
| Only add "run it yourself" without specific commands | Vague; agents perform better with concrete command examples |

### Implementation Details

Replace each validation section with explicit instructions. Example pattern:

```markdown
## Validation

Run validation directly using terminal access. Execute the commands most relevant to the files you changed:

**Backend changes** (if applicable):
- `cd solune/backend && ruff check src/ tests/` — lint
- `cd solune/backend && ruff format --check src/ tests/` — format check
- `cd solune/backend && pyright src/` — type check
- `cd solune/backend && pytest tests/ -x -q` — run tests

**Frontend changes** (if applicable):
- `cd solune/frontend && npm run lint` — ESLint
- `cd solune/frontend && npm run type-check` — TypeScript check
- `cd solune/frontend && npm run test` — Vitest
- `cd solune/frontend && npm run build` — production build

**Documentation changes**:
- Verify markdown renders correctly
- Check internal links are valid
- Confirm code examples match the actual implementation
```

Adapt the specifics per agent (e.g., Archivist emphasizes doc validation, Designer emphasizes visual checks).

---

## Topic 4: Failure and Degradation Guidance — Shared vs. Per-Agent

### Decision

Add a shared "Failure and Degradation" section to `copilot-instructions.md` covering the 3 common failure modes: MCP server unavailability, missing context (PR diff, branch info), and repeated terminal command failures. This avoids duplicating the same guidance across 7 agent files.

### Rationale

- The Architect agent is the only agent with degradation guidance (for Azure MCP unavailability), but this is embedded in its agent-specific instructions because it's specific to Azure MCP.
- The 3 failure modes identified in the spec (MCP unavailability, missing context, repeated command failures) are common to ALL agents, not agent-specific.
- Placing shared guidance in `copilot-instructions.md` follows the DRY principle (Constitution V) and ensures consistency. All agents inherit from this shared file.
- Per-agent overrides are only needed when an agent has unique failure modes (e.g., Architect + Azure MCP). The shared clause handles the generic cases.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Add identical degradation sections to all 7 agent files | Violates DRY; 7× maintenance burden |
| Create a separate `failure-guidance.md` file | Over-engineering; `copilot-instructions.md` already serves as the shared config |
| Only add guidance to agents that use MCP | All agents face context unavailability and command failures, not just MCP issues |

### Implementation Details

Add a new section to `copilot-instructions.md` after the "Validation Expectations" section:

```markdown
## Failure and Degradation Guidance

When operating in environments where tools or context may be unavailable, follow these guidelines:

### MCP Server Unavailability
- If an MCP server (Context7, CodeGraphContext, Azure MCP) fails to start or respond, continue without it. Use alternative approaches: direct file reading, grep-based search, or web documentation lookup.
- Log a brief warning noting which MCP server was unavailable and what fallback was used.
- Do not block the entire workflow for a single MCP failure.

### Missing Context (PR Diff, Branch Info)
- If PR context is unavailable (e.g., running locally without a PR), switch to Local mode and work from the current branch changes.
- If branch information is unavailable, explicitly ask the user for scope before proceeding.
- Never assume the full repository is in scope when context is missing.

### Repeated Terminal Command Failures
- If a terminal command fails, retry once with the same parameters.
- If it fails again, try with verbose/debug flags to get more diagnostic output.
- After 3 consecutive failures of the same command, stop retrying, report the failure clearly to the user, and continue with other tasks that don't depend on the failing command.
- Do not silently swallow errors or claim success when commands fail.
```

---

## Topic 5: Invocability Settings — Evaluation

### Decision

All 7 agents should remain at default invocability settings (both user-invocable and model-invocable). No `user-invocable` or `disable-model-invocation` fields need to be added.

### Rationale

- **Architect**: Should be user-invocable (for manual IaC generation) and model-invocable (for auto-invocation during app creation). Default is correct.
- **Archivist**: Should be user-invocable (for manual doc updates) and model-invocable (for auto-triggered doc drift detection). Default is correct.
- **Designer**: Should be user-invocable (for manual design work) and model-invocable (for auto-triggered visual polish). Default is correct.
- **Judge**: Should be user-invocable (for manual PR comment triage) and model-invocable (for auto-triggered review processing). Default is correct.
- **Linter**: Should be user-invocable (for manual lint runs) and model-invocable (for auto-triggered validation). Default is correct.
- **Quality Assurance**: Should be user-invocable (for manual QA) and model-invocable (for auto-triggered quality checks). Default is correct.
- **Tester**: Should be user-invocable (for manual test writing) and model-invocable (for auto-triggered test generation). Default is correct.

None of the agents are internal-only pipeline agents — all serve legitimate direct-invocation and auto-selection use cases. Adding restriction fields would reduce flexibility without a clear benefit.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Restrict Linter to model-invocable only | Users legitimately invoke Linter directly for ad-hoc lint runs |
| Restrict Judge to user-invocable only | Model may auto-select Judge when PR review comments are detected |
| Add `user-invocable: true` explicitly | Redundant; true is the default. Adds YAML clutter without value |

### Implementation Details

Document the evaluation decision in `copilot-instructions.md` as a brief note in the Custom Agents section. No frontmatter changes needed.
