# Data Model: Non-Speckit Agent Definitions — Improvement Opportunities

**Branch**: `051-agent-config-cleanup` | **Date**: 2026-03-17

## Overview

This feature modifies static configuration files (agent definition markdown files and the shared instructions file). There are no database entities, API models, or runtime data structures involved. The "data model" for this feature is the structure of the agent definition files themselves — specifically their YAML frontmatter schema and markdown body sections.

## Entities

### Agent Definition File (Modified Structure)

Each of the 7 non-speckit agent files in `.github/agents/` follows this structure. The changes add a `tools` field and remove the `handoffs` block.

#### YAML Frontmatter Schema (After Changes)

| Field | Type | Required | Description | Change |
|---|---|---|---|---|
| name | string | Yes | Agent display name (e.g., "Architect") | No change |
| description | string | Yes | Agent purpose description | No change |
| tools | string[] | **New** | Built-in tool access grants (e.g., `["*"]`) | **Added** |
| ~~handoffs~~ | ~~array~~ | ~~No~~ | ~~Sub-agent handoff declarations~~ | **Removed** |
| mcp-servers | object | No | MCP server configurations | No change |

#### Before (Current State — 5 Agents with Handoffs)

```yaml
---
name: <Agent Name>
description: <Agent description>
handoffs:                    # ← REMOVE (unsupported, dead config)
- label: Run Validation
  agent: Linter
  prompt: <validation prompt>
  send: true
mcp-servers:
  context7: { ... }
  CodeGraphContext: { ... }
---
```

#### After (Target State — All 7 Agents)

```yaml
---
name: <Agent Name>
description: <Agent description>
tools:                       # ← ADD (explicit tool access)
- '*'
mcp-servers:
  context7: { ... }
  CodeGraphContext: { ... }
---
```

**Location**: `.github/agents/*.agent.md`

### Shared Instructions File (Modified Structure)

The shared instructions file (`copilot-instructions.md`) gains 3 new sections.

| Section | Description | Change |
|---|---|---|
| Failure and Degradation Guidance | Shared degradation clause for all agents | **Added** — new section |
| $ARGUMENTS Convention | Documentation for the `$ARGUMENTS` pattern | **Added** — subsection in Custom Agents |
| Invocability Notes | Evaluation outcome for invocability settings | **Added** — brief note in Custom Agents |

**Location**: `.github/agents/copilot-instructions.md`

### Agent Markdown Body — Validation Sections (Modified)

5 agents have validation-related body sections that need rewriting.

| Agent | Current Section | Action |
|---|---|---|
| Archivist | `## Validation` (lines ~169–177) | Rewrite to explicit commands |
| Designer | `## Validation` (lines ~170–178) | Rewrite to explicit commands |
| Judge | No explicit validation section | No body change needed |
| Quality Assurance | Validation mentioned in `## Output Requirements` | Add explicit validation step |
| Tester | `### 6. Validate the Changes` (lines ~156–165) | Rewrite to explicit commands |

## State Transitions

N/A — This feature modifies static configuration files. There are no runtime state transitions, workflows, or data flow changes.

## Relationships

```
copilot-instructions.md ──── shared by ────→ All 7 Agent Definition Files
    ├── Failure/Degradation Guidance (new — all agents inherit)
    ├── $ARGUMENTS Convention docs (new — all agents reference)
    └── Invocability evaluation notes (new — documents decisions)

Agent Definition File ──── uses ────→ tools: ["*"] (new — built-in tool access)
Agent Definition File ──── uses ────→ mcp-servers (unchanged)
Agent Definition File ──── had ────→ handoffs (REMOVED — was dead config)
```

## No Database Migration Required

This feature does NOT touch any database schema, API models, or persistent data structures. All changes are to static markdown files in `.github/agents/`.

## No New Dependencies

No new packages, libraries, or external dependencies are introduced. The `tools` field and updated markdown sections use only native GitHub Custom Agent features and standard markdown.
