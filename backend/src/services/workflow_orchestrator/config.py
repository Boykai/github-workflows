"""Workflow configuration load/persist/defaults and transition audit logging."""

import json
import logging

import aiosqlite

from src.models.agent import AgentAssignment
from src.models.workflow import (
    WorkflowConfiguration,
    WorkflowTransition,
)
from src.utils import utcnow

logger = logging.getLogger(__name__)

# In-memory storage for workflow transitions (audit log)
_transitions: list[WorkflowTransition] = []

# In-memory storage for workflow configurations (per project)
_workflow_configs: dict[str, WorkflowConfiguration] = {}


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

            # Fall back to agent_pipeline_mappings only
            cursor = await db.execute(
                "SELECT agent_pipeline_mappings FROM project_settings WHERE github_user_id = '__workflow__' AND project_id = ? AND agent_pipeline_mappings IS NOT NULL LIMIT 1",
                (project_id,),
            )
            row = await cursor.fetchone()

            if row and row["agent_pipeline_mappings"]:
                raw_mappings = json.loads(row["agent_pipeline_mappings"])
                # Convert raw dicts to AgentAssignment objects
                agent_mappings: dict[str, list[AgentAssignment]] = {}
                for status, agents in raw_mappings.items():
                    agent_mappings[status] = [
                        AgentAssignment(**a)
                        if isinstance(a, dict)
                        else AgentAssignment(slug=str(a))
                        for a in agents
                    ]
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
                except Exception:
                    pass
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

    # Serialize config
    config_json = config.model_dump_json()
    agent_mappings_json = json.dumps(
        {
            status: [
                a.model_dump(mode="json") if hasattr(a, "model_dump") else {"slug": str(a)}
                for a in agents
            ]
            for status, agents in config.agent_mappings.items()
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


def get_transitions(issue_id: str | None = None, limit: int = 50) -> list[WorkflowTransition]:
    """Get workflow transitions, optionally filtered by issue_id."""
    if issue_id:
        filtered = [t for t in _transitions if t.issue_id == issue_id]
        return filtered[-limit:]
    return _transitions[-limit:]
