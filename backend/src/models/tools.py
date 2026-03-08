"""Pydantic models for MCP tool configuration management."""

from pydantic import BaseModel, Field


class McpToolConfig(BaseModel):
    """Full MCP tool configuration entity."""

    id: str
    github_user_id: str
    project_id: str
    name: str
    description: str = ""
    endpoint_url: str
    config_content: str = "{}"
    sync_status: str = "pending"
    sync_error: str = ""
    synced_at: str | None = None
    github_repo_target: str = ""
    is_active: bool = True
    created_at: str
    updated_at: str


class McpToolConfigCreate(BaseModel):
    """Request body for creating/uploading a new MCP tool configuration."""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    config_content: str = Field(min_length=2, max_length=262144)
    github_repo_target: str = Field(default="", max_length=200)


class McpToolConfigUpdate(BaseModel):
    """Request body for updating an existing MCP tool configuration."""

    name: str | None = None
    description: str | None = None
    config_content: str | None = None
    github_repo_target: str | None = None


class McpToolConfigResponse(BaseModel):
    """Single MCP tool configuration in API responses."""

    id: str
    name: str
    description: str
    endpoint_url: str
    config_content: str
    sync_status: str
    sync_error: str
    synced_at: str | None
    github_repo_target: str
    is_active: bool
    created_at: str
    updated_at: str


class McpToolConfigListResponse(BaseModel):
    """Response for the list endpoint."""

    tools: list[McpToolConfigResponse]
    count: int


class McpToolConfigSyncResult(BaseModel):
    """Response for sync operations."""

    id: str
    sync_status: str
    sync_error: str
    synced_at: str | None
    synced_paths: list[str] = Field(default_factory=list)


class RepoMcpServerUpdate(BaseModel):
    """Request body for updating a repository MCP server entry directly."""

    name: str = Field(min_length=1, max_length=100)
    config_content: str = Field(min_length=2, max_length=262144)


class RepoMcpServerConfig(BaseModel):
    """A normalized MCP server entry discovered in the repository."""

    name: str
    config: dict[str, object]
    source_paths: list[str] = Field(default_factory=list)


class RepoMcpConfigResponse(BaseModel):
    """Repository MCP configuration discovered from known GitHub paths."""

    paths_checked: list[str] = Field(default_factory=list)
    available_paths: list[str] = Field(default_factory=list)
    primary_path: str | None = None
    servers: list[RepoMcpServerConfig] = Field(default_factory=list)


class McpPresetResponse(BaseModel):
    """Static MCP preset returned to the frontend."""

    id: str
    name: str
    description: str
    category: str
    icon: str
    config_content: str


class McpPresetListResponse(BaseModel):
    """Response for listing available MCP presets."""

    presets: list[McpPresetResponse]
    count: int


class AgentToolAssociation(BaseModel):
    """Represents the many-to-many relationship between agents and MCP tools."""

    agent_id: str
    tool_id: str
    assigned_at: str


class AgentToolInfo(BaseModel):
    """Lightweight tool info returned in agent-tool association endpoints."""

    id: str
    name: str
    description: str


class AgentToolsResponse(BaseModel):
    """Response for agent tools endpoints."""

    tools: list[AgentToolInfo]


class AgentToolsUpdate(BaseModel):
    """Request body for updating agent tool associations."""

    tool_ids: list[str]


class ToolDeleteResult(BaseModel):
    """Response for delete operations."""

    success: bool
    deleted_id: str | None = None
    affected_agents: list[AgentToolInfo] = Field(default_factory=list)
