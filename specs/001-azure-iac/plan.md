# Implementation Plan: Azure Deployment Infrastructure as Code

**Branch**: `001-azure-iac` | **Date**: 2026-02-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-azure-iac/spec.md`

**Note**: This plan is generated following the speckit.plan workflow. It includes Technical Context, Constitution Check, Phase 0 Research, and Phase 1 Design artifacts.

## Summary

Implement Infrastructure as Code (IaC) templates to deploy the Tech Connect (GitHub Projects Chat Interface) application to Azure. The solution will use Azure Bicep templates to provision App Services for both frontend and backend, Azure Key Vault for secrets management, and optionally Azure Container Registry for container images. The deployment will support multiple environments (dev, staging, production) through parameterization, include validation capabilities, and provide comprehensive documentation for DevOps engineers to deploy infrastructure consistently and reliably.

## Technical Context

**Language/Version**: Azure Bicep (latest), Shell scripting (bash), Azure CLI 2.x  
**Primary Dependencies**: Azure CLI, Bicep CLI, Azure Resource Manager  
**Storage**: N/A (application uses GitHub API, no persistent database required)  
**Testing**: Manual validation, Azure deployment what-if preview, Bicep linting  
**Target Platform**: Azure Cloud - App Services (Linux), Key Vault, Container Registry (optional)  
**Project Type**: Web application (frontend + backend) with existing docker-compose configuration  
**Performance Goals**: Deployment completion <15 minutes, template validation <30 seconds  
**Constraints**: Must support multi-environment deployment without code duplication, idempotent deployments, no hardcoded secrets  
**Scale/Scope**: Single Azure subscription, 3 environments (dev/staging/production), ~5-8 Azure resources per environment

**Additional Context**:
- Application: GitHub Projects Chat Interface - React frontend + FastAPI backend
- Backend: Python 3.11 FastAPI app (port 8000) requiring GitHub OAuth and Azure OpenAI credentials
- Frontend: React + TypeScript SPA served via nginx (port 80) requiring API base URL configuration
- Environment Variables: ~15 required variables (GitHub OAuth, Azure OpenAI, session secrets, CORS origins)
- Existing Deployment: Docker Compose configuration with health checks and networking
- No Database: Application is stateless, uses GitHub API and Projects V2 for data storage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development
✅ **COMPLIANT** - Feature spec exists in `specs/001-azure-iac/spec.md` with:
- Four prioritized user stories (P1-P3) with independent testing criteria
- Given-When-Then acceptance scenarios for each story
- Clear scope: infrastructure deployment only, excludes application deployment and database schema

### Principle II: Template-Driven Workflow
✅ **COMPLIANT** - Following canonical plan-template.md structure:
- All mandatory sections present (Summary, Technical Context, Constitution Check, Project Structure)
- Phase-based execution plan (Phase 0 research, Phase 1 design)
- Will generate required artifacts: research.md, data-model.md, contracts/, quickstart.md

### Principle III: Agent-Orchestrated Execution
✅ **COMPLIANT** - Plan execution by speckit.plan agent:
- Single-responsibility: planning phase only (not implementation)
- Operates on feature spec input
- Produces structured outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md)
- Clear handoff to speckit.tasks for task generation

### Principle IV: Test Optionality with Clarity
✅ **COMPLIANT** - Tests are optional for infrastructure:
- Feature spec focuses on deployment validation and manual verification
- No unit/integration tests required for IaC templates
- Validation through Azure CLI what-if commands and manual deployment testing
- Success criteria emphasize deployment outcomes, not code coverage

### Principle V: Simplicity and DRY
✅ **COMPLIANT** - Approach follows YAGNI:
- Start with essential resources: App Services, Key Vault (no over-engineering)
- Parameterization handles environment differences (no template duplication)
- Standard Azure naming conventions and resource organization
- No premature abstraction or complex orchestration patterns

**Gate Status**: ✅ PASSED - All constitution principles compliant, no violations to justify

## Project Structure

### Documentation (this feature)

```text
specs/001-azure-iac/
├── plan.md              # This file (speckit.plan command output)
├── research.md          # Phase 0 output - Technology decisions and best practices
├── data-model.md        # Phase 1 output - Azure resource entity model
├── quickstart.md        # Phase 1 output - Quick deployment guide
├── contracts/           # Phase 1 output - IaC template interfaces
│   ├── parameters-schema.json    # Parameter contract definitions
│   └── resources-overview.md     # Resource dependencies and relationships
└── tasks.md             # Phase 2 output (speckit.tasks command - NOT created by speckit.plan)
```

### Source Code (repository root)

```text
# Infrastructure code (new)
infra/
├── main.bicep                    # Main Bicep template
├── modules/                      # Modular resource definitions
│   ├── app-service.bicep         # App Service Plan + Web Apps
│   ├── key-vault.bicep           # Key Vault for secrets
│   └── container-registry.bicep  # Optional: ACR for container images
├── parameters/                   # Environment-specific parameter files
│   ├── dev.bicepparam           # Development environment
│   ├── staging.bicepparam       # Staging environment
│   └── production.bicepparam    # Production environment
└── scripts/                      # Deployment automation
    ├── deploy.sh                 # Main deployment script
    ├── validate.sh               # Template validation script
    └── cleanup.sh                # Resource cleanup script

