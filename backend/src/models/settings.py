"""Settings Pydantic models for user preferences, global settings, and project settings."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ── Enums ──


class AIProvider(StrEnum):
    """Supported AI providers."""

    COPILOT = "copilot"
    AZURE_OPENAI = "azure_openai"


# ── Provider metadata ──

PROVIDER_METADATA: dict[str, dict[str, bool]] = {
    AIProvider.COPILOT: {"supports_dynamic_models": True, "requires_auth": True},
    AIProvider.AZURE_OPENAI: {"supports_dynamic_models": False, "requires_auth": False},
}


# ── Dynamic model fetching models ──


class ModelOption(BaseModel):
    """A single model option returned by a provider."""

    id: str
    name: str
    provider: str


class ModelsResponse(BaseModel):
    """Response from the /settings/models/{provider} endpoint."""

    status: str  # "success", "auth_required", "rate_limited", "error"
    models: list[ModelOption] = Field(default_factory=list)
    fetched_at: str | None = None
    cache_hit: bool = False
    rate_limit_warning: bool = False
    message: str | None = None


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
