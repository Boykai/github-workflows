# Quickstart: Deploy Tech Connect to Azure

**Feature**: Azure IaC for Tech Connect  
**Estimated Time**: 15-20 minutes  
**Skill Level**: Intermediate DevOps

---

## Prerequisites

### Required Tools

- **Azure CLI** 2.50 or later ([installation guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))
  ```bash
  # Verify installation
  az version
  
  # Should show Azure CLI 2.50+ and Bicep CLI
  ```

- **Bicep CLI** (included with Azure CLI, verify with):
  ```bash
  az bicep version
  ```

### Required Accounts & Resources

1. **Azure Subscription** with:
   - Contributor or Owner role
   - Sufficient quota for App Services and Key Vault
   - No existing resources with conflicting names

2. **GitHub OAuth App** ([setup guide](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app)):
   - Application name: Tech Connect (or your choice)
   - Homepage URL: `https://{your-prefix}-{env}-frontend.azurewebsites.net`
   - Authorization callback URL: `https://{your-prefix}-{env}-frontend.azurewebsites.net/api/v1/auth/github/callback`
   - Save Client ID and generate Client Secret

3. **Azure OpenAI Resource** with deployment ([setup guide](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource)):
   - Create Azure OpenAI resource in Azure Portal
   - Deploy a model (e.g., gpt-5, gpt-4)
   - Save endpoint URL and API key

---

## Quick Deploy: Development Environment

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/github-workflows.git
cd github-workflows
```

### Step 2: Login to Azure

```bash
# Login interactively
az login

# List subscriptions
az account list --output table

# Set active subscription
az account set --subscription <subscription-id>

# Verify
az account show --output table
```

### Step 3: Set Environment Variables

Create a `.env.azure` file in the repository root:

```bash
# Copy template
cp infra/.env.example .env.azure

# Edit with your values
nano .env.azure
```

**Required values**:
```bash
# Azure Configuration
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_LOCATION=eastus
RESOURCE_PREFIX=techcon
ENVIRONMENT=dev

# GitHub OAuth
GITHUB_CLIENT_ID=<your-github-oauth-client-id>
GITHUB_CLIENT_SECRET=<your-github-oauth-client-secret>

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_KEY=<your-azure-openai-api-key>
AZURE_OPENAI_DEPLOYMENT=gpt-5

# Session Secret (generate with: openssl rand -hex 32)
SESSION_SECRET_KEY=<64-character-hex-string>

# Container Images (update after building)
BACKEND_DOCKER_IMAGE=ghcr.io/your-org/backend:latest
FRONTEND_DOCKER_IMAGE=ghcr.io/your-org/frontend:latest
```

**Generate session secret**:
```bash
openssl rand -hex 32
```

### Step 4: Validate Deployment

```bash
cd infra

# Validate template syntax
./scripts/validate.sh dev

# Output should show:
# ✅ Template validation passed
# ✅ Parameter file validated
```

### Step 5: Preview Changes

```bash
# Run what-if analysis
az deployment sub what-if \
  --location eastus \
  --template-file main.bicep \
  --parameters environment=dev location=eastus resourcePrefix=techcon \
  --parameters @parameters/dev.bicepparam

# Review the output - should show resources to be created (green +)
```

### Step 6: Deploy Infrastructure

```bash
# Deploy using convenience script
./scripts/deploy.sh dev

# OR deploy manually with Azure CLI
az deployment sub create \
  --name techcon-dev-deployment \
  --location eastus \
  --template-file main.bicep \
  --parameters @parameters/dev.bicepparam

# Deployment will take 3-5 minutes
```

**Expected Output**:
```
Deployment started...
Resource Group: Created ✓
Key Vault: Created ✓
Key Vault Secrets: Created ✓
App Service Plan: Created ✓
Backend App Service: Created ✓
Frontend App Service: Created ✓
Access Policies: Updated ✓

Deployment completed successfully!

Outputs:
  backendUrl: https://techcon-dev-backend.azurewebsites.net
  frontendUrl: https://techcon-dev-frontend.azurewebsites.net
  resourceGroupName: techcon-dev-rg
```

### Step 7: Verify Deployment

```bash
# List deployed resources
az resource list \
  --resource-group techcon-dev-rg \
  --output table

