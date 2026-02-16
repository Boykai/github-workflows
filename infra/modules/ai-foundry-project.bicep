@description('Name of the AI Foundry project')
param name string

@description('Azure region for deployment')
param location string

@description('Resource ID of the AI Foundry hub')
param hubId string

@description('Resource tags')
param tags object = {}

resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: name
  location: location
  tags: tags
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  properties: {
    friendlyName: name
    hubResourceId: hubId
  }
}

@description('Resource ID of the AI Foundry project')
output id string = aiProject.id
