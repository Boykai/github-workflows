"""Unit tests for completion providers."""

from unittest.mock import MagicMock, patch

import pytest

from src.services.completion_providers import (
    CopilotCompletionProvider,
    create_completion_provider,
)


class TestCopilotCompletionProvider:
    """Tests for CopilotCompletionProvider."""

    def test_name_returns_copilot(self):
        """Should return 'copilot' as provider name."""
        provider = CopilotCompletionProvider()

        assert provider.name == "copilot"

    def test_default_model_is_gpt4o(self):
        """Should use gpt-4o as default model."""
        provider = CopilotCompletionProvider()

        assert provider._model == "gpt-4o"

    def test_custom_model(self):
        """Should accept custom model name."""
        provider = CopilotCompletionProvider(model="gpt-3.5-turbo")

        assert provider._model == "gpt-3.5-turbo"

    def test_token_key_returns_stable_hash(self):
        """Should return consistent hash for same token."""
        key1 = CopilotCompletionProvider._token_key("my_token_123")
        key2 = CopilotCompletionProvider._token_key("my_token_123")

        assert key1 == key2
        assert len(key1) == 16

    def test_token_key_differs_for_different_tokens(self):
        """Should return different hashes for different tokens."""
        key1 = CopilotCompletionProvider._token_key("token_a")
        key2 = CopilotCompletionProvider._token_key("token_b")

        assert key1 != key2

    def test_token_key_does_not_contain_raw_token(self):
        """Should not expose raw token in key."""
        token = "ghp_super_secret_token_12345"
        key = CopilotCompletionProvider._token_key(token)

        assert token not in key
        assert "ghp_" not in key

    @pytest.mark.asyncio
    async def test_complete_without_token_raises_error(self):
        """Should raise ValueError when no GitHub token provided."""
        provider = CopilotCompletionProvider()
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(ValueError, match="GitHub OAuth token required"):
            await provider.complete(messages)

    @pytest.mark.asyncio
    async def test_complete_with_none_token_raises_error(self):
        """Should raise ValueError when token is explicitly None."""
        provider = CopilotCompletionProvider()
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(ValueError, match="GitHub OAuth token required"):
            await provider.complete(messages, github_token=None)

    @pytest.mark.asyncio
    async def test_complete_with_empty_token_raises_error(self):
        """Should raise ValueError when token is empty string."""
        provider = CopilotCompletionProvider()
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(ValueError, match="GitHub OAuth token required"):
            await provider.complete(messages, github_token="")

    def test_clients_cache_initially_empty(self):
        """Should start with empty clients cache."""
        provider = CopilotCompletionProvider()

        assert len(provider._clients) == 0


class TestCreateCompletionProvider:
    """Tests for create_completion_provider factory function."""

    @patch("src.services.completion_providers.get_settings")
    def test_creates_copilot_provider_by_default(self, mock_settings):
        """Should create CopilotCompletionProvider for 'copilot' setting."""
        mock_settings.return_value = MagicMock(
            ai_provider="copilot", copilot_model="gpt-4o"
        )

        provider = create_completion_provider()

        assert isinstance(provider, CopilotCompletionProvider)
        assert provider.name == "copilot"

    @patch("src.services.completion_providers.get_settings")
    def test_creates_copilot_provider_with_custom_model(self, mock_settings):
        """Should pass model from settings to CopilotCompletionProvider."""
        mock_settings.return_value = MagicMock(
            ai_provider="copilot", copilot_model="gpt-3.5-turbo"
        )

        provider = create_completion_provider()

        assert isinstance(provider, CopilotCompletionProvider)
        assert provider._model == "gpt-3.5-turbo"

    @patch("src.services.completion_providers.get_settings")
    def test_unknown_provider_raises_error(self, mock_settings):
        """Should raise ValueError for unknown provider."""
        mock_settings.return_value = MagicMock(ai_provider="unknown_provider")

        with pytest.raises(ValueError, match="Unknown AI provider"):
            create_completion_provider()

    @patch("src.services.completion_providers.get_settings")
    def test_azure_provider_without_credentials_raises_error(self, mock_settings):
        """Should raise ValueError when Azure credentials missing."""
        mock_settings.return_value = MagicMock(
            ai_provider="azure_openai",
            azure_openai_endpoint=None,
            azure_openai_key=None,
            azure_openai_deployment="gpt-4",
        )

        with pytest.raises(ValueError, match="Azure OpenAI credentials not configured"):
            create_completion_provider()
