# Feature Specification: Azure IaC, CI/CD, and Managed Identity Deployment

**Feature Branch**: `003-azure-iac-cicd`  
**Created**: 2026-02-16  
**Status**: Draft  
**Input**: User description: "Implement Azure IaC, Managed Identity, AI Foundry, and CI/CD for GitHub Projects Chat app"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deploy Infrastructure from Code (Priority: P1)

As the repository owner, I want all Azure cloud resources (Container Apps, Container Registry, Key Vault, AI services, networking, identity) defined as Infrastructure as Code so that I can provision and reproduce the entire production environment with a single command, without any manual portal steps beyond initial Azure AD app registration.

**Why this priority**: Without the infrastructure foundation, no other deployment or security features can exist. This is the bedrock upon which all other stories depend.

**Independent Test**: Can be fully tested by running the infrastructure deployment command against an Azure subscription and verifying all resources are created with correct names, configurations, and interdependencies.

**Acceptance Scenarios**:

1. **Given** the Bicep templates exist in the `infra/` directory, **When** the operator runs the infrastructure deployment command, **Then** all Azure resources (Log Analytics, Container Registry, Key Vault, AI Foundry Hub, AI Foundry Project, OpenAI, Container Apps Environment, Managed Identity, Backend Container App, Frontend Container App) are provisioned with Cloud Adoption Framework naming conventions.
2. **Given** the infrastructure has been deployed once, **When** the operator runs the deployment command again with no changes, **Then** the deployment completes idempotently with no errors or resource recreation.
3. **Given** a parameter file specifying project name, environment, and location, **When** the deployment runs, **Then** all resource names incorporate these parameters according to the defined naming patterns.

---

### User Story 2 - Secure Secret Management and Identity-Based Authentication (Priority: P1)

As the repository owner, I want the application to use managed identities for all service-to-service authentication (Azure OpenAI, Container Registry image pulls, Key Vault secret access) so that no API keys or passwords are stored in code, configuration, or GitHub secrets beyond the minimum required for initial setup.

**Why this priority**: Security is a non-negotiable requirement. Managed identity authentication eliminates credential leakage risks and is a prerequisite for production readiness.

**Independent Test**: Can be tested by verifying the backend authenticates to Azure OpenAI without an API key, Container Apps pull images from the registry without admin credentials, and secrets are retrieved from Key Vault using role-based access.

**Acceptance Scenarios**:

1. **Given** the backend Container App is deployed with a user-assigned managed identity, **When** it makes a request to Azure OpenAI, **Then** it authenticates using the managed identity credential (no API key in environment or configuration).
2. **Given** the Key Vault is provisioned with RBAC authorization, **When** the Container App's managed identity requests a secret, **Then** it receives the secret value via the Key Vault Secrets User role assignment.
3. **Given** the Container Registry has admin user disabled, **When** the Container Apps pull images, **Then** they authenticate using the managed identity's AcrPull role assignment.
4. **Given** the GitHub repository secrets, **When** reviewing what is stored, **Then** only OIDC configuration (client ID, tenant ID, subscription ID) and the GitHub PAT for Key Vault seeding are present — no Azure API keys or passwords.

---

### User Story 3 - Automated CI/CD Pipeline (Priority: P2)

As the repository owner, I want a CI/CD pipeline that automatically builds container images, deploys infrastructure, and updates the running applications whenever code is pushed to the main branch, so that deployments are consistent, auditable, and require no manual intervention.

**Why this priority**: Automated deployment eliminates human error in the release process and enables continuous delivery. It depends on the infrastructure and security stories being complete.

**Independent Test**: Can be tested by pushing a commit to the main branch and verifying the pipeline builds images, deploys infrastructure, and updates Container Apps with the new image tags.

**Acceptance Scenarios**:

1. **Given** a commit is pushed to the `main` branch, **When** the CI/CD pipeline triggers, **Then** it executes three sequential jobs: build-and-push, deploy-infra, and deploy-apps.
2. **Given** the build-and-push job runs, **When** it completes, **Then** both backend and frontend Docker images are built, tagged with the commit SHA and `latest`, and pushed to the Azure Container Registry.
3. **Given** the deploy-infra job runs, **When** it completes, **Then** the Bicep templates are deployed to Azure, creating or updating all resources.
4. **Given** the deploy-apps job runs, **When** it completes, **Then** both Container Apps are updated to use the new image tag and a health verification confirms they are running.
5. **Given** the pipeline uses Azure login, **When** it authenticates, **Then** it uses OIDC federated credentials (no stored Azure passwords or service principal secrets).

