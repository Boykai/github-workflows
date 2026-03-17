# Contract: Backend REST API — Azure Credential Storage

**Feature**: 050-architect-azure-iac

This document defines the REST API contract extension for Azure credential storage during new-repo app creation.

---

## Contract 1: Create App with Azure Credentials (Extended)

**Endpoint**: `POST /api/v1/apps`
**Producer**: Backend `create_app_endpoint()` in `solune/backend/src/api/apps.py`
**Consumer**: Frontend `appsApi.create()` in `solune/frontend/src/services/api.ts`

### Request (Extended with Azure Fields)

```json
{
  "name": "my-azure-app",
  "display_name": "My Azure App",
  "description": "An app deployed to Azure",
  "repo_type": "new-repo",
  "repo_owner": "username-or-org",
  "repo_visibility": "private",
  "create_project": true,
  "ai_enhance": true,
  "azure_client_id": "00000000-0000-0000-0000-000000000000",
  "azure_client_secret": "secret-value-here"
}
```

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| name | string | Yes | — | 2-64 chars, kebab-case pattern |
| display_name | string | Yes | — | 1-128 chars |
| description | string | No | `""` | — |
| repo_type | string | No | `"same-repo"` | One of: `same-repo`, `external-repo`, `new-repo` |
| branch | string | Conditional | — | Required when `repo_type != "new-repo"` |
| repo_owner | string | Conditional | — | Required when `repo_type = "new-repo"` |
| repo_visibility | string | No | `"private"` | One of: `public`, `private` |
| create_project | boolean | No | `true` | Only for `new-repo` |
| pipeline_id | string | No | `null` | — |
| external_repo_url | string | No | `null` | For `external-repo` |
| ai_enhance | boolean | No | `true` | — |
| **azure_client_id** | **string** | **No** | **`null`** | **Min 1 char; must pair with `azure_client_secret`** |
| **azure_client_secret** | **string** | **No** | **`null`** | **Min 1 char; must pair with `azure_client_id`; password-masked in UI** |

### Response (201 Created)

No change from existing `POST /apps` response. Azure credentials are NOT returned in the response.

```json
{
  "name": "my-azure-app",
  "display_name": "My Azure App",
  "description": "An app deployed to Azure",
  "directory_path": ".",
  "associated_pipeline_id": null,
  "status": "active",
  "repo_type": "new-repo",
  "external_repo_url": null,
  "github_repo_url": "https://github.com/username-or-org/my-azure-app",
  "github_project_url": "https://github.com/users/username-or-org/projects/42",
  "github_project_id": "PVT_kwDO...",
  "port": null,
  "error_message": null,
  "created_at": "2026-03-17T15:00:00Z",
  "updated_at": "2026-03-17T15:00:00Z"
}
```

### Error Responses

| Status | Condition | Body |
|---|---|---|
| 422 | `azure_client_id` provided without `azure_client_secret` (or vice versa) | `{"detail": "Azure Client ID and Client Secret must both be provided or both omitted"}` |
| 201 (partial) | App created but Azure secret storage failed | App is returned normally; error is logged server-side; user receives a warning in the success response or follow-up notification |

### Backend Behavior

1. Validate paired fields: if one Azure credential is provided, both must be provided
2. Create GitHub repository (existing behavior)
3. **NEW**: If Azure credentials are provided, call GitHub Secrets API:
   - `GET /repos/{owner}/{repo}/actions/secrets/public-key` — retrieve encryption key
   - `PUT /repos/{owner}/{repo}/actions/secrets/AZURE_CLIENT_ID` — store encrypted Client ID
   - `PUT /repos/{owner}/{repo}/actions/secrets/AZURE_CLIENT_SECRET` — store encrypted Client Secret
4. Continue with existing flow: commit templates, create project, insert DB record
5. Azure credentials are discarded from memory after storage (not persisted in Solune DB)

### Security Requirements

- `azure_client_secret` MUST be transmitted over HTTPS only
- `azure_client_secret` MUST NOT appear in server logs (use `SecretStr` or explicit exclusion)
- `azure_client_secret` MUST NOT appear in API responses
- `azure_client_secret` MUST NOT be stored in Solune's database
- GitHub Secrets API handles encryption at rest

---

## Contract 2: GitHub Secrets API (Internal — Backend to GitHub)

**Endpoint**: `GET /repos/{owner}/{repo}/actions/secrets/public-key`
**Producer**: GitHub REST API
**Consumer**: Backend `set_repository_secret()` in `solune/backend/src/services/github_projects/repository.py`

### Request

```
GET /repos/{owner}/{repo}/actions/secrets/public-key
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "key_id": "012345678912345678",
  "key": "base64-encoded-public-key"
}
```

---

**Endpoint**: `PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}`
**Producer**: GitHub REST API
**Consumer**: Backend `set_repository_secret()` in `solune/backend/src/services/github_projects/repository.py`

### Request

```json
PUT /repos/{owner}/{repo}/actions/secrets/AZURE_CLIENT_ID
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "encrypted_value": "base64-encoded-encrypted-value",
  "key_id": "012345678912345678"
}
```

### Response (201 Created / 204 No Content)

Empty body on success.

### Error Responses

| Status | Condition |
|---|---|
| 403 | Insufficient permissions (missing `repo` or `actions` scope) |
| 404 | Repository not found |
| 422 | Invalid encrypted value or key_id |

### Dependencies

- **PyNaCl** (`pynacl`): Required for `libsodium` sealed box encryption of secret values before calling the GitHub Secrets API.
- **Existing OAuth scope**: The `repo` scope already configured for Solune OAuth should include access to repository secrets. If not, the `actions` scope may need to be added.
