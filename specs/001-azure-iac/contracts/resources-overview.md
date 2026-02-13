# Azure Resources Overview

**Feature**: Azure IaC for Tech Connect  
**Date**: 2026-02-13  
**Purpose**: Document resource relationships, deployment dependencies, and naming conventions

---

## Resource Hierarchy

```
Azure Subscription
│
└── Resource Group: techcon-{env}-rg
    │
    ├── Key Vault: techcon-{env}-kv-{hash}
    │   ├── Secret: github-client-secret
    │   ├── Secret: azure-openai-key
    │   ├── Secret: session-secret-key
    │   └── Access Policies (for App Service managed identities)
    │
    └── App Service Plan: techcon-{env}-plan
        ├── App Service (Backend): techcon-{env}-backend
        │   ├── System-Assigned Managed Identity
        │   ├── Container: Backend FastAPI application
        │   ├── Health Check: /api/v1/health
        │   └── Key Vault References in App Settings
        │
        └── App Service (Frontend): techcon-{env}-frontend
            ├── System-Assigned Managed Identity
            ├── Container: Frontend React + nginx
            └── Health Check: /health
```

---

## Deployment Dependencies

Resources must be deployed in the following order to satisfy dependencies:

### Phase 1: Foundation
1. **Resource Group**
   - No dependencies
   - Creates logical container for all resources
   - **Duration**: < 5 seconds

### Phase 2: Security Infrastructure
2. **Key Vault**
   - Depends on: Resource Group
   - Must exist before secrets can be created
   - **Duration**: 10-30 seconds

3. **Key Vault Secrets**
   - Depends on: Key Vault
   - Creates secrets for sensitive configuration
   - Secrets:
     - `github-client-secret`: GitHub OAuth app secret
     - `azure-openai-key`: Azure OpenAI API key
     - `session-secret-key`: Backend session encryption key
   - **Duration**: < 5 seconds per secret

### Phase 3: Compute Infrastructure
4. **App Service Plan**
   - Depends on: Resource Group
   - Defines compute tier and capacity
   - Can be deployed in parallel with Key Vault
   - **Duration**: 30-60 seconds

5. **App Services** (parallel deployment)
   - **Backend App Service**:
     - Depends on: App Service Plan, Key Vault (for secret references)
     - Creates system-assigned managed identity
     - Configures container deployment
     - References Key Vault secrets in app settings
     - **Duration**: 60-90 seconds
   
   - **Frontend App Service**:
     - Depends on: App Service Plan
     - Creates system-assigned managed identity
     - Configures container deployment
     - **Duration**: 60-90 seconds

### Phase 4: Access Configuration
6. **Key Vault Access Policies**
   - Depends on: App Services (needs managed identity object IDs)
   - Grants backend App Service GET permission on secrets
   - Can be included in Key Vault definition or updated separately
   - **Duration**: < 5 seconds

**Total Deployment Time**: ~3-5 minutes (excluding container image pull time)

---

## Resource Naming Convention

All resources follow the pattern: `{resourcePrefix}-{environment}-{resourceType}-{suffix}`

### Naming Table

| Resource Type | Naming Pattern | Dev Example | Staging Example | Production Example |
|--------------|----------------|-------------|-----------------|-------------------|
| Resource Group | `{prefix}-{env}-rg` | `techcon-dev-rg` | `techcon-stg-rg` | `techcon-prod-rg` |
| App Service Plan | `{prefix}-{env}-plan` | `techcon-dev-plan` | `techcon-stg-plan` | `techcon-prod-plan` |
| Backend App Service | `{prefix}-{env}-backend` | `techcon-dev-backend` | `techcon-stg-backend` | `techcon-prod-backend` |
| Frontend App Service | `{prefix}-{env}-frontend` | `techcon-dev-frontend` | `techcon-stg-frontend` | `techcon-prod-frontend` |
| Key Vault | `{prefix}-{env}-kv-{hash}` | `techcon-dev-kv-a1b2` | `techcon-stg-kv-c3d4` | `techcon-prod-kv-e5f6` |

**Notes**:
- **{prefix}**: Configurable, default 'techcon' (2-10 chars, lowercase alphanumeric + hyphens)
- **{env}**: Environment identifier (dev, stg, prod)
- **{hash}**: 4-character unique string derived from subscription ID (Key Vault only)
- **Global Uniqueness**: App Service names become `{name}.azurewebsites.net`, Key Vault names become `{name}.vault.azure.net`

### Naming Constraints

| Resource Type | Min Length | Max Length | Allowed Characters | Must Be Globally Unique |
|--------------|-----------|------------|-------------------|------------------------|
| Resource Group | 1 | 90 | Alphanumeric, hyphens, underscores, periods, parentheses | Within subscription |
| App Service Plan | 1 | 40 | Alphanumeric, hyphens | Within resource group |
| App Service | 2 | 60 | Alphanumeric, hyphens (no leading/trailing) | Globally (DNS) |
| Key Vault | 3 | 24 | Alphanumeric, hyphens (no consecutive, no leading/trailing) | Globally (DNS) |

---

## Inter-Resource References

### 1. App Service → App Service Plan

**Reference Type**: Resource ID  
**Bicep Syntax**:
```bicep
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${resourcePrefix}-${environment}-plan'
  // ... properties
}

resource backendApp 'Microsoft.Web/sites@2023-01-01' = {
  name: '${resourcePrefix}-${environment}-backend'
  properties: {
    serverFarmId: appServicePlan.id  // Resource ID reference
  }
}
```

**Runtime Behavior**: App Service must be assigned to an existing App Service Plan. Changing the plan requires app restart.