# Check backend health
curl https://techcon-dev-backend.azurewebsites.net/api/v1/health

# Expected: {"status":"healthy"}

# Check frontend (should return HTML)
curl https://techcon-dev-frontend.azurewebsites.net
```

### Step 8: Update GitHub OAuth Callback URL

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Open your OAuth App
3. Update **Authorization callback URL** to: `https://techcon-dev-frontend.azurewebsites.net/api/v1/auth/github/callback`
4. Save changes

---

## Deploying to Staging/Production

### Create Parameter File

```bash
cd infra/parameters

# Copy dev template
cp dev.bicepparam staging.bicepparam

# Edit for staging environment
nano staging.bicepparam
```

**Update values**:
```bicep
using '../main.bicep'

param environment = 'staging'  // Change to staging
param location = 'centralus'   // Different region
param resourcePrefix = 'techcon'
param appServiceSku = 'S1'     // Upgrade to Standard
param backendDockerImage = 'ghcr.io/your-org/backend:v1.0.0'  // Use tagged version
param frontendDockerImage = 'ghcr.io/your-org/frontend:v1.0.0'

// ... other parameters
```

### Deploy Staging

```bash
./scripts/deploy.sh staging

# OR manual deployment
az deployment sub create \
  --name techcon-staging-deployment \
  --location centralus \
  --template-file main.bicep \
  --parameters @parameters/staging.bicepparam
```

### Deploy Production (with approval)

```bash
# IMPORTANT: Always run what-if first in production
az deployment sub what-if \
  --location eastus2 \
  --template-file main.bicep \
  --parameters @parameters/production.bicepparam

# Review changes carefully
# If approved, deploy:
./scripts/deploy.sh production
```

---

## Post-Deployment Tasks

### 1. Configure Continuous Deployment

Enable continuous deployment from container registry:

```bash
# Enable CD webhook for backend
az webapp deployment container config \
  --enable-cd true \
  --name techcon-dev-backend \
  --resource-group techcon-dev-rg

# Enable CD webhook for frontend
az webapp deployment container config \
  --enable-cd true \
  --name techcon-dev-frontend \
  --resource-group techcon-dev-rg
```

### 2. View Logs

```bash
# Stream backend logs
az webapp log tail \
  --name techcon-dev-backend \
  --resource-group techcon-dev-rg

# Stream frontend logs
az webapp log tail \
  --name techcon-dev-frontend \
  --resource-group techcon-dev-rg
```

### 3. Access Application

**Development Environment**:
- Frontend: https://techcon-dev-frontend.azurewebsites.net
- Backend: https://techcon-dev-backend.azurewebsites.net
- Health Check: https://techcon-dev-backend.azurewebsites.net/api/v1/health

### 4. Configure Custom Domain (Optional)

For production deployments with custom domain:

```bash
# Add custom domain
az webapp config hostname add \
  --webapp-name techcon-prod-frontend \
  --resource-group techcon-prod-rg \
  --hostname www.yourdomain.com

# Bind SSL certificate (free managed certificate)
az webapp config ssl bind \
  --certificate-thumbprint auto \
  --ssl-type SNI \
  --name techcon-prod-frontend \
  --resource-group techcon-prod-rg
```

---

## Updating Infrastructure

### Update Configuration

```bash
# Edit parameter file
nano parameters/dev.bicepparam

# Validate changes
./scripts/validate.sh dev

# Preview changes
az deployment sub what-if \
  --location eastus \
  --template-file main.bicep \
  --parameters @parameters/dev.bicepparam

# Apply changes (idempotent)
./scripts/deploy.sh dev
```

### Update Container Images

```bash
# Update image tag in parameter file
nano parameters/dev.bicepparam

# Change:
param backendDockerImage = 'ghcr.io/org/backend:v1.1.0'

# Redeploy (only updates app settings)
./scripts/deploy.sh dev

# Restart apps to pull new image
az webapp restart --name techcon-dev-backend --resource-group techcon-dev-rg
az webapp restart --name techcon-dev-frontend --resource-group techcon-dev-rg
```

---

## Cleanup

### Delete Development Environment

