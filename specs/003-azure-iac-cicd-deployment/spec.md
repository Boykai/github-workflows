# Feature Specification: Azure IaC, CI/CD, and Managed Identity Deployment

**Feature Branch**: `003-azure-iac-cicd-deployment`  
**Created**: February 16, 2026  
**Status**: Draft  
**Input**: User description: "Implement Azure IaC (Bicep), CI/CD (GitHub Actions), and Managed Identity Deployment for GitHub Projects Chat"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Infrastructure as Code Deployment (Priority: P1)

An engineer deploys the complete Azure infrastructure for GitHub Projects Chat by running a single Bicep deployment command. The deployment provisions all required resources (Container Apps, Key Vault, Container Registry, Azure OpenAI, AI Foundry, Log Analytics, Managed Identity) in the correct dependency order with consistent naming, tagging, and security configuration. All resources are parameterized so the same template can be reused with different project names, environments, or regions.

**Why this priority**: Without infrastructure, nothing else can be deployed. The Bicep templates are the foundation for the entire cloud deployment. Every other story depends on having properly provisioned, correctly wired Azure resources.

**Independent Test**: Can be fully tested by running `az deployment group create` with the Bicep templates and verifying that all Azure resources are created with correct naming, configuration, role assignments, and inter-resource dependencies. Delivers value by providing a reproducible, version-controlled infrastructure deployment.

**Acceptance Scenarios**:

1. **Given** an engineer has an Azure subscription and required permissions, **When** they run `az deployment group create` with the Bicep template and production parameters, **Then** all Azure resources are provisioned with correct naming conventions (e.g., `cae-ghprojectschat-prod`, `kv-ghprojectschat-prod`) and linked dependencies
2. **Given** the Bicep deployment completes successfully, **When** the engineer inspects resource configuration, **Then** the managed identity has `AcrPull`, `Key Vault Secrets User`, and `Cognitive Services OpenAI User` roles assigned
3. **Given** the Bicep deployment completes successfully, **When** the engineer inspects Key Vault, **Then** it contains secrets for `GITHUB-TOKEN`, `AZURE-OPENAI-ENDPOINT`, and `AZURE-OPENAI-DEPLOYMENT` with RBAC authorization enabled
4. **Given** the Bicep deployment completes successfully, **When** the engineer inspects Azure OpenAI, **Then** a `gpt-41` model deployment exists with the `gpt-4.1` model and parameterized capacity
5. **Given** a parameter value is invalid (e.g., non-alphanumeric project name), **When** the deployment is attempted, **Then** the deployment fails early with a clear validation error message

---

### User Story 2 - Automated CI/CD Pipeline (Priority: P2)

When an engineer pushes code to the `main` branch, a GitHub Actions workflow automatically builds Docker images for both services, pushes them to Azure Container Registry, deploys the Bicep infrastructure, and updates the Container Apps with the new image tags. The pipeline uses OIDC for Azure authentication, eliminating the need for stored Azure credentials.

**Why this priority**: Automated deployment is essential for a production-ready workflow. It builds directly on the infrastructure from P1 and ensures every code change is deployed consistently without manual steps.

**Independent Test**: Can be tested by pushing a commit to `main` and verifying that the GitHub Actions workflow (1) builds and pushes Docker images to ACR, (2) deploys Bicep infrastructure, and (3) updates Container Apps with the new image. Delivers value by automating the entire deployment pipeline.

**Acceptance Scenarios**:

1. **Given** an engineer pushes code to `main`, **When** the GitHub Actions workflow triggers, **Then** it authenticates to Azure using OIDC without stored credentials
2. **Given** the build-and-push job runs, **When** it completes, **Then** both backend and frontend Docker images are tagged with the commit SHA and `latest`, and pushed to ACR
3. **Given** the deploy-infra job runs after build-and-push, **When** it completes, **Then** all Bicep resources are deployed or updated in the target resource group
4. **Given** the deploy-apps job runs after deploy-infra, **When** it completes, **Then** both Container Apps are updated to use the new image tag and health checks pass
5. **Given** any job in the pipeline fails, **When** the failure is detected, **Then** subsequent dependent jobs do not run and the failure is clearly reported in the workflow logs

---

### User Story 3 - Managed Identity Authentication for Backend (Priority: P3)

The backend service authenticates to Azure OpenAI using managed identity (DefaultAzureCredential) instead of API keys. When deployed to Azure Container Apps, the backend uses the user-assigned managed identity to securely access Azure OpenAI and Key Vault secrets without any stored API keys. Local development continues to work with API key-based authentication as a fallback.

**Why this priority**: Zero-trust security with managed identities is a core requirement. This story ensures the backend can operate securely in the Azure environment while maintaining backward compatibility for local development.

