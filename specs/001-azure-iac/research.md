# Research: Azure Deployment Infrastructure as Code

**Feature**: Azure IaC for Tech Connect  
**Date**: 2026-02-13  
**Purpose**: Resolve technology decisions and establish best practices for infrastructure deployment

---

## Decision: Template Technology (Bicep vs. ARM)

**Decision**: Use Azure Bicep for all IaC templates

**Rationale**:
- **Readability**: Bicep syntax is significantly more concise and readable than ARM JSON (50-70% less code for equivalent functionality)
- **Tooling Support**: Native Azure CLI integration, VS Code extension with IntelliSense, built-in validation
- **Type Safety**: Strong typing prevents common configuration errors at authoring time
- **Modularity**: Native module system enables clean separation of concerns
- **No Migration Risk**: Bicep transpiles to ARM templates, ensuring full Azure Resource Manager compatibility
- **Learning Curve**: Easier for DevOps engineers to learn and maintain compared to verbose ARM JSON

**Alternatives Considered**:
- **ARM Templates (JSON)**: Rejected due to verbosity, poor readability, and lack of modern language features. ARM is the underlying technology but not the optimal authoring format.
- **Terraform**: Rejected to avoid introducing HashiCorp dependency and state management complexity. Azure-native tooling preferred for Azure-only deployment.
- **Azure CLI scripts**: Rejected due to lack of declarative benefits, no idempotency guarantees, and poor change detection.

**Implications**:
- Requires Bicep CLI (included with Azure CLI 2.20+)
- Template files use `.bicep` extension
- Parameter files use `.bicepparam` extension (Bicep parameter format, more readable than JSON)
- All templates will be linted with `az bicep build` before deployment

---

## Decision: App Service Container Deployment

**Decision**: Use Web App for Containers with Docker Compose configuration converted to individual container deployments

**Rationale**:
- **Existing Configuration**: Application already has working docker-compose.yml with health checks and networking
- **App Service Native Support**: Web App for Containers provides managed container hosting without Kubernetes complexity
- **Health Check Integration**: App Service health checks map directly to Docker health checks
- **Environment Variable Management**: App Service application settings provide secure configuration injection
- **Scaling**: App Service Plan enables horizontal and vertical scaling without container orchestration

**Configuration Requirements**:
- **Backend App Service**:
  - `linuxFxVersion`: `DOCKER|<registry>/<image>:<tag>` format
  - Site config: `alwaysOn: true`, `http20Enabled: true`
  - Health check path: `/api/v1/health` (existing endpoint from docker-compose)
  - Port: 8000 (WEBSITES_PORT app setting)
- **Frontend App Service**:
  - `linuxFxVersion`: `DOCKER|<registry>/<image>:<tag>` format
  - Site config: `alwaysOn: true`, `http20Enabled: true`
  - Health check path: `/health` (to be added to nginx config)
  - Port: 80 (default)

**Container Registry Options**:
1. **Docker Hub (Phase 1)**: Public images for dev/staging using existing GitHub workflow builds
2. **Azure Container Registry (Phase 2)**: Private registry for production with managed identity auth
3. **GitHub Container Registry**: Alternative for private images with PAT authentication

**Deployment Flow**:
1. Build containers via GitHub Actions (existing workflow)
2. Push to container registry
3. Deploy infrastructure with Bicep templates
4. Configure App Service to pull container image
5. App Service handles image updates via webhook or manual restart

---

## Decision: Secret Management with Key Vault

**Decision**: Store all secrets in Azure Key Vault and reference them in App Service using Key Vault references with managed identity authentication

**Rationale**:
- **Security**: Secrets never appear in Bicep templates, parameter files, or logs
- **Centralized Management**: Single source of truth for secrets across environments
- **Rotation Support**: Secrets can be rotated in Key Vault without redeploying infrastructure
- **Audit Trail**: Key Vault provides access logging and compliance tracking
- **Managed Identity**: Eliminates need for storing credentials to access secrets (passwordless authentication)

**Implementation Pattern**:

