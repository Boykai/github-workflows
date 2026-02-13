# Data Model: Azure Infrastructure Resources

**Feature**: Azure IaC for Tech Connect  
**Date**: 2026-02-13  
**Purpose**: Define Azure resources as entities with properties, relationships, and validation rules

---

## Entity: Resource Group

**Description**: Logical container for all Tech Connect resources in a specific environment

### Fields
- `name` (string): Resource group name following pattern `{prefix}-{env}-rg`
- `location` (string): Azure region (e.g., eastus, centralus, westus2)
- `tags` (object): Metadata for organization and cost tracking
  - `Environment` (string): dev | staging | production
  - `Application` (string): tech-connect
  - `ManagedBy` (string): bicep
  - `CostCenter` (string): Optional, configurable per deployment
  - `Owner` (string): Optional, configurable per deployment

### Validation Rules
- `name` must be unique within Azure subscription
- `name` must be 1-90 characters, alphanumeric, hyphens, underscores, periods, parentheses
- `location` must be a valid Azure region from `az account list-locations`
- `tags` values must be strings, max 512 characters each

### Relationships
- **Contains**: All other resources (App Service Plan, App Services, Key Vault)
- **Belongs to**: Azure Subscription

### State Transitions
1. **Created**: Resource group provisioned in subscription
2. **Updated**: Tags or metadata modified (no resource recreation)
3. **Deleted**: Resource group and all contained resources removed

---

## Entity: App Service Plan

**Description**: Compute resource defining performance tier, region, and OS for hosting applications

### Fields
- `name` (string): Plan name following pattern `{prefix}-{env}-plan`
- `location` (string): Azure region (must match resource group)
- `sku` (object): Performance tier configuration
  - `name` (string): SKU identifier (B1, S1, P1V2, etc.)
  - `tier` (string): Tier name (Basic, Standard, PremiumV2)
  - `capacity` (integer): Number of worker instances (1-20)
- `kind` (string): Fixed value 'linux' for Linux-based apps
- `reserved` (boolean): Fixed value true (required for Linux)
- `tags` (object): Inherited from resource group

### Validation Rules
- `name` must be unique within resource group
- `name` must be 1-40 characters, alphanumeric, hyphens
- `sku.name` must be from allowed values:
  - Development: B1, B2, B3
  - Staging: S1, S2, S3
  - Production: P1V2, P2V2, P3V2
- `sku.capacity` must be 1-20 (varies by SKU)
- `location` must match resource group location
- `kind` must be 'linux' (Windows not supported for containers)

### Relationships
- **Parent to**: Backend App Service, Frontend App Service
- **Belongs to**: Resource Group

### State Transitions
1. **Created**: Plan provisioned with initial SKU
2. **Scaled Vertically**: SKU changed (B1 → S1 → P1V2)
3. **Scaled Horizontally**: Capacity increased (1 → 2 instances)
4. **Deleted**: Plan and all dependent App Services removed

---

## Entity: App Service (Backend)

**Description**: Web App hosting the FastAPI backend application container

### Fields
- `name` (string): App name following pattern `{prefix}-{env}-backend`
- `location` (string): Azure region (must match App Service Plan)
- `serverFarmId` (resourceId): Reference to parent App Service Plan
- `identity` (object): Managed identity for Key Vault access
  - `type` (string): 'SystemAssigned'
- `siteConfig` (object): Application configuration
  - `linuxFxVersion` (string): Container image in format `DOCKER|registry/image:tag`
  - `appCommandLine` (string): Optional container command override
  - `alwaysOn` (boolean): Keep app loaded (requires Standard+ SKU)
  - `http20Enabled` (boolean): Enable HTTP/2 support
  - `minTlsVersion` (string): '1.2' for security
  - `ftpsState` (string): 'Disabled' for security
  - `healthCheckPath` (string): '/api/v1/health'
  - `cors` (object): Cross-origin configuration
    - `allowedOrigins` (array): List of allowed origin URLs
    - `supportCredentials` (boolean): true for auth cookies
- `appSettings` (array): Environment variables (name-value pairs)
  - `GITHUB_CLIENT_ID` (string): GitHub OAuth client ID
  - `GITHUB_CLIENT_SECRET` (reference): Key Vault reference
  - `AZURE_OPENAI_ENDPOINT` (string): OpenAI service URL
  - `AZURE_OPENAI_KEY` (reference): Key Vault reference
  - `SESSION_SECRET_KEY` (reference): Key Vault reference
  - `FRONTEND_URL` (string): Frontend URL for CORS
  - `WEBSITES_PORT` (string): '8000' (container port)
  - Additional app-specific settings (~15 total)
- `tags` (object): Inherited from resource group

### Validation Rules
- `name` must be globally unique (becomes {name}.azurewebsites.net)
- `name` must be 2-60 characters, alphanumeric, hyphens (no leading/trailing hyphen)
- `linuxFxVersion` format must be `DOCKER|{image}` where image is valid registry path
- `serverFarmId` must reference an existing Linux App Service Plan
- `healthCheckPath` must return HTTP 200 for app to be marked healthy
- Key Vault references must use format: `@Microsoft.KeyVault(SecretUri={uri})`
- `allowedOrigins` must be valid URLs (http/https)