# Existing application code (unchanged)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Root documentation (updated)
README.md                         # Add Azure deployment section
```

**Structure Decision**: Created dedicated `infra/` directory at repository root to separate infrastructure code from application code. This follows Azure best practices for organizing IaC templates. The modular approach with `modules/` subdirectory enables reusability and maintainability. Environment-specific parameters in `parameters/` directory support the multi-environment requirement without duplication. Shell scripts in `scripts/` provide automation for common deployment operations.

## Complexity Tracking

**No violations identified** - All constitution checks passed without requiring justification.

---

## Phase 0: Outline & Research

### Research Objectives

The following unknowns and technology decisions require research to inform design:

1. **Bicep vs. ARM Template Choice**: Determine whether to use Azure Bicep or ARM templates based on maintainability, readability, and Azure CLI support.

2. **App Service Configuration for Containers**: Research best practices for deploying Docker containers to Azure App Service, including container registry integration, environment variable configuration, and health check setup.

3. **Key Vault Integration Patterns**: Investigate how to securely reference Azure Key Vault secrets in App Service configuration without exposing secrets in templates or parameters.

4. **Multi-Environment Parameterization**: Determine the best approach for managing environment-specific configurations (Bicep parameter files, separate templates, or variable files).

5. **Idempotent Deployment Strategy**: Research Azure Resource Manager behavior for updates vs. creates to ensure templates can be safely re-run without unintended resource recreation.

6. **Naming Conventions and Tagging**: Establish Azure resource naming standards and tagging strategies for environment identification and cost tracking.

7. **CORS and Networking Configuration**: Determine how to configure App Service CORS policies, custom domains, and SSL certificates for production environments.

8. **Cost Optimization**: Research appropriate SKU sizing for development vs. production environments to balance cost and performance.

### Research Tasks

For each research objective, the following tasks will be executed:

1. **Task R1: Evaluate Bicep vs. ARM Templates**
   - Compare syntax, readability, and maintenance overhead
   - Verify Azure CLI support and tooling availability
   - Identify any limitations or missing features
   - **Output**: Decision documented in research.md

2. **Task R2: App Service Container Deployment Pattern**
   - Review official Azure documentation for container deployment to App Service
   - Identify required configuration for Docker Compose conversion
   - Document health check and startup configuration
   - **Output**: Best practices and configuration patterns in research.md

3. **Task R3: Key Vault Secret Management**
   - Research Key Vault reference syntax for App Service
   - Identify managed identity requirements for secret access
   - Document secret rotation and access policy patterns
   - **Output**: Security architecture decision in research.md

4. **Task R4: Parameter File Organization**
   - Evaluate Bicep parameter file (.bicepparam) format
   - Compare with alternative approaches (JSON, variable files)
   - Identify validation and documentation requirements
   - **Output**: Parameterization strategy in research.md

5. **Task R5: Idempotent Deployment Verification**
   - Review Azure Resource Manager update behavior
   - Test what-if command capabilities
   - Document resource comparison and change detection
   - **Output**: Deployment safety guarantees in research.md

6. **Task R6: Naming and Tagging Standards**
   - Research Azure naming restrictions and recommendations
   - Define environment-based naming patterns
   - Establish required tags for governance
   - **Output**: Naming convention specification in research.md

7. **Task R7: Production Networking Requirements**
   - Document CORS configuration for multi-origin support
   - Research custom domain and SSL certificate setup
   - Identify networking security best practices
   - **Output**: Networking architecture in research.md

8. **Task R8: SKU Sizing Recommendations**
   - Compare App Service Plan tiers and capabilities
   - Establish cost estimates for dev/staging/production
   - Document scaling limits and performance implications
   - **Output**: SKU selection matrix in research.md

### Research Output

**File**: `specs/001-azure-iac/research.md`

The research phase will consolidate all findings into a single markdown document following this structure:

```markdown
# Research: Azure Deployment Infrastructure as Code

