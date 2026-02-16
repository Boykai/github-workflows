@description('Name of the Key Vault')
param name string

@description('Azure region for deployment')
param location string

@description('Tenant ID for the Key Vault')
param tenantId string

@description('Principal ID to grant Key Vault Secrets User role')
param secretsUserPrincipalId string

@description('GitHub personal access token')
@secure()
param githubToken string

@description('Azure OpenAI endpoint URL')
param azureOpenAIEndpoint string

@description('Azure OpenAI deployment name')
param azureOpenAIDeployment string

@description('Resource tags')
param tags object = {}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    enablePurgeProtection: true
    softDeleteRetentionInDays: 90
  }
}

// Key Vault Secrets User role assignment for managed identity
resource secretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, secretsUserPrincipalId, 'KeyVaultSecretsUser')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: secretsUserPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Store secrets
resource githubTokenSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'GITHUB-TOKEN'
  properties: {
    value: githubToken
  }
}

resource openAIEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AZURE-OPENAI-ENDPOINT'
  properties: {
    value: azureOpenAIEndpoint
  }
}

resource openAIDeploymentSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AZURE-OPENAI-DEPLOYMENT'
  properties: {
    value: azureOpenAIDeployment
  }
}

@description('Resource ID of the Key Vault')
output id string = keyVault.id

@description('URI of the Key Vault')
output uri string = keyVault.properties.vaultUri
