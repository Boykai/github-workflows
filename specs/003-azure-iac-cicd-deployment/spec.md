# Feature Specification: Azure IaC, CI/CD Pipeline, and Secure Cloud Deployment

**Feature Branch**: `003-azure-iac-cicd-deployment`  
**Created**: 2026-02-16  
**Status**: Draft  
**Input**: User description: "Implement Azure IaC (Bicep), Managed Identity, CI/CD Pipeline, and Secure Cloud Deployment for Projects Chat"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Infrastructure as Code Provisioning (Priority: P1)

As a DevOps engineer, I want to provision all required Azure resources for the Projects Chat application using a single Infrastructure as Code deployment, so that the entire cloud environment is reproducible, auditable, and requires no manual portal steps (except initial identity setup).

**Why this priority**: Without cloud infrastructure, neither the backend nor frontend can be deployed to Azure. This is the foundational capability that enables all subsequent deployment and operations stories.

**Independent Test**: Can be fully tested by running the IaC deployment command against an Azure subscription and verifying that all resources (container registry, container apps environment, key vault, AI services, managed identity, log analytics) are created with correct naming, configuration, and role assignments. Delivers immediate value by establishing the entire production environment.

**Acceptance Scenarios**:

1. **Given** an Azure subscription and resource group, **When** the IaC template is deployed with project name, environment, and location parameters, **Then** all specified resources are created with names following the Azure Cloud Adoption Framework conventions
2. **Given** the IaC template is deployed, **When** resource creation completes, **Then** a user-assigned managed identity exists with AcrPull, Key Vault Secrets User, and Cognitive Services OpenAI User role assignments
3. **Given** the IaC template is deployed, **When** resource creation completes, **Then** the key vault contains secrets for GitHub token, Azure OpenAI endpoint, and Azure OpenAI deployment name (no API keys stored)
4. **Given** the IaC template is deployed, **When** resource creation completes, **Then** an Azure OpenAI resource exists with a gpt-4.1 model deployment (deployment name: gpt-41) at the specified capacity
5. **Given** the IaC template is deployed, **When** resource creation completes, **Then** AI Foundry hub and project resources are provisioned and linked to the OpenAI resource and key vault
6. **Given** the IaC template has been deployed previously, **When** the same template is re-deployed with no parameter changes, **Then** the deployment succeeds idempotently with no resource recreation or data loss

---

### User Story 2 - Automated CI/CD Pipeline (Priority: P1)

As a DevOps engineer, I want an automated CI/CD pipeline that builds container images, deploys infrastructure, and updates the running application whenever code is pushed to the main branch, so that deployments are consistent, repeatable, and require no manual intervention.

**Why this priority**: Equally critical as IaC — without automated deployment, every release requires manual steps that are error-prone and time-consuming. This story enables continuous delivery.

**Independent Test**: Can be fully tested by pushing a code change to the main branch and observing the pipeline: images are built and pushed to the container registry, infrastructure is deployed/updated, and container apps are updated with the new image. The frontend is accessible and proxies to the backend correctly.

**Acceptance Scenarios**:

1. **Given** code is pushed to the main branch, **When** the CI/CD pipeline triggers, **Then** backend and frontend container images are built, tagged with the commit SHA and "latest", and pushed to the Azure container registry
2. **Given** images are pushed successfully, **When** the infrastructure deployment job runs, **Then** the IaC template is deployed (creating or updating resources as needed) and the resource group is created if it does not exist
3. **Given** infrastructure is deployed, **When** the application deployment job runs, **Then** both container apps are updated to use the new image tag and health checks confirm successful deployment
4. **Given** a pipeline job fails (image build, IaC deployment, or app update), **When** the failure occurs, **Then** subsequent jobs are skipped and actionable error logs are available in the workflow run output
5. **Given** the pipeline uses Azure authentication, **When** credentials are used, **Then** authentication is performed via OpenID Connect (OIDC) federated credentials — no long-lived secrets are used for Azure login

---

### User Story 3 - Secure Managed Identity Authentication (Priority: P1)

As a DevOps engineer, I want the backend service to authenticate to Azure OpenAI and Key Vault using managed identity instead of API keys, so that no secrets are stored in code, environment variables, or CI/CD configuration, achieving a zero-trust security posture.