---

### 2. App Service → Key Vault Secret

**Reference Type**: Key Vault Reference (App Setting)  
**Bicep Syntax**:
```bicep
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${resourcePrefix}-${environment}-kv-${uniqueString(subscription().subscriptionId)}'
  // ... properties
}

resource backendApp 'Microsoft.Web/sites@2023-01-01' = {
  name: '${resourcePrefix}-${environment}-backend'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    siteConfig: {
      appSettings: [
        {
          name: 'GITHUB_CLIENT_SECRET'
          value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/github-client-secret)'
        }
      ]
    }
  }
}
```

**Runtime Behavior**: 
- App Service resolves Key Vault reference on startup
- Uses managed identity to authenticate to Key Vault
- Fetches secret value and injects as environment variable
- Secret updates require app restart to take effect

---

### 3. Key Vault Access Policy → App Service Managed Identity

**Reference Type**: Principal Object ID  
**Bicep Syntax**:
```bicep
resource backendApp 'Microsoft.Web/sites@2023-01-01' = {
  name: '${resourcePrefix}-${environment}-backend'
  identity: {
    type: 'SystemAssigned'  // Creates managed identity
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  properties: {
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: backendApp.identity.principalId  // Reference to managed identity
        permissions: {
          secrets: ['get', 'list']
        }
      }
    ]
  }
}
```

**Runtime Behavior**:
- Managed identity created when App Service is provisioned
- Access policy grants identity permission to read secrets
- Identity can access Key Vault without storing credentials

---

### 4. Backend App Service → Frontend App Service (CORS)

**Reference Type**: Hostname/URL  
**Bicep Syntax**:
```bicep
resource frontendApp 'Microsoft.Web/sites@2023-01-01' = {
  name: '${resourcePrefix}-${environment}-frontend'
}

resource backendApp 'Microsoft.Web/sites@2023-01-01' = {
  name: '${resourcePrefix}-${environment}-backend'
  properties: {
    siteConfig: {
      cors: {
        allowedOrigins: [
          'https://${frontendApp.properties.defaultHostName}'
          // Additional origins from parameters
        ]
        supportCredentials: true
      }
    }
  }
}
```

**Runtime Behavior**:
- Backend allows requests from frontend domain
- Frontend makes API calls to backend
- CORS headers validated on each request

---

## Resource Tags

All resources are tagged with the following metadata for organization and cost tracking:

### Standard Tags (applied to all resources)

| Tag Key | Values | Purpose |
|---------|--------|---------|
| `Environment` | dev, staging, production | Environment identification |
| `Application` | tech-connect | Application grouping |
| `ManagedBy` | bicep | Indicates IaC management |

### Optional Tags (configurable per deployment)

| Tag Key | Example Values | Purpose |
|---------|---------------|---------|
| `CostCenter` | engineering, ops | Chargeback/cost allocation |
| `Owner` | team-devops, john@example.com | Resource ownership |
| `ProjectCode` | PRJ-12345 | Project tracking |

### Tag Inheritance

- Tags defined at **Resource Group** level are inherited by all child resources
- Tags can be overridden at individual resource level if needed
- Azure Policy can enforce required tags

---

## Network Topology

### Default Configuration (No VNet)

```
Internet
    │
    ├─→ Frontend App Service (techcon-{env}-frontend.azurewebsites.net)
    │   │   Port 443 (HTTPS)
    │   │   Free SSL certificate
    │   └─→ nginx serves React SPA
    │
    └─→ Backend App Service (techcon-{env}-backend.azurewebsites.net)
        │   Port 443 (HTTPS)
        │   Free SSL certificate
        │   CORS configured to allow frontend
        └─→ FastAPI application
```

**Security**:
- All traffic over HTTPS (TLS 1.2+)
- App Services are publicly accessible (no VNet integration)
- Key Vault accessible via public endpoint with access policies
- Managed identities provide secure authentication

### Future Enhancement: VNet Integration

For enhanced security in production:
- Deploy App Services in VNet subnet
- Key Vault with private endpoint
- Network Security Groups for traffic control
- Application Gateway for frontend

**Requires**: Premium V2 or higher SKU

---

## Resource Outputs

After successful deployment, the following values are available as outputs:

| Output Name | Description | Example Value |
|------------|-------------|---------------|
| `resourceGroupName` | Resource group name | `techcon-dev-rg` |
| `backendUrl` | Backend application URL | `https://techcon-dev-backend.azurewebsites.net` |
| `frontendUrl` | Frontend application URL | `https://techcon-dev-frontend.azurewebsites.net` |
| `keyVaultName` | Key Vault name | `techcon-dev-kv-a1b2` |
| `backendPrincipalId` | Backend managed identity ID | `12345678-abcd-1234-abcd-1234567890ab` |
| `frontendPrincipalId` | Frontend managed identity ID | `87654321-dcba-4321-dcba-0987654321ba` |

**Usage**:
```bash
# Get output values
az deployment group show \
  --name techcon-deployment \
  --resource-group techcon-dev-rg \
  --query properties.outputs
```

---

## Summary

This infrastructure consists of **6 primary resources** per environment:
1. Resource Group (container)
2. Key Vault (secrets storage)
3. App Service Plan (compute tier)
4. Backend App Service (FastAPI container)
5. Frontend App Service (React container)
6. Key Vault Secrets (3 secrets)

**Deployment Time**: 3-5 minutes  
**Monthly Cost** (development): ~$15-20  
**Monthly Cost** (production): ~$150-250 (with auto-scaling)

Resources are deployed in dependency order, with managed identities providing secure, passwordless access to Key Vault secrets.