---

### User Story 4 - Backend Health Check and AI Model Integration (Priority: P2)

As the repository owner, I want the backend to expose a health check endpoint and connect to the AI model through Azure AI Foundry so that the platform can monitor application health and the chat functionality uses the provisioned AI model deployment.

**Why this priority**: Health checks are required for Container Apps liveness/readiness probes. AI Foundry integration ensures the chat feature works with the cloud-deployed model.

**Independent Test**: Can be tested by calling the `/health` endpoint and verifying it returns a 200 OK status with a JSON health payload, and by sending a chat request to verify AI model connectivity.

**Acceptance Scenarios**:

1. **Given** the backend application is running, **When** a GET request is sent to `/health`, **Then** it returns HTTP 200 with `{"status": "healthy"}`.
2. **Given** the Azure OpenAI resource is provisioned with a gpt-4.1 model deployment, **When** the backend sends a chat completion request, **Then** it receives a response via managed identity authentication.
3. **Given** the AI Foundry Hub and Project are provisioned, **When** viewing the Azure portal, **Then** the project is linked to the OpenAI resource and the model deployment is visible.

---

### User Story 5 - Frontend Proxying to Backend via Internal FQDN (Priority: P2)

As the repository owner, I want the frontend container to dynamically proxy API requests to the backend using the backend's internal fully qualified domain name so that the frontend is publicly accessible while the backend remains internal-only.

**Why this priority**: Proper network segmentation (public frontend, internal backend) is a security best practice and ensures the backend is not directly exposed to the internet.

**Independent Test**: Can be tested by accessing the frontend's public URL and verifying that API requests are correctly proxied to the internal backend service.

**Acceptance Scenarios**:

1. **Given** the frontend Container App is deployed with external ingress, **When** a user accesses the public URL, **Then** the frontend application loads successfully.
2. **Given** the frontend Nginx configuration uses the `BACKEND_URL` environment variable, **When** the container starts, **Then** the variable is substituted into the Nginx config at runtime using envsubst.
3. **Given** the frontend proxies `/api/` requests, **When** a user interacts with the chat, **Then** the request is forwarded to the backend's internal FQDN on port 8000.

---

### User Story 6 - Comprehensive Documentation (Priority: P3)

As a developer or operator, I want clear documentation covering architecture, setup prerequisites, deployment instructions, and teardown procedures so that I can understand, maintain, and operate the system without tribal knowledge.

**Why this priority**: Documentation enables team onboarding and operational independence. While important, it does not block deployment functionality.

**Independent Test**: Can be tested by following the documented setup instructions from scratch on a new Azure subscription and verifying all steps complete successfully.

**Acceptance Scenarios**:

1. **Given** the README.md is updated, **When** a new developer reads it, **Then** they find an architecture diagram, prerequisites list, setup instructions, CI/CD explanation, local development instructions, and environment variable reference.
2. **Given** the infra/README.md exists, **When** an operator reads it, **Then** they find Bicep parameter documentation, module dependency graph, and teardown instructions.
3. **Given** the documentation references manual setup steps (Azure AD app registration, federated credentials, GitHub secrets), **When** an operator follows the steps, **Then** they can complete the initial setup without external guidance.

---

### Edge Cases

- What happens when the Azure OpenAI model deployment reaches its token-per-minute capacity limit? The system should return a user-friendly error message indicating temporary unavailability, and the Container App scaling rules should not trigger additional replicas for rate-limited responses.
- What happens when Key Vault is temporarily unreachable? The Container App should continue running with cached environment values and log the connectivity issue, rather than crashing.
- What happens when the Container Registry is unavailable during a CI/CD deployment? The pipeline should fail fast with a clear error message in the build-and-push job, preventing the deploy-infra and deploy-apps jobs from executing.
- What happens when the Bicep deployment is run against a resource group that already has partial resources from a failed previous deployment? The deployment should be idempotent and reconcile to the desired state without duplicating resources.
- What happens when the GitHub PAT stored in Key Vault expires? The backend should return a clear error on GitHub API calls indicating authentication failure, and the documentation should include instructions for rotating the PAT secret in Key Vault.

## Requirements *(mandatory)*

### Functional Requirements

#### Infrastructure as Code

