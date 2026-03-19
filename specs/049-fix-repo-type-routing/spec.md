# Feature Specification: Fix App Creation to Respect Repo Type for Issue/Pipeline Placement

**Feature Branch**: `049-fix-repo-type-routing`  
**Created**: 2025-03-18  
**Status**: Draft  
**Input**: User description: "Fix App Creation to Respect Repo Type for Issue/Pipeline Placement"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Same-Repo App Pipeline Launch (Priority: P1)

A user creates an app with repo type `same-repo` and selects a pipeline. The system creates a parent GitHub issue and sub-issues in the user's selected project within Solune's default repository. This is the most common workflow and must continue to work correctly.

**Why this priority**: Same-repo is the default repo type and the most frequently used path. Any regression here affects all existing users.

**Independent Test**: Create an app with `same-repo`, select a pipeline and project, verify parent issue and sub-issues appear in the selected project's repository.

**Acceptance Scenarios**:

1. **Given** a user selects repo type `same-repo` and chooses a project during app creation, **When** the app is created with a pipeline, **Then** the parent issue and sub-issues are created in the repository linked to the user's selected project.
2. **Given** a user selects repo type `same-repo` and provides a `project_id`, **When** pipeline launch executes, **Then** the system resolves the target repository from the user-supplied `project_id`.
3. **Given** a user selects repo type `same-repo` without selecting a pipeline, **When** the app is created, **Then** the app is created successfully with no pipeline launch and no issues created.

---

### User Story 2 — New-Repo App Pipeline Launch (Priority: P1)

A user creates an app with repo type `new-repo`. The system creates a new GitHub repository with its own Project V2. When a pipeline is selected, parent issue and sub-issues must be created in the **new repository's project**, not in the user's selected project from the Solune workspace.

**Why this priority**: New-repo apps already create a project (`app.github_project_id`), but pipeline launch currently ignores it in favor of the user's selected project. This is a critical data-routing bug — issues land in the wrong repo.

**Independent Test**: Create an app with `new-repo` and a pipeline, verify parent issue and sub-issues appear in the newly created repository, not in Solune's default repo.

**Acceptance Scenarios**:

1. **Given** a user creates a `new-repo` app with a pipeline, **When** pipeline launch executes, **Then** the parent issue and sub-issues are created in the new repository's own project (stored as `app.github_project_id`).
2. **Given** a `new-repo` app has `app.github_project_id` populated after repo creation, **When** the pipeline launches, **Then** the system uses `app.github_project_id` and ignores any user-supplied `project_id`.
3. **Given** a user creates a `new-repo` app without selecting a pipeline, **When** the app is created, **Then** the new repo and project are created but no issues are generated.

---

### User Story 3 — External-Repo App Scaffold Placement (Priority: P1)

A user creates an app with repo type `external-repo` and provides an external repository URL. The system must scaffold template files (e.g., README, config) into the **external repository**, not Solune's default repository.

**Why this priority**: This is a correctness bug — scaffold files currently go to the wrong repository entirely, making the feature non-functional. External-repo support is broken without this fix.

**Independent Test**: Create an app with `external-repo` and a valid external repo URL, verify scaffold files are committed to the external repository.

**Acceptance Scenarios**:

1. **Given** a user creates an `external-repo` app with a valid `external_repo_url`, **When** the app is created, **Then** the scaffold files are committed to the external repository (parsed from the URL).
2. **Given** a user provides `external_repo_url` as `https://github.com/org/repo`, **When** the system scaffolds the app, **Then** it resolves `owner=org` and `repo=repo` from the URL and commits files there.
3. **Given** a user provides an `external_repo_url` that the authenticated user does not have write access to, **When** the system attempts to scaffold, **Then** an appropriate error is returned indicating insufficient permissions.

---

### User Story 4 — External-Repo App Auto-Create Project and Pipeline Launch (Priority: P2)

When a user creates an `external-repo` app with a pipeline, the system must auto-create a GitHub Project V2 on the external repository (if none exists), link it, and use it for pipeline issue creation.

**Why this priority**: Pipeline launch is silently skipped for external-repo apps because no project exists. While the scaffold fix (P1) is the higher priority, pipelines are a key feature and auto-creating the project makes external-repo fully functional.

**Independent Test**: Create an `external-repo` app with a pipeline, verify a Project V2 is created on the external repo and parent issue + sub-issues appear there.

**Acceptance Scenarios**:

1. **Given** a user creates an `external-repo` app with a pipeline, **When** the external repo has no linked Project V2, **Then** the system creates a new Project V2 on the external repo and links it to that repository.
2. **Given** a Project V2 is auto-created for the external repo, **When** pipeline launch executes, **Then** the parent issue and sub-issues are created in the external repository using the newly created project.
3. **Given** a Project V2 is auto-created, **When** the app record is persisted, **Then** `app.github_project_id` and `app.github_project_url` are stored in the database.
4. **Given** the external repo already has a Project V2 linked, **When** the user creates an app, **Then** the existing project is reused and no duplicate is created.

---

### User Story 5 — Frontend Project ID Scoping (Priority: P2)

The app creation dialog must only send a `project_id` in the payload when the repo type is `same-repo`. For `new-repo` and `external-repo`, the backend determines the correct project from the app's own data.

**Why this priority**: Sending a `project_id` for non-same-repo types causes the backend to use the wrong project. This fix prevents the frontend from overriding the backend's correct routing logic.