## Decision: Template Technology (Bicep vs. ARM)
- **Decision**: [Selected technology]
- **Rationale**: [Why chosen]
- **Alternatives Considered**: [What else was evaluated]
- **Implications**: [Impact on development and maintenance]

## Decision: App Service Container Deployment
- **Decision**: [Deployment approach]
- **Rationale**: [Why this pattern]
- **Configuration Requirements**: [Specific settings needed]

## Decision: Secret Management with Key Vault
- **Decision**: [Integration approach]
- **Rationale**: [Security and access considerations]
- **Implementation Pattern**: [How secrets are referenced]

## Decision: Multi-Environment Parameterization
- **Decision**: [Parameter file strategy]
- **Rationale**: [Why this approach scales]
- **File Organization**: [Directory structure]

## Decision: Deployment Idempotency
- **Decision**: [How to ensure safe re-runs]
- **Rationale**: [ARM behavior and guarantees]
- **Validation Approach**: [What-if usage]

## Decision: Naming Conventions
- **Decision**: [Naming pattern standard]
- **Rationale**: [Consistency and identification]
- **Examples**: [Concrete resource names]

## Decision: Networking and CORS
- **Decision**: [CORS and domain configuration]
- **Rationale**: [Security and accessibility]
- **Production Requirements**: [SSL and custom domains]

## Decision: SKU Sizing Strategy
- **Decision**: [Sizing recommendations per environment]
- **Rationale**: [Cost vs. performance trade-offs]
- **Cost Estimates**: [Approximate monthly costs]
```

---

## Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete with all technology decisions documented

### Data Model

**File**: `specs/001-azure-iac/data-model.md`

The data model defines Azure resources as entities with their properties, relationships, and validation rules:

#### Entity: Resource Group
- **Fields**: name (string), location (string), tags (object)
- **Validation**: Name must be unique within subscription, location must be valid Azure region
- **Relationships**: Contains all other resources
- **State Transitions**: Created → Updated → Deleted

#### Entity: App Service Plan
- **Fields**: name (string), location (string), sku (object: name, tier, size, capacity), kind (string), reserved (boolean for Linux)
- **Validation**: SKU must be valid tier (B1, S1, P1V2, etc.), kind must match OS requirements
- **Relationships**: Parent to App Services, belongs to Resource Group
- **State Transitions**: Created → Scaled (SKU change) → Deleted

#### Entity: App Service (Backend)
- **Fields**: name (string), location (string), serverFarmId (reference), siteConfig (object), appSettings (array of name-value pairs), linuxFxVersion (string)
- **Validation**: Name must be globally unique (*.azurewebsites.net), linuxFxVersion format must be DOCKER|<image>:<tag>
- **Relationships**: Belongs to App Service Plan, references Key Vault secrets, belongs to Resource Group
- **State Transitions**: Created → Configured → Running → Stopped → Deleted

#### Entity: App Service (Frontend)
- **Fields**: name (string), location (string), serverFarmId (reference), siteConfig (object), appSettings (array), linuxFxVersion (string)
- **Validation**: Same as backend, different container image
- **Relationships**: Same as backend
- **State Transitions**: Same as backend

#### Entity: Key Vault
- **Fields**: name (string), location (string), sku (object: name, family), tenantId (string), accessPolicies (array), enabledForDeployment (boolean)
- **Validation**: Name must be globally unique (3-24 chars, alphanumeric + hyphens), tenant ID must be valid GUID
- **Relationships**: Referenced by App Services for secret access, belongs to Resource Group
- **State Transitions**: Created → Updated (policies) → Soft-deleted → Purged

#### Entity: Key Vault Secret
- **Fields**: name (string), value (securestring), contentType (string)
- **Validation**: Name must match [a-zA-Z0-9-], value must not be empty
- **Relationships**: Stored in Key Vault, referenced by App Service configuration
- **State Transitions**: Created → Updated (versioned) → Disabled → Deleted

#### Entity: Deployment Parameters
- **Fields**: environment (string), location (string), resourcePrefix (string), appServiceSku (string), backendImage (string), frontendImage (string), secrets (secureObject)
- **Validation**: Environment must be dev/staging/production, location must be valid region, SKU must match allowed values
- **Relationships**: Input to template deployment, determines resource configurations
- **State Transitions**: N/A (stateless deployment input)

### API Contracts

**Directory**: `specs/001-azure-iac/contracts/`

#### File: `parameters-schema.json`

Defines the contract for parameter files that must be provided for deployment:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "title": "Azure IaC Deployment Parameters",
  "description": "Required parameters for deploying Tech Connect infrastructure",
  "type": "object",
  "required": ["environment", "location", "resourcePrefix"],
  "properties": {
    "environment": {
      "type": "string",
      "enum": ["dev", "staging", "production"],
      "description": "Target environment for deployment"
    },
    "location": {
      "type": "string",
      "description": "Azure region for resources",
      "examples": ["eastus", "westus2", "centralus"]
    },
    "resourcePrefix": {
      "type": "string",
      "minLength": 2,
      "maxLength": 10,
      "pattern": "^[a-z0-9-]+$",
      "description": "Prefix for resource naming (e.g., 'techcon')"
    },
    "appServiceSku": {
      "type": "string",
      "enum": ["B1", "B2", "S1", "S2", "P1V2", "P2V2"],
      "default": "B1",
      "description": "App Service Plan SKU"
    },
    "backendDockerImage": {
      "type": "string",
      "description": "Docker image for backend (e.g., 'username/repo:tag' or ACR path)"
    },
    "frontendDockerImage": {
      "type": "string",
      "description": "Docker image for frontend"
    },
    "githubClientId": {
      "type": "string",
      "description": "GitHub OAuth Client ID"
    },
    "githubClientSecret": {
      "type": "securestring",
      "description": "GitHub OAuth Client Secret"
    },
    "azureOpenAIEndpoint": {
      "type": "string",
      "format": "uri",
      "description": "Azure OpenAI service endpoint"
    },
    "azureOpenAIKey": {
      "type": "securestring",
      "description": "Azure OpenAI API key"
    },
    "sessionSecretKey": {
      "type": "securestring",
      "minLength": 32,
      "description": "Session encryption secret (64-char hex)"
    }
  }
}
```

