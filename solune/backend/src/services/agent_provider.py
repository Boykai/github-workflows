"""Agent provider factory for the Microsoft Agent Framework.

Creates the appropriate agent instance based on the configured AI_PROVIDER:
- "copilot"      → GitHubCopilotAgent (agent_framework.github)
- "azure_openai" → Agent with AzureOpenAIResponsesClient

Replaces CopilotCompletionProvider + AzureOpenAICompletionProvider +
CopilotClientPool from v0.1.x.

v0.2.0 — Intelligent Chat Agent (Microsoft Agent Framework)
"""

from __future__ import annotations

from typing import Any

from src.config import get_settings
from src.logging_utils import get_logger

logger = get_logger(__name__)


class AgentProvider:
    """Thin wrapper around a Microsoft Agent Framework agent instance.

    Provides a uniform interface regardless of the underlying provider
    (Copilot or Azure OpenAI).
    """

    def __init__(self, provider_name: str, agent: Any) -> None:
        self._provider_name = provider_name
        self._agent = agent

    @property
    def name(self) -> str:
        """Provider name for logging and diagnostics."""
        return self._provider_name

    @property
    def agent(self) -> Any:
        """The underlying agent instance."""
        return self._agent


def create_agent_provider(
    system_instructions: str,
    tools: list[Any] | None = None,
) -> AgentProvider:
    """Factory: create an Agent Framework agent with the configured provider.

    Args:
        system_instructions: The system prompt / instructions for the agent.
        tools: List of tool functions decorated with @tool.

    Returns:
        AgentProvider wrapping the configured agent instance.

    Raises:
        ValueError: If the configured provider is unknown or dependencies
            are missing.
    """
    settings = get_settings()
    provider_name = settings.ai_provider

    if provider_name == "copilot":
        return _create_copilot_agent(system_instructions, tools or [])
    elif provider_name == "azure_openai":
        return _create_azure_agent(system_instructions, tools or [])
    else:
        raise ValueError(
            f"Unknown AI provider: '{provider_name}'. "
            "Set AI_PROVIDER to 'copilot' or 'azure_openai'."
        )


def _create_copilot_agent(
    system_instructions: str,
    tools: list[Any],
) -> AgentProvider:
    """Create a GitHubCopilotAgent from the agent framework.

    Raises:
        ValueError: If agent-framework-github-copilot is not installed.
    """
    try:
        from agent_framework.github import GitHubCopilotAgent  # type: ignore[import-untyped]

        agent = GitHubCopilotAgent(
            instructions=system_instructions,
            tools=tools,
        )
        logger.info("Created GitHubCopilotAgent with %d tools", len(tools))
        return AgentProvider("copilot", agent)
    except ImportError as exc:
        raise ValueError(
            "GitHubCopilotAgent requires agent-framework-github-copilot. "
            "Install it with: pip install agent-framework-github-copilot"
        ) from exc


def _create_azure_agent(
    system_instructions: str,
    tools: list[Any],
) -> AgentProvider:
    """Create an Agent with AzureOpenAIResponsesClient.

    Raises:
        ValueError: If Azure OpenAI credentials are not configured or
            agent-framework-openai is not installed.
    """
    settings = get_settings()

    if not settings.azure_openai_endpoint or not settings.azure_openai_key:
        raise ValueError(
            "Azure OpenAI credentials not configured. "
            "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY."
        )

    try:
        from agent_framework import Agent  # type: ignore[import-untyped]
        from agent_framework.openai import (  # type: ignore[import-untyped]
            AzureOpenAIResponsesClient,
        )

        client = AzureOpenAIResponsesClient(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_key,
            model=settings.azure_openai_deployment,
        )
        agent = Agent(
            instructions=system_instructions,
            client=client,
            tools=tools,
        )
        logger.info(
            "Created Azure OpenAI Agent (deployment: %s) with %d tools",
            settings.azure_openai_deployment,
            len(tools),
        )
        return AgentProvider("azure_openai", agent)
    except ImportError as exc:
        raise ValueError(
            "Azure OpenAI agent requires agent-framework-openai. "
            "Install it with: pip install agent-framework-openai"
        ) from exc