**Independent Test**: Can be tested by deploying the backend to Azure Container Apps and verifying that (1) it authenticates to Azure OpenAI using managed identity, (2) it reads secrets from Key Vault, and (3) it responds to chat requests successfully. Local testing with API keys confirms backward compatibility. Delivers value by eliminating API key storage in the production environment.

**Acceptance Scenarios**:

1. **Given** the backend is deployed to Azure Container Apps with a user-assigned managed identity, **When** it initializes the Azure OpenAI client, **Then** it uses `DefaultAzureCredential` with the `AZURE_CLIENT_ID` environment variable
2. **Given** the backend runs locally with `AZURE_OPENAI_KEY` set, **When** it initializes the Azure OpenAI client, **Then** it falls back to API key-based authentication for local development
3. **Given** the backend is deployed with managed identity, **When** a user sends a chat message, **Then** the backend successfully authenticates to Azure OpenAI and returns a response
4. **Given** the managed identity does not have the required role, **When** the backend attempts to access Azure OpenAI, **Then** a clear authentication error is logged

---

### User Story 4 - Frontend Proxying to Internal Backend (Priority: P4)

The frontend container is publicly accessible and proxies API requests to the backend Container App's internal FQDN. The Nginx configuration supports runtime substitution of the backend URL, allowing the same container image to be used across different environments without rebuilding.

**Why this priority**: The frontend must correctly route traffic to the backend in the Azure Container Apps environment. This is essential for end-to-end functionality but depends on both the infrastructure (P1) and the backend being deployed (P3).

**Independent Test**: Can be tested by deploying both Container Apps and verifying that (1) the frontend is publicly accessible on port 80, (2) API requests from the frontend reach the backend via the internal FQDN, and (3) the Nginx configuration correctly substitutes the `BACKEND_URL` at runtime. Delivers value by making the application accessible to users.

**Acceptance Scenarios**:

1. **Given** the frontend Container App is deployed with the `BACKEND_URL` environment variable set to the backend's internal FQDN, **When** a user accesses the frontend, **Then** API requests are proxied to the backend through the internal network
2. **Given** the frontend Nginx container starts, **When** the `BACKEND_URL` variable is set, **Then** `envsubst` replaces the backend host in the Nginx configuration at runtime
3. **Given** the frontend is accessed by a user, **When** they interact with the chat interface, **Then** messages are sent through the frontend proxy to the backend and responses are displayed correctly
4. **Given** the backend is unreachable, **When** a user sends an API request, **Then** the frontend returns an appropriate error response

---

### User Story 5 - Documentation and Onboarding (Priority: P5)

A new engineer joining the team can understand the Azure architecture, set up the required Azure AD app registration and GitHub secrets, deploy the infrastructure, and troubleshoot issues by following the comprehensive documentation in the README and infra/README.md files.

**Why this priority**: Documentation ensures the deployment process is maintainable and reproducible by team members beyond the original implementer. It's lower priority because it doesn't affect functionality, but it's essential for long-term maintainability.

**Independent Test**: Can be tested by having a new engineer follow the README documentation to (1) set up Azure AD app registration and federated credentials, (2) configure GitHub secrets, (3) deploy infrastructure using Bicep, and (4) trigger the CI/CD pipeline. Delivers value by enabling self-service onboarding and reducing dependency on tribal knowledge.

**Acceptance Scenarios**:

1. **Given** a new engineer reads the README, **When** they follow the prerequisites section, **Then** they can identify all required Azure and GitHub setup steps without additional guidance
2. **Given** a new engineer follows the initial setup instructions, **When** they complete the Azure AD app registration and GitHub secrets configuration, **Then** they can trigger a successful CI/CD deployment
3. **Given** a deployment fails, **When** the engineer consults the documentation, **Then** they find troubleshooting guidance and environment variable references to diagnose the issue
4. **Given** the team needs to tear down infrastructure, **When** they follow the infra/README.md teardown instructions, **Then** all Azure resources are cleanly removed

---

### Edge Cases

