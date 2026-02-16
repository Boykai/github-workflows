@description('Name of the container registry')
param name string

@description('Azure region for deployment')
param location string

@description('Principal ID to grant AcrPull role')
param acrPullPrincipalId string

@description('Resource tags')
param tags object = {}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
}

// AcrPull role assignment for managed identity
resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, acrPullPrincipalId, 'AcrPull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: acrPullPrincipalId
    principalType: 'ServicePrincipal'
  }
}

@description('Login server of the container registry')
output loginServer string = acr.properties.loginServer

@description('Resource ID of the container registry')
output id string = acr.id
