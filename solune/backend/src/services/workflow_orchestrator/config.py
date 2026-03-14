"""Workflow configuration load/persist/defaults and transition audit logging."""

import json
from dataclasses import dataclass, field

import aiosqlite

from src.logging_utils import get_logger
from src.models.agent import AgentAssignment
from src.models.workflow import (
    ExecutionGroupMapping,
    WorkflowConfiguration,
    WorkflowTransition,
)
from src.utils import BoundedDict, utcnow


@dataclass
class PipelineResolutionResult:
    """Result of pipeline resolution for issue creation.

    Carries both the resolved agent mappings and metadata about which
    tier in the fallback chain was used — used by ``confirm_proposal``
    to populate the response and for logging/observability.
    """

    agent_mappings: dict[str, list[AgentAssignment]] = field(default_factory=dict)
    source: str = "default"  # "pipeline" | "user" | "default"
    pipeline_name: str | None = None
    pipeline_id: str | None = None
    stage_execution_modes: dict[str, str] = field(default_factory=dict)
    group_mappings: dict[str, list[ExecutionGroupMapping]] = field(default_factory=dict)


logger = get_logger(__name__)

# In-memory storage for workflow transitions (audit log)
_transitions: list[WorkflowTransition] = []

# In-memory storage for workflow configurations (per project)
_workflow_configs: BoundedDict[str, WorkflowConfiguration] = BoundedDict(maxlen=100)


async def get_workflow_config(project_id: str) -> WorkflowConfiguration | None:
    """Get workflow configuration for a project.

    Checks in-memory cache first, then falls back to SQLite project_settings.
    """
    cached = _workflow_configs.get(project_id)
    if cached is not None:
        return cached

    # Fall back to SQLite
    config = await _load_workflow_config_from_db(project_id)
    if config is not None:
        _workflow_configs[project_id] = config
    return config


async def set_workflow_config(
    project_id: str,
    config: WorkflowConfiguration,
) -> None:
    """Set workflow configuration for a project.

    Updates in-memory cache and persists to SQLite project_settings.
    The config is always stored under the canonical ``__workflow__`` user.
    """
    _workflow_configs[project_id] = config
    await _persist_workflow_config_to_db(project_id, config)


def _parse_agent_mappings(raw_mappings: dict) -> dict[str, list[AgentAssignment]]:
    """Convert raw JSON agent mappings to AgentAssignment objects."""
    agent_mappings: dict[str, list[AgentAssignment]] = {}
    for status, agents in raw_mappings.items():
        agent_mappings[status] = [
            AgentAssignment(**a) if isinstance(a, dict) else AgentAssignment(slug=str(a))
            for a in agents
        ]
    return agent_mappings


def deduplicate_agent_mappings(
    mappings: dict[str, list],
) -> dict[str, list]:
    """Merge case-variant status keys in agent_mappings.

    GitHub project column names may differ in casing from the backend
    defaults (e.g. ``"In progress"`` vs ``"In Progress"``).  When both
    variants end up in agent_mappings the empty default-cased key can
    shadow the populated board-cased key at lookup time.

    This helper keeps one entry per case-insensitive status name.  When
    duplicates exist the **non-empty** list wins; if both are non-empty
    the first encountered value wins.
    """
    seen: dict[str, str] = {}  # lowercase → chosen key
    result: dict[str, list] = {}
    for key, agents in mappings.items():
        lower = key.lower()
        if lower not in seen:
            seen[lower] = key
            result[key] = agents
        else:
            existing_key = seen[lower]
            # Keep the entry that has agents; prefer the first if both have agents
            if not result[existing_key] and agents:
                del result[existing_key]
                seen[lower] = key
                result[key] = agents
            # else keep existing (it already has agents, or both are empty)
    return result