- What happens when the OIDC token exchange fails during the GitHub Actions workflow? The pipeline job fails with a clear error message indicating the Azure login failure, and subsequent jobs do not run.
- What happens when Key Vault secrets are missing or empty at Container App startup? The backend logs the missing configuration and returns unhealthy status on the `/health` endpoint, preventing traffic routing.
- What happens when the Azure OpenAI model deployment is not yet available? The Bicep deployment completes but the backend health check may fail until the model is fully provisioned; the Container App readiness probe handles this gracefully.
- What happens when ACR image pull fails due to missing identity role? The Container App revision fails to activate, and the error is visible in Container Apps logs and the GitHub Actions deployment verification step.
- What happens when the backend Container App is unhealthy? The Container Apps platform stops routing traffic to unhealthy replicas and attempts to restart them per the scaling configuration.
- What happens when a deployment is re-run with the same parameters? Bicep deployments are idempotent — existing resources are updated in place, and no duplicate resources are created.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a modular Bicep infrastructure under `infra/` with an orchestrator (`main.bicep`), parameter file (`main.bicepparam`), and separate module files for each Azure resource type
- **FR-002**: System MUST parameterize all Azure resources with `projectName`, `environment`, and `location` parameters, applying Azure Cloud Adoption Framework naming conventions (e.g., `ca-{projectName}-backend-{env}`, `kv-{projectName}-{env}`)
- **FR-003**: System MUST provision a Log Analytics Workspace with SKU `PerGB2018` and 30-day retention, linked to the Container Apps Environment for centralized logging
- **FR-004**: System MUST provision an Azure Container Registry with Basic SKU, admin user disabled, and `AcrPull` role granted to the user-assigned managed identity
- **FR-005**: System MUST provision an Azure Key Vault with RBAC authorization, soft delete, and purge protection enabled, storing secrets `GITHUB-TOKEN`, `AZURE-OPENAI-ENDPOINT`, and `AZURE-OPENAI-DEPLOYMENT`
- **FR-006**: System MUST grant `Key Vault Secrets User` role to the user-assigned managed identity on the Key Vault
- **FR-007**: System MUST provision an Azure OpenAI resource (Kind: OpenAI, SKU: S0) with a `gpt-41` model deployment using the `gpt-4.1` model, parameterized capacity (default 10K TPM), and output endpoint and deployment name for Key Vault storage
- **FR-008**: System MUST grant `Cognitive Services OpenAI User` role to the user-assigned managed identity on the Azure OpenAI resource
- **FR-009**: System MUST provision an AI Foundry Hub associated with Key Vault and Log Analytics, and an AI Foundry Project linked to the Azure OpenAI resource
- **FR-010**: System MUST provision a Container Apps Environment linked to Log Analytics with zone redundancy disabled
- **FR-011**: System MUST provision a User-Assigned Managed Identity with `AcrPull`, `Key Vault Secrets User`, and `Cognitive Services OpenAI User` role assignments
- **FR-012**: System MUST configure the backend Container App with internal-only ingress on port 8000, image from ACR, user-assigned managed identity, min 1/max 3 replicas, CPU 0.5/memory 1Gi, environment variables sourced from Key Vault secrets, and an HTTP health probe on `/health`
- **FR-013**: System MUST configure the frontend Container App with external ingress on port 80, image from ACR, user-assigned managed identity, min 1/max 3 replicas, CPU 0.5/memory 1Gi, `BACKEND_URL` set to the backend's internal FQDN, and an HTTP health probe on `/`
- **FR-014**: System MUST wire all Bicep modules in `main.bicep` with correct dependency ordering: Log Analytics → Container Apps Environment, Managed Identity → Role Assignments, Key Vault → Secrets, ACR → Container Apps, OpenAI → AI Foundry Hub → AI Foundry Project
- **FR-015**: System MUST update the backend to authenticate with Azure OpenAI using `DefaultAzureCredential` (managed identity) when `AZURE_OPENAI_KEY` is not set, using `AZURE_CLIENT_ID` for user-assigned managed identity
- **FR-016**: System MUST maintain backward compatibility with API key-based authentication for local development when `AZURE_OPENAI_KEY` is set
- **FR-017**: System MUST add `azure-identity` as a backend dependency for managed identity authentication
- **FR-018**: System MUST provide a `/health` endpoint in the FastAPI backend returning `200 OK` with `{"status": "healthy"}`
- **FR-019**: System MUST update the frontend Nginx configuration to use a `BACKEND_URL` (or equivalent) environment variable for the API proxy pass target, substituted at container runtime via `envsubst`
- **FR-020**: System MUST create a `.github/workflows/deploy.yml` workflow triggered on push to `main` with three jobs: build-and-push (Docker images to ACR), deploy-infra (Bicep deployment), and deploy-apps (Container App image update), using OIDC for Azure authentication
- **FR-021**: System MUST tag Docker images with both the commit SHA and `latest` when pushing to ACR
- **FR-022**: System MUST document in the README the manual setup steps for Azure AD app registration, federated credentials, GitHub secrets (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `GITHUB_TOKEN_VALUE`), and required role assignments
- **FR-023**: System MUST update the README with an architecture diagram (Mermaid), prerequisites, initial setup instructions, infrastructure deployment guide, CI/CD pipeline explanation, local development instructions, and environment variable reference table
- **FR-024**: System MUST create `infra/README.md` documenting Bicep parameters, module dependency graph, and infrastructure teardown instructions
- **FR-025**: System MUST ensure all Azure resources are tagged with `project`, `environment`, and `owner` tags for cost tracking
- **FR-026**: System MUST ensure secrets and credentials are never exposed in GitHub Actions workflow logs or outputs
- **FR-027**: System MUST ensure the CI/CD workflow uses explicit job dependencies so deploy-infra depends on build-and-push, and deploy-apps depends on deploy-infra