### Relationships
- **Belongs to**: App Service Plan (via serverFarmId)
- **References**: Key Vault secrets (via managed identity)
- **Belongs to**: Resource Group
- **Connects to**: Frontend App Service (via CORS configuration)

### State Transitions
1. **Created**: App provisioned, managed identity assigned
2. **Configured**: App settings applied, Key Vault access granted
3. **Running**: Container pulled and started, health check passing
4. **Stopped**: Manually stopped or SKU changed
5. **Updated**: Configuration or container image changed (rolling restart)
6. **Deleted**: App removed, managed identity deleted

---

## Entity: App Service (Frontend)

**Description**: Web App hosting the React frontend application container (nginx)

### Fields
- `name` (string): App name following pattern `{prefix}-{env}-frontend`
- `location` (string): Azure region (must match App Service Plan)
- `serverFarmId` (resourceId): Reference to parent App Service Plan
- `identity` (object): Managed identity (not required for frontend, but included for consistency)
  - `type` (string): 'SystemAssigned'
- `siteConfig` (object): Application configuration
  - `linuxFxVersion` (string): Container image in format `DOCKER|registry/image:tag`
  - `alwaysOn` (boolean): Keep app loaded (requires Standard+ SKU)
  - `http20Enabled` (boolean): Enable HTTP/2 support
  - `minTlsVersion` (string): '1.2' for security
  - `ftpsState` (string): 'Disabled' for security
  - `healthCheckPath` (string): '/health' (requires nginx health endpoint)
  - `cors` (object): Not configured (frontend doesn't need CORS)
- `appSettings` (array): Environment variables
  - `VITE_API_BASE_URL` (string): Backend API URL (e.g., '/api/v1')
  - `WEBSITES_PORT` (string): '80' (nginx default port)
- `tags` (object): Inherited from resource group

### Validation Rules
- Same naming and format rules as Backend App Service
- `linuxFxVersion` must reference frontend container image (nginx-based)
- `healthCheckPath` must return HTTP 200 (requires nginx config update)
- `VITE_API_BASE_URL` can be relative path (proxy to backend) or absolute URL

### Relationships
- **Belongs to**: App Service Plan (via serverFarmId)
- **Belongs to**: Resource Group
- **Connects to**: Backend App Service (via API calls)

### State Transitions
Same as Backend App Service (Created → Configured → Running → Stopped → Updated → Deleted)

---

## Entity: Key Vault

**Description**: Secure storage for application secrets (credentials, API keys, encryption keys)

### Fields
- `name` (string): Vault name following pattern `{prefix}-{env}-kv-{uniquifier}`
  - `uniquifier` = `uniqueString(subscription().subscriptionId)` (4 chars)
- `location` (string): Azure region (must match resource group)
- `sku` (object): Pricing tier
  - `name` (string): 'standard' (default) or 'premium' (for HSM)
  - `family` (string): 'A' (fixed value)
- `tenantId` (string): Azure AD tenant ID from subscription
- `enableSoftDelete` (boolean): true (soft delete enabled, 90-day retention)
- `softDeleteRetentionInDays` (integer): 90 (default, cannot be decreased)
- `enableRbacAuthorization` (boolean): false (using access policies)
- `accessPolicies` (array): List of permission grants
  - `tenantId` (string): Azure AD tenant ID
  - `objectId` (string): Principal ID (managed identity of App Service)
  - `permissions` (object):
    - `secrets` (array): ['get', 'list'] for App Services
- `tags` (object): Inherited from resource group

### Validation Rules
- `name` must be globally unique across all Azure Key Vaults
- `name` must be 3-24 characters, alphanumeric, hyphens (no consecutive hyphens)
- `name` must start with letter, end with letter or digit
- `tenantId` must be valid GUID
- `objectId` in access policies must reference existing Azure AD principal
- Soft delete cannot be disabled once enabled

### Relationships
- **Contains**: Key Vault Secrets (github-client-secret, azure-openai-key, session-secret-key)
- **Grants Access to**: Backend App Service (via access policy for managed identity)
- **Belongs to**: Resource Group

### State Transitions
1. **Created**: Vault provisioned with soft delete enabled
2. **Updated**: Access policies added/modified for App Service identities
3. **Soft-deleted**: Vault marked deleted, secrets inaccessible, 90-day recovery period
4. **Purged**: Permanently deleted after soft delete retention period

---

## Entity: Key Vault Secret

**Description**: Individual secret stored in Key Vault (password, API key, token)

### Fields
- `name` (string): Secret name (e.g., 'github-client-secret', 'azure-openai-key')
- `value` (securestring): Secret value (never logged or displayed)
- `contentType` (string): Optional MIME type or description
- `enabled` (boolean): true if secret can be retrieved
- `tags` (object): Optional metadata

### Validation Rules
- `name` must be 1-127 characters, alphanumeric, hyphens only
- `name` must match regex: `^[a-zA-Z0-9-]+$`
- `value` must not be empty
- `value` must be provided as securestring in Bicep (never plain text)

### Relationships
- **Stored in**: Key Vault
- **Referenced by**: App Service application settings (via SecretUri)

### State Transitions
1. **Created**: Secret stored with version 1
2. **Updated**: New version created (version 2, 3, etc.), previous versions retained
3. **Disabled**: Secret exists but cannot be retrieved (`enabled: false`)
4. **Deleted**: Secret marked deleted, recoverable during soft delete period
5. **Purged**: Permanently deleted (if vault-level purge protection enabled)

---

## Entity: Deployment Parameters

**Description**: Configuration input for Bicep template deployment (not an Azure resource)

### Fields
- `environment` (string): Target environment identifier
- `location` (string): Azure region for resource deployment
- `resourcePrefix` (string): Prefix for resource naming (e.g., 'techcon')
- `appServiceSku` (string): App Service Plan SKU (B1, S1, P1V2)
- `backendDockerImage` (string): Backend container image reference
- `frontendDockerImage` (string): Frontend container image reference
- `githubClientId` (string): GitHub OAuth client ID (public)
- `githubClientSecret` (securestring): GitHub OAuth client secret (sensitive)
- `githubRedirectUri` (string): OAuth callback URL
- `azureOpenAIEndpoint` (string): OpenAI service endpoint URL
- `azureOpenAIKey` (securestring): OpenAI API key (sensitive)
- `azureOpenAIDeployment` (string): Model deployment name (e.g., 'gpt-5')
- `sessionSecretKey` (securestring): Session encryption key (sensitive)
- `frontendUrl` (string): Frontend base URL for backend CORS
- `corsOrigins` (array): Additional CORS origins (optional)

### Validation Rules
- `environment` must be one of: 'dev', 'staging', 'production'
- `location` must be valid Azure region
- `resourcePrefix` must be 2-10 characters, lowercase alphanumeric + hyphens
- `appServiceSku` must be valid SKU from allowed list
- `backendDockerImage` format: `registry/repo:tag`
- `frontendDockerImage` format: `registry/repo:tag`
- `githubClientId` must not be empty
- `githubClientSecret` must not be empty (provided via secure input)
- `azureOpenAIEndpoint` must be valid HTTPS URL
- `azureOpenAIKey` must not be empty (provided via secure input)
- `sessionSecretKey` must be at least 32 characters (64 recommended)
- `frontendUrl` must be valid HTTPS URL (or HTTP for dev)

### Relationships
- **Input to**: Bicep template deployment
- **Determines**: All resource configurations and names
- **Contains**: Sensitive values passed to Key Vault

### State Transitions
N/A (stateless input, not persisted beyond deployment execution)

---

## Resource Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                        Deployment Order                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Resource Group                                              │
│     └─ Foundation for all resources                             │
│                                                                 │
│  2. Key Vault                                                   │
│     └─ Must exist before secrets can be created                 │
│                                                                 │
│  3. Key Vault Secrets                                           │
│     ├─ github-client-secret                                     │
│     ├─ azure-openai-key                                         │
│     └─ session-secret-key                                       │
│                                                                 │
│  4. App Service Plan                                            │
│     └─ Compute foundation for web apps                          │
│                                                                 │
│  5. App Services (parallel deployment)                          │
│     ├─ Backend App Service                                      │
│     │  ├─ System-assigned managed identity created              │
│     │  └─ Depends on: App Service Plan, Key Vault               │
│     └─ Frontend App Service                                     │
│        ├─ System-assigned managed identity created              │
│        └─ Depends on: App Service Plan                          │
│                                                                 │
│  6. Key Vault Access Policies                                   │
│     └─ Grant App Service identities GET permission on secrets   │
│        └─ Depends on: App Services (for managed identity IDs)   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Cross-Resource References

### 1. App Service → App Service Plan
```bicep
resource backend 'Microsoft.Web/sites@2023-01-01' = {
  name: backendAppName
  properties: {
    serverFarmId: appServicePlan.id  // Resource ID reference
  }
}
```

### 2. App Service → Key Vault Secret
```bicep
appSettings: [
  {
    name: 'GITHUB_CLIENT_SECRET'
    value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/github-client-secret)'
  }
]
```

### 3. Key Vault Access Policy → App Service Identity
```bicep
accessPolicies: [
  {
    tenantId: subscription().tenantId
    objectId: backend.identity.principalId  // Managed identity object ID
    permissions: {
      secrets: ['get']
    }
  }
]
```

---

## Summary

This data model defines 7 entity types representing Azure infrastructure resources:

| Entity | Type | Lifecycle | Dependencies |
|--------|------|-----------|--------------|
| Resource Group | Container | Persistent | None |
| App Service Plan | Compute | Persistent | Resource Group |
| App Service (Backend) | Compute | Persistent | Plan, Key Vault |
| App Service (Frontend) | Compute | Persistent | Plan |
| Key Vault | Security | Persistent | Resource Group |
| Key Vault Secret | Security | Versioned | Key Vault |
| Deployment Parameters | Input | Transient | None |

All entities follow Azure naming conventions, include comprehensive validation rules, and define clear relationships for dependency management during deployment.
