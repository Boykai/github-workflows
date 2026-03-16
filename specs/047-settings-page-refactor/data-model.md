# Data Model: Settings Page Refactor with Secrets

**Feature**: 047-settings-page-refactor | **Date**: 2026-03-16

## Overview

This feature introduces new entities for GitHub environment secret management and extends the existing MCP preset model. No existing data models are modified — only extended. The settings page restructuring is purely a UI concern with no data model changes to user/global/project settings.

## New Entities

### SecretListItem (Frontend Type)

Represents a single secret's metadata as returned by the GitHub API. Secret values are never included (write-only by design).

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| name | `string` | `^[A-Z][A-Z0-9_]*$`, max 255 chars | GitHub secret name (e.g., `COPILOT_MCP_CONTEXT7_API_KEY`) |
| created_at | `string` | ISO 8601 datetime | When the secret was first created |
| updated_at | `string` | ISO 8601 datetime | When the secret value was last updated |

**Source**: GitHub REST API `GET /repos/{owner}/{repo}/environments/{env}/secrets` response.

### SecretsListResponse (Frontend Type)

List response wrapper for secret metadata.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| total_count | `number` | `>= 0` | Total number of secrets in the environment |
| secrets | `SecretListItem[]` | — | Array of secret metadata objects |

**Source**: GitHub REST API response shape, proxied through backend.

### SecretCheckResponse (Frontend Type)

Bulk check result indicating which secrets are configured.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| [key: string] | `boolean` | — | Secret name → exists flag (e.g., `{ "COPILOT_MCP_CONTEXT7_API_KEY": true }`) |

**Source**: Backend `GET /secrets/{owner}/{repo}/{env}/check` endpoint.

### SetSecretRequest (Backend Pydantic Model)

Request body for creating or updating a secret value.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| value | `str` | max 65536 bytes (64 KB) | Plaintext secret value; encrypted before GitHub API call |

**Validation rules**:
- `value` must not be empty
- `value` must not exceed 64 KB (65,536 bytes)
- Path parameter `secret_name` validated separately: `^[A-Z][A-Z0-9_]*$`, max 255 chars

### KnownSecret (Frontend Constant)

Static mapping of well-known MCP secrets to user-friendly labels.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| name | `string` | Must match `^[A-Z][A-Z0-9_]*$` | GitHub secret name |
| label | `string` | Human-readable | Displayed in the Secrets Manager UI |
| description | `string` | Optional help text | Explains what the secret is used for |

**Instance data** (initial set, hardcoded):

| name | label | description |
|------|-------|-------------|
| `COPILOT_MCP_CONTEXT7_API_KEY` | Context7 API Key | API key for Context7 library documentation MCP server |

**Extensibility**: New entries added when new MCP presets declare `required_secrets`.

## Modified Entities

### McpPresetResponse (Backend Pydantic Model)

**Current fields** (unchanged):

| Field | Type | Notes |
|-------|------|-------|
| id | `str` | Preset identifier (e.g., `"context7"`) |
| name | `str` | Display name |
| description | `str` | Description text |
| category | `str` | Grouping category |
| icon | `str` | Icon identifier |
| config_content | `str` | JSON configuration |

**New field**:

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| required_secrets | `list[str]` | `[]` | Secret names required for this preset to function |

**Preset data updates**:

| Preset ID | required_secrets |
|-----------|-----------------|
| `context7` | `["COPILOT_MCP_CONTEXT7_API_KEY"]` |
| All others | `[]` (empty, backward-compatible) |

## Relationships

```
McpPresetResponse
  ├── required_secrets: list[str]  ──references──▶  KnownSecret.name
  │                                                       │
  │                                                       ▼
  │                                              SecretsManager UI
  │                                              (displays known secrets)
  │
  └── required_secrets  ──checked via──▶  SecretCheckResponse
                                              │
                                              ▼
                                        Tools Page Warning Badge
                                        ("⚠ API key not configured")

GitHub Environment
  ├── environment_name: "copilot" (default)
  └── secrets: SecretListItem[]
        ├── created via PUT with NaCl-encrypted value
        └── values NEVER returned (write-only)
```