**Why this priority**: Security is non-negotiable for production. Managed identity eliminates the risk of leaked API keys and is a prerequisite for the container apps to access Azure OpenAI and Key Vault.

**Independent Test**: Can be fully tested by deploying the backend container app and verifying it successfully calls Azure OpenAI using managed identity credentials (no API key environment variable set), retrieves secrets from Key Vault, and returns chat responses.

**Acceptance Scenarios**:

1. **Given** the backend is deployed with a user-assigned managed identity, **When** a chat request is made, **Then** the backend authenticates to Azure OpenAI using the managed identity credential (not an API key)
2. **Given** the backend has the AZURE_CLIENT_ID environment variable set, **When** the application starts, **Then** it uses the user-assigned managed identity associated with that client ID for all Azure service authentication
3. **Given** no AZURE_OPENAI_KEY environment variable is set in production, **When** the backend initializes the AI client, **Then** it falls back to managed identity authentication automatically
4. **Given** the backend container app has Key Vault Secrets User role, **When** environment variables reference Key Vault secrets, **Then** the secrets are resolved and available to the application at runtime

---

### User Story 4 - Backend Health Monitoring (Priority: P2)

As a DevOps engineer, I want the backend to expose a health check endpoint that the container platform can probe, so that unhealthy instances are automatically detected and replaced.

**Why this priority**: Health checks are required for reliable container orchestration but the application can technically run without them — the platform just won't auto-heal.

**Independent Test**: Can be fully tested by sending an HTTP GET request to the backend health endpoint and verifying it returns a 200 OK response with a healthy status indicator.

**Acceptance Scenarios**:

1. **Given** the backend is running, **When** an HTTP GET request is sent to the health endpoint, **Then** a 200 OK response is returned with a status indicator
2. **Given** the container platform is configured with health probes, **When** the health endpoint is unreachable or returns an error, **Then** the platform marks the instance as unhealthy and restarts it

---

### User Story 5 - Frontend Proxy Configuration for Cloud Deployment (Priority: P2)

As a DevOps engineer, I want the frontend container to dynamically configure its backend proxy target at runtime using an environment variable, so that the same container image works across different deployment environments without rebuilding.

**Why this priority**: The frontend must know where to route API requests in the cloud environment. Without this, the frontend cannot communicate with the backend container app.

**Independent Test**: Can be fully tested by starting the frontend container with a BACKEND_URL environment variable pointing to a backend service, making an API request through the frontend, and verifying it is proxied to the correct backend address.

**Acceptance Scenarios**:

1. **Given** the frontend container is started with a BACKEND_URL environment variable, **When** the container starts, **Then** the web server configuration is updated to proxy API requests to the specified backend URL
2. **Given** the frontend is deployed as a container app with external ingress, **When** a user accesses the application URL, **Then** the frontend serves the web application and API requests are transparently proxied to the backend's internal address
3. **Given** no BACKEND_URL is provided, **When** the container starts, **Then** a sensible default is used (e.g., the docker-compose default of backend:8000) to maintain backward compatibility with local development

---

### User Story 6 - Comprehensive Deployment Documentation (Priority: P2)

As a DevOps engineer or new team member, I want clear documentation covering architecture, prerequisites, setup steps, deployment instructions, and environment variable references, so that I can understand, operate, and troubleshoot the cloud deployment without tribal knowledge.

**Why this priority**: Documentation is essential for maintainability and onboarding but does not block the technical deployment itself.

**Independent Test**: Can be fully tested by having a new team member follow the documentation to set up Azure AD app registration, configure GitHub secrets, and deploy the application — completing all steps without asking for clarification.

**Acceptance Scenarios**:

1. **Given** a new team member reads the README, **When** they follow the prerequisites and initial setup sections, **Then** they can configure Azure AD app registration, federated credentials, and GitHub repository secrets without additional guidance
2. **Given** the infrastructure README exists, **When** a DevOps engineer needs to tear down the environment, **Then** clear teardown instructions are provided with the correct commands and order of operations
3. **Given** the README includes an architecture diagram, **When** a team member views it, **Then** they can understand the Azure resource topology, data flow, and security boundaries at a glance

