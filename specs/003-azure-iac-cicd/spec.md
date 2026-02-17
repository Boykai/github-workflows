# Feature Specification: Azure Infrastructure as Code, CI/CD, and Secure Deployment

**Feature Branch**: `003-azure-iac-cicd`  
**Created**: 2026-02-17  
**Status**: Draft  
**Input**: User description: "Implement Azure Infrastructure as Code (Bicep), CI/CD pipelines (GitHub Actions), and Azure cloud deployment for the GitHub Projects Chat application. Deploy both services (Python/FastAPI backend and React/Vite frontend) to Azure Container Apps with full IaC, secret management via Azure Key Vault, Azure AI Foundry for model management, and a zero-trust security posture using managed identities throughout."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Infrastructure Provisioning via IaC (Priority: P1)

As a project maintainer, I want to define all Azure cloud resources in declarative infrastructure-as-code files so that the entire production environment can be created, updated, or torn down from the command line without any manual portal steps (beyond initial identity setup).

**Why this priority**: Without provisioned infrastructure, no deployment or CI/CD can function. This is the foundational layer upon which all other stories depend.

**Independent Test**: Can be fully tested by running a single deployment command against an Azure subscription and verifying that all expected resources (container registry, container apps environment, key vault, AI services, log analytics, managed identity) are created with the correct names, configurations, and role assignments.

**Acceptance Scenarios**:

1. **Given** the IaC files exist in the repository and an Azure subscription is available, **When** the maintainer runs the deployment command with a parameter file, **Then** all Azure resources are provisioned with names following the project naming convention and correct configurations.
2. **Given** all resources have been provisioned, **When** the maintainer runs the same deployment command again without changes, **Then** the deployment completes successfully and makes no modifications (idempotent).
3. **Given** a previously deployed environment, **When** the maintainer deletes the resource group, **Then** all resources are cleaned up and no orphaned resources remain.

---

### User Story 2 — Secure Secret Management (Priority: P1)

As a project maintainer, I want all application secrets (GitHub token, AI service endpoint, AI model deployment name) stored in a centralized, access-controlled vault and accessed only through managed identities, so that no secrets are embedded in code, configuration files, or CI/CD variables beyond the minimum needed for identity federation.

**Why this priority**: Security is a non-negotiable foundation. Without managed-identity-based secret access, the application would rely on API keys, which is a security risk.

**Independent Test**: Can be fully tested by verifying that the vault is provisioned with RBAC authorization, that the managed identity has the correct role assignment, and that the backend service can retrieve its configuration values from the vault at runtime without any API key.

**Acceptance Scenarios**:

1. **Given** the vault is provisioned with RBAC authorization, **When** a secret is stored, **Then** only principals with the appropriate role can read it; access-policy-based access is disabled.
2. **Given** the backend container app is running with a managed identity, **When** it starts up, **Then** it retrieves its required secrets (GitHub token, AI endpoint, AI deployment name) from the vault without any API key.
3. **Given** the backend must connect to the AI service, **When** it authenticates, **Then** it uses the managed identity credential (not an API key), and the environment contains no `AZURE_OPENAI_KEY` variable.

---

### User Story 3 — Automated CI/CD Pipeline (Priority: P2)

As a project maintainer, I want an automated pipeline that builds container images, deploys infrastructure, and updates the running application whenever code is pushed to the main branch, so that every change reaches production without manual intervention.

**Why this priority**: Automation reduces human error and enables rapid iteration, but it depends on having the infrastructure and security layers in place first.

**Independent Test**: Can be fully tested by pushing a commit to the main branch and verifying that the pipeline builds both container images, pushes them to the registry, deploys any infrastructure changes, updates both container apps to the new image, and confirms health check responses.

**Acceptance Scenarios**:

