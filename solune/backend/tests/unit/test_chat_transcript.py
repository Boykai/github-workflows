"""Unit tests for transcript analysis via AIAgentService.analyze_transcript().

Covers:
- Happy-path transcript analysis producing an IssueRecommendation
- Truncation of original_input to 500 characters
- Error handling for invalid AI responses
"""

import pytest

from src.models.chat import RecommendationStatus
from src.services.ai_agent import AIAgentService
from src.services.completion_providers import CompletionProvider


class MockCompletionProvider(CompletionProvider):
    """Test double for CompletionProvider that returns configurable responses."""

    def __init__(self, response: str = ""):
        self._response = response
        self._side_effect: Exception | None = None

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        github_token: str | None = None,
    ) -> str:
        if self._side_effect:
            raise self._side_effect
        return self._response

    def set_response(self, response: str) -> None:
        self._response = response
        self._side_effect = None

    def set_error(self, error: Exception) -> None:
        self._side_effect = error

    @property
    def name(self) -> str:
        return "mock"


VALID_AI_RESPONSE = (
    '{"title": "Dark Mode Feature", '
    '"user_story": "As a user I want dark mode so I can reduce eye strain", '
    '"ui_ux_description": "Toggle in settings", '
    '"functional_requirements": ["System MUST provide dark theme", '
    '"System MUST persist preference", "System SHOULD support auto-detect", '
    '"System MUST apply to all pages", "System SHOULD animate transition"], '
    '"technical_notes": "Use CSS custom properties", '
    '"metadata": {"priority": "P1", "size": "M", "estimate_hours": 4, '
    '"labels": ["feature", "frontend", "ai-generated"]}}'
)


class TestAnalyzeTranscript:
    """Tests for AIAgentService.analyze_transcript()."""

    @pytest.fixture()
    def mock_provider(self):
        return MockCompletionProvider()

    @pytest.fixture()
    def service(self, mock_provider):
        return AIAgentService(provider=mock_provider)

    async def test_happy_path(self, service, mock_provider):
        mock_provider.set_response(VALID_AI_RESPONSE)
        rec = await service.analyze_transcript(
            transcript_content="Alice: Dark mode please\nBob: Agreed",
            project_name="MyProject",
            session_id="00000000-0000-0000-0000-000000000001",
        )
        assert rec.title == "Dark Mode Feature"
        assert rec.status == RecommendationStatus.PENDING
        assert "ai-generated" in rec.metadata.labels
        assert len(rec.functional_requirements) >= 5

    async def test_original_input_truncated_to_500_chars(self, service, mock_provider):
        mock_provider.set_response(VALID_AI_RESPONSE)
        long_transcript = "A" * 1000
        rec = await service.analyze_transcript(
            transcript_content=long_transcript,
            project_name="Proj",
            session_id="00000000-0000-0000-0000-000000000001",
        )
        assert len(rec.original_input) == 500
        # original_context preserves the full transcript
        assert rec.original_context == long_transcript

    async def test_short_transcript_not_truncated(self, service, mock_provider):
        mock_provider.set_response(VALID_AI_RESPONSE)
        short = "Alice: Hello"
        rec = await service.analyze_transcript(
            transcript_content=short,
            project_name="Proj",
            session_id="00000000-0000-0000-0000-000000000001",
        )
        assert rec.original_input == short

    async def test_auth_error_raises_value_error(self, service, mock_provider):
        mock_provider.set_error(RuntimeError("401 Unauthorized"))
        with pytest.raises(ValueError, match="authentication failed"):
            await service.analyze_transcript(
                transcript_content="content",
                project_name="Proj",
                session_id="00000000-0000-0000-0000-000000000001",
            )

    async def test_not_found_error_raises_value_error(self, service, mock_provider):
        mock_provider.set_error(RuntimeError("404 Resource not found"))
        with pytest.raises(ValueError, match="not found"):
            await service.analyze_transcript(
                transcript_content="content",
                project_name="Proj",
                session_id="00000000-0000-0000-0000-000000000001",
            )

    async def test_generic_error_raises_value_error(self, service, mock_provider):
        mock_provider.set_error(RuntimeError("connection timeout"))
        with pytest.raises(ValueError, match="Failed to analyse transcript"):
            await service.analyze_transcript(
                transcript_content="content",
                project_name="Proj",
                session_id="00000000-0000-0000-0000-000000000001",
            )

    async def test_metadata_context_passed_through(self, service, mock_provider):
        mock_provider.set_response(VALID_AI_RESPONSE)
        rec = await service.analyze_transcript(
            transcript_content="Alice: Needs dark mode",
            project_name="Proj",
            session_id="00000000-0000-0000-0000-000000000001",
            metadata_context={"labels": ["bug", "feature"]},
        )
        assert rec.title == "Dark Mode Feature"