async def load_user_agent_mappings(
    github_user_id: str, project_id: str
) -> dict[str, list[AgentAssignment]] | None:
    """Load user-specific agent pipeline mappings from project_settings.

    Users configure their agent pipeline via the Settings UI, which stores
    mappings under their own ``github_user_id``.  This helper retrieves those
    user-specific mappings so they can be applied during workflow orchestration.
    """
    try:
        from src.config import get_settings

        db_path = get_settings().database_path
    except Exception:
        return None

    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT agent_pipeline_mappings FROM project_settings "
                "WHERE github_user_id = ? AND project_id = ? "
                "AND agent_pipeline_mappings IS NOT NULL LIMIT 1",
                (github_user_id, project_id),
            )
            row = await cursor.fetchone()
            if row and row["agent_pipeline_mappings"]:
                raw_mappings = json.loads(row["agent_pipeline_mappings"])
                logger.info(
                    "Loaded user-specific agent mappings for user=%s project=%s",
                    github_user_id,
                    project_id,
                )
                return _parse_agent_mappings(raw_mappings)
    except Exception:
        logger.warning(
            "Failed to load user agent mappings for user=%s project=%s",
            github_user_id,
            project_id,
            exc_info=True,
        )
    return None


async def _load_workflow_config_from_db(project_id: str) -> WorkflowConfiguration | None:
    """Load workflow configuration from SQLite project_settings table.

    Uses async aiosqlite to avoid blocking the event loop.
    """
    try:
        from src.config import get_settings

        db_path = get_settings().database_path
    except Exception:
        return None

    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row

            # Try loading from the workflow_config column first (full config).
            # Filter by canonical user '__workflow__' to avoid nondeterministic
            # results when multiple users have rows for the same project.
            cursor = await db.execute(
                "SELECT workflow_config FROM project_settings WHERE github_user_id = '__workflow__' AND project_id = ? AND workflow_config IS NOT NULL LIMIT 1",
                (project_id,),
            )
            row = await cursor.fetchone()
            if row and row["workflow_config"]:
                raw = json.loads(row["workflow_config"])
                logger.info(
                    "Loaded workflow config from DB (workflow_config column) for project %s",
                    project_id,
                )
                return WorkflowConfiguration(**raw)

            # Fall back to agent_pipeline_mappings from __workflow__ user
            cursor = await db.execute(
                "SELECT agent_pipeline_mappings FROM project_settings WHERE github_user_id = '__workflow__' AND project_id = ? AND agent_pipeline_mappings IS NOT NULL LIMIT 1",
                (project_id,),
            )
            row = await cursor.fetchone()

            if row and row["agent_pipeline_mappings"]:
                raw_mappings = json.loads(row["agent_pipeline_mappings"])
                agent_mappings = _parse_agent_mappings(raw_mappings)
                logger.info(
                    "Loaded workflow config from DB (agent_pipeline_mappings column) for project %s",
                    project_id,
                )
                config = WorkflowConfiguration(
                    project_id=project_id,
                    repository_owner="",
                    repository_name="",
                    agent_mappings=agent_mappings,
                )
                # Backfill: persist the full config to workflow_config column
                # so subsequent loads use the preferred path.
                try:
                    await _persist_workflow_config_to_db(project_id, config)
                    logger.info("Backfilled workflow_config column for project %s", project_id)
                except Exception as e:
                    logger.debug("Suppressed error: %s", e)
                return config

            # Fallback: if no __workflow__ row exists, check for any user's
            # agent_pipeline_mappings for this project.  This covers the case
            # where a user configured their pipeline via the Settings UI but
            # the canonical row was never created (the original bug).
            cursor = await db.execute(
                "SELECT agent_pipeline_mappings FROM project_settings "
                "WHERE project_id = ? AND agent_pipeline_mappings IS NOT NULL "
                "AND github_user_id != '__workflow__' LIMIT 1",
                (project_id,),
            )
            row = await cursor.fetchone()
            if row and row["agent_pipeline_mappings"]:
                raw_mappings = json.loads(row["agent_pipeline_mappings"])
                agent_mappings = _parse_agent_mappings(raw_mappings)
                logger.info(
                    "Loaded workflow config from DB (user fallback) for project %s",
                    project_id,
                )
                config = WorkflowConfiguration(
                    project_id=project_id,
                    repository_owner="",
                    repository_name="",
                    agent_mappings=agent_mappings,
                )
                # Backfill to canonical __workflow__ row
                try:
                    await _persist_workflow_config_to_db(project_id, config)
                    logger.info(
                        "Backfilled workflow_config from user row for project %s",
                        project_id,
                    )
                except Exception as e:
                    logger.debug("Suppressed error: %s", e)
                return config

            return None
    except Exception:
        logger.warning(
            "Failed to load workflow config from DB for project %s", project_id, exc_info=True
        )
        return None


