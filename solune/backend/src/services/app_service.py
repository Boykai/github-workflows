# ^^^ os.path used intentionally — CodeQL recognises os.path.realpath+startswith
# as a path-traversal sanitiser but does not recognise pathlib.Path.is_relative_to.
"""App lifecycle service for Solune multi-app management.

Handles CRUD operations, state transitions, GitHub-based directory scaffolding,
and path validation for applications managed by the platform.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import aiosqlite

from src.config import get_settings
from src.exceptions import ConflictError, NotFoundError, ValidationError
from src.logging_utils import get_logger
from src.models.app import (
    APP_NAME_PATTERN,
    RESERVED_NAMES,
    App,
    AppAssetInventory,
    AppCreate,
    AppStatus,
    AppStatusResponse,
    AppUpdate,
    DeleteAppResult,
    RepoType,
)

if TYPE_CHECKING:
    from src.services.github_projects import GitHubProjectsService

logger = get_logger(__name__)

# Valid state transitions: mapping from current status to set of allowed next statuses
_VALID_TRANSITIONS: dict[AppStatus, set[AppStatus]] = {
    AppStatus.CREATING: {AppStatus.ACTIVE, AppStatus.ERROR},
    AppStatus.ACTIVE: {AppStatus.STOPPED, AppStatus.ERROR},
    AppStatus.STOPPED: {AppStatus.ACTIVE},
    AppStatus.ERROR: {AppStatus.CREATING},
}

# Allowlist of columns that may appear in dynamic UPDATE SET clauses.
_APP_UPDATABLE_COLUMNS = frozenset({"display_name", "description", "associated_pipeline_id"})


def validate_app_name(name: str) -> None:
    """Validate an application name for safety and uniqueness rules.

    Raises ``ValidationError`` on any violation.
    """
    if not re.match(APP_NAME_PATTERN, name):
        raise ValidationError(
            f"Invalid app name '{name}': must be 2-64 lowercase alphanumeric "
            "characters or hyphens, starting and ending with alphanumeric."
        )
    if len(name) < 2 or len(name) > 64:
        raise ValidationError(
            f"Invalid app name '{name}': length must be between 2 and 64 characters."
        )
    if name in RESERVED_NAMES:
        raise ValidationError(f"App name '{name}' is reserved and cannot be used.")
    # Path traversal protection
    if ".." in name or "/" in name or "\\" in name:
        raise ValidationError(f"Invalid app name '{name}': path traversal characters not allowed.")


def _build_scaffold_files(
    name: str,
    display_name: str,
    description: str,
) -> list[dict[str, str]]:
    """Build the list of files for a new application scaffold.

    Returns ``[{"path": "apps/<name>/...", "content": "..."}]``.
    """
    prefix = f"apps/{name}"
    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [
        {
            "path": f"{prefix}/README.md",
            "content": f"# {display_name}\n\n{description}\n\nCreated by the Solune platform.\n",
        },
        {
            "path": f"{prefix}/config.json",
            "content": json.dumps(
                {
                    "name": name,
                    "display_name": display_name,
                    "version": "0.1.0",
                    "created_at": now_str,
                },
                indent=2,
            )
            + "\n",
        },
        {
            "path": f"{prefix}/src/.gitkeep",
            "content": "",
        },
        {
            "path": f"{prefix}/CHANGELOG.md",
            "content": f"# Changelog — {display_name}\n\nAll notable changes will be documented here.\n",
        },
        {
            "path": f"{prefix}/docker-compose.yml",
            "content": f"# Docker Compose for {display_name}\n# Extend or customize as needed.\nservices: {{}}\n",
        },
    ]


def _row_to_app(row: aiosqlite.Row) -> App:
    """Convert a database row to an App model."""
    return App(
        name=row["name"],
        display_name=row["display_name"],
        description=row["description"],
        directory_path=row["directory_path"],
        associated_pipeline_id=row["associated_pipeline_id"],
        status=AppStatus(row["status"]),
        repo_type=row["repo_type"],
        external_repo_url=row["external_repo_url"],
        github_repo_url=row["github_repo_url"],
        github_project_url=row["github_project_url"],
        github_project_id=row["github_project_id"],
        parent_issue_number=row["parent_issue_number"],
        parent_issue_url=row["parent_issue_url"],
        port=row["port"],
        error_message=row["error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------------------------------------------------------------------------
# AI Enhancement
# ---------------------------------------------------------------------------


async def _enhance_app_descriptions(
    display_name: str,
    description: str,
    *,
    access_token: str,
) -> tuple[str, str]:
    """Use AI to generate a short repo description and a rich issue description.

    Returns ``(repo_description, full_description)``.
    Falls back to the original description for both on any error.
    """
    from src.services.ai_agent import get_ai_agent_service

    ai_service = get_ai_agent_service()

    messages = [
        {
            "role": "system",
            "content": (
                "You are a concise technical writer. "
                "The user is creating a new application. Given the app's display name "
                "and their rough description, produce TWO outputs separated by the "
                "exact delimiter '---SPLIT---' on its own line:\n\n"
                "1. A short, single-sentence repository description, max 350 characters. "
                "No markdown.\n"
                "2. A rich Markdown description for a GitHub issue body (3-8 sentences). "
                "Include key goals, scope, or tech notes. Use bullet points if helpful.\n\n"
                "Respond with ONLY the two sections separated by ---SPLIT---. "
                "No fences, no labels, no extra formatting."
            ),
        },
        {
            "role": "user",
            "content": f"App name: {display_name}\n\nUser description: {description or '(none provided)'}",
        },
    ]

    try:
        response = await ai_service._call_completion(
            messages=messages,
            github_token=access_token,
            temperature=0.5,
            max_tokens=600,
        )
        parts = response.split("---SPLIT---", maxsplit=1)
        repo_desc = parts[0].strip()
        full_desc = parts[1].strip() if len(parts) > 1 else repo_desc
        if repo_desc:
            logger.info("AI-enhanced descriptions for app '%s'", display_name)
            # Hard-cap repo description to GitHub limit
            if len(repo_desc) > 350:
                repo_desc = repo_desc[:347] + "..."
            return repo_desc, full_desc
    except Exception as exc:
        logger.warning("AI enhancement failed for app '%s', using original: %s", display_name, exc)

    return description, description


# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------


async def create_app(
    db: aiosqlite.Connection,
    payload: AppCreate,
    *,
    access_token: str,
    github_service: GitHubProjectsService,
) -> App:
    """Create a new application by committing scaffold files to a GitHub branch."""
    if payload.repo_type == RepoType.NEW_REPO:
        return await create_app_with_new_repo(
            db, payload, access_token=access_token, github_service=github_service
        )

    validate_app_name(payload.name)

    # Check for duplicate
    cursor = await db.execute("SELECT name FROM apps WHERE name = ?", (payload.name,))
    if await cursor.fetchone():
        raise ConflictError(f"App '{payload.name}' already exists.")

    if payload.repo_type == RepoType.EXTERNAL_REPO:
        from src.utils import parse_github_url

        owner, repo = parse_github_url(payload.external_repo_url or "")
    else:
        settings = get_settings()
        owner = settings.default_repo_owner
        repo = settings.default_repo_name
        if not owner or not repo:
            raise ValidationError("Default repository not configured (DEFAULT_REPOSITORY).")

    branch_name = payload.branch
    if not branch_name:
        raise ValidationError("Branch is required for same-repo and external-repo app types.")

    # Resolve branch HEAD
    head_oid = await github_service.get_branch_head_oid(
        access_token,
        owner,
        repo,
        branch_name,
    )
    if not head_oid:
        raise ValidationError(
            f"Branch '{branch_name}' not found in {owner}/{repo}. "
            "Ensure the parent issue branch exists before creating an app."
        )

    # Optionally enhance the description with AI
    description = payload.description
    if payload.ai_enhance:
        _repo_desc, description = await _enhance_app_descriptions(
            payload.display_name,
            description,
            access_token=access_token,
        )

    # Build scaffold files and commit to the branch
    files = _build_scaffold_files(payload.name, payload.display_name, description)
    commit_oid = await github_service.commit_files(
        access_token=access_token,
        owner=owner,
        repo=repo,
        branch_name=branch_name,
        head_oid=head_oid,
        files=files,
        message=f"scaffold: create app `{payload.name}`",
    )
    if not commit_oid:
        raise ValidationError(
            f"Failed to commit scaffold files for app '{payload.name}' to branch '{branch_name}'."
        )

    # For external-repo apps, auto-create a Project V2 and link it to the repo.
    github_repo_url: str | None = payload.external_repo_url
    github_project_url: str | None = None
    github_project_id: str | None = None

    if payload.repo_type == RepoType.EXTERNAL_REPO and payload.pipeline_id:
        try:
            project = await github_service.create_project_v2(
                access_token,
                owner=owner,
                title=payload.display_name,
            )
            github_project_id = project.get("id")
            github_project_url = project.get("url")

            if github_project_id:
                try:
                    repo_info = await github_service.get_repository_info(access_token, owner, repo)
                    repository_id = repo_info.get("node_id")
                    if repository_id:
                        await github_service.link_project_to_repository(
                            access_token,
                            project_id=github_project_id,
                            repository_id=repository_id,
                        )
                        await github_service.set_project_default_repository(
                            access_token,
                            project_id=github_project_id,
                            repository_id=repository_id,
                        )
                except Exception as exc:
                    logger.warning("Non-blocking: could not link project to repo: %s", exc)
        except Exception as exc:
            logger.warning(
                "Non-blocking: project creation failed for app '%s': %s",
                payload.name,
                exc,
            )

    directory_path = f"apps/{payload.name}"

    # Insert into database
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    await db.execute(
        """
        INSERT INTO apps (
            name, display_name, description, directory_path,
            associated_pipeline_id, status, repo_type, external_repo_url,
            github_repo_url, github_project_url, github_project_id,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.name,
            payload.display_name,
            description,
            directory_path,
            payload.pipeline_id,
            AppStatus.ACTIVE.value,
            payload.repo_type.value,
            payload.external_repo_url,
            github_repo_url,
            github_project_url,
            github_project_id,
            now,
            now,
        ),
    )
    await db.commit()

    logger.info(
        "Created app '%s' — scaffold committed to %s/%s:%s (oid=%s)",
        payload.name,
        owner,
        repo,
        branch_name,
        commit_oid,
    )

    cursor = await db.execute("SELECT * FROM apps WHERE name = ?", (payload.name,))
    row = await cursor.fetchone()
    if not row:
        raise NotFoundError(f"App '{payload.name}' not found after creation.")
    return _row_to_app(row)