1. **Secret Storage**: Deploy Key Vault and populate with secrets during initial setup
2. **Managed Identity**: Enable system-assigned managed identity on both App Services
3. **Access Policy**: Grant App Service identities `GET` permission on Key Vault secrets
4. **Reference Syntax**: Use `@Microsoft.KeyVault(SecretUri=https://{vault}.vault.azure.net/secrets/{name})` in appSettings

**Secrets to Store**:
- `github-client-secret`: GitHub OAuth app secret
- `azure-openai-key`: Azure OpenAI API key
- `session-secret-key`: Backend session encryption key
- `github-webhook-secret`: Webhook signature verification secret (optional)

**Example App Setting**:
```bicep
appSettings: [
  {
    name: 'GITHUB_CLIENT_SECRET'
    value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/github-client-secret)'
  }
]
```

**Implications**:
- Key Vault must be deployed before App Services
- Managed identities must be created and access policies configured before app startup
- Initial secret values must be provided during deployment (securestring parameters)
- Secret rotation requires updating Key Vault, not redeploying infrastructure

---

## Decision: Multi-Environment Parameterization

**Decision**: Use Bicep parameter files (`.bicepparam`) with a single main template, one parameter file per environment

**Rationale**:
- **No Duplication**: Single main.bicep template shared across all environments
- **Type Safety**: Bicep parameter files validated against template parameters at authoring time
- **Readability**: Bicep parameter syntax more readable than JSON (using `using` directive)
- **Version Control**: Parameter files committed to repo (except sensitive values via secure parameters)
- **Validation**: Parameter files validated independently with `az bicep build-params`

**File Organization**:
```
infra/
├── main.bicep                    # Single template for all environments
├── parameters/
│   ├── dev.bicepparam           # Development (B1 SKU, dev region, minimal resources)
│   ├── staging.bicepparam       # Staging (S1 SKU, staging region, mirrors production)
│   └── production.bicepparam    # Production (P1V2 SKU, production region, high availability)
```

**Parameter File Structure**:
```bicep
using '../main.bicep'

param environment = 'dev'
param location = 'eastus'
param resourcePrefix = 'techcon'
param appServiceSku = 'B1'
param backendDockerImage = 'ghcr.io/org/backend:dev'
param frontendDockerImage = 'ghcr.io/org/frontend:dev'
param githubClientId = 'dev-client-id'
param githubClientSecret = readEnvironmentVariable('GITHUB_CLIENT_SECRET') // Secure
param azureOpenAIEndpoint = 'https://dev-openai.openai.azure.com'
param azureOpenAIKey = readEnvironmentVariable('AZURE_OPENAI_KEY') // Secure
param sessionSecretKey = readEnvironmentVariable('SESSION_SECRET_KEY') // Secure
```

**Environment Differences**:
| Parameter | Dev | Staging | Production |
|-----------|-----|---------|------------|
| SKU | B1 | S1 | P1V2 |
| Region | eastus | centralus | eastus2 |
| Always On | false | true | true |
| Min Instances | 1 | 1 | 2 |
| Health Check | enabled | enabled | enabled |

**Implications**:
- Sensitive values passed via environment variables (not stored in repo)
- Deployment scripts read environment variables and pass to Bicep CLI
- Parameter files documented with example values (real values in CI/CD secrets)

---

## Decision: Deployment Idempotency

**Decision**: Leverage Azure Resource Manager's declarative model with explicit what-if validation before every deployment

**Rationale**:
- **ARM Guarantees**: Azure Resource Manager provides idempotency by design - deploys only calculate and apply changes
- **Change Detection**: ARM compares desired state (template) with current state (deployed resources) and computes minimal changeset
- **What-If Preview**: `az deployment group what-if` command shows exact changes without applying them
- **Safe Re-runs**: Running same deployment multiple times results in no operation if no changes detected
- **Update Logic**: ARM determines whether to create, update, or skip each resource based on existence and configuration

**Validation Approach**:

1. **Pre-Deployment Validation**:
   ```bash
   az deployment group validate \
     --resource-group techcon-dev-rg \
     --template-file main.bicep \
     --parameters @parameters/dev.bicepparam
   ```
   - Validates template syntax
   - Checks parameter types and constraints
   - Verifies resource dependencies

