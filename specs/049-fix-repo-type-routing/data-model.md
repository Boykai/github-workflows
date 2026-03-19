# Data Model: Fix Repo-Type Routing

**Feature**: 049-fix-repo-type-routing | **Date**: 2026-03-18

## Entities

### App (existing — no schema changes)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Unique app identifier (kebab-case, 2-64 chars) |
| `display_name` | `str` | Human-readable name |
| `description` | `str` | App description |
| `directory_path` | `str` | Path prefix in the target repo (`apps/{name}`) |
| `associated_pipeline_id` | `str | None` | Pipeline config ID |
| `status` | `AppStatus` | `creating`, `active`, `stopped`, `error` |
| `repo_type` | `RepoType` | `same-repo`, `new-repo`, `external-repo` |
| `external_repo_url` | `str | None` | GitHub URL for external-repo type |
| `github_repo_url` | `str | None` | Created repo URL (new-repo) |
| `github_project_url` | `str | None` | Project V2 URL |
| `github_project_id` | `str | None` | Project V2 GraphQL node ID |
| `parent_issue_number` | `int | None` | Pipeline parent issue number |
| `parent_issue_url` | `str | None` | Pipeline parent issue URL |
| `port` | `int | None` | Assigned port |
| `error_message` | `str | None` | Last error message |
| `created_at` | `str` | ISO 8601 timestamp |
| `updated_at` | `str` | ISO 8601 timestamp |

### AppCreate (existing — validation added)

| Field | Type | Changes |
|-------|------|---------|
| `external_repo_url` | `str | None` | **NEW VALIDATION**: Must match `https://github.com/{owner}/{repo}` when `repo_type == external-repo` |

All other fields unchanged.

## State Transitions

### App Creation by Repo Type

```
AppCreate payload
  │
  ├─ repo_type == same-repo
  │   ├─ Scaffold: default repo (settings.default_repo_owner/name)
  │   ├─ Pipeline project_id: payload.project_id (user-selected)
  │   └─ github_project_id: null (not owned by app)
  │
  ├─ repo_type == new-repo
  │   ├─ Scaffold: new repo (created via create_repository)
  │   ├─ Pipeline project_id: app.github_project_id (created with repo)
  │   └─ github_project_id: populated during repo creation
  │
  └─ repo_type == external-repo
      ├─ Scaffold: external repo (parsed from external_repo_url)
      ├─ Pipeline project_id: app.github_project_id (auto-created)
      └─ github_project_id: populated after auto-creation
```

### Pipeline Launch Project Resolution

```
create_app_endpoint
  │
  ├─ same-repo:     launch_project_id = payload.project_id
  ├─ new-repo:      launch_project_id = app.github_project_id
  └─ external-repo: launch_project_id = app.github_project_id
  │
  └─ if launch_project_id is None → skip pipeline (log warning)
  └─ if launch_project_id is set  → execute_pipeline_launch(project_id=launch_project_id)
```

## Validation Rules

### external_repo_url (FR-005)

- Must be present when `repo_type == external-repo`
- Must match pattern: `https://github.com/{owner}/{repo}` (with optional trailing slash, `.git` suffix)
- Host must be `github.com` (no GitHub Enterprise in this iteration)
- Path must have exactly 2 segments (owner and repo name)
- Validated by `parse_github_url()` utility

### project_id Scoping (FR-006)

- Frontend sends `project_id` only when `repo_type == same-repo`
- Backend ignores `payload.project_id` for `new-repo` and `external-repo` — uses `app.github_project_id` instead

## New Utility

### `parse_github_url(url: str) -> tuple[str, str]`

**Location**: `solune/backend/src/utils.py`

**Behavior**:
- Input: `"https://github.com/org/repo"` → Output: `("org", "repo")`
- Input: `"https://github.com/org/repo.git"` → Output: `("org", "repo")`
- Input: `"https://github.com/org/repo/"` → Output: `("org", "repo")`
- Input: `"https://gitlab.com/org/repo"` → Raises `ValidationError`
- Input: `"not-a-url"` → Raises `ValidationError`
- Input: `"https://github.com/org"` → Raises `ValidationError` (missing repo)

## Relationships

```
App ──── 1:0..1 ──── Project V2 (via github_project_id)
App ──── 1:0..1 ──── Repository (via github_repo_url or external_repo_url)
App ──── 1:0..1 ──── Pipeline (via associated_pipeline_id)
App ──── 1:0..1 ──── Parent Issue (via parent_issue_number)
Project V2 ──── 1:1 ──── Repository (linked via link_project_to_repository)
```
