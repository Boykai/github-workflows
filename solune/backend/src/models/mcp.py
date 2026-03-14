"""Pydantic models for MCP (Model Context Protocol) configuration management."""

from pydantic import BaseModel, Field


class McpConfigurationCreate(BaseModel):
    """Request body for creating a new MCP configuration."""

    name: str = Field(min_length=1, max_length=100)
    endpoint_url: str = Field(min_length=1, max_length=2048)


class McpConfigurationResponse(BaseModel):
    """Single MCP configuration in API responses."""

    id: str
    name: str
    endpoint_url: str
    is_active: bool
    created_at: str
    updated_at: str


class McpConfigurationListResponse(BaseModel):
    """List of MCP configurations for a user."""

    mcps: list[McpConfigurationResponse]
    count: int
