# Feature Specification: Azure IaC, CI/CD, and Secure Deployment

**Feature Branch**: `003-azure-iac-cicd-deployment`  
**Created**: 2026-02-16  
**Status**: Draft  
**Input**: User description: "Implement Azure IaC, CI/CD, and Secure Deployment for GitHub Projects Chat (Bicep, GitHub Actions, Managed Identity)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deploy Infrastructure via Bicep IaC (Priority: P1)

As the application owner, I want all Azure resources (Container Registry, Key Vault, AI Foundry, OpenAI, Log Analytics, Container Apps Environment, Managed Identity, and Container Apps) defined in modular Bicep files so that I can provision the entire production environment with a single deployment command, with no manual portal steps except initial Azure AD app registration.

**Why this priority**: Infrastructure is the foundation; no deployment, CI/CD, or security posture is possible without the Azure resources being defined and provisionable first.

**Independent Test**: Can be fully tested by running the Bicep deployment against an Azure subscription and verifying all resources are created with correct names, SKUs, and configurations.

**Acceptance Scenarios**:

1. **Given** the infra/ directory contains the orchestrator file, parameter file, and all module files, **When** the deployment is executed with valid parameters, **Then** all Azure resources are provisioned with correct naming conventions (e.g., `rg-ghprojectschat-prod`, `crghprojectschatprod`, `kv-ghprojectschat-prod`) and correct SKU/configuration per resource type.
2. **Given** a previously deployed environment, **When** the same deployment is re-run with no parameter changes, **Then** the deployment completes idempotently with no errors and no duplicate resources or role assignments.
3. **Given** the deployment templates, **When** an invalid parameter (e.g., empty project name) is provided, **Then** the deployment fails with a clear validation error before any resources are created.

---

### User Story 2 - Automated CI/CD Pipeline (Priority: P1)

As the application owner, I want a CI/CD workflow that automatically builds container images, deploys infrastructure, and updates container apps on every push to main, so that I achieve continuous, hands-off deployment with secure federated authentication (no stored cloud credentials).

**Why this priority**: Automated deployment is essential for production readiness and eliminates manual deployment steps, reducing human error and deployment time.

**Independent Test**: Can be fully tested by pushing a commit to the main branch and observing the workflow complete all three jobs (build-and-push, deploy-infra, deploy-apps) successfully.

**Acceptance Scenarios**:

1. **Given** the CI/CD workflow file is configured, **When** a push to the `main` branch occurs, **Then** the workflow triggers and executes three jobs in order: build-and-push (container images to registry), deploy-infra (infrastructure deployment), deploy-apps (container app image update and health verification).
2. **Given** correct repository secrets for Azure identity, **When** the workflow runs, **Then** Azure login succeeds using federated credentials with no stored Azure passwords or service principal secrets.
3. **Given** a workflow run where the infrastructure deployment job fails, **When** the failure is inspected, **Then** clear error messages are visible in the CI/CD logs indicating the specific deployment failure.

---

### User Story 3 - Secure Managed Identity Authentication (Priority: P1)

As the application owner, I want the backend to authenticate with Azure OpenAI using managed identity instead of API keys, and all secrets to be stored in a vault accessible only via managed identity, so that no API keys or secrets are stored in code, environment variables, or CI/CD configuration.

**Why this priority**: Zero-trust security posture is a core requirement; managed identity eliminates secret sprawl and key rotation burden.

**Independent Test**: Can be fully tested by deploying the backend container app and verifying it successfully calls the Azure OpenAI endpoint using managed identity, with no API key environment variable present.

**Acceptance Scenarios**:

1. **Given** the backend container app is deployed with a user-assigned managed identity, **When** the backend initializes the Azure OpenAI client, **Then** it uses credential-based authentication with the managed identity client ID and does not require an API key.
2. **Given** the managed identity has the appropriate secret reader role on the vault, **When** the backend container app starts, **Then** it successfully reads the GitHub token, OpenAI endpoint, and deployment name from vault secret references.
3. **Given** the managed identity has the appropriate AI service user role on the OpenAI resource, **When** the backend sends a chat completion request, **Then** the request succeeds with managed identity authentication.

