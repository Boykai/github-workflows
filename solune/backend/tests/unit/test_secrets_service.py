"""Unit tests for SecretsService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.secrets_service import SecretsService


@pytest.fixture
def mock_client_factory():
    factory = MagicMock()
    factory.get_client = AsyncMock()
    return factory


@pytest.fixture
def secrets_service(mock_client_factory):
    return SecretsService(mock_client_factory)


@pytest.fixture
def mock_client(mock_client_factory):
    client = AsyncMock()
    mock_client_factory.get_client.return_value = client
    return client


class TestGetOrCreateEnvironment:
    async def test_calls_create_or_update_environment(self, secrets_service, mock_client):
        await secrets_service.get_or_create_environment("token", "owner", "repo", "copilot")

        mock_client.rest.repos.async_create_or_update_environment.assert_awaited_once_with(
            owner="owner",
            repo="repo",
            environment_name="copilot",
        )


class TestListSecrets:
    async def test_returns_parsed_data(self, secrets_service, mock_client):
        mock_response = MagicMock()
        mock_response.parsed_data.model_dump.return_value = {
            "total_count": 2,
            "secrets": [
                {"name": "KEY_A", "created_at": "2026-01-01", "updated_at": "2026-01-02"},
                {"name": "KEY_B", "created_at": "2026-01-01", "updated_at": "2026-01-02"},
            ],
        }
        mock_client.rest.actions.async_list_environment_secrets.return_value = mock_response

        result = await secrets_service.list_secrets("token", "owner", "repo", "copilot")

        assert result["total_count"] == 2
        assert len(result["secrets"]) == 2
        assert result["secrets"][0]["name"] == "KEY_A"


class TestDeleteSecret:
    async def test_calls_delete_endpoint(self, secrets_service, mock_client):
        await secrets_service.delete_secret("token", "owner", "repo", "copilot", "MY_KEY")

        mock_client.rest.actions.async_delete_environment_secret.assert_awaited_once_with(
            owner="owner",
            repo="repo",
            environment_name="copilot",
            secret_name="MY_KEY",
        )


class TestCheckSecrets:
    async def test_returns_existence_map(self, secrets_service, mock_client):
        mock_response = MagicMock()
        mock_response.parsed_data.model_dump.return_value = {
            "total_count": 1,
            "secrets": [
                {"name": "KEY_A", "created_at": "2026-01-01", "updated_at": "2026-01-02"},
            ],
        }
        mock_client.rest.actions.async_list_environment_secrets.return_value = mock_response

        result = await secrets_service.check_secrets(
            "token", "owner", "repo", "copilot", ["KEY_A", "KEY_B"]
        )

        assert result == {"KEY_A": True, "KEY_B": False}


class TestSetSecret:
    async def test_encrypts_and_upserts(self, secrets_service, mock_client):
        # Mock the public key response
        pk_response = MagicMock()
        pk_response.parsed_data.key = "2Sg8iYjAxxmI2LvUXpJjkYrMxURPc8r+dB7TJyvvcCU="
        pk_response.parsed_data.key_id = "key-id-123"
        mock_client.rest.actions.async_get_environment_public_key.return_value = pk_response

        await secrets_service.set_secret(
            "token", "owner", "repo", "copilot", "MY_KEY", "my-secret-value"
        )

        # Verify the encrypted value was sent
        call_args = mock_client.rest.actions.async_create_or_update_environment_secret.call_args
        assert call_args.kwargs["owner"] == "owner"
        assert call_args.kwargs["repo"] == "repo"
        assert call_args.kwargs["environment_name"] == "copilot"
        assert call_args.kwargs["secret_name"] == "MY_KEY"
        data = call_args.kwargs["data"]
        assert data["key_id"] == "key-id-123"
        # encrypted_value should be a non-empty base64 string
        assert len(data["encrypted_value"]) > 0