## State Transitions

### Secret Lifecycle

```
[Not Set]
  │
  ├── User clicks "Set" → enters value → PUT /secrets/{owner}/{repo}/{env}/{name}
  │     → Backend encrypts with NaCl sealed-box
  │     → GitHub API stores encrypted value
  │     → UI shows "Set ✓" badge
  │
  ▼
[Set]
  │
  ├── User clicks "Update" → enters new value → PUT (same endpoint, upsert)
  │     → Backend encrypts new value
  │     → GitHub API replaces encrypted value
  │     → UI shows updated_at timestamp change
  │     → Status remains "Set ✓"
  │
  ├── User clicks "Remove" → confirms → DELETE /secrets/{owner}/{repo}/{env}/{name}
  │     → GitHub API removes secret
  │     → UI shows "Not Set" badge
  │     → Returns to [Not Set]
  │
  ▼
[Not Set] (after removal)
```

### Environment Lifecycle

```
[Does Not Exist]
  │
  ├── First secret operation triggers auto-creation
  │     → get_or_create_environment(access_token, owner, repo, "copilot")
  │     → GitHub API creates environment
  │
  ▼
[Exists]
  │
  └── Subsequent secret operations use existing environment
      (no further environment API calls needed after creation)
```

### Tab Navigation State

```
[Page Load]
  │
  ├── No URL hash → default to "essential"
  ├── #essential → select Essential tab
  ├── #secrets → select Secrets tab
  ├── #preferences → select Preferences tab
  ├── #admin (admin user) → select Admin tab
  └── #admin (non-admin) → fall back to "essential"
  │
  ▼
[Tab Selected]
  │
  ├── User clicks different tab → update URL hash
  ├── User modifies settings → unsaved changes warning tracked
  └── User navigates away → prompt if unsaved changes exist
```

## Validation Rules

### Secret Name (Backend + Frontend)

| Rule | Pattern | Error Message |
|------|---------|---------------|
| Format | `^[A-Z][A-Z0-9_]*$` | "Secret name must contain only uppercase letters, digits, and underscores, and must start with a letter" |
| Max length | 255 characters | "Secret name must not exceed 255 characters" |
| Min length | 1 character | "Secret name is required" |

### Secret Value (Backend + Frontend)

| Rule | Constraint | Error Message |
|------|-----------|---------------|
| Not empty | `len(value) > 0` | "Secret value cannot be empty" |
| Max size | 65,536 bytes (64 KB) | "Secret value must not exceed 64 KB" |

### Custom Secret Prefix (Frontend Warning Only)

| Rule | Pattern | Warning Message |
|------|---------|-----------------|
| Recommended prefix | `^COPILOT_MCP_` | "GitHub Copilot only exposes secrets with the COPILOT_MCP_ prefix to MCP servers" |

**Note**: This is a warning, not a validation error. Secrets without the prefix are allowed but may not be visible to MCP servers.

## Indexes & Storage

### No New Database Tables

This feature does not add any database tables. All secret storage is handled by GitHub's environment secrets API (external). Settings data continues to use the existing SQLite tables via `settings_store.py`.

### GitHub API as External Storage

| Operation | GitHub API Endpoint | Method |
|-----------|-------------------|--------|
| List secrets | `/repos/{owner}/{repo}/environments/{env}/secrets` | GET |
| Get public key | `/repos/{owner}/{repo}/environments/{env}/secrets/public-key` | GET |
| Create/update secret | `/repos/{owner}/{repo}/environments/{env}/secrets/{name}` | PUT |
| Delete secret | `/repos/{owner}/{repo}/environments/{env}/secrets/{name}` | DELETE |
| Create/update environment | `/repos/{owner}/{repo}/environments/{env_name}` | PUT |

**Caching**: No caching of secret lists (always fetch fresh from GitHub API). TanStack Query provides client-side caching with appropriate `staleTime` for the secrets list query.
