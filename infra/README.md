# Infrastructure as Code (Bicep)

This directory contains Azure Bicep templates for deploying the GitHub Projects Chat application to Azure.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `projectName` | string | — | Short project identifier (alphanumeric, lowercase) |
| `environment` | string | `prod` | Deployment environment |
| `location` | string | Resource group location | Azure region |
| `githubToken` | secureString | — | GitHub PAT for API access |
| `modelDeploymentName` | string | `gpt-41` | Azure OpenAI model deployment name |
| `modelCapacity` | int | `10` | Model capacity (thousands of tokens per minute) |
| `backendImage` | string | `''` (auto-resolved) | Backend container image |
| `frontendImage` | string | `''` (auto-resolved) | Frontend container image |

## Module Dependency Graph

```
main.bicep
├── log-analytics.bicep
├── managed-identity.bicep
├── container-registry.bicep ← managed-identity
├── openai.bicep ← managed-identity
├── key-vault.bicep ← managed-identity, openai
├── ai-foundry-hub.bicep ← key-vault, log-analytics
├── ai-foundry-project.bicep ← ai-foundry-hub
├── container-apps-environment.bicep ← log-analytics
├── container-app-backend.bicep ← container-apps-environment, managed-identity
└── container-app-frontend.bicep ← container-apps-environment, managed-identity, container-app-backend
```

## Resource Naming Convention

Resources follow Azure Cloud Adoption Framework naming:

| Resource | Pattern | Example |
|----------|---------|---------|
| Resource Group | `rg-{project}-{env}` | `rg-ghprojectschat-prod` |
| Container Registry | `cr{project}{env}` | `crghprojectschatprod` |
| Container Apps Environment | `cae-{project}-{env}` | `cae-ghprojectschat-prod` |
| Container App (backend) | `ca-{project}-backend-{env}` | `ca-ghprojectschat-backend-prod` |
| Container App (frontend) | `ca-{project}-frontend-{env}` | `ca-ghprojectschat-frontend-prod` |
| Key Vault | `kv-{project}-{env}` | `kv-ghprojectschat-prod` |
| AI Foundry Hub | `aih-{project}-{env}` | `aih-ghprojectschat-prod` |
| AI Foundry Project | `aip-{project}-{env}` | `aip-ghprojectschat-prod` |
| Azure OpenAI | `aoai-{project}-{env}` | `aoai-ghprojectschat-prod` |
| Log Analytics Workspace | `law-{project}-{env}` | `law-ghprojectschat-prod` |
| Managed Identity | `id-{project}-{env}` | `id-ghprojectschat-prod` |

## Deployment

### Deploy

```bash
# Create resource group
az group create --name rg-ghprojectschat-prod --location eastus2

# Deploy all resources
az deployment group create \
  --resource-group rg-ghprojectschat-prod \
  --template-file main.bicep \
  --parameters main.bicepparam
```

### Tear Down

```bash
# Delete the entire resource group and all resources within it
az group delete --name rg-ghprojectschat-prod --yes --no-wait
```

> **Warning**: This permanently deletes all resources. Key Vault has soft-delete enabled with 90-day retention, so the vault name cannot be reused immediately. To purge:
>
> ```bash
> az keyvault purge --name kv-ghprojectschat-prod --location eastus2
> ```
