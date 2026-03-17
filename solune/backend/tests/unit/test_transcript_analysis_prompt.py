"""Unit tests for transcript analysis prompt construction.

Follows the pattern from ``test_prompts.py`` for issue generation prompts.
"""

from src.prompts.transcript_analysis import (
    TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT,
    create_transcript_analysis_prompt,
)
from src.utils import utcnow


class TestTranscriptAnalysisSystemPrompt:
    """Validate the system prompt constant."""

    def test_prompt_is_non_empty_string(self):
        assert isinstance(TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT, str)
        assert len(TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT) > 100

    def test_prompt_instructs_json_output(self):
        assert "JSON" in TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT

    def test_prompt_mentions_user_story(self):
        assert "user_story" in TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT

    def test_prompt_mentions_functional_requirements(self):
        assert "functional_requirements" in TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT

    def test_prompt_mentions_title(self):
        assert "title" in TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT

    def test_prompt_mentions_speakers(self):
        assert "speaker" in TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT.lower()


class TestCreateTranscriptAnalysisPrompt:
    """Tests for create_transcript_analysis_prompt()."""

    SAMPLE_TRANSCRIPT = (
        "Alice: I think we need a dark mode feature.\n"
        "Bob: Agreed, let me handle the CSS.\n"
        "Alice: Also, responsive layout is important.\n"
    )

    def test_returns_two_messages(self):
        msgs = create_transcript_analysis_prompt(self.SAMPLE_TRANSCRIPT, "My Project")
        assert len(msgs) == 2

    def test_system_message_first(self):
        msgs = create_transcript_analysis_prompt(self.SAMPLE_TRANSCRIPT, "My Project")
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == TRANSCRIPT_ANALYSIS_SYSTEM_PROMPT

    def test_user_message_second(self):
        msgs = create_transcript_analysis_prompt(self.SAMPLE_TRANSCRIPT, "My Project")
        assert msgs[1]["role"] == "user"

    def test_user_message_contains_transcript(self):
        msgs = create_transcript_analysis_prompt(self.SAMPLE_TRANSCRIPT, "My Project")
        assert self.SAMPLE_TRANSCRIPT in msgs[1]["content"]

    def test_user_message_contains_project_name(self):
        msgs = create_transcript_analysis_prompt(self.SAMPLE_TRANSCRIPT, "Test Project")
        assert "Test Project" in msgs[1]["content"]

    def test_user_message_contains_date(self):
        msgs = create_transcript_analysis_prompt(self.SAMPLE_TRANSCRIPT, "proj")
        today = utcnow().strftime("%Y-%m-%d")
        assert today in msgs[1]["content"]

    def test_metadata_context_labels_included(self):
        ctx = {"labels": [{"name": "bug"}, {"name": "feature"}]}
        msgs = create_transcript_analysis_prompt(
            self.SAMPLE_TRANSCRIPT, "proj", metadata_context=ctx
        )
        user_content = msgs[1]["content"]
        assert '"bug"' in user_content
        assert '"feature"' in user_content

    def test_metadata_context_branches_included(self):
        ctx = {"branches": [{"name": "main"}, {"name": "develop"}]}
        msgs = create_transcript_analysis_prompt(
            self.SAMPLE_TRANSCRIPT, "proj", metadata_context=ctx
        )
        user_content = msgs[1]["content"]
        assert '"main"' in user_content
        assert '"develop"' in user_content

    def test_no_metadata_context(self):
        msgs = create_transcript_analysis_prompt(self.SAMPLE_TRANSCRIPT, "proj")
        # Should still produce valid output
        assert len(msgs) == 2
        assert "proj" in msgs[1]["content"]

    def test_empty_metadata_context(self):
        msgs = create_transcript_analysis_prompt(
            self.SAMPLE_TRANSCRIPT, "proj", metadata_context={}
        )
        assert len(msgs) == 2
