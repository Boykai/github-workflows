# Contract: Agent and Configuration Files

**Feature**: 050-architect-azure-iac

This document defines the file-level contracts for the Architect agent definition, prompt file, MCP configuration entries, and documentation updates.

---

## Contract 1: Architect Agent Definition

**File**: `.github/agents/architect.agent.md`
**Type**: NEW file
**Pattern**: Follows `designer.agent.md` and `speckit.implement.agent.md` conventions

### YAML Frontmatter

```yaml
---
name: Architect
description: Generates Azure IaC (Bicep), azd scaffolds, architecture diagrams,
  and deploy buttons for new Solune apps. Always invoked during app creation.
mcp-servers:
  context7:
    type: http
    url: https://mcp.context7.com/mcp
    tools:
    - resolve-library-id
    - get-library-docs
    headers:
      CONTEXT7_API_KEY: $COPILOT_MCP_CONTEXT7_API_KEY
  CodeGraphContext:
    type: local
    command: uvx
    args:
    - --from
    - codegraphcontext
    - cgc
    - mcp
    - start
    tools:
    - '*'
  azure-mcp:
    type: local
    command: npx
    args:
    - '@azure/mcp@latest'
    - server
    - start
    tools:
    - '*'
---
```

### Instruction Body Phases

| Phase | Name | Description |
|---|---|---|
| Phase 0 | Discovery | Analyze project structure, detect existing infra, map dependencies via CodeGraphContext |
| Phase 1 | Architecture Diagram | Generate Mermaid `.mmd` diagrams (high-level, deployment) in `docs/architectures/` |
| Phase 2 | IaC Generation | Generate Bicep modules in `infra/` using AVM; `main.bicep` + per-resource modules |
| Phase 3 | Azure Developer CLI Scaffold | Generate `azure.yaml` manifest with services, hooks, env config |
| Phase 4 | 1-Click Deploy Button | Add "Deploy to Azure" badge and `azd init` one-liner to README |
| Phase 5 | GitHub Secrets Setup | Document CI/CD workflow referencing `${{ secrets.AZURE_CLIENT_ID }}` and `${{ secrets.AZURE_CLIENT_SECRET }}` |
| Phase 6 | Validation | Verify Bicep compiles, `azure.yaml` is valid, diagrams render |

### Operating Rules (Embedded in Agent)

- Bicep over ARM JSON — always
- Use Azure Verified Modules (AVM) when available
- Follow Well-Architected Framework principles
- Never hardcode secrets — Key Vault refs, managed identity, GitHub Secrets
- Use `azd` environment variables for parameterization
- Follow project naming conventions discovered via CodeGraphContext

---

## Contract 2: Architect Prompt Shortcut

**File**: `.github/prompts/architect.prompt.md`
**Type**: NEW file
**Pattern**: Matches all 15 existing prompt files

### Content

```yaml
---
agent: architect
---
```

---

## Contract 3: Azure MCP Entry in `.vscode/mcp.json`

**File**: `.vscode/mcp.json`
**Type**: MODIFY — add entry to existing `servers` object

### New Entry

```json
"microsoft/azure-mcp": {
    "type": "stdio",
    "command": "npx",
    "args": [
        "@azure/mcp@latest",
        "server",
        "start"
    ]
}
```

**Position**: After the existing `debugmcp` entry (last entry in `servers`)

### Validation

- File remains valid JSON after edit
- No duplicate keys in `servers` object
- `type: "stdio"` matches the pattern used by Playwright MCP, markitdown, Context7, and serena

---

## Contract 4: Azure MCP Entry in `.github/agents/mcp.json`

**File**: `.github/agents/mcp.json`
**Type**: MODIFY — add entry to existing `mcpServers` object

### New Entry

```json
"azure-mcp": {
    "type": "local",
    "command": "npx",
    "args": [
        "@azure/mcp@latest",
        "server",
        "start"
    ],
    "tools": ["*"]
}
```

**Position**: After the existing `CodeGraphContext` entry

### Validation

- File remains valid JSON after edit
- `type: "local"` matches the pattern used by CodeGraphContext
- `tools: ["*"]` grants access to all Azure MCP tools

---

## Contract 5: copilot-instructions.md Updates

**File**: `.github/agents/copilot-instructions.md`
**Type**: MODIFY — two sections updated

### Update 1: Utility Agents Table

Add row to the utility agents table:

| Agent | Purpose |
|---|---|
| `architect` | Generates Azure IaC (Bicep), `azd` scaffolds, architecture diagrams, and deploy buttons. Always runs for new apps. |

**Position**: Alphabetical — first row in the utility agents table (before `archivist`)

### Update 2: MCP Configuration Section

Add note about Azure MCP availability:

> Azure MCP is available in `.github/agents/mcp.json` for remote GitHub Custom Agents, providing Azure resource schema lookups, Bicep best practices, and Well-Architected Framework guidance.

**Position**: After the existing note about Context7 in the MCP configuration section
