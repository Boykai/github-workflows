"""Database-backed settings store for user preferences, global settings, and project settings."""

import json
from typing import Any

import aiosqlite

from src.logging_utils import get_logger
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
from src.utils import utcnow

logger = get_logger(__name__)


USER_PREFERENCE_COLUMNS = (
    "ai_provider",
    "ai_model",
    "ai_agent_model",
    "ai_temperature",
    "theme",
    "default_view",
    "sidebar_collapsed",
    "default_repository",
    "default_assignee",
    "copilot_polling_interval",
    "notify_task_status_change",
    "notify_agent_completion",
    "notify_new_recommendation",
    "notify_chat_mention",
)

GLOBAL_SETTINGS_COLUMNS = (*USER_PREFERENCE_COLUMNS, "allowed_models")

PROJECT_SETTINGS_COLUMNS = (
    "board_display_config",
    "agent_pipeline_mappings",
    "queue_mode",
    "auto_merge",
)


def _validate_update_keys(updates: dict[str, Any], allowed_columns: tuple[str, ...]) -> None:
    """Reject unexpected update keys before binding values into SQL."""
    unknown_columns = sorted(set(updates) - set(allowed_columns))
    if unknown_columns:
        msg = f"Unsupported settings columns: {', '.join(unknown_columns)}"
        raise ValueError(msg)


