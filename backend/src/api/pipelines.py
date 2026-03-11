"""Pipeline API endpoints — CRUD and launch actions for Agent Pipeline configurations."""

from __future__ import annotations

import logging
import re
from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.auth import get_session_dep
from src.config import get_settings
from src.constants import GITHUB_ISSUE_BODY_MAX_LENGTH, with_blocking_label
from src.exceptions import AppException, AuthorizationError, NotFoundError, ValidationError
from src.models.pipeline import (
    PipelineConfig,
    PipelineConfigCreate,
    PipelineConfigListResponse,
    PipelineConfigUpdate,
    PipelineIssueLaunchRequest,
    ProjectAssignmentBlockingUpdate,
    ProjectPipelineAssignment,
    ProjectPipelineAssignmentUpdate,
)
from src.models.user import UserSession
from src.models.workflow import WorkflowConfiguration, WorkflowResult
from src.services.agent_tracking import append_tracking_to_body
from src.services.database import get_db
from src.services.github_projects import github_projects_service
from src.services.pipelines.service import PipelineService
from src.services.settings_store import get_effective_user_settings
from src.services.workflow_orchestrator import (
    WorkflowContext,
    get_agent_slugs,
    get_pipeline_state,
    get_status_order,
    get_workflow_config,
    get_workflow_orchestrator,
    set_pipeline_state,
    set_workflow_config,
)
from src.services.workflow_orchestrator.config import load_pipeline_as_agent_mappings
from src.utils import resolve_repository, utcnow

logger = logging.getLogger(__name__)
router = APIRouter()
MAX_DERIVED_TITLE_LENGTH = 120
DERIVED_TITLE_TRUNCATE_AT = MAX_DERIVED_TITLE_LENGTH - 3
MARKDOWN_TITLE_PREFIX_RE = re.compile(r"^[>\-*+\d.\s`_~]+")


def _get_service() -> PipelineService:
    """Instantiate PipelineService with the current DB connection."""
    return PipelineService(get_db())


def _normalize_issue_description(issue_description: str) -> str:
    """Trim and validate uploaded issue text."""
    normalized = issue_description.strip()
    if not normalized:
        raise ValidationError("Issue description is required")
    return normalized


def _derive_issue_title(issue_description: str) -> str:
    """Derive a concise issue title from the first heading or opening line."""
    markdown_heading = re.search(r"^\s{0,3}#{1,6}\s+(.+)$", issue_description, flags=re.MULTILINE)
    if markdown_heading:
        candidate = markdown_heading.group(1).strip()
    else:
        candidate = next(
            (line.strip() for line in issue_description.splitlines() if line.strip()),
            "Imported Parent Issue",
        )

    candidate = MARKDOWN_TITLE_PREFIX_RE.sub("", candidate).strip()
    candidate = re.sub(r"\s+", " ", candidate)
    if not candidate:
        candidate = "Imported Parent Issue"
    return (
        candidate[:DERIVED_TITLE_TRUNCATE_AT].rstrip() + "..."
        if len(candidate) > MAX_DERIVED_TITLE_LENGTH
        else candidate
    )


async def _prepare_workflow_config(
    *,
    project_id: str,
    owner: str,
    repo: str,
    pipeline_id: str,
) -> tuple[WorkflowConfiguration, str]:
    """Load or create the workflow config, then override it with the selected pipeline."""
    settings = get_settings()
    config = await get_workflow_config(project_id)
    if config is None:
        config = WorkflowConfiguration(
            project_id=project_id,
            repository_owner=owner,
            repository_name=repo,
            copilot_assignee=settings.default_assignee,
        )
    else:
        config = config.model_copy(deep=True)
        config.repository_owner = owner
        config.repository_name = repo
        if not config.copilot_assignee:
            config.copilot_assignee = settings.default_assignee

    pipeline_result = await load_pipeline_as_agent_mappings(project_id, pipeline_id)
    if pipeline_result is None:
        raise NotFoundError("Selected pipeline config is no longer available")

    config.agent_mappings, pipeline_name, exec_modes = pipeline_result
    config.stage_execution_modes = exec_modes
    await set_workflow_config(project_id, config)
    return config, pipeline_name


async def _load_user_agent_model(session: UserSession) -> str:
    """Load the user's effective agent model for pipeline execution."""
    if not session.github_user_id:
        return ""

    try:
        effective_settings = await get_effective_user_settings(get_db(), session.github_user_id)
        return effective_settings.ai.agent_model or ""
    except Exception as e:
        logger.debug("Failed to load user agent model for pipeline launch: %s", e)
        return ""


# ── List Pipelines ──


