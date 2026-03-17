# Contract: Agent Frontmatter Changes

**Feature**: 051-agent-config-cleanup

This document defines the YAML frontmatter change contracts for all 7 non-speckit agent definition files, plus the validation section rewrite contracts for the 5 affected agents.

---

## Contract 1: Add `tools: ["*"]` to All 7 Agents

**Files**: All 7 agent files in `.github/agents/`
**Type**: MODIFY — add field to YAML frontmatter

### Change Pattern

Insert `tools:` block immediately after the `description:` field and before any `handoffs:` or `mcp-servers:` block.

```yaml
# ADD after description, before mcp-servers
tools:
- '*'
```

### Affected Files

| File | Has Handoffs | Has MCP Servers |
|---|---|---|
| `architect.agent.md` | No | Yes (Context7, CodeGraphContext, Azure MCP) |
| `archivist.agent.md` | Yes (remove first) | Yes (Context7, CodeGraphContext) |
| `designer.agent.md` | Yes (remove first) | Yes (Context7, CodeGraphContext) |
| `judge.agent.md` | Yes (remove first) | Yes (Context7, CodeGraphContext) |
| `linter.agent.md` | No | Yes (Context7, CodeGraphContext) |
| `quality-assurance.agent.md` | Yes (remove first) | Yes (Context7, CodeGraphContext) |
| `tester.agent.md` | Yes (remove first) | Yes (Context7, CodeGraphContext) |

### Validation

- Each file's YAML frontmatter includes `tools:` with `- '*'`
- `tools:` appears between `description:` and `mcp-servers:`
- YAML remains valid after insertion (verify with a YAML parser)
- No other frontmatter fields are modified

---

## Contract 2: Remove `handoffs:` from 5 Agents

**Files**: `archivist.agent.md`, `designer.agent.md`, `judge.agent.md`, `quality-assurance.agent.md`, `tester.agent.md`
**Type**: MODIFY — remove field from YAML frontmatter

### Remove Block (per agent)

**archivist.agent.md:**
```yaml
# REMOVE
handoffs:
- label: Run Validation
  agent: Linter
  prompt: Run the relevant lint, type-check, test, build, and documentation validation
    for the archivist changes
  send: true
```

**designer.agent.md:**
```yaml
# REMOVE
handoffs:
- label: Run Validation
  agent: Linter
  prompt: Run the relevant lint, type-check, test, and build validation for the designer
    changes
  send: true
```

**judge.agent.md:**
```yaml
# REMOVE (note copy-paste bug: says "quality-assurance" instead of "judge")
handoffs:
- label: Run Validation
  agent: Linter
  prompt: Run the relevant lint, type-check, test, and build validation for the quality-assurance
    changes
  send: true
```

**quality-assurance.agent.md:**
```yaml
# REMOVE
handoffs:
- label: Run Validation
  agent: Linter
  prompt: Run the relevant lint, type-check, test, and build validation for the quality-assurance
    changes
  send: true
```

**tester.agent.md:**
```yaml
# REMOVE
handoffs:
- label: Run Validation
  agent: Linter
  prompt: Run relevant lint, type-check, test, and build validation for the tester
    changes
  send: true
```

### Validation

- Zero agent files contain a `handoffs:` key in YAML frontmatter
- `grep -r "handoffs:" .github/agents/*.agent.md` returns no results
- All other frontmatter fields (name, description, mcp-servers) remain unchanged
- YAML remains valid after removal

---

## Contract 3: Rewrite Validation Sections — Archivist

**File**: `.github/agents/archivist.agent.md`
**Type**: MODIFY — rewrite `## Validation` section in markdown body

### Current Content (approximate)

```markdown
## Validation

Run the most relevant validation for the changed area:

- Markdown linting or docs checks when available.
- Targeted build, type-check, test, or command verification when the docs depend on executable behavior.
- Manual consistency checks between docs and the changed code when tooling is unavailable.

Do not claim documentation accuracy without checking the changed behavior against the live implementation.
```

### Replacement Content

```markdown
## Validation

Run validation directly using terminal access. Execute the checks most relevant to the documentation you changed:

**Documentation validation**:
- Verify markdown renders correctly and internal links are valid
- Confirm code examples in docs match the actual implementation
- Check that README sections reference correct file paths and commands

**If docs reference executable behavior** (backend/frontend):
- `cd solune/backend && ruff check src/ tests/` — lint check
- `cd solune/backend && pyright src/` — type check
- `cd solune/frontend && npm run lint` — ESLint
- `cd solune/frontend && npm run type-check` — TypeScript check

Do not claim documentation accuracy without checking the changed behavior against the live implementation.
```

