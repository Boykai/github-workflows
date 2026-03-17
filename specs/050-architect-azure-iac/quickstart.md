# Quickstart: Architect Agent for Azure IaC

**Branch**: `050-architect-azure-iac` | **Date**: 2026-03-17

## Prerequisites

- Node.js 22+ (for `npx @azure/mcp@latest`)
- Python 3.13+ with the backend virtualenv activated (`cd solune/backend && pip install -e ".[dev]"`)
- VS Code with Copilot extension (for agent testing)
- Optional: Bicep VS Code extension (`ms-azuretools.vscode-bicep`) for full Bicep MCP support

## Phase 1: MCP Configuration

### Step 1: Add Azure MCP to `.vscode/mcp.json`

Add the following entry to the `servers` object in `.vscode/mcp.json`:

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

Verify: Open VS Code → Agent mode → click tools icon → Azure MCP tools should appear.

### Step 2: Add Azure MCP to `.github/agents/mcp.json`

Add the following entry to the `mcpServers` object:

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

Verify: Both `mcp.json` files are valid JSON (`cat .github/agents/mcp.json | python -m json.tool`).

## Phase 2: Agent Definition

### Step 3: Create `.github/agents/architect.agent.md`

Create the agent file with YAML frontmatter (name, description, mcp-servers) and instruction body covering:
- Phase 0: Discovery
- Phase 1: Architecture Diagram generation
- Phase 2: IaC Generation (Bicep)
- Phase 3: Azure Developer CLI Scaffold
- Phase 4: 1-Click Deploy Button
- Phase 5: GitHub Secrets Setup documentation
- Phase 6: Validation

Reference `designer.agent.md` for YAML structure and `speckit.implement.agent.md` for MCP declarations.

Verify: Open VS Code → Copilot agent picker → "Architect" should appear.

### Step 4: Create `.github/prompts/architect.prompt.md`

```yaml
---
agent: architect
---
```

Verify: File matches the pattern of all 15 existing prompt files.

## Phase 3: Documentation Updates

### Step 5: Update `copilot-instructions.md`

Add `architect` to the Utility Agents table:

| `architect` | Generates Azure IaC (Bicep), `azd` scaffolds, architecture diagrams, and deploy buttons. Always runs for new apps. |

Add Azure MCP note to the MCP Configuration section.

Verify: `cat .github/agents/copilot-instructions.md | grep architect`

## Phase 4: Backend — Azure Credential Storage

### Step 6: Add `pynacl` dependency

```bash
cd solune/backend
pip install pynacl
```

Add `pynacl` to the dependencies in `pyproject.toml`.

### Step 7: Add `set_repository_secret()` to GitHub service

Add to `solune/backend/src/services/github_projects/repository.py`:

```python
async def set_repository_secret(
    self,
    access_token: str,
    owner: str,
    repo: str,
    secret_name: str,
    secret_value: str,
) -> None:
    """Store an encrypted secret in a GitHub repository via Secrets API."""
    # GET /repos/{owner}/{repo}/actions/secrets/public-key
    key_data = await self._rest(
        access_token,
        "GET",
        f"/repos/{owner}/{repo}/actions/secrets/public-key",
    )
    # Encrypt with libsodium sealed box
    from nacl.public import SealedBox, PublicKey
    import base64

    pk_bytes = base64.b64decode(key_data["key"])
    sealed_box = SealedBox(PublicKey(pk_bytes))
    encrypted = sealed_box.encrypt(secret_value.encode())
    encrypted_b64 = base64.b64encode(encrypted).decode()

    # PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}
    await self._rest(
        access_token,
        "PUT",
        f"/repos/{owner}/{repo}/actions/secrets/{secret_name}",
        json={"encrypted_value": encrypted_b64, "key_id": key_data["key_id"]},
    )
```

Verify: `cd solune/backend && ruff check src/ && pyright src`

### Step 8: Extend `AppCreate` model

Add to `solune/backend/src/models/app.py`:

```python
azure_client_id: str | None = Field(default=None, min_length=1)
azure_client_secret: str | None = Field(default=None, min_length=1, json_schema_extra={"writeOnly": True})
```

Add validator for paired fields:

```python
@model_validator(mode="after")
def validate_azure_credentials(self) -> Self:
    has_id = self.azure_client_id is not None
    has_secret = self.azure_client_secret is not None
    if has_id != has_secret:
        msg = "Azure Client ID and Client Secret must both be provided or both omitted"
        raise ValueError(msg)
    return self
```

### Step 9: Wire credential storage into `create_app_with_new_repo()`

In `solune/backend/src/services/app_service.py`, after repository creation and before template commit:

```python
# Store Azure credentials as GitHub Secrets (non-blocking)
if payload.azure_client_id and payload.azure_client_secret:
    try:
        await github_service.set_repository_secret(
            access_token, owner, repo_name,
            "AZURE_CLIENT_ID", payload.azure_client_id,
        )
        await github_service.set_repository_secret(
            access_token, owner, repo_name,
            "AZURE_CLIENT_SECRET", payload.azure_client_secret,
        )
    except Exception as exc:
        logger.warning("Failed to store Azure credentials for %s: %s", payload.name, exc)
```

Verify:
```bash
cd solune/backend
pyright src
ruff check src/
pytest tests/ -x -q
```

## Phase 5: Frontend — Azure Credential Fields

### Step 10: Extend TypeScript types

Add to `solune/frontend/src/types/apps.ts` `AppCreate` interface:

```typescript
azure_client_id?: string;
azure_client_secret?: string;
```

### Step 11: Add form fields to AppsPage.tsx

Add state variables:
```typescript
const [azureClientId, setAzureClientId] = useState('');
const [azureClientSecret, setAzureClientSecret] = useState('');
```

Add input fields in the "New Repository Settings" section (after Create Project checkbox):
- Azure Client ID: `type="text"`, label "Azure Client ID (optional)"
- Azure Client Secret: `type="password"`, label "Azure Client Secret (optional)"

Add paired validation in the submit handler.

Include new fields in the `createMutation.mutate()` payload when `repo_type === 'new-repo'`.

Verify:
```bash
cd solune/frontend
npx tsc --noEmit
npx vitest run
```

## Verification Checklist

- [ ] `.vscode/mcp.json` — valid JSON, Azure MCP entry present
- [ ] `.github/agents/mcp.json` — valid JSON, Azure MCP entry present
- [ ] `.github/agents/architect.agent.md` — appears in VS Code agent picker
- [ ] `.github/prompts/architect.prompt.md` — routes to Architect agent
- [ ] `copilot-instructions.md` — `architect` in utility agents table
- [ ] `copilot-instructions.md` — Azure MCP noted in MCP section
- [ ] `pyright src` — 0 errors
- [ ] `ruff check src/` — clean
- [ ] `pytest tests/ -x -q` — all pass
- [ ] `npx tsc --noEmit` — 0 TS errors
- [ ] `npx vitest run` — FE tests pass
- [ ] Agent mode → `@architect` prompt → valid Bicep + azure.yaml output
- [ ] Create new app with Azure credentials → secrets appear in repo settings
- [ ] Create new app without Azure credentials → app created normally
- [ ] Paired validation: one field without the other → error message