```bash
# Delete entire resource group (WARNING: irreversible)
az group delete \
  --name techcon-dev-rg \
  --yes

# Key Vault will be soft-deleted (90-day retention)
# To permanently purge:
az keyvault purge \
  --name techcon-dev-kv-<hash> \
  --location eastus
```

### Delete Specific Resources

```bash
# Delete only web apps (keep infrastructure)
az webapp delete --name techcon-dev-backend --resource-group techcon-dev-rg
az webapp delete --name techcon-dev-frontend --resource-group techcon-dev-rg
```

---

## Troubleshooting

### Error: "The resource name is invalid"

**Cause**: Resource naming constraints violated  
**Solution**:
- Resource prefix must be lowercase alphanumeric + hyphens only
- Total resource name must not exceed max length:
  - App Service: 60 characters
  - Key Vault: 24 characters
- Check parameters file: `resourcePrefix` value

```bash
# Valid examples
resourcePrefix = 'techcon'
resourcePrefix = 'tc-app'

# Invalid examples
resourcePrefix = 'TechCon'      # Uppercase not allowed
resourcePrefix = 'tech_connect' # Underscores not allowed
```

### Error: "Key Vault name already exists"

**Cause**: Key Vault names are globally unique across all Azure  
**Solution**:
- Change `resourcePrefix` parameter to something unique
- OR wait 90 days for soft-deleted vault to be purged
- OR purge manually if you have permissions:

```bash
# List soft-deleted vaults
az keyvault list-deleted

# Purge specific vault
az keyvault purge --name <vault-name> --location <location>
```

### Error: "Insufficient permissions"

**Cause**: Inadequate Azure RBAC permissions  
**Solution**:
- Verify you have Contributor role on subscription:
  ```bash
  az role assignment list --assignee <your-email> --output table
  ```
- Request Owner or Contributor role from subscription admin
- For Key Vault operations, may need "Key Vault Administrator" role

### Error: "Subscription quota exceeded"

**Cause**: Azure resource quotas reached  
**Solution**:
- Check current quota:
  ```bash
  az vm list-usage --location eastus --output table
  ```
- Request quota increase in Azure Portal (Support → New support request)
- Use different region with available capacity

### Error: "Container image not found"

**Cause**: Docker image specified in parameters doesn't exist or is private  
**Solution**:
- Verify image exists:
  ```bash
  docker pull <image-name>
  ```
- For private registries, configure App Service credentials:
  ```bash
  az webapp config container set \
    --name techcon-dev-backend \
    --resource-group techcon-dev-rg \
    --docker-custom-image-name <image> \
    --docker-registry-server-url https://ghcr.io \
    --docker-registry-server-user <username> \
    --docker-registry-server-password <token>
  ```

### Health Check Failing

**Cause**: Application not starting or health endpoint returning errors  
**Solution**:
- Check application logs:
  ```bash
  az webapp log tail --name techcon-dev-backend --resource-group techcon-dev-rg
  ```
- Verify environment variables are set correctly:
  ```bash
  az webapp config appsettings list \
    --name techcon-dev-backend \
    --resource-group techcon-dev-rg
  ```
- Ensure Key Vault references are resolving (check for `@Microsoft.KeyVault...` in output)
- Verify container starts successfully locally:
  ```bash
  docker run --rm -p 8000:8000 <backend-image>
  curl http://localhost:8000/api/v1/health
  ```

---

## Next Steps

1. **Configure CI/CD Pipeline**: Set up GitHub Actions to automatically deploy on push
2. **Enable Monitoring**: Configure Application Insights for logging and metrics
3. **Set Up Alerts**: Create Azure Monitor alerts for failures and performance issues
4. **Configure Auto-scaling**: Add auto-scaling rules for production environments
5. **Enable Backups**: Configure Key Vault backup and App Service snapshots

---

## Additional Resources

- [Azure App Service Documentation](https://learn.microsoft.com/en-us/azure/app-service/)
- [Azure Bicep Documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Azure Key Vault Best Practices](https://learn.microsoft.com/en-us/azure/key-vault/general/best-practices)
- [Main Project README](../../../README.md)

---

**Support**: For issues specific to this infrastructure, open an issue in the repository.  
**Deployment Time**: Development ~5 minutes, Production ~15-20 minutes (with review)
