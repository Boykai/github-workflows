"""Settings Pydantic models for user preferences, global settings, and project settings."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ── Enums ──


class AIProvider(StrEnum):
    """Supported AI providers."""

    COPILOT = "copilot"
    AZURE_OPENAI = "azure_openai"


class ThemeMode(StrEnum):
    """UI theme modes."""

    DARK = "dark"
    LIGHT = "light"


class DefaultView(StrEnum):
    """Default landing view options."""

    CHAT = "chat"
    BOARD = "board"
    SETTINGS = "settings"


# ── Sub-models for API responses (fully resolved, no nulls) ──


class AIPreferences(BaseModel):
    """AI-related settings (fully resolved)."""

    provider: AIProvider
    model: str
    temperature: float = Field(ge=0.0, le=2.0)


class DisplayPreferences(BaseModel):
    """UI/display settings (fully resolved)."""

    theme: ThemeMode
    default_view: DefaultView
    sidebar_collapsed: bool


class WorkflowDefaults(BaseModel):
    """Workflow configuration (fully resolved)."""

    default_repository: str | None
    default_assignee: str
    copilot_polling_interval: int = Field(ge=0)


class NotificationPreferences(BaseModel):
    """Per-event notification toggles (fully resolved)."""

    task_status_change: bool
    agent_completion: bool
    new_recommendation: bool
    chat_mention: bool


# ── Effective Settings (GET responses — fully resolved, no nulls) ──


class EffectiveUserSettings(BaseModel):
    """Fully resolved user settings. Computed as global merged with user overrides."""

    ai: AIPreferences
    display: DisplayPreferences
    workflow: WorkflowDefaults
    notifications: NotificationPreferences


class GlobalSettingsResponse(BaseModel):
    """Instance-wide default settings response."""

    ai: AIPreferences
    display: DisplayPreferences
    workflow: WorkflowDefaults
    notifications: NotificationPreferences
    allowed_models: list[str] = Field(default_factory=list)


class ProjectBoardConfig(BaseModel):
    """Board display configuration for a project."""

    column_order: list[str] = Field(default_factory=list)
    collapsed_columns: list[str] = Field(default_factory=list)
    show_estimates: bool = False


class ProjectAgentMapping(BaseModel):
    """Agent assignment for a pipeline status."""

    slug: str
    display_name: str | None = None


class ProjectSpecificSettings(BaseModel):
    """Project-specific settings section in the response."""

    project_id: str
    board_display_config: ProjectBoardConfig | None = None
    agent_pipeline_mappings: dict[str, list[ProjectAgentMapping]] | None = None


class EffectiveProjectSettings(BaseModel):
    """Fully resolved project settings including user + global effective settings."""

    ai: AIPreferences
    display: DisplayPreferences
    workflow: WorkflowDefaults
    notifications: NotificationPreferences
    project: ProjectSpecificSettings


# ── Update Request Models (partial updates, nullable fields) ──


class AIPreferencesUpdate(BaseModel):
    """Partial update for AI preferences. None means reset to global default."""

    provider: AIProvider | None = None
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)


class DisplayPreferencesUpdate(BaseModel):
    """Partial update for display preferences."""

    theme: ThemeMode | None = None
    default_view: DefaultView | None = None
    sidebar_collapsed: bool | None = None


class WorkflowDefaultsUpdate(BaseModel):
    """Partial update for workflow defaults."""

    default_repository: str | None = None
    default_assignee: str | None = None
    copilot_polling_interval: int | None = Field(default=None, ge=0)


class NotificationPreferencesUpdate(BaseModel):
    """Partial update for notification preferences."""

    task_status_change: bool | None = None
    agent_completion: bool | None = None
    new_recommendation: bool | None = None
    chat_mention: bool | None = None


class UserPreferencesUpdate(BaseModel):
    """Partial update payload for user preferences. All sections optional."""

    ai: AIPreferencesUpdate | None = None
    display: DisplayPreferencesUpdate | None = None
    workflow: WorkflowDefaultsUpdate | None = None
    notifications: NotificationPreferencesUpdate | None = None


class GlobalSettingsUpdate(BaseModel):
    """Partial update payload for global settings."""

    ai: AIPreferencesUpdate | None = None
    display: DisplayPreferencesUpdate | None = None
    workflow: WorkflowDefaultsUpdate | None = None
    notifications: NotificationPreferencesUpdate | None = None
    allowed_models: list[str] | None = None


class ProjectSettingsUpdate(BaseModel):
    """Partial update for project-specific settings."""

    board_display_config: ProjectBoardConfig | None = None
    agent_pipeline_mappings: dict[str, list[ProjectAgentMapping]] | None = None


# ── Database Row Models (for model_dump/model_validate with SQLite) ──


class UserPreferencesRow(BaseModel):
    """Represents a user_preferences database row. All preference fields nullable."""

    github_user_id: str
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_temperature: float | None = None
    theme: str | None = None
    default_view: str | None = None
    sidebar_collapsed: int | None = None  # 0/1 in SQLite
    default_repository: str | None = None
    default_assignee: str | None = None
    copilot_polling_interval: int | None = None
    notify_task_status_change: int | None = None  # 0/1 in SQLite
    notify_agent_completion: int | None = None
    notify_new_recommendation: int | None = None
    notify_chat_mention: int | None = None
    updated_at: str = ""


class GlobalSettingsRow(BaseModel):
    """Represents a global_settings database row."""

    id: int = 1
    ai_provider: str = "copilot"
    ai_model: str = "gpt-4o"
    ai_temperature: float = 0.7
    theme: str = "light"
    default_view: str = "chat"
    sidebar_collapsed: int = 0
    default_repository: str | None = None
    default_assignee: str = ""
    copilot_polling_interval: int = 60
    notify_task_status_change: int = 1
    notify_agent_completion: int = 1
    notify_new_recommendation: int = 1
    notify_chat_mention: int = 1
    allowed_models: str = "[]"  # JSON string in SQLite
    updated_at: str = ""


class ProjectSettingsRow(BaseModel):
    """Represents a project_settings database row."""

    github_user_id: str
    project_id: str
    board_display_config: str | None = None  # JSON string
    agent_pipeline_mappings: str | None = None  # JSON string
    updated_at: str = ""

    def get_board_config(self) -> dict[str, Any] | None:
        """Parse board_display_config JSON."""
        if self.board_display_config:
            return json.loads(self.board_display_config)
        return None

    def get_agent_mappings(self) -> dict[str, Any] | None:
        """Parse agent_pipeline_mappings JSON."""
        if self.agent_pipeline_mappings:
            return json.loads(self.agent_pipeline_mappings)
        return None
