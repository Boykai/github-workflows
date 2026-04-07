"""Tests for agent provider factory (src/services/agent_provider.py).

Verifies that the factory creates the correct agent type based on
AI_PROVIDER setting, handles missing dependencies gracefully, and
validates configuration.

v0.2.0 — Intelligent Chat Agent (Microsoft Agent Framework)
"""

from unittest.mock import MagicMock, patch

import pytest

from src.services.agent_provider import (
    AgentProvider,
    create_agent_provider,
)

# ── AgentProvider wrapper ────────────────────────────────────────────────


class TestAgentProvider:
    def test_name_property(self):
        provider = AgentProvider("copilot", MagicMock())
        assert provider.name == "copilot"

    def test_agent_property(self):
        mock_agent = MagicMock()
        provider = AgentProvider("azure_openai", mock_agent)
        assert provider.agent is mock_agent


# ── Factory — unknown provider ───────────────────────────────────────────


class TestCreateAgentProviderUnknown:
    def test_unknown_provider_raises(self):
        with patch("src.services.agent_provider.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(ai_provider="openrouter")
            with pytest.raises(ValueError, match="Unknown AI provider"):
                create_agent_provider("instructions")


# ── Factory — Copilot provider ───────────────────────────────────────────


class TestCreateCopilotAgent:
    def test_copilot_with_framework_installed(self):
        """When agent-framework-github-copilot is available, factory creates agent."""
        mock_agent = MagicMock()
        mock_copilot_cls = MagicMock(return_value=mock_agent)

        with (
            patch("src.services.agent_provider.get_settings") as mock_settings,
            patch.dict(
                "sys.modules",
                {"agent_framework": MagicMock(), "agent_framework.github": MagicMock()},
            ),
        ):
            mock_settings.return_value = MagicMock(ai_provider="copilot")
            # Patch the import inside the function
            import sys

            sys.modules["agent_framework.github"].GitHubCopilotAgent = mock_copilot_cls

            result = create_agent_provider("system prompt", [MagicMock()])

        assert result.name == "copilot"
        mock_copilot_cls.assert_called_once()

    def test_copilot_without_framework_raises(self):
        """When agent-framework-github-copilot is missing, factory raises ValueError."""
        with (
            patch("src.services.agent_provider.get_settings") as mock_settings,
            patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'agent_framework.github'"),
            ),
        ):
            mock_settings.return_value = MagicMock(ai_provider="copilot")
            with pytest.raises(ValueError, match="agent-framework-github-copilot"):
                create_agent_provider("instructions")


# ── Factory — Azure OpenAI provider ─────────────────────────────────────


class TestCreateAzureAgent:
    def test_azure_without_credentials_raises(self):
        """Missing Azure OpenAI credentials should raise ValueError."""
        with patch("src.services.agent_provider.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                ai_provider="azure_openai",
                azure_openai_endpoint=None,
                azure_openai_key=None,
            )
            with pytest.raises(ValueError, match="credentials not configured"):
                create_agent_provider("instructions")

    def test_azure_without_endpoint_raises(self):
        with patch("src.services.agent_provider.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                ai_provider="azure_openai",
                azure_openai_endpoint=None,
                azure_openai_key="key-123",
            )
            with pytest.raises(ValueError, match="credentials not configured"):
                create_agent_provider("instructions")

    def test_azure_with_framework_installed(self):
        """When agent-framework-openai is available, factory creates agent."""
        mock_agent = MagicMock()
        mock_agent_cls = MagicMock(return_value=mock_agent)
        mock_client = MagicMock()
        mock_client_cls = MagicMock(return_value=mock_client)

        with (
            patch("src.services.agent_provider.get_settings") as mock_settings,
            patch.dict(
                "sys.modules",
                {
                    "agent_framework": MagicMock(),
                    "agent_framework.openai": MagicMock(),
                },
            ),
        ):
            mock_settings.return_value = MagicMock(
                ai_provider="azure_openai",
                azure_openai_endpoint="https://test.openai.azure.com",
                azure_openai_key="key-123",
                azure_openai_deployment="gpt-4",
            )
            import sys

            sys.modules["agent_framework"].Agent = mock_agent_cls
            sys.modules["agent_framework.openai"].AzureOpenAIResponsesClient = mock_client_cls

            result = create_agent_provider("system prompt", [MagicMock()])

        assert result.name == "azure_openai"
        mock_client_cls.assert_called_once()
        mock_agent_cls.assert_called_once()

    def test_azure_without_framework_raises(self):
        """When agent-framework-openai is missing, factory raises ValueError."""
        with (
            patch("src.services.agent_provider.get_settings") as mock_settings,
            patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'agent_framework'"),
            ),
        ):
            mock_settings.return_value = MagicMock(
                ai_provider="azure_openai",
                azure_openai_endpoint="https://test.openai.azure.com",
                azure_openai_key="key-123",
            )
            with pytest.raises(ValueError, match="agent-framework-openai"):
                create_agent_provider("instructions")