### Key Entities

- **Managed Identity**: A User-Assigned Managed Identity shared by both Container Apps, granting secure access to ACR, Key Vault, and Azure OpenAI without storing credentials
- **Container App**: An Azure Container Apps resource running either the backend (internal, port 8000) or frontend (external, port 80) service, pulling images from ACR via managed identity
- **Key Vault Secret**: A sensitive configuration value stored in Azure Key Vault (e.g., GitHub token, OpenAI endpoint), accessed by Container Apps via managed identity and RBAC
- **Bicep Module**: A reusable infrastructure template defining a single Azure resource type, parameterized and composed by the orchestrator (`main.bicep`)
- **CI/CD Pipeline**: A GitHub Actions workflow with three sequential jobs that build, deploy infrastructure, and update Container Apps on each push to `main`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All Azure resources are deployable via a single `az deployment group create` command with no manual portal steps (except initial AD app registration)
- **SC-002**: The CI/CD pipeline completes all three jobs (build-and-push, deploy-infra, deploy-apps) successfully on push to `main` within 15 minutes
- **SC-003**: The backend authenticates to Azure OpenAI using managed identity with zero API keys stored in the production environment
- **SC-004**: The frontend is publicly accessible and successfully proxies API requests to the backend via the internal FQDN
- **SC-005**: Both Container Apps pull images from ACR using managed identity without admin credentials
- **SC-006**: Health check endpoints respond with 200 OK on both frontend (`/`) and backend (`/health`) within 30 seconds of deployment
- **SC-007**: A new engineer can complete the initial setup (AD registration, GitHub secrets, first deployment) by following the README documentation within 1 hour
- **SC-008**: Bicep deployments are idempotent — redeploying with the same parameters produces no errors or duplicate resources
- **SC-009**: The AI Foundry Hub, Project, and `gpt-41` model deployment are provisioned and linked correctly
- **SC-010**: No secrets or credentials appear in GitHub Actions workflow logs or outputs

## Assumptions

1. **Azure Subscription**: The team has access to an Azure subscription with sufficient permissions to create resources (Contributor + User Access Administrator roles)
2. **GitHub Copilot / Actions**: The repository has GitHub Actions enabled and the team has permissions to configure repository secrets and workflow permissions
3. **Production-Only Scope**: Only a single production environment is required; no dev, staging, or multi-environment support is needed at this time
4. **Existing Docker Support**: The backend and frontend already have working Dockerfiles and docker-compose.yml for local development, which will be preserved
5. **Backend Health Endpoint**: The backend already has a `/health` endpoint at `/api/v1/health`; the Container App health probe will target this existing endpoint
6. **Frontend Nginx Proxy**: The frontend Nginx configuration already proxies `/api/` to `backend:8000`; the update adds `envsubst`-based runtime configuration for the backend host
7. **Azure OpenAI Model Availability**: The `gpt-4.1` model is available in the specified Azure region for deployment
8. **OIDC Support**: GitHub Actions OIDC integration with Azure AD is supported and the team can create the required federated credential
9. **Backward Compatibility**: Local development with API keys via docker-compose continues to work unchanged; managed identity is only used when deployed to Azure
10. **No Custom GitHub Agents**: The `/api/agent` routes and related tooling are out of scope and remain unchanged

## Dependencies

- Azure subscription with Contributor and User Access Administrator role assignments
- Azure AD tenant for app registration and federated credential configuration
- GitHub Actions enabled on the repository with id-token write permissions
- Azure CLI for manual Bicep deployment and initial setup
- Docker for building container images locally and in CI
- Existing backend and frontend Dockerfiles (maintained as-is)

## Scope Boundaries

### In Scope

- Creating modular Bicep IaC templates for all specified Azure resources
- Creating a CI/CD GitHub Actions workflow for automated deployment
- Updating backend authentication to support managed identity (while maintaining API key fallback)
- Updating frontend Nginx configuration for runtime backend URL substitution
- Comprehensive documentation (README updates, infra/README.md)
- Resource tagging for cost tracking and ownership
- Health check configuration for Container Apps

### Out of Scope

- Custom GitHub Agents (the `/api/agent` routes and related tooling)
- Multi-environment deployments (dev, staging) — production only
- Frontend application logic changes (no React component modifications)
- Microsoft Agent Framework integration (deferred to a separate feature)
- Azure AD app registration automation (documented as manual steps)
- Custom domain and TLS certificate configuration
- Monitoring dashboards and alerting rules beyond basic logging
- Database provisioning (the application does not currently use a database)
- Network security groups or virtual network integration
