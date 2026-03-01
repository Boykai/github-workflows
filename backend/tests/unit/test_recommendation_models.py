"""Tests for recommendation Pydantic models (src/models/recommendation.py).

Covers:
- AITaskProposal max_length boundary for proposed_description
- ProposalConfirmRequest max_length boundary for edited_description
- Unicode and special character preservation
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.constants import GITHUB_ISSUE_BODY_MAX_LENGTH
from src.models.recommendation import AITaskProposal, ProposalConfirmRequest

# ── AITaskProposal ──────────────────────────────────────────────────────────


class TestAITaskProposalDescriptionLength:
    """T004: AITaskProposal must accept descriptions up to 65,536 characters."""

    def test_accepts_max_length_description(self):
        """A description at exactly GITHUB_ISSUE_BODY_MAX_LENGTH (65,536) chars is valid."""
        long_desc = "x" * GITHUB_ISSUE_BODY_MAX_LENGTH
        proposal = AITaskProposal(
            session_id=uuid4(),
            original_input="test",
            proposed_title="Test",
            proposed_description=long_desc,
        )
        assert len(proposal.proposed_description) == GITHUB_ISSUE_BODY_MAX_LENGTH

    def test_rejects_over_max_length_description(self):
        """T012: A description exceeding 65,536 characters raises Pydantic ValidationError."""
        over_desc = "x" * (GITHUB_ISSUE_BODY_MAX_LENGTH + 1)
        with pytest.raises(ValidationError):
            AITaskProposal(
                session_id=uuid4(),
                original_input="test",
                proposed_title="Test",
                proposed_description=over_desc,
            )


# ── ProposalConfirmRequest ──────────────────────────────────────────────────


class TestProposalConfirmRequestDescriptionLength:
    """T005: ProposalConfirmRequest must accept descriptions up to 65,536 characters."""

    def test_accepts_max_length_edited_description(self):
        """An edited_description at exactly 65,536 chars is valid."""
        long_desc = "y" * GITHUB_ISSUE_BODY_MAX_LENGTH
        req = ProposalConfirmRequest(edited_description=long_desc)
        assert len(req.edited_description) == GITHUB_ISSUE_BODY_MAX_LENGTH

    def test_rejects_over_max_length_edited_description(self):
        """An edited_description exceeding 65,536 characters raises Pydantic ValidationError."""
        over_desc = "y" * (GITHUB_ISSUE_BODY_MAX_LENGTH + 1)
        with pytest.raises(ValidationError):
            ProposalConfirmRequest(edited_description=over_desc)


# ── Unicode and Special Characters ──────────────────────────────────────────


class TestDescriptionFormattingPreservation:
    """T023: Unicode, emoji, and special characters are preserved in descriptions."""

    def test_unicode_emoji_preserved(self):
        desc = "Hello 🌍 – «résumé» — naïve — 日本語テスト — 🚀🎉"
        proposal = AITaskProposal(
            session_id=uuid4(),
            original_input="test",
            proposed_title="Test",
            proposed_description=desc,
        )
        assert proposal.proposed_description == desc

    def test_markdown_formatting_preserved(self):
        desc = (
            "# Header\n\n"
            "## Sub-header\n\n"
            "- bullet 1\n"
            "- bullet 2\n\n"
            "```python\nprint('hello')\n```\n\n"
            "> blockquote\n\n"
            "| Col1 | Col2 |\n|------|------|\n| a | b |\n\n"
            "**bold** *italic* ~~strike~~ `code`\n\n"
            "[link](https://example.com)\n\n"
            "---\n"
        )
        proposal = AITaskProposal(
            session_id=uuid4(),
            original_input="test",
            proposed_title="Test",
            proposed_description=desc,
        )
        assert proposal.proposed_description == desc

    def test_newlines_and_whitespace_preserved(self):
        desc = "line1\n\nline3\n\n\nline5\ttab\rcarriage"
        proposal = AITaskProposal(
            session_id=uuid4(),
            original_input="test",
            proposed_title="Test",
            proposed_description=desc,
        )
        assert proposal.proposed_description == desc
