# Contract: GraphQL Mutations for GitHub Projects V2

**Feature**: 049-repo-project-creation

This document defines the GraphQL mutation contracts used by the backend to interact with GitHub's API for repository and project management.

---

## Contract 1: Create Project V2

**Mutation**: `createProjectV2`
**Producer**: GitHub GraphQL API
**Consumer**: `ProjectsMixin.create_project_v2()` in `solune/backend/src/services/github_projects/projects.py`

### Mutation

```graphql
mutation CreateProjectV2($ownerId: ID!, $title: String!) {
  createProjectV2(input: {ownerId: $ownerId, title: $title}) {
    projectV2 {
      id
      number
      url
    }
  }
}
```

### Variables

| Variable | Type | Description |
|---|---|---|
| ownerId | ID! | The node ID of the user or organization that will own the project |
| title | String! | The title of the project |

### Response

```json
{
  "data": {
    "createProjectV2": {
      "projectV2": {
        "id": "PVT_kwDOABC123...",
        "number": 42,
        "url": "https://github.com/users/username/projects/42"
      }
    }
  }
}
```

### Contract Rules

- `ownerId` must be the `node_id` (GraphQL global ID) of a user or organization, obtained via `GET /users/{username}` or `GET /orgs/{org}` REST endpoints.
- The authenticated user must have permission to create projects under the specified owner.
- A default Status field with options "Todo", "In Progress", "Done" is automatically created by GitHub.
- The `id` in the response is the project's global node ID, used for all subsequent project operations.

---

## Contract 2: Link Project V2 to Repository

**Mutation**: `linkProjectV2ToRepository`
**Producer**: GitHub GraphQL API
**Consumer**: `ProjectsMixin.link_project_to_repository()` in `solune/backend/src/services/github_projects/projects.py`

### Mutation

```graphql
mutation LinkProjectV2ToRepository($projectId: ID!, $repositoryId: ID!) {
  linkProjectV2ToRepository(input: {projectId: $projectId, repositoryId: $repositoryId}) {
    repository {
      id
    }
  }
}
```

### Variables

| Variable | Type | Description |
|---|---|---|
| projectId | ID! | The node ID of the Project V2 (from `createProjectV2` response) |
| repositoryId | ID! | The node ID of the repository (from repo creation response `node_id`) |

### Response

```json
{
  "data": {
    "linkProjectV2ToRepository": {
      "repository": {
        "id": "R_kgDOABC123..."
      }
    }
  }
}
```

### Contract Rules

- Both `projectId` and `repositoryId` must be valid GraphQL node IDs.
- The authenticated user must have write access to both the project and the repository.
- The mutation is idempotent — calling it with the same IDs again is a no-op.
- After linking, issues and pull requests from the repository can be added to the project.

---

## Contract 3: Update Project V2 Single Select Field (Status Configuration)

**Mutation**: `updateProjectV2SingleSelectField`
**Producer**: GitHub GraphQL API
**Consumer**: `ProjectsMixin.create_project_v2()` (best-effort post-creation step)

### Mutation

```graphql
mutation UpdateProjectV2SingleSelectField(
  $fieldId: ID!,
  $projectId: ID!,
  $options: [ProjectV2SingleSelectFieldOptionInput!]!
) {
  updateProjectV2SingleSelectField(input: {
    fieldId: $fieldId,
    projectId: $projectId,
    singleSelectOptions: $options
  }) {
    projectV2SingleSelectField {
      id
      options {
        id
        name
        color
      }
    }
  }
}
```

### Variables

| Variable | Type | Description |
|---|---|---|
| fieldId | ID! | The node ID of the Status single-select field |
| projectId | ID! | The node ID of the project |
| options | [ProjectV2SingleSelectFieldOptionInput!]! | Array of option definitions |

### Option Definitions (Solune Defaults)

```json
[
  {"name": "Backlog", "color": "GRAY", "description": "Not yet started"},
  {"name": "In Progress", "color": "YELLOW", "description": "Currently being worked on"},
  {"name": "In Review", "color": "ORANGE", "description": "Awaiting review"},
  {"name": "Done", "color": "GREEN", "description": "Completed"}
]
```

### Contract Rules

- The Status field ID must be obtained by querying the project's fields after creation (using `GET_PROJECT_FIELD_QUERY` or similar).
- This mutation replaces ALL options on the field — existing options (Todo, In Progress, Done) are overwritten.
- Failure is non-blocking: if this mutation fails, the project still functions with GitHub's default status options.
- The `color` values must be valid GitHub project field option colors: GRAY, RED, ORANGE, YELLOW, GREEN, BLUE, PINK, PURPLE.

---

## Contract 4: Create Commit on Branch (Existing — Used for Template Files)

**Mutation**: `createCommitOnBranch` (already defined in `graphql.py` as `CREATE_COMMIT_ON_BRANCH_MUTATION`)
**Producer**: GitHub GraphQL API
**Consumer**: `RepositoryMixin.commit_files()` in `solune/backend/src/services/github_projects/repository.py`

### Usage in New Repo Flow

After repository creation with `auto_init=True`, the template files are committed to the default branch using the existing `commit_files()` method. The flow is:

1. Create repository → returns `node_id`, `default_branch`
2. Get branch HEAD OID → `get_branch_head_oid(access_token, owner, repo, default_branch)`
3. Build template files → `build_template_files(repo_name, display_name)` returns `[{"path": "...", "content": "..."}]`
4. Commit files → `commit_files(access_token, owner, repo, default_branch, head_oid, template_files, "scaffold: initial template files")`

### Contract Rules

- The repository must have at least one commit (ensured by `auto_init=True`) for `createCommitOnBranch` to work.
- Template files are base64-encoded before being sent to the API (handled by existing `commit_files()` implementation).
- The `copilot-instructions.md` file in the template set is replaced with the generic version before committing.
