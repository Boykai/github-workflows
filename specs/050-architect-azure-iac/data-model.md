# Data Model: Architect Agent for Azure IaC

**Branch**: `050-architect-azure-iac` | **Date**: 2026-03-17

## Overview

This feature introduces a new Architect utility agent with its supporting MCP configuration, prompt file, and documentation updates. It also extends the existing app creation flow with optional Azure credential storage. The data model changes are minimal: two new optional fields on the `AppCreate` input model for credentials (never persisted in the database — sent directly to GitHub Secrets API), and static file artifacts (agent definition, MCP config entries, prompt file).

## Entities

### AppCreate (Extended Input Model)

The existing `AppCreate` Pydantic model is extended with two optional fields for Azure credentials. These fields are transient — they are consumed during the app creation flow to store GitHub Secrets and are NOT persisted in the Solune database.

| Field | Type | Description | New? |
|---|---|---|---|
| name | str | App name (validated against APP_NAME_PATTERN) | No |
| display_name | str | Human-readable name | No |
| description | str | App description | No |
| branch | str \| None | Target branch (for same-repo/external-repo) | No |
| pipeline_id | str \| None | Optional pipeline association | No |
| repo_type | RepoType | One of: same-repo, external-repo, new-repo | No |
| external_repo_url | str \| None | URL for external-repo type | No |
| repo_owner | str \| None | GitHub owner for new-repo | No |
| repo_visibility | Literal["public", "private"] | Repository visibility | No |
| create_project | bool | Whether to create a linked Project V2 | No |
| ai_enhance | bool | Whether to AI-enhance description | No |
| azure_client_id | str \| None | Optional Azure Client ID for GitHub Secrets | **New** |
| azure_client_secret | str \| None | Optional Azure Client Secret for GitHub Secrets | **New** |

**Validation Rules**:
- `azure_client_id` and `azure_client_secret` must both be provided or both be `None` (paired validation)
- Only used when `repo_type = 'new-repo'`; ignored for other repo types
- Minimum length: 1 character each when provided (no empty strings)
- `azure_client_secret` must NEVER be logged, stored in the database, or included in API responses
- Values are consumed once during app creation to call GitHub Secrets API, then discarded

**Location**: `solune/backend/src/models/app.py`

### AppCreate TypeScript (Extended Frontend Type)

| Field | Type | Description | New? |
|---|---|---|---|
| name | string? | App name | No |
| display_name | string | Human-readable name | No |
| description | string? | App description | No |
| branch | string? | Target branch | No |
| pipeline_id | string? | Pipeline association | No |
| repo_type | RepoType? | Repo type selector | No |
| external_repo_url | string? | External repo URL | No |
| repo_owner | string? | GitHub owner for new-repo | No |
| repo_visibility | 'public' \| 'private'? | Repo visibility | No |
| create_project | boolean? | Create linked project | No |
| ai_enhance | boolean? | AI-enhance description | No |
| azure_client_id | string? | Optional Azure Client ID | **New** |
| azure_client_secret | string? | Optional Azure Client Secret | **New** |

**Location**: `solune/frontend/src/types/apps.ts`

### Architect Agent (New Static File)

The Architect agent is a static markdown file with YAML frontmatter. It is not a database entity.

| Property | Value | Description |
|---|---|---|
| name | Architect | Agent display name |
| description | IaC generation, Azure deployment scaffolding... | Agent purpose |
| mcp-servers | Context7, CodeGraphContext, Azure MCP | Configured tool servers |
| handoffs | (none) | Custom GitHub Agents don't support handoffs |

**Location**: `.github/agents/architect.agent.md`

### Architect Prompt (New Static File)

Minimal YAML redirect to the agent.

| Property | Value |
|---|---|
| agent | architect |

**Location**: `.github/prompts/architect.prompt.md`

### MCP Server Entry — Azure MCP (New Config Entry)

Added to both MCP configuration files.

| Property | Value (Local) | Value (Remote) |
|---|---|---|
| type | stdio | local |
| command | npx | npx |
| args | `["@azure/mcp@latest", "server", "start"]` | `["@azure/mcp@latest", "server", "start"]` |
| tools | (all — no filter) | `["*"]` |

**Locations**: `.vscode/mcp.json`, `.github/agents/mcp.json`

## State Transitions

### App Creation with Azure Credentials (New Repo Flow — Extended)

```
INPUT_RECEIVED → REPO_CREATING → REPO_CREATED → SECRETS_STORING → SECRETS_STORED → TEMPLATES_COMMITTING → TEMPLATES_COMMITTED → PROJECT_CREATING → PROJECT_CREATED → PROJECT_LINKED → DB_RECORD_INSERTED → ACTIVE
```

New steps in the flow:
- `REPO_CREATED → SECRETS_STORING` (after repo exists, store Azure credentials as GitHub Secrets)
- `SECRETS_STORING → SECRETS_STORED` (success — secrets are encrypted and stored)

Error branches:
- `SECRETS_STORING → SECRETS_PARTIAL` (one or both secrets fail → app continues, user notified)
- All existing error branches from `create_app_with_new_repo()` remain unchanged

### App Creation without Azure Credentials

The existing `create_app_with_new_repo()` flow is unchanged — the `SECRETS_STORING` step is skipped when `azure_client_id` and `azure_client_secret` are both `None`.

## Relationships

```
AppCreate ──── 0..2 ────→ GitHub Repository Secrets (via GitHub Secrets API)
    ├── AZURE_CLIENT_ID (encrypted, stored as repo secret)
    └── AZURE_CLIENT_SECRET (encrypted, stored as repo secret)

Architect Agent ──── uses ────→ Context7 MCP Server
Architect Agent ──── uses ────→ CodeGraphContext MCP Server
Architect Agent ──── uses ────→ Azure MCP Server
Architect Agent ──── uses ────→ Bicep MCP (via VS Code extension, local only)

Architect Agent ──── generates ────→ infra/ (Bicep modules)
Architect Agent ──── generates ────→ azure.yaml (azd manifest)
Architect Agent ──── generates ────→ docs/architectures/*.mmd (Mermaid diagrams)
Architect Agent ──── generates ────→ README.md deploy button
Architect Agent ──── generates ────→ .github/workflows/deploy.yml (CI/CD workflow)
```

## No Database Migration Required

This feature does NOT add new columns to the `apps` table. Azure credentials are:
1. Received in the `AppCreate` payload (transient)
2. Sent to GitHub Secrets API (encrypted at rest by GitHub)
3. Never stored in Solune's database

The `azure_client_id` and `azure_client_secret` fields exist only on the Pydantic input model (`AppCreate`) and TypeScript interface — not on the `App` response model or database schema.