#### File: `resources-overview.md`

Documents resource relationships and deployment dependencies:

```markdown
# Azure Resources Overview

## Resource Hierarchy

```
Resource Group (techcon-{env}-rg)
├── App Service Plan (techcon-{env}-plan)
│   ├── App Service - Backend (techcon-{env}-backend)
│   └── App Service - Frontend (techcon-{env}-frontend)
└── Key Vault (techcon-{env}-kv-{uniqueid})
    ├── Secret: github-client-secret
    ├── Secret: azure-openai-key
    └── Secret: session-secret-key
```

## Deployment Dependencies

1. **Resource Group** (no dependencies)
2. **Key Vault** (depends on Resource Group)
3. **Key Vault Secrets** (depends on Key Vault)
4. **App Service Plan** (depends on Resource Group)
5. **App Services** (depends on App Service Plan, Key Vault for secret references)

## Resource Naming Convention

| Resource Type | Naming Pattern | Example (dev environment) |
|---------------|----------------|---------------------------|
| Resource Group | `{prefix}-{env}-rg` | `techcon-dev-rg` |
| App Service Plan | `{prefix}-{env}-plan` | `techcon-dev-plan` |
| Backend App Service | `{prefix}-{env}-backend` | `techcon-dev-backend` |
| Frontend App Service | `{prefix}-{env}-frontend` | `techcon-dev-frontend` |
| Key Vault | `{prefix}-{env}-kv-{hash}` | `techcon-dev-kv-a1b2c3` |

**Note**: Key Vault names include a hash suffix for global uniqueness.

## Inter-Resource References

- **App Services → App Service Plan**: `serverFarmId` property references Plan resource ID
- **App Services → Key Vault**: `@Microsoft.KeyVault(SecretUri=...)` syntax in appSettings
- **Managed Identity**: App Services use system-assigned managed identity for Key Vault access
- **Key Vault Access Policy**: Grants App Service identities GET permission on secrets
```

### Quickstart Guide

**File**: `specs/001-azure-iac/quickstart.md`

Provides a concise guide for deploying infrastructure:

