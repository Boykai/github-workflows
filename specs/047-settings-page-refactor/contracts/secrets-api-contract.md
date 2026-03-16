# Secrets API Contract

**Feature**: 047-settings-page-refactor | **Date**: 2026-03-16

## Contract: Secrets REST API

All secret operations are proxied through the backend to GitHub's environment secrets API. The backend handles encryption (NaCl sealed-box) and authentication (GitHub token from session).

### Base Path

```
/api/v1/secrets
```

### Authentication

All endpoints require an authenticated session. The `require_session` dependency extracts the GitHub access token from the session cookie.

```
[Request] → require_session dependency
  → Session cookie present → Extract access_token → Proceed
  → Session cookie missing/invalid → 401 Unauthorized
```

---

### Endpoint: List Environment Secrets

```
GET /api/v1/secrets/{owner}/{repo}/{environment}
```

**Path Parameters**:

| Parameter | Type | Constraints | Example |
|-----------|------|-------------|---------|
| owner | string | GitHub username/org | `"Boykai"` |
| repo | string | Repository name | `"github-workflows"` |
| environment | string | Environment name | `"copilot"` |

**Response** (200 OK):

```json
{
  "total_count": 2,
  "secrets": [
    {
      "name": "COPILOT_MCP_CONTEXT7_API_KEY",
      "created_at": "2026-03-16T10:00:00Z",
      "updated_at": "2026-03-16T10:00:00Z"
    },
    {
      "name": "COPILOT_MCP_CUSTOM_KEY",
      "created_at": "2026-03-15T08:30:00Z",
      "updated_at": "2026-03-16T09:15:00Z"
    }
  ]
}
```

**Error Responses**:

| Status | Condition | Body |
|--------|-----------|------|
| 401 | No valid session | `{ "detail": "Not authenticated" }` |
| 404 | Environment does not exist | `{ "detail": "Environment not found" }` |
| 403 | Insufficient GitHub permissions | `{ "detail": "Insufficient permissions to access environment secrets" }` |

---

### Endpoint: Create or Update Secret

```
PUT /api/v1/secrets/{owner}/{repo}/{environment}/{secret_name}
```

**Path Parameters**:

| Parameter | Type | Constraints | Example |
|-----------|------|-------------|---------|
| owner | string | GitHub username/org | `"Boykai"` |
| repo | string | Repository name | `"github-workflows"` |
| environment | string | Environment name | `"copilot"` |
| secret_name | string | `^[A-Z][A-Z0-9_]*$`, max 255 chars | `"COPILOT_MCP_CONTEXT7_API_KEY"` |

**Request Body**:

```json
{
  "value": "ctx7-abc123..."
}
```

| Field | Type | Constraints |
|-------|------|-------------|
| value | string | Required, non-empty, max 64 KB |

**Processing Flow**:

```
1. Validate secret_name against ^[A-Z][A-Z0-9_]*$ (reject if invalid → 422)
2. Validate value is non-empty and ≤ 64 KB (reject if invalid → 422)
3. Ensure environment exists: get_or_create_environment()
4. Fetch environment public key: GET /environments/{env}/secrets/public-key
5. Encrypt value: nacl.public.SealedBox(PublicKey(decoded_key)).encrypt(value.encode())
6. Base64-encode encrypted bytes
7. PUT to GitHub: /environments/{env}/secrets/{secret_name} with { encrypted_value, key_id }
```

**Response** (204 No Content):

No body. Secret created or updated successfully.

**Error Responses**:

| Status | Condition | Body |
|--------|-----------|------|
| 401 | No valid session | `{ "detail": "Not authenticated" }` |
| 403 | Insufficient GitHub permissions | `{ "detail": "Insufficient permissions to manage environment secrets" }` |
| 422 | Invalid secret name | `{ "detail": "Secret name must contain only uppercase letters, digits, and underscores, and must start with a letter" }` |
| 422 | Empty value | `{ "detail": "Secret value cannot be empty" }` |
| 422 | Value too large | `{ "detail": "Secret value must not exceed 64 KB" }` |

---

### Endpoint: Delete Secret

```
DELETE /api/v1/secrets/{owner}/{repo}/{environment}/{secret_name}
```

**Path Parameters**: Same as Create/Update.

**Response** (204 No Content):

No body. Secret deleted successfully.

**Error Responses**:

| Status | Condition | Body |
|--------|-----------|------|
| 401 | No valid session | `{ "detail": "Not authenticated" }` |
| 403 | Insufficient GitHub permissions | `{ "detail": "Insufficient permissions to manage environment secrets" }` |
| 404 | Secret does not exist | `{ "detail": "Secret not found" }` |

---

### Endpoint: Bulk Check Secrets

```
GET /api/v1/secrets/{owner}/{repo}/{environment}/check?names=KEY1,KEY2,KEY3
```

**Path Parameters**: Same as List.

**Query Parameters**:

| Parameter | Type | Constraints | Example |
|-----------|------|-------------|---------|
| names | string | Comma-separated secret names | `"COPILOT_MCP_CONTEXT7_API_KEY,COPILOT_MCP_OTHER"` |

**Response** (200 OK):

```json
{
  "COPILOT_MCP_CONTEXT7_API_KEY": true,
  "COPILOT_MPC_OTHER": false
}
```

**Processing Flow**:

```
1. Parse comma-separated names from query string
2. Fetch full secret list from GitHub API (names only)
3. For each requested name, check if it exists in the list
4. Return name → boolean map
```

**Error Responses**:

| Status | Condition | Body |
|--------|-----------|------|
| 401 | No valid session | `{ "detail": "Not authenticated" }` |
| 422 | No names provided | `{ "detail": "At least one secret name must be provided" }` |

---

## Contract: Encryption

### NaCl Sealed-Box Encryption

Secret values MUST be encrypted before transmission to the GitHub API. The encryption uses NaCl sealed-box (Curve25519 + XSalsa20-Poly1305).

```
[Plaintext secret value]
  → Fetch public key from GitHub (Base64-encoded 32-byte Curve25519 key)
  → Decode Base64 → raw 32 bytes
  → Create PublicKey object: nacl.public.PublicKey(raw_bytes)
  → Create SealedBox: nacl.public.SealedBox(public_key)
  → Encrypt: sealed_box.encrypt(value.encode("utf-8"))
  → Base64-encode result → encrypted_value string
  → Send { encrypted_value, key_id } to GitHub PUT endpoint
```

**Constraints**:
- Public key MUST be fetched fresh for each encryption operation (keys may rotate)
- Encryption happens server-side (backend), never client-side
- Plaintext values exist in memory only during the encryption operation
- No secret values are logged at any level
