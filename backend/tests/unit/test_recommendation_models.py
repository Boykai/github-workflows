"""Tests for recommendation Pydantic models (src/models/recommendation.py).

Covers:
- AITaskProposal max_length boundary for proposed_description
- ProposalConfirmRequest max_length boundary for edited_description
- Unicode and special character preservation
- file_urls field defaults and serialization
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.constants import GITHUB_ISSUE_BODY_MAX_LENGTH
from src.models.recommendation import AITaskProposal, IssueRecommendation, ProposalConfirmRequest

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
        desc = "Hello 🌍 – «résumé» — naïve — 日本語テスト — 🚀🎉"  # noqa: RUF001
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


# ── File URLs ───────────────────────────────────────────────────────────────


class TestFileUrlsField:
    """file_urls field defaults, serialization, and round-trip behavior."""

    def test_proposal_file_urls_default(self):
        """New AITaskProposal has empty file_urls list."""
        proposal = AITaskProposal(
            session_id=uuid4(),
            original_input="test",
            proposed_title="Test",
            proposed_description="Desc",
        )
        assert proposal.file_urls == []

    def test_proposal_file_urls_set(self):
        """AITaskProposal accepts file_urls at construction."""
        urls = ["/chat/uploads/abc-screenshot.png", "/chat/uploads/def-report.pdf"]
        proposal = AITaskProposal(
            session_id=uuid4(),
            original_input="test",
            proposed_title="Test",
            proposed_description="Desc",
            file_urls=urls,
        )
        assert proposal.file_urls == urls

    def test_proposal_file_urls_serialization(self):
        """file_urls round-trips through JSON serialization."""
        urls = ["/chat/uploads/abc-screenshot.png"]
        proposal = AITaskProposal(
            session_id=uuid4(),
            original_input="test",
            proposed_title="Test",
            proposed_description="Desc",
            file_urls=urls,
        )
        data = proposal.model_dump()
        restored = AITaskProposal(**data)
        assert restored.file_urls == urls

    def test_recommendation_file_urls_default(self):
        """New IssueRecommendation has empty file_urls list."""
        rec = IssueRecommendation(
            session_id=uuid4(),
            original_input="test",
            title="Test",
            user_story="As a user...",
            ui_ux_description="Button on page",
            functional_requirements=["FR-001"],
        )
        assert rec.file_urls == []

    def test_recommendation_file_urls_set(self):
        """IssueRecommendation accepts file_urls at construction."""
        urls = ["/chat/uploads/abc-img.png"]
        rec = IssueRecommendation(
            session_id=uuid4(),
            original_input="test",
            title="Test",
            user_story="As a user...",
            ui_ux_description="Button on page",
            functional_requirements=["FR-001"],
            file_urls=urls,
        )
        assert rec.file_urls == urls

    def test_recommendation_file_urls_serialization(self):
        """file_urls round-trips through JSON serialization on IssueRecommendation."""
        urls = ["/chat/uploads/abc-img.png", "/chat/uploads/def-doc.pdf"]
        rec = IssueRecommendation(
            session_id=uuid4(),
            original_input="test",
            title="Test",
            user_story="As a user...",
            ui_ux_description="Button on page",
            functional_requirements=["FR-001"],
            file_urls=urls,
        )
        data = rec.model_dump()
        restored = IssueRecommendation(**data)
        assert restored.file_urls == urls
