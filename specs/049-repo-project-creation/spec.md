# Feature Specification: New Repository & New Project Creation for Solune

**Feature Branch**: `049-repo-project-creation`  
**Created**: 2026-03-17  
**Status**: Draft  
**Input**: User description: "Add New Repository and New Project creation capabilities throughout Solune. Users can: (A) create a new GitHub repo with template files + a linked Project V2 from the Apps page, (B) create a standalone GitHub Project V2 from the project selector dropdown anywhere in the app, and (C) combine both when creating a new app. All new projects get default Solune columns (Backlog / In Progress / In Review / Done). All new repos get .github/, .specify/, .gitignore with a generic copilot-instructions.md."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Create a New App with a New GitHub Repository (Priority: P1)

A user navigates to the Apps page and clicks "New App." They select the "New Repository" repo type from a segmented control. The dialog presents fields for the app name, display name, and description (common to all modes), plus fields specific to new-repo mode: an owner dropdown (personal account or any organization the user belongs to), a visibility toggle (public / private, defaulting to private), and a "Create linked project" checkbox (defaulting to on).

Upon submission, Solune creates a new GitHub repository under the chosen owner with the selected visibility. The repository is initialized with a default branch and populated with template files (all `.github/` files, all `.specify/` files, and `.gitignore`), where `copilot-instructions.md` is replaced with a generic placeholder containing TODO sections. If the "Create linked project" option is enabled, a GitHub Project V2 is also created, linked to the new repository, and configured with the default Solune status columns (Backlog, In Progress, In Review, Done). The app record is stored in the database with references to the new repository and project.

**Why this priority**: This is the primary value proposition of the feature — enabling users to bootstrap a fully scaffolded GitHub repository with Solune's standard configuration and a linked project board in a single action. Without this, users must manually create repos, add template files, create projects, and link them individually.

**Independent Test**: Can be fully tested by opening the Apps page, clicking "New App," selecting "New Repository" mode, filling in the form, and submitting. Delivers a ready-to-use GitHub repo with template files and a linked project board.

**Acceptance Scenarios**:

1. **Given** a user is on the Apps page, **When** they click "New App" and select "New Repository" mode, **Then** they see fields for app name, display name, description, owner dropdown, visibility toggle, and a "Create linked project" checkbox (on by default).
2. **Given** a user fills in valid app details in "New Repository" mode with a personal account as owner and private visibility, **When** they submit the form, **Then** a private GitHub repository is created under their personal account, initialized with a default branch and all template files (`.github/`, `.specify/`, `.gitignore`), and the `copilot-instructions.md` file contains a generic placeholder with TODO sections instead of project-specific content.
3. **Given** a user submits the "New Repository" form with "Create linked project" enabled, **When** creation succeeds, **Then** a GitHub Project V2 is created, linked to the new repository, and configured with Solune's default status columns (Backlog, In Progress, In Review, Done). The app record in the database includes the repository URL, project URL, and project ID.
4. **Given** a user submits the "New Repository" form with an organization as the owner, **When** the user has permission to create repos in that organization, **Then** the repository is created under that organization with the specified visibility.
5. **Given** a user submits the "New Repository" form and project creation fails after the repository was successfully created, **When** the error is non-blocking, **Then** the app is created with the repository details but with null project fields, and the user is informed that the project could not be created and can be retried later.

---

### User Story 2 — Create a Standalone GitHub Project V2 from the Project Selector (Priority: P2)

A user is working anywhere in Solune and opens the project selector dropdown. At the bottom of the project list, they see a "+ New Project" option. Clicking it opens a small dialog with fields for project title (required), an owner dropdown (personal account or organization), and an optional field to link the project to an existing repository.

Upon submission, Solune creates a GitHub Project V2 under the chosen owner, configures it with default Solune status columns, and optionally links it to the specified repository. The newly created project is automatically selected as the active project in the selector.

**Why this priority**: This enables users to create project boards on-the-fly from any context within Solune, without navigating away from their current task. It supports the common workflow of needing a new project board for an existing repository or as a standalone tracking board.

**Independent Test**: Can be fully tested by opening the project selector dropdown from any page, clicking "+ New Project," filling in the title and owner, and submitting. Delivers a new GitHub Project V2 that is immediately active in the selector.

**Acceptance Scenarios**:

1. **Given** a user opens the project selector dropdown, **When** the dropdown is displayed, **Then** a "+ New Project" option appears at the bottom of the project list.
2. **Given** a user clicks "+ New Project," **When** the dialog opens, **Then** they see fields for project title (required), owner dropdown, and an optional repository link field.
3. **Given** a user fills in a project title and owner, **When** they submit without linking a repository, **Then** a standalone GitHub Project V2 is created with default Solune status columns and automatically selected as the active project.
4. **Given** a user fills in a project title, owner, and selects an existing repository to link, **When** they submit, **Then** the project is created, linked to the specified repository, and auto-selected.