# ---------------------------------------------------------------------------
# New-repo creation orchestration
# ---------------------------------------------------------------------------


async def create_app_with_new_repo(
    db: aiosqlite.Connection,
    payload: AppCreate,
    *,
    access_token: str,
    github_service: GitHubProjectsService,
) -> App:
    """Create a new app by first creating a new GitHub repository.

    Flow: validate → create repo → commit template files → optionally create
    project → link project → insert DB record.

    Error tolerance:
    * Repo creation failure → entire operation fails.
    * Project creation / linking failure after repo → app created with null
      project fields (partial success).
    """
    from src.services.template_files import build_template_files

    validate_app_name(payload.name)

    # Check for duplicate
    cursor = await db.execute("SELECT name FROM apps WHERE name = ?", (payload.name,))
    if await cursor.fetchone():
        raise ConflictError(f"App '{payload.name}' already exists.")

    if not payload.repo_owner:
        raise ValidationError("repo_owner is required when creating a new repository.")

    is_private = payload.repo_visibility != "public"

    # Optionally enhance the description with AI
    description = payload.description
    if payload.ai_enhance:
        repo_description, description = await _enhance_app_descriptions(
            payload.display_name,
            description,
            access_token=access_token,
        )
    else:
        repo_description = description

    # GitHub limits repo descriptions to 350 characters
    if len(repo_description) > 350:
        repo_description = repo_description[:347] + "..."

    # 1. Create the GitHub repository
    repo_data = await github_service.create_repository(
        access_token,
        payload.name,
        owner=payload.repo_owner
        if payload.repo_owner != (await _get_authenticated_username(access_token, github_service))
        else None,
        private=is_private,
        description=repo_description,
        auto_init=True,
    )
    logger.info("Created repository %s", repo_data.get("full_name"))

    repo_owner = repo_data["full_name"].split("/")[0]
    repo_name = repo_data["name"]
    default_branch = repo_data.get("default_branch", "main")

    # 2. Get HEAD OID for template commit
    import asyncio

    head_oid: str | None = None
    last_poll_exc: Exception | None = None
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            info = await github_service.get_repository_info(access_token, repo_owner, repo_name)
            head_oid = info.get("head_oid")
            if head_oid:
                break
        except Exception as exc:
            last_poll_exc = exc
        if attempt < max_attempts - 1:
            await asyncio.sleep(min(1.0 * (1.5**attempt), 4.0))

    if not head_oid:
        detail = f" Last error: {last_poll_exc}" if last_poll_exc else ""
        raise ValidationError(
            f"Repository '{repo_data['full_name']}' was created but default branch "
            f"is not yet available. Please try again.{detail}"
        )

    # 3. Commit template files
    warnings: list[str] = []
    template_files, template_warnings = await build_template_files(
        payload.name, payload.display_name
    )
    warnings.extend(template_warnings)
    if template_files:
        commit_oid = await github_service.commit_files(
            access_token=access_token,
            owner=repo_owner,
            repo=repo_name,
            branch_name=default_branch,
            head_oid=head_oid,
            files=template_files,
            message="scaffold: initial template files",
        )
        if commit_oid:
            logger.info(
                "Committed %d template files to %s", len(template_files), repo_data["full_name"]
            )
        else:
            logger.warning("Failed to commit template files to %s", repo_data["full_name"])

    # 3a. Store Azure credentials as GitHub Secrets (best-effort, synchronous).
    # Failure here is non-fatal: the app is still created, but the user must
    # add AZURE_CLIENT_ID / AZURE_CLIENT_SECRET to the repo secrets manually.
    if payload.azure_client_id and payload.azure_client_secret:
        try:
            await github_service.set_repository_secret(
                access_token,
                repo_owner,
                repo_name,
                "AZURE_CLIENT_ID",
                payload.azure_client_id,
            )
            await github_service.set_repository_secret(
                access_token,
                repo_owner,
                repo_name,
                "AZURE_CLIENT_SECRET",
                payload.azure_client_secret,
            )
        except Exception as exc:
            logger.warning(
                "Failed to store Azure credentials for '%s': %s",
                payload.name,
                exc,
            )
            warnings.append(
                "Azure credentials could not be stored as GitHub Secrets. "
                "Add AZURE_CLIENT_ID and AZURE_CLIENT_SECRET to the repository secrets manually."
            )

    # 4. Optionally create and link a Project V2
    github_repo_url: str | None = repo_data.get("html_url")
    github_project_url: str | None = None
    github_project_id: str | None = None

    if payload.create_project:
        try:
            project = await github_service.create_project_v2(
                access_token,
                owner=repo_owner,
                title=payload.display_name,
            )
            github_project_id = project.get("id")
            github_project_url = project.get("url")

            # Link project to repository and set as default
            if github_project_id and repo_data.get("node_id"):
                try:
                    await github_service.link_project_to_repository(
                        access_token,
                        project_id=github_project_id,
                        repository_id=repo_data["node_id"],
                    )
                    await github_service.set_project_default_repository(
                        access_token,
                        project_id=github_project_id,
                        repository_id=repo_data["node_id"],
                    )
                except Exception as exc:
                    logger.warning("Non-blocking: could not link project to repo: %s", exc)
        except Exception as exc:
            logger.warning(
                "Non-blocking: project creation failed for app '%s': %s",
                payload.name,
                exc,
            )
            # Partial success — app is still created with null project fields.

    # 5. Insert into database
    directory_path = f"apps/{payload.name}"
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    await db.execute(
        """
        INSERT INTO apps (
            name, display_name, description, directory_path,
            associated_pipeline_id, status, repo_type, external_repo_url,
            github_repo_url, github_project_url, github_project_id,
            parent_issue_number, parent_issue_url,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.name,
            payload.display_name,
            description,
            directory_path,
            payload.pipeline_id,
            AppStatus.ACTIVE.value,
            RepoType.NEW_REPO.value,
            None,
            github_repo_url,
            github_project_url,
            github_project_id,
            None,  # parent_issue_number — set later if pipeline is used
            None,  # parent_issue_url — set later if pipeline is used
            now,
            now,
        ),
    )
    await db.commit()

    logger.info(
        "Created app '%s' with new repo %s (project=%s)",
        payload.name,
        repo_data.get("full_name"),
        github_project_url or "none",
    )

    cursor = await db.execute("SELECT * FROM apps WHERE name = ?", (payload.name,))
    row = await cursor.fetchone()
    if not row:
        raise NotFoundError(f"App '{payload.name}' not found after creation.")
    app = _row_to_app(row)
    if warnings:
        app = app.model_copy(update={"warnings": warnings})
    return app


async def _get_authenticated_username(
    access_token: str,
    github_service: GitHubProjectsService,
) -> str:
    """Fetch the authenticated user's login."""
    from typing import cast

    user = cast(dict, await github_service._rest(access_token, "GET", "/user"))
    return user.get("login", "")


async def create_standalone_project(
    access_token: str,
    owner: str,
    title: str,
    github_service: GitHubProjectsService,
    *,
    repo_owner: str | None = None,
    repo_name: str | None = None,
) -> dict:
    """Create a standalone GitHub Project V2 without creating a new repo.

    Args:
        access_token: GitHub OAuth access token.
        owner: Project owner login.
        title: Project title.
        github_service: GitHub API service.
        repo_owner: Optional repository owner to link to.
        repo_name: Optional repository name to link to.

    Returns:
        ``{project_id, project_number, project_url}``
    """
    project = await github_service.create_project_v2(access_token, owner=owner, title=title)

    result = {
        "project_id": project.get("id", ""),
        "project_number": project.get("number"),
        "project_url": project.get("url", ""),
    }

    # Optionally link to an existing repository
    if repo_owner and repo_name and project.get("id"):
        try:
            repo_info = await github_service.get_repository_info(
                access_token, repo_owner, repo_name
            )
            repo_node_id = repo_info.get("repository_id")
            if repo_node_id:
                await github_service.link_project_to_repository(
                    access_token,
                    project_id=project["id"],
                    repository_id=repo_node_id,
                )
        except Exception as exc:
            logger.warning("Non-blocking: could not link project to repo: %s", exc)

    return result


async def list_apps(
    db: aiosqlite.Connection,
    *,
    status_filter: AppStatus | None = None,
) -> list[App]:
    """List all applications, optionally filtered by status."""
    if status_filter:
        cursor = await db.execute(
            "SELECT * FROM apps WHERE status = ? ORDER BY created_at DESC",
            (status_filter.value,),
        )
    else:
        cursor = await db.execute("SELECT * FROM apps ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [_row_to_app(row) for row in rows]


async def get_app(db: aiosqlite.Connection, name: str) -> App:
    """Get an application by name."""
    cursor = await db.execute("SELECT * FROM apps WHERE name = ?", (name,))
    row = await cursor.fetchone()
    if not row:
        raise NotFoundError(f"App '{name}' not found.")
    return _row_to_app(row)


async def update_app(db: aiosqlite.Connection, name: str, payload: AppUpdate) -> App:
    """Update application metadata."""
    app = await get_app(db, name)

    updates: dict[str, str | None] = {}
    if payload.display_name is not None:
        updates["display_name"] = payload.display_name
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.pipeline_id is not None:
        updates["associated_pipeline_id"] = payload.pipeline_id

    if not updates:
        return app

    # Reject unexpected column names (defense-in-depth against SQL injection)
    bad = set(updates) - _APP_UPDATABLE_COLUMNS
    if bad:
        raise ValidationError(
            "Invalid fields in update payload.",
            details={"invalid_fields": sorted(bad)},
        )

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values())
    values.append(name)

    await db.execute(f"UPDATE apps SET {set_clause} WHERE name = ?", values)
    await db.commit()

    return await get_app(db, name)


# ---------------------------------------------------------------------------
# Lifecycle Operations
# ---------------------------------------------------------------------------


async def start_app(db: aiosqlite.Connection, name: str) -> AppStatusResponse:
    """Transition an app to 'active' status."""
    app = await get_app(db, name)

    if app.status == AppStatus.ACTIVE:
        return AppStatusResponse(
            name=app.name, status=app.status, port=app.port, error_message=app.error_message
        )

    if AppStatus.ACTIVE not in _VALID_TRANSITIONS.get(app.status, set()):
        raise ValidationError(
            f"Cannot start app '{name}': invalid transition from '{app.status.value}' to 'active'."
        )

    await db.execute(
        "UPDATE apps SET status = ?, error_message = NULL WHERE name = ?",
        (AppStatus.ACTIVE.value, name),
    )
    await db.commit()

    updated = await get_app(db, name)
    logger.info("Started app '%s'", name)
    return AppStatusResponse(
        name=updated.name,
        status=updated.status,
        port=updated.port,
        error_message=updated.error_message,
    )


async def stop_app(db: aiosqlite.Connection, name: str) -> AppStatusResponse:
    """Transition an app to 'stopped' status."""
    app = await get_app(db, name)

    if app.status == AppStatus.STOPPED:
        return AppStatusResponse(
            name=app.name, status=app.status, port=app.port, error_message=app.error_message
        )

    if AppStatus.STOPPED not in _VALID_TRANSITIONS.get(app.status, set()):
        raise ValidationError(
            f"Cannot stop app '{name}': invalid transition from '{app.status.value}' to 'stopped'."
        )

    await db.execute(
        "UPDATE apps SET status = ?, port = NULL WHERE name = ?",
        (AppStatus.STOPPED.value, name),
    )
    await db.commit()

    updated = await get_app(db, name)
    logger.info("Stopped app '%s'", name)
    return AppStatusResponse(
        name=updated.name,
        status=updated.status,
        port=updated.port,
        error_message=updated.error_message,
    )


async def get_app_assets(
    db: aiosqlite.Connection,
    name: str,
    *,
    access_token: str | None = None,
    github_service: GitHubProjectsService | None = None,
) -> AppAssetInventory:
    """Return an inventory of all GitHub assets associated with an app.

    Fetches sub-issues and branches live from GitHub when credentials are provided.
    """
    app = await get_app(db, name)

    owner: str | None = None
    repo: str | None = None
    github_repo: str | None = None

    # Resolve owner/repo from available URLs
    repo_url = app.github_repo_url or app.external_repo_url
    if repo_url:
        from urllib.parse import urlparse

        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            owner, repo = path_parts[0], path_parts[1]
            github_repo = f"{owner}/{repo}"

    sub_issues: list[int] = []
    branches: list[str] = []

    if access_token and github_service and owner and repo:
        # Fetch sub-issues of the parent issue
        if app.parent_issue_number:
            try:
                timeline = await github_service._rest(
                    access_token,
                    "GET",
                    f"/repos/{owner}/{repo}/issues/{app.parent_issue_number}/timeline",
                    params={"per_page": "100"},
                )
                if isinstance(timeline, list):
                    for event in timeline:
                        if isinstance(event, dict) and event.get("event") == "cross-referenced":
                            source = event.get("source", {}).get("issue", {})
                            if source.get("number"):
                                sub_issues.append(source["number"])
            except Exception as exc:
                logger.debug("Could not fetch sub-issues for app '%s': %s", name, exc)

        # Fetch branches matching the app name pattern
        try:
            branch_prefix = f"app/{app.name}"
            refs = await github_service._rest(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/git/matching-refs/heads/{branch_prefix}",
            )
            if isinstance(refs, list):
                for ref in refs:
                    ref_name = ref.get("ref", "").removeprefix("refs/heads/")
                    if ref_name:
                        branches.append(ref_name)
        except Exception as exc:
            logger.debug("Could not fetch branches for app '%s': %s", name, exc)

    return AppAssetInventory(
        app_name=app.name,
        github_repo=github_repo,
        github_project_id=app.github_project_id,
        parent_issue_number=app.parent_issue_number,
        sub_issues=sub_issues,
        branches=branches,
        has_azure_secrets=False,  # Cannot detect from outside; conservative default
    )


async def delete_app(
    db: aiosqlite.Connection,
    name: str,
    *,
    access_token: str | None = None,
    github_service: GitHubProjectsService | None = None,
    force: bool = False,
) -> DeleteAppResult | None:
    """Delete an application — must be stopped or in error/creating state first.

    When *force* is ``True``, performs a full cleanup of all associated GitHub
    assets (issues, branches, project, repository) before removing the DB record.
    Returns a ``DeleteAppResult`` in force mode, ``None`` otherwise.

    When *access_token* and *github_service* are provided and the app has a
    ``parent_issue_number``, the parent issue is closed (best-effort).
    """
    import asyncio

    app = await get_app(db, name)

    if app.status == AppStatus.ACTIVE:
        raise ValidationError(f"Cannot delete app '{name}': must stop the app first.")

    validate_app_name(app.name)

    owner: str | None = None
    repo: str | None = None

    # Resolve owner/repo from available URLs
    repo_url = app.parent_issue_url or app.github_repo_url or app.external_repo_url
    if repo_url:
        from urllib.parse import urlparse

        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            owner, repo = path_parts[0], path_parts[1]

    if not force:
        # Legacy behaviour: best-effort close parent issue + delete DB record
        if app.parent_issue_number and access_token and github_service and owner and repo:
            try:
                await github_service._rest(
                    access_token,
                    "PATCH",
                    f"/repos/{owner}/{repo}/issues/{app.parent_issue_number}",
                    json={"state": "closed"},
                )
                logger.info(
                    "Closed parent issue #%d in %s/%s",
                    app.parent_issue_number,
                    owner,
                    repo,
                )
            except Exception as exc:
                logger.warning(
                    "Could not close parent issue #%d for app '%s': %s",
                    app.parent_issue_number,
                    name,
                    exc,
                )

        await db.execute("DELETE FROM apps WHERE name = ?", (name,))
        await db.commit()
        logger.info("Deleted app '%s'", name)
        return None

    # ── Force mode: full asset cleanup ──────────────────────────────────
    result = DeleteAppResult(app_name=name)
    RATE_LIMIT_DELAY = 0.2

    if access_token and github_service and owner and repo:
        # 1. Close parent issue and sub-issues
        all_issues: list[int] = []
        if app.parent_issue_number:
            all_issues.append(app.parent_issue_number)
            # Fetch sub-issues
            try:
                timeline = await github_service._rest(
                    access_token,
                    "GET",
                    f"/repos/{owner}/{repo}/issues/{app.parent_issue_number}/timeline",
                    params={"per_page": "100"},
                )
                if isinstance(timeline, list):
                    for event in timeline:
                        if isinstance(event, dict) and event.get("event") == "cross-referenced":
                            source = event.get("source", {}).get("issue", {})
                            if source.get("number"):
                                all_issues.append(source["number"])
            except Exception as exc:
                logger.debug("Could not fetch sub-issues: %s", exc)

        for issue_number in all_issues:
            try:
                await github_service._rest(
                    access_token,
                    "PATCH",
                    f"/repos/{owner}/{repo}/issues/{issue_number}",
                    json={"state": "closed", "state_reason": "not_planned"},
                )
                result.issues_closed += 1
                await asyncio.sleep(RATE_LIMIT_DELAY)
            except Exception as exc:
                result.errors.append(f"Could not close issue #{issue_number}: {exc}")

        # 2. Delete app-related branches
        try:
            branch_prefix = f"app/{app.name}"
            refs = await github_service._rest(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/git/matching-refs/heads/{branch_prefix}",
            )
            if isinstance(refs, list):
                for ref in refs:
                    branch_name = ref.get("ref", "").removeprefix("refs/heads/")
                    if branch_name:
                        try:
                            await github_service.delete_branch(
                                access_token, owner, repo, branch_name
                            )
                            result.branches_deleted += 1
                            await asyncio.sleep(RATE_LIMIT_DELAY)
                        except Exception as exc:
                            result.errors.append(f"Could not delete branch '{branch_name}': {exc}")
        except Exception as exc:
            result.errors.append(f"Could not list branches: {exc}")

        # 3. Delete GitHub project (new-repo apps only)
        if app.github_project_id:
            try:
                await github_service.delete_project_v2(access_token, app.github_project_id)
                result.project_deleted = True
            except Exception as exc:
                result.errors.append(f"Could not delete project: {exc}")

        # 4. Delete GitHub repository (new-repo apps only)
        if app.repo_type == RepoType.NEW_REPO and app.github_repo_url:
            try:
                await github_service.delete_repository(access_token, owner, repo)
                result.repo_deleted = True
            except Exception as exc:
                result.errors.append(f"Could not delete repository: {exc}")

    # 5. Delete database record
    await db.execute("DELETE FROM apps WHERE name = ?", (name,))
    await db.commit()
    result.db_deleted = True
    logger.info(
        "Force-deleted app '%s' (issues=%d, branches=%d, project=%s, repo=%s, errors=%d)",
        name,
        result.issues_closed,
        result.branches_deleted,
        result.project_deleted,
        result.repo_deleted,
        len(result.errors),
    )
    return result


async def get_app_status(db: aiosqlite.Connection, name: str) -> AppStatusResponse:
    """Get the current status of an application."""
    app = await get_app(db, name)
    return AppStatusResponse(
        name=app.name, status=app.status, port=app.port, error_message=app.error_message
    )


def resolve_working_directory(active_app_name: str | None) -> str:
    """Return the working directory path for the active context.

    Returns ``apps/<app-name>`` when an app is selected, or ``solune``
    for the platform context.
    """
    if active_app_name:
        return f"apps/{active_app_name}"
    return "solune"
