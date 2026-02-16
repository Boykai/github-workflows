@description('Name of the Azure OpenAI resource')
param name string

@description('Azure region for deployment')
param location string

@description('Principal ID to grant Cognitive Services OpenAI User role')
param openAIUserPrincipalId string

@description('Model deployment name')
param modelDeploymentName string = 'gpt-41'

@description('Model capacity in thousands of tokens per minute')
param modelCapacity int = 10

@description('Resource tags')
param tags object = {}

resource openAI 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: name
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
  }
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAI
  name: modelDeploymentName
  sku: {
    name: 'Standard'
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1'
      version: '2025-04-14'
    }
  }
}

// Cognitive Services OpenAI User role assignment
resource openAIUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAI.id, openAIUserPrincipalId, 'CognitiveServicesOpenAIUser')
  scope: openAI
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd') // Cognitive Services OpenAI User
    principalId: openAIUserPrincipalId
    principalType: 'ServicePrincipal'
  }
}

@description('Endpoint of the Azure OpenAI resource')
output endpoint string = openAI.properties.endpoint

@description('Deployment name of the model')
output deploymentName string = modelDeployment.name

@description('Resource ID of the Azure OpenAI resource')
output id string = openAI.id
