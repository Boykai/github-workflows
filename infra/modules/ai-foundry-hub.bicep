@description('Name of the AI Foundry hub')
param name string

@description('Azure region for deployment')
param location string

@description('Resource ID of the Key Vault')
param keyVaultId string

@description('Resource ID of the Log Analytics workspace')
param logAnalyticsId string

@description('Resource tags')
param tags object = {}

resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: name
  location: location
  tags: tags
  kind: 'Hub'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  properties: {
    friendlyName: name
    keyVault: keyVaultId
    applicationInsights: logAnalyticsId
  }
}

@description('Resource ID of the AI Foundry hub')
output id string = aiHub.id

@description('Name of the AI Foundry hub')
output hubName string = aiHub.name