---

### User Story 3 — Create a New App with Same Repo Mode and Inline New Project (Priority: P3)

A user creates a new app using "Same Repo" mode. Within the creation dialog, the project selector field includes a "+ New Project" inline option. The user can create a new project right within the app creation flow without leaving the dialog. The new project is created, linked to the same repository, and associated with the app.

**Why this priority**: This extends the existing "Same Repo" workflow with the ability to create a new project inline, reducing friction for users who already have a repository but need a fresh project board for their app.

**Independent Test**: Can be fully tested by opening "New App," selecting "Same Repo" mode, clicking "+ New Project" within the project selector, creating a project, and completing the app creation. Delivers a new app linked to the newly created project.

**Acceptance Scenarios**:

1. **Given** a user is creating a new app in "Same Repo" mode, **When** they interact with the project selector field, **Then** they see a "+ New Project" option alongside existing projects.
2. **Given** a user clicks "+ New Project" in the same-repo app creation flow, **When** the inline project creation dialog opens, **Then** they can create a project that is automatically linked to the same repository and selected for the app.

---

### User Story 4 — Standalone "New Repository" Button on Apps Page (Priority: P3)

A user navigates to the Apps page and sees a standalone "New Repository" button (separate from the "New App" button). Clicking it opens the same creation dialog pre-set to "New Repository" mode, providing a quick shortcut for users who know they want to create a new repository.

**Why this priority**: This is a UX convenience shortcut that reduces the number of clicks for the most common creation action. It builds directly on the "New App" dialog from User Story 1.

**Independent Test**: Can be fully tested by clicking the "New Repository" button on the Apps page and verifying the dialog opens in "New Repository" mode with the same fields and behavior as Story 1.

**Acceptance Scenarios**:

1. **Given** a user is on the Apps page, **When** they click the "New Repository" button, **Then** the creation dialog opens pre-set to "New Repository" mode.
2. **Given** the dialog is opened via the "New Repository" button, **When** the user submits the form, **Then** the behavior is identical to creating a new app in "New Repository" mode (Story 1).

---

### User Story 5 — View Repository and Project Details on App Cards (Priority: P3)

After an app has been created with a new repository and/or project, the AppCard component displays a repo type badge (indicating "Same Repo," "New Repository," or "External Repo") and clickable links to the GitHub repository and project URLs. The AppDetailView also shows these links and metadata.

**Why this priority**: This provides visibility into how each app was created and quick navigation to the associated GitHub resources, improving the user experience for managing apps.

**Independent Test**: Can be fully tested by creating apps with different repo types and verifying that the correct badges and links appear on the AppCard and AppDetailView components.

**Acceptance Scenarios**:

1. **Given** an app was created with repo type "new-repo," **When** the user views the Apps page, **Then** the AppCard shows a "New Repository" badge and clickable links to the repository and project URLs.
2. **Given** an app has a linked GitHub project, **When** the user views the AppDetailView, **Then** the project URL is displayed as a clickable link.

---

### Edge Cases

- What happens when a user tries to create a repository with a name that already exists under the selected owner? The system displays a clear error message indicating the name conflict and allows the user to choose a different name.
- How does the system handle insufficient permissions when creating a repository in an organization? The owner dropdown only lists organizations where the user has repository creation permissions. If permissions change between loading and submission, a clear error message is shown.
- What happens if the network connection fails mid-creation (e.g., after the repository is created but before templates are committed)? The app creation fails with an error. Since the repository was already initialized, it exists but may lack template files. The user is informed and can retry or manually add templates.
- What happens if project column configuration fails after project creation? Column configuration is best-effort. The project is still created and linked; the user can manually configure columns in GitHub if the automatic setup fails.
- What happens if the user has no organizations? The owner dropdown only shows their personal account, which is sufficient for creating repositories.
- How does the system handle very long repository or project names? Repository names follow GitHub's naming constraints (max 100 characters, alphanumeric and hyphens). The form validates input before submission.
- What happens if the template source directory is missing or empty at runtime? The template file reader validates the source directory at startup. If files are unavailable, repository creation proceeds without templates and the user is informed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to create a new GitHub repository from the Apps page via a "New Repository" mode in the app creation dialog.
- **FR-002**: System MUST support selecting the repository owner from a list that includes the user's personal account and all organizations where the user can create repositories.
- **FR-003**: System MUST allow users to choose between public and private visibility for new repositories, defaulting to private.
- **FR-004**: New repositories MUST be initialized with a default branch and populated with all template files from `.github/`, `.specify/`, and `.gitignore`.
- **FR-005**: The `copilot-instructions.md` file in new repositories MUST be a generic placeholder with TODO sections (stack, conventions, testing, deployment), not the project-specific version from the workspace.
- **FR-006**: System MUST support creating a GitHub Project V2 linked to the new repository, with default Solune status columns (Backlog, In Progress, In Review, Done), as an optional step during repository creation.
- **FR-007**: System MUST allow users to create a standalone GitHub Project V2 from the project selector dropdown anywhere in the app, with fields for title, owner, and optional repository link.
- **FR-008**: Newly created standalone projects MUST be automatically selected as the active project after creation.
- **FR-009**: The app creation dialog MUST present a segmented control with three repo type options: "Same Repo," "New Repository," and "External Repo," with mode-specific fields shown conditionally.
- **FR-010**: System MUST support a "+ New Project" inline option within the project selector during "Same Repo" app creation, allowing project creation without leaving the dialog.
- **FR-011**: The Apps page MUST include a standalone "New Repository" button that opens the creation dialog pre-set to "New Repository" mode.
- **FR-012**: AppCard and AppDetailView MUST display a repo type badge and clickable links to the GitHub repository URL and project URL when available.
- **FR-013**: System MUST store the repository URL, project URL, and project ID in the app's database record for "new-repo" type apps.
- **FR-014**: If repository creation fails, the entire app creation MUST fail with a clear error message.
- **FR-015**: If project creation or linking fails after a successful repository creation, the app MUST be created with null project fields and the user MUST be informed that the project step failed.
- **FR-016**: Project V2 status column configuration (Backlog, In Progress, In Review, Done) MUST be attempted on a best-effort basis; failure MUST NOT block project creation.
- **FR-017**: The template file reader MUST validate against path traversal and symlink attacks when reading template files from the source directory.
- **FR-018**: The `branch` field MUST become optional when creating a "new-repo" type app, defaulting to the repository's default branch.

