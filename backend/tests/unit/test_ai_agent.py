"""Unit tests for the AI agent service (Azure OpenAI integration)."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.services.ai_agent import (
    AIAgentService,
    GeneratedTask,
    StatusChangeIntent,
)


class TestAIAgentServiceInit:
    """Tests for AIAgentService initialization."""

    @patch("src.services.ai_agent.get_settings")
    def test_init_creates_client_with_settings(self, mock_get_settings):
        """Service should initialize with Azure OpenAI settings."""
        mock_settings = Mock()
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai_api_key = "test-api-key"
        mock_settings.azure_openai_deployment = "gpt-4-test"
        mock_get_settings.return_value = mock_settings

        with patch("openai.AzureOpenAI"):
            service = AIAgentService()
            assert service._deployment == "gpt-4-test"


class TestGenerateTaskFromDescription:
    """Tests for task generation from natural language."""

    @pytest.fixture
    def mock_service(self):
        """Create a service with mocked client."""
        with patch("src.services.ai_agent.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                azure_openai_endpoint="https://test.openai.azure.com",
                azure_openai_api_key="test-key",
                azure_openai_deployment="gpt-4",
            )
            with patch("openai.AzureOpenAI"):
                service = AIAgentService()
                return service

    @pytest.mark.asyncio
    async def test_generate_task_parses_json_response(self, mock_service):
        """Service should parse JSON response and return GeneratedTask."""
        # Mock the _call_completion method
        mock_service._call_completion = Mock(
            return_value='{"title": "Test Task", "description": "Test Description"}'
        )

        result = await mock_service.generate_task_from_description(
            "Create a task for testing", "Test Project"
        )

        assert isinstance(result, GeneratedTask)
        assert result.title == "Test Task"
        assert result.description == "Test Description"

    @pytest.mark.asyncio
    async def test_generate_task_handles_markdown_code_blocks(self, mock_service):
        """Service should handle JSON wrapped in markdown code blocks."""
        mock_service._call_completion = Mock(
            return_value='```json\n{"title": "Markdown Task", "description": "With code block"}\n```'
        )

        result = await mock_service.generate_task_from_description(
            "Create a task", "Project"
        )

        assert result.title == "Markdown Task"
        assert result.description == "With code block"

    @pytest.mark.asyncio
    async def test_generate_task_raises_on_invalid_json(self, mock_service):
        """Service should raise ValueError on invalid JSON."""
        mock_service._call_completion = Mock(return_value="Not valid JSON")

        with pytest.raises(ValueError, match="Failed to generate task"):
            await mock_service.generate_task_from_description("Create task", "Project")

    @pytest.mark.asyncio
    async def test_generate_task_raises_on_missing_title(self, mock_service):
        """Service should raise ValueError when title is missing."""
        mock_service._call_completion = Mock(return_value='{"description": "No title"}')

        with pytest.raises(ValueError, match="Failed to generate task"):
            await mock_service.generate_task_from_description("Create task", "Project")

    @pytest.mark.asyncio
    async def test_generate_task_truncates_long_title(self, mock_service):
        """Service should truncate titles over 256 characters."""
        long_title = "A" * 300
        mock_service._call_completion = Mock(
            return_value=f'{{"title": "{long_title}", "description": "Test"}}'
        )

        result = await mock_service.generate_task_from_description("Create task", "Project")

        assert len(result.title) == 256
        assert result.title.endswith("...")

    @pytest.mark.asyncio
    async def test_generate_task_helpful_error_on_401(self, mock_service):
        """Service should provide helpful error message on 401."""
        mock_service._call_completion = Mock(side_effect=Exception("401 Access denied"))

        with pytest.raises(ValueError, match="authentication failed"):
            await mock_service.generate_task_from_description("Create task", "Project")

    @pytest.mark.asyncio
    async def test_generate_task_helpful_error_on_404(self, mock_service):
        """Service should provide helpful error message on 404."""
        mock_service._call_completion = Mock(side_effect=Exception("404 Resource not found"))

        with pytest.raises(ValueError, match="not found"):
            await mock_service.generate_task_from_description("Create task", "Project")


class TestParseStatusChangeRequest:
    """Tests for status change intent detection."""

    @pytest.fixture
    def mock_service(self):
        """Create a service with mocked client."""
        with patch("src.services.ai_agent.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                azure_openai_endpoint="https://test.openai.azure.com",
                azure_openai_api_key="test-key",
                azure_openai_deployment="gpt-4",
            )
            with patch("openai.AzureOpenAI"):
                service = AIAgentService()
                return service

    @pytest.mark.asyncio
    async def test_parse_status_change_returns_intent(self, mock_service):
        """Service should return StatusChangeIntent for valid requests."""
        mock_service._call_completion = Mock(
            return_value='{"intent": "status_change", "task_reference": "Login feature", "target_status": "Done", "confidence": 0.9}'
        )

        result = await mock_service.parse_status_change_request(
            "Mark login feature as done",
            ["Login feature", "Dashboard"],
            ["Todo", "In Progress", "Done"]
        )

        assert isinstance(result, StatusChangeIntent)
        assert result.task_reference == "Login feature"
        assert result.target_status == "Done"
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_parse_status_change_returns_none_for_low_confidence(self, mock_service):
        """Service should return None for low confidence detections."""
        mock_service._call_completion = Mock(
            return_value='{"intent": "status_change", "task_reference": "Task", "target_status": "Done", "confidence": 0.3}'
        )

        result = await mock_service.parse_status_change_request(
            "Maybe done?", ["Task"], ["Todo", "Done"]
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_status_change_returns_none_for_non_status_intent(self, mock_service):
        """Service should return None when intent is not status_change."""
        mock_service._call_completion = Mock(
            return_value='{"intent": "create_task", "confidence": 0.9}'
        )

        result = await mock_service.parse_status_change_request(
            "Create a new task", ["Task"], ["Todo", "Done"]
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_status_change_handles_errors_gracefully(self, mock_service):
        """Service should return None on errors, not raise."""
        mock_service._call_completion = Mock(side_effect=Exception("API Error"))

        result = await mock_service.parse_status_change_request(
            "Move task", ["Task"], ["Todo", "Done"]
        )

        assert result is None


class TestIdentifyTargetTask:
    """Tests for task reference matching."""

    @pytest.fixture
    def service(self):
        """Create a service with mocked initialization."""
        with patch("src.services.ai_agent.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                azure_openai_endpoint="https://test.openai.azure.com",
                azure_openai_api_key="test-key",
                azure_openai_deployment="gpt-4",
            )
            with patch("openai.AzureOpenAI"):
                return AIAgentService()

    def test_identify_task_exact_match(self, service):
        """Should find exact title match."""
        tasks = [
            {"task_id": "1", "title": "Login Feature"},
            {"task_id": "2", "title": "Dashboard"},
        ]

        result = service.identify_target_task("Login Feature", tasks)

        assert result["task_id"] == "1"

    def test_identify_task_case_insensitive(self, service):
        """Should match case-insensitively."""
        tasks = [{"task_id": "1", "title": "Login Feature"}]

        result = service.identify_target_task("login feature", tasks)

        assert result["task_id"] == "1"

    def test_identify_task_partial_match(self, service):
        """Should match partial references."""
        tasks = [
            {"task_id": "1", "title": "Implement Login Feature"},
            {"task_id": "2", "title": "Dashboard Widget"},
        ]

        result = service.identify_target_task("Login Feature", tasks)

        assert result["task_id"] == "1"

    def test_identify_task_word_overlap(self, service):
        """Should match by word overlap when no partial match."""
        tasks = [
            {"task_id": "1", "title": "Create user authentication system"},
            {"task_id": "2", "title": "Build dashboard"},
        ]

        result = service.identify_target_task("user authentication", tasks)

        assert result["task_id"] == "1"

    def test_identify_task_returns_none_for_empty(self, service):
        """Should return None for empty inputs."""
        assert service.identify_target_task("", []) is None
        assert service.identify_target_task("task", []) is None
        assert service.identify_target_task("", [{"task_id": "1", "title": "Task"}]) is None


class TestIdentifyTargetStatus:
    """Tests for status reference matching."""

    @pytest.fixture
    def service(self):
        """Create a service with mocked initialization."""
        with patch("src.services.ai_agent.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                azure_openai_endpoint="https://test.openai.azure.com",
                azure_openai_api_key="test-key",
                azure_openai_deployment="gpt-4",
            )
            with patch("openai.AzureOpenAI"):
                return AIAgentService()

    def test_identify_status_exact_match(self, service):
        """Should find exact status match."""
        statuses = ["Todo", "In Progress", "Done"]

        assert service.identify_target_status("Done", statuses) == "Done"

    def test_identify_status_case_insensitive(self, service):
        """Should match case-insensitively."""
        statuses = ["Todo", "In Progress", "Done"]

        assert service.identify_target_status("done", statuses) == "Done"
        assert service.identify_target_status("TODO", statuses) == "Todo"

    def test_identify_status_partial_match(self, service):
        """Should match partial references."""
        statuses = ["Todo", "In Progress", "Done"]

        assert service.identify_target_status("progress", statuses) == "In Progress"

    def test_identify_status_aliases(self, service):
        """Should recognize common status aliases."""
        statuses = ["Todo", "In Progress", "Done"]

        # "completed" is an alias for "done"
        assert service.identify_target_status("completed", statuses) == "Done"
        # "doing" is an alias for "in progress"
        assert service.identify_target_status("doing", statuses) == "In Progress"

    def test_identify_status_returns_none_for_unknown(self, service):
        """Should return None for unrecognized statuses."""
        statuses = ["Todo", "In Progress", "Done"]

        assert service.identify_target_status("random status", statuses) is None

    def test_identify_status_returns_none_for_empty(self, service):
        """Should return None for empty inputs."""
        assert service.identify_target_status("", []) is None
        assert service.identify_target_status("done", []) is None
        assert service.identify_target_status("", ["Todo"]) is None


class TestParseJsonResponse:
    """Tests for JSON parsing helper."""

    @pytest.fixture
    def service(self):
        """Create a service with mocked initialization."""
        with patch("src.services.ai_agent.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                azure_openai_endpoint="https://test.openai.azure.com",
                azure_openai_api_key="test-key",
                azure_openai_deployment="gpt-4",
            )
            with patch("openai.AzureOpenAI"):
                return AIAgentService()

    def test_parse_plain_json(self, service):
        """Should parse plain JSON."""
        result = service._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_with_markdown(self, service):
        """Should strip markdown code blocks."""
        result = service._parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_with_generic_markdown(self, service):
        """Should strip generic markdown code blocks."""
        result = service._parse_json_response('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_raises_on_invalid(self, service):
        """Should raise ValueError on invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON response"):
            service._parse_json_response("not json at all")


