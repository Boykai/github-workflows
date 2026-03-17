# Quickstart: Non-Speckit Agent Definitions — Improvement Opportunities

**Branch**: `051-agent-config-cleanup` | **Date**: 2026-03-17

## Prerequisites

- Access to the `.github/agents/` directory in the repository
- Text editor with YAML syntax highlighting (for frontmatter validation)
- Terminal access (for grep-based verification)

## Phase 1: Frontmatter Cleanup (HIGH — User Stories 1, 2)

### Step 1: Remove `handoffs` blocks from 5 agents

Remove the entire `handoffs:` block from the YAML frontmatter of these files:

1. `.github/agents/archivist.agent.md`
2. `.github/agents/designer.agent.md`
3. `.github/agents/judge.agent.md`
4. `.github/agents/quality-assurance.agent.md`
5. `.github/agents/tester.agent.md`

Verify:
```bash
grep -r "handoffs:" .github/agents/*.agent.md
# Expected: no output (0 matches)
```

### Step 2: Add `tools: ["*"]` to all 7 agents

Insert `tools:` block immediately after the `description:` field in each agent's YAML frontmatter:

```yaml
tools:
- '*'
```

**Files to modify** (all in `.github/agents/`):
1. `architect.agent.md`
2. `archivist.agent.md`
3. `designer.agent.md`
4. `judge.agent.md`
5. `linter.agent.md`
6. `quality-assurance.agent.md`
7. `tester.agent.md`

Verify:
```bash
grep -c "tools:" .github/agents/architect.agent.md .github/agents/archivist.agent.md .github/agents/designer.agent.md .github/agents/judge.agent.md .github/agents/linter.agent.md .github/agents/quality-assurance.agent.md .github/agents/tester.agent.md
# Expected: each file shows at least 1 match for the top-level tools field
```

## Phase 2: Validation Section Rewrites (HIGH — User Story 3)

### Step 3: Rewrite Archivist validation section

In `.github/agents/archivist.agent.md`, replace the `## Validation` section with explicit commands for documentation and code validation. See `contracts/agent-frontmatter.md` Contract 3 for exact content.

### Step 4: Rewrite Designer validation section

In `.github/agents/designer.agent.md`, replace the `## Validation` section with explicit frontend validation commands. See `contracts/agent-frontmatter.md` Contract 4 for exact content.

### Step 5: Rewrite Tester validation section

In `.github/agents/tester.agent.md`, replace `### 6. Validate the Changes` with explicit test and lint commands. See `contracts/agent-frontmatter.md` Contract 5 for exact content.

### Step 6: Add validation section to Quality Assurance agent

In `.github/agents/quality-assurance.agent.md`, insert a `## Validation` section before `## Output Requirements` with explicit backend/frontend validation commands. See `contracts/agent-frontmatter.md` Contract 7 for exact content.

Verify (all validation rewrites):
```bash
grep -r "handoff\|hand off" .github/agents/archivist.agent.md .github/agents/designer.agent.md .github/agents/judge.agent.md .github/agents/quality-assurance.agent.md .github/agents/tester.agent.md
# Expected: no output (0 matches — no references to handoff mechanism)
```

## Phase 3: Shared Instructions Updates (MEDIUM/LOW — User Stories 4, 5, 6)

### Step 7: Add Failure and Degradation Guidance

In `.github/agents/copilot-instructions.md`, add a `## Failure and Degradation Guidance` section after `## Validation Expectations`. See `contracts/shared-instructions.md` Contract 1 for exact content.

Verify:
```bash
grep "Failure and Degradation" .github/agents/copilot-instructions.md
# Expected: 1 match
```

### Step 8: Add Invocability evaluation note

In `.github/agents/copilot-instructions.md`, add a blockquote after the Utility Agents table documenting the invocability decision. See `contracts/shared-instructions.md` Contract 3 for exact content.

### Step 9: Document $ARGUMENTS convention

In `.github/agents/copilot-instructions.md`, add a `### Agent Input Convention ($ARGUMENTS)` subsection in the Custom Agents section. See `contracts/shared-instructions.md` Contract 2 for exact content.

Verify:
```bash
grep "ARGUMENTS" .github/agents/copilot-instructions.md
# Expected: matches showing the documented convention
```

## Verification Checklist

- [ ] `grep -r "handoffs:" .github/agents/*.agent.md` → 0 results
- [ ] All 7 agent files contain `tools:` with `- '*'` in frontmatter
- [ ] `grep -ri "handoff\|hand off" .github/agents/archivist.agent.md .github/agents/designer.agent.md .github/agents/judge.agent.md .github/agents/quality-assurance.agent.md .github/agents/tester.agent.md` → 0 results
- [ ] Archivist validation section references explicit commands
- [ ] Designer validation section references explicit commands
- [ ] Tester validation section references explicit commands
- [ ] QA agent has explicit `## Validation` section
- [ ] `copilot-instructions.md` has `## Failure and Degradation Guidance` section
- [ ] `copilot-instructions.md` has invocability evaluation note
- [ ] `copilot-instructions.md` has `$ARGUMENTS` convention documentation
- [ ] All YAML frontmatter is valid (no parse errors)
- [ ] No functional regressions — agents still have correct name, description, MCP servers