### Key Entities

- **App**: An application record in Solune. Extended with a new "new-repo" repo type, plus references to the associated GitHub repository URL, project URL, and project identifier. Represents the user's configured app within Solune, linked to GitHub resources.
- **GitHub Repository**: A code repository created under a user's personal account or organization. Initialized with template files and a default branch. Identified by owner, name, and unique identifier.
- **GitHub Project V2**: A project board for tracking work items. Configured with Solune's default status columns. Can be linked to a repository or exist standalone. Identified by unique identifier, number, and URL.
- **Owner**: A GitHub user or organization under which repositories and projects can be created. Includes the personal account and all organizations with appropriate permissions.
- **Template Files**: The set of `.github/`, `.specify/`, and `.gitignore` files bundled with the application and committed to new repositories during creation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new GitHub repository with template files and a linked project board in a single action, completing the entire flow in under 60 seconds from clicking "New App" to seeing the new app on the Apps page.
- **SC-002**: Users can create a standalone GitHub Project V2 from the project selector dropdown in under 15 seconds, and the new project is immediately available as the active project.
- **SC-003**: 100% of new repositories contain the complete set of template files (`.github/`, `.specify/`, `.gitignore`) with the generic `copilot-instructions.md` placeholder — no project-specific content leaks into new repositories.
- **SC-004**: All new GitHub Project V2 boards are created with the four default Solune status columns (Backlog, In Progress, In Review, Done) on a best-effort basis; column configuration failure does not prevent project creation or app creation.
- **SC-005**: The owner dropdown correctly lists the user's personal account and all organizations where they have repository creation permissions, with zero false inclusions of organizations where they lack permissions.
- **SC-006**: When repository creation succeeds but project creation fails, the app is still created with repository details, and the user receives a clear notification about the partial failure — zero data loss in partial failure scenarios.
- **SC-007**: All three entry points for creation (New App dialog with "New Repository" mode, standalone "New Repository" button, and "+ New Project" in project selector) are discoverable and functional without requiring documentation or training.
- **SC-008**: App cards and detail views correctly display the repo type badge and clickable links for all three repo types, with links opening the correct GitHub pages.

## Assumptions

- The existing authentication scopes are sufficient for all new GitHub operations (repository creation, project creation, project linking, template file commits). No additional scope changes are needed.
- GitHub's interfaces for repository creation and project management are stable and available. The number of operations per creation (approximately 4) is well within rate limits.
- Template files (`.github/`, `.specify/`, `.gitignore`) are bundled with the application at build time and available at a configurable path at runtime.
- The generic `copilot-instructions.md` is embedded directly within the application to guarantee it is always the generic version regardless of workspace state.
- Users creating repositories in organizations have the necessary permissions (the system filters the owner list to only show permitted organizations).
- The database changes to add new fields and update constraints are backward-compatible with existing app records.
- Repository initialization provides immediate commit capability without requiring additional setup steps.
- The project selector dropdown component already exists and supports extensibility for adding a "+ New Project" option.

## Dependencies

- GitHub repository and project management capabilities (creation, linking, configuration)
- Existing Solune Apps management infrastructure (data storage, models, handlers)
- Existing project selector dropdown component
- Template files available at runtime