---

### Edge Cases

- What happens when the IaC deployment is run against a subscription that already has resources with the same names from a previous deployment? The deployment must be idempotent and update existing resources without data loss.
- What happens when the Azure OpenAI model quota is exceeded? The IaC deployment should fail gracefully with a clear error message indicating insufficient capacity.
- What happens when the managed identity role assignments take time to propagate? The container apps should retry authentication with appropriate backoff, and the CI/CD pipeline should include a wait/verification step after role assignment.
- What happens when the container registry is empty (first deployment) and container apps reference images that don't yet exist? The CI/CD pipeline must ensure images are pushed before container apps are created or updated.
- What happens when the GitHub PAT stored in Key Vault expires? The application should return clear error messages, and documentation should describe how to rotate the secret.
- What happens when the OIDC federated credential is misconfigured? The pipeline should fail fast with a clear authentication error rather than proceeding with partial deployments.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a modular IaC directory structure under `infra/` with an orchestrator template and individual module templates for each Azure resource (log analytics, container registry, key vault, AI foundry hub, AI foundry project, OpenAI, container apps environment, managed identity, backend container app, frontend container app)
- **FR-002**: System MUST parameterize all resource names using project name, environment, and location inputs, constructing names per Azure Cloud Adoption Framework conventions (e.g., `rg-{projectName}-{env}`, `cr{projectName}{env}`, `kv-{projectName}-{env}`)
- **FR-003**: System MUST provision a Log Analytics Workspace with PerGB2018 SKU and 30-day retention, used by the Container Apps Environment for centralized logging
- **FR-004**: System MUST provision an Azure Container Registry with Basic SKU, admin user disabled, and AcrPull role granted to the shared managed identity
- **FR-005**: System MUST provision an Azure Key Vault with standard SKU, RBAC authorization enabled, soft delete and purge protection enabled, storing secrets for GitHub token, Azure OpenAI endpoint, and Azure OpenAI deployment name — with Key Vault Secrets User role granted to the shared managed identity
- **FR-006**: System MUST provision an Azure OpenAI resource with S0 SKU, deploying a gpt-4.1 model (deployment name: gpt-41, latest version, parameterized capacity defaulting to 10K TPM), and grant Cognitive Services OpenAI User role to the shared managed identity
- **FR-007**: System MUST provision an AI Foundry Hub associated with the Key Vault and Log Analytics workspace, and an AI Foundry Project linked to the Azure OpenAI resource
- **FR-008**: System MUST provision a Container Apps Environment linked to the Log Analytics workspace with zone redundancy disabled
- **FR-009**: System MUST provision a User-Assigned Managed Identity shared by both container apps, with role assignments for AcrPull, Key Vault Secrets User, and Cognitive Services OpenAI User
- **FR-010**: System MUST provision a backend Container App with internal-only ingress on port 8000, the managed identity attached, environment variables sourced from Key Vault secrets (GITHUB_TOKEN, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT), AZURE_CLIENT_ID set to the managed identity client ID, and a health probe on /health
- **FR-011**: System MUST provision a frontend Container App with external ingress on port 80, the managed identity attached, BACKEND_URL set to the backend's internal FQDN, and a health probe on /
- **FR-012**: System MUST enforce correct dependency ordering in the IaC orchestrator: Log Analytics before Container Apps Environment, Managed Identity before role assignments, Key Vault before secrets, ACR before Container Apps, OpenAI before AI Foundry resources
- **FR-013**: System MUST update the backend to authenticate with Azure OpenAI using managed identity credentials when no API key is provided, using AZURE_CLIENT_ID for user-assigned managed identity selection
- **FR-014**: System MUST ensure the backend health endpoint returns a 200 OK response with a health status indicator, suitable for container platform health probes
- **FR-015**: System MUST update the frontend web server configuration to dynamically substitute the BACKEND_URL environment variable into the proxy pass target at container runtime, maintaining backward compatibility with the existing local development setup
- **FR-016**: System MUST create a CI/CD pipeline triggered on push to main with three sequential jobs: (1) build and push container images to ACR, (2) deploy IaC template, (3) update container apps with new image tags and verify health
- **FR-017**: System MUST use OIDC federated credentials for Azure authentication in the CI/CD pipeline — no long-lived Azure secrets stored in GitHub
- **FR-018**: System MUST tag container images with both the Git commit SHA and "latest" during the build-and-push pipeline job
- **FR-019**: System MUST abort subsequent pipeline jobs if any prior job fails, and surface actionable error logs in the workflow output
- **FR-020**: System MUST document prerequisites, Azure AD app registration setup, GitHub secret configuration, infrastructure deployment commands, CI/CD pipeline operation, local development instructions, and environment variable references in README files
- **FR-021**: System MUST ensure no application secrets (API keys, tokens) are stored in GitHub repository secrets — only OIDC configuration (client ID, tenant ID, subscription ID) and the GitHub PAT for initial Key Vault seeding are permitted
- **FR-022**: System MUST ensure all IaC deployments are idempotent — re-running the same deployment with unchanged parameters produces no errors or unintended changes