2. **What-If Analysis**:
   ```bash
   az deployment group what-if \
     --resource-group techcon-dev-rg \
     --template-file main.bicep \
     --parameters @parameters/dev.bicepparam
   ```
   - Shows resources to be created (green +)
   - Shows resources to be modified (yellow ~)
   - Shows resources to be deleted (red -)
   - Shows resources unchanged (gray =)

3. **Deployment**:
   ```bash
   az deployment group create \
     --resource-group techcon-dev-rg \
     --template-file main.bicep \
     --parameters @parameters/dev.bicepparam
   ```

**Resource Update Behavior**:
- **App Service**: Configuration changes applied without restart (unless linuxFxVersion changes)
- **Key Vault**: Access policies updated in-place, secrets versioned automatically
- **App Service Plan**: SKU changes trigger in-place update (brief downtime possible on downgrade)

**Implications**:
- Always run what-if before production deployments
- Review change output carefully (especially deletions)
- Use `--mode Incremental` (default) to only modify declared resources, not delete unlisted ones
- CI/CD pipeline includes what-if as approval gate for production

---

## Decision: Naming Conventions

**Decision**: Use Azure Cloud Adoption Framework naming standards with environment-based prefixes

**Rationale**:
- **Consistency**: Standardized naming across all Azure resources enables easy identification
- **Environment Isolation**: Environment name in resource name prevents accidental cross-environment operations
- **Searchability**: Prefix-based naming enables filtering in Azure Portal and CLI
- **Compliance**: Meets Azure naming restrictions (length, character sets, global uniqueness)

**Naming Pattern**:
```
{workload}-{environment}-{resource-type}-{uniquifier}
```

**Examples**:
| Resource Type | Pattern | Dev Example | Production Example |
|--------------|---------|-------------|-------------------|
| Resource Group | `{prefix}-{env}-rg` | `techcon-dev-rg` | `techcon-prod-rg` |
| App Service Plan | `{prefix}-{env}-plan` | `techcon-dev-plan` | `techcon-prod-plan` |
| Backend App | `{prefix}-{env}-backend` | `techcon-dev-backend` | `techcon-prod-backend` |
| Frontend App | `{prefix}-{env}-frontend` | `techcon-dev-frontend` | `techcon-prod-frontend` |
| Key Vault | `{prefix}-{env}-kv-{hash}` | `techcon-dev-kv-a1b2` | `techcon-prod-kv-x9y8` |

**Key Vault Uniqueness**:
- Key Vault names must be globally unique across all Azure subscriptions
- Append 4-character hash derived from subscription ID: `uniqueString(subscription().subscriptionId)`
- Total length: 3-24 characters (alphanumeric + hyphens)

**Tagging Strategy**:
All resources tagged with:
- `Environment`: dev | staging | production
- `Application`: tech-connect
- `ManagedBy`: bicep
- `CostCenter`: [configurable per environment]
- `Owner`: [configurable per environment]

**Implications**:
- Resource prefix configurable per deployment (default: 'techcon')
- Environment name validated against allowed values (dev, staging, production)
- Tags enable cost tracking and automated resource management policies

---

## Decision: Networking and CORS

**Decision**: Configure CORS at App Service level with environment-specific allowed origins, defer custom domain/SSL to post-deployment

**Rationale**:
- **Built-in CORS**: App Service provides native CORS configuration (no reverse proxy needed)
- **Environment-Specific**: Dev allows localhost, staging/production allow only production domains
- **SSL by Default**: *.azurewebsites.net domains include free SSL certificates
- **Custom Domain Flexibility**: Custom domains configured after initial deployment (requires DNS verification)

**CORS Configuration**:

**Development**:
```
Allowed Origins:
- http://localhost:5173
- http://localhost:80
- https://{backend}.azurewebsites.net
```

**Staging/Production**:
```
Allowed Origins:
- https://{frontend}.azurewebsites.net
- https://custom-domain.com (if configured)
```