---

## Contract 4: Rewrite Validation Sections — Designer

**File**: `.github/agents/designer.agent.md`
**Type**: MODIFY — rewrite `## Validation` section in markdown body

### Current Content (approximate)

```markdown
## Validation

Run the most relevant validation for the changed area:

- Targeted lint, type-check, build, or test validation for touched files.
- Any available visual or component-level checks relevant to the changed surface.
- Manual sanity review of responsive and themed behavior when possible.

Do not claim polish or production readiness without validating the changed surface appropriately.
```

### Replacement Content

```markdown
## Validation

Run validation directly using terminal access. Execute the checks most relevant to the design surface you changed:

**Frontend validation** (if applicable):
- `cd solune/frontend && npm run lint` — ESLint
- `cd solune/frontend && npm run type-check` — TypeScript check
- `cd solune/frontend && npm run test` — Vitest unit tests
- `cd solune/frontend && npm run build` — production build

**Visual validation**:
- Review component rendering in the browser for responsive and themed behavior
- Verify Tailwind utility classes are applied correctly (CSS-first v4 model in `src/index.css`)
- Check that design tokens and theme variables are consistent across changed surfaces

Do not claim polish or production readiness without validating the changed surface appropriately.
```

---

## Contract 5: Rewrite Validation Sections — Tester

**File**: `.github/agents/tester.agent.md`
**Type**: MODIFY — rewrite `### 6. Validate the Changes` section in markdown body

### Current Content (approximate)

```markdown
### 6. Validate the Changes

Run the most relevant validation for the changed area:

- Targeted tests first.
- Broader test suites when the local change affects shared behavior.
- Type checks, lint checks, or builds when relevant to the files touched.

Do not claim quality improvements without running the checks needed to support them.
```

### Replacement Content

```markdown
### 6. Validate the Changes

Run validation directly using terminal access. Execute the checks relevant to the test files and source code you changed:

**Backend validation** (if applicable):
- `cd solune/backend && pytest tests/ -x -q` — run tests (targeted first, then broader)
- `cd solune/backend && ruff check src/ tests/` — lint check
- `cd solune/backend && pyright src/` — type check

**Frontend validation** (if applicable):
- `cd solune/frontend && npm run test` — Vitest unit tests
- `cd solune/frontend && npm run lint` — ESLint
- `cd solune/frontend && npm run type-check` — TypeScript check

Do not claim quality improvements without running the checks needed to support them.
```

---

## Contract 6: Judge Agent — No Body Validation Section Change Needed

**File**: `.github/agents/judge.agent.md`
**Type**: MODIFY — frontmatter only (tools + handoffs removal)

The Judge agent does not have a dedicated `## Validation` section in its markdown body. Its workflow is inherently about PR comment triage and applying code changes, with validation being implicit in the "apply changes" step. No body text rewrite is required beyond the frontmatter changes.

---

## Contract 7: Quality Assurance Agent — Update Output Requirements

**File**: `.github/agents/quality-assurance.agent.md`
**Type**: MODIFY — add explicit validation step to `## Output Requirements`

The QA agent's output requirements mention "Validation run" as item 7 but don't provide explicit commands. Add a validation execution section before the output requirements.

### Addition (insert before `## Output Requirements`)

```markdown
## Validation

Run validation directly using terminal access before producing your final output. Execute the checks most relevant to the code paths you reviewed and changed:

**Backend validation** (if applicable):
- `cd solune/backend && ruff check src/ tests/` — lint check
- `cd solune/backend && ruff format --check src/ tests/` — format check
- `cd solune/backend && pyright src/` — type check
- `cd solune/backend && pytest tests/ -x -q` — run tests

**Frontend validation** (if applicable):
- `cd solune/frontend && npm run lint` — ESLint
- `cd solune/frontend && npm run type-check` — TypeScript check
- `cd solune/frontend && npm run test` — Vitest unit tests
- `cd solune/frontend && npm run build` — production build

Do not claim quality assurance completeness without running the validation checks relevant to the code you changed.
```