**Independent Test**: Inspect the API payload when creating apps of each repo type. Verify `project_id` is present only for `same-repo`.

**Acceptance Scenarios**:

1. **Given** a user creates an app with repo type `same-repo`, **When** the creation payload is submitted, **Then** `project_id` is included in the request body.
2. **Given** a user creates an app with repo type `new-repo`, **When** the creation payload is submitted, **Then** `project_id` is omitted from the request body.
3. **Given** a user creates an app with repo type `external-repo`, **When** the creation payload is submitted, **Then** `project_id` is omitted from the request body.

---

### Edge Cases

- What happens when an `external_repo_url` is malformed or does not match the expected GitHub URL pattern? The system must reject it with a clear validation error.
- What happens when the authenticated user has read-only access to the external repository? The scaffold commit must fail gracefully with a permission error, and no partial state should be persisted.
- What happens when project auto-creation fails (e.g., GitHub API rate limit, network error)? The app record should still be created, but `github_project_id` should be `null` and pipeline launch should be skipped with a logged warning.
- What happens when a `new-repo` app's `github_project_id` is unexpectedly `null` (e.g., project creation failed during repo setup)? Pipeline launch should be skipped with a logged warning rather than silently failing or crashing.
- What happens when a user provides an `external_repo_url` pointing to a repository in a different GitHub instance (e.g., GitHub Enterprise)? The system should only support `github.com` URLs in this iteration and reject others with a validation error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST route pipeline launch issues (parent + sub-issues) to the repository determined by the app's `repo_type`:
  - `same-repo`: use the user-supplied `project_id` to resolve the target repo
  - `new-repo`: use `app.github_project_id` (created during repo setup)
  - `external-repo`: use `app.github_project_id` (auto-created or pre-existing)
- **FR-002**: System MUST parse `external_repo_url` to extract `owner` and `repo` and use them for all scaffold operations (branch head lookup, file commits) instead of Solune's default repository.
- **FR-003**: System MUST auto-create a GitHub Project V2 for `external-repo` apps if no project is linked to the external repository, then link the project to that repository.
- **FR-004**: System MUST store `github_project_id` and `github_project_url` on the app database record after auto-creating a project for an external repo.
- **FR-005**: System MUST validate `external_repo_url` format before attempting any operations. Only `github.com` URLs in the format `https://github.com/{owner}/{repo}` are accepted.
- **FR-006**: System MUST NOT send `project_id` in the app creation payload from the frontend when repo type is `new-repo` or `external-repo`.
- **FR-007**: System MUST skip pipeline launch gracefully (with a logged warning) when `github_project_id` is `null` for `new-repo` or `external-repo` apps.
- **FR-008**: System MUST return a clear error when scaffold operations fail due to insufficient permissions on the external repository.
- **FR-009**: System MUST NOT modify existing `same-repo` behavior — the current flow for same-repo apps must remain unchanged.

### Key Entities

- **App**: Represents a user-created application. Key attributes: `repo_type` (same-repo, new-repo, external-repo), `external_repo_url`, `github_project_id`, `github_project_url`, `pipeline_id`.
- **Project V2**: A GitHub Projects (V2) board linked to a repository. Used to organize issues created by the pipeline launch.
- **Pipeline**: A sequence of agent stages that produces parent issues and sub-issues in a target repository.
- **Repository**: The GitHub repository where scaffold files and issues are placed. Determined by `repo_type`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of `new-repo` app pipeline launches create issues in the new repository (not Solune's default repo).
- **SC-002**: 100% of `external-repo` app scaffold operations commit files to the external repository (not Solune's default repo).
- **SC-003**: 100% of `external-repo` app pipeline launches create issues in the external repository's project.
- **SC-004**: All `same-repo` app workflows continue to function identically to pre-fix behavior (zero regressions).
- **SC-005**: External-repo apps with no pre-existing project have a Project V2 auto-created and linked within the same creation flow.
- **SC-006**: The frontend only includes `project_id` in the payload for `same-repo` apps — verified across all three repo types.
- **SC-007**: Invalid or inaccessible `external_repo_url` values produce user-visible error messages within the creation flow (no silent failures).

## Assumptions

- The authenticated user has write access to any external repository they provide via `external_repo_url`. If they do not, the system will surface a permissions error.
- `github.com` is the only supported GitHub host. GitHub Enterprise Server URLs are out of scope for this iteration.
- The existing `create_project_v2()` and `link_project_to_repository()` service methods work correctly and do not need modification.
- The `resolve_repository()` utility correctly resolves the target repo from a `project_id`. The fix is about ensuring the correct `project_id` is passed, not about changing resolution logic.
- The external repo URL format follows the standard `https://github.com/{owner}/{repo}` pattern. SSH URLs and other formats are not supported.

## Scope Boundaries

**In scope**:
- Fixing pipeline launch routing for all three repo types
- Fixing external-repo scaffold to commit to the correct repository
- Auto-creating Project V2 for external repos
- Frontend payload scoping by repo type
- Unit and integration tests for all fixed paths

**Out of scope**:
- Changing how `new-repo` creates its repository or project (already working correctly)
- Adding support for GitHub Enterprise Server URLs
- Adding support for SSH-style git URLs
- UI changes beyond the `project_id` payload adjustment
- Modifying the pipeline execution logic itself (stages, agents, etc.)
- Retroactively fixing apps created before this fix