1. **Given** the pipeline is configured and required repository secrets are set, **When** a commit is pushed to the main branch, **Then** the pipeline triggers and completes three sequential jobs: build-and-push, deploy-infra, deploy-apps.
2. **Given** both container images are built and pushed to the registry, **When** the deploy-apps job runs, **Then** both container apps are updated to the new image tagged with the commit SHA.
3. **Given** the deploy-apps job has updated the container apps, **When** the health verification step runs, **Then** the backend health endpoint returns a 200 status with a healthy status indicator and the frontend responds on its public URL.
4. **Given** any job in the pipeline fails, **When** the failure is detected, **Then** subsequent jobs do not execute and the pipeline reports a clear error.

---

### User Story 4 — AI Service Provisioning and Model Deployment (Priority: P2)

As a project maintainer, I want the AI service account, AI hub, AI project, and the GPT-4.1 model deployment to be provisioned automatically through IaC, so that the backend has access to a managed AI model without manual setup in the Azure portal.

**Why this priority**: The AI model is a core dependency for the chat application, but its provisioning can build on the identity and vault infrastructure established in P1 stories.

**Independent Test**: Can be fully tested by deploying the IaC and verifying that the AI service, hub, and project exist, that a model deployment named `gpt-41` is active, and that the endpoint and deployment name are stored in the vault.

**Acceptance Scenarios**:

1. **Given** the IaC is deployed, **When** the AI resources are inspected, **Then** an AI service, hub, project, and model deployment (gpt-41) exist with correct associations.
2. **Given** the model is deployed, **When** the backend authenticates via managed identity, **Then** it can send a chat completion request and receive a response.
3. **Given** the AI service endpoint and deployment name are outputs of the IaC, **When** the vault secrets are inspected, **Then** they contain the correct endpoint URL and deployment name values.

---

### User Story 5 — Frontend-to-Backend Connectivity in Cloud (Priority: P2)

As an end user, I want to access the chat application through a public URL and have my requests seamlessly routed to the backend service, so that the application works in the cloud environment exactly as it does locally.

**Why this priority**: User-facing connectivity is essential for a production deployment, but depends on infrastructure and container app provisioning.

**Independent Test**: Can be fully tested by navigating to the frontend's public URL, verifying the page loads, and sending a chat message that is proxied to the internal backend and returns a response.

**Acceptance Scenarios**:

1. **Given** both container apps are deployed, **When** a user navigates to the frontend's public URL, **Then** the application loads and is fully functional.
2. **Given** the frontend is configured with the backend's internal address, **When** the frontend receives an API request from the browser, **Then** it proxies the request to the backend's internal endpoint and returns the response.
3. **Given** the backend is configured with internal-only ingress, **When** an external request is made directly to the backend's FQDN, **Then** the request is denied (backend is not publicly accessible).

---

### User Story 6 — Documentation for Setup and Operations (Priority: P3)

As a new team member or contributor, I want clear documentation covering architecture, prerequisites, initial setup, deployment, local development, and environment variables, so that I can onboard and operate the system without tribal knowledge.

**Why this priority**: Documentation is important for maintainability but does not block deployment or functionality.

**Independent Test**: Can be tested by having a new contributor follow the documentation from scratch: setting up the identity provider, configuring repository secrets, deploying infrastructure, and verifying a working deployment.

**Acceptance Scenarios**:

1. **Given** the README is updated, **When** a new contributor reads it, **Then** they find an architecture diagram, prerequisites list, step-by-step setup instructions, and environment variable reference.
2. **Given** the infrastructure README exists, **When** an operator needs to tear down the environment, **Then** they find clear teardown instructions.
3. **Given** a contributor wants to develop locally, **When** they read the documentation, **Then** they find the existing docker-compose instructions preserved alongside the cloud deployment information.

---

### Edge Cases

