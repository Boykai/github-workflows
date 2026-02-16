@description('Name of the Log Analytics workspace')
param name string

@description('Azure region for deployment')
param location string

@description('Resource tags')
param tags object = {}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

@description('Resource ID of the Log Analytics workspace')
output id string = logAnalytics.id

@description('Customer ID of the Log Analytics workspace')
output customerId string = logAnalytics.properties.customerId

@description('Primary shared key of the Log Analytics workspace')
output primarySharedKey string = logAnalytics.listKeys().primarySharedKey