---

### User Story 4 - Frontend Proxying to Backend via Internal Network (Priority: P2)

As an end user, I want the frontend container app to be publicly accessible and correctly proxy API requests to the backend container app over the internal network, so that I can use the application seamlessly in production.

**Why this priority**: User-facing functionality depends on the frontend being able to reach the backend; this is critical for the application to function but depends on infrastructure being deployed first.

**Independent Test**: Can be fully tested by accessing the frontend's public URL in a browser and verifying that API calls (e.g., chat requests) are successfully proxied to the backend and return expected responses.

**Acceptance Scenarios**:

1. **Given** the frontend container app is deployed with external ingress on port 80, **When** a user navigates to the frontend's public URL, **Then** the frontend loads and is accessible.
2. **Given** the frontend web server config uses the backend URL environment variable, **When** the frontend container app starts, **Then** the backend URL placeholder is replaced with the backend container app's internal fully qualified domain name at runtime.
3. **Given** the frontend is proxying to the backend, **When** a user sends a chat message, **Then** the request is routed through the web server to the backend's internal address and returns a successful response.

---

### User Story 5 - Comprehensive Documentation (Priority: P2)

As a developer or operations team member, I want complete documentation covering architecture, setup prerequisites, deployment instructions, CI/CD flow, and tear-down procedures, so that I can understand, operate, and maintain the Azure deployment independently.

**Why this priority**: Documentation enables operational independence and reduces bus-factor risk; it is essential for maintainability but does not block deployment.

**Independent Test**: Can be fully tested by having a new team member follow the documentation instructions to set up the Azure identity, configure repository secrets, and deploy infrastructure successfully.

**Acceptance Scenarios**:

1. **Given** the root README is updated, **When** a new developer reads it, **Then** they find an architecture diagram, prerequisites list, initial setup steps (identity registration, federated credentials, repository secrets), infrastructure deployment instructions, CI/CD pipeline explanation, local development instructions, and an environment variables reference table.
2. **Given** the infrastructure README is created, **When** a developer reads it, **Then** they find all deployment parameters documented, a module dependency graph, and infrastructure tear-down instructions.

---

### User Story 6 - Backend Agent Framework Integration (Priority: P3)

As the application owner, I want the backend chat endpoint to leverage the Microsoft Agent Framework while maintaining backward compatibility with the existing API contract, so that I can take advantage of agent framework capabilities without breaking existing functionality.

**Why this priority**: Agent framework integration enhances capabilities but is not required for initial deployment; existing chat functionality continues to work without it.

**Independent Test**: Can be fully tested by sending a chat request to the backend's chat endpoint and verifying the response matches the existing API contract (same request/response format).

**Acceptance Scenarios**:

1. **Given** the backend is updated with the agent framework SDK, **When** a chat request is sent to the existing chat endpoint, **Then** the response format and behavior are backward-compatible with the current API contract.
2. **Given** the agent framework integration, **When** the backend processes a chat request, **Then** it utilizes agent framework capabilities for enhanced responses while maintaining the same response structure.

---

### Edge Cases