- What happens when the managed identity role assignment is not yet propagated at the time the container app starts? The container app should handle delayed identity propagation gracefully and become available once permissions are active; it should report unhealthy status until dependencies are reachable.
- What happens when the AI model deployment capacity is exhausted? The backend should return a user-friendly error indicating temporary unavailability, not expose internal details.
- What happens when the vault is temporarily unreachable? The backend should fail its health check and container orchestration should restart the instance.
- What happens when the container registry is empty (first-ever deployment)? The CI/CD pipeline must build and push images before deploying infrastructure that references them, or the container apps must tolerate a missing image on initial infrastructure deployment.
- What happens when the GitHub PAT stored in the vault expires or is revoked? The application should return a clear error for GitHub-dependent operations; health check may optionally report degraded status.
- What happens when IaC deployment is run concurrently (e.g., two pushes in rapid succession)? The pipeline should use concurrency controls to prevent conflicting deployments.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST organize all infrastructure-as-code files in an `infra/` directory with a single entry-point orchestrator file, a parameter file, and individual module files for each Azure resource.
- **FR-002**: System MUST parameterize all resource creation using at minimum: project name (alphanumeric, lowercase), environment identifier, and Azure region.
- **FR-003**: System MUST name all Azure resources following the Azure Cloud Adoption Framework naming convention patterns specified in the issue (e.g., `rg-{projectName}-{env}`, `cr{projectName}{env}`, `kv-{projectName}-{env}`).
- **FR-004**: System MUST provision a log analytics workspace with PerGB2018 SKU and 30-day retention, used for container app environment logging.
- **FR-005**: System MUST provision a container registry with Basic SKU and admin user disabled; image pull access granted to the shared managed identity.
- **FR-006**: System MUST provision a key vault with standard SKU, RBAC authorization (not access policies), soft delete enabled, and purge protection enabled.
- **FR-007**: System MUST store the following secrets in the vault: GitHub token, AI service endpoint, and AI model deployment name. No AI service API key is stored.
- **FR-008**: System MUST provision a user-assigned managed identity shared by both container apps, with role assignments for container registry pull, vault secret reading, and AI service usage.
- **FR-009**: System MUST provision an AI service account (S0 SKU) with a GPT-4.1 model deployment (deployment name `gpt-41`, parameterized capacity defaulting to 10K TPM).
- **FR-010**: System MUST provision an AI Foundry hub associated with the vault and log analytics, and an AI Foundry project linked to the AI service.
- **FR-011**: System MUST provision a container apps environment linked to the log analytics workspace, without zone redundancy.
- **FR-012**: System MUST provision a backend container app with internal-only ingress on port 8000, user-assigned managed identity, environment variables sourced from vault secrets (GitHub token, AI endpoint, AI deployment name) plus managed identity client ID, a health probe on `/health`, and configurable scaling (min 1, max 3 replicas, 0.5 CPU, 1Gi memory).
- **FR-013**: System MUST provision a frontend container app with external (public) ingress on port 80, user-assigned managed identity, environment variable for the backend's internal FQDN, a health probe on `/`, and configurable scaling (min 1, max 3 replicas, 0.5 CPU, 1Gi memory).
- **FR-014**: System MUST update the backend to authenticate with the AI service using the default credential chain with a user-assigned managed identity (via `AZURE_CLIENT_ID` environment variable), removing all API key references.
- **FR-015**: System MUST add `azure-identity` as a backend dependency.
- **FR-016**: System MUST ensure the backend exposes a `/health` endpoint returning HTTP 200 with a JSON body indicating healthy status.
- **FR-017**: System MUST update the frontend's web server configuration to use an environment variable for the backend proxy target address, with runtime substitution at container startup.
- **FR-018**: System MUST implement a CI/CD pipeline triggered on push to the main branch, with three sequential jobs: (1) build and push container images to the registry, (2) deploy infrastructure, (3) update container apps with new images and verify health.
- **FR-019**: System MUST use federated identity (OIDC) for CI/CD pipeline authentication to Azure — no Azure credentials stored as long-lived secrets.
- **FR-020**: System MUST tag container images with both the git commit SHA and `latest`.
- **FR-021**: System MUST document in the README: architecture diagram, prerequisites, initial setup instructions (identity provider, federated credentials, repository secrets), infrastructure deployment, CI/CD flow, local development, and environment variable reference.
- **FR-022**: System MUST create infrastructure-specific documentation covering all parameters, module dependency graph, and teardown instructions.
- **FR-023**: System MUST ensure the orchestrator wires modules with correct dependency ordering: log analytics before container apps environment, managed identity before role assignments, vault before secrets, registry before container apps, AI service before AI hub before AI project.
- **FR-024**: System MUST ensure no application secrets (beyond OIDC configuration values and the initial GitHub PAT for vault seeding) are stored in the CI/CD system.
- **FR-025**: System MUST integrate the Microsoft Agent Framework SDK in the backend chat endpoint while maintaining backward compatibility with the existing chat API contract.

