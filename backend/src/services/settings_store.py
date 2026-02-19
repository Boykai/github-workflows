"""Database-backed settings store for user preferences, global settings, and project settings."""

import json
import logging
from datetime import UTC, datetime

import aiosqlite

from src.models.settings import (
    AIPreferences,
    AIProvider,
    DefaultView,
    DisplayPreferences,
    EffectiveProjectSettings,
    EffectiveUserSettings,
    GlobalSettingsResponse,
    NotificationPreferences,
    ProjectAgentMapping,
    ProjectBoardConfig,
    ProjectSpecificSettings,
    ThemeMode,
    WorkflowDefaults,
)

logger = logging.getLogger(__name__)


# ── Global Settings ──


async def get_global_settings(db: aiosqlite.Connection) -> GlobalSettingsResponse:
    """
    Load global settings singleton row and return as response model.

    Global settings always exist (seeded at first startup), so this never returns None.
    """
    logger.debug("Loading global settings")
    cursor = await db.execute("SELECT * FROM global_settings WHERE id = 1")
    row = await cursor.fetchone()

    if row is None:
        raise RuntimeError("Global settings not found — seed_global_settings() was not called")

    return _row_to_global_response(row)


async def update_global_settings(
    db: aiosqlite.Connection,
    updates: dict,
) -> GlobalSettingsResponse:
    """
    Partial-update global settings. Only fields present in `updates` are changed.

    Args:
        db: Database connection
        updates: Flat dict of column_name → value pairs to update

    Returns:
        Updated global settings response after merge
    """
    if not updates:
        return await get_global_settings(db)

    now = datetime.now(UTC).isoformat()
    updates["updated_at"] = now

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values())

    logger.debug("Updating global settings: %s", list(updates.keys()))
    await db.execute(
        f"UPDATE global_settings SET {set_clause} WHERE id = 1",  # noqa: S608
        values,
    )
    await db.commit()

    return await get_global_settings(db)


# ── User Preferences ──


async def get_user_preferences_row(
    db: aiosqlite.Connection, github_user_id: str
) -> aiosqlite.Row | None:
    """
    Load raw user_preferences row. Returns None if user has no saved preferences.
    """
    logger.debug("Loading user preferences for %s", github_user_id)
    cursor = await db.execute(
        "SELECT * FROM user_preferences WHERE github_user_id = ?", (github_user_id,)
    )
    return await cursor.fetchone()


async def upsert_user_preferences(
    db: aiosqlite.Connection,
    github_user_id: str,
    updates: dict,
) -> None:
    """
    Insert or update user preferences. Creates row if not exists, otherwise merges.

    Args:
        db: Database connection
        github_user_id: GitHub user ID (primary key)
        updates: Flat dict of column_name → value pairs to upsert
    """
    now = datetime.now(UTC).isoformat()

    existing = await get_user_preferences_row(db, github_user_id)

    if existing is None:
        # INSERT new row
        updates["github_user_id"] = github_user_id
        updates["updated_at"] = now
        cols = ", ".join(updates.keys())
        placeholders = ", ".join("?" for _ in updates)
        logger.debug("Inserting user preferences for %s", github_user_id)
        await db.execute(
            f"INSERT INTO user_preferences ({cols}) VALUES ({placeholders})",  # noqa: S608
            list(updates.values()),
        )
    else:
        # UPDATE existing row
        updates["updated_at"] = now
        set_clause = ", ".join(f"{col} = ?" for col in updates)
        values = list(updates.values()) + [github_user_id]
        logger.debug("Updating user preferences for %s", github_user_id)
        await db.execute(
            f"UPDATE user_preferences SET {set_clause} WHERE github_user_id = ?",  # noqa: S608
            values,
        )

    await db.commit()


# ── Project Settings ──


async def get_project_settings_row(
    db: aiosqlite.Connection, github_user_id: str, project_id: str
) -> aiosqlite.Row | None:
    """
    Load raw project_settings row. Returns None if no project-specific settings exist.
    """
    logger.debug("Loading project settings for user=%s project=%s", github_user_id, project_id)
    cursor = await db.execute(
        "SELECT * FROM project_settings WHERE github_user_id = ? AND project_id = ?",
        (github_user_id, project_id),
    )
    return await cursor.fetchone()