async def _persist_workflow_config_to_db(
    project_id: str,
    config: WorkflowConfiguration,
) -> None:
    """Persist workflow configuration to SQLite project_settings table.

    Uses async aiosqlite to avoid blocking the event loop.
    """
    try:
        from src.config import get_settings

        db_path = get_settings().database_path
    except Exception:
        return

    # Deduplicate case-variant status keys before serialising
    deduped = deduplicate_agent_mappings(config.agent_mappings)

    # Serialize config — use deduped mappings
    config.agent_mappings = deduped  # type: ignore[assignment]
    config_json = config.model_dump_json()
    agent_mappings_json = json.dumps(
        {
            status: [
                a.model_dump(mode="json") if hasattr(a, "model_dump") else {"slug": str(a)}
                for a in agents
            ]
            for status, agents in deduped.items()
        }
    )
    now = utcnow().isoformat()

    # Always use canonical '__workflow__' user to keep config per-project,
    # not per-user, ensuring deterministic load/persist pairing.
    user_id = "__workflow__"

    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA busy_timeout=5000;")

            cursor = await db.execute(
                "SELECT 1 FROM project_settings WHERE github_user_id = ? AND project_id = ?",
                (user_id, project_id),
            )
            existing = await cursor.fetchone()

            if existing:
                await db.execute(
                    "UPDATE project_settings SET agent_pipeline_mappings = ?, workflow_config = ?, updated_at = ? "
                    "WHERE github_user_id = ? AND project_id = ?",
                    (agent_mappings_json, config_json, now, user_id, project_id),
                )
            else:
                await db.execute(
                    "INSERT INTO project_settings (github_user_id, project_id, agent_pipeline_mappings, workflow_config, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, project_id, agent_mappings_json, config_json, now),
                )
            await db.commit()
        logger.info("Persisted workflow config to DB for project %s (user=%s)", project_id, user_id)
    except Exception:
        logger.warning(
            "Failed to persist workflow config to DB for project %s", project_id, exc_info=True
        )


async def load_pipeline_as_agent_mappings(
    project_id: str,
    pipeline_id: str,
) -> (
    tuple[
        dict[str, list[AgentAssignment]],
        str,
        dict[str, str],
        dict[str, list[ExecutionGroupMapping]],
    ]
    | None
):
    """Load a pipeline config and convert its stages to agent_mappings.

    Returns ``(agent_mappings, pipeline_name, stage_execution_modes,
    group_mappings)`` or ``None`` if the pipeline does not exist (e.g. was
    deleted).
    """
    try:
        from src.services.database import get_db
        from src.services.pipelines.service import PipelineService

        db = get_db()
        service = PipelineService(db)
        config = await service.get_pipeline(project_id, pipeline_id)
        if config is None:
            return None

        agent_mappings: dict[str, list[AgentAssignment]] = {}
        stage_execution_modes: dict[str, str] = {}
        group_mappings: dict[str, list[ExecutionGroupMapping]] = {}
        for stage in sorted(config.stages, key=lambda s: s.order):
            # Build group_mappings from stage.groups when available
            if stage.groups:
                groups_for_stage: list[ExecutionGroupMapping] = []
                flat_agents: list[AgentAssignment] = []
                for group in sorted(stage.groups, key=lambda g: g.order):
                    group_agents = [
                        AgentAssignment(
                            slug=node.agent_slug,
                            display_name=node.agent_display_name or None,
                            config={
                                "model_id": node.model_id,
                                "model_name": node.model_name,
                            }
                            if node.model_id
                            else None,
                        )
                        for node in group.agents
                    ]
                    groups_for_stage.append(
                        ExecutionGroupMapping(
                            group_id=group.id,
                            order=group.order,
                            execution_mode=group.execution_mode,
                            agents=group_agents,
                        )
                    )
                    flat_agents.extend(group_agents)
                group_mappings[stage.name] = groups_for_stage
                agent_mappings[stage.name] = flat_agents
            else:
                # Legacy fallback: use flat stage.agents
                agent_mappings[stage.name] = [
                    AgentAssignment(
                        slug=node.agent_slug,
                        display_name=node.agent_display_name or None,
                        config={
                            "model_id": node.model_id,
                            "model_name": node.model_name,
                        }
                        if node.model_id
                        else None,
                    )
                    for node in stage.agents
                ]
            stage_execution_modes[stage.name] = getattr(stage, "execution_mode", "sequential")

        return agent_mappings, config.name, stage_execution_modes, group_mappings
    except Exception:
        logger.warning(
            "Failed to load pipeline %s for project %s",
            pipeline_id,
            project_id,
            exc_info=True,
        )
        return None


