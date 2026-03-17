# Research: New Repository & New Project Creation for Solune

> Researched 2026-03-17 against the live Solune codebase.

---

## Topic 1: GitHub Repository Creation via GitHubKit

### Decision

Use GitHubKit's typed REST methods for repository creation: `github.rest.repos.async_create_for_authenticated_user()` for personal accounts and `github.rest.repos.async_create_in_org()` for organizations. Set `auto_init=True` to ensure the repository has an immediate default branch and initial commit, enabling subsequent file commits without requiring a local clone.

### Rationale

- GitHubKit is already the GitHub client in the codebase (`solune/backend/src/services/github_projects/__init__.py`). Using its typed REST methods provides type safety and consistent error handling.
- The existing `RepositoryMixin` pattern (`repository.py`) uses both `self._rest()` for raw REST calls and `self._graphql()` for GraphQL. Repository creation is best done via REST because GitHub's GraphQL API does not expose a `createRepository` mutation.
- `auto_init=True` creates a default branch with an initial commit (README.md), which is required for `createCommitOnBranch` (the existing commit mechanism in `commit_files()`) to work immediately.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Raw `self._rest("POST", "/user/repos")` | Works but loses type safety; GitHubKit typed methods are available and preferred |
| GraphQL `createRepository` | Does not exist in GitHub's GraphQL API |
| GitHub CLI (`gh repo create`) | External dependency; not available in Docker runtime |
| Create without `auto_init` + push via Git | Requires git binary and clone; unnecessary complexity |

### Implementation Details

```python
# Personal account
response = await github.rest.repos.async_create_for_authenticated_user(
    name=repo_name,
    private=(visibility == "private"),
    auto_init=True,
    description=description,
)

# Organization
response = await github.rest.repos.async_create_in_org(
    org=owner,
    name=repo_name,
    private=(visibility == "private"),
    auto_init=True,
    description=description,
)
```

Returns: `FullRepository` model with `id`, `node_id`, `name`, `full_name`, `html_url`, `default_branch`, `clone_url`.

---

## Topic 2: GitHub Project V2 Creation and Configuration via GraphQL

### Decision

Use the `createProjectV2` GraphQL mutation to create new projects. After creation, attempt best-effort configuration of the Status field options (Backlog, In Progress, In Review, Done) using `updateProjectV2SingleSelectField`. The owner's `node_id` is fetched via GitHubKit's REST API (`github.rest.users.async_get_by_username()` for users, `github.rest.orgs.async_get()` for orgs).

### Rationale

- GitHub Project V2 operations are GraphQL-only — no REST API equivalents exist for creating projects or configuring fields.
- The existing `ProjectsMixin` already uses `self._graphql()` for all project operations, establishing the pattern.
- The `createProjectV2` mutation requires the owner's GraphQL `node_id` (not the REST `id`), which is available from both the REST user/org endpoints (as `node_id` field) and GraphQL queries.
- Status field configuration is best-effort because: (a) the default Status field created by `createProjectV2` has options "Todo/In Progress/Done" which differ from Solune's columns, and (b) the `updateProjectV2SingleSelectField` mutation may fail if the field schema changes.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| REST API for projects | GitHub does not provide REST endpoints for Project V2 |
| Create project without status configuration | Acceptable as fallback, but Solune defaults (Backlog, In Progress, In Review, Done) improve UX |
| Use `addProjectV2ItemById` to create status columns | Incorrect — status columns are field options, not items |

### Implementation Details

```graphql
mutation($ownerId: ID!, $title: String!) {
  createProjectV2(input: {ownerId: $ownerId, title: $title}) {
    projectV2 {
      id
      number
      url
    }
  }
}
```

After creation, query the project's Status field to get its `id` and existing option IDs, then use `updateProjectV2SingleSelectField` to set the desired options:

```graphql
mutation($fieldId: ID!, $projectId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
  updateProjectV2SingleSelectField(input: {
    fieldId: $fieldId,
    projectId: $projectId,
    singleSelectOptions: $options
  }) {
    projectV2SingleSelectField {
      id
    }
  }
}
```

---

## Topic 3: Linking Project V2 to Repository

### Decision

Use the `linkProjectV2ToRepository` GraphQL mutation immediately after project creation. Both the `projectId` (from `createProjectV2` response) and `repositoryId` (from repository creation response `node_id`) are already available in the creation flow.

### Rationale

- This is the only mechanism to associate a Project V2 with a repository in GitHub's API.
- Linking enables the project to appear in the repository's "Projects" tab and allows issues/PRs from the repo to be automatically trackable in the project.
- The mutation is idempotent — calling it twice with the same IDs is a no-op.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Manual linking via GitHub UI | Defeats the purpose of automated creation |
| Skip linking | Reduces the value of creating a project alongside the repo |

### Implementation Details

```graphql
mutation($projectId: ID!, $repositoryId: ID!) {
  linkProjectV2ToRepository(input: {projectId: $projectId, repositoryId: $repositoryId}) {
    repository {
      id
    }
  }
}
```

---

## Topic 4: Template File Bundling and Reading

### Decision

Create a `template_files.py` service module that reads template files from a configurable `TEMPLATE_SOURCE_DIR` environment variable (defaulting to the workspace root for local development). The Dockerfile bundles templates via `COPY .github/ /app/templates/.github/`, `COPY .specify/ /app/templates/.specify/`, and `COPY .gitignore /app/templates/.gitignore`. The generic `copilot-instructions.md` is a hardcoded string constant, not read from disk.

### Rationale