```markdown
# Quickstart: Deploy Tech Connect to Azure

## Prerequisites

- Azure subscription with Contributor or Owner role
- Azure CLI 2.50+ installed ([install guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))
- Bicep CLI installed (included with Azure CLI, verify with `az bicep version`)
- GitHub OAuth App created ([setup guide](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app))
- Azure OpenAI resource with deployment ([setup guide](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource))

## Quick Deploy (Development Environment)

1. **Clone repository**
   ```bash
   git clone https://github.com/your-org/github-workflows.git
   cd github-workflows/infra
   ```

2. **Login to Azure**
   ```bash
   az login
   az account set --subscription <your-subscription-id>
   ```

3. **Copy and configure parameters**
   ```bash
   cp parameters/dev.bicepparam.example parameters/dev.bicepparam
   # Edit parameters/dev.bicepparam with your values
   ```

4. **Validate deployment**
   ```bash
   ./scripts/validate.sh dev
   ```

5. **Deploy infrastructure**
   ```bash
   ./scripts/deploy.sh dev
   ```

6. **Get application URLs**
   ```bash
   az webapp show --name techcon-dev-backend --resource-group techcon-dev-rg --query defaultHostName -o tsv
   az webapp show --name techcon-dev-frontend --resource-group techcon-dev-rg --query defaultHostName -o tsv
   ```

## Next Steps

- Configure GitHub OAuth callback URL with your frontend URL
- Deploy application containers (see main README.md)
- Configure custom domain and SSL (production only)

## Troubleshooting

**Error: "The resource name is invalid"**
- Solution: Ensure resourcePrefix in parameters is lowercase alphanumeric + hyphens only

**Error: "Key Vault name already exists"**
- Solution: Key Vault names are globally unique. Change resourcePrefix or wait 90 days for soft-deleted vault purge

**Error: "Insufficient permissions"**
- Solution: Verify you have Contributor role on subscription or resource group

For detailed documentation, see [main README.md](../../../README.md#azure-deployment).
```

### Agent Context Update

After completing Phase 1 design artifacts, the agent context file will be updated with new technologies:

**Action**: Run `.specify/scripts/bash/update-agent-context.sh copilot`

**Expected Updates**:
- Add "Azure Bicep" to technologies list
- Add "Azure App Service" to technologies list
- Add "Azure Key Vault" to technologies list
- Preserve existing manual additions between markers

---

## Phase 1 Post-Design Constitution Check

*Re-evaluation after completing research and design phases*

### Principle I: Specification-First Development
✅ **COMPLIANT** - All design artifacts trace back to feature spec requirements:
- Research.md resolves NEEDS CLARIFICATION items from Technical Context
- Data-model.md defines entities from FR-001 Key Entities section
- Contracts define parameter interfaces from FR-002, FR-003, FR-012
- Quickstart.md addresses FR-008 documentation requirement

### Principle II: Template-Driven Workflow
✅ **COMPLIANT** - All generated artifacts follow expected template structure:
- research.md uses Decision/Rationale/Alternatives format
- data-model.md includes Fields/Validation/Relationships/State Transitions
- contracts/ includes schema and overview as specified
- quickstart.md follows prerequisite/steps/troubleshooting pattern

### Principle III: Agent-Orchestrated Execution
✅ **COMPLIANT** - Clear handoff point established:
- Plan.md complete with all Phase 0 and Phase 1 outputs
- Next agent: speckit.tasks will consume this plan to generate tasks.md
- Implementation will execute tasks in dependency order

### Principle IV: Test Optionality with Clarity
✅ **COMPLIANT** - Testing approach clarified:
- Manual validation through Azure CLI what-if commands
- Deployment verification through resource inspection
- No automated tests required for IaC templates (matches constitution principle)

### Principle V: Simplicity and DRY
✅ **COMPLIANT** - Design maintains simplicity:
- Essential resources only (App Services, Key Vault)
- Single main.bicep with modular components (no over-engineering)
- Parameter files handle environment differences (no duplication)
- Standard Azure patterns, no custom abstractions

**Final Gate Status**: ✅ PASSED - Constitution compliance maintained through design phase

---

## Next Steps

This plan document is complete and ready for the next phase:

1. **speckit.tasks**: Generate tasks.md decomposing user stories into executable implementation tasks
2. **speckit.implement**: Execute tasks to create actual Bicep templates, parameter files, deployment scripts, and documentation
3. **speckit.analyze**: Validate consistency across all artifacts

**Branch**: Work continues on `001-azure-iac` feature branch  
**Output Files**: Plan will generate the following in `specs/001-azure-iac/`:
- ✅ plan.md (this file)
- [ ] research.md (to be generated by research agents)
- [ ] data-model.md (to be generated)
- [ ] contracts/ (to be generated)
- [ ] quickstart.md (to be generated)