def _presence_flag_values(
    updates: dict[str, Any],
    allowed_columns: tuple[str, ...],
) -> tuple[list[Any], list[int]]:
    """Return ordered column values plus presence flags for static partial updates."""
    values = [updates.get(column_name) for column_name in allowed_columns]
    flags = [int(column_name in updates) for column_name in allowed_columns]
    return values, flags


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

    _validate_update_keys(updates, GLOBAL_SETTINGS_COLUMNS)

    now = utcnow().isoformat()
    values, flags = _presence_flag_values(updates, GLOBAL_SETTINGS_COLUMNS)

    logger.debug("Updating global settings: %s", list(updates.keys()))
    await db.execute(
        """
        UPDATE global_settings
        SET ai_provider = CASE WHEN ? THEN ? ELSE ai_provider END,
            ai_model = CASE WHEN ? THEN ? ELSE ai_model END,
            ai_agent_model = CASE WHEN ? THEN ? ELSE ai_agent_model END,
            ai_temperature = CASE WHEN ? THEN ? ELSE ai_temperature END,
            theme = CASE WHEN ? THEN ? ELSE theme END,
            default_view = CASE WHEN ? THEN ? ELSE default_view END,
            sidebar_collapsed = CASE WHEN ? THEN ? ELSE sidebar_collapsed END,
            default_repository = CASE WHEN ? THEN ? ELSE default_repository END,
            default_assignee = CASE WHEN ? THEN ? ELSE default_assignee END,
            copilot_polling_interval = CASE WHEN ? THEN ? ELSE copilot_polling_interval END,
            notify_task_status_change = CASE WHEN ? THEN ? ELSE notify_task_status_change END,
            notify_agent_completion = CASE WHEN ? THEN ? ELSE notify_agent_completion END,
            notify_new_recommendation = CASE WHEN ? THEN ? ELSE notify_new_recommendation END,
            notify_chat_mention = CASE WHEN ? THEN ? ELSE notify_chat_mention END,
            allowed_models = CASE WHEN ? THEN ? ELSE allowed_models END,
            updated_at = ?
        WHERE id = 1
        """,
        [item for pair in zip(flags, values, strict=False) for item in pair] + [now],
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
    if not updates:
        return

    _validate_update_keys(updates, USER_PREFERENCE_COLUMNS)

    now = utcnow().isoformat()
    values, flags = _presence_flag_values(updates, USER_PREFERENCE_COLUMNS)

    logger.debug("Upserting user preferences for %s", github_user_id)
    await db.execute(
        """
        INSERT INTO user_preferences (
            github_user_id,
            ai_provider,
            ai_model,
            ai_agent_model,
            ai_temperature,
            theme,
            default_view,
            sidebar_collapsed,
            default_repository,
            default_assignee,
            copilot_polling_interval,
            notify_task_status_change,
            notify_agent_completion,
            notify_new_recommendation,
            notify_chat_mention,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(github_user_id) DO UPDATE SET
            ai_provider = CASE WHEN ? THEN excluded.ai_provider ELSE user_preferences.ai_provider END,
            ai_model = CASE WHEN ? THEN excluded.ai_model ELSE user_preferences.ai_model END,
            ai_agent_model = CASE WHEN ? THEN excluded.ai_agent_model ELSE user_preferences.ai_agent_model END,
            ai_temperature = CASE WHEN ? THEN excluded.ai_temperature ELSE user_preferences.ai_temperature END,
            theme = CASE WHEN ? THEN excluded.theme ELSE user_preferences.theme END,
            default_view = CASE WHEN ? THEN excluded.default_view ELSE user_preferences.default_view END,
            sidebar_collapsed = CASE WHEN ? THEN excluded.sidebar_collapsed ELSE user_preferences.sidebar_collapsed END,
            default_repository = CASE WHEN ? THEN excluded.default_repository ELSE user_preferences.default_repository END,
            default_assignee = CASE WHEN ? THEN excluded.default_assignee ELSE user_preferences.default_assignee END,
            copilot_polling_interval = CASE WHEN ? THEN excluded.copilot_polling_interval ELSE user_preferences.copilot_polling_interval END,
            notify_task_status_change = CASE WHEN ? THEN excluded.notify_task_status_change ELSE user_preferences.notify_task_status_change END,
            notify_agent_completion = CASE WHEN ? THEN excluded.notify_agent_completion ELSE user_preferences.notify_agent_completion END,
            notify_new_recommendation = CASE WHEN ? THEN excluded.notify_new_recommendation ELSE user_preferences.notify_new_recommendation END,
            notify_chat_mention = CASE WHEN ? THEN excluded.notify_chat_mention ELSE user_preferences.notify_chat_mention END,
            updated_at = excluded.updated_at
        """,
        [github_user_id, *values, now, *flags],
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
    if not updates:
        return

    _validate_update_keys(updates, PROJECT_SETTINGS_COLUMNS)

    now = utcnow().isoformat()
    values, flags = _presence_flag_values(updates, PROJECT_SETTINGS_COLUMNS)

    logger.debug("Upserting project settings for user=%s project=%s", github_user_id, project_id)

    # Replace None with default for NOT NULL columns
    insert_values = list(values)
    # queue_mode must be non-NULL (DEFAULT 0 in schema)
    queue_mode_idx = list(PROJECT_SETTINGS_COLUMNS).index("queue_mode")
    if insert_values[queue_mode_idx] is None:
        insert_values[queue_mode_idx] = 0
    # auto_merge must be non-NULL (DEFAULT 0 in schema)
    auto_merge_idx = list(PROJECT_SETTINGS_COLUMNS).index("auto_merge")
    if insert_values[auto_merge_idx] is None:
        insert_values[auto_merge_idx] = 0

    await db.execute(
        """
        INSERT INTO project_settings (
            github_user_id,
            project_id,
            board_display_config,
            agent_pipeline_mappings,
            queue_mode,
            auto_merge,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(github_user_id, project_id) DO UPDATE SET
            board_display_config = CASE
                WHEN ? THEN excluded.board_display_config
                ELSE project_settings.board_display_config
            END,
            agent_pipeline_mappings = CASE
                WHEN ? THEN excluded.agent_pipeline_mappings
                ELSE project_settings.agent_pipeline_mappings
            END,
            queue_mode = CASE
                WHEN ? THEN excluded.queue_mode
                ELSE project_settings.queue_mode
            END,
            auto_merge = CASE
                WHEN ? THEN excluded.auto_merge
                ELSE project_settings.auto_merge
            END,
            updated_at = excluded.updated_at
        """,
        [github_user_id, project_id, *insert_values, now, *flags],
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
            agent_model=str(row["ai_agent_model"] or ""),
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

    def _pick(user_col: str, global_col: str | None = None) -> Any:
        """Return user value if not NULL, else global value."""
        g_col = global_col or user_col
        if user_row is not None and user_row[user_col] is not None:
            return user_row[user_col]
        return global_row[g_col]

    def _pick_nullable(user_col: str, global_col: str | None = None) -> Any:
        """Return user value when row exists (None is a valid explicit override), else global value."""
        g_col = global_col or user_col
        if user_row is not None:
            return user_row[user_col]
        return global_row[g_col]

    return EffectiveUserSettings(
        ai=AIPreferences(
            provider=AIProvider(str(_pick("ai_provider"))),
            model=str(_pick("ai_model")),
            temperature=float(_pick("ai_temperature")),
            agent_model=str(_pick("ai_agent_model") or ""),
        ),
        display=DisplayPreferences(
            theme=ThemeMode(str(_pick("theme"))),
            default_view=DefaultView(str(_pick("default_view"))),
            sidebar_collapsed=bool(_pick("sidebar_collapsed")),
        ),
        workflow=WorkflowDefaults(
            default_repository=_pick_nullable("default_repository"),
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

    # Merge the queue_mode column into the board config.
    # Create a board config when either the JSON config exists or queue_mode
    # has been explicitly enabled, so the toggle state is visible to the frontend.
    queue_mode_val = (
        bool(project_row["queue_mode"]) if "queue_mode" in project_row.keys() else False
    )
    auto_merge_val = (
        bool(project_row["auto_merge"]) if "auto_merge" in project_row.keys() else False
    )
    if board_config is None:
        if queue_mode_val or auto_merge_val:
            board_config = ProjectBoardConfig(queue_mode=queue_mode_val, auto_merge=auto_merge_val)
    else:
        board_config.queue_mode = queue_mode_val
        board_config.auto_merge = auto_merge_val

    agent_mappings = None
    if project_row["agent_pipeline_mappings"]:
        raw = json.loads(project_row["agent_pipeline_mappings"])
        # raw is dict[str, list[dict]] — convert inner dicts to ProjectAgentMapping
        agent_mappings = {
            status: [ProjectAgentMapping(**m) for m in mappings] for status, mappings in raw.items()
        }

    return ProjectSpecificSettings(
        project_id=project_id,
        board_display_config=board_config,
        agent_pipeline_mappings=agent_mappings,
    )


# ── Queue Mode Helpers ──


# Short-TTL in-memory cache for queue mode lookups to avoid repeated DB reads
# during a single polling cycle.
_queue_mode_cache: dict[str, tuple[bool, float]] = {}
_QUEUE_MODE_CACHE_TTL_SECONDS = 10.0


async def is_queue_mode_enabled(db: aiosqlite.Connection, project_id: str) -> bool:
    """Check if queue mode is enabled for a project.

    Uses a short-TTL in-memory cache to avoid repeated DB reads during
    polling cycles.  Falls back to DB query on cache miss or expiry.
    """
    import time

    now = time.monotonic()
    cached = _queue_mode_cache.get(project_id)
    if cached is not None:
        value, cached_at = cached
        if now - cached_at < _QUEUE_MODE_CACHE_TTL_SECONDS:
            return value

    # Query only the canonical __workflow__ row — the settings API syncs
    # queue_mode to this row, so it is the single source of truth.
    cursor = await db.execute(
        "SELECT queue_mode FROM project_settings"
        " WHERE project_id = ? AND github_user_id = '__workflow__' LIMIT 1",
        (project_id,),
    )
    row = await cursor.fetchone()
    enabled = row is not None and bool(row[0])
    _queue_mode_cache[project_id] = (enabled, now)
    return enabled


# ── Auto Merge Helpers ──


# Short-TTL in-memory cache for auto merge lookups to avoid repeated DB reads
# during a single polling cycle.
_auto_merge_cache: dict[str, tuple[bool, float]] = {}
_AUTO_MERGE_CACHE_TTL_SECONDS = 10.0


async def is_auto_merge_enabled(db: aiosqlite.Connection, project_id: str) -> bool:
    """Check if auto merge is enabled for a project.

    Uses a short-TTL in-memory cache to avoid repeated DB reads during
    polling cycles.  Falls back to DB query on cache miss or expiry.
    """
    import time

    now = time.monotonic()
    cached = _auto_merge_cache.get(project_id)
    if cached is not None:
        value, cached_at = cached
        if now - cached_at < _AUTO_MERGE_CACHE_TTL_SECONDS:
            return value

    # Query only the canonical __workflow__ row — the settings API syncs
    # auto_merge to this row, so it is the single source of truth.
    cursor = await db.execute(
        "SELECT auto_merge FROM project_settings"
        " WHERE project_id = ? AND github_user_id = '__workflow__' LIMIT 1",
        (project_id,),
    )
    row = await cursor.fetchone()
    enabled = row is not None and bool(row[0])
    _auto_merge_cache[project_id] = (enabled, now)
    return enabled


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
            "agent_model": "ai_agent_model",
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