- **Env-var path**: `TEMPLATE_SOURCE_DIR` allows flexibility between local dev (workspace root) and Docker (bundled `/app/templates/`). This follows the existing `get_settings()` pattern in `src/config.py`.
- **Hardcoded copilot-instructions**: The spec explicitly requires that the generic version is "not the project-specific one from the workspace." Hardcoding guarantees this regardless of what exists on disk.
- **Security**: The template reader must validate against path traversal (`..` in paths) and symlinks to prevent reading outside the template directory. This follows the same security pattern used in `validate_app_name()` in `app_service.py`.
- **Caching**: Files are read once at startup and cached in memory. Template files change rarely (only on deployment), so caching avoids repeated filesystem I/O.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Read templates from GitHub API | Adds API calls, latency, and rate limit consumption; templates are local files |
| Embed all files as Python string literals | Unmanageable for 55+ files; filesystem reading is simpler |
| Read copilot-instructions from disk and filter | Risk of leaking project-specific content if file path changes |
| Git submodule for templates | Over-engineering; files are already in the monorepo |

### Implementation Details

```python
GENERIC_COPILOT_INSTRUCTIONS = """# Copilot Instructions

> This file was auto-generated by Solune. Customize it for your project.

## Tech Stack
<!-- TODO: List your primary languages, frameworks, and tools -->

## Coding Conventions
<!-- TODO: Describe naming conventions, code style, and patterns -->

## Testing
<!-- TODO: Describe testing approach, frameworks, and coverage expectations -->

## Deployment
<!-- TODO: Describe deployment process, environments, and CI/CD -->
"""
```

---

## Topic 5: Database Schema Extension for New Repo Type

### Decision

Add a new migration `028_new_repo_support.sql` that adds three columns to the `apps` table (`github_repo_url`, `github_project_url`, `github_project_id`) and recreates the `repo_type` CHECK constraint to include `'new-repo'`. Migration numbering is `028` because `027_done_items_cache.sql` is the latest existing migration.

### Rationale

- SQLite does not support `ALTER TABLE ... ADD CONSTRAINT` or `ALTER TABLE ... MODIFY COLUMN`. The CHECK constraint on `repo_type` must be recreated by creating a new table, copying data, dropping the old table, and renaming.
- The three new columns are nullable TEXT fields — existing rows will have NULL values, which is correct (they don't have new-repo metadata).
- This follows the existing migration pattern seen in `024_apps.sql` and `025_fix_apps_fk.sql`.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Store repo/project URLs in a separate table | Over-normalized for 2-3 fields per app; adds join complexity |
| Use JSON column for extension fields | Loses query/index capability; harder to validate |
| Skip CHECK constraint update | Allows invalid data; violates data integrity |

---

## Topic 6: Owner Listing for Dropdowns

### Decision

Create a `list_available_owners()` method on `RepositoryMixin` that calls `GET /user` (for the authenticated user's personal account) and `GET /user/orgs` (for organizations). Filter organizations to those where the user has `can_create_repositories` permission.

### Rationale

- The `/user` endpoint returns the authenticated user's login and avatar URL.
- The `/user/orgs` endpoint returns all organizations the user belongs to, with role information.
- For org-level permission checking, use `GET /orgs/{org}/memberships/{username}` or check the `permissions` field on org data to determine if the user can create repositories.
- This is a read-only operation that can be cached briefly (30s) on the frontend via TanStack Query.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| GraphQL `viewer` query | REST is simpler for user/org listing; GraphQL doesn't expose `can_create_repositories` directly |
| Only show personal account | Spec requires org support; many users work in organizations |
| Cache on backend | Frontend caching via TanStack Query is sufficient; avoids backend state |

---

## Topic 7: Error Tolerance Strategy

### Decision

Implement a two-tier error tolerance model:
1. **Repository creation failure** → Entire app creation fails. User receives a clear error message.
2. **Project creation/linking failure after repo success** → App is created with repository details but null project fields. User is informed of partial success.
3. **Status column configuration failure** → Non-blocking. Project is created and linked; columns can be configured manually.

### Rationale

- A repository is the primary artifact; without it, the app record has no meaningful GitHub resource.
- A project is secondary — it enhances the workflow but the repository is independently useful.
- Status columns are cosmetic configuration — the project board functions without custom columns.
- This matches the spec's explicit requirement (FR-014, FR-015, FR-016).

### Alternatives Considered

| Alternative | Why not |
|---|---|
| All-or-nothing (rollback repo on project failure) | GitHub doesn't support transactional multi-resource creation; deleting a just-created repo is destructive |
| Retry project creation in background | Adds complexity; user can retry manually from the UI |
| Skip project creation entirely on first failure | Loses the convenience of automatic project setup |

---

## Topic 8: Frontend Repo Type Selector UX Pattern

### Decision

Use a segmented control (radio button group styled as tabs) for the three repo type options: "Same Repo," "New Repository," and "External Repo." Conditional fields appear/disappear based on the selected mode. The existing create dialog is extended in-place rather than replaced.

### Rationale

- The current create dialog (`AppsPage.tsx`) uses a modal with form fields. Adding a segmented control at the top is the minimal change to support three modes.
- Conditional rendering of fields based on `repo_type` keeps the dialog clean — users only see fields relevant to their chosen mode.
- The "Same Repo" mode retains all existing fields and behavior, ensuring backward compatibility.
- The existing dialog accessibility patterns (backdrop, Escape key, focus management) are preserved.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Three separate dialogs | Duplicates shared fields (name, display_name, description); harder to maintain |
| Wizard/stepper UI | Over-engineering for 3-5 fields per mode; adds navigation complexity |
| Dropdown for repo type | Segmented control is more discoverable for 3 options; standard UX pattern |
