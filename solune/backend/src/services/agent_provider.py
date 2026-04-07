"""Agent provider factory — creates framework Agent instances.

Maps the ``AI_PROVIDER`` configuration to the appropriate chat client:
- ``"copilot"``     → OpenAI-compatible client using GitHub Copilot
- ``"azure_openai"`` → Azure OpenAI chat client

Replaces ``CopilotCompletionProvider`` + ``AzureOpenAICompletionProvider``
+ ``CopilotClientPool`` for agent-based interactions.  The old providers
are kept (with deprecation warnings) for backward compatibility.
"""

from __future__ import annotations

from typing import Any

from src.config import get_settings
from src.logging_utils import get_logger

logger = get_logger(__name__)


def create_agent_client(
    github_token: str | None = None,
) -> Any:
    """Create a chat client for the Microsoft Agent Framework.

    The client type is determined by the ``AI_PROVIDER`` setting:
    - ``"copilot"`` → Uses an OpenAI-compatible client configured for
      GitHub Copilot (the token is the user's OAuth token).
    - ``"azure_openai"`` → Uses the Azure OpenAI chat client with
      static API keys from settings.

    Args:
        github_token: GitHub OAuth token (required for the Copilot provider).

    Returns:
        A chat client instance compatible with ``Agent(client=...)``.

    Raises:
        ValueError: If the provider is not configured or credentials
            are missing.
    """
    settings = get_settings()
    provider = settings.ai_provider.lower()

    if provider == "copilot":
        return _create_copilot_client(github_token, settings)
    elif provider == "azure_openai":
        return _create_azure_client(settings)
    else:
        raise ValueError(f"Unsupported AI_PROVIDER: {provider!r}")


def _create_copilot_client(github_token: str | None, settings: Any) -> Any:
    """Create an OpenAI-compatible client for GitHub Copilot.

    Uses the ``agent_framework.openai.OpenAIChatClient`` pointed at the
    Copilot API endpoint with the user's GitHub OAuth token as the API key.
    """
    if not github_token:
        raise ValueError(
            "GitHub OAuth token is required for the Copilot AI provider. "
            "Please authenticate via GitHub OAuth first."
        )

    try:
        from agent_framework.openai import OpenAIChatClient
    except ImportError:
        # Fallback: if agent-framework is not installed, raise clearly
        raise ValueError(
            "agent-framework-core is not installed. "
            "Run: pip install agent-framework-core"
        )

    model_id = getattr(settings, "copilot_model", "gpt-4o")

    return OpenAIChatClient(
        model_id=model_id,
        api_key=github_token,
    )


def _create_azure_client(settings: Any) -> Any:
    """Create an Azure OpenAI chat client.

    Uses ``agent_framework.azure.AzureOpenAIChatClient`` with the
    endpoint and API key from settings.
    """
    endpoint = getattr(settings, "azure_openai_endpoint", None)
    api_key = getattr(settings, "azure_openai_key", None)
    deployment = getattr(settings, "azure_openai_deployment", "gpt-4")

    if not endpoint or not api_key:
        raise ValueError(
            "Azure OpenAI requires AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY. "
            "Set these in your environment or .env file."
        )

    try:
        from agent_framework.azure import AzureOpenAIChatClient
    except ImportError:
        # Fallback: try the openai-based Azure approach
        try:
            from agent_framework.openai import OpenAIChatClient

            return OpenAIChatClient(
                model_id=deployment,
                api_key=api_key,
                base_url=f"{endpoint.rstrip('/')}/openai/deployments/{deployment}",
            )
        except ImportError:
            raise ValueError(
                "agent-framework-core is not installed. "
                "Run: pip install agent-framework-core"
            )

    return AzureOpenAIChatClient(
        endpoint=endpoint,
        api_key=api_key,
        deployment_name=deployment,
    )