- What happens when the Azure OpenAI model deployment (gpt-4.1) is not available in the specified region? The deployment should fail with a clear error message indicating model availability constraints.
- How does the system handle secret retrieval failures at container app startup? The backend should fail to start with clear error logs rather than running with missing configuration.
- What happens when the container image pull fails due to incorrect managed identity permissions? The container app should report a clear deployment error, and the workflow should detect the failure in the health check step.
- How does the system handle container app scaling (1-3 replicas) when the backend is under load? Each replica should independently authenticate via managed identity without session affinity requirements.
- What happens when the CI/CD federated token exchange fails due to misconfigured credentials? The workflow should fail at the Azure login step with a clear error indicating the credential configuration issue.
- How does the system handle re-deployment when a previous infrastructure deployment partially failed? The deployment should be resumable and idempotent, completing successfully on retry without creating duplicate resources.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create an `infra/` directory with modular Bicep files: an orchestrator file, a production parameter file, and separate modules for container registry, container apps environment, backend container app, frontend container app, key vault, AI Foundry hub, AI Foundry project, OpenAI resource, log analytics workspace, and managed identity.
- **FR-002**: System MUST parameterize all Azure resources with project name, environment, and location parameters, enforcing Cloud Adoption Framework naming conventions for each resource type (e.g., `rg-{project}-{env}`, `cr{project}{env}`, `kv-{project}-{env}`).
- **FR-003**: System MUST provision a Log Analytics Workspace with PerGB2018 SKU and 30-day retention, used by the Container Apps Environment for centralized logging.
- **FR-004**: System MUST provision a Container Registry with Basic SKU, admin user disabled, with container image pull role granted to the shared managed identity.
- **FR-005**: System MUST provision a Key Vault with standard SKU, role-based access control enabled (not access policies), soft delete and purge protection enabled, with secret reader role granted to the shared managed identity, storing secrets for the GitHub token, OpenAI endpoint, and OpenAI deployment name.
- **FR-006**: System MUST provision an AI Foundry Hub associated with Key Vault and Log Analytics, and an AI Foundry Project linked to the Azure OpenAI resource.
- **FR-007**: System MUST provision an Azure OpenAI resource with an S0 SKU and a gpt-4.1 model deployment with parameterized capacity (default 10K TPM), granting the AI service user role to the shared managed identity, and outputting the endpoint and deployment name for vault secret storage.
- **FR-008**: System MUST provision a Container Apps Environment linked to the Log Analytics workspace with zone redundancy disabled.
- **FR-009**: System MUST create a User-Assigned Managed Identity shared by both container apps, with role assignments for container image pull (on registry), secret reading (on vault), and AI service access (on OpenAI resource).
- **FR-010**: System MUST deploy the backend container app from the registry with user-assigned managed identity, internal-only ingress on port 8000, min/max replicas 1/3, CPU 0.5 / Memory 1Gi, environment variables sourced from vault secrets (GitHub token, OpenAI endpoint, OpenAI deployment) plus managed identity client ID, and HTTP GET health probe on `/health`.
- **FR-011**: System MUST deploy the frontend container app from the registry with user-assigned managed identity, external ingress on port 80, min/max replicas 1/3, CPU 0.5 / Memory 1Gi, backend URL environment variable set to the backend container app's internal fully qualified domain name, and HTTP GET health probe on `/`.
- **FR-012**: System MUST ensure the orchestrator wires all modules with correct dependency ordering: Log Analytics → Container Apps Environment, Managed Identity → Role Assignments, Key Vault → Secrets, Registry → Container Apps, OpenAI → AI Foundry Hub → AI Foundry Project.
- **FR-013**: System MUST update the backend code to authenticate with Azure OpenAI using credential-based managed identity authentication with the managed identity client ID, removing API key as the sole authentication method while maintaining backward compatibility for local development (API key fallback when available).
- **FR-014**: System MUST add the Azure identity library to backend dependencies.
- **FR-015**: System MUST integrate the Microsoft Agent Framework in the backend chat endpoint while maintaining backward compatibility with the existing chat API contract (same request/response format).
- **FR-016**: System MUST ensure the backend's existing health endpoint returns 200 OK with healthy status (already present; verify and preserve).
- **FR-017**: System MUST update the frontend web server configuration to support a backend URL environment variable for proxying API requests to the backend container app's internal address, using environment variable substitution at runtime.
- **FR-018**: System MUST create a CI/CD deployment workflow with three jobs: (1) build-and-push — build and push container images to the registry with commit hash and latest tags using federated Azure login; (2) deploy-infra — deploy infrastructure templates with parameters, ensure resource group exists; (3) deploy-apps — update container apps to new image tags and verify health. Triggered on push to main branch with appropriate identity and content permissions.
- **FR-019**: System MUST document manual repository configuration steps: Azure identity registration, federated credentials for the repo/main branch, repository secrets (Azure client ID, tenant ID, subscription ID, GitHub token value), and required Azure roles (Contributor, User Access Administrator).
- **FR-020**: System MUST update the root README with an architecture diagram, prerequisites, initial setup steps, infrastructure deployment instructions, CI/CD pipeline explanation, local development instructions (existing docker-compose preserved), and environment variables reference table.
- **FR-021**: System MUST create an infrastructure README documenting all deployment parameters, module dependency graph, and infrastructure tear-down process.
- **FR-022**: System MUST ensure all deployments are idempotent — re-running infrastructure deployments or CI/CD pipelines produces no errors or duplicate resources.
- **FR-023**: System MUST ensure no secrets are stored in the repository or workflow files (except identity configuration: client ID, tenant ID, subscription ID, and the GitHub PAT for initial vault seeding via repository secret).
- **FR-024**: System MUST ensure all CI/CD workflow jobs report failures clearly in logs with actionable error messages.