async def upsert_project_settings(
    db: aiosqlite.Connection,
    github_user_id: str,
    project_id: str,
    updates: dict,
) -> None:
    """
    Insert or update project settings.

    Args:
        db: Database connection
        github_user_id: GitHub user ID
        project_id: GitHub Project ID
        updates: Dict with board_display_config and/or agent_pipeline_mappings (JSON strings)
    """
    now = datetime.now(UTC).isoformat()

    existing = await get_project_settings_row(db, github_user_id, project_id)

    if existing is None:
        updates["github_user_id"] = github_user_id
        updates["project_id"] = project_id
        updates["updated_at"] = now
        cols = ", ".join(updates.keys())
        placeholders = ", ".join("?" for _ in updates)
        logger.debug("Inserting project settings for user=%s project=%s", github_user_id, project_id)
        await db.execute(
            f"INSERT INTO project_settings ({cols}) VALUES ({placeholders})",  # noqa: S608
            list(updates.values()),
        )
    else:
        updates["updated_at"] = now
        set_clause = ", ".join(f"{col} = ?" for col in updates)
        values = list(updates.values()) + [github_user_id, project_id]
        logger.debug("Updating project settings for user=%s project=%s", github_user_id, project_id)
        await db.execute(
            f"UPDATE project_settings SET {set_clause} WHERE github_user_id = ? AND project_id = ?",  # noqa: S608
            values,
        )

    await db.commit()


# ── Merge Logic ──


async def get_effective_user_settings(
    db: aiosqlite.Connection, github_user_id: str
) -> EffectiveUserSettings:
    """
    Compute effective user settings by merging global defaults with user overrides.

    Merge order: global_settings (base) ← user_preferences (override)
    All fields in the result are fully resolved (no nulls).
    """
    global_row = await _get_global_row(db)
    user_row = await get_user_preferences_row(db, github_user_id)

    return _merge_user_settings(global_row, user_row)


async def get_effective_project_settings(
    db: aiosqlite.Connection, github_user_id: str, project_id: str
) -> EffectiveProjectSettings:
    """
    Compute effective project settings:
    global_settings ← user_preferences ← project_settings

    The result includes all user-level effective settings plus project-specific overrides.
    """
    global_row = await _get_global_row(db)
    user_row = await get_user_preferences_row(db, github_user_id)
    project_row = await get_project_settings_row(db, github_user_id, project_id)

    # Merge user-level first
    effective_user = _merge_user_settings(global_row, user_row)

    # Build project-specific section
    project_section = _build_project_section(project_id, project_row)

    return EffectiveProjectSettings(
        ai=effective_user.ai,
        display=effective_user.display,
        workflow=effective_user.workflow,
        notifications=effective_user.notifications,
        project=project_section,
    )


# ── Internal Helpers ──


async def _get_global_row(db: aiosqlite.Connection) -> aiosqlite.Row:
    """Load the singleton global_settings row."""
    cursor = await db.execute("SELECT * FROM global_settings WHERE id = 1")
    row = await cursor.fetchone()
    if row is None:
        raise RuntimeError("Global settings not found")
    return row


def _row_to_global_response(row: aiosqlite.Row) -> GlobalSettingsResponse:
    """Convert a global_settings row to the API response model."""
    allowed_models = json.loads(row["allowed_models"]) if row["allowed_models"] else []

    return GlobalSettingsResponse(
        ai=AIPreferences(
            provider=AIProvider(row["ai_provider"]),
            model=row["ai_model"],
            temperature=row["ai_temperature"],
        ),
        display=DisplayPreferences(
            theme=ThemeMode(row["theme"]),
            default_view=DefaultView(row["default_view"]),
            sidebar_collapsed=bool(row["sidebar_collapsed"]),
        ),
        workflow=WorkflowDefaults(
            default_repository=row["default_repository"],
            default_assignee=row["default_assignee"],
            copilot_polling_interval=row["copilot_polling_interval"],
        ),
        notifications=NotificationPreferences(
            task_status_change=bool(row["notify_task_status_change"]),
            agent_completion=bool(row["notify_agent_completion"]),
            new_recommendation=bool(row["notify_new_recommendation"]),
            chat_mention=bool(row["notify_chat_mention"]),
        ),
        allowed_models=allowed_models,
    )