- **FR-001**: System MUST provide a modular Bicep template structure under `infra/` containing `main.bicep`, `main.bicepparam`, and individual module files for each Azure resource (container-registry, container-apps-environment, container-app-backend, container-app-frontend, key-vault, ai-foundry-hub, ai-foundry-project, openai, log-analytics, managed-identity).
- **FR-002**: System MUST parameterize all Azure resources with `projectName`, `environment`, and `location` inputs, enforcing Azure Cloud Adoption Framework naming conventions for every resource (e.g., `rg-{projectName}-{env}`, `cr{projectName}{env}`, `kv-{projectName}-{env}`).
- **FR-003**: System MUST provision a Log Analytics Workspace with PerGB2018 SKU and 30-day retention, used by the Container Apps Environment for centralized logging.
- **FR-004**: System MUST provision an Azure Container Registry with Basic SKU, admin user disabled, and AcrPull role assigned to the shared managed identity.
- **FR-005**: System MUST provision a Key Vault with standard SKU, RBAC authorization enabled, soft delete enabled, purge protection enabled, and Key Vault Secrets User role assigned to the shared managed identity.
- **FR-006**: System MUST store the following secrets in Key Vault: `GITHUB-TOKEN` (GitHub PAT), `AZURE-OPENAI-ENDPOINT` (from OpenAI module output), and `AZURE-OPENAI-DEPLOYMENT` (model deployment name from OpenAI module output). No `AZURE-OPENAI-KEY` secret shall be stored.
- **FR-007**: System MUST provision an Azure OpenAI resource with S0 SKU, deploy a gpt-4.1 model with deployment name `gpt-41`, parameterized capacity (default 10K TPM), and assign the Cognitive Services OpenAI User role to the shared managed identity.
- **FR-008**: System MUST provision an AI Foundry Hub associated with the Key Vault and Log Analytics Workspace, with system-assigned managed identity enabled.
- **FR-009**: System MUST provision an AI Foundry Project under the AI Foundry Hub, linked to the Azure OpenAI resource.
- **FR-010**: System MUST provision a Container Apps Environment linked to the Log Analytics Workspace, without internal networking or zone redundancy.
- **FR-011**: System MUST create a User-Assigned Managed Identity shared by both Container Apps, with role assignments for AcrPull (on Container Registry), Key Vault Secrets User (on Key Vault), and Cognitive Services OpenAI User (on Azure OpenAI).
- **FR-012**: System MUST provision a Backend Container App with the user-assigned managed identity, internal-only ingress on port 8000, scaling from 1 to 3 replicas, 0.5 CPU / 1Gi memory, environment variables sourced from Key Vault secrets (GITHUB_TOKEN, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT) and AZURE_CLIENT_ID from the managed identity, and an HTTP health probe on `/health`.
- **FR-013**: System MUST provision a Frontend Container App with the user-assigned managed identity, external ingress on port 80, scaling from 1 to 3 replicas, 0.5 CPU / 1Gi memory, BACKEND_URL environment variable set to the backend's internal FQDN, and an HTTP health probe on `/`.
- **FR-014**: System MUST wire all modules in `main.bicep` with correct dependency ordering: Log Analytics → Container Apps Environment, Managed Identity → Role Assignments, Key Vault → Secrets, ACR → Container Apps, OpenAI → AI Foundry Hub → AI Foundry Project.

#### Backend Changes

- **FR-015**: System MUST update the backend to authenticate with Azure OpenAI using managed identity credentials instead of API keys, using the AZURE_CLIENT_ID environment variable for user-assigned managed identity selection.
- **FR-016**: System MUST remove all references to `AZURE_OPENAI_KEY` from backend code and configuration.
- **FR-017**: System MUST add a `/health` endpoint to the backend that returns HTTP 200 with `{"status": "healthy"}`.
- **FR-018**: System MUST add managed identity authentication dependencies to the backend's dependency configuration.

#### Frontend Changes

- **FR-019**: System MUST update the frontend Nginx configuration to use a `BACKEND_URL` environment variable for the proxy pass target, replacing any hardcoded backend address.
- **FR-020**: System MUST ensure the frontend Docker entrypoint substitutes environment variables into the Nginx configuration at runtime using envsubst.

#### CI/CD Pipeline

