using 'main.bicep'

param projectName = 'ghprojectschat'
param environment = 'prod'
param location = 'eastus2'
param githubToken = readEnvironmentVariable('GITHUB_TOKEN_VALUE', '')
param modelDeploymentName = 'gpt-41'
param modelCapacity = 10
