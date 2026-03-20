"""Pipeline API endpoints — CRUD and launch actions for Agent Pipeline configurations."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends

from src.api.auth import get_session_dep
from src.config import get_settings
from src.constants import GITHUB_ISSUE_BODY_MAX_LENGTH, build_pipeline_label
from src.exceptions import AppException, AuthorizationError, NotFoundError, ValidationError
from src.logging_utils import get_logger
from src.models.pipeline import (
    PipelineConfig,
    PipelineConfigCreate,
    PipelineConfigListResponse,
    PipelineConfigUpdate,
    PipelineIssueLaunchRequest,
    ProjectPipelineAssignment,
    ProjectPipelineAssignmentUpdate,
)
from src.models.pipeline_run import PipelineRunCreate
from src.models.user import UserSession
from src.models.workflow import WorkflowConfiguration, WorkflowResult
from src.services.agent_tracking import append_tracking_to_body
from src.services.database import get_db
from src.services.github_projects import github_projects_service
from src.services.pipelines.service import PipelineService
from src.services.settings_store import get_effective_user_settings
from src.services.workflow_orchestrator import (
    WorkflowContext,
    count_active_pipelines_for_project,
    get_agent_slugs,
    get_pipeline_state,
    get_queued_pipelines_for_project,
    get_status_order,
    get_workflow_config,
    get_workflow_orchestrator,
    set_pipeline_state,
    set_workflow_config,
)
from src.services.workflow_orchestrator.config import load_pipeline_as_agent_mappings
from src.utils import resolve_repository, utcnow

if TYPE_CHECKING:
    from src.services.copilot_polling.pipeline_state_service import PipelineRunService

logger = get_logger(__name__)
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
    markdown_heading = re.search(
        r"^\s{0,3}#{1,6}[ \t]+(\S.*)$", issue_description, flags=re.MULTILINE
    )
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
    pipeline_project_id: str | None = None,
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

    lookup_project = pipeline_project_id or project_id
    pipeline_result = await load_pipeline_as_agent_mappings(lookup_project, pipeline_id)
    if pipeline_result is None:
        raise NotFoundError("Selected pipeline config is no longer available")

    config.agent_mappings, pipeline_name, exec_modes, grp_mappings = pipeline_result
    config.stage_execution_modes = exec_modes
    config.group_mappings = grp_mappings
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


@router.post("/{project_id}/launch", response_model=WorkflowResult)
async def launch_pipeline_issue(
    project_id: str,
    body: PipelineIssueLaunchRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> WorkflowResult:
    """Create a project issue from raw issue text and launch the selected agent pipeline."""
    return await execute_pipeline_launch(
        project_id=project_id,
        issue_description=body.issue_description,
        pipeline_id=body.pipeline_id,
        session=session,
    )


async def execute_pipeline_launch(
    *,
    project_id: str,
    issue_description: str,
    pipeline_id: str,
    session: UserSession,
    pipeline_project_id: str | None = None,
    target_repo: tuple[str, str] | None = None,
) -> WorkflowResult:
    """Core pipeline launch logic — reusable by both the endpoint and app creation.

    Creates a parent issue from the description, adds it to the project,
    creates sub-issues for each pipeline agent, and starts the first agent.

    Args:
        project_id: Target project for issue creation and routing.
        pipeline_project_id: Project where the pipeline config is stored.
            Defaults to *project_id* when not supplied (same-repo case).
        target_repo: Explicit ``(owner, repo)`` for issue creation.  When
            supplied the ``resolve_repository`` fallback is skipped — this
            is required for new-repo / external-repo apps whose project has
            no items yet.
    """
    from src.services.copilot_polling import ensure_polling_started
    from src.services.workflow_orchestrator import PipelineState, find_next_actionable_status

    issue_description = _normalize_issue_description(issue_description)
    ctx: WorkflowContext | None = None
    if target_repo:
        owner, repo = target_repo
    else:
        owner, repo = await resolve_repository(session.access_token, project_id)

    # ── Transcript detection: if the description looks like a transcript,
    #    extract structured requirements via the Transcribe agent. ─────────
    issue_title_override: str | None = None
    from src.services.transcript_detector import detect_transcript

    detection = detect_transcript("pasted_content.txt", issue_description)
    if detection.is_transcript:
        try:
            from src.services.ai_agent import get_ai_agent_service

            ai_service = get_ai_agent_service()
            recommendation = await ai_service.analyze_transcript(
                transcript_content=issue_description,
                project_name=project_id,
                session_id=str(session.session_id),
                github_token=session.access_token,
            )
            issue_title_override = recommendation.title

            # Build a structured body from the recommendation
            reqs = "\n".join(f"- {r}" for r in recommendation.functional_requirements)
            issue_description = (
                f"## {recommendation.title}\n\n"
                f"**User Story:** {recommendation.user_story}\n\n"
                f"**UI/UX Description:** {recommendation.ui_ux_description}\n\n"
                f"**Functional Requirements:**\n{reqs}\n\n"
                f"**Technical Notes:** {recommendation.technical_notes}"
            )
        except Exception as exc:
            logger.warning("Transcript analysis failed, using raw description: %s", exc)

    service = _get_service()
    lookup_project = pipeline_project_id or project_id
    pipeline = await service.get_pipeline(lookup_project, pipeline_id)
    if pipeline is None:
        raise NotFoundError("Selected pipeline config is no longer available")

    try:
        config, _pipeline_name = await _prepare_workflow_config(
            project_id=project_id,
            owner=owner,
            repo=repo,
            pipeline_id=pipeline_id,
            pipeline_project_id=pipeline_project_id,
        )

        issue_body = issue_description
        if config.agent_mappings:
            issue_body = append_tracking_to_body(
                issue_body,
                config.agent_mappings,
                get_status_order(config),
                group_mappings=config.group_mappings or None,
            )

        if len(issue_body) > GITHUB_ISSUE_BODY_MAX_LENGTH:
            raise ValidationError(
                f"Issue description is too large for GitHub's {GITHUB_ISSUE_BODY_MAX_LENGTH}-character limit"
            )

        issue_labels = ["ai-generated"]
        if _pipeline_name:
            issue_labels.append(build_pipeline_label(_pipeline_name))

        issue = await github_projects_service.create_issue(
            access_token=session.access_token,
            owner=owner,
            repo=repo,
            title=issue_title_override or _derive_issue_title(issue_description),
            body=issue_body,
            labels=issue_labels,
        )
        await service.set_assignment(lookup_project, pipeline_id)

        ctx = WorkflowContext(
            session_id=str(session.session_id),
            project_id=project_id,
            access_token=session.access_token,
            repository_owner=owner,
            repository_name=repo,
            selected_pipeline_id=pipeline_id,
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

        # ── Queue mode gate ──
        # If queue mode is ON and another pipeline is already active for this
        # project, mark this pipeline as queued and skip agent assignment.
        from src.services.settings_store import is_queue_mode_enabled

        queue_enabled = await is_queue_mode_enabled(get_db(), project_id)
        active_count = count_active_pipelines_for_project(project_id)
        if queue_enabled and active_count > 0 and ctx.issue_number is not None:
            # Mark pipeline as queued — no agent assigned, no polling started
            queued_state = PipelineState(
                issue_number=ctx.issue_number,
                project_id=project_id,
                status=status_name,
                agents=get_agent_slugs(config, status_name),
                agent_sub_issues=agent_sub_issues or {},
                started_at=utcnow(),
                queued=True,
            )
            set_pipeline_state(ctx.issue_number, queued_state)
            queue_position = len(get_queued_pipelines_for_project(project_id))
            logger.info(
                "Pipeline for issue #%d queued (position #%d) — queue mode ON for project %s",
                ctx.issue_number,
                queue_position,
                project_id,
            )
            return WorkflowResult(
                success=True,
                issue_id=ctx.issue_id,
                issue_number=ctx.issue_number,
                issue_url=ctx.issue_url,
                project_item_id=ctx.project_item_id,
                current_status=status_name,
                message=(
                    f"Pipeline queued — position #{queue_position}. "
                    "It will start automatically when the active pipeline reaches In Review or Done."
                ),
            )

        await orchestrator.assign_agent_for_status(ctx, status_name, agent_index=0)

        # For new-repo / external-repo apps the main polling loop may already
        # be running for the Solune project.  Start a secondary scoped loop
        # that monitors only this pipeline and auto-stops on completion.
        if target_repo and ctx.issue_number is not None:
            from src.services.copilot_polling import ensure_app_pipeline_polling

            await ensure_app_pipeline_polling(
                access_token=session.access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                parent_issue_number=ctx.issue_number,
            )
        else:
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


# ══════════════════════════════════════════════════════════════
# Pipeline Runs — FR-001, FR-002, FR-003
# ══════════════════════════════════════════════════════════════


_run_service_instance: PipelineRunService | None = None


def _get_run_service() -> PipelineRunService:
    """Return a shared PipelineRunService so the asyncio.Lock is effective."""
    global _run_service_instance
    if _run_service_instance is None:
        from src.services.copilot_polling.pipeline_state_service import PipelineRunService

        _run_service_instance = PipelineRunService(get_db())
    return _run_service_instance


@router.post("/{pipeline_id}/runs", status_code=201)
async def create_pipeline_run(
    pipeline_id: str,
    body: PipelineRunCreate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Create and start a new pipeline run (FR-001, FR-016)."""
    # Verify the pipeline exists
    service = _get_service()
    pipeline = await service.get_pipeline(session.selected_project_id or "", pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline configuration not found")

    # Build stage list from pipeline config
    stages = [{"stage_id": stage.id, "group_id": None} for stage in pipeline.stages]

    run_service = _get_run_service()
    run = await run_service.create_run(
        pipeline_config_id=pipeline_id,
        project_id=session.selected_project_id or "",
        trigger=body.trigger if isinstance(body, PipelineRunCreate) else "manual",
        stages=stages,
    )
    return run.model_dump()


@router.get("/{pipeline_id}/runs")
async def list_pipeline_runs(
    pipeline_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List all runs for a pipeline configuration (FR-003).

    No artificial cap on total results.
    """
    # Verify the pipeline belongs to the user's selected project
    service = _get_service()
    pipeline = await service.get_pipeline(session.selected_project_id or "", pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline configuration not found")

    run_service = _get_run_service()
    result = await run_service.list_runs(
        pipeline_config_id=pipeline_id,
        status=status,
        limit=min(limit, 100),
        offset=max(offset, 0),
    )
    return result.model_dump()


@router.get("/{pipeline_id}/runs/{run_id}")
async def get_pipeline_run(
    pipeline_id: str,
    run_id: int,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Get detailed run state with all stages/groups (FR-001, FR-002)."""
    # Verify the pipeline belongs to the user's selected project
    service = _get_service()
    pipeline = await service.get_pipeline(session.selected_project_id or "", pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline configuration not found")

    run_service = _get_run_service()
    run = await run_service.get_run(run_id)
    if run is None or run.pipeline_config_id != pipeline_id:
        raise NotFoundError("Pipeline run not found")
    return run.model_dump()


@router.post("/{pipeline_id}/runs/{run_id}/cancel")
async def cancel_pipeline_run(
    pipeline_id: str,
    run_id: int,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Cancel a running or pending pipeline run."""
    # Verify the pipeline belongs to the user's selected project
    service = _get_service()
    pipeline = await service.get_pipeline(session.selected_project_id or "", pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline configuration not found")

    run_service = _get_run_service()

    # Verify the run exists and belongs to this pipeline
    run = await run_service.get_run(run_id)
    if run is None or run.pipeline_config_id != pipeline_id:
        raise NotFoundError("Pipeline run not found")

    if run.status not in ("pending", "running"):
        raise ValidationError(f"Cannot cancel a run with status '{run.status}'")

    event = await run_service.cancel_run(run_id)
    if event is None:
        raise NotFoundError("Pipeline run not found")

    return {"success": True, "run_id": run_id, "status": "cancelled"}


@router.post("/{pipeline_id}/runs/{run_id}/recover")
async def recover_pipeline_run(
    pipeline_id: str,
    run_id: int,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Rebuild state and resume a pipeline run (FR-002)."""
    # Verify the pipeline belongs to the user's selected project
    service = _get_service()
    pipeline = await service.get_pipeline(session.selected_project_id or "", pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline configuration not found")

    run_service = _get_run_service()

    run = await run_service.get_run(run_id)
    if run is None or run.pipeline_config_id != pipeline_id:
        raise NotFoundError("Pipeline run not found")

    if run.status not in ("running", "failed"):
        raise ValidationError(f"Cannot recover a run with status '{run.status}'")

    # Reset failed stages to pending for re-execution
    for stage in run.stages:
        if stage.status == "failed":
            await run_service.update_stage_status(stage.id, "pending")

    # Set run back to running if it was failed
    if run.status == "failed":
        await run_service.update_run_status(run_id, "running")

    return {"success": True, "run_id": run_id, "status": "running"}


# ── Stage Groups ──


@router.get("/{pipeline_id}/groups")
async def list_stage_groups(
    pipeline_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """List stage groups for a pipeline configuration."""
    run_service = _get_run_service()
    result = await run_service.list_groups(pipeline_id)
    return result.model_dump()


@router.put("/{pipeline_id}/groups")
async def upsert_stage_groups(
    pipeline_id: str,
    body: list[dict],
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Create or update stage groups atomically."""
    # Validate input
    for group in body:
        if not group.get("name"):
            raise ValidationError("Each group must have a name")
        if "order_index" not in group:
            raise ValidationError("Each group must have an order_index")

    run_service = _get_run_service()
    result = await run_service.upsert_groups(pipeline_id, body)
    return result.model_dump()