- **FR-021**: System MUST create a GitHub Actions workflow (`.github/workflows/deploy.yml`) triggered on push to the `main` branch, with OIDC permissions (`id-token: write`, `contents: read`).
- **FR-022**: System MUST implement a `build-and-push` job that checks out the repository, authenticates to Azure and ACR using OIDC, builds backend and frontend Docker images, tags them with the commit SHA and `latest`, and pushes them to ACR.
- **FR-023**: System MUST implement a `deploy-infra` job (depending on `build-and-push`) that checks out the repository, authenticates to Azure, creates the resource group if needed, and deploys the Bicep templates.
- **FR-024**: System MUST implement a `deploy-apps` job (depending on `deploy-infra`) that checks out the repository, authenticates to Azure, updates both Container Apps to the new image tag, and verifies deployment health.
- **FR-025**: System MUST document the required GitHub repository secrets (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID, GITHUB_TOKEN_VALUE) and the manual Azure AD app registration and federated credential setup steps.

#### Documentation

- **FR-026**: System MUST update README.md with a Mermaid architecture diagram, prerequisites, initial setup instructions, infrastructure deployment instructions, CI/CD pipeline explanation, preserved local docker-compose instructions, and an environment variables reference table.
- **FR-027**: System MUST create `infra/README.md` documenting all Bicep parameters, the module dependency graph, and the teardown process.

### Key Entities

- **Managed Identity**: A user-assigned identity shared across Container Apps that grants access to Container Registry, Key Vault, and Azure OpenAI without storing credentials.
- **Key Vault**: Centralized secret store holding the GitHub PAT, OpenAI endpoint, and deployment name. Accessed via RBAC role assignments, not access policies.
- **Container Apps Environment**: The shared hosting environment for both backend and frontend Container Apps, connected to Log Analytics for centralized monitoring.
- **AI Foundry Hub**: The organizational unit for AI resources, linking Key Vault and Log Analytics for governance and monitoring of AI model deployments.
- **AI Foundry Project**: A project scoped under the Hub, linking to the Azure OpenAI resource for model management and usage tracking.
- **CI/CD Pipeline**: A three-job GitHub Actions workflow that builds images, deploys infrastructure, and updates running applications on every push to main.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All Azure resources are deployed successfully via a single command with no manual portal steps (except initial Azure AD app registration), and re-running the deployment produces no errors (idempotent).
- **SC-002**: The backend Container App authenticates to Azure OpenAI using managed identity — no API keys are present in environment variables, configuration files, or GitHub secrets.
- **SC-003**: Both Container Apps pull images from the Container Registry using managed identity — admin user is disabled and no registry passwords are stored.
- **SC-004**: The CI/CD pipeline triggers on push to main and completes all three jobs (build-and-push, deploy-infra, deploy-apps) within 15 minutes for a typical deployment.
- **SC-005**: The frontend is publicly accessible via its external URL and correctly proxies API requests to the internal backend service.
- **SC-006**: The backend `/health` endpoint returns HTTP 200 with a healthy status within 2 seconds of being called.
- **SC-007**: The AI Foundry Hub and Project are provisioned and the gpt-4.1 model deployment is accessible to the backend via managed identity.
- **SC-008**: Documentation enables a new operator to complete the initial Azure AD setup, configure GitHub secrets, and trigger a successful first deployment by following the README instructions alone.
- **SC-009**: No secrets are stored in GitHub beyond the four required values (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID, GITHUB_TOKEN_VALUE).
- **SC-010**: The system scales the backend from 1 to 3 replicas under load and returns to 1 replica when load subsides.

## Assumptions

- The Azure subscription used for deployment has sufficient quota for all required resources (Container Apps, OpenAI S0, Container Registry Basic).
- The Azure region specified in the `location` parameter supports all required resource types (Container Apps, Azure OpenAI, AI Foundry).
- The operator has Owner or Contributor + User Access Administrator roles on the target Azure subscription or resource group for initial setup.
- The GitHub PAT provided for Key Vault storage has the necessary scopes for the application's GitHub API access requirements.
- The existing Docker Compose-based local development workflow is preserved and unaffected by cloud deployment changes.
- The `gpt-4.1` model is available in the specified Azure region at deployment time. If not available, the operator can substitute a different model name in the parameter file.
- The backend currently has no `/health` endpoint and one needs to be added.
- The frontend Nginx configuration currently uses a hardcoded or environment-variable-based backend address (`BACKEND_HOST`) that needs to be updated to support `BACKEND_URL`.