### Key Entities

- **Managed Identity**: A user-assigned Azure identity shared by both container apps, granting access to the container registry, key vault, and Azure OpenAI without API keys. Key attributes: client ID, principal ID, resource ID
- **Key Vault**: A centralized secret store holding application secrets (GitHub token, OpenAI endpoint, OpenAI deployment name). Accessed by container apps via managed identity with RBAC authorization
- **Container App**: A containerized service (backend or frontend) running in the Container Apps Environment. Key attributes: image source (ACR), ingress configuration (internal/external), environment variables, managed identity assignment, health probe configuration
- **Container Registry**: The private registry storing built container images for both services. Key attributes: login server URL, managed identity access via AcrPull role
- **OpenAI Deployment**: An Azure OpenAI model deployment (gpt-4.1) used by the backend for chat functionality. Key attributes: endpoint URL, deployment name, model version, capacity (TPM)
- **AI Foundry Hub/Project**: Azure AI management resources linking the OpenAI service with the key vault and logging. Used for model governance and project organization

## Assumptions

- The Azure subscription has sufficient quota for all requested resources (Container Apps, OpenAI S0 SKU, gpt-4.1 model capacity)
- The Azure AD app registration and federated credential for OIDC are configured manually as a one-time setup step before the CI/CD pipeline can run
- The GitHub PAT for the application's GitHub API access is manually stored in Key Vault as a one-time setup step or seeded via the CI/CD pipeline's initial run
- The backend currently supports dual authentication (API key and managed identity) — the change extends existing behavior rather than breaking the API key path used in local development
- A single production environment is sufficient; multi-environment (dev, staging) deployment is out of scope
- Custom GitHub Agent routes (`/api/agent`) and frontend application logic changes are out of scope
- Standard web application performance expectations apply (page load under 3 seconds, API responses under 2 seconds) unless otherwise specified
- Error handling follows the existing application patterns — user-friendly messages with appropriate fallbacks

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All Azure resources are provisioned successfully via a single IaC deployment command with no manual portal steps required (except initial AD app registration)
- **SC-002**: The CI/CD pipeline completes all three jobs (build, infrastructure deployment, application deployment) in under 15 minutes for a typical code push
- **SC-003**: The frontend application is publicly accessible via its container app URL and successfully proxies API requests to the backend within 2 seconds
- **SC-004**: The backend authenticates to Azure OpenAI using managed identity and processes chat requests without any API key environment variables configured
- **SC-005**: Both container apps pull images from the container registry using managed identity — no registry admin credentials are used
- **SC-006**: A new team member can follow the documentation to configure prerequisites and deploy the full stack within 1 hour
- **SC-007**: Re-deploying the IaC template with unchanged parameters completes successfully with no resource recreation or data loss (idempotency)
- **SC-008**: Health check endpoints respond correctly, enabling the container platform to detect and replace unhealthy instances within 60 seconds
- **SC-009**: No application secrets (API keys, tokens) are present in the GitHub repository, CI/CD logs, or container environment variables in plaintext — all secrets are sourced from Key Vault via managed identity
- **SC-010**: The gpt-4.1 model deployment is accessible through the AI Foundry project and responds to inference requests from the backend