**App Service Settings**:
```bicep
siteConfig: {
  cors: {
    allowedOrigins: allowedOrigins
    supportCredentials: true
  }
  httpLoggingEnabled: true
  detailedErrorLoggingEnabled: true
  minTlsVersion: '1.2'
  ftpsState: 'Disabled'
  http20Enabled: true
}
```

**Production Networking Requirements**:
1. **Custom Domain** (manual post-deployment):
   - Add CNAME record pointing to *.azurewebsites.net
   - Verify domain ownership in Azure Portal
   - Bind SSL certificate (free managed certificate or custom)

2. **HTTPS Redirect**: Enabled by default on App Service
3. **IP Restrictions**: Optional, configured via `ipSecurityRestrictions` if needed
4. **VNet Integration**: Out of scope for initial deployment (requires Premium SKU)

**Implications**:
- CORS configured during deployment via parameters
- Custom domains require manual DNS configuration (not automated in templates)
- Free SSL certificates automatically provisioned for *.azurewebsites.net
- Managed certificates for custom domains require App Service Certificate or Let's Encrypt

---

## Decision: SKU Sizing Strategy

**Decision**: Use Basic SKU for development, Standard for staging, Premium for production with auto-scaling configurations

**Rationale**:
- **Cost Optimization**: Basic SKU costs ~$13/month for dev, acceptable for non-critical environments
- **Feature Parity**: Standard and Premium SKUs required for always-on, SSL, auto-scaling
- **Performance**: Premium V2 SKUs provide dedicated compute with better performance guarantees
- **Scaling**: Auto-scaling enabled on staging/production for handling variable load

**SKU Recommendations**:

| Environment | SKU | vCPU | RAM | Cost/Month | Features |
|------------|-----|------|-----|------------|----------|
| Development | B1 | 1 | 1.75 GB | ~$13 | Basic features, no always-on |
| Staging | S1 | 1 | 1.75 GB | ~$69 | Always-on, auto-scale, SSL |
| Production | P1V2 | 1 | 3.5 GB | ~$99 | Enhanced performance, better SLA |

**Scaling Configuration**:

**Development**: No auto-scaling (fixed 1 instance)
```bicep
sku: {
  name: 'B1'
  tier: 'Basic'
  capacity: 1
}
```

**Staging**: Auto-scale 1-2 instances
```bicep
sku: {
  name: 'S1'
  tier: 'Standard'
  capacity: 1
}
// Auto-scale rule: CPU > 70% for 5 min → scale to 2
```

**Production**: Auto-scale 2-5 instances
```bicep
sku: {
  name: 'P1V2'
  tier: 'PremiumV2'
  capacity: 2
}
// Auto-scale rule: CPU > 70% for 5 min → scale up (max 5)
```

**Cost Estimates** (per environment per month):
- **Development**: ~$15 (1x B1 + Key Vault)
- **Staging**: ~$75 (1-2x S1 + Key Vault)
- **Production**: ~$200 (2-5x P1V2 + Key Vault + possible ACR)

**Implications**:
- SKU specified in parameter files (easily changed)
- Development environment may have slower cold start (no always-on)
- Production requires budget approval for premium features
- Auto-scaling rules configured separately via Azure Monitor (not in initial template)

---

## Summary of Research Decisions

| Decision Area | Selected Approach | Key Benefit |
|--------------|-------------------|-------------|
| Template Technology | Azure Bicep | Readability and type safety |
| Container Deployment | Web App for Containers | Managed hosting without orchestration complexity |
| Secret Management | Key Vault + Managed Identity | Secure, passwordless secret access |
| Parameterization | Bicep parameter files per environment | Type-safe, no duplication |
| Idempotency | ARM declarative model + what-if | Safe re-runs, change preview |
| Naming | CAF standards + environment prefix | Consistency and searchability |
| Networking | App Service CORS + default SSL | Built-in security, defer custom domain |
| SKU Sizing | Tiered strategy (Basic→Standard→Premium) | Cost optimization per environment |

**Next Phase**: Use these decisions to generate data-model.md, contracts/, and quickstart.md