async def resolve_project_pipeline_mappings(
    project_id: str,
    github_user_id: str,
) -> PipelineResolutionResult:
    """Resolve agent pipeline mappings for issue creation.

    Three-tier fallback:
    1. Project-level pipeline assignment (``assigned_pipeline_id``)
    2. User-specific agent mappings (``agent_pipeline_mappings``)
    3. System default agent mappings

    Returns a `PipelineResolutionResult` with the resolved mappings
    and metadata about which resolution tier was used.
    """
    from src.constants import AGENT_DISPLAY_NAMES, DEFAULT_AGENT_MAPPINGS

    # ── Tier 1: Project-level pipeline assignment ────────────────────
    try:
        from src.config import get_settings

        db_path = get_settings().database_path
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT assigned_pipeline_id FROM project_settings "
                "WHERE github_user_id = ? AND project_id = ? LIMIT 1",
                ("__workflow__", project_id),
            )
            row = await cursor.fetchone()
            assigned_id = (row["assigned_pipeline_id"] or "") if row else ""

        if assigned_id:
            result = await load_pipeline_as_agent_mappings(project_id, assigned_id)
            if result is not None:
                mappings, pipeline_name, exec_modes, grp_mappings = result
                logger.info(
                    "Resolved pipeline '%s' (%s) for project %s",
                    pipeline_name,
                    assigned_id,
                    project_id,
                )
                return PipelineResolutionResult(
                    agent_mappings=mappings,
                    source="pipeline",
                    pipeline_name=pipeline_name,
                    pipeline_id=assigned_id,
                    stage_execution_modes=exec_modes,
                    group_mappings=grp_mappings,
                )
            # Pipeline was deleted — auto-cleanup stale reference (T012/R5)
            logger.warning(
                "Assigned pipeline %s not found for project %s — clearing stale reference",
                assigned_id,
                project_id,
            )
            try:
                async with aiosqlite.connect(db_path) as db:
                    await db.execute("PRAGMA busy_timeout=5000;")
                    await db.execute(
                        "UPDATE project_settings SET assigned_pipeline_id = '' "
                        "WHERE github_user_id = ? AND project_id = ?",
                        ("__workflow__", project_id),
                    )
                    await db.commit()
            except Exception:
                logger.warning(
                    "Failed to clear stale pipeline assignment for project %s",
                    project_id,
                    exc_info=True,
                )
    except Exception:
        logger.warning(
            "Failed to check project pipeline assignment for project %s",
            project_id,
            exc_info=True,
        )

    # ── Tier 2: User-specific agent mappings ─────────────────────────
    user_mappings = await load_user_agent_mappings(github_user_id, project_id)
    if user_mappings:
        logger.info(
            "Resolved user-specific agent mappings for user=%s project=%s",
            github_user_id,
            project_id,
        )
        return PipelineResolutionResult(
            agent_mappings=user_mappings,
            source="user",
        )

    # ── Tier 3: System defaults ──────────────────────────────────────
    default_mappings: dict[str, list[AgentAssignment]] = {
        k: [AgentAssignment(slug=s, display_name=AGENT_DISPLAY_NAMES.get(s)) for s in v]
        for k, v in DEFAULT_AGENT_MAPPINGS.items()
    }
    logger.info("Using default agent mappings for project %s", project_id)
    return PipelineResolutionResult(
        agent_mappings=default_mappings,
        source="default",
    )


def get_transitions(issue_id: str | None = None, limit: int = 50) -> list[WorkflowTransition]:
    """Get workflow transitions, optionally filtered by issue_id."""
    if issue_id:
        filtered = [t for t in _transitions if t.issue_id == issue_id]
        return filtered[-limit:]
    return _transitions[-limit:]
