"""Shared utility functions for the backend application."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime.

    Single chokepoint replacing deprecated ``datetime.utcnow()`` calls.
    Returns an aware datetime with ``tzinfo=UTC``.
    """
    return datetime.now(UTC)


async def resolve_repository(access_token: str, project_id: str) -> tuple[str, str]:
    """Resolve repository owner and name for a project using 3-step fallback.

    Lookup order:
    1. Project items (via GitHub Projects GraphQL API)
    2. Workflow configuration (in-memory/DB)
    3. Default repository from app settings (.env)

    Args:
        access_token: GitHub access token.
        project_id: GitHub Project node ID.

    Returns:
        ``(owner, repo_name)`` tuple.

    Raises:
        src.exceptions.ValidationError: If no repository can be resolved.
    """
    from src.exceptions import ValidationError
    from src.services.github_projects import github_projects_service
    from src.services.workflow_orchestrator import get_workflow_config

    # 1. Try project items
    repo_info = await github_projects_service.get_project_repository(access_token, project_id)
    if repo_info:
        return repo_info

    # 2. Try workflow config
    config = await get_workflow_config(project_id)
    if config and config.repository_owner and config.repository_name:
        return config.repository_owner, config.repository_name

    # 3. Fall back to default repository from settings
    from src.config import get_settings

    settings = get_settings()
    if settings.default_repo_owner and settings.default_repo_name:
        return settings.default_repo_owner, settings.default_repo_name

    raise ValidationError(
        "No repository found for this project. Configure DEFAULT_REPOSITORY in .env "
        "or ensure the project has at least one linked issue."
    )
