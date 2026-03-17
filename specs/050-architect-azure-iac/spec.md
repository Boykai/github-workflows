# Feature Specification: Architect Agent for Azure IaC

**Feature Branch**: `050-architect-azure-iac`  
**Created**: 2026-03-17  
**Status**: Draft  
**Input**: User description: "Create a new Architect utility agent (.github/agents/architect.agent.md) that generates Infrastructure as Code using Bicep, Azure Developer CLI (azd), and architecture diagrams. Equipped with four MCP servers — Context7, CodeGraphContext, Bicep (via VS Code extension), and Azure MCP. Produces azd-compatible project scaffolds with 1-click Deploy to Azure buttons on new app READMEs. Always invoked during the Solune Create New App flow, which also collects Azure Client ID/Secret and stores them as GitHub repo secrets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New App Ships with Azure-Ready Infrastructure (Priority: P1)

A developer creates a new application through the Solune "Create New App" flow. After the app repository is scaffolded, the Architect agent automatically generates a complete Azure infrastructure package: Bicep modules for all required cloud resources, an `azure.yaml` manifest for Azure Developer CLI compatibility, architecture diagrams documenting the system design, and a "Deploy to Azure" button in the app README. The developer can immediately deploy the app to Azure using `azd up` without writing any infrastructure code manually.

**Why this priority**: This is the core value proposition — every new Solune app ships Azure-ready out of the box. Without this, developers must manually author infrastructure code, which delays first deployment and introduces inconsistency across apps.

**Independent Test**: Can be fully tested by triggering the Architect agent on a freshly scaffolded app repository and verifying that the `infra/` directory, `azure.yaml`, architecture diagrams, and README deploy button are all generated and structurally valid.

**Acceptance Scenarios**:

1. **Given** a new app repository has been scaffolded via the Solune "Create New App" flow, **When** the Architect agent is invoked on the repository, **Then** the agent analyzes the project structure and generates a complete `infra/` directory containing `main.bicep`, per-resource Bicep modules, and `main.bicepparam`.
2. **Given** the Architect agent has generated Bicep modules for a new app, **When** `az bicep build --file infra/main.bicep` is run against the generated output, **Then** the build succeeds without errors.
3. **Given** the Architect agent has completed its run on a new app, **When** a developer inspects the app README, **Then** a "Deploy to Azure" badge and `azd init` one-liner are present.
4. **Given** the Architect agent has generated an `azure.yaml` manifest, **When** a developer runs `azd init` followed by `azd up` in the repository, **Then** the Azure Developer CLI recognizes the manifest and proceeds with deployment without requiring additional configuration.

---

### User Story 2 - Azure Credentials Securely Stored During App Creation (Priority: P1)

