@description('Short project identifier (alphanumeric, lowercase)')
param projectName string

@description('Deployment environment')
param environment string = 'prod'

@description('Azure region')
param location string = resourceGroup().location

@description('GitHub personal access token for API access')
@secure()
param githubToken string

@description('Azure OpenAI model deployment name')
param modelDeploymentName string = 'gpt-41'

@description('Azure OpenAI model capacity (thousands of tokens per minute)')
param modelCapacity int = 10

@description('Backend container image')
param backendImage string = ''

@description('Frontend container image')
param frontendImage string = ''

// ── Resource Naming (Azure CAF conventions) ──────────────────────────
var naming = {
  logAnalytics: 'law-${projectName}-${environment}'
  managedIdentity: 'id-${projectName}-${environment}'
  containerRegistry: 'cr${projectName}${environment}'
  keyVault: 'kv-${projectName}-${environment}'
  openAI: 'aoai-${projectName}-${environment}'
  aiHub: 'aih-${projectName}-${environment}'
  aiProject: 'aip-${projectName}-${environment}'
  containerAppsEnv: 'cae-${projectName}-${environment}'
  backendApp: 'ca-${projectName}-backend-${environment}'
  frontendApp: 'ca-${projectName}-frontend-${environment}'
}

var tags = {
  project: projectName
  environment: environment
  managedBy: 'bicep'
}

var resolvedBackendImage = !empty(backendImage) ? backendImage : '${naming.containerRegistry}.azurecr.io/backend:latest'
var resolvedFrontendImage = !empty(frontendImage) ? frontendImage : '${naming.containerRegistry}.azurecr.io/frontend:latest'

// ── 1. Log Analytics ─────────────────────────────────────────────────
module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'logAnalytics'
  params: {
    name: naming.logAnalytics
    location: location
    tags: tags
  }
}

// ── 2. Managed Identity ──────────────────────────────────────────────
module managedIdentity 'modules/managed-identity.bicep' = {
  name: 'managedIdentity'
  params: {
    name: naming.managedIdentity
    location: location
    tags: tags
  }
}

// ── 3. Container Registry ────────────────────────────────────────────
module containerRegistry 'modules/container-registry.bicep' = {
  name: 'containerRegistry'
  params: {
    name: naming.containerRegistry
    location: location
    acrPullPrincipalId: managedIdentity.outputs.principalId
    tags: tags
  }
}

// ── 4. Azure OpenAI ──────────────────────────────────────────────────
module openAI 'modules/openai.bicep' = {
  name: 'openAI'
  params: {
    name: naming.openAI
    location: location
    openAIUserPrincipalId: managedIdentity.outputs.principalId
    modelDeploymentName: modelDeploymentName
    modelCapacity: modelCapacity
    tags: tags
  }
}

// ── 5. Key Vault ─────────────────────────────────────────────────────
module keyVault 'modules/key-vault.bicep' = {
  name: 'keyVault'
  params: {
    name: naming.keyVault
    location: location
    tenantId: subscription().tenantId
    secretsUserPrincipalId: managedIdentity.outputs.principalId
    githubToken: githubToken
    azureOpenAIEndpoint: openAI.outputs.endpoint
    azureOpenAIDeployment: openAI.outputs.deploymentName
    tags: tags
  }
}

// ── 6. AI Foundry Hub ────────────────────────────────────────────────
module aiHub 'modules/ai-foundry-hub.bicep' = {
  name: 'aiHub'
  params: {
    name: naming.aiHub
    location: location
    keyVaultId: keyVault.outputs.id
    logAnalyticsId: logAnalytics.outputs.id
    tags: tags
  }
}

// ── 7. AI Foundry Project ────────────────────────────────────────────
module aiProject 'modules/ai-foundry-project.bicep' = {
  name: 'aiProject'
  params: {
    name: naming.aiProject
    location: location
    hubId: aiHub.outputs.id
    tags: tags
  }
}

// ── 8. Container Apps Environment ────────────────────────────────────
module containerAppsEnv 'modules/container-apps-environment.bicep' = {
  name: 'containerAppsEnv'
  params: {
    name: naming.containerAppsEnv
    location: location
    logAnalyticsCustomerId: logAnalytics.outputs.customerId
    logAnalyticsPrimarySharedKey: logAnalytics.outputs.primarySharedKey
    tags: tags
  }
}

// ── 9. Backend Container App ─────────────────────────────────────────
module backendApp 'modules/container-app-backend.bicep' = {
  name: 'backendApp'
  params: {
    name: naming.backendApp
    location: location
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerImage: resolvedBackendImage
    managedIdentityId: managedIdentity.outputs.id
    managedIdentityClientId: managedIdentity.outputs.clientId
    keyVaultName: naming.keyVault
    tags: tags
  }
}

// ── 10. Frontend Container App ───────────────────────────────────────
module frontendApp 'modules/container-app-frontend.bicep' = {
  name: 'frontendApp'
  params: {
    name: naming.frontendApp
    location: location
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerImage: resolvedFrontendImage
    managedIdentityId: managedIdentity.outputs.id
    backendFqdn: backendApp.outputs.fqdn
    tags: tags
  }
}

// ── Outputs ──────────────────────────────────────────────────────────
@description('Container Registry login server')
output acrLoginServer string = containerRegistry.outputs.loginServer

@description('Backend Container App FQDN')
output backendFqdn string = backendApp.outputs.fqdn

@description('Frontend Container App FQDN')
output frontendFqdn string = frontendApp.outputs.fqdn

@description('Key Vault URI')
output keyVaultUri string = keyVault.outputs.uri

@description('Azure OpenAI endpoint')
output openAIEndpoint string = openAI.outputs.endpoint

@description('Managed Identity Client ID')
output managedIdentityClientId string = managedIdentity.outputs.clientId
