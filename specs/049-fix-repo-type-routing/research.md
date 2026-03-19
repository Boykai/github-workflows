# Research: Fix Repo-Type Routing

**Feature**: 049-fix-repo-type-routing | **Date**: 2026-03-18

## R1: External Repo URL Parsing Approach

**Decision**: Use `urllib.parse.urlparse()` (standard library)

**Rationale**: The codebase already uses `urlparse` for URL parsing in `config.py` (L178) and `mcp_store.py` (L38). `app_service.py` itself already contains inline URL parsing at L740 and L829 using `urlparse`. A shared utility function (`parse_github_url`) avoids duplication while following established patterns.

**Alternatives considered**:
- Regex-based parsing: No precedent in the codebase; `urlparse` is cleaner and handles edge cases (trailing slashes, `.git` suffix) more reliably.

**Implementation**: Add `parse_github_url(url: str) -> tuple[str, str]` to `utils.py` that validates the URL is a `github.com` URL, strips `.git` suffix, and returns `(owner, repo)`. Raise `ValidationError` for malformed URLs.

## R2: Project V2 Creation for External Repos

**Decision**: Use existing `create_project_v2()` + `link_project_to_repository()` service methods

**Rationale**: Both methods exist and accept the parameters we need:
- `create_project_v2(access_token, owner, title)` — takes owner login (string), returns `{id, number, url}`
- `link_project_to_repository(access_token, project_id, repository_id)` — takes GraphQL node IDs
- `get_repository_info(access_token, owner, repo)` — returns `repository_id` (node_id) needed for linking

**Alternatives considered**:
- Creating a new service layer for external repo project management: Rejected for YAGNI — the existing methods are sufficient.

**Implementation flow**:
1. Parse URL → extract `owner`, `repo`
2. `create_project_v2(access_token, owner, title)` → `project_id`
3. `get_repository_info(access_token, owner, repo)` → `repository_id` (node_id)
4. `link_project_to_repository(access_token, project_id, repository_id)`
5. Store `project_id` and project URL on the app record

## R3: Scaffold Routing for External Repos

**Decision**: Substitute `owner`/`repo` parameters in existing `get_branch_head_oid()` and `commit_files()` calls

**Rationale**: Both functions accept arbitrary `owner` and `repo` parameters — they use GraphQL with `{owner}/{repo}` internally. No hardcoded repo checks exist. The fix is purely a parameter substitution: extract owner/repo from `external_repo_url` instead of using `settings.default_repo_owner`/`settings.default_repo_name`.

**Alternatives considered**:
- Creating separate scaffold functions for external repos: Rejected — same logic, different parameters.

**Implementation**: In the non-`NEW_REPO` branch of `create_app()`, check if `repo_type == EXTERNAL_REPO` and parse `external_repo_url` to get `owner`/`repo`. Otherwise use settings defaults.

## R4: Pipeline Launch Routing — Project Resolution

**Decision**: Route `project_id` in `create_app_endpoint` based on `repo_type`

**Rationale**: `execute_pipeline_launch()` resolves the target repo via `resolve_repository(access_token, project_id)`. The resolution cascade is: project items → workflow config → default repo. For a freshly created project with no items yet, `resolve_repository` falls through to the default repo — which is wrong.

**Critical insight**: Before launching the pipeline for `new-repo` or `external-repo`, we must ensure the `project_id` resolves to the correct repo. Two approaches:
1. Pre-populate the workflow config with the correct `owner`/`repo` before calling `execute_pipeline_launch`
2. Use `app.github_project_id` (which points to a project linked to the correct repo)

**Decision**: Use approach 2 — for `new-repo`, `app.github_project_id` is already populated after repo creation. For `external-repo`, auto-create the project and store `github_project_id`. Then in `create_app_endpoint`, route based on `repo_type`:
- `same-repo`: use `payload.project_id` (user's selected project)
- `new-repo`: use `app.github_project_id` (ignore `payload.project_id`)
- `external-repo`: use `app.github_project_id` (auto-created)

**Remaining risk**: For freshly linked projects, `resolve_repository()` may not find items. Mitigation: After `link_project_to_repository()`, the project is linked to the repo, so `get_project_repository()` should resolve it. If it doesn't (race condition), `resolve_repository` falls back to workflow config and then default repo. An explicit workflow config pre-set handles this edge case.

## R5: Test Patterns

**Decision**: Follow existing test patterns with `AsyncMock` and `patch()` fixtures

**Rationale**: All backend tests use `pytest` with `AsyncMock` for GitHub service calls. API route tests patch service functions at module level. Service tests mock `github_service` directly.

**Key patterns**:
- `github_service = AsyncMock()` for service mocks
- `@pytest.fixture(autouse=True)` with `patch()` for API tests
- `await mock_db.execute(INSERT INTO apps ...)` for DB setup
- `side_effect=[...]` for simulating failures