A developer creating a new app through the Solune UI is presented with optional fields for Azure Client ID and Azure Client Secret. When they provide these credentials, the values are encrypted and stored as GitHub repository secrets (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`) via the GitHub Secrets API. The Architect agent's generated CI/CD workflows reference these secrets for `azd` authentication — credentials never appear in source code, logs, or plaintext anywhere.

**Why this priority**: Secure credential management is foundational. If credentials are mishandled, the entire deployment pipeline is compromised. This shares P1 because the deploy workflow depends on properly stored secrets.

**Independent Test**: Can be fully tested by creating a new app via the Solune UI with Azure credentials provided, then verifying that `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET` appear in the new repository's GitHub Secrets and that no plaintext credentials exist in any generated files.

**Acceptance Scenarios**:

1. **Given** a developer is on the Solune "Create New App" form, **When** they fill in the Azure Client ID and Azure Client Secret fields and submit, **Then** the backend stores these values as encrypted GitHub repository secrets named `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET`.
2. **Given** Azure credentials have been stored as GitHub Secrets for a new app, **When** the Architect agent generates CI/CD workflows, **Then** the workflows reference `${{ secrets.AZURE_CLIENT_ID }}` and `${{ secrets.AZURE_CLIENT_SECRET }}` — no plaintext credentials appear anywhere.
3. **Given** a developer is on the Solune "Create New App" form, **When** they leave the Azure credential fields empty and submit, **Then** the app is created normally without Azure secrets, and the Architect agent still generates infrastructure code that can be deployed once credentials are configured later.
4. **Given** the Azure Client Secret field on the "Create New App" form, **When** a developer types into it, **Then** the input is masked (password field behavior) so the secret is not visible on screen.

---

### User Story 3 - Architecture Diagrams Generated for Every New App (Priority: P2)

When the Architect agent runs for a new app, it generates Mermaid-format architecture diagrams (`.mmd` files) that document the system design. These diagrams follow the established pattern in `solune/docs/architectures/` (high-level, deployment, components, and data-flow views) and are placed in the app's `docs/architectures/` directory. Diagrams are immediately renderable in GitHub's markdown preview and other Mermaid-compatible tools.

**Why this priority**: Architecture documentation is valuable for onboarding, reviews, and audits, but the app can be deployed without it. Diagrams enhance understanding but are not a deployment blocker.

**Independent Test**: Can be tested by running the Architect agent on a new app and verifying that `.mmd` files are created in `docs/architectures/`, follow the Mermaid syntax, and render correctly when previewed.

**Acceptance Scenarios**:

1. **Given** the Architect agent is analyzing a new app's project structure, **When** it generates architecture diagrams, **Then** at least a high-level architecture diagram and a deployment diagram are produced as `.mmd` files in the app's `docs/architectures/` directory.
2. **Given** the Architect agent has generated `.mmd` diagram files, **When** the files are opened in any Mermaid-compatible renderer (GitHub markdown, VS Code Mermaid extension), **Then** the diagrams render correctly without syntax errors.
3. **Given** an existing Solune app that already has diagrams in `solune/docs/architectures/`, **When** the Architect agent generates diagrams for a new app, **Then** the new diagrams follow the same Mermaid conventions (graph type, labeling, arrow notation) used in the existing diagrams.

---

### User Story 4 - MCP Configuration Enables Agent Tooling (Priority: P2)

The Azure MCP server is configured in both `.vscode/mcp.json` (for local development) and `.github/agents/mcp.json` (for remote GitHub Custom Agents). When a developer opens VS Code Agent mode and clicks the tools icon, Azure MCP tools are listed alongside existing tools. The Architect agent uses these MCP servers — Context7, CodeGraphContext, Azure MCP, and Bicep (via extension) — to access Azure resource schemas, Bicep best practices, and project dependency graphs during IaC generation.

**Why this priority**: MCP configuration is the foundation that enables the agent's tooling capabilities. It is P2 because the configuration itself is an enabler — the user-facing value comes from the agent generating correct infrastructure, which requires these tools.

**Independent Test**: Can be tested by opening VS Code with the updated MCP configuration and verifying that Azure MCP tools appear in the tools list, and by confirming the `.github/agents/mcp.json` entry follows the existing pattern for remote agents.

**Acceptance Scenarios**:

1. **Given** a developer opens the repository in VS Code, **When** they enter Agent mode and view the available tools, **Then** Azure MCP server tools are listed alongside the 8 existing MCP servers.
2. **Given** the `.github/agents/mcp.json` has been updated with an Azure MCP entry, **When** a GitHub Custom Agent (the Architect) is invoked remotely, **Then** it can access Azure MCP tools for resource schema lookups and Bicep best practices.
3. **Given** a `.bicep` file is present in the workspace, **When** the Bicep VS Code extension is installed, **Then** the Bicep MCP server auto-activates and provides Bicep-specific tools without requiring a separate `mcp.json` entry.

---

### User Story 5 - Agent and Prompt Files Registered in Copilot (Priority: P3)

The Architect agent file (`.github/agents/architect.agent.md`) and prompt file (`.github/prompts/architect.prompt.md`) are created following the established conventions of existing agents. The `copilot-instructions.md` utility agents table is updated to include the Architect. When a developer types `@architect` in VS Code Copilot, the agent appears in the picker and responds to infrastructure generation requests.

**Why this priority**: Registration and discoverability are the final polish — the agent must exist and work before it can be registered. Once the infrastructure generation capability is built, making it discoverable is straightforward.

**Independent Test**: Can be tested by opening the agent file in VS Code, confirming it appears in the Copilot agent picker, and verifying the prompt shortcut redirects correctly.

**Acceptance Scenarios**:

1. **Given** the `.github/agents/architect.agent.md` file exists with proper YAML frontmatter, **When** a developer opens VS Code and accesses the Copilot agent picker, **Then** "Architect" appears as an available agent.
2. **Given** the `.github/prompts/architect.prompt.md` file exists with `agent: architect`, **When** a developer uses the `/architect` prompt command, **Then** the request is routed to the Architect agent.
3. **Given** the `copilot-instructions.md` has been updated, **When** a developer reviews the utility agents table, **Then** `architect` is listed with a description: "Generates Azure IaC (Bicep), `azd` scaffolds, architecture diagrams, and deploy buttons. Always runs for new apps."

---

### Edge Cases

- What happens when the Architect agent analyzes a project that already has existing infrastructure (Bicep, Terraform, or ARM templates)? The agent detects existing infrastructure during its Discovery phase and adapts — it does not overwrite existing files but may suggest enhancements or flag conflicts.
- What happens when the Azure MCP server is unavailable during a remote agent run? The agent degrades gracefully — it generates Bicep and `azure.yaml` using schema knowledge from Context7 and Azure Verified Modules metadata. Live resource queries are skipped; only locally authenticated sessions support those.
- What happens when the user provides an Azure Client ID but not a Client Secret (or vice versa)? The frontend validates that either both fields are filled or both are empty. Submitting with only one field populated shows a validation error.
- What happens when the GitHub Secrets API call fails (e.g., rate limiting or permissions error)? The app creation still succeeds, but the user is notified that Azure credential storage failed and they should add secrets manually via the repository settings.
- What happens when the Bicep VS Code extension is not installed locally? The Architect agent still functions using Context7 for Bicep documentation and Azure MCP's built-in Bicep tool area as a fallback. A warning is logged suggesting the extension be installed for the best experience.
- What happens when a generated Bicep module references an Azure Verified Module that has been deprecated or versioned? The agent uses the latest stable AVM version available at generation time and documents the version used in the generated code comments.
- What happens when the branch name for a generated deploy workflow exceeds GitHub's 244-byte limit? This does not apply — the agent generates workflow files with standard names (e.g., `deploy.yml`) that are independent of branch naming.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a new Architect utility agent defined in `.github/agents/architect.agent.md` with proper YAML frontmatter including name, description, and MCP server declarations.
- **FR-002**: System MUST provide a prompt shortcut file at `.github/prompts/architect.prompt.md` that routes to the Architect agent, matching the pattern of existing prompt files.
- **FR-003**: The Architect agent MUST perform a Discovery phase that analyzes project structure (docker-compose, services, existing infrastructure files) before generating any output.
- **FR-004**: The Architect agent MUST generate Mermaid-format architecture diagrams (`.mmd` files) covering at least high-level and deployment views, placed in the app's `docs/architectures/` directory.
- **FR-005**: The Architect agent MUST generate Bicep infrastructure modules structured as `infra/main.bicep`, per-resource modules, and `main.bicepparam`, using Azure Verified Modules (AVM) when available.
- **FR-006**: The Architect agent MUST generate an `azure.yaml` manifest compatible with `azd init` / `azd up` / `azd deploy` workflows, defining services, hooks, and environment configuration.
- **FR-007**: The Architect agent MUST add a "Deploy to Azure" badge and `azd init` one-liner to the app README for every new app.
- **FR-008**: The Architect agent MUST generate CI/CD workflow files that reference GitHub Secrets (`${{ secrets.AZURE_CLIENT_ID }}` and `${{ secrets.AZURE_CLIENT_SECRET }}`) for `azd` authentication — no plaintext credentials anywhere.
- **FR-009**: The Architect agent MUST validate its output: Bicep compiles via `az bicep build`, `azure.yaml` is structurally valid, and diagrams use correct Mermaid syntax.
- **FR-010**: The Architect agent MUST always prefer Bicep over ARM JSON for infrastructure definitions.
- **FR-011**: The Architect agent MUST follow Azure Well-Architected Framework principles when making infrastructure design decisions.
- **FR-012**: The Architect agent MUST never hardcode secrets — it MUST use Key Vault references, managed identity, and GitHub Secrets for all sensitive values.
- **FR-013**: Azure MCP server MUST be added to `.vscode/mcp.json` using `npx @azure/mcp@latest server start` as the stdio command for local development.
- **FR-014**: Azure MCP server MUST be added to `.github/agents/mcp.json` using the local/stdio `npx` pattern for remote GitHub Custom Agents.
- **FR-015**: The Solune "Create New App" form MUST include optional input fields for Azure Client ID and Azure Client Secret (password-masked).
- **FR-016**: The backend app-creation flow MUST accept optional Azure credentials and store them as encrypted GitHub repository secrets via the GitHub Secrets API (`PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}`).
- **FR-017**: The Architect agent MUST be automatically invoked after every new app repository is scaffolded — this is not optional.
- **FR-018**: The `copilot-instructions.md` utility agents table MUST be updated to include the Architect agent with its description.
- **FR-019**: The MCP Configuration section in `copilot-instructions.md` MUST note Azure MCP availability in `.github/agents/mcp.json`.
- **FR-020**: The Architect agent MUST use `azd` environment variables for parameterization rather than hardcoded values.
- **FR-021**: The Architect agent MUST follow existing project naming conventions discovered via CodeGraphContext during its Discovery phase.

### Key Entities

- **Architect Agent**: A utility agent that generates Azure infrastructure code, deployment scaffolds, architecture diagrams, and deploy buttons. Operates standalone with no handoffs. Equipped with Context7, CodeGraphContext, Azure MCP, and Bicep MCP servers.
- **Azure MCP Server**: A Model Context Protocol server providing Azure resource schema lookups, Bicep best practices, Well-Architected Framework guidance, and live Azure resource queries (when authenticated). Installed via `npx @azure/mcp@latest` or VS Code extension.
- **Bicep Module**: An infrastructure-as-code file using Azure Bicep language. Organized as `main.bicep` (entry point), per-resource modules (e.g., `containerApp.bicep`, `containerRegistry.bicep`), and `main.bicepparam` (parameters).
- **Azure Developer CLI Manifest (`azure.yaml`)**: Configuration file defining services, deployment hooks, and environment settings for the `azd` toolchain. Enables `azd init` / `azd up` / `azd deploy` workflows.
- **Deploy Button**: A "Deploy to Azure" markdown badge and `azd init` one-liner in the app README, enabling 1-click deployment for anyone visiting the repository.
- **Azure Credentials (GitHub Secrets)**: `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET` stored as encrypted repository secrets. Collected optionally during app creation, referenced by CI/CD workflows, never present in source code.

### Assumptions

- Azure MCP is GA 1.0 at `microsoft/mcp` (the old `Azure/azure-mcp` was archived February 2026). The `npx @azure/mcp@latest` command is the canonical installation method.
- Bicep MCP is auto-provided by the Bicep VS Code extension (`ms-azuretools.vscode-bicep`) and does not need a `mcp.json` entry — it activates when a `.bicep` file is present.
- Custom GitHub Agents do not support handoffs — the Architect agent operates standalone.
- The Architect agent is a utility agent, not a SpecKit pipeline agent, and can be invoked independently.
- Mermaid format (`.mmd` files) is used for diagrams, matching the 5 existing diagrams in `solune/docs/architectures/`.
- The agent generates code but does not provision resources — it does not run `azd up` or interact with live Azure subscriptions during generation.
- The existing Solune "Create New App" frontend and backend flows support adding new form fields and extending the create-app payload without architectural changes.
- The GitHub Secrets API requires the repository's public key for encryption, which the backend retrieves before storing secrets.
- For remote agent runs without local Azure authentication, the agent degrades gracefully by relying on schema-based generation via Context7 and AVM metadata.

### Out of Scope

- Terraform or ARM JSON infrastructure generation — Bicep is the exclusive IaC language.
- Running `azd up` or provisioning live Azure resources — the agent generates code only.
- Self-hosting the Azure MCP server on Azure Container Apps — local/stdio is used initially.
- Multi-cloud support — this feature targets Azure exclusively.
- Modifying the SpecKit pipeline agent chain to include the Architect agent — it is a utility agent invoked separately.
- Automatic Azure subscription provisioning or billing configuration.
- Migration tooling for converting existing Terraform or ARM templates to Bicep.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every new Solune app created through the "Create New App" flow includes a complete `infra/` directory, `azure.yaml` manifest, architecture diagrams, and a "Deploy to Azure" button in the README — 100% of new apps ship Azure-ready.
- **SC-002**: Generated Bicep modules compile successfully via `az bicep build` on first generation for at least 95% of app types supported by the Solune platform.
- **SC-003**: Developers can go from app creation to first Azure deployment in under 10 minutes using the generated `azd up` command, assuming valid Azure credentials are configured.
- **SC-004**: Generated architecture diagrams render correctly in GitHub's markdown preview and Mermaid-compatible tools without syntax errors for 100% of generated apps.
- **SC-005**: Azure credentials provided during app creation are stored as encrypted GitHub Secrets within 5 seconds of form submission and are never present in plaintext in any generated file, log, or API response.
- **SC-006**: The Architect agent is discoverable in the VS Code Copilot agent picker and responds to infrastructure generation prompts (e.g., `@architect Create an Azure Container App deployment`) with valid Bicep + azure.yaml + deploy button output.
- **SC-007**: Generated CI/CD workflows pass security scanning — no hardcoded secrets, all credentials referenced via `${{ secrets.* }}` pattern.
- **SC-008**: The Azure MCP server tools are visible in VS Code Agent mode's tool list alongside existing MCP servers after configuration updates.
