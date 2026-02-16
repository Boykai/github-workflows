@description('Name of the Container Apps environment')
param name string

@description('Azure region for deployment')
param location string

@description('Resource ID of the Log Analytics workspace')
param logAnalyticsCustomerId string

@description('Primary shared key of the Log Analytics workspace')
@secure()
param logAnalyticsPrimarySharedKey string

@description('Resource tags')
param tags object = {}

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsPrimarySharedKey
      }
    }
    zoneRedundant: false
  }
}

@description('Resource ID of the Container Apps environment')
output id string = containerAppsEnv.id

@description('Default domain of the Container Apps environment')
output defaultDomain string = containerAppsEnv.properties.defaultDomain