def _merge_user_settings(
    global_row: aiosqlite.Row, user_row: aiosqlite.Row | None
) -> EffectiveUserSettings:
    """Merge global defaults with optional user overrides into effective settings."""

    def _pick(user_col: str, global_col: str | None = None) -> object:
        """Return user value if not NULL, else global value."""
        g_col = global_col or user_col
        if user_row is not None and user_row[user_col] is not None:
            return user_row[user_col]
        return global_row[g_col]

    return EffectiveUserSettings(
        ai=AIPreferences(
            provider=AIProvider(str(_pick("ai_provider"))),
            model=str(_pick("ai_model")),
            temperature=float(_pick("ai_temperature")),
        ),
        display=DisplayPreferences(
            theme=ThemeMode(str(_pick("theme"))),
            default_view=DefaultView(str(_pick("default_view"))),
            sidebar_collapsed=bool(_pick("sidebar_collapsed")),
        ),
        workflow=WorkflowDefaults(
            default_repository=_pick("default_repository"),
            default_assignee=str(_pick("default_assignee")),
            copilot_polling_interval=int(_pick("copilot_polling_interval")),
        ),
        notifications=NotificationPreferences(
            task_status_change=bool(_pick("notify_task_status_change")),
            agent_completion=bool(_pick("notify_agent_completion")),
            new_recommendation=bool(_pick("notify_new_recommendation")),
            chat_mention=bool(_pick("notify_chat_mention")),
        ),
    )


def _build_project_section(
    project_id: str, project_row: aiosqlite.Row | None
) -> ProjectSpecificSettings:
    """Build the project-specific settings section from a DB row."""
    if project_row is None:
        return ProjectSpecificSettings(project_id=project_id)

    board_config = None
    if project_row["board_display_config"]:
        raw = json.loads(project_row["board_display_config"])
        board_config = ProjectBoardConfig(**raw)

    agent_mappings = None
    if project_row["agent_pipeline_mappings"]:
        raw = json.loads(project_row["agent_pipeline_mappings"])
        # raw is dict[str, list[dict]] — convert inner dicts to ProjectAgentMapping
        agent_mappings = {
            status: [ProjectAgentMapping(**m) for m in mappings]
            for status, mappings in raw.items()
        }

    return ProjectSpecificSettings(
        project_id=project_id,
        board_display_config=board_config,
        agent_pipeline_mappings=agent_mappings,
    )


def flatten_user_preferences_update(update: dict) -> dict:
    """
    Flatten nested UserPreferencesUpdate dict into flat column → value mapping.

    Input shape: { "ai": {"provider": "copilot"}, "display": {"theme": "dark"} }
    Output shape: { "ai_provider": "copilot", "theme": "dark" }
    """
    column_map = {
        "ai": {
            "provider": "ai_provider",
            "model": "ai_model",
            "temperature": "ai_temperature",
        },
        "display": {
            "theme": "theme",
            "default_view": "default_view",
            "sidebar_collapsed": "sidebar_collapsed",
        },
        "workflow": {
            "default_repository": "default_repository",
            "default_assignee": "default_assignee",
            "copilot_polling_interval": "copilot_polling_interval",
        },
        "notifications": {
            "task_status_change": "notify_task_status_change",
            "agent_completion": "notify_agent_completion",
            "new_recommendation": "notify_new_recommendation",
            "chat_mention": "notify_chat_mention",
        },
    }

    flat: dict = {}
    for section_key, field_map in column_map.items():
        section_data = update.get(section_key)
        if section_data is None:
            continue
        for field_key, col_name in field_map.items():
            if field_key in section_data:
                value = section_data[field_key]
                # Convert enums to their value
                if hasattr(value, "value"):
                    value = value.value
                # Convert booleans to int for SQLite
                if isinstance(value, bool):
                    value = int(value)
                flat[col_name] = value
    return flat


def flatten_global_settings_update(update: dict) -> dict:
    """
    Flatten nested GlobalSettingsUpdate dict into flat column → value mapping.

    Same as user preferences flattening, but also handles allowed_models.
    """
    flat = flatten_user_preferences_update(update)

    if "allowed_models" in update and update["allowed_models"] is not None:
        flat["allowed_models"] = json.dumps(update["allowed_models"])

    return flat