### Key Entities

- **Managed Identity**: A user-assigned identity shared by both container apps; holds role assignments for registry pull, vault secret access, and AI service usage.
- **Key Vault**: Centralized secret store using RBAC authorization; contains GitHub token, AI endpoint, and AI deployment name. Protected by soft delete and purge protection.
- **Container App (Backend)**: Internal-only service running the Python/FastAPI application on port 8000; retrieves configuration from vault via managed identity.
- **Container App (Frontend)**: Public-facing service running the React/Vite application behind a web server on port 80; proxies API requests to the backend's internal address.
- **Container Registry**: Private registry storing both container images; access controlled by managed identity (no admin credentials).
- **AI Service + Model Deployment**: Azure AI service with a deployed GPT-4.1 model; endpoint and deployment name are stored in the vault.
- **AI Foundry Hub & Project**: Management layer for AI resources; hub associated with vault and log analytics, project linked to the AI service.
- **Container Apps Environment**: Shared hosting environment for both container apps; linked to log analytics for centralized logging.
- **CI/CD Pipeline**: Automated workflow that builds, pushes, deploys, and verifies on every push to main; authenticates via OIDC federation.

## Assumptions

- **Single environment**: Only a production environment is in scope; no dev/staging/preview environments.
- **Azure AD app registration**: An Azure AD app registration with federated credentials for the GitHub repository and main branch will be created manually as a one-time prerequisite. This is documented but not automated.
- **GitHub PAT**: A GitHub personal access token for the application's GitHub API access will be manually created and stored as a GitHub repository secret for initial Key Vault seeding.
- **Model availability**: The GPT-4.1 model is available in the selected Azure region. If not, the operator selects a region where it is available.
- **Container app image on first deploy**: The CI/CD pipeline builds and pushes images before infrastructure references them. On the very first deployment, the infrastructure and image build may need to be coordinated (pipeline handles this by ordering jobs).
- **Backend health endpoint**: The existing backend exposes a health endpoint at `/api/v1/health`. The container app health probe must target the path where this endpoint is reachable.
- **No frontend code changes**: Only the web server configuration and Docker entrypoint are modified; no React/Vite source code changes.
- **Out of scope**: Custom GitHub Agents (`/api/agent` routes), multi-environment deployments, and frontend application logic changes.
- **Performance defaults**: Standard web application performance expectations apply (page load under 3 seconds, API response under 5 seconds under normal load).
- **Error handling**: User-friendly error messages with appropriate fallbacks are used throughout; no internal details exposed to end users.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All Azure resources can be provisioned from scratch by running a single deployment command with a parameter file, completing within 15 minutes.
- **SC-002**: Re-running the deployment command on an already-provisioned environment completes successfully with no changes (idempotent deployment).
- **SC-003**: The CI/CD pipeline completes all three jobs (build-push, deploy-infra, deploy-apps) within 15 minutes on a typical push to main.
- **SC-004**: The backend service authenticates to the AI service using managed identity only — no API keys are present in configuration, code, or secrets.
- **SC-005**: The frontend is publicly accessible and returns a 200 response within 3 seconds of the page load request.
- **SC-006**: The backend health endpoint returns a 200 response with healthy status within 2 seconds.
- **SC-007**: A chat message sent through the frontend is proxied to the backend, processed by the AI model, and a response is returned to the user within 10 seconds under normal conditions.
- **SC-008**: Zero application secrets are stored in the CI/CD system beyond OIDC federation values (client ID, tenant ID, subscription ID) and the GitHub PAT for initial vault seeding.
- **SC-009**: A new contributor can follow the documentation to set up and deploy the application to a fresh Azure subscription within 60 minutes.
- **SC-010**: Infrastructure teardown (resource group deletion) removes all provisioned resources with no orphaned resources remaining.