### Key Entities

- **Azure Resource Group**: Logical container for all Azure resources, scoped to a single production environment.
- **User-Assigned Managed Identity**: Shared security principal used by both container apps for authentication to the registry, vault, and OpenAI — eliminates all API keys and connection strings.
- **Key Vault**: Centralized secret store holding the GitHub token, OpenAI endpoint, and deployment name — accessible only via managed identity role-based access control.
- **Container Apps Environment**: Shared hosting environment for both backend and frontend container apps, linked to Log Analytics for observability.
- **Azure OpenAI Resource**: AI model hosting with gpt-4.1 deployment, accessed via managed identity (no API keys).
- **AI Foundry Hub/Project**: Model management layer linking the OpenAI resource for governance and project organization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All Azure resources are provisionable via a single deployment command with no manual portal steps (except initial identity registration), completing within 15 minutes.
- **SC-002**: The CI/CD pipeline triggers on push to main and completes all three jobs (build, infra, deploy) within 20 minutes end-to-end.
- **SC-003**: The backend container app authenticates to Azure OpenAI using managed identity — zero API keys are stored in environment variables, code, or configuration in production.
- **SC-004**: The frontend container app is publicly accessible and successfully proxies requests to the backend, with end-to-end request completion in under 5 seconds for standard chat interactions.
- **SC-005**: Both container apps pull images from the registry using managed identity — no admin credentials or access keys are used.
- **SC-006**: Health check endpoints respond correctly: backend health endpoint returns 200 OK, frontend root returns 200 OK, within 2 seconds.
- **SC-007**: The entire infrastructure can be torn down and redeployed from scratch within 30 minutes following documentation instructions.
- **SC-008**: A new team member can follow the README documentation to complete initial Azure setup and trigger a successful deployment within 1 hour.
- **SC-009**: The deployment supports horizontal scaling (1-3 replicas per container app) with each replica independently authenticating via managed identity.
- **SC-010**: Zero secrets are exposed in repository code, workflow files, or CI/CD logs — all sensitive values are in the vault or repository encrypted secrets.

## Assumptions

- A valid Azure subscription is available with sufficient quota for all resources in the target region (default: eastus2).
- The deploying user or service principal has sufficient permissions to create Azure identity registrations and configure federated credentials.
- The gpt-4.1 model is available in the target Azure region; if not, the deployment may require region adjustment.
- Only a production environment is deployed; dev/staging environments are out of scope but the parameterized structure supports future multi-environment extension.
- The backend chat API contract (request/response format) is preserved; no breaking changes to the frontend-backend interface.
- Local development via docker-compose continues to work unchanged; Azure deployment is additive.
- The existing backend health endpoint is sufficient for container app health probes.
- The existing frontend web server configuration uses a backend host variable for proxying; this will be updated or aliased for Azure deployment compatibility while maintaining docker-compose compatibility.
- The Microsoft Agent SDK is available and compatible with the existing backend and Python version.
- The CI/CD identity provider is configured and trusted by the Azure tenant for the target subscription.

## Out of Scope

- Custom GitHub Agents (the `/api/agent` routes and related tooling)
- Multi-environment deployments (dev, staging) — production only for this iteration
- Frontend application logic changes (no React component changes)
- Custom domain or SSL certificate configuration for container apps
- Database or persistent storage provisioning (application is stateless)
- Monitoring dashboards or alerting rules beyond basic log analytics
- Load testing or performance benchmarking infrastructure