class TestAzureOpenAIIntegration:
    """Integration tests for Azure OpenAI connection (requires valid credentials).
    
    These tests are skipped by default. Run with: pytest -m integration
    """

    @pytest.fixture
    def live_service(self):
        """Create a service using real settings (if available)."""
        try:
            # This will use actual .env settings
            service = AIAgentService()
            return service
        except Exception as e:
            pytest.skip(f"Azure OpenAI credentials not configured: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_live_task_generation(self, live_service):
        """Test actual task generation with Azure OpenAI.
        
        This test requires valid Azure OpenAI credentials and deployment.
        Skipped if the API returns an error (invalid credentials or deployment).
        """
        try:
            result = await live_service.generate_task_from_description(
                "Create a login page with email and password fields",
                "Web App Project"
            )

            assert isinstance(result, GeneratedTask)
            assert len(result.title) > 0
            assert len(result.description) > 0
        except ValueError as e:
            error_msg = str(e)
            if any(code in error_msg for code in ["404", "401", "403", "Resource not found", "Access denied"]):
                pytest.skip(f"Azure OpenAI not available or credentials invalid: {e}")
            raise

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_live_status_change_detection(self, live_service):
        """Test actual status change detection with Azure OpenAI.
        
        This test requires valid Azure OpenAI credentials and deployment.
        Skipped if the API returns an error.
        """
        try:
            result = await live_service.parse_status_change_request(
                "Mark the login feature task as completed",
                ["Login feature", "Dashboard", "Settings page"],
                ["Todo", "In Progress", "Done"]
            )

            # Should detect status change intent
            if result:
                assert isinstance(result, StatusChangeIntent)
                assert result.confidence >= 0.5
        except Exception as e:
            error_msg = str(e)
            if any(code in error_msg for code in ["404", "401", "403", "Resource not found", "Access denied"]):
                pytest.skip(f"Azure OpenAI not available or credentials invalid: {e}")
            # For status change, we return None on errors, so this shouldn't happen
            raise