@router.get("/{project_id}", response_model=PipelineConfigListResponse)
async def list_pipelines(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    sort: str = "updated_at",
    order: str = "desc",
) -> PipelineConfigListResponse:
    """List all pipeline configurations for a project."""
    service = _get_service()
    return await service.list_pipelines(project_id, sort=sort, order=order)


# ── Seed Presets ──


@router.post("/{project_id}/seed-presets")
async def seed_presets(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Idempotently seed preset pipeline configurations for a project."""
    service = _get_service()
    return await service.seed_presets(project_id)


# ── Assignment ──


@router.get("/{project_id}/assignment", response_model=ProjectPipelineAssignment)
async def get_assignment(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> ProjectPipelineAssignment:
    """Get the current pipeline assignment for a project."""
    service = _get_service()
    return await service.get_assignment(project_id)


@router.put("/{project_id}/assignment", response_model=ProjectPipelineAssignment)
async def set_assignment(
    project_id: str,
    body: ProjectPipelineAssignmentUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> ProjectPipelineAssignment:
    """Set the pipeline assignment for a project."""
    service = _get_service()
    try:
        return await service.set_assignment(project_id, body.pipeline_id)
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc


@router.patch("/{project_id}/assignment", response_model=ProjectPipelineAssignment)
async def set_assignment_blocking(
    project_id: str,
    body: ProjectAssignmentBlockingUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> ProjectPipelineAssignment:
    """Set the project-level blocking override for the assigned pipeline."""
    service = _get_service()
    return await service.set_blocking_override(project_id, body.blocking_override)


@router.post("/{project_id}/launch", response_model=WorkflowResult)
async def launch_pipeline_issue(
    project_id: str,
    body: PipelineIssueLaunchRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> WorkflowResult:
    """Create a project issue from raw issue text and launch the selected agent pipeline."""
    from src.services import blocking_queue as blocking_queue_service
    from src.services.copilot_polling import ensure_polling_started
    from src.services.workflow_orchestrator import PipelineState, find_next_actionable_status

    issue_description = _normalize_issue_description(body.issue_description)
    ctx: WorkflowContext | None = None
    owner, repo = await resolve_repository(session.access_token, project_id)
    service = _get_service()
    pipeline = await service.get_pipeline(project_id, body.pipeline_id)
    if pipeline is None:
        raise NotFoundError("Selected pipeline config is no longer available")

    try:
        config, _pipeline_name = await _prepare_workflow_config(
            project_id=project_id,
            owner=owner,
            repo=repo,
            pipeline_id=body.pipeline_id,
        )

        issue_body = issue_description
        if config.agent_mappings:
            issue_body = append_tracking_to_body(
                issue_body,
                config.agent_mappings,
                get_status_order(config),
            )

        if len(issue_body) > GITHUB_ISSUE_BODY_MAX_LENGTH:
            raise ValidationError(
                f"Issue description is too large for GitHub's {GITHUB_ISSUE_BODY_MAX_LENGTH}-character limit"
            )

        is_blocking = pipeline.blocking
        assignment = await service.get_assignment(project_id)
        if assignment.blocking_override is not None:
            is_blocking = assignment.blocking_override

        issue = await github_projects_service.create_issue(
            access_token=session.access_token,
            owner=owner,
            repo=repo,
            title=_derive_issue_title(issue_description),
            body=issue_body,
            labels=with_blocking_label(["ai-generated"], is_blocking),
        )
        await service.set_assignment(project_id, body.pipeline_id)

        ctx = WorkflowContext(
            session_id=str(session.session_id),
            project_id=project_id,
            access_token=session.access_token,
            repository_owner=owner,
            repository_name=repo,
            selected_pipeline_id=body.pipeline_id,
            config=config,
            user_agent_model=await _load_user_agent_model(session),
        )
        ctx.issue_id = issue["node_id"]
        ctx.issue_number = issue["number"]
        ctx.issue_url = issue["html_url"]

        orchestrator = get_workflow_orchestrator()

        await orchestrator.add_to_project_with_backlog(ctx)

        status_name = config.status_backlog
        agent_sub_issues = await orchestrator.create_all_sub_issues(ctx)
        if agent_sub_issues and ctx.issue_number is not None:
            set_pipeline_state(
                ctx.issue_number,
                PipelineState(
                    issue_number=ctx.issue_number,
                    project_id=project_id,
                    status=status_name,
                    agents=get_agent_slugs(config, status_name),
                    agent_sub_issues=agent_sub_issues,
                    started_at=utcnow(),
                ),
            )

        issue_activated = True
        if ctx.issue_number is not None:
            repo_key = f"{owner}/{repo}"
            _entry, issue_activated = await blocking_queue_service.enqueue_issue(
                repo_key,
                ctx.issue_number,
                project_id,
                is_blocking,
            )
            if not issue_activated:
                await ensure_polling_started(
                    access_token=session.access_token,
                    project_id=project_id,
                    owner=owner,
                    repo=repo,
                    caller="pipeline_issue_launch_blocked",
                )
                return WorkflowResult(
                    success=True,
                    issue_id=ctx.issue_id,
                    issue_number=ctx.issue_number,
                    issue_url=ctx.issue_url,
                    project_item_id=ctx.project_item_id,
                    current_status="pending",
                    message=(
                        f"Issue #{ctx.issue_number} created and queued behind blocking work. "
                        "It will activate automatically."
                    ),
                )

        if not get_agent_slugs(config, status_name):
            next_status = find_next_actionable_status(config, status_name)
            if next_status and ctx.project_item_id:
                await github_projects_service.update_item_status_by_name(
                    access_token=session.access_token,
                    project_id=project_id,
                    item_id=ctx.project_item_id,
                    status_name=next_status,
                )
                status_name = next_status

        await orchestrator.assign_agent_for_status(ctx, status_name, agent_index=0)
        await ensure_polling_started(
            access_token=session.access_token,
            project_id=project_id,
            owner=owner,
            repo=repo,
            caller="pipeline_issue_launch",
        )

        pipeline_state = (
            get_pipeline_state(ctx.issue_number) if ctx.issue_number is not None else None
        )
        if pipeline_state and pipeline_state.error:
            return WorkflowResult(
                success=False,
                issue_id=ctx.issue_id,
                issue_number=ctx.issue_number,
                issue_url=ctx.issue_url,
                project_item_id=ctx.project_item_id,
                current_status=status_name,
                message=(
                    "The parent issue was created, but the first agent could not be assigned "
                    "automatically. Open the issue to continue from the board."
                ),
            )

        return WorkflowResult(
            success=True,
            issue_id=ctx.issue_id,
            issue_number=ctx.issue_number,
            issue_url=ctx.issue_url,
            project_item_id=ctx.project_item_id,
            current_status=status_name,
            message=(
                f"Issue #{ctx.issue_number} created, added to the project, and launched "
                "with the selected pipeline."
            ),
        )
    except AppException:
        raise
    except Exception as e:
        logger.exception("Failed to launch pipeline issue for project %s: %s", project_id, e)
        return WorkflowResult(
            success=False,
            issue_id=ctx.issue_id if ctx is not None else None,
            issue_number=ctx.issue_number if ctx is not None else None,
            issue_url=ctx.issue_url if ctx is not None else None,
            project_item_id=ctx.project_item_id if ctx is not None else None,
            current_status="error",
            message=(
                "We couldn't launch the pipeline from this issue description. Please try again."
            ),
        )


# ── Create Pipeline ──


@router.post("/{project_id}", response_model=PipelineConfig, status_code=201)
async def create_pipeline(
    project_id: str,
    body: PipelineConfigCreate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> PipelineConfig:
    """Create a new pipeline configuration."""
    service = _get_service()
    try:
        return await service.create_pipeline(project_id, body)
    except ValueError as exc:
        raise AppException(str(exc), status_code=409) from exc


# ── Get Pipeline ──


@router.get("/{project_id}/{pipeline_id}", response_model=PipelineConfig)
async def get_pipeline(
    project_id: str,
    pipeline_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> PipelineConfig:
    """Get a single pipeline configuration."""
    service = _get_service()
    pipeline = await service.get_pipeline(project_id, pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline not found")
    return pipeline


# ── Update Pipeline ──


@router.put("/{project_id}/{pipeline_id}", response_model=PipelineConfig)
async def update_pipeline(
    project_id: str,
    pipeline_id: str,
    body: PipelineConfigUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> PipelineConfig:
    """Update an existing pipeline configuration."""
    service = _get_service()
    try:
        updated = await service.update_pipeline(project_id, pipeline_id, body)
    except PermissionError as exc:
        raise AuthorizationError(str(exc)) from exc
    except ValueError as exc:
        raise AppException(str(exc), status_code=409) from exc

    if updated is None:
        raise NotFoundError("Pipeline not found")
    return updated


# ── Delete Pipeline ──


@router.delete("/{project_id}/{pipeline_id}")
async def delete_pipeline(
    project_id: str,
    pipeline_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Delete a pipeline configuration."""
    service = _get_service()
    deleted = await service.delete_pipeline(project_id, pipeline_id)
    if not deleted:
        raise NotFoundError("Pipeline not found")
    return {"success": True, "deleted_id": pipeline_id}
