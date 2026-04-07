"""Unit tests for agent provider factory (src/services/agent_provider.py).

Covers:
- create_agent_provider with copilot setting
- create_agent_provider with azure_openai setting
- create_agent_provider with unsupported provider
- AgentProvider.run() placeholder
- AgentProvider.run_stream() placeholder
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.services.agent_provider import AgentProvider, create_agent_provider

# ── AgentProvider basic behaviour ──────────────────────────────────────────


class TestAgentProvider:
    def test_init(self):
        p = AgentProvider(provider_name="test", model="gpt-4o")
        assert p.provider_name == "test"
        assert p.model == "gpt-4o"

    async def test_run_returns_dict(self):
        p = AgentProvider(provider_name="test")
        result = await p.run("hello")
        assert isinstance(result, dict)
        assert "content" in result
        assert "test" in result["content"]

    async def test_run_stream_yields_chunks(self):
        p = AgentProvider(provider_name="test")
        chunks = [chunk async for chunk in p.run_stream("hello")]
        assert len(chunks) >= 1
        assert "delta" in chunks[0]


# ── Factory: create_agent_provider ─────────────────────────────────────────


class TestCreateAgentProvider:
    @patch("src.services.agent_provider.get_settings")
    def test_copilot_provider(self, mock_settings):
        mock_settings.return_value.ai_provider = "copilot"
        mock_settings.return_value.copilot_model = "gpt-4o"

        provider = create_agent_provider()
        assert provider.provider_name == "copilot"
        assert provider.model == "gpt-4o"

    @patch("src.services.agent_provider.get_settings")
    def test_azure_openai_provider(self, mock_settings):
        mock_settings.return_value.ai_provider = "azure_openai"
        mock_settings.return_value.azure_openai_deployment = "gpt-4"

        provider = create_agent_provider()
        assert provider.provider_name == "azure_openai"
        assert provider.model == "gpt-4"

    @patch("src.services.agent_provider.get_settings")
    def test_unsupported_provider_raises(self, mock_settings):
        mock_settings.return_value.ai_provider = "unsupported"

        with pytest.raises(ValueError, match="Unsupported AI_PROVIDER"):
            create_agent_provider()

    @patch("src.services.agent_provider.get_settings")
    def test_case_insensitive(self, mock_settings):
        mock_settings.return_value.ai_provider = "COPILOT"
        mock_settings.return_value.copilot_model = "gpt-4o"

        provider = create_agent_provider()
        assert provider.provider_name == "copilot"
